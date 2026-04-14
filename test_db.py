"""
数据库测试脚本

测试数据持久化层的各项功能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.database import get_db
from db.models import Document, DocumentVersion, Message, Session, WritingTask
from db.repositories import (
    DocumentRepository,
    DocumentVersionRepository,
    MessageRepository,
    SessionRepository,
    WritingTaskRepository,
)
from services import (
    get_document_service,
    get_message_service,
    get_session_service,
    get_writing_task_service,
)


def test_session_repository():
    """测试会话仓库"""
    print("\n=== 测试 SessionRepository ===")
    db = get_db()
    repo = SessionRepository(db)

    # 创建会话
    session = Session(title="测试会话", user_id="user_001")
    session = repo.create(session)
    print(f"创建会话: {session.id}")

    # 查询会话
    found = repo.get_by_id(session.id)
    print(f"查询会话: {found.title if found else 'Not found'}")

    # 更新会话
    session.title = "更新后的标题"
    repo.update(session)
    updated = repo.get_by_id(session.id)
    print(f"更新会话: {updated.title if updated else 'Not found'}")

    # 列出会话
    sessions = repo.list_all(limit=10)
    print(f"会话数量: {len(sessions)}")

    return session.id


def test_message_repository(session_id: str):
    """测试消息仓库"""
    print("\n=== 测试 MessageRepository ===")
    db = get_db()
    repo = MessageRepository(db)

    # 创建消息
    msg1 = repo.create(Message(session_id=session_id, role="user", content="你好"))
    msg2 = repo.create(Message(session_id=session_id, role="assistant", content="你好！有什么可以帮助你？"))
    print(f"创建消息: user={msg1.id}, assistant={msg2.id}")

    # 查询消息
    messages = repo.get_by_session_id(session_id)
    print(f"会话消息数量: {len(messages)}")

    # 获取最近消息
    recent = repo.get_recent_by_session_id(session_id, limit=5)
    print(f"最近消息: {len(recent)}")

    # 统计消息
    count = repo.count_by_session_id(session_id)
    print(f"消息统计: {count}")


def test_document_repository(session_id: str):
    """测试文档仓库"""
    print("\n=== 测试 DocumentRepository ===")
    db = get_db()
    repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)

    # 创建文档
    doc = Document(
        session_id=session_id,
        title="测试文档",
        content="这是文档内容",
        doc_type="article",
    )
    doc = repo.create(doc)
    print(f"创建文档: {doc.id}")

    # 创建版本
    version = version_repo.create(
        DocumentVersion(
            document_id=doc.id,
            version=1,
            title=doc.title,
            content=doc.content,
            change_summary="初始版本",
        )
    )
    print(f"创建版本: {version.id}")

    # 更新文档
    doc.content = "更新后的内容"
    repo.update(doc)
    updated = repo.get_by_id(doc.id)
    print(f"更新文档: {updated.content if updated else 'Not found'}")

    # 查询版本
    versions = version_repo.get_by_document_id(doc.id)
    print(f"文档版本数量: {len(versions)}")

    return doc.id


def test_writing_task_repository(session_id: str, document_id: str):
    """测试写作任务仓库"""
    print("\n=== 测试 WritingTaskRepository ===")
    db = get_db()
    repo = WritingTaskRepository(db)

    # 创建任务
    task = WritingTask(
        session_id=session_id,
        document_id=document_id,
        task_type="article",
        topic="AI写作",
        request={"tone": "professional", "length": "medium"},
    )
    task = repo.create(task)
    print(f"创建任务: {task.id}")

    # 更新状态
    repo.update_status(task.id, "running")
    updated = repo.get_by_id(task.id)
    print(f"任务状态: {updated.status if updated else 'Not found'}")

    # 完成任务
    repo.complete_task(task.id, "这是写作结果...")
    completed = repo.get_by_id(task.id)
    print(f"任务完成: {completed.status if completed else 'Not found'}")

    # 列出任务
    tasks = repo.get_by_session_id(session_id)
    print(f"会话任务数量: {len(tasks)}")


def test_services():
    """测试服务层"""
    print("\n=== 测试 Services ===")

    # 会话服务
    session_service = get_session_service()
    session = session_service.create_session(user_id="user_001", title="服务测试会话")
    print(f"创建会话: {session.id}")

    # 消息服务
    message_service = get_message_service()
    msg1 = message_service.add_user_message(session.id, "请帮我写一篇文章")
    msg2 = message_service.add_assistant_message(session.id, "好的，请告诉我主题")
    print(f"创建消息: {msg1.id}, {msg2.id}")

    # 获取聊天历史
    history = message_service.get_chat_history(session.id)
    print(f"聊天历史: {len(history)} 条")

    # 文档服务
    document_service = get_document_service()
    doc = document_service.create_document(
        session_id=session.id,
        title="服务测试文档",
        content="初始内容",
    )
    print(f"创建文档: {doc.id}")

    # 更新文档并创建版本
    document_service.update_content(doc.id, "更新后的内容", create_version=True)
    versions = document_service.get_document_versions(doc.id)
    print(f"文档版本: {len(versions)}")

    # 写作任务服务
    task_service = get_writing_task_service()
    task = task_service.create_task(
        session_id=session.id,
        task_type="article",
        topic="AI技术",
        document_id=doc.id,
    )
    print(f"创建任务: {task.id}")

    task_service.start_task(task.id)
    task_service.complete_task(task.id, "写作完成！")
    completed = task_service.get_task(task.id)
    print(f"任务状态: {completed.status if completed else 'Not found'}")

    # 获取会话统计
    stats = session_service.get_session_stats(session.id)
    print(f"会话统计: {stats}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("DeepWriter 数据库测试")
    print("=" * 50)

    # 初始化数据库
    db = get_db()
    db.init_tables()
    print("\n数据库已初始化")

    try:
        # 测试仓库层
        session_id = test_session_repository()
        test_message_repository(session_id)
        doc_id = test_document_repository(session_id)
        test_writing_task_repository(session_id, doc_id)

        # 测试服务层
        test_services()

        print("\n" + "=" * 50)
        print("所有测试通过！")
        print("=" * 50)

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
