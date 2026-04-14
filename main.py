import asyncio

from agents import AgentRegistry, WriterAgent
from config.settings import get_settings
from llm.factory import create_llm


async def main():
    settings = get_settings()
    print(f"Project: {settings.project_name}")
    print(f"LLM Provider: {settings.llm_provider.value}")
    print(f"Model: {settings.llm_model_name}")
    print("-" * 50)

    llm = create_llm(settings)
    print(f"LLM created: {llm}")

    agent = WriterAgent(settings=settings)
    print(f"Agent created: {agent}")

    print("\nRegistered agents:", AgentRegistry.list_agents())


if __name__ == "__main__":
    asyncio.run(main())
