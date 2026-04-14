"""
DeepWriter 数据持久化层使用示例

展示如何使用新创建的会话、消息、文档和任务服务。
"""

from db.database import get_db
from services import (
    get_document_service,
    get_message_service,
    get_session_service,
    get_writing_task_service,
)


def main():
    """主示例函数"""
    # 初始化数据库
    db = get_db()
    db.init_tables()
    print("数据库已初始化\n")

    # 获取服务实例
    session_service = get_session_service()
    message_service = get_message_service()
    document_service = get_document_service()
    task_service = get_writing_task_service()

    # ========== 1. 创建会话 ==========
    print("=" * 50)
    print("1. 创建会话")
    print("=" * 50)

    session = session_service.create_session(
        user_id="user_001",
        title="AI写作助手会话",
        config={"language": "zh", "style": "professional"},
    )
    print(f"创建会话: ID={session.id}, 标题={session.title}")

    # ========== 2. 添加消息 ==========
    print("\n" + "=" * 50)
    print("2. 添加消息")
    print("=" * 50)

    message_service.add_user_message(
        session.id,
        "请帮我写一篇关于人工智能的文章",
        metadata={"intent": "writing_request"},
    )
    message_service.add_assistant_message(
        session.id,
        "好的！请告诉我您希望文章涵盖哪些方面？比如：AI的历史、当前应用、未来发展等。",
    )
    message_service.add_user_message(
        session.id,
        "重点写AI在医疗领域的应用",
    )

    # 获取聊天历史
    history = message_service.get_chat_history(session.id)
    print(f"已添加 {len(history)} 条消息")
    for msg in history:
        print(f"  [{msg['role']}] {msg['content'][:30]}...")

    # ========== 3. 创建文档 ==========
    print("\n" + "=" * 50)
    print("3. 创建文档")
    print("=" * 50)

    document = document_service.create_document(
        session_id=session.id,
        title="AI在医疗领域的应用",
        content="# AI在医疗领域的应用\n\n人工智能正在改变医疗行业...",
        doc_type="article",
        metadata={"topic": "AI医疗", "word_count": 0},
    )
    print(f"创建文档: ID={document.id}")
    print(f"标题: {document.title}")
    print(f"类型: {document.doc_type}")

    # ========== 4. 更新文档并创建版本 ==========
    print("\n" + "=" * 50)
    print("4. 更新文档并创建版本")
    print("=" * 50)

    # 第一次更新
    document_service.update_content(
        document.id,
        "# AI在医疗领域的应用\n\n人工智能正在改变医疗行业。\n\n## 1. 医学影像诊断\nAI可以帮助医生更准确地识别病灶...",
        create_version=True,
    )
    print("更新文档内容（创建版本）")

    # 第二次更新
    document_service.update_content(
        document.id,
        "# AI在医疗领域的应用\n\n人工智能正在改变医疗行业。\n\n## 1. 医学影像诊断\nAI可以帮助医生更准确地识别病灶...\n\n## 2. 药物研发\nAI加速新药发现过程...",
        create_version=True,
    )
    print("再次更新文档内容（创建版本）")

    # 查看版本
    versions = document_service.get_document_versions(document.id)
    print(f"\n文档共有 {len(versions)} 个版本:")
    for v in versions:
        print(f"  版本 {v.version}: {v.change_summary} ({v.created_at.strftime('%H:%M:%S')})")

    # ========== 5. 创建写作任务 ==========
    print("\n" + "=" * 50)
    print("5. 创建写作任务")
    print("=" * 50)

    task = task_service.create_task(
        session_id=session.id,
        task_type="article",
        topic="AI在医疗领域的应用",
        request={
            "tone": "professional",
            "length": "long",
            "sections": ["医学影像", "药物研发", "个性化治疗"],
        },
        document_id=document.id,
    )
    print(f"创建任务: ID={task.id}")
    print(f"主题: {task.topic}")
    print(f"状态: {task.status}")

    # 模拟任务执行
    print("\n模拟任务执行...")
    task_service.start_task(task.id)
    print(f"任务状态更新为: running")

    # 更新任务状态
    task_service.update_task_state(
        task.id,
        {"current_stage": "writing", "progress": 50},
    )

    # 完成任务
    task_service.complete_task(
        task.id,
        result="文章已完成，包含医学影像、药物研发和个性化治疗三个部分。",
    )
    print(f"任务完成!")

    # ========== 6. 查看会话统计 ==========
    print("\n" + "=" * 50)
    print("6. 查看会话统计")
    print("=" * 50)

    stats = session_service.get_session_stats(session.id)
    print(f"会话 ID: {stats['session_id']}")
    print(f"消息数量: {stats['message_count']}")
    print(f"文档数量: {stats['document_count']}")
    print(f"任务数量: {stats['task_count']}")

    # ========== 7. 列出所有会话 ==========
    print("\n" + "=" * 50)
    print("7. 列出所有会话")
    print("=" * 50)

    all_sessions = session_service.list_all_sessions(limit=10)
    print(f"共有 {len(all_sessions)} 个会话:")
    for s in all_sessions:
        print(f"  - {s.title} (ID: {s.id[:8]}..., 状态: {s.status})")

    # ========== 8. 版本回滚示例 ==========
    print("\n" + "=" * 50)
    print("8. 版本回滚示例")
    print("=" * 50)

    # 恢复到第一个版本
    restored_doc = document_service.restore_version(document.id, version_number=1)
    if restored_doc:
        print(f"文档已恢复到版本 1")
        print(f"当前内容长度: {len(restored_doc.content)} 字符")

    # 查看恢复后的版本
    versions_after_restore = document_service.get_document_versions(document.id)
    print(f"恢复后共有 {len(versions_after_restore)} 个版本")

    print("\n" + "=" * 50)
    print("示例完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
