from services.session_service import get_session_service as _get_session_service
from services.message_service import get_message_service as _get_message_service
from services.document_service import get_document_service as _get_document_service
from services.writing_task_service import get_writing_task_service as _get_writing_task_service


def get_session_service():
    return _get_session_service()


def get_message_service():
    return _get_message_service()


def get_document_service():
    return _get_document_service()


def get_task_service():
    return _get_writing_task_service()
