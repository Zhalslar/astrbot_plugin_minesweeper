from pathlib import Path

from astrbot.api.event import AstrMessageEvent
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import Image
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


class ImageService:
    """
    图片缓存与发送服务
    - 管理临时图片缓存
    - 支持消息替换发送（撤回上一条后发送新图）
    """

    def __init__(self, config: AstrBotConfig, cache_dir: Path):
        self.config = config
        self.cache_dir = cache_dir
        self._last_message_id: dict[str, int] = {}

    def save_cache(self, event: AstrMessageEvent, img_bytes: bytes) -> str:
        """保存图片到缓存目录，返回绝对路径"""
        sid = event.session_id
        uid = event.get_sender_id()
        fname = f"{sid}_{uid}.png"
        fpath = self.cache_dir / fname
        fpath.write_bytes(img_bytes)
        return str(fpath.absolute())

    @staticmethod
    def _make_key(event: AiocqhttpMessageEvent) -> str:
        return f"{event.session_id}:{event.get_sender_id()}"

    @staticmethod
    async def _send_msg(event: AiocqhttpMessageEvent, payloads: dict) -> int | None:
        if event.is_private_chat():
            payloads["user_id"] = event.get_sender_id()
            result = await event.bot.api.call_action("send_private_msg", **payloads)
        else:
            payloads["group_id"] = event.get_group_id()
            result = await event.bot.api.call_action("send_group_msg", **payloads)
        return result.get("message_id")

    async def _recall_last_message(self, event: AiocqhttpMessageEvent):
        key = self._make_key(event)
        last_message_id = self._last_message_id.get(key)
        if not last_message_id:
            return
        try:
            await event.bot.delete_msg(message_id=last_message_id)
        except Exception:
            pass
        finally:
            self._last_message_id.pop(key, None)

    async def send_with_replace(self, event: AstrMessageEvent, image_path: str):
        """发送图片并替换（撤回上一条后发送新图）"""
        if not isinstance(event, AiocqhttpMessageEvent):
            await event.send(event.chain_result([Image.fromFileSystem(image_path)]))
            return

        # 先撤回上一条消息
        await self._recall_last_message(event)

        # 再发送新图片
        payloads = {
            "message": [{"type": "image", "data": {"file": f"file://{image_path}"}}]
        }
        message_id = await self._send_msg(event, payloads)
        if message_id:
            key = self._make_key(event)
            self._last_message_id[key] = message_id
