from dico_command import Addon
from dico_interaction import InteractionContext
from dico_interaction.exception import CheckFailed

from .bot import LaytheBot
from .perm import PermissionNotFound


class LaytheAddonBase(Addon):
    bot: LaytheBot


class DMNotAllowedAddonBase(LaytheAddonBase):
    async def addon_interaction_check(self, ctx: InteractionContext):
        return bool(ctx.guild_id)

    async def on_addon_interaction_error(
        self, ctx: InteractionContext, error: Exception
    ):
        if isinstance(error, CheckFailed) and not issubclass(
            type(error), PermissionNotFound
        ):
            await ctx.send("❌ 해당 명령어는 DM에서는 사용할 수 없어요.")
            return True
        return False
