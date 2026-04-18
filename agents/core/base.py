from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings, get_settings
from llm.factory import create_llm


class AgentState(BaseModel):
    messages: list[BaseMessage] = Field(default_factory=list)
    current_task: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
        settings: Optional[Settings] = None,
    ):
        self.name = name
        self.settings = settings or get_settings()
        self.llm = llm or create_llm(self.settings)
        self.tools = tools or []
        self._state = AgentState()

    @property
    def state(self) -> AgentState:
        return self._state

    def reset_state(self) -> None:
        self._state = AgentState()

    def add_tool(self, tool: BaseTool) -> None:
        self.tools.append(tool)

    def add_tools(self, tools: list[BaseTool]) -> None:
        self.tools.extend(tools)

    @abstractmethod
    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    async def astream_chat(
        self, session_id: str, message: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天方法

        子类应实现此方法以提供流式输出支持。
        默认实现会回退到 execute 方法，逐字符输出完整内容。

        Args:
            session_id: 会话 ID
            message: 用户消息
            **kwargs: 其他参数

        Yields:
            流式输出的文本片段
        """
        response = await self.execute(message, session_id=session_id, **kwargs)
        if response.success and response.content:
            for char in response.content:
                yield char

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
