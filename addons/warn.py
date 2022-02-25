from contextlib import suppress
from datetime import datetime

from dico import (
    ApplicationCommandOptionType,
    GuildMember,
    Embed,
    ActionRow,
    SelectMenu,
    SelectOption,
)
from dico.exception import HTTPError
from dico_interaction import (
    slash,
    option,
    checks,
    InteractionContext,
    component_callback,
)

from laythe import has_perm, DMNotAllowedAddonBase, LaytheBot, Warn as WarnData
from laythe.utils import EmbedColor


WARN_METADATA = {"name": "경고", "description": "경고와 관련된 명령어들이에요."}


class Warn(DMNotAllowedAddonBase, name="경고"):
    @slash(
        **WARN_METADATA,
        subcommand="추가",
        subcommand_description="유저에게 경고를 추가해요.",
        connector={"유저": "user", "사유": "reason"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="경고 추가 대상",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="사유",
        description="경고 추가의 사유",
        required=False,
    )
    @checks(has_perm(ban_members=True))
    async def warn_add(
        self, ctx: InteractionContext, user: GuildMember, reason: str = "없음"
    ):
        await ctx.defer()
        data = WarnData.create(
            guild_id=int(ctx.guild_id),
            date=int(ctx.id.timestamp.timestamp()),
            user_id=int(user),
            mod_id=int(ctx.author),
            reason=reason,
        )
        await self.bot.database.add_guild_warn(data)
        embed = Embed(
            title="유저 경고 추가", color=EmbedColor.NEGATIVE, timestamp=ctx.id.timestamp
        )
        embed.add_field(
            name="경고 대상",
            value=f"{user.mention} (`{user.user}` (ID: `{user.id}`))",
            inline=False,
        )
        embed.add_field(
            name="경고를 추가한 관리자",
            value=f"{ctx.member.mention} (`{ctx.author}` (ID: `{ctx.author.id}`))",
            inline=False,
        )
        embed.add_field(name="경고 ID", value=f"`{data.date}`", inline=False)
        embed.add_field(name="경고 사유", value=reason, inline=False)
        await self.bot.execute_log(self.bot.get_guild(ctx.guild_id), embed=embed)
        await ctx.send("✅ 성공적으로 경고를 추가했어요. 자세한 내용은 다음을 참고해주세요.", embed=embed)

    @slash(
        **WARN_METADATA,
        subcommand="삭제",
        subcommand_description="선택한 경고를 삭제해요.",
        connector={"id": "warn_id"},
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="id",
        description="삭제할 경고의 ID",
        required=True,
    )
    @checks(has_perm(ban_members=True))
    async def warn_remove(self, ctx: InteractionContext, warn_id: int):
        await ctx.defer()
        target = await self.bot.database.request_guild_warn(int(ctx.guild_id), warn_id)
        if not target:
            return await ctx.send(
                "❌ 해당 경고를 찾을 수 없어요. 올바른 ID인지 다시 확인해주세요.", ephemeral=True
            )
        await self.bot.database.remove_guild_warn(target)
        await ctx.send("✅ 성공적으로 해당 경고를 삭제했어요.")

    @slash(
        **WARN_METADATA,
        subcommand="목록",
        subcommand_description="자신 또는 선택한 유저가 받았던 모든 경고를 확인해요.",
        connector={"유저": "user"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="경고를 확인할 유저",
        required=False,
    )
    async def warn_list(self, ctx: InteractionContext, user: GuildMember = None):
        await ctx.defer()
        user = user or ctx.member
        warns = await self.bot.database.request_guild_warns(
            int(ctx.guild_id), int(user)
        )
        if not warns:
            return await ctx.send("❌ 경고 기록을 찾지 못했어요.")
        options = [
            SelectOption(label=f"경고 ID #{x.date}", value=str(x.date))
            for x in (
                x for i, x in enumerate(warns) if i < (25 if len(warns) == 25 else 24)
            )
        ]
        if len(warns) > 25:
            options.append(SelectOption(label="다음 페이지", value="npage24", emoji="➡"))
        menu = SelectMenu(custom_id="warn", options=options)
        row = ActionRow(menu)
        await ctx.send(f"ℹ 총 `{len(warns)}`개의 경고 기록을 찾았어요.", components=[row])

    @component_callback("warn")
    async def warn_show(self, ctx: InteractionContext):
        author = ctx.message.interaction.user
        if ctx.author.id != author.id:
            """
            with suppress(HTTPError):
                row = ctx.message.components[0]
                row.components[0].disabled = True
                await ctx.message.edit(components=[row])
            """
            return await ctx.send("❌ 이 목록은 사용하실 수 없어요.", ephemeral=True)
        value = ctx.data.values[0]
        if value.startswith("npage"):
            await ctx.defer(update_message=True)
            page = int(value.lstrip("npage")) + 1
            warns = await self.bot.database.request_guild_warns(
                int(ctx.guild_id), int(author)
            )
            if not warns:
                return await ctx.send(
                    "❌ 해당 유저의 경고 목록을 더이상 찾을 수 없어요. 혹시 이 목록이 생성된 지 오래됐나요? 명령어를 재실행해주세요.",
                    ephemeral=True,
                )
            after_warns = warns[page:]
            if not after_warns:
                after_warns = warns
            options = [
                SelectOption(label=f"경고 ID #{x.date}", value=str(x.date))
                for x in (
                    x
                    for i, x in enumerate(after_warns)
                    if i < (25 if len(after_warns) == 25 else 24)
                )
            ]
            if len(after_warns) > 25:
                options.append(
                    SelectOption(label="다음 페이지", value=f"npage{page+23}", emoji="➡")
                )
            row = ctx.message.components[0]
            row[0].options = options
            return await ctx.send(components=[row], update_message=True)
        await ctx.defer(ephemeral=True)
        warn_id = int(value)
        data = await self.bot.database.request_guild_warn(int(ctx.guild_id), warn_id)
        if not data:
            return await ctx.send(
                "❌ 해당 경고를 찾을 수 없어요. 혹시 이 목록이 생성된 지 오래됐나요? 명령어를 재실행해주세요."
            )

        user = None
        moderator = None
        with suppress(HTTPError):
            user = self.bot.get_user(data.user_id) or await self.bot.request_user(
                data.user_id
            )
        with suppress(HTTPError):
            moderator = self.bot.get_user(data.mod_id) or await self.bot.request_user(
                data.mod_id
            )

        embed = Embed(
            title=f"경고 정보 - #{data.date}",
            color=EmbedColor.NEGATIVE,
            timestamp=datetime.fromtimestamp(data.date),
        )
        embed.add_field(
            name="경고 대상",
            value=f"{user.mention} (`{user}` (ID: `{user.id}`))"
            if user
            else f"⚠ 해당 유저를 찾지 못했어요. (유저 ID: `{data.user_id}`)",
            inline=False,
        )
        embed.add_field(
            name="경고를 추가한 관리자",
            value=f"{moderator.mention} (`{moderator}` (ID: `{moderator.id}`))"
            if moderator
            else f"⚠ 관리자를 찾지 못했어요. (관리자 ID: `{data.mod_id}`)",
            inline=False,
        )
        embed.add_field(name="경고 ID", value=f"`{data.date}`", inline=False)
        embed.add_field(name="경고 사유", value=data.reason, inline=False)
        await ctx.send(embed=embed)


def load(bot: LaytheBot):
    bot.load_addons(Warn)


def unload(bot: LaytheBot):
    bot.unload_addons(Warn)
