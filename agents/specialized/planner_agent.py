"""规划智能体 - 负责生成文章大纲"""

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


@AgentRegistry.register("planner")
class PlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str = "PlannerAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        language: str = "zh",
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.language = language
        self.prompt_manager = get_prompt_manager()

    def get_system_prompt(self, **kwargs) -> str:
        variables = {
            "topic": kwargs.get("topic", ""),
            "audience": kwargs.get("audience", "通用读者"),
            "goal": kwargs.get("goal", "信息传达"),
            "tone": kwargs.get("tone", "专业"),
            "length": kwargs.get("length", "medium"),
        }
        return self.prompt_manager.get_system_prompt(
            agent_name="specialized",
            language=self.language,
            variables=variables,
        )

    def _load_prompt_template(self) -> str:
        prompts = self.prompt_manager.load(
            agent_name="specialized",
            prompt_name="planner",
            language=self.language,
        )
        return prompts.get("system", "")

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        try:
            template = self._load_prompt_template()
            system_prompt = template.format(
                topic=kwargs.get("topic", input_text),
                audience=kwargs.get("audience", "通用读者"),
                goal=kwargs.get("goal", "信息传达"),
                tone=kwargs.get("tone", "专业"),
                length=kwargs.get("length", "medium"),
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"请为以下主题创建文章大纲：{input_text}"),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 尝试解析 JSON
            outline = self._parse_outline(content)

            return AgentResponse(
                content=content,
                success=True,
                metadata={"outline": outline},
            )
        except Exception as e:
            logger.error(f"PlannerAgent 执行失败: {e}")
            return AgentResponse(content="", success=False, error=str(e))

    def _parse_outline(self, content: str) -> dict[str, Any]:
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试从 markdown code block 中提取
            import re
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"raw_content": content}
