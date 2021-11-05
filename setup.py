from pathlib import Path

from setuptools import find_packages
from setuptools import setup

setup(
    name="telminal",
    version="1.0.0",
    description="A Terminal in Telegram",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/fristhon/telminal",
    author="Mohammadreza Jafari",
    author_email="fristhon@outlook.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    setup_requires=["wheel"],
    install_requires=["pexpect>=4.8.0,<5", "Telethon>=1.23.0,<2", "pyppeteer>=0.2.6<1"],
    python_requires=">=3.7",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "telminal = telminal.main:main",
        ],
    },
)
