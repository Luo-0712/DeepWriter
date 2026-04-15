from abc import ABC, abstractmethod
from typing import Any, Optional

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
