import json
import re
from typing import Any, Dict, List, Optional
import pandas as pd
import structlog
from app.analyzer import analyzer_instance, DataAnalyzer, AnalysisError
from app.dataset import dataset_loader, DatasetLoader
from app.downloader import downloader_instance, DatasetDownloader, DownloaderError
from app.logger import ExecutionLogger
from app.memory import memory_manager, ConversationMemory
from app.prompts import SYSTEM_PROMPT, PLANNING_PROMPT_TEMPLATE, EXTRACT_SCHEMA_PROMPT_TEMPLATE
from app.schemas import DatasetInfo
from services.llm import llm_service, LLMService
from services.telegram_service import telegram_service

logger = structlog.get_logger()


class DataAnalystAgent:
    """Production AI Data Analyst Agent for Telegram Bot."""

    def __init__(
        self,
        memory: Optional[ConversationMemory] = None,
        downloader: Optional[DatasetDownloader] = None,
        analyzer: Optional[DataAnalyzer] = None,
        llm: Optional[LLMService] = None
    ):
        self.memory = memory or memory_manager
        self.downloader = downloader or downloader_instance
        self.analyzer = analyzer or analyzer_instance
        self.llm = llm or llm_service

    async def process_message(
        self,
        chat_id: int,
        user_id: int,
        message_text: str,
        execution_id: Optional[str] = None
    ) -> str:
        """
        Main entry point for processing a Telegram message.
        Returns a single JSON string formatted as {"answer": ..., "log_url": "..."}.
        """
        exec_logger = ExecutionLogger(execution_id=execution_id, user_id=user_id, chat_id=chat_id)
        exec_logger.log_event("message_received", message_text=message_text)

        # Normalize unicode whitespace (non-breaking space \xa0, etc.) in message_text
        message_text = re.sub(r'[\xa0\u2000-\u200b\u202f\u205f\u3000]', ' ', message_text)

        log_url = exec_logger.get_log_url()

        try:
            # 1. Detect dataset URLs from current message and prior history
            extracted_urls = DatasetLoader.extract_urls(message_text)
            historical_urls = await self.memory.get_all_dataset_urls(chat_id)
            all_urls = list(dict.fromkeys(extracted_urls + historical_urls))

            # Store user message in conversation memory
            has_dataset = len(extracted_urls) > 0 or DatasetLoader.parse_inline_dataset(message_text) is not None
            await self.memory.add_user_message(
                chat_id=chat_id,
                content=message_text,
                has_dataset=has_dataset,
                dataset_urls=extracted_urls
            )

            # 2. Download/load datasets
            loaded_dfs: Dict[str, pd.DataFrame] = {}
            dataset_summaries: List[Dict[str, Any]] = []

            # Process URLs
            for url in all_urls:
                try:
                    exec_logger.log_event("dataset_download_started", url=url)
                    file_path, file_ext = await self.downloader.download_file(url)
                    exec_logger.log_event("dataset_downloaded", url=url, file_path=str(file_path))

                    df = DatasetLoader.load_file(file_path)
                    ds_name = f"df_{len(loaded_dfs) + 1}"
                    loaded_dfs[ds_name] = df

                    info = DatasetLoader.summarize_dataframe(df, source=url)
                    dataset_summaries.append(info.model_dump())
                except DownloaderError as de:
                    exec_logger.log_event("dataset_download_error", url=url, error=str(de))
                except Exception as ex:
                    exec_logger.log_event("dataset_parse_error", url=url, error=str(ex))

            # Check for inline dataset in current message if no datasets loaded yet
            if not loaded_dfs:
                inline_df = DatasetLoader.parse_inline_dataset(message_text)
                if inline_df is not None:
                    loaded_dfs["df_1"] = inline_df
                    info = DatasetLoader.summarize_dataframe(inline_df, source="inline_text")
                    dataset_summaries.append(info.model_dump())
                    exec_logger.log_event("inline_dataset_parsed", rows=len(inline_df), cols=len(inline_df.columns))

            # 3. Retrieve conversation history
            history_msgs = await self.memory.get_history(chat_id)
            formatted_history = "\n".join(f"{m.role}: {m.content}" for m in history_msgs[:-1])

            # 4. Formulate planning prompt and get analysis Python code from LLM
            dataset_summary_str = json.dumps(dataset_summaries, indent=2) if dataset_summaries else "No dataset attached."
            planning_prompt = PLANNING_PROMPT_TEMPLATE.format(
                question=message_text,
                history=formatted_history or "None",
                dataset_summary=dataset_summary_str
            )

            exec_logger.log_event("planning_started", prompt_length=len(planning_prompt))
            llm_response = await self.llm.generate_response(SYSTEM_PROMPT, planning_prompt)
            exec_logger.log_event("planning_completed", llm_response=llm_response)

            # 5. Execute code/analysis
            code = self._extract_python_code(llm_response)
            exec_logger.log_event("analysis_started", code=code)

            if code:
                try:
                    raw_result = self.analyzer.execute_python_code(code, loaded_dfs)
                except Exception as ex:
                    exec_logger.log_event("code_execution_error", error=str(ex))
                    if loaded_dfs:
                        raw_result = self.analyzer.compute_summary_stats(list(loaded_dfs.values())[0], list(loaded_dfs.values())[0].columns[0])
                    else:
                        raw_result = llm_response
            elif loaded_dfs:
                # Default fallback calculation if LLM gave no code: describe primary dataframe
                raw_result = self.analyzer.compute_summary_stats(list(loaded_dfs.values())[0], list(loaded_dfs.values())[0].columns[0])
            else:
                # General query without dataset
                raw_result = llm_response

            exec_logger.log_event("analysis_completed", raw_result=str(raw_result))

            # 6. Format raw result into requested JSON answer schema
            answer_object = await self._format_answer_schema(message_text, raw_result)

            exec_logger.log_event("response_generated", answer=answer_object)

            # Save assistant response to memory
            await self.memory.add_assistant_message(chat_id=chat_id, content=json.dumps(answer_object, default=str))

            return telegram_service.format_bot_response(answer=answer_object, log_url=log_url)

        except Exception as e:
            logger.error("agent_execution_error", error=str(e), chat_id=chat_id)
            exec_logger.log_event("error", error=str(e))
            error_answer = {"error": str(e)}
            return telegram_service.format_bot_response(answer=error_answer, log_url=log_url)

    def _extract_python_code(self, text: str) -> str:
        """Extracts python code snippet from markdown code blocks or raw string."""
        match = re.search(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        if "result =" in text or "result=" in text:
            return text.strip()
        return ""

    async def _format_answer_schema(self, question: str, raw_result: Any) -> Any:
        """Converts raw calculation output into exact JSON schema implied by user question."""
        # If result is already structured dict or list
        if isinstance(raw_result, (dict, list)):
            return raw_result

        # Ask LLM to format string/numeric raw result into clean JSON structure
        extract_prompt = EXTRACT_SCHEMA_PROMPT_TEMPLATE.format(
            question=question,
            raw_result=str(raw_result)
        )
        try:
            formatted_json_str = await self.llm.generate_response(SYSTEM_PROMPT, extract_prompt)
            # Clean markdown codeblocks if present in LLM response
            clean_str = re.sub(r"^```(?:json)?\s*", "", formatted_json_str.strip(), flags=re.IGNORECASE)
            clean_str = re.sub(r"\s*```$", "", clean_str)

            parsed = json.loads(clean_str)
            return parsed
        except Exception:
            # Fallback to direct key-value or raw value
            return {"result": raw_result}


agent_instance = DataAnalystAgent()
