"""起草智能体 - 负责根据大纲和研究笔记生成文章初稿"""

import json
import logging
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.core import AgentRegistry, AgentResponse, BaseAgent
from config.settings import Settings
from services.prompt.manager import get_prompt_manager

logger = logging.getLogger(__name__)


@AgentRegistry.register("draft")
class DraftAgent(BaseAgent):
    def __init__(
        self,
        name: str = "DraftAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        language: str = "zh",
        style: str = "professional",
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.language = language
        self.style = style
        self.prompt_manager = get_prompt_manager()

    def get_system_prompt(self) -> str:
        return self.prompt_manager.get_system_prompt(
            agent_name="specialized",
            language=self.language,
        )

    def _load_prompt_template(self) -> str:
        prompts = self.prompt_manager.load(
            agent_name="specialized",
            prompt_name="draft",
            language=self.language,
        )
        return prompts.get("system", "")

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        try:
            outline = kwargs.get("outline", {})
            research_notes = kwargs.get("research_notes", {})
            tone = kwargs.get("tone", "专业")

            template = self._load_prompt_template()
            system_prompt = template.format(style=self.style, tone=tone)

            user_content = f"文章大纲：\n{json.dumps(outline, ensure_ascii=False, indent=2)}\n\n"
            if research_notes:
                user_content += f"研究笔记：\n{json.dumps(research_notes, ensure_ascii=False, indent=2)}\n\n"
            user_content += "请根据以上大纲和研究资料，撰写完整的文章。"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content),
            ]

            response = await self.llm.ainvoke(messages)

            return AgentResponse(
                content=response.content,
                success=True,
                metadata={"word_count": len(response.content)},
            )
        except Exception as e:
            logger.error(f"DraftAgent 执行失败: {e}")
            return AgentResponse(content="", success=False, error=str(e))
