"""
Prompt 管理器

负责加载、缓存和管理 prompt 模板文件。
支持多语言、模板变量格式化、缓存和 fallback 机制。
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate


class PromptManager:
    """Prompt 管理器"""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        default_language: str = "zh",
        fallback_language: str = "en",
    ):
        """
        初始化 Prompt 管理器

        Args:
            base_dir: prompt 文件基础目录，默认为 agents/<agent_name>/prompts/
            default_language: 默认语言
            fallback_language: 回退语言（当目标语言文件不存在时）
        """
        self.base_dir = base_dir or Path(__file__).parent.parent.parent / "agents"
        self.default_language = default_language
        self.fallback_language = fallback_language
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_prompt_path(self, agent_name: str, language: str) -> Path:
        """获取 prompt 文件路径"""
        return self.base_dir / agent_name / "prompts" / language

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """加载 YAML 文件"""
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        if path.is_dir():
            # 如果是目录，尝试加载该目录下的所有 yaml 文件
            prompts = {}
            for file in path.glob("*.yaml"):
                with open(file, "r", encoding="utf-8") as f:
                    key = file.stem
                    prompts[key] = yaml.safe_load(f)
            return prompts
        else:
            # 如果是文件，直接加载
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

    def load(
        self,
        agent_name: str,
        prompt_name: str = "system",
        language: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        加载 prompt 文件

        Args:
            agent_name: Agent 名称
            prompt_name: prompt 文件名称（不含扩展名），或目录名
            language: 语言，默认使用 default_language
            use_cache: 是否使用缓存

        Returns:
            prompt 内容字典
        """
        language = language or self.default_language
        cache_key = f"{agent_name}:{prompt_name}:{language}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        prompt_path = self._get_prompt_path(agent_name, language) / f"{prompt_name}.yaml"

        # 尝试加载目标语言
        try:
            prompts = self._load_yaml(prompt_path)
            self._cache[cache_key] = prompts
            return prompts
        except FileNotFoundError:
            pass

        # 尝试回退语言
        if language != self.fallback_language:
            fallback_path = self._get_prompt_path(agent_name, self.fallback_language) / f"{prompt_name}.yaml"
            try:
                prompts = self._load_yaml(fallback_path)
                self._cache[cache_key] = prompts
                return prompts
            except FileNotFoundError:
                pass

        raise FileNotFoundError(
            f"Prompt not found for agent '{agent_name}': {prompt_name} "
            f"(tried {language} and {self.fallback_language})"
        )

    def get_system_prompt(
        self,
        agent_name: str,
        language: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        获取系统提示词

        Args:
            agent_name: Agent 名称
            language: 语言
            variables: 模板变量

        Returns:
            格式化后的系统提示词
        """
        prompts = self.load(agent_name, "system", language)
        template = prompts.get("system", "")

        if variables:
            return template.format(**variables)
        return template

    def get_chat_prompt(
        self,
        agent_name: str,
        language: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> ChatPromptTemplate:
        """
        获取聊天提示词模板

        Args:
            agent_name: Agent 名称
            language: 语言
            variables: 模板变量

        Returns:
            ChatPromptTemplate 对象
        """
        prompts = self.load(agent_name, "system", language)

        messages = []

        # 系统消息
        if "system" in prompts:
            system_template = prompts["system"]
            if variables:
                system_template = system_template.format(**variables)
            messages.append(SystemMessagePromptTemplate.from_template(system_template))

        # 用户消息
        if "user" in prompts:
            user_template = prompts["user"]
            messages.append(HumanMessagePromptTemplate.from_template(user_template))
        else:
            messages.append(HumanMessagePromptTemplate.from_template("{input}"))

        return ChatPromptTemplate(messages=messages)

    def clear_cache(self, agent_name: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            agent_name: 指定 Agent 名称清除，None 则清除全部
        """
        if agent_name:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{agent_name}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()

    def reload(self, agent_name: str, prompt_name: str = "system") -> dict[str, Any]:
        """强制重新加载 prompt 文件"""
        return self.load(agent_name, prompt_name, use_cache=False)


# 全局实例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取全局 PromptManager 实例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
