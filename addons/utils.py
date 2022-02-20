import datetime
import platform

import psutil

from typing import TYPE_CHECKING

from dico import (
    Ready,
    Embed,
    ActionRow,
    Button,
    ButtonStyles,
    ApplicationCommandOptionType,
    __version__ as dico_version,
    GuildMember,
)
from dico_command import Addon, on
from dico_interaction import (
    slash,
    option,
    checks,
    InteractionContext,
    __version__ as interaction_version,
)

from config import Config

from laythe import (
    utils,
    verification_level_translates,
    verification_desc_translates,
    rtc_region_translates,
    LaytheBot,
    LaytheAddonBase,
    has_perm,
    bot_has_perm,
)


INFO_METADATA = {"name": "정보", "description": "다양한 정보를 보여주는 명령어들이에요."}


class Utils(LaytheAddonBase, name="유틸리티"):
    @slash("핑", description="현재 봇의 레이턴시를 알려드려요.")
    async def ping(self, ctx: InteractionContext):
        await ctx.send(f"🏓 퐁! (`{round(self.bot.ping)}`ms)")

    @slash(**INFO_METADATA, subcommand="레이테", subcommand_description="레이테의 정보를 알려드려요.")
    async def info_laythe(self, ctx: InteractionContext):
        process = psutil.Process()
        uptime_sys = (
            datetime.datetime.now()
            - datetime.datetime.fromtimestamp(psutil.boot_time())
        ).total_seconds()
        uptime_bot = (
            datetime.datetime.now()
            - datetime.datetime.fromtimestamp(process.create_time())
        ).total_seconds()
        memory = psutil.virtual_memory()
        # node = self.bot.lavalink.node_manager.nodes[0].stats
        embed = Embed(
            title="레이테 정보",
            description="Developed and maintained by [CodeNU](https://discord.gg/gqJBhar).",
            color=utils.EmbedColor.DEFAULT,
            timestamp=ctx.id.timestamp,
        )
        embed.add_field(name="서버 수", value=f"`{self.bot.guild_count}`개", inline=False)
        embed.add_field(
            name="유저 수",
            value=f"`{self.bot.cache.get_storage('user').size}`명",
            inline=False,
        )
        embed.add_field(
            name="라이브러리 버전",
            value=f"<:python:815496209682006036> Python `{platform.python_version()}` | "
            f"<:soontm:919137921590784021> dico `{dico_version}` | "
            f"<:slash:815496477224468521> dico-interaction `{interaction_version}`\n",
            inline=False,
        )
        embed.add_field(
            name="업타임",
            value=f"서버: `{utils.parse_second_with_date(round(uptime_sys))}` | 봇: `{utils.parse_second_with_date(round(uptime_bot))}`",
            inline=False,
        )
        embed.add_field(
            name="레이테 서버 정보",
            value=f"CPU `{psutil.cpu_percent()}`% 사용중\n램 `{memory.percent}`% 사용중",
            inline=False,
        )
        """
        embed.add_field(name="Lavalink 정보",
                        value=f"총 `{node.players}`개 노드 (`{node.playing_players}`개 노드에서 재생중)\n노드 부하: `{round(node.lavalink_load * 100)}`%",
                        inline=False)
        """
        codenu = Button(
            style=ButtonStyles.LINK,
            label="CodeNU Web",
            emoji="<:codenu:919133992236765234>",
            url="https://codenu.github.io/",
        )
        github = Button(
            style=ButtonStyles.LINK,
            label="GitHub",
            emoji="<:github:872322613987389441>",
            url="https://github.com/codenu/laythe-v2",
        )
        privacy = Button(
            style=ButtonStyles.LINK,
            label="개인정보 취급 방침",
            emoji="📃",
            url="https://codenu.github.io/privacyPolicy.html",
        )
        row = ActionRow(codenu, github, privacy)
        await ctx.send(embed=embed, components=[row])

    @slash(
        **INFO_METADATA,
        subcommand="유저",
        subcommand_description="유저의 정보를 보여드려요.",
        connector={"유저": "member"},
    )
    @option(
        ApplicationCommandOptionType.USER,
        name="유저",
        description="정보를 볼 유저",
        required=False,
    )
    async def info_user(self, ctx: InteractionContext, member: GuildMember = None):
        member = member or ctx.author
        as_user_object = member.user
        join_time = int(member.joined_at.timestamp())
        embed = Embed(
            title="유저 정보", color=utils.EmbedColor.DEFAULT, timestamp=ctx.id.timestamp
        )
        embed.add_field(name="닉네임", value=f"{str(member)}", inline=False)
        embed.add_field(name="ID", value=f"{member.id}", inline=False)
        embed.add_field(
            name="계정 생성일",
            value=f"<t:{int(as_user_object.id.timestamp.timestamp())}>",
            inline=False,
        )
        embed.add_field(
            name="서버 입장일", value=f"<t:{join_time}> (<t:{join_time}:R>)", inline=False
        )
        # embed.add_field(name="최고 역할", value=f"<@&{int(member.role_ids[0])}>", inline=False)
        # TODO: top role finder
        embed.set_thumbnail(url=as_user_object.avatar_url())
        embed.set_author(name=str(as_user_object), icon_url=member.avatar_url())
        await ctx.send(embed=embed)

    @slash(**INFO_METADATA, subcommand="서버", subcommand_description="서버의 정보를 보여드려요.")
    async def info_server(self, ctx: InteractionContext):
        guild = self.bot.get_guild(ctx.guild_id) or await self.bot.request_guild(
            ctx.guild_id
        )
        vi = verification_level_translates.get(str(guild.verification_level).lower())
        vd = verification_desc_translates.get(str(guild.verification_level).lower())
        embed = Embed(
            title="서버 정보", color=utils.EmbedColor.DEFAULT, timestamp=ctx.id.timestamp
        )
        embed.add_field(name="소유자", value=f"<@!{guild.owner_id}>", inline=False)
        embed.add_field(name="유저 수", value=f"`{guild.member_count}`명", inline=False)
        embed.add_field(
            name="서버 생성일",
            value=f"<t:{int(guild.id.timestamp.timestamp())}>",
            inline=False,
        )
        embed.add_field(
            name="채널 수",
            value=f"총 `{guild.cache.get_storage('channel').size}`개\n"
            f"- 채팅 채널 `{len(tuple(x for x in guild.channels if x.type.guild_text))}`개\n"
            f"- 음성 채널 `{len(tuple(x for x in guild.channels if x.type.guild_voice or x.type.guild_stage_voice))}`개\n"
            f"- 카테고리 `{len(tuple(x for x in guild.channels if x.type.guild_category))}`개",
            inline=False,
        )
        embed.add_field(
            name="서버 부스트 레벨", value=f"`{int(guild.premium_tier)}`레벨", inline=False
        )
        embed.add_field(
            name="서버 부스트 수",
            value=f"`{guild.premium_subscription_count}`개 "
            f"(부스터 `{len(tuple(x for x in guild.members if x.premium_since))}`명)",
            inline=False,
        )
        embed.add_field(name="역할 수", value=f"`{len(guild.roles)}`개", inline=False)
        # embed.add_field(name="서버 최고 역할", value=guild.roles[-1].mention, inline=False)
        # embed.add_field(name="서버 위치", value=f"`{region}`", inline=False)
        embed.add_field(name="서버 보안 수준", value=f"`{vi}`\n{vd}", inline=False)
        embed.set_author(name=guild.name, icon_url=guild.icon_url())
        embed.set_thumbnail(url=guild.icon_url())
        embed.set_image(url=guild.banner_url())
        await ctx.send(embed=embed)

    @slash("구독", description="CodeNU 봇 공지에 구독해요.")
    @checks(has_perm(manage_webhooks=True), bot_has_perm(manage_webhooks=True))
    async def subscribe(self, ctx: InteractionContext):
        await ctx.defer()
        await self.bot.follow_news_channel(Config.NOTICE_CHANNEL, ctx.channel_id)
        await ctx.send("✅ 성공적으로 CodeNU 레이테 공지 채널에 구독했어요.")

    @on("ready")
    async def on_ready(self, ready: Ready):
        print(
            f"{f'Shard #{ready.shard_id}' if self.bot.monoshard else 'Bot'} dispatched READY event, "
            f"and this {'shard' if self.bot.monoshard else 'bot'} is managing {ready.guild_count} guilds."
        )

    @on("shards_ready")
    async def on_shards_ready(self):
        print("All shards ready.")


def load(bot: LaytheBot):
    bot.load_addons(Utils)


def unload(bot: LaytheBot):
    bot.unload_addons(Utils)
