import asyncio
import os
import sys

import pytest

from telminal import Telminal
from telminal import TProcess


@pytest.mark.asyncio
async def test_normal_process():
    process = TProcess("pwd", 0)
    process.run(stream=False)
    await process.stream()
    assert process.full_output.strip() == os.getcwd()


@pytest.mark.asyncio
async def test_interactive_process(tmp_path):
    py_version = "".join(str(i) for i in sys.version_info)
    file_path = (tmp_path / f"{py_version}.temp").as_posix()
    nano = TProcess(f"nano {file_path}", 0)
    nano.run()
    # must be a delay between commands to execute correctly
    await asyncio.sleep(1.5)
    nano.push(py_version)
    nano.is_interactive_process = True
    await asyncio.sleep(0.5)
    nano.push("^o")
    await asyncio.sleep(0.5)
    nano.push("^m")
    await asyncio.sleep(0.5)
    nano.push("^x")

    pytest.shared = file_path

    process = TProcess(f"cat {file_path}", 0)
    process.run(stream=False)
    await process.stream()
    assert process.full_output.strip() == py_version


@pytest.mark.asyncio
async def test_xtermjs():
    telminal = Telminal(api_id=None, api_hash=None, token=None)
    await telminal.setup_browser()

    file_path = pytest.shared
    nano = TProcess(f"nano {file_path}", 0)
    nano.run()

    # same as line23
    await asyncio.sleep(2)
    output, _ = await telminal.render_xtermjs(nano)
    assert output.strip().startswith(file_path)
    await telminal.browser.close()
    nano.terminate()
