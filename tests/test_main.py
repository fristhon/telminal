import asyncio
import os

import pytest

from telminal import TProcess


@pytest.mark.asyncio
async def test_process():
    process = TProcess("pwd", 0)
    process.run()
    while process.is_running:
        await asyncio.sleep(00.1)
    assert process.full_output.strip() == os.getcwd()
