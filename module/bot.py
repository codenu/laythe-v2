import logging

import dico
import dico_command
import dico_interaction

from config import Config


class LaytheBot(dico_command.Bot):
    interaction: dico_interaction.InteractionClient

    def __init__(self, *, logger: logging.Logger):
        intents = dico.Intents.no_privileged()
        super().__init__(
            Config.TOKEN,
            self.get_prefix,
            intents=intents,
            default_allowed_mentions=dico.AllowedMentions(everyone=False),
            monoshard=Config.MONO_SHARD
        )
        self.laythe_logger = logger
        dico_interaction.InteractionClient(client=self, guild_ids_lock=Config.TESTING_GUILDS, auto_register_commands=bool(Config.TESTING_GUILDS))
        self.nugrid = None  # soonTM

    async def get_prefix(self, message: dico.Message):
        await self.wait_ready()
        if message.content.split()[0] in [f"<@{self.user.id}>", f"<@!{self.user.id}>"]:
            return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]
        else:
            return [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
