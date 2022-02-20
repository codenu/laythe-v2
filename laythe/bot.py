from typing import Union
from logging import Logger

from dico import AllowedMentions, Intents
from dico_command import Bot, Message
from dico_interaction import (
    InteractionClient as InteractionBase,
    InteractionContext,
    InteractionCommand,
    ComponentCallback,
    AutoComplete,
)

from config import Config

from .database import LaytheDB


class InteractionClient(InteractionBase):
    async def handle_interaction(
        self,
        target: Union[InteractionCommand, ComponentCallback, AutoComplete],
        interaction: InteractionContext,
    ):
        if isinstance(target, InteractionCommand) and not interaction.guild_id:
            return await interaction.send("❌ 명령어는 DM에서 사용할 수 없어요.")
        return await super().handle_interaction(target, interaction)


class LaytheBot(Bot):
    interaction: InteractionClient
    database: LaytheDB

    def __init__(self, *, logger: Logger):
        intents = Intents.no_privileged()
        super().__init__(
            Config.TOKEN,
            self.get_prefix,
            intents=intents,
            default_allowed_mentions=AllowedMentions(everyone=False),
            monoshard=Config.MONO_SHARD,
        )
        self.laythe_logger = logger
        InteractionClient(
            client=self,
            guild_ids_lock=Config.TESTING_GUILDS,
            auto_register_commands=bool(Config.TESTING_GUILDS),
        )
        self.nugrid = None  # soonTM
        self.loop.create_task(self.setup_bot())

    async def setup_bot(self):
        await self.wait_ready()
        self.database = await LaytheDB.login(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            login_id=Config.DB_ID,
            login_pw=Config.DB_PW,
            db_name=Config.DB_NAME,
        )

    async def get_prefix(self, message: Message):
        await self.wait_ready()
        if message.content.split()[0] in [f"<@{self.user.id}>", f"<@!{self.user.id}>"]:
            return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]
        else:
            return [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
