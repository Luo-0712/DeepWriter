from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.base import AgentResponse, BaseAgent
from agents.registry import AgentRegistry
from config.settings import Settings
from services.models import WritingRequest, WritingState
from services.prompt.manager import get_prompt_manager
from services.session.manager import get_session_manager


@AgentRegistry.register("writer")
class WriterAgent(BaseAgent):
    def __init__(
        self,
        name: str = "WriterAgent",
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
        style: str = "professional",
        language: str = "zh",
        session_manager=None,
    ):
        super().__init__(name=name, llm=llm, tools=tools, settings=settings)
        self.style = style
        self.language = language
        self.prompt_manager = get_prompt_manager()
        self.session_manager = session_manager or get_session_manager()
        self._current_state: Optional[WritingState] = None

    def get_system_prompt(self) -> str:
        """从 prompt 文件加载系统提示词"""
        return self.prompt_manager.get_system_prompt(
            agent_name="writer",
            language=self.language,
            variables={"style": self.style},
        )

    async def execute(
        self, input_text: str, request: Optional[WritingRequest] = None, **kwargs
    ) -> AgentResponse:
        """
        执行写作任务

        Args:
            input_text: 用户输入文本
            request: 写作请求对象，可选

        Returns:
            AgentResponse 响应对象
        """
        try:
            # 如果提供了 WritingRequest，则创建或更新 WritingState
            if request:
                self._current_state = self.session_manager.start_writing(request)
                self.session_manager.add_message("user", input_text)
            elif self.session_manager.current_session:
                # 使用现有 session 的状态
                self._current_state = self.session_manager.current_session.writing_state
                self.session_manager.add_message("user", input_text)

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=input_text),
            ]

            response = await self.llm.ainvoke(messages)

            # 更新状态
            if self._current_state:
                self._current_state.add_draft_section(response.content)
                self._current_state.set_final_text(response.content)
                self.session_manager.save_session()

            if self.session_manager.current_session:
                self.session_manager.add_message("assistant", response.content)

            return AgentResponse(
                content=response.content,
                success=True,
                metadata={
                    "style": self.style,
                    "language": self.language,
                    "session_id": self.session_manager.current_session_id,
                },
            )
        except Exception as e:
            return AgentResponse(
                content="",
                success=False,
                error=str(e),
            )

    def get_current_state(self) -> Optional[WritingState]:
        """获取当前写作状态"""
        return self._current_state

    def reset_state(self) -> None:
        """重置状态"""
        self._current_state = None
        if self.session_manager.current_session:
            self.session_manager.current_session.writing_state = None
            self.session_manager.save_session()
