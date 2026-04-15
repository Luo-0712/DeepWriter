"""联网搜索工具模块，使用Tavily API"""

from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings, get_settings


class SearchInput(BaseModel):
    """搜索输入参数"""
    query: str = Field(description="搜索查询内容")
    max_results: int = Field(default=5, description="返回结果数量", ge=1, le=10)


class TavilySearchTool(BaseTool):
    """Tavily联网搜索工具"""

    name: str = "tavily_search"
    description: str = """使用Tavily搜索引擎进行联网搜索，获取实时信息。
    适用于需要获取最新资讯、验证事实、查找参考资料等场景。
    输入应为搜索查询字符串，返回搜索结果摘要。
    """
    args_schema: type[BaseModel] = SearchInput

    def __init__(self, api_key: Optional[str] = None, settings: Optional[Settings] = None):
        super().__init__()
        self._settings = settings or get_settings()
        self._api_key = api_key or self._settings.tavily_api_key

    def _run(self, query: str, max_results: int = 5) -> str:
        """同步执行搜索"""
        import requests

        if not self._api_key:
            return "错误：Tavily API密钥未配置。请在配置文件中设置TAVILY_API_KEY。"

        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": True,
            "include_images": False,
            "include_raw_content": False,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            return self._format_results(data)
        except requests.exceptions.RequestException as e:
            return f"搜索请求失败: {str(e)}"
        except Exception as e:
            return f"搜索过程中发生错误: {str(e)}"

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """异步执行搜索"""
        import aiohttp

        if not self._api_key:
            return "错误：Tavily API密钥未配置。请在配置文件中设置TAVILY_API_KEY。"

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": True,
            "include_images": False,
            "include_raw_content": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return self._format_results(data)
        except aiohttp.ClientError as e:
            return f"搜索请求失败: {str(e)}"
        except Exception as e:
            return f"搜索过程中发生错误: {str(e)}"

    def _format_results(self, data: dict[str, Any]) -> str:
        """格式化搜索结果"""
        results = []

        # 添加AI生成的答案摘要
        if answer := data.get("answer"):
            results.append("【AI摘要】")
            results.append(answer)
            results.append("")

        # 添加搜索结果
        if search_results := data.get("results", []):
            results.append("【搜索结果】")
            for i, result in enumerate(search_results, 1):
                title = result.get("title", "无标题")
                content = result.get("content", "")
                url = result.get("url", "")
                score = result.get("score", 0)

                results.append(f"{i}. {title} (相关度: {score:.2f})")
                if content:
                    # 截断过长的内容
                    content = content[:300] + "..." if len(content) > 300 else content
                    results.append(f"   {content}")
                if url:
                    results.append(f"   链接: {url}")
                results.append("")

        return "\n".join(results) if results else "未找到相关结果。"


def get_search_tool(api_key: Optional[str] = None, settings: Optional[Settings] = None) -> TavilySearchTool:
    """获取搜索工具实例"""
    return TavilySearchTool(api_key=api_key, settings=settings)
