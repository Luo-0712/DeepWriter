import asyncio

from agents import AgentRegistry, WriterAgent
from config.settings import get_settings
from llm.factory import create_llm
from services.models import WritingRequest
from workflows import WritingOrchestrator


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


async def run_workflow_demo():
    """工作流演示：展示标准写作工作流的完整执行"""
    print("=" * 60)
    print("DeepWriter 写作工作流演示")
    print("=" * 60)

    request = WritingRequest(
        topic="人工智能在教育领域的应用与前景",
        task_type="article",
        audience="教育工作者和技术爱好者",
        goal="介绍AI在教育中的当前应用和未来发展趋势",
        tone="专业且易懂",
        length="medium",
        language="zh",
        style="informative",
        use_rag=False,
        use_web=False,
    )

    # 标准模式
    orchestrator = WritingOrchestrator(mode="standard", max_iterations=2)

    print(f"\n主题: {request.topic}")
    print(f"模式: {orchestrator.mode}")
    print("-" * 60)

    # 流式执行，显示每个阶段
    print("\n开始执行工作流...\n")
    async for event in orchestrator.execute_stream(request):
        node = event["node"]
        stage = event["stage"]
        update = event["update"]

        print(f"[{node}] 阶段: {stage}")

        if node == "plan" and "outline" in update:
            outline = update["outline"]
            print(f"  标题: {outline.get('title', 'N/A')}")

        if node == "critic" and "review_feedback" in update:
            review = update["review_feedback"]
            print(f"  评分: {review.get('overall_score', 'N/A')}")
            print(f"  通过: {review.get('passed', 'N/A')}")

        if update.get("error"):
            print(f"  错误: {update['error']}")

        print()

    print("=" * 60)
    print("工作流演示结束")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "workflow":
        asyncio.run(run_workflow_demo())
    else:
        asyncio.run(main())
