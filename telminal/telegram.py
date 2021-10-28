import os

from telethon import TelegramClient
from telethon.hints import ProgressCallback

from . import utils


class Telegram:
    # upload limitaion at this moment > 2GB
    UPLOAD_LIMIT = 2147483648
    MEDIA_CAPTION_LIMIT = 1024
    INLINE_RESULT_LIMIT = 50

    def __init__(
        self, api_id: int, api_hash: str, token: str, session_name: str
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._token = token
        self.session_name = session_name
        self._remove_old_sessions()
        self._client = TelegramClient(session_name, api_id, api_hash)
        self._client.parse_mode = None

    def _remove_old_sessions(self) -> None:
        # an easy way to handle session db lock error
        utils.silent_file_remover(f"{self.session_name}.session")
        utils.silent_file_remover(f"{self.session_name}.session-journal")

    async def start(self, handlers: dict):
        await self._client.start(bot_token=self._token)
        for handler, type_ in handlers.items():
            self._client.add_event_handler(handler, type_)

    async def run_until_disconnected(self):
        await self._client.run_until_disconnected()

    async def send_message(
        self,
        chat_id: int,
        message: str,
        *,
        reply_to: int = None,
        buttons=None,
        file=None,
        parse_mode=None,
    ):
        return await self._client.send_message(
            chat_id,
            message,
            link_preview=False,
            reply_to=reply_to,
            buttons=buttons,
            file=file,
            parse_mode=parse_mode,
        )

    async def edit_message(
        self, chat_id, *, message_id: int, message=None, buttons=None, file=None
    ):
        return await self._client.edit_message(
            chat_id,
            message=message_id,
            text=message,
            link_preview=False,
            buttons=buttons,
            file=file,
        )

    async def send_file(
        self, chat_id: int, file: str, reply_to=None, progress_callback=None
    ):
        error = None
        if not os.path.isfile(file):
            error = f"{file} is not a file"
        elif os.path.getsize(file) > Telegram.UPLOAD_LIMIT:
            error = "Sorry I can't send file bigger than 2G"

        if error is not None:
            return await self._client.send_message(chat_id, error, reply_to=reply_to)

        return await self._client.send_file(
            chat_id,
            file=file,
            force_document=True,
            reply_to=reply_to,
            progress_callback=progress_callback,
        )

    async def get_message(self, chat_id, message_id: int):
        return await self._client.get_messages(chat_id, ids=message_id)

    async def download_media(self, message, *, progress_callback, file):
        await self._client.download_media(
            message, progress_callback=progress_callback, file=file
        )

    @staticmethod
    def media_strip(message: str):
        if len(message) >= Telegram.MEDIA_CAPTION_LIMIT:
            message = message[len(message) - Telegram.MEDIA_CAPTION_LIMIT :]
        return message.strip()
