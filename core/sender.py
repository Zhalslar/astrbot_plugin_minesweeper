from pathlib import Path

import botpy.message
from botpy.http import Route

from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.core.message.components import Image
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.platform.sources.qqofficial.qqofficial_message_event import (
    QQOfficialMessageEvent,
)


class MessageSender:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self._last_message_id: dict[str, str | int] = {}

    @staticmethod
    def _make_key(event: AstrMessageEvent) -> str:
        return f"{event.unified_msg_origin}:{event.get_sender_id()}"

    @staticmethod
    async def _send_msg(event: AiocqhttpMessageEvent, payloads: dict) -> int | None:
        """Send a message through OneBot and return its message ID."""
        if event.is_private_chat():
            payloads["user_id"] = event.get_sender_id()
            result = await event.bot.api.call_action("send_private_msg", **payloads)
        else:
            payloads["group_id"] = event.get_group_id()
            result = await event.bot.api.call_action("send_group_msg", **payloads)

        return result.get("message_id")

    def save_cache(self, event: AstrMessageEvent, img_bytes: bytes) -> str:
        """save cache"""
        key = self._make_key(event).replace(":", "_")
        image_path = self.cache_dir / f"{key}.png"
        image_path.write_bytes(img_bytes)
        return str(image_path.absolute())

    async def _recall_qqofficial_message(
        self, event: QQOfficialMessageEvent, message_id: str
    ) -> None:
        """Recall a message through the QQ Official API"""
        source = event.message_obj.raw_message
        route_path = None
        route_params = {}

        if isinstance(source, botpy.message.GroupMessage):
            route_path = "/v2/groups/{group_openid}/messages/{message_id}"
            route_params["group_openid"] = source.group_openid
        elif isinstance(source, botpy.message.C2CMessage):
            route_path = "/v2/users/{openid}/messages/{message_id}"
            route_params["openid"] = source.author.user_openid
        elif isinstance(source, botpy.message.DirectMessage):
            route_path = "/dms/{guild_id}/messages/{message_id}"
            route_params["guild_id"] = source.guild_id
        elif isinstance(source, botpy.message.Message):
            await event.bot.api.recall_message(
                channel_id=source.channel_id,
                message_id=message_id,
            )
            return

        if route_path:
            await event.bot.api._http.request(
                Route(
                    "DELETE",
                    route_path,
                    message_id=message_id,
                    **route_params,
                )
            )

    async def _recall_last_message(self, event: AstrMessageEvent):
        """Recall the last image sent for this session and sender when supported."""
        key = self._make_key(event)
        last_message_id = self._last_message_id.get(key)
        if not last_message_id:
            return

        try:
            if isinstance(event, AiocqhttpMessageEvent):
                await event.bot.delete_msg(message_id=int(last_message_id))
            elif isinstance(event, QQOfficialMessageEvent):
                await self._recall_qqofficial_message(event, str(last_message_id))
        except Exception:
            pass
        finally:
            self._last_message_id.pop(key, None)

    async def send_img_replace_last(self, event: AstrMessageEvent, image_path: str):
        """Send an image and replace the previous image for this session and sender."""
        key = self._make_key(event)
        message_id: str | int | None = None

        if isinstance(event, AiocqhttpMessageEvent):
            payloads = {"message": [{"type": "image", "data": {"file": image_path}}]}
            message_id = await self._send_msg(event, payloads)
        elif isinstance(event, QQOfficialMessageEvent):
            platform = getattr(event.bot, "platform", None)
            if platform is None:
                return
            message_chain = MessageChain([Image.fromFileSystem(image_path)])
            await platform.send_by_session(event.session, message_chain)
            message_id = getattr(platform, "_session_last_message_id", {}).get(
                event.session_id
            )
        else:
            message_chain = MessageChain([Image.fromFileSystem(image_path)])
            await event.send(message_chain)
            return

        await self._recall_last_message(event)
        if message_id:
            self._last_message_id[key] = message_id
