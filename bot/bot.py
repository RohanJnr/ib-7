import asyncio
import logging
import os
from typing import Callable, Iterable, Union

import asyncpg
import hikari
import lightbulb

from bot.constants import Channels, Client
from model import train
from postgres import init_db


logger = logging.getLogger(__name__)  # Required additional setup.


class Bot(lightbulb.Bot):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.loop = asyncio.get_event_loop()

        self.dev_logs: hikari.GuildTextChannel = ...

        self.db_conn: asyncpg.Connection = ...
        self.vectorizer = train()

    @classmethod
    def create(cls, token: str, *, prefix: Union[Callable, Iterable, str], **kwargs) -> "Bot":
        return cls(
            token=token,
            prefix=prefix,
            intents=hikari.Intents.ALL,
            insensitive_commands=True,
            ignore_bots=True,
            **kwargs,
        )

    def run(self, **kwargs) -> None:
        self.event_manager.subscribe(hikari.StartingEvent, self.on_starting)
        self.event_manager.subscribe(hikari.StartedEvent, self.on_started)
        self.event_manager.subscribe(hikari.StoppingEvent, self.on_stopping)

        super().run(
            activity=hikari.Activity(
                name=f"IceBreaker",
                type=hikari.ActivityType.PLAYING,
            ),
            **kwargs
        )

    async def on_starting(self, _event: hikari.StartingEvent) -> None:
        """Load extensions when bot is starting."""
        logging.info("Connecting to database...")
        self.db_conn = await init_db()

        logging.info("Loading extensions...")

        for ext in Client.extensions:
            ext = str(ext).replace(os.sep, ".")[:-3]
            self.load_extension(ext)
            logging.info(f"{ext}: Loaded")

        logging.info("Done loading extensions.")

    async def on_started(self, _event: hikari.StartedEvent) -> None:
        """Notify dev-logs."""
        self.dev_logs = await self.rest.fetch_channel(Channels.dev_logs)
        await self.dev_logs.send(f"Bot online !")

        logging.info("Bot is ready.")

    async def on_stopping(self, _event: hikari.StoppingEvent) -> None:
        """Disconnect DB."""
        pass
