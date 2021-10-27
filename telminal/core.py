import asyncio
import os
import re
from functools import partial
from io import StringIO
from subprocess import PIPE
from time import time

import pexpect
from pexpect.exceptions import EOF
from pexpect.exceptions import TIMEOUT

from . import utils
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
        self.buttons = None

    def run(self) -> None:
        self._process = pexpect.spawn("/bin/bash", ["-c", self.command], timeout=None)
        self.pid = self._process.pid
        self.is_running = True
        self.start_time = time()
        asyncio.create_task(self.stream())

    def done(self):
        self.is_running = False
        self.done_time = time()

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
        # TODO seprate this stuff
        self.last_update_time = time()

    def terminate(self):
        self._process.terminate()
        self.done()

    def push(self, command):
        if command.startswith("^") and len(command) == 2:
            self._process.sendcontrol(command[-1])
        else:
            for index, word in enumerate(command.split("\n")):
                if index != 0:
                    # for each \n send an enter
                    self._process.sendcontrol("m")
                self._process.sendcontrol("m") if not word else self._process.send(word)

    def update_buttons(self, interactive_process):
        from telethon import Button

        if self.is_running:
            interact_switch_text = "Interactive mode"
            if self is interactive_process:
                interact_switch_text = "Exit interactive mode"

            buttons = [
                [Button.inline("Terminate", data=f"terminate&{self.pid}")],
                [Button.inline(interact_switch_text, data=f"interact&{self.pid}")],
                [Button.inline("HTML", data=f"html&{self.pid}")],
            ]
        else:
            buttons = [
                [Button.inline("HTML", data=f"html&{self.pid}")],
            ]

        if self.buttons != buttons:
            self.buttons = buttons
            return True
        return False


