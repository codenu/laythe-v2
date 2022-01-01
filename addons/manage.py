from typing import TYPE_CHECKING

from dico import ApplicationCommandOptionType, Message, GuildMember
from dico.exception import BadRequest, NotFound, Forbidden
from dico_command import Addon
from dico_interaction import slash, option, checks, InteractionContext

from module import has_perm, bot_has_perm

if TYPE_CHECKING:
    from module.bot import LaytheBot


PURGE_METADATA = {"name": "정리", "description": "메시지 정리와 관련된 명령어들이에요."}


class Manage(Addon, name="관리"):
    @slash(
        **PURGE_METADATA,
        subcommand="개수",
        subcommand_description="개수를 기준으로 메시지를 정리해요.",
        connector={"개수": "count"},
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="개수",
        description="지울 메시지의 최대 개수 (최대 100)",
        required=True,
    )
    @checks(has_perm(manage_messages=True), bot_has_perm(manage_messages=True))
    async def purge_count(self, ctx: InteractionContext, count: int):
        if not 0 < count <= 100:
            return await ctx.send("❌ `개수`는 최소 1, 최대 100 까지만 가능해요.", ephemeral=True)
        try:
            await ctx.defer(ephemeral=True)
        except BadRequest:
            return await ctx.send("❌ 삭제할 메시지를 가져오지 못했어요. 2주 이내에 전송된 메시지만 가져울 수 있어요.")
        msgs = await self.bot.request_channel_messages(ctx.channel_id, limit=count)
        await self.bot.bulk_delete_messages(
            ctx.channel_id,
            *msgs,
            reason=f"유저 ID가 `{ctx.author.id}`인 관리자가 `/정리 개수 개수:{count}` 명령어를 실행함.",
        )
        await ctx.send(f"✅ 성공적으로 메시지 `{count}`개를 정리했어요.")

    @slash(
        **PURGE_METADATA,
        subcommand="메시지",
        subcommand_description="주어진 메시지 ID 이후의 모든 메시지를 정리해요.",
        connector={"메시지": "msg_id"},
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="메시지",
        description="기준점으로 사용할 메시지의 ID",
        required=True,
    )
    @checks(has_perm(manage_messages=True), bot_has_perm(manage_messages=True))
    async def purge_message(self, ctx: InteractionContext, msg_id: str):
        try:
            msg_id = int(msg_id)
        except ValueError:
            return await ctx.send("❌ `메시지`는 숫자로 된 ID만 가능해요.", ephemeral=True)
        await ctx.defer(ephemeral=True)
        try:
            msgs = await self.bot.request_channel_messages(ctx.channel_id, after=msg_id)
        except BadRequest:
            return await ctx.send("❌ 삭제할 메시지를 가져오지 못했어요. 2주 이내에 전송된 메시지만 가져울 수 있어요.")
        await self.bot.bulk_delete_messages(
            ctx.channel_id,
            *msgs,
            reason=f"유저 ID가 `{ctx.author.id}`인 관리자가 `/정리 메시지 메시지:{msg_id}` 명령어를 실행함.",
        )
        await ctx.send(f"✅ 성공적으로 `{msg_id}` 부터의 메시지 `{len(msgs)}`개를 정리했어요.")

    @slash(
        **PURGE_METADATA,
        subcommand="유저",
        subcommand_description="주어진 유저가 전송한 메시지를 주어진 범위 내에서 정리해요.",
        connector={"유저": "user", "범위": "search_range"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="정리할 메시지를 보낸 유저",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="범위",
        description="메시지를 탐색할 범위",
        required=True,
    )
    @checks(has_perm(manage_messages=True), bot_has_perm(manage_messages=True))
    async def purge_user(
        self, ctx: InteractionContext, user: GuildMember, search_range: int
    ):
        if not 0 < search_range <= 100:
            return await ctx.send("❌ `범위`는 최소 1, 최대 100 까지만 가능해요.", ephemeral=True)
        await ctx.defer(ephemeral=True)
        try:
            msgs = await self.bot.request_channel_messages(
                ctx.channel_id, limit=search_range
            )
            msgs = [x for x in msgs if x.author == user]
        except BadRequest:
            return await ctx.send("❌ 삭제할 메시지를 가져오지 못했어요. 2주 이내에 전송된 메시지만 가져울 수 있어요.")
        await self.bot.bulk_delete_messages(
            ctx.channel_id,
            *msgs,
            reason=f"유저 ID가 `{ctx.author.id}`인 관리자가 `/정리 유저 유저:{user} 범위:{search_range}` 명령어를 실행함.",
        )
        await ctx.send(f"✅ 성공적으로 <@{int(user)}>이/가 전송한 메시지 `{len(msgs)}`개를 정리했어요.")

    @slash("추방", description="선택한 유저를 추방해요.", connector={"유저": "user", "사유": "reason"})
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="추방할 사용자",
        required=True,
    )
    @checks(has_perm(kick_members=True), bot_has_perm(kick_members=True))
    async def kick(self, ctx: InteractionContext, user: GuildMember):
        await ctx.defer()
        try:
            await self.bot.remove_guild_member(ctx.guild_id, user)
        except NotFound:
            await ctx.send("❌ 추방할 사용자를 찾지 못했어요.")
        except Forbidden:
            await ctx.send("❌ 레이테의 권한이 부족해요. `멤버 추방하기` 권한이 있는지 다시 확인해주세요.")
        else:
            user_as = user.user if isinstance(user, GuildMember) else user
            await ctx.send(
                f"✅ 성공적으로 <@{int(user)}>(`{user_as}` | ID: `{int(user)}`)을/를 추방했어요."
            )


def load(bot: "LaytheBot"):
    bot.load_addons(Manage)


def unload(bot: "LaytheBot"):
    bot.unload_addons(Manage)
