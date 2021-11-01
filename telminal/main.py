import asyncio
import json

from telminal import Telminal


async def amain():
    try:
        with open("config.json", encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {
            "api_id": input("API ID : "),
            "api_hash": input("API hash : "),
            "token": input("Token : "),
        }

    telminal = Telminal(**config)
    await telminal.start()


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
