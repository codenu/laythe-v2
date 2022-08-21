from contextlib import suppress

from dico import (
    Embed,
    MessageUpdate,
    MessageDelete,
    MessageDeleteBulk,
    GuildMember,
    Channel,
    Role,
    ChannelCreate,
    ChannelDelete,
    ChannelUpdate,
    GuildUpdate,
    GuildRoleCreate,
    GuildRoleDelete,
    GuildRoleUpdate,
    GuildBanAdd,
    GuildBanRemove,
    GuildMemberUpdate,
    GuildMemberAdd,
    GuildMemberRemove,
    AuditLogEvents,
    MessageReactionRemoveAll,
    InviteCreate,
    InviteDelete,
)
from dico.exception import HTTPError
from dico_command import on
from dico_interaction import InteractionContext

from laythe import (
    LaytheAddonBase,
    LaytheBot,
    rtc_region_translates,
    verification_level_translates,
    permission_translates,
)
from laythe.utils import (
    kstnow,
    EmbedColor,
    parse_second_with_date,
    to_readable_bool,
    permission_names,
)


class Log(LaytheAddonBase, name="로깅"):
    CONTENT_UNAVAILABLE: str = "(메시지의 내용이 없거나 디스코드의 정책으로 메시지 내용을 읽어올 수 없어요.)"

    @on("management_command")
    async def on_management_command(self, ctx: InteractionContext):
        cmd = self.bot.interaction.get_command(ctx)
        usage = f"/{cmd.command.name}"
        if cmd.subcommand_group:
            usage += f" {cmd.subcommand_group}"
        if cmd.subcommand:
            usage += f" {cmd.subcommand}"
        if ctx.options:
            for k, v in ctx.options.items():
                if isinstance(v, GuildMember) or isinstance(v, Channel):
                    v = v.mention
                elif isinstance(v, Role):
                    v = f"<@&{v.id}>"
                usage += f" {k}:{v}"
        embed = Embed(
            title="관리 명령어 실행",
            description=usage,
            color=EmbedColor.NEUTRAL,
            timestamp=kstnow(),
        )
        embed.set_footer(text=f"관리자 ID: {ctx.author.id}")
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url())
        await self.bot.execute_log(self.bot.get_guild(ctx.guild_id), embed=embed)

    @on("message_update")
    async def on_message_update(self, message: MessageUpdate):
        if not message:
            return
        if not message.original:
            return
        if message.author.bot:
            return
        if message.content == message.original.content:
            return
        embed = Embed(
            title="메시지 수정",
            description=f"{message.channel.mention} (`#{message.channel.name}`)\n[메시지로 바로가기]({message.link})",
            color=EmbedColor.NEUTRAL,
            timestamp=kstnow(),
        )
        embed.add_field(
            name="기존 내용",
            value=message.original.content or self.CONTENT_UNAVAILABLE,
            inline=False,
        )
        embed.add_field(
            name="수정된 내용",
            value=message.content or self.CONTENT_UNAVAILABLE,
            inline=False,
        )
        embed.set_footer(
            text=f"메시지 ID: {message.id}\n작성자 ID: {message.author.id}\n채널 ID: {message.channel_id}"
        )
        embed.set_author(name=str(message.member), icon_url=message.member.avatar_url())
        await self.bot.execute_log(message.guild, embed=embed)

    @on("message_delete")
    async def on_message_delete(self, message_delete: MessageDelete):
        message = message_delete.message
        link = (
            message.link
            if message
            else f"https://discord.com/channels/{message_delete.guild_id}/{message_delete.channel_id}/{message_delete.id}"
        )
        embed = Embed(
            title="메시지 삭제",
            description=f"{message_delete.channel.mention} (`#{message_delete.channel.name}`)\n[메시지 위치로 바로가기]({link})",
            color=EmbedColor.NEGATIVE,
            timestamp=kstnow(),
        )
        extra_msg = ""
        if not message:
            embed.set_footer(
                text=f"메시지 ID: {message_delete.id}\n채널 ID: {message_delete.channel_id}"
            )
        else:
            embed.add_field(
                name="메시지 내용",
                value=message.content or self.CONTENT_UNAVAILABLE,
                inline=False,
            )
            embed.set_author(
                name=str(message.member), icon_url=message.member.avatar_url()
            )
            embed.set_footer(
                text=f"메시지 ID: {message_delete.id}\n채널 ID: {message_delete.channel_id}\n작성자 ID: {message.author.id}"
            )
            if message.attachments:
                files = [x.url for x in message.attachments]
                extra_msg = "\n".join(files)
                embed.add_field(name="첨부파일", value=f"{len(files)}개", inline=False)
        resp = await self.bot.execute_log(message_delete.guild, embed=embed)
        if resp and extra_msg:
            await resp.reply(extra_msg)

    @on("message_delete_bulk")
    async def on_message_delete_bulk(self, message_bulk: MessageDeleteBulk):
        if len(message_bulk.ids) < 2:
            return
        embed = Embed(
            title="메시지 대량 삭제",
            description=message_bulk.channel.mention
            + f" (`#{message_bulk.channel.name}`)",
            color=EmbedColor.NEGATIVE,
            timestamp=kstnow(),
        )
        embed.add_field(
            name="삭제된 메시지 개수", value=f"{len(message_bulk.ids)}개", inline=False
        )
        embed.set_footer(text=f"채널 ID: {message_bulk.channel_id}")
        await self.bot.execute_log(message_bulk.guild, embed=embed)

    @on("channel_create")
    async def on_channel_create(self, channel: ChannelCreate):
        embed = Embed(
            title="새 스레드 생성" if channel.is_thread_channel() else "채널 생성",
            color=EmbedColor.POSITIVE,
            timestamp=kstnow(),
        )
        embed.add_field(
            name="스레드 이름" if channel.is_thread_channel() else "채널 이름",
            value=f"{channel.mention} (`#{channel.name}`)",
            inline=False,
        )
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_log(channel.guild, embed=embed)

    @on("channel_delete")
    async def on_channel_delete(self, channel: ChannelDelete):
        embed = Embed(title="채널 삭제", color=EmbedColor.NEGATIVE, timestamp=kstnow())
        embed.add_field(name="채널 이름", value=f"`#{channel.name}`", inline=False)
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_log(channel.guild, embed=embed)

    @on("channel_update")
    async def on_channel_update(self, channel: ChannelUpdate):
        if not channel.original:
            return
        embed = Embed(
            title="채널 업데이트",
            description=channel.mention + f" (`#{channel.name}`)",
            color=EmbedColor.NEUTRAL,
            timestamp=kstnow(),
        )

        if (
            channel.name
            and channel.original.name
            and channel.name != channel.original.name
        ):
            embed.add_field(
                name="채널 이름",
                value=f"`{channel.original.name}` -> `{channel.name}`",
                inline=False,
            )
        if (channel.parent_id or 0) != (channel.original.parent_id or 0):
            parent_original = (
                self.bot.get_channel(channel.original.parent_id)
                if channel.original.parent_id
                else None
            )
            parent = (
                self.bot.get_channel(channel.parent_id) if channel.parent_id else None
            )
            original_name = (
                parent_original.name if parent_original else "(카테고리를 찾지 못했어요.)"
            )
            name = parent.name if parent else "(카테고리를 찾지 못했어요.)"
            embed.add_field(
                name="카테고리", value=f"`#{original_name}` -> `#{name}`", inline=False
            )
        if (
            channel.bitrate
            and channel.original.bitrate
            and channel.bitrate != channel.original.bitrate
        ):
            embed.add_field(
                name="비트레이트",
                value=f"`{channel.original.bitrate}`kbps -> `{channel.bitrate}`kbps",
                inline=False,
            )
        if (channel.rtc_region or "") != (channel.original.rtc_region or ""):
            region_original = channel.original.rtc_region
            region_original = (
                rtc_region_translates.get(
                    region_original.replace("-", "_"), region_original
                )
                if region_original
                else "자동"
            )
            region = channel.rtc_region
            region = (
                rtc_region_translates.get(region.replace("-", "_"), region)
                if region
                else "자동"
            )
            embed.add_field(
                name="지역 우선 설정",
                value=f"`{region_original}` -> `{region}`",
                inline=False,
            )

        if (channel.rate_limit_per_user or 0) != (
            channel.original.rate_limit_per_user or 0
        ):
            original = (
                parse_second_with_date(channel.original.rate_limit_per_user)
                if channel.original.rate_limit_per_user
                else "설정되지 않음"
            )
            now = (
                parse_second_with_date(channel.rate_limit_per_user)
                if channel.rate_limit_per_user
                else "설정되지 않음"
            )
            embed.add_field(
                name="슬로우 모드", value=f"**{original}** -> **{now}**", inline=False
            )
        if (channel.nsfw or False) != (channel.original.nsfw or False):
            embed.add_field(
                name="연령 제한 채널 여부",
                value=f"`{to_readable_bool(channel.original.nsfw)}` -> `{to_readable_bool(channel.nsfw)}`",
                inline=False,
            )
        embed.set_footer(text=f"채널 ID: {channel.id}")

        """
        overwrites_original = channel.original.permission_overwrites
        overwrites = channel.permission_overwrites
        if overwrites_original != overwrites:
            for overwrite in overwrites_original:
                if overwrite.
        """

        if not embed.fields:
            return

        if channel.position != channel.original.position:  # Prevent spam
            embed.add_field(
                name="채널 위치",
                value=f"`{channel.original.position}`번째 -> `{channel.position}`번째",
                inline=False,
            )

        await self.bot.execute_log(channel.guild, embed=embed)

    @on("guild_update")
    async def on_guild_update(self, guild: GuildUpdate):
        if not guild.original:
            return
        embed = Embed(title="서버 업데이트", color=EmbedColor.NEUTRAL, timestamp=kstnow())
        if guild.name != guild.original.name:
            embed.add_field(
                name="서버 이름", value=f"`{guild.original.name}` -> `{guild.name}`"
            )
        if guild.verification_level.value != guild.original.verification_level.value:
            verification_level_before = verification_level_translates.get(
                str(guild.original.verification_level).replace("-", "_"),
                str(guild.original.verification_level),
            )
            verification_level_after = verification_level_translates.get(
                str(guild.verification_level).replace("-", "_"),
                str(guild.verification_level),
            )
            embed.add_field(
                name="보안 수준",
                value=f"`{verification_level_before}` -> `{verification_level_after}`",
                inline=False,
            )
        if guild.owner_id != guild.original.owner_id:
            owner_before = guild.original.get_owner()
            before_mention = owner_before.mention
            if not owner_before:
                try:
                    owner_before = await guild.request_member(guild.original.owner_id)
                    before_mention = owner_before.mention
                except HTTPError:
                    owner_before = "(기존 소유자를 찾을 수 없어요.)"
                    before_mention = "(기존 소유자를 찾을 수 없어요.)"
            owner_after = guild.get_owner() or await guild.request_member(
                guild.owner_id
            )
            embed.add_field(
                name="서버 소유자",
                value=f"{before_mention} -> {owner_after.mention}\n(`{owner_before}` -> `{owner_after}`)",
                inline=False,
            )
        if (
            (not guild.original.system_channel_id and guild.system_channel_id)
            or (not guild.system_channel_id and guild.original.system_channel_id)
            or guild.system_channel_id != guild.original.system_channel_id
        ):
            before_sys = (
                f"<#{guild.original.system_channel_id}>"
                if guild.original.system_channel_id
                else "`(없음)`"
            )
            after_sys = (
                f"<#{guild.system_channel_id}>" if guild.system_channel_id else "`(없음)`"
            )
            embed.add_field(
                name="시스템 메시지 채널", value=f"{before_sys} -> {after_sys}", inline=False
            )
        if guild.premium_tier.value != guild.original.premium_tier.value:
            embed.add_field(
                name="니트로 부스트 레벨",
                value=f"{guild.original.premium_tier.value}레벨 -> {guild.premium_tier.value}레벨",
                inline=False,
            )
        if (
            guild.original.premium_subscription_count is not None
            and guild.premium_subscription_count
            != guild.original.premium_subscription_count
        ):
            embed.add_field(
                name="니트로 부스트 수",
                value=f"{guild.original.premium_subscription_count}개 -> {guild.premium_subscription_count}개",
                inline=False,
            )
        embed.set_footer(text=f"서버 ID: {guild.id}")
        if not embed.fields:
            return
        await self.bot.execute_log(guild, embed=embed)

    @on("guild_role_create")
    async def on_guild_role_create(self, role_create: GuildRoleCreate):
        embed = Embed(title="역할 생성", color=EmbedColor.POSITIVE, timestamp=kstnow())
        embed.add_field(
            name="역할",
            value=f"<@&{role_create.role.id}> (`@{role_create.role.name}`)",
            inline=False,
        )
        embed.set_footer(text=f"역할 ID: {role_create.role.id}")
        await self.bot.execute_log(role_create.role.guild, embed=embed)

    @on("guild_role_delete")
    async def on_guild_role_delete(self, role_delete: GuildRoleDelete):
        embed = Embed(title="역할 삭제", color=EmbedColor.NEGATIVE, timestamp=kstnow())
        embed.add_field(
            name="역할",
            value=f"`@{role_delete.role.name}`"
            if role_delete.role
            else "(삭제된 역할의 이름을 찾을 수 없어요.)",
            inline=False,
        )
        embed.set_footer(text=f"역할 ID: {role_delete.role.id}")
        await self.bot.execute_log(role_delete.guild, embed=embed)

    @on("guild_role_update")
    async def on_guild_role_update(self, role_update: GuildRoleUpdate):
        if not role_update.original:
            return

        embed = Embed(
            title="역할 업데이트",
            description=f"<@&{role_update.role.id}> (`@{role_update.role.name}`)",
            color=EmbedColor.NEUTRAL,
            timestamp=kstnow(),
        )

        if role_update.role.name != role_update.original.name:
            embed.add_field(
                name="이름",
                value=f"`{role_update.original.name}` -> `{role_update.role.name}`",
                inline=False,
            )
        if role_update.role.color != role_update.original.color:
            embed.add_field(
                name="색상",
                value=f"{role_update.original.color} -> {role_update.role.color}",
                inline=False,
            )

        before_perms = role_update.original.permissions
        after_perms = role_update.role.permissions
        diffs = [
            f"`{permission_translates.get(permission_names.get(x), permission_names.get(x, '알 수 없음'))}`: 네 -> 아니요"
            for x in before_perms
            if x not in after_perms
        ]
        diffs.extend(
            [
                f"`{permission_translates.get(permission_names.get(x),  permission_names.get(x, '알 수 없음'))}`: 아니요 -> 네"
                for x in after_perms
                if x not in before_perms
            ]
        )
        if before_perms != after_perms:
            embed.add_field(name="권한", value="\n".join(diffs), inline=False)
        embed.set_footer(text=f"역할 ID: {role_update.role.id}")

        if not embed.fields:
            return

        if role_update.original.position != role_update.role.position:  # Prevent spam.
            embed.add_field(
                name="위치",
                value=f"`{role_update.original.position}`번째 -> `{role_update.role.position}`번째",
                inline=False,
            )
        await self.bot.execute_log(role_update.role.guild, embed=embed)

    @on("guild_ban_add")
    async def on_guild_ban_add(self, ban: GuildBanAdd):
        embed = Embed(
            title="멤버 차단",
            description=str(ban.user),
            color=EmbedColor.NEGATIVE,
            timestamp=kstnow(),
        )
        embed.set_thumbnail(url=ban.user.avatar_url())
        embed.set_footer(text=f"유저 ID: {ban.user.id}")
        await self.bot.execute_log(ban.guild, embed=embed)

    @on("guild_ban_remove")
    async def on_guild_ban_remove(self, ban: GuildBanRemove):
        embed = Embed(
            title="멤버 차단 해제",
            description=str(ban.user),
            color=EmbedColor.POSITIVE,
            timestamp=kstnow(),
        )
        embed.set_thumbnail(url=ban.user.avatar_url())
        embed.set_footer(text=f"유저 ID: {ban.user.id}")
        await self.bot.execute_log(ban.guild, embed=embed)

    @on("guild_member_update")
    async def on_guild_member_update(self, member: GuildMemberUpdate):
        if not member.original:
            return
        embed = Embed(
            title="멤버 정보 업데이트",
            description=member.mention + f" (`{member}`)",
            color=EmbedColor.NEUTRAL,
            timestamp=kstnow(),
        )
        if member.nick != member.original.nick:
            embed.add_field(
                name="닉네임",
                value=f"{member.original.nick or member.original.user.username} -> {member.nick or member.user.username}",
                inline=False,
            )
        if member.role_ids != member.original.role_ids:
            deleted = [x for x in member.original.role_ids if x not in member.role_ids]
            added = [x for x in member.role_ids if x not in member.original.role_ids]
            if added:
                embed.add_field(
                    name="추가된 역할",
                    value=", ".join([f"<@&{x}>" for x in added]),
                    inline=False,
                )
            if deleted:
                embed.add_field(
                    name="제거된 역할",
                    value=", ".join([f"<@&{x}>" for x in deleted]),
                    inline=False,
                )
        if not embed.fields:
            return
        embed.set_footer(text=f"유저 ID: {member.id}")
        await self.bot.execute_log(self.bot.get_guild(member.guild_id), embed=embed)

    @on("guild_member_add")
    async def on_guild_member_add(self, member: GuildMemberAdd):
        guild = self.bot.get_guild(member.guild_id)
        embed = Embed(
            title="새로운 멤버",
            description=member.mention + f" (`{member}`)",
            color=EmbedColor.POSITIVE,
            timestamp=kstnow(),
        )
        embed.set_thumbnail(url=member.avatar_url())
        embed.set_footer(text=f"유저 ID: {member.id}")
        maybe_me = guild.get(self.bot.user.id, "member")
        if member.user.bot and maybe_me and maybe_me.permissions.view_audit_log:
            with suppress(Exception):
                resp = await self.bot.request_guild_audit_log(
                    guild, action_type=AuditLogEvents.BOT_ADD, limit=10
                )
                resp = resp if isinstance(resp, list) else [resp]
                for x in resp:
                    found = False
                    for y in x.audit_log_entries:
                        if member.id == y.target.id:
                            embed.title = "새로운 봇 추가"
                            embed.add_field(
                                name="봇 추가자", value=f"<@!{y.user_id}>", inline=False
                            )
                            embed.footer.text += f"\n관리자 ID: {y.user_id}"
                            found = True
                            break
                    if found:
                        break
        await self.bot.execute_log(guild, embed=embed)

    @on("guild_member_add")
    async def execute_welcome(self, member: GuildMemberAdd):
        data = await self.bot.database.request_guild_setting(int(member.guild_id))
        if not data.welcome_channel:
            return
        if data.greet:
            await self.bot.create_message(
                data.welcome_channel, data.greet.format(mention=member.mention)
            )
        if data.greet_dm and member.user and not member.user.bot:
            with suppress(HTTPError):
                await member.user.send(
                    f"> `{self.bot.get_guild(member.guild_id).name}`에서 자동으로 전송한 환영 메세지에요.\n{data.greet_dm.format(name=str(member.user))}"
                )

    @on("guild_member_remove")
    async def on_guild_member_remove(self, member_delete: GuildMemberRemove):
        embed = Embed(
            title="멤버 퇴장",
            description=str(member_delete.member or member_delete.user),
            color=EmbedColor.NEGATIVE,
            timestamp=kstnow(),
        )
        if member_delete.member:
            embed.set_thumbnail(url=member_delete.member.avatar_url())
        embed.set_footer(text=f"유저 ID: {member_delete.user.id}")
        await self.bot.execute_log(member_delete.guild, embed=embed)

    @on("guild_member_remove")
    async def execute_goodbye(self, member_delete: GuildMemberRemove):
        data = await self.bot.database.request_guild_setting(
            int(member_delete.guild_id)
        )
        if not data.welcome_channel or not data.bye:
            return
        await self.bot.create_message(
            data.welcome_channel, data.bye.format(name=str(member_delete.user))
        )

    @on("message_reaction_remove_all")
    async def on_message_reaction_remove_all(self, remove: MessageReactionRemoveAll):
        try:
            msg = remove.message or await self.bot.request_channel_message(
                remove.channel_id, remove.message_id
            )
        except HTTPError:
            return
        embed = Embed(
            title="모든 반응 제거",
            description=f"[해당 메시지로 바로가기]({msg.link})",
            color=EmbedColor.NEGATIVE,
            timestamp=kstnow(),
        )
        embed.set_footer(text=f"메시지 ID: {remove.message_id}")
        await self.bot.execute_log(remove.guild, embed=embed)

    @on("invite_create")
    async def on_invite_create(self, invite: InviteCreate):
        embed = Embed(title="새 초대코드 생성", color=EmbedColor.POSITIVE, timestamp=kstnow())
        if invite.inviter:
            embed.add_field(
                name="초대코드를 생성한 멤버",
                value=invite.inviter.mention + f" (`{invite.inviter}`)",
                inline=False,
            )
        embed.add_field(name="초대코드", value=f"https://discord.gg/{invite.code}")
        if invite.inviter:
            embed.set_footer(text=f"멤버 ID: {invite.inviter.id}")
        await self.bot.execute_log(invite.guild, embed=embed)

    @on("invite_delete")
    async def on_invite_delete(self, invite: InviteDelete):
        embed = Embed(title="초대코드 삭제", color=EmbedColor.NEGATIVE, timestamp=kstnow())
        embed.add_field(name="삭제된 초대코드", value=f"https://discord.gg/{invite.code}")
        await self.bot.execute_log(invite.guild, embed=embed)


def load(bot: LaytheBot):
    bot.load_addons(Log)


def unload(bot: LaytheBot):
    bot.unload_addons(Log)
