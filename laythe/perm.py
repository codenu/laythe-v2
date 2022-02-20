from typing import Union, Dict

from dico import PermissionFlags
from dico.exception import DicoException
from dico_interaction import InteractionContext


PRELOADED_VALUES: Dict[str, int] = {
    getattr(PermissionFlags, x): x
    for x in dir(PermissionFlags)
    if isinstance(getattr(PermissionFlags, x), int)
}


class PermissionNotFound(DicoException):
    PREFIX = "Permission not found"

    def __init__(self, *perms_missing):
        super().__init__(f"{self.PREFIX}: {', '.join(perms_missing)}")
        self.perms_missing = perms_missing

    def __iter__(self):
        for perm in self.perms_missing:
            yield perm


class BotPermissionNotFound(PermissionNotFound):
    PREFIX = "Bot permission not found"


class PermissionUnavailable(DicoException):
    def __init__(self):
        super().__init__(
            "Permission unavailable. This may happen due to invocation in DM or missing cache."
        )


def has_perm(*perms: Union[int, str], **kwargs: bool):
    perms = [x if isinstance(x, str) else PRELOADED_VALUES[x] for x in perms]
    if kwargs:
        perms.extend([k for k, v in kwargs.items() if v])

    def wrap(ctx: InteractionContext):
        if not ctx.member:
            raise PermissionUnavailable
        perms_has = ctx.member.permissions
        if not perms_has:
            raise PermissionUnavailable
        if perms_has.administrator:
            # bypass all perms
            return True
        missing = []
        for x in perms:
            if not perms_has.has(x):
                missing.append(x)
        if missing:
            raise PermissionNotFound(*perms)
        else:
            return True

    return wrap


def bot_has_perm(*perms: Union[int, str], **kwargs: bool):
    perms = [x if isinstance(x, str) else PRELOADED_VALUES[x] for x in perms]
    if kwargs:
        perms.extend([k for k, v in kwargs.items() if v])

    async def wrap(ctx: InteractionContext):
        self_user = ctx.client.user
        guild = ctx.client.get_guild(ctx.guild_id) or await ctx.client.request_guild(
            ctx.guild_id
        )
        self_member = guild.get(self_user.id, "member") or await guild.request_member(
            self_user
        )
        perms_has = self_member.permissions
        if not perms_has:
            raise PermissionUnavailable
        if perms_has.administrator:
            # bypass all perms
            return True
        missing = []
        for x in perms:
            if not perms_has.has(x):
                missing.append(x)
        if missing:
            raise BotPermissionNotFound(*perms)
        else:
            return True

    return wrap
