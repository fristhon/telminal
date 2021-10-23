import asyncio
from io import StringIO
from time import time

import pexpect
from pexpect.exceptions import EOF
from pexpect.exceptions import TIMEOUT

from .telegram import Telegram


class TProcess:
    def __init__(self, command: str, request_id: int) -> None:
        self.command = command
        self.request_id = request_id
        self._buffer = StringIO()
        self.is_running = None
        self.is_partial = None
        self.start_time = None
        self.run_time = 0
        self._new_data = None
        self.response_id = None
        self._last_message = ""

    def run(self) -> None:
        self._process = pexpect.spawn("/bin/bash", ["-c", self.command], timeout=None)
        self.pid = self._process.pid
        self.is_running = True
        self.start_time = time()
        asyncio.create_task(self.stream())

    def done(self):
        self.is_running = False

    def terminate(self):
        self._process.terminate()
        self.done()

    async def stream(self) -> None:
        while True:
            try:
                line = self._process.read_nonblocking(size=1000, timeout=0)
                self._buffer.write(line.decode("utf-8"))
                self._new_data = True
            except EOF:
                self.done()
                break
            except TIMEOUT:
                pass
            finally:
                self.run_time = int(time() - self.start_time)
                await asyncio.sleep(00.1)

    @property
    def full_output(self) -> str:
        self._buffer.seek(0)
        return self._buffer.read()

    @property
    def last_message(self):
        return self._last_message

    @last_message.setter
    def last_message(self, last_message: str):
        self._last_message = last_message
        self._new_data = False

    def terminate(self):
        self._process.terminate()
        self.done()


class Telminal:
    all_process = {}

    def __init__(
        self, *, api_id: int, api_hash: str, token: str, session_name: str = "telminal"
    ) -> None:
        self.interactive_process = None
        self.bot = Telegram(api_id, api_hash, token, session_name)

    async def start(self):
        # TODO bad coupling
        from telethon import events

        handlers = {
            self.all_messages_handler: events.NewMessage(incoming=True),
            self.terminate_handler: events.CallbackQuery(pattern=r"terminate&\d+"),
        }
        await self.bot.start(handlers)

    def new_process(self, command: str, request_id: int) -> TProcess:
        process = TProcess(command, request_id)
        process.run()
        return process

    async def all_messages_handler(self, event):
        self.bot.chat_id = event.chat_id  # TODO
        command: str = event.message.message
        process = self.new_process(command, event.message.id)
        # TODO better?
        Telminal.all_process[process.pid] = process

        asyncio.shield(self.run_in_background(process))

    async def terminate_handler(self, event):
        pid = int(event.data.decode().split("&")[-1])
        process = Telminal.find_process_by_id(pid)
        process.terminate()

    def get_buttons(self, process):
        from telethon import Button

        if process.is_running:
            return [[Button.inline("terminate", data=f"terminate&{process.pid}")]]

    async def response(self, process: TProcess):
        result = process.full_output
        # handle telegram caption limit
        if len(result) >= Telegram.MEDIA_CAPTION_LIMIT:
            result = result[len(result) - Telegram.MEDIA_CAPTION_LIMIT :]

        # there is no output for commands like `touch`
        # telegram api raise an error for no changes edit
        if not result or process.last_message == result:
            return

        buttons = self.get_buttons(process)
        if process.is_partial:
            await self.bot.edit_message(
                result, message_id=process.response_id, buttons=buttons
            )
        else:
            process.response_id = (
                await self.bot.send_message(
                    result, reply_to=process.request_id, buttons=buttons
                )
            ).id
            process.is_partial = True
        process.last_message = result

    async def run_in_background(self, process: TProcess):
        while process.is_running:
            partial_update_time = (process.run_time + 1) % 4 == 0
            try:
                if partial_update_time or process.response_id is None:
                    # first time fast response needed but next times
                    # for a partial update must passed at least 1 second
                    response_delay = 0.5 if process.response_id is None else 1.1
                    await asyncio.sleep(response_delay)
                    await self.response(process)
            except Exception:
                # TODO should I reaction to this?
                pass
            finally:
                await asyncio.sleep(0.1)

        # maybe process will be finished before next update
        await self.response(process)

    @staticmethod
    def find_process_by_id(pid: int):
        return Telminal.all_process.get(pid)
