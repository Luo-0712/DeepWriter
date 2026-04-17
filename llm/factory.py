from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from config.settings import LLMProvider, Settings, get_settings


class LLMFactory:
    _instances: dict[str, BaseChatModel] = {}

    @classmethod
    def create(cls, settings: Optional[Settings] = None, force_new: bool = False) -> BaseChatModel:
        if settings is None:
            settings = Settings()
        else:
            settings = settings

        cache_key = f"{settings.llm_provider.value}:{settings.llm_model_name}"

        if not force_new and cache_key in cls._instances:
            return cls._instances[cache_key]

        llm = cls._create_llm(settings)
        cls._instances[cache_key] = llm
        return llm

    @classmethod
    def _create_llm(cls, settings: Settings) -> BaseChatModel:
        provider = settings.llm_provider

        if provider == LLMProvider.OPENAI:
            return cls._create_openai(settings)
        elif provider == LLMProvider.ANTHROPIC:
            return cls._create_anthropic(settings)
        elif provider == LLMProvider.AZURE_OPENAI:
            return cls._create_azure_openai(settings)
        elif provider == LLMProvider.DEEPSEEK:
            return cls._create_deepseek(settings)
        elif provider == LLMProvider.ZHIPU:
            return cls._create_zhipu(settings)
        elif provider == LLMProvider.QWEN:
            return cls._create_qwen(settings)
        elif provider == LLMProvider.CUSTOM:
            return cls._create_custom(settings)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _create_openai(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

    @staticmethod
    def _create_anthropic(settings: Settings) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.anthropic_api_key,
        )

    @staticmethod
    def _create_azure_openai(settings: Settings) -> AzureChatOpenAI:
        return AzureChatOpenAI(
            azure_deployment=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
        )

    @staticmethod
    def _create_deepseek(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_api_base,
        )

    @staticmethod
    def _create_zhipu(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_api_base,
        )

    @staticmethod
    def _create_qwen(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_api_base,
        )

    @staticmethod
    def _create_custom(settings: Settings) -> ChatOpenAI:
        if not settings.openai_api_base:
            raise ValueError("Custom provider requires openai_api_base to be set")
        return ChatOpenAI(
            model=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

    @classmethod
    def clear_cache(cls) -> None:
        cls._instances.clear()


def create_llm(settings: Optional[Settings] = None, force_new: bool = False) -> BaseChatModel:
    return LLMFactory.create(settings, force_new)
