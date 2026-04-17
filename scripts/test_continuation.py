"""
测试脚本 - 网文续写对比测试
对比有/无知识库检索时大模型的续写效果
"""

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.messages import HumanMessage, SystemMessage
from llm.factory import create_llm
from services.rag.service import RAGService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ContinuationTest")

WEB_NOVEL_PROMPT = """你是一位资深的网络小说作家，擅长创作西方奇幻风格的网文。

你的写作风格特点：
1. **克苏鲁+蒸汽朋克风格**：融合神秘、诡异、机械与魔法的元素
2. **细腻的心理描写**：深入刻画角色的内心活动和情绪变化
3. **生活化的细节**：注重日常生活场景的描绘，让虚构世界有真实感
4. **悬念的铺设**：在平静的日常中暗藏伏笔和危机
5. **对话自然**：人物对话符合身份和性格，幽默与严肃并存

写作要求：
- 保持与原作风调一致，使用中文全角标点
- 段落开头使用全角空格缩进
- 注重场景氛围的营造
- 适当加入角色的内心独白
- 在温馨日常中隐约透露世界观设定

请根据提供的上下文，续写下一章内容，字数控制在1500-2000字左右。"""

CONTINUATION_PROMPT = '''请续写《诡秘之主》第二十七章"兄妹三人的晚餐"的后续内容。

前文概要：
克莱恩·莫雷蒂刚刚获得了值夜者的工作，周薪3镑。他回到家中，与哥哥班森和妹妹梅丽莎相聚。班森刚刚出差回来，三人准备一起庆祝克莱恩找到新工作。

前文最后一段：
　　班森嘴角上翘，一本正经地补充道：
　　"你应该明白，要制定一个合理又简单的币制需要一个前提，那就是懂得数数，掌握了十进制，可惜，在那些大人物里面，这样的人才太稀少了。"

需要续写的内容：
描写兄妹三人准备晚餐、用餐的过程，展现莫雷蒂家庭的温馨氛围，同时体现这个家庭的经济状况和成员性格。可以适当加入一些关于值夜者工作的伏笔，但不要过于明显。

请直接输出续写内容，从"第二十七章 兄妹三人的晚餐"的后续开始写。'''


async def test_without_kb():
    """无知识库检索的续写"""
    logger.info("=" * 60)
    logger.info("【测试1】无知识库检索的续写")
    logger.info("=" * 60)

    llm = create_llm()
    messages = [
        SystemMessage(content=WEB_NOVEL_PROMPT),
        HumanMessage(content=CONTINUATION_PROMPT),
    ]

    logger.info("正在调用大模型（无知识库）...")
    try:
        response = await llm.ainvoke(messages)
        result = response.content
        logger.info(f"✅ 生成完成，字数：约 {len(result)} 字")
        return result
    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        return None


async def test_with_kb():
    """有知识库检索的续写"""
    logger.info("=" * 60)
    logger.info("【测试2】有知识库检索的续写")
    logger.info("=" * 60)

    rag_service = RAGService()
    query = "莫雷蒂家庭 兄妹 晚餐 班森 梅丽莎 克莱恩 家庭经济 日常生活"

    logger.info(f"正在检索知识库...")
    try:
        search_result = await rag_service.search(
            query=query,
            kb_name="guimizhizhu",
            top_k=5
        )

        context = search_result.content if search_result.content else "无相关上下文"
        logger.info(f"检索到 {len(search_result.chunks)} 个相关片段")

        enhanced_prompt = f"""{CONTINUATION_PROMPT}

【参考上下文】（来自原文的知识库检索结果）：
{context}

请根据以上参考上下文，保持与原作一致的设定和风格进行续写。"""

        llm = create_llm()
        messages = [
            SystemMessage(content=WEB_NOVEL_PROMPT),
            HumanMessage(content=enhanced_prompt),
        ]

        logger.info("正在调用大模型（带知识库上下文）...")
        response = await llm.ainvoke(messages)
        result = response.content
        logger.info(f"✅ 生成完成，字数：约 {len(result)} 字")
        return result, context

    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None


async def main():
    logger.info("\n" + "=" * 60)
    logger.info("《诡秘之主》续写对比测试")
    logger.info("=" * 60)

    # 测试1：无知识库
    result_without_kb = await test_without_kb()

    print("\n" + "=" * 60)
    print("【无知识库续写结果】")
    print("=" * 60)
    print(result_without_kb if result_without_kb else "生成失败")
    print("\n\n")

    # 测试2：有知识库
    result_with_kb, context = await test_with_kb()

    print("\n" + "=" * 60)
    print("【检索到的知识库内容】")
    print("=" * 60)
    print(context[:1500] + "..." if context and len(context) > 1500 else context)
    print("\n\n")

    print("=" * 60)
    print("【有知识库续写结果】")
    print("=" * 60)
    print(result_with_kb if result_with_kb else "生成失败")

    # 保存结果
    output_dir = Path(project_root) / "data" / "temp"
    output_dir.mkdir(parents=True, exist_ok=True)

    if result_without_kb:
        with open(output_dir / "result_no_kb.txt", "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n无知识库检索续写\n" + "=" * 60 + "\n\n")
            f.write(result_without_kb)
        logger.info(f"✅ 无知识库结果已保存")

    if result_with_kb:
        with open(output_dir / "result_with_kb.txt", "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n有知识库检索续写\n" + "=" * 60 + "\n\n")
            f.write("【检索上下文】\n" + (context or "无") + "\n\n")
            f.write("=" * 60 + "\n【续写内容】\n" + "=" * 60 + "\n\n")
            f.write(result_with_kb)
        logger.info(f"✅ 有知识库结果已保存")

    logger.info("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
