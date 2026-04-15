"""
服务层CRUD测试

测试所有服务的完整CRUD操作流程。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.database import get_db
from services import (
    get_document_service,
    get_message_service,
    get_session_service,
    get_writing_task_service,
)


def test_session_service_crud():
    """测试会话服务CRUD"""
    print("\n" + "=" * 60)
    print("测试 SessionService CRUD")
    print("=" * 60)

    service = get_session_service()

    print("\n[1] Create - 创建会话")
    session = service.create_session(
        user_id="test_user_001",
        title="测试会话",
        config={"language": "zh", "theme": "dark"}
    )
    print(f"    创建成功: session_id={session.id}, title={session.title}")

    print("\n[2] Read - 读取会话")
    retrieved = service.get_session(session.id)
    print(f"    读取成功: title={retrieved.title}, status={retrieved.status}")

    print("\n[3] Update - 更新会话")
    service.update_session_title(session.id, "更新后的会话标题")
    updated = service.get_session(session.id)
    print(f"    更新成功: title={updated.title}")

    print("\n[4] List - 列出会话")
    sessions = service.list_all_sessions(limit=10)
    print(f"    当前会话总数: {len(sessions)}")

    print("\n[5] Delete - 删除会话")
    deleted = service.delete_session(session.id)
    print(f"    删除成功: {deleted}")

    print("\n[6] Verify Delete - 验证删除")
    verify = service.get_session(session.id)
    print(f"    验证结果: {verify is None}")

    return True


def test_message_service_crud():
    """测试消息服务CRUD"""
    print("\n" + "=" * 60)
    print("测试 MessageService CRUD")
    print("=" * 60)

    service = get_message_service()
    session_service = get_session_service()

    session = session_service.create_session(title="消息测试会话")
    print(f"    关联会话: {session.id}")

    print("\n[1] Create - 创建消息")
    msg1 = service.add_user_message(session.id, "第一用户消息")
    msg2 = service.add_assistant_message(session.id, "第一助手回复")
    msg3 = service.add_system_message(session.id, "系统提示")
    print(f"    创建成功: user_msg={msg1.id}, assistant_msg={msg2.id}, system_msg={msg3.id}")

    print("\n[2] Read - 读取消息")
    retrieved = service.get_message(msg1.id)
    print(f"    单条读取: id={retrieved.id}, role={retrieved.role}, content={retrieved.content}")

    print("\n[3] Read - 读取会话所有消息")
    messages = service.get_session_messages(session.id)
    print(f"    会话消息数: {len(messages)}")

    print("\n[4] Read - 读取最近消息")
    recent = service.get_recent_messages(session.id, limit=2)
    print(f"    最近2条: {[m.id for m in recent]}")

    print("\n[5] Read - 获取聊天历史")
    history = service.get_chat_history(session.id, limit=10)
    print(f"    聊天历史条数: {len(history)}")

    print("\n[6] Count - 统计消息")
    count = service.count_messages(session.id)
    print(f"    消息总数: {count}")

    print("\n[7] Update - 更新消息（通过创建新消息模拟）")
    new_msg = service.add_user_message(session.id, "更新的用户消息")
    print(f"    新消息: id={new_msg.id}")

    print("\n[8] Delete - 删除消息")
    deleted = service.delete_message(msg3.id)
    print(f"    删除消息: {deleted}")

    print("\n[9] Clear - 清空会话消息")
    cleared = service.clear_session_messages(session.id)
    print(f"    清空消息数: {cleared}")

    print("\n[10] Cleanup - 清理测试数据")
    session_service.delete_session(session.id)
    print(f"    清理完成")

    return True


def test_document_service_crud():
    """测试文档服务CRUD"""
    print("\n" + "=" * 60)
    print("测试 DocumentService CRUD")
    print("=" * 60)

    service = get_document_service()
    session_service = get_session_service()

    session = session_service.create_session(title="文档测试会话")
    print(f"    关联会话: {session.id}")

    print("\n[1] Create - 创建文档")
    doc = service.create_document(
        session_id=session.id,
        title="测试文档",
        content="这是初始文档内容",
        doc_type="article",
        metadata={"author": "test"}
    )
    print(f"    创建成功: doc_id={doc.id}, title={doc.title}")

    print("\n[2] Read - 读取文档")
    retrieved = service.get_document(doc.id)
    print(f"    读取成功: title={retrieved.title}, status={retrieved.status}")

    print("\n[3] Read - 读取会话的所有文档")
    docs = service.get_session_documents(session.id)
    print(f"    会话文档数: {len(docs)}")

    print("\n[4] Update - 更新文档标题和内容")
    updated = service.update_document(doc.id, title="更新后的标题", content="更新后的内容")
    print(f"    更新成功: title={updated.title}")

    print("\n[5] Update - 更新文档内容并创建版本")
    service.update_content(doc.id, "版本2内容", create_version=True)
    versions = service.get_document_versions(doc.id)
    print(f"    版本数量: {len(versions)}")

    print("\n[6] Read - 获取文档版本")
    latest = service.get_latest_version(doc.id)
    print(f"    最新版本: v{latest.version}, summary={latest.change_summary}")

    print("\n[7] Update - 发布文档")
    published = service.publish_document(doc.id)
    print(f"    发布成功: {published}")

    print("\n[8] Update - 归档文档")
    archived = service.archive_document(doc.id)
    print(f"    归档成功: {archived}")

    print("\n[9] Restore - 恢复版本")
    restored = service.restore_version(doc.id, 1)
    print(f"    恢复成功: title={restored.title if restored else None}")

    print("\n[10] Delete - 删除文档")
    deleted = service.delete_document(doc.id)
    print(f"    删除成功: {deleted}")

    print("\n[11] Cleanup - 清理测试数据")
    session_service.delete_session(session.id)
    print(f"    清理完成")

    return True


def test_writing_task_service_crud():
    """测试写作任务服务CRUD"""
    print("\n" + "=" * 60)
    print("测试 WritingTaskService CRUD")
    print("=" * 60)

    service = get_writing_task_service()
    session_service = get_session_service()
    doc_service = get_document_service()

    session = session_service.create_session(title="任务测试会话")
    doc = doc_service.create_document(session.id, "关联文档")
    print(f"    关联会话: {session.id}, 关联文档: {doc.id}")

    print("\n[1] Create - 创建任务")
    task = service.create_task(
        session_id=session.id,
        task_type="article",
        topic="AI写作测试",
        request={"tone": "professional"},
        document_id=doc.id
    )
    print(f"    创建成功: task_id={task.id}, status={task.status}")

    print("\n[2] Read - 读取任务")
    retrieved = service.get_task(task.id)
    print(f"    读取成功: topic={retrieved.topic}, status={retrieved.status}")

    print("\n[3] Read - 读取会话的所有任务")
    tasks = service.get_session_tasks(session.id)
    print(f"    会话任务数: {len(tasks)}")

    print("\n[4] Read - 读取文档的所有任务")
    doc_tasks = service.get_document_tasks(doc.id)
    print(f"    文档任务数: {len(doc_tasks)}")

    print("\n[5] Update - 开始任务")
    started = service.start_task(task.id)
    print(f"    开始成功: {started}")

    print("\n[6] Update - 更新任务状态")
    updated = service.update_task_state(task.id, {"progress": 50, "step": "writing"})
    print(f"    状态更新: state={updated.state if updated else None}")

    print("\n[7] Update - 完成任务")
    completed = service.complete_task(task.id, "写作任务完成，内容如下...")
    print(f"    任务完成: {completed}")

    print("\n[8] Read - 获取已完成任务列表")
    completed_tasks = service.list_completed_tasks()
    print(f"    已完成任务数: {len(completed_tasks)}")

    print("\n[9] Create - 创建新任务用于失败测试")
    failed_task = service.create_task(
        session_id=session.id,
        task_type="blog",
        topic="失败测试任务"
    )
    print(f"    创建失败任务: {failed_task.id}")

    print("\n[10] Update - 标记任务失败")
    failed = service.fail_task(failed_task.id, "测试错误信息")
    print(f"    标记失败: {failed}")

    print("\n[11] Read - 获取失败任务列表")
    failed_tasks = service.list_failed_tasks()
    print(f"    失败任务数: {len(failed_tasks)}")

    print("\n[12] Update - 重试失败任务")
    retried = service.retry_task(failed_task.id)
    print(f"    重试成功: new_task_id={retried.id if retried else None}")

    print("\n[13] Read - 获取待处理任务")
    pending_tasks = service.list_pending_tasks()
    print(f"    待处理任务数: {len(pending_tasks)}")

    print("\n[14] Read - 获取运行中任务")
    running_tasks = service.list_running_tasks()
    print(f"    运行中任务数: {len(running_tasks)}")

    print("\n[15] Read - 获取任务统计")
    stats = service.get_task_stats()
    print(f"    任务统计: {stats}")

    print("\n[16] Delete - 删除任务")
    deleted = service.delete_task(retried.id)
    print(f"    删除任务: {deleted}")

    print("\n[17] Cleanup - 清理测试数据")
    doc_service.delete_document(doc.id)
    session_service.delete_session(session.id)
    print(f"    清理完成")

    return True


def run_all_crud_tests():
    """运行所有CRUD测试"""
    print("\n" + "=" * 60)
    print("DeepWriter 服务层 CRUD 测试")
    print("=" * 60)

    db = get_db()
    db.init_tables()
    print("数据库初始化完成")

    results = []

    try:
        result = test_session_service_crud()
        results.append(("SessionService", result))
        print(f"\n>>> SessionService CRUD 测试通过")
    except Exception as e:
        results.append(("SessionService", False))
        print(f"\n!!! SessionService CRUD 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        result = test_message_service_crud()
        results.append(("MessageService", result))
        print(f"\n>>> MessageService CRUD 测试通过")
    except Exception as e:
        results.append(("MessageService", False))
        print(f"\n!!! MessageService CRUD 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        result = test_document_service_crud()
        results.append(("DocumentService", result))
        print(f"\n>>> DocumentService CRUD 测试通过")
    except Exception as e:
        results.append(("DocumentService", False))
        print(f"\n!!! DocumentService CRUD 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        result = test_writing_task_service_crud()
        results.append(("WritingTaskService", result))
        print(f"\n>>> WritingTaskService CRUD 测试通过")
    except Exception as e:
        results.append(("WritingTaskService", False))
        print(f"\n!!! WritingTaskService CRUD 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n*** 所有CRUD测试全部通过！")
    else:
        print(f"\n*** 有 {total - passed} 项测试失败")


if __name__ == "__main__":
    run_all_crud_tests()