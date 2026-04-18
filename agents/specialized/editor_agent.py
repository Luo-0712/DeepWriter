"""编辑智能体 - 负责审查和改进文章草稿"""

import json
import logging
import re
from typing import Any, AsyncGenerator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.core import AgentRegistry, AgentResponse, BaseAgent
from config.settings import Settings
from services.prompt.manager import get_prompt_manager

logger = logging.getLogger(__name__)


@AgentRegistry.register("editor")
class EditorAgent(BaseAgent):
    def __init__(
        self,
        name: str = "EditorAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        language: str = "zh",
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.language = language
        self.prompt_manager = get_prompt_manager()

    def get_system_prompt(self) -> str:
        return self.prompt_manager.get_system_prompt(
            agent_name="specialized",
            language=self.language,
        )

    def _load_prompt_template(self) -> str:
        prompts = self.prompt_manager.load(
            agent_name="specialized",
            prompt_name="editor",
            language=self.language,
        )
        return prompts.get("system", "")

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        try:
            draft_content = kwargs.get("draft_content", input_text)

            template = self._load_prompt_template()

            messages = [
                SystemMessage(content=template),
                HumanMessage(
                    content=f"请审查和改进以下文章草稿：\n\n{draft_content}"
                ),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            edit_result = self._parse_edit_result(content)

            return AgentResponse(
                content=content,
                success=True,
                metadata={"edit_result": edit_result},
            )
        except Exception as e:
            logger.error(f"EditorAgent 执行失败: {e}")
            return AgentResponse(content="", success=False, error=str(e))

    def _parse_edit_result(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"revised_content": content, "suggestions": [], "summary": ""}

    async def astream_chat(
        self, session_id: str, message: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天方法

        Args:
            session_id: 会话 ID
            message: 用户消息
            **kwargs: 其他参数

        Yields:
            流式输出的文本片段
        """
        try:
            draft_content = kwargs.get("draft_content", message)

            template = self._load_prompt_template()

            messages = [
                SystemMessage(content=template),
                HumanMessage(content=f"请审查和改进以下文章草稿：\n\n{draft_content}"),
            ]

            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content

        except Exception as e:
            yield f"[错误] 流式聊天失败: {str(e)}"
