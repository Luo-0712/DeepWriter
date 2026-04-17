import asyncio
from typing import Dict, List


class SSEManager:
    """SSE 连接管理器"""

    def __init__(self):
        self._subscriptions: Dict[str, List[asyncio.Queue]] = {}

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """订阅频道"""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        queue = asyncio.Queue()
        self._subscriptions[channel].append(queue)
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """取消订阅"""
        if channel in self._subscriptions:
            if queue in self._subscriptions[channel]:
                self._subscriptions[channel].remove(queue)

    async def publish(self, channel: str, message: dict):
        """发布消息到频道"""
        if channel in self._subscriptions:
            for queue in self._subscriptions[channel]:
                await queue.put(message)


# 全局实例
sse_manager = SSEManager()
