from astrbot.api.event import AstrMessageEvent
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import Image
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


class MessageSender:
    """
    会话 + 用户级“覆盖发送”工具：
    - 同一会话 + 同一用户 只保留最后一条消息
    - 新消息发送时自动撤回上一条
    """

    def __init__(self, config: AstrBotConfig):
        self.config = config
        # key(session_id:uid) -> last message_id
        self._last_message_id: dict[str, int] = {}

    @staticmethod
    def _make_key(event: AiocqhttpMessageEvent) -> str:
        """
        umo + sender 作为唯一键
        """
        return f"{event.unified_msg_origin}:{event.get_sender_id()}"

    @staticmethod
    async def _send_msg(event: AiocqhttpMessageEvent, payloads: dict) -> int | None:
        """
        发送消息并返回 message_id
        """
        if event.is_private_chat():
            payloads["user_id"] = event.get_sender_id()
            result = await event.bot.api.call_action("send_private_msg", **payloads)
        else:
            payloads["group_id"] = event.get_group_id()
            result = await event.bot.api.call_action("send_group_msg", **payloads)

        return result.get("message_id")

    async def _recall_last_message(self, event: AiocqhttpMessageEvent):
        """
        撤回当前 session + 用户 上一次发送的消息（若存在）
        """
        key = self._make_key(event)
        last_message_id = self._last_message_id.get(key)

        if not last_message_id:
            return

        try:
            await event.bot.delete_msg(message_id=last_message_id)
        except Exception:
            # 已被撤回 / 超时 / 权限不足等情况，直接忽略
            pass
        finally:
            self._last_message_id.pop(key, None)

    async def send_img_replace_last(self, event: AstrMessageEvent, image_path: str):
        """
        发送图片，并撤回同 session + 同用户 上一次发送的消息
        """
        if not isinstance(event, AiocqhttpMessageEvent):
            await event.send(event.chain_result([Image.fromFileSystem(image_path)]))
            return
        payloads = {"message": [{"type": "image", "data": {"file": image_path}}]}
        message_id = await self._send_msg(event, payloads)

        await self._recall_last_message(event)

        # 3. 记录 message_id
        if message_id:
            key = self._make_key(event)
            self._last_message_id[key] = message_id