class Telminal:
    all_process = {}
    all_progress_callback = {}

    def __init__(
        self,
        *,
        api_id: int,
        api_hash: str,
        token: str,
        admins: list,
        session_name: str = "telminal",
    ) -> None:
        self.interactive_process = None
        self.bot = Telegram(api_id, api_hash, token, session_name)
        self.admins = admins

    @classmethod
    async def process_cleaner(cls):
        while True:
            for pid, process in cls.all_process.copy().items():
                # TODO configable or constant variables
                if not process.is_running and int(time() - process.done_time) > 60:
                    del cls.all_process[pid]
                    utils.silent_file_remover(f"{pid}.html")
            await asyncio.sleep(100)

    def check_permission(func):
        async def inner(self, event):
            if event.sender_id not in self.admins:
                return
            await func(self, event)

        return inner

    async def start(self):
        # TODO bad coupling
        from telethon import events

        handlers = {
            self.all_messages_handler: events.NewMessage(
                incoming=True, from_users=self.admins
            ),
            self.terminate_handler: events.CallbackQuery(pattern=r"terminate&\d+"),
            self.html_handler: events.CallbackQuery(pattern=r"html&\d+"),
            self.interactive_handler: events.CallbackQuery(pattern=r"interact&\d+"),
            self.inline_query_handler: events.InlineQuery(),
            self.cancell_download_handler: events.CallbackQuery(pattern=r"removeme"),
            self.confirm_download_handler: events.CallbackQuery(pattern=r"savefile&.+"),
        }
        asyncio.shield(Telminal.process_cleaner())
        await self.bot.start(handlers)

    def new_process(self, command: str, request_id: int) -> TProcess:
        process = TProcess(command, request_id)
        process.run()
        return process

    async def special_commands_handler(self, command: str, event):
        param = command.split(" ", 1)[-1]
        chat_id, request_id = event.chat_id, event.message.id
        if command.startswith("!get"):
            if not os.path.isfile(param):
                await self.bot.send_message(
                    chat_id, f"`{param}` is not a file", reply_to=request_id
                )
                return

            message = await self.bot.send_message(
                chat_id, "Uploading started...", reply_to=request_id
            )
            partial_callback = partial(
                self.progress_callback,
                chat_id=event.chat_id,
                message_id=message.id,
                title=f"Uploading `{param}`",
            )
            await self.bot.send_file(
                chat_id,
                file=param,
                reply_to=request_id,
                progress_callback=partial_callback,
            )
        elif command.startswith("cd"):
            try:
                os.chdir(param)
            except FileNotFoundError:
                await self.bot.send_message(
                    chat_id,
                    f"cd: {param}: No such file or directory",
                    reply_to=request_id,
                )

    async def send_download_buttons(self, event):
        from telethon import Button

        message_id, file_name = event.id, event.file.name
        buttons = []
        if os.path.exists(file_name):
            message = f"`{file_name}` currentlly exists on this directory"
            buttons.extend(
                [
                    [
                        Button.inline(
                            "Save as new file", data=f"savefile&new&{message_id}"
                        )
                    ],
                    [Button.inline("Overwrite", data=f"savefile&true&{message_id}")],
                ]
            )
        else:
            message = "Do you want to save this file on sever?"
            buttons.append([Button.inline("Yes", data=f"savefile&new&{message_id}")])

        buttons.append([Button.inline("Cancell", data="removeme")])

        await self.bot.send_message(
            event.chat_id,
            message,
            reply_to=message_id,
            buttons=buttons,
        )

    async def all_messages_handler(self, event):
        command: str = event.message.message

        if event.file:
            await self.send_download_buttons(event)

        elif (
            self.interactive_process is None
            and command.startswith("!")
            or command.split()[0] == "cd"
        ):
            await self.special_commands_handler(command, event)

        elif self.interactive_process:
            self.interactive_process.push(command)
            # maybe background task finish sooner
            # also a minimum time must be passed from last update
            # editing a message for each input charachter not reasonable/possible
            next_update_arrived = (
                int(time()) - self.interactive_process.last_update_time >= 2
            )
            if self.interactive_process is not None and next_update_arrived:
                await self.response(self.interactive_process, event.chat_id)
        else:
            process = self.new_process(command, event.message.id)
            # TODO better?
            Telminal.all_process[process.pid] = process

            asyncio.shield(self.run_in_background(process, event.chat_id))

    @check_permission
    async def terminate_handler(self, event):
        process = Telminal.find_process_by_event(event)
        process.terminate()

    @check_permission
    async def html_handler(self, event):
        process = Telminal.find_process_by_event(event)
        if process is None:
            await event.answer("this process not exist anymore", alert=True)
            # clear button
            await self.bot.edit_message(event.chat_id, message_id=event.message_id)
            return
        await self.bot.send_file(
            event.chat_id,
            utils.make_html(process.pid, process.command, process.full_output),
            reply_to=process.response_id,
        )

    @check_permission
    async def interactive_handler(self, event):
        process = self.find_process_by_event(event)
        if self.interactive_process is process:
            self.interactive_process = None
            answer = "Normal mode activated"
        else:
            answer = f"You are talking to PID {process.pid}"
            self.interactive_process = process

        await event.answer(answer, alert=True)
        await self.response(process, event.chat_id)

    @check_permission
    async def inline_query_handler(self, event):
        command = "ls -la" if not event.text else f"ls -la | grep {event.text}"
        process = await asyncio.subprocess.create_subprocess_shell(
            command, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        files = (await process.stdout.read()).decode().split("\n")

        builder = event.builder
        results = []
        file_name_pattern = re.compile(r"(.+)\s\d{2}:*\d{2}\s")
        for file in files:
            # means this is a file and not a directory
            if file.startswith("-"):
                # handle space in file name
                file_name = file_name_pattern.findall(file[::-1])[0][::-1]
                results.append(
                    builder.article(
                        text=f"!get {file_name}", title=file_name, description=file
                    )
                )
        await event.answer(results=results, cache_time=0)

    async def progress_callback(
        self, current, total, *, chat_id: int, message_id: int, title: str
    ):
        percent_str = f"{current / total:.2%}"
        percent_int = int(percent_str.split(".")[0])
        upload_finished = percent_int == 100

        emoji = "🟩"
        if upload_finished:
            emoji = "☑️"
            title = "Finished Successfully"

        emoji_count = 0 if percent_int <= 10 else int(percent_str[0])

        text = f"""\
        {title}
        {emoji_count * emoji} {percent_str}
        """
        # showing upload state to user each 5 second
        if (
            int(time() - self.all_progress_callback.get(message_id, 0)) > 5
            or upload_finished
        ):
            await self.bot.edit_message(chat_id, message_id=message_id, message=text)
            self.all_progress_callback[message_id] = time()

    @check_permission
    async def confirm_download_handler(self, event):
        _, overwrite, message_id = event.data.decode().split("&")
        message = await self.bot.get_message(event.chat_id, int(message_id))
        partial_callback = partial(
            self.progress_callback,
            chat_id=event.chat_id,
            message_id=event.message_id,
            title="Downloading started...",
        )

        file = message.file.name if overwrite == "true" else None
        await self.bot.download_media(
            message, progress_callback=partial_callback, file=file
        )

    @check_permission
    async def cancell_download_handler(self, event):
        await event.delete()

    async def response(self, process: TProcess, chat_id: int):
        result = process.full_output
        # handle telegram caption limit
        if len(result) >= Telegram.MEDIA_CAPTION_LIMIT:
            result = result[len(result) - Telegram.MEDIA_CAPTION_LIMIT :]

        new_buttons = process.update_buttons(self.interactive_process)
        # for a button update request, content dosen't matter anymore
        if new_buttons is False:
            # there is no output for commands like `touch`
            # telegram api raise an error for no changes edit
            if not result or process.last_message == result:
                return

        if process.is_partial:
            await self.bot.edit_message(
                chat_id,
                message=result,
                message_id=process.response_id,
                buttons=process.buttons,
            )
        else:
            process.response_id = (
                await self.bot.send_message(
                    chat_id,
                    result,
                    reply_to=process.request_id,
                    buttons=process.buttons,
                )
            ).id
            process.is_partial = True
        process.last_message = result

    async def run_in_background(self, process: TProcess, chat_id: int):
        while process.is_running:
            partial_update_time = (process.run_time + 1) % 4 == 0
            try:
                if partial_update_time or process.response_id is None:
                    # first time fast response needed but next times
                    # for a partial update must passed at least 1 second
                    response_delay = 0.5 if process.response_id is None else 1.1
                    await asyncio.sleep(response_delay)
                    await self.response(process, chat_id)
            except Exception:
                # TODO should I reaction to this?
                pass
            finally:
                await asyncio.sleep(0.1)

        try:
            # maybe process will be finished before next update
            await self.response(process, chat_id)
        finally:
            if self.interactive_process is process:
                self.interactive_process = None

    @staticmethod
    def find_process_by_event(event) -> TProcess:
        pid = int(event.data.decode().split("&")[-1])
        return Telminal.all_process.get(pid)
