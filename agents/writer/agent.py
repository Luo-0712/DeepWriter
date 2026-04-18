from typing import AsyncGenerator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from agents.core import AgentRegistry, AgentResponse, BaseAgent
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

    async def astream_chat(
        self, session_id: str, message: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天方法

        使用 LLM 的流式 API 逐块输出内容。

        Args:
            session_id: 会话 ID
            message: 用户消息
            **kwargs: 其他参数

        Yields:
            流式输出的文本片段
        """
        try:
            # 确保加载了正确的会话
            if self.session_manager.current_session_id != session_id:
                self.session_manager.load_session(session_id)

            # 获取会话的聊天历史
            chat_history = self.session_manager.get_message_history(limit=10)

            # 构建消息列表
            messages = [SystemMessage(content=self.get_system_prompt())]

            # 添加历史消息
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        messages.append(HumanMessage(content=msg.get("content", "")))

            # 添加当前消息
            messages.append(HumanMessage(content=message))

            # 保存用户消息到会话
            if self.session_manager.current_session:
                self.session_manager.add_message("user", message)

            # 使用流式 API 调用 LLM
            full_content = ""
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    full_content += chunk.content
                    yield chunk.content

            # 保存完整回复
            if self.session_manager.current_session:
                self.session_manager.add_message("assistant", full_content)

            # 更新写作状态
            if self._current_state:
                self._current_state.add_draft_section(full_content)
                self._current_state.set_final_text(full_content)
                self.session_manager.save_session()

        except Exception as e:
            yield f"[错误] 流式聊天失败: {str(e)}"

    def get_current_state(self) -> Optional[WritingState]:
        """获取当前写作状态"""
        return self._current_state

    def reset_state(self) -> None:
        """重置状态"""
        self._current_state = None
        if self.session_manager.current_session:
            self.session_manager.current_session.writing_state = None
            self.session_manager.save_session()
