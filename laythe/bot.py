import logging

import dico
import dico_command
import dico_interaction

from config import Config

from .database import LaytheDB


class LaytheBot(dico_command.Bot):
    interaction: dico_interaction.InteractionClient
    database: LaytheDB

    def __init__(self, *, logger: logging.Logger):
        intents = dico.Intents.no_privileged()
        super().__init__(
            Config.TOKEN,
            self.get_prefix,
            intents=intents,
            default_allowed_mentions=dico.AllowedMentions(everyone=False),
            monoshard=Config.MONO_SHARD,
        )
        self.laythe_logger = logger
        dico_interaction.InteractionClient(
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

    async def get_prefix(self, message: dico.Message):
        await self.wait_ready()
        if message.content.split()[0] in [f"<@{self.user.id}>", f"<@!{self.user.id}>"]:
            return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]
        else:
            return [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
