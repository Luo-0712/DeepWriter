"""研究智能体 - 负责收集和整理研究资料"""

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


@AgentRegistry.register("researcher")
class ResearcherAgent(BaseAgent):
    def __init__(
        self,
        name: str = "ResearcherAgent",
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
            prompt_name="researcher",
            language=self.language,
        )
        return prompts.get("system", "")

    async def _gather_materials(self, outline: dict, use_rag: bool, use_web: bool) -> str:
        """使用工具收集研究资料"""
        materials = []
        keywords = outline.get("keywords", [])
        sections = outline.get("sections", [])

        # 收集所有需要搜索的查询
        queries = list(keywords)
        for section in sections:
            for point in section.get("key_points", []):
                queries.append(point)

        for tool in self.tools:
            tool_name = getattr(tool, "name", "")
            for query in queries[:5]:  # 限制查询数量
                try:
                    if use_web and "search" in tool_name:
                        result = await tool.ainvoke({"query": query})
                        materials.append(f"[网络搜索] {query}:\n{result}")
                    elif use_rag and "rag" in tool_name:
                        result = await tool.ainvoke({"query": query, "kb_name": "default"})
                        materials.append(f"[知识库检索] {query}:\n{result}")
                except Exception as e:
                    logger.warning(f"工具调用失败 ({tool_name}, {query}): {e}")

        return "\n\n---\n\n".join(materials) if materials else "无额外参考资料"

    async def execute(self, input_text: str, **kwargs) -> AgentResponse:
        try:
            outline = kwargs.get("outline", {})
            use_rag = kwargs.get("use_rag", False)
            use_web = kwargs.get("use_web", False)

            # 收集研究资料
            materials = await self._gather_materials(outline, use_rag, use_web)

            template = self._load_prompt_template()
            messages = [
                SystemMessage(content=template),
                HumanMessage(
                    content=f"文章大纲：\n{json.dumps(outline, ensure_ascii=False, indent=2)}\n\n"
                    f"参考资料：\n{materials}\n\n"
                    f"请根据以上大纲和参考资料，整理研究笔记。"
                ),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            research_notes = self._parse_research(content)

            return AgentResponse(
                content=content,
                success=True,
                metadata={"research_notes": research_notes},
            )
        except Exception as e:
            logger.error(f"ResearcherAgent 执行失败: {e}")
            return AgentResponse(content="", success=False, error=str(e))

    def _parse_research(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"raw_content": content}

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
            outline = kwargs.get("outline", {})
            use_rag = kwargs.get("use_rag", False)
            use_web = kwargs.get("use_web", False)

            # 收集研究资料
            materials = await self._gather_materials(outline, use_rag, use_web)

            template = self._load_prompt_template()
            messages = [
                SystemMessage(content=template),
                HumanMessage(
                    content=f"文章大纲：\n{json.dumps(outline, ensure_ascii=False, indent=2)}\n\n"
                    f"参考资料：\n{materials}\n\n"
                    f"请根据以上大纲和参考资料，整理研究笔记。"
                ),
            ]

            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content

        except Exception as e:
            yield f"[错误] 流式聊天失败: {str(e)}"
