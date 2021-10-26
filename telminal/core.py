import asyncio
import os
import re
from asyncio.events import Handle
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

    def __init__(
        self, *, api_id: int, api_hash: str, token: str, session_name: str = "telminal"
    ) -> None:
        self.interactive_process = None
        self.bot = Telegram(api_id, api_hash, token, session_name)

    @classmethod
    async def process_cleaner(cls):
        while True:
            for pid, process in cls.all_process.copy().items():
                # TODO configable or constant variables
                if not process.is_running and int(time() - process.done_time) > 60:
                    del cls.all_process[pid]
                    utils.silent_file_remover(f"{pid}.html")
            await asyncio.sleep(100)

    async def start(self):
        # TODO bad coupling
        from telethon import events

        handlers = {
            self.all_messages_handler: events.NewMessage(incoming=True),
            self.terminate_handler: events.CallbackQuery(pattern=r"terminate&\d+"),
            self.html_handler: events.CallbackQuery(pattern=r"html&\d+"),
            self.interactive_handler: events.CallbackQuery(pattern=r"interact&\d+"),
            self.inline_query_handler: events.InlineQuery(),
            self.cancell_saving_file: events.CallbackQuery(pattern=r"removeme"),
            self.confirm_saving_file: events.CallbackQuery(pattern=r"savefile&\d+"),
        }
        asyncio.shield(Telminal.process_cleaner())
        await self.bot.start(handlers)

    def new_process(self, command: str, request_id: int) -> TProcess:
        process = TProcess(command, request_id)
        process.run()
        return process

    async def special_commands_handler(self, command: str, request_id: int):
        param = command.split(" ", 1)[-1]
        if command.startswith("!get"):
            message = await self.bot.send_message(
                "Uploading started...", reply_to=request_id
            )
            partial_callback = partial(
                self.progress_callback,
                message_id=message.id,
                title=f"Uploading `{param}`",
            )
            await self.bot.send_file(
                file=param, reply_to=request_id, progress_callback=partial_callback
            )
        elif command.startswith("cd"):
            try:
                os.chdir(param)
            except FileNotFoundError:
                await self.bot.send_message(
                    f"cd: {param}: No such file or directory", reply_to=request_id
                )

    async def all_messages_handler(self, event):
        self.bot.chat_id = event.chat_id  # TODO
        command: str = event.message.message

        if event.file:
            from telethon import Button

            buttons = [
                Button.inline("cancell", data=f"removeme"),
                Button.inline("Yes", data=f"savefile&{event.message.id}"),
            ]
            await self.bot.send_message(
                "Do you want to save this file on sever?",
                reply_to=event.message.id,
                buttons=buttons,
            )
            return

        is_special_command = command.startswith("!") or command.split()[0] == "cd"
        if self.interactive_process is None and is_special_command:
            await self.special_commands_handler(command, event.message.id)
            return

        if self.interactive_process:
            self.interactive_process.push(command)
            # maybe background task finish sooner
            # also a minimum time must be passed from last update
            # editing a message for each input charachter not reasonable/possible
            next_update_arrived = (
                int(time()) - self.interactive_process.last_update_time >= 2
            )
            if self.interactive_process is not None and next_update_arrived:
                await self.response(self.interactive_process)
        else:
            process = self.new_process(command, event.message.id)
            # TODO better?
            Telminal.all_process[process.pid] = process

            asyncio.shield(self.run_in_background(process))

    async def terminate_handler(self, event):
        process = Telminal.find_process_by_event(event)
        process.terminate()

    async def html_handler(self, event):
        process = Telminal.find_process_by_event(event)
        if process is None:
            await event.answer("this process not exist anymore", alert=True)
            # clear button
            await self.bot.edit_message(message_id=event.message_id)
            return
        await self.bot.send_file(
            utils.make_html(process.pid, process.command, process.full_output),
            reply_to=process.response_id,
        )

    async def interactive_handler(self, event):
        process = self.find_process_by_event(event)
        if self.interactive_process is None:
            self.interactive_process = process
            answer = f"You are talking to PID : {process.pid}"
        else:
            self.interactive_process = None
            answer = "Normal mode activated"
        await event.answer(answer, alert=True)
        await self.response(process)

    async def inline_query_handler(self, event):
        command = "ls -la" if not event.text else f"ls -la | grep {event.text}"
        process = await asyncio.subprocess.create_subprocess_shell(
            command, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        files = (await process.stdout.read()).decode().split("\n")

        builder = event.builder
        results = []
        file_name_pattern = re.compile(r"(.+)\s\d{2}:\d{2}")
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

    async def progress_callback(self, current, total, *, message_id: int, title: str):
        percent_str = f"{current / total:.2%}"
        percent_int = int(percent_str.split(".")[0])

        emoji = "🟩" if percent_int != 100 else "☑️"
        emoji_count = 0 if percent_int <= 10 else int(percent_str[0])

        text = f"""\
        {title}
        {emoji_count * emoji} {percent_str}
        """
        await self.bot.edit_message(message_id=message_id, message=text)
        await asyncio.sleep(5)

    async def confirm_saving_file(self, event):
        message_id = int(event.data.decode().split("&")[-1])
        message = await self.bot.get_message(message_id)
        partial_callback = partial(
            self.progress_callback,
            message_id=event.message_id,
            title=f"Downloading `{message.file.name}`",
        )
        await self.bot.download_media(message, partial_callback)

    async def cancell_saving_file(self, event):
        await event.delete()

    async def response(self, process: TProcess):
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
                message=result, message_id=process.response_id, buttons=process.buttons
            )
        else:
            process.response_id = (
                await self.bot.send_message(
                    result, reply_to=process.request_id, buttons=process.buttons
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

        try:
            # maybe process will be finished before next update
            await self.response(process)
        finally:
            if self.interactive_process is process:
                self.interactive_process = None

    @staticmethod
    def find_process_by_event(event) -> TProcess:
        pid = int(event.data.decode().split("&")[-1])
        return Telminal.all_process.get(pid)
