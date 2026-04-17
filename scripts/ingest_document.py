"""
临时脚本 - 喂文档进向量知识库 (Test Script)
用于将文档导入到向量知识库中

用法:
    python scripts/ingest_document.py <文件路径> [--kb-name <知识库名称>]

示例:
    python scripts/ingest_document.py "data/temp/truncated_《诡秘之主》作者：爱潜水的乌贼.txt" --kb-name guimizhizhu
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.rag.service import RAGService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IngestDocument")


async def ingest_document(file_path: str, kb_name: str = None):
    """
    将文档导入到向量知识库

    Args:
        file_path: 文档路径
        kb_name: 知识库名称，默认为文件名（不含扩展名）
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        logger.error(f"文件不存在: {file_path}")
        return False

    # 如果没有指定知识库名称，使用文件名（不含扩展名）
    if kb_name is None:
        kb_name = file_path_obj.stem
        # 清理文件名，移除特殊字符
        import re
        kb_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', kb_name)[:50]

    logger.info(f"开始导入文档: {file_path}")
    logger.info(f"目标知识库: {kb_name}")

    # 创建 RAG 服务
    rag_service = RAGService()

    # 定义进度回调
    def on_progress(stage: str, progress: float):
        percentage = progress * 100
        logger.info(f"进度 [{stage}]: {percentage:.1f}%")

    try:
        # 初始化知识库
        success = await rag_service.initialize_kb(
            kb_name=kb_name,
            file_paths=[str(file_path)],
            progress_callback=on_progress,
        )

        if success:
            logger.info(f"✅ 文档导入成功！知识库 '{kb_name}' 已创建")

            # 显示知识库信息
            kb_info = rag_service.get_kb_info(kb_name)
            if kb_info:
                logger.info(f"知识库信息: {kb_info}")

            return True
        else:
            logger.error("❌ 文档导入失败")
            return False

    except Exception as e:
        logger.error(f"导入过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    parser = argparse.ArgumentParser(
        description="将文档导入到向量知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/ingest_document.py "data/temp/truncated_《诡秘之主》作者：爱潜水的乌贼.txt"
    python scripts/ingest_document.py "docs/mybook.txt" --kb-name my_knowledge_base
        """
    )

    parser.add_argument(
        "file_path",
        help="要导入的文档路径"
    )

    parser.add_argument(
        "--kb-name",
        dest="kb_name",
        default=None,
        help="知识库名称（默认为文件名）"
    )

    args = parser.parse_args()

    # 运行异步任务
    result = asyncio.run(ingest_document(args.file_path, args.kb_name))

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
