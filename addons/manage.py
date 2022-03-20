from contextlib import suppress
from datetime import datetime, timedelta

from dico import ApplicationCommandOptionType, GuildMember, User
from dico.exception import BadRequest, NotFound, Forbidden, DicoException
from dico_interaction import slash, option, checks, InteractionContext

from laythe import has_perm, bot_has_perm, DMNotAllowedAddonBase, LaytheBot


PURGE_METADATA = {"name": "정리", "description": "메시지 정리와 관련된 명령어들이에요."}


class Manage(DMNotAllowedAddonBase, name="관리"):
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

        # TODO: make this automatic
        self.bot.dispatch("management_command", ctx)

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
            msg_id,
            *msgs,
            reason=f"유저 ID가 `{ctx.author.id}`인 관리자가 `/정리 메시지 메시지:{msg_id}` 명령어를 실행함.",
        )
        await ctx.send(f"✅ 성공적으로 `{msg_id}` 부터의 메시지 `{len(msgs)+1}`개를 정리했어요.")

        self.bot.dispatch("management_command", ctx)

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

        self.bot.dispatch("management_command", ctx)

    @slash(
        "뮤트",
        description="선택한 유저를 뮤트하거나 타임아웃을 적용해요.",
        connector={
            "유저": "user",
            "사유": "reason",
            "타임아웃": "use_timeout",
            "기간": "timeout",
        },
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="뮤트를 하거나 타임아웃을 활성화할 유저",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="사유",
        description="뮤트 또는 타임아웃의 사유",
        required=False,
    )
    @option(
        ApplicationCommandOptionType.BOOLEAN,
        name="타임아웃",
        description="타임아웃을 사용할 지의 여부, 만약에 뮤트 역할이 설정되지 않았다면 타임아웃이 강제됩니다.",
        required=False,
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="기간",
        description="타임아웃을 적용할 기간 (최대 7일)",
        required=False,
    )
    @checks(
        has_perm(manage_roles=True, moderate_members=True),
        bot_has_perm(manage_roles=True, moderate_members=True),
    )
    async def mute(
        self,
        ctx: InteractionContext,
        user: GuildMember,
        reason: str = None,
        use_timeout: bool = False,
        timeout: int = 0,
    ):
        if use_timeout and timeout < 1:
            return await ctx.send(
                "❌ 타임아웃을 사용하는 경우 `기간` 값을 1 이상 7 이하로 설정해주세요.", ephemeral=True
            )
        elif not use_timeout and timeout:
            return await ctx.send("❌ 뮤트 역할을 사용하는 경우 아직 기간을 설정하실 수 없어요.", ephemeral=True)
        await ctx.defer()
        if use_timeout:
            end_at = datetime.utcnow() + timedelta(days=timeout)
            await self.bot.modify_guild_member(
                ctx.guild_id, user, communication_disabled_until=end_at, reason=reason
            )
        else:
            data = await self.bot.database.request_guild_setting(int(ctx.guild_id))
            if not data.mute_role:
                return await ctx.send("❌ 뮤트 역할이 존재하지 않아요. 먼저 뮤트 역할을 설정해주세요.")
            await self.bot.add_guild_member_role(
                ctx.guild_id, user, data.mute_role, reason=reason
            )
        await ctx.send(
            f"✅ 성공적으로 <@!{int(user)}>{'에게 타임아웃을 적용했어요.' if use_timeout else '를 뮤트했어요.'}"
        )

        self.bot.dispatch("management_command", ctx)

    @slash(
        "언뮤트",
        description="선택한 유저를 언뮤트하거나 타임아웃을 제거해요.",
        connector={"유저": "user", "타임아웃": "use_timeout", "사유": "reason"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="뮤트를 하거나 타임아웃을 활성화할 유저",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.BOOLEAN,
        name="타임아웃",
        description="역할 대신 타임아웃을 제거할 지의 여부, 만약에 뮤트 역할이 설정되지 않았다면 타임아웃으로 강제됩니다.",
        required=False,
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="사유",
        description="언뮤트 또는 타임아웃 제거의 사유",
        required=False,
    )
    async def unmute(
        self,
        ctx: InteractionContext,
        user: GuildMember,
        use_timeout: bool = False,
        reason: str = None,
    ):
        await ctx.defer()
        if use_timeout:
            await self.bot.modify_guild_member(
                ctx.guild_id, user, communication_disabled_until=None, reason=reason
            )
        else:
            data = await self.bot.database.request_guild_setting(int(ctx.guild_id))
            if not data.mute_role:
                return await ctx.send("❌ 뮤트 역할이 존재하지 않아요. 먼저 뮤트 역할을 설정해주세요.")
            await self.bot.remove_guild_member_role(
                ctx.guild_id, user, data.mute_role, reason=reason
            )
        await ctx.send(
            f"✅ 성공적으로 <@!{int(user)}>{'에게 타임아웃을 제거했어요.' if use_timeout else '를 언뮤트했어요.'}"
        )

    @slash("추방", description="선택한 유저를 추방해요.", connector={"유저": "user", "사유": "reason"})
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="추방할 유저",
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

            self.bot.dispatch("management_command", ctx)

    @slash(
        "차단",
        description="선택한 유저를 차단해요. 핵밴도 가능해요.",
        connector={"유저": "user", "사유": "reason", "삭제": "delete_message_days"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="차단할 유저",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="사유",
        description="차단의 사유",
        required=False,
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="삭제",
        description="차단할 유저가 보낸 메시지 중 삭제할 메시지를 보낸 일 수 (일 단위로, 최대 7일)",
        required=False,
    )
    @checks(has_perm(ban_members=True), bot_has_perm(ban_members=True))
    async def ban(
        self,
        ctx: InteractionContext,
        user: GuildMember.TYPING,
        reason: str = None,
        delete_message_days: int = 0,
    ):
        await ctx.defer()
        try:
            delete_message_days = min(delete_message_days, 7)
            await self.bot.create_guild_ban(
                ctx.guild_id,
                user,
                delete_message_days=delete_message_days,
                reason=reason,
            )
        except NotFound:
            await ctx.send("❌ 차단할 사용자를 찾지 못했어요.")
        except Forbidden:
            await ctx.send("❌ 레이테의 권한이 부족해요. `멤버 차단하기` 권한이 있는지 다시 확인해주세요.")
        else:
            with suppress(DicoException):
                user_as = (
                    user.user
                    if isinstance(user, GuildMember)
                    else user
                    if isinstance(user, User)
                    else self.bot.get_user(int(user))
                    or await self.bot.request_user(int(user))
                )
                if user_as:
                    await ctx.send(
                        f"✅ 성공적으로 <@{int(user)}>(`{user_as}` | ID: `{int(user)}`)을/를 차단했어요. (사유: {reason})"
                    )
                    return
            await ctx.send(
                f"✅ 성공적으로 <@{int(user)}>(`유저를 찾지 못함` | ID: `{int(user)}`)을/를 차단했어요. (사유: {reason})"
            )

            self.bot.dispatch("management_command", ctx)


def load(bot: LaytheBot):
    bot.load_addons(Manage)


def unload(bot: LaytheBot):
    bot.unload_addons(Manage)
