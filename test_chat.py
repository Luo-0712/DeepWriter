"""
DeepWriter 对话测试脚本

使用方法:
    python test_chat.py

命令:
    quit/exit/q - 退出对话
    clear - 清空上下文
    help - 显示帮助信息
    style <style> - 切换写作风格 (professional, casual, academic, creative)
    language <lang> - 切换语言 (zh, en)
    session [id] - 查看/切换 Session
    status - 显示当前写作状态
    history - 显示消息历史
"""

import asyncio

from agents import AgentRegistry, WriterAgent
from config.settings import get_settings
from llm.factory import create_llm
from services.models import WritingRequest
from services.prompt.manager import get_prompt_manager
from services.session.manager import get_session_manager


async def chat_test():
    """交互式对话测试"""
    settings = get_settings()
    print(f"项目：{settings.project_name}")
    print(f"LLM 提供商：{settings.llm_provider.value}")
    print(f"模型：{settings.llm_model_name}")
    print("-" * 50)

    llm = create_llm(settings)
    print(f"LLM 已创建：{llm}")

    agent = WriterAgent(settings=settings)
    print(f"Agent 已创建：{agent}")

    session_manager = get_session_manager()
    print(f"SessionManager 已创建")

    print("\n已注册的 agents:", AgentRegistry.list_agents())
    print("-" * 50)
    print("对话测试已启动！输入 'quit' 退出，输入 'help' 显示帮助")
    print("可用命令：style, language, session, status, history")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n[You]: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n[Bye] Goodbye!")
                break

            if user_input.lower() == "help":
                print("\n[Help] Available commands:")
                print("  quit/exit/q    - 退出对话")
                print("  clear          - 清空上下文")
                print("  help           - 显示帮助信息")
                print("  style <风格>    - 切换写作风格 (professional, casual, academic, creative)")
                print("  language <语言> - 切换语言 (zh, en)")
                print("  session [id]   - 查看/切换 Session")
                print("  status         - 显示当前写作状态")
                print("  history        - 显示消息历史")
                continue

            if user_input.lower() == "clear":
                agent.reset_state()
                print("\n[Clear] Context cleared")
                continue

            # 切换写作风格
            if user_input.lower().startswith("style "):
                new_style = user_input[6:].strip()
                agent.style = new_style
                print(f"\n[Style] 写作风格已切换为：{new_style}")
                continue

            # 切换语言
            if user_input.lower().startswith("language "):
                new_lang = user_input[9:].strip()
                if new_lang in ["zh", "en"]:
                    agent.language = new_lang
                    # 清除 prompt 缓存以重新加载
                    get_prompt_manager().clear_cache("writer")
                    print(f"\n[Language] 语言已切换为：{new_lang}")
                else:
                    print("\n[Error] 不支持的语言，请使用 zh 或 en")
                continue

            # Session 管理
            if user_input.lower().startswith("session"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    # 切换 Session
                    session_id = parts[1]
                    if session_manager.switch_session(session_id):
                        print(f"\n[Session] 已切换到 Session: {session_id}")
                    else:
                        print(f"\n[Error] Session 不存在：{session_id}")
                else:
                    # 查看当前 Session
                    if session_manager.current_session:
                        s = session_manager.current_session
                        print(f"\n[Session] 当前 Session:")
                        print(f"  ID: {s.session_id}")
                        print(f"  消息数：{len(s.message_history)}")
                        print(f"  版本数：{len(s.versions)}")
                    else:
                        print("\n[Session] 当前没有活动 Session")
                continue

            # 显示状态
            if user_input.lower() == "status":
                if agent.get_current_state():
                    state = agent.get_current_state()
                    print(f"\n[Status] 当前写作状态:")
                    print(f"  主题：{state.request.topic}")
                    print(f"  阶段：{state.current_stage}")
                    print(f"  大纲：{len(state.outline)} 条")
                    print(f"  草稿章节：{len(state.draft_sections)} 条")
                else:
                    print("\n[Status] 没有活动的写作任务")
                continue

            # 显示历史
            if user_input.lower() == "history":
                history = session_manager.get_message_history(5)
                if history:
                    print(f"\n[History] 最近消息:")
                    for msg in history:
                        print(f"  [{msg['role']}] {msg['content'][:50]}...")
                else:
                    print("\n[History] 没有消息历史")
                continue

            print("\n[WriterAgent] Thinking...")
            # 使用 WritingRequest 执行
            request = WritingRequest(
                topic=user_input[:50],
                style=agent.style,
                language=agent.language,
            )
            response = await agent.execute(user_input, request=request)

            if response.success:
                print(f"\n[WriterAgent]:\n{response.content}")
            else:
                print(f"\n[Error]: {response.error}")

        except KeyboardInterrupt:
            print("\n\n[Interrupt] Exiting")
            break
        except EOFError:
            print("\n\n[Bye] Goodbye!")
            break


async def main():
    await chat_test()


if __name__ == "__main__":
    asyncio.run(main())
