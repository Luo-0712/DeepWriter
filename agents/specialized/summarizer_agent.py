from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.core import AgentRegistry, AgentResponse, BaseAgent
from config.settings import Settings
from services.prompt.manager import get_prompt_manager


@AgentRegistry.register("summarizer")
class SummarizerAgent(BaseAgent):
    """标题生成智能体

    用于在会话的第一条消息之后，自动生成一句话标题。
    """

    def __init__(
        self,
        name: str = "SummarizerAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        language: str = "zh",
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.language = language
        self.prompt_manager = get_prompt_manager()

    def get_system_prompt(self) -> str:
        """加载标题生成的系统提示词"""
        return self.prompt_manager.get_system_prompt(
            agent_name="summarizer",
            language=self.language,
            variables={},
        )

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        """执行标题生成任务

        Args:
            input_text: 用户输入的第一条消息内容

        Returns:
            AgentResponse: 包含生成的标题
        """
        try:
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=input_text),
            ]

            response = await self.llm.ainvoke(messages)
            title = response.content.strip()

            return AgentResponse(
                content=title,
                success=True,
                metadata={"language": self.language},
            )
        except Exception as e:
            return AgentResponse(
                content="",
                success=False,
                error=str(e),
            )
