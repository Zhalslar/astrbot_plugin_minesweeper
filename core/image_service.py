import base64
from pathlib import Path

from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import Image
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


class ImageService:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self._last_message_id: dict[str, int] = {}

    def save_cache(self, event: AstrMessageEvent, img_bytes: bytes) -> str:
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
        if not isinstance(event, AiocqhttpMessageEvent):
            await event.send(event.chain_result([Image.fromFileSystem(image_path)]))
            return
        await self._recall_last_message(event)
        image_file = Path(image_path)
        image_bytes = image_file.read_bytes()
        image_b64_bytes = base64.b64encode(image_bytes)
        image_b64_str = str(image_b64_bytes, "utf-8")
        payloads = {
            "message": [
                {"type": "image", "data": {"file": f"base64://{image_b64_str}"}}
            ]
        }
        message_id = await self._send_msg(event, payloads)
        if message_id:
            key = self._make_key(event)
            self._last_message_id[key] = message_id
