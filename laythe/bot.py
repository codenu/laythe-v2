from contextlib import suppress
from typing import Union
from logging import Logger

from dico import AllowedMentions, Intents, Guild
from dico.exception import HTTPError
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

try:
    from extlib.klist import KListClient
    from extlib.spellchecker import SpellChecker
except ImportError:
    import sys

    print("extlib missing, `/맞춤법` command and klist-related features disabled.")
    KListClient = None
    SpellChecker = None


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
        intents.guild_members = True
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
        self.klist = (
            KListClient(self, Config.KBOT_TOKEN, self.http.session)
            if KListClient
            else KListClient
        )  # noqa
        self.spell = (
            SpellChecker(self.http.session) if SpellChecker else SpellChecker
        )  # noqa

    async def setup_bot(self):
        await self.wait_ready()
        self.database = await LaytheDB.login(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            login_id=Config.DB_ID,
            login_pw=Config.DB_PW,
            db_name=Config.DB_NAME,
        )
        if self.klist and not Config.DEBUG:
            self.klist.create_guild_count_task()

    async def get_prefix(self, message: Message):
        await self.wait_ready()
        if message.content.split()[0] in [f"<@{self.user.id}>", f"<@!{self.user.id}>"]:
            return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]
        else:
            return [f"<@{self.user.id}>", f"<@!{self.user.id}>"]

    async def execute_log(self, guild: Guild, **kwargs):
        setting = await self.database.request_guild_setting(int(guild))
        if not setting.log_channel:
            return
        with suppress(HTTPError):  # ignore sending failure
            # TODO: use cache?
            webhooks = await self.request_channel_webhooks(setting.log_channel)
            filtered = [
                *filter(lambda w: w.user == self.user and w.name == "서버 로깅", webhooks)
            ]
            if not filtered:
                webhook = await self.create_webhook(setting.log_channel, name="서버 로깅")
            else:
                webhook = webhooks[0]
            kwargs["username"] = guild.name
            kwargs["avatar_url"] = guild.icon_url()
            return await webhook.execute(**kwargs)
