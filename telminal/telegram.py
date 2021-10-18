import contextlib
import os

from telethon import TelegramClient


class Telegram:
    # upload limitaion at this moment > 2GB
    UPLOAD_LIMIT = 2147483648

    def __init__(
        self, *, api_id: int, api_hash: str, token: str, session_name: str = "telminal"
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._token = token
        self.session_name = session_name
        self._remove_old_sessions()
        self.client = TelegramClient(session_name, api_id, api_hash)

    def _remove_old_sessions(self) -> None:
        # an easy way to handle session db lock error
        with contextlib.suppress(FileNotFoundError):
            os.remove(f"{self.session_name}.session")
            os.remove(f"{self.session_name}.session-journal")

    async def start(self, handlers: dict):
        await self.client.start(bot_token=self._token)
        for handler, type_ in handlers.items():
            self.client.add_event_handler(handler, type_)
        await self.client.run_until_disconnected()

    async def send_file(self, file, reply_to=None):
        error = None
        if not os.path.isfile(file):
            error = f"{file} is not a file"
        elif os.path.getsize(file) > Telegram.UPLOAD_LIMIT:
            error = "Sorry I can't send file bigger than 2G"

        if error is not None:
            return await self.client.send_message(
                self.chat_id, error, reply_to=reply_to
            )

        return await self.client.send_message(
            self.chat_id, file=file, force_document=True, reply_to=reply_to
        )

    async def send_message(self, message: str):
        return await self.client.send_message(self.chat_id, message, link_preview=False)

    async def edit_message(self, message: str, *, message_id: int):
        return await self.client.edit_message(
            self.chat_id, message=message_id, text=message, link_preview=False
        )
