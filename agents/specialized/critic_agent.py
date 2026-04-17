"""评审智能体 - 负责评估文章质量并给出评分和反馈"""

import json
import logging
import re
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.core import AgentRegistry, AgentResponse, BaseAgent
from config.settings import Settings
from services.prompt.manager import get_prompt_manager

logger = logging.getLogger(__name__)


@AgentRegistry.register("critic")
class CriticAgent(BaseAgent):
    def __init__(
        self,
        name: str = "CriticAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        language: str = "zh",
        pass_threshold: float = 7.0,
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.language = language
        self.pass_threshold = pass_threshold
        self.prompt_manager = get_prompt_manager()

    def get_system_prompt(self) -> str:
        return self.prompt_manager.get_system_prompt(
            agent_name="specialized",
            language=self.language,
        )

    def _load_prompt_template(self) -> str:
        prompts = self.prompt_manager.load(
            agent_name="specialized",
            prompt_name="critic",
            language=self.language,
        )
        return prompts.get("system", "")

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        try:
            article_content = kwargs.get("article_content", input_text)

            template = self._load_prompt_template()

            messages = [
                SystemMessage(content=template),
                HumanMessage(
                    content=f"请评审以下文章：\n\n{article_content}"
                ),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            review = self._parse_review(content)

            return AgentResponse(
                content=content,
                success=True,
                metadata={"review": review},
            )
        except Exception as e:
            logger.error(f"CriticAgent 执行失败: {e}")
            return AgentResponse(content="", success=False, error=str(e))

    def _parse_review(self, content: str) -> dict[str, Any]:
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                except json.JSONDecodeError:
                    result = None
            else:
                result = None

        if result is None:
            return {
                "overall_score": 0,
                "passed": False,
                "raw_content": content,
            }

        # 确保 passed 字段基于阈值判断
        overall_score = result.get("overall_score", 0)
        result["passed"] = overall_score >= self.pass_threshold
        return result
