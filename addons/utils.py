import datetime
import platform

import psutil

from typing import TYPE_CHECKING

from dico import Ready, Embed, ActionRow, Button, ButtonStyles, __version__ as dico_version, GuildMember
from dico_command import Addon, on
from dico_interaction import slash, InteractionContext, __version__ as interaction_version

from modules import utils

if TYPE_CHECKING:
    from modules.bot import LaytheBot


class Utils(Addon, name="유틸리티"):
    bot: "LaytheBot"

    @slash("ping", description="현재 봇의 레이턴시를 알려줘요.")
    async def ping(self, ctx: InteractionContext):
        await ctx.send(f"🏓 퐁! (`{round(self.bot.ping)}`ms)")

    @slash("info", description="레이테의 정보를 알려드려요.")
    async def info(self, ctx: InteractionContext):
        process = psutil.Process()
        uptime_sys = (datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        uptime_bot = (datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())).total_seconds()
        memory = psutil.virtual_memory()
        # node = self.bot.lavalink.node_manager.nodes[0].stats
        embed = Embed(title="레이테 정보",
                      description="Developed and maintained by [CodeNU](https://discord.gg/gqJBhar).",
                      color=utils.EmbedColor.DEFAULT,
                      timestamp=ctx.id.timestamp)
        embed.add_field(name="서버 수", value=f"`{self.bot.guild_count}`개", inline=False)
        embed.add_field(name="유저 수", value=f"`{self.bot.cache.get_storage('user').size}`명", inline=False)
        embed.add_field(name="라이브러리 버전",
                        value=f"<:python:815496209682006036> Python `{platform.python_version()}` | "
                              f"<:soontm:919137921590784021> dico `{dico_version}` | "
                              f"<:slash:815496477224468521> dico-interaction `{interaction_version}`\n",
                        inline=False)
        embed.add_field(name="업타임",
                        value=f"서버: `{utils.parse_second_with_date(round(uptime_sys))}` | 봇: `{utils.parse_second_with_date(round(uptime_bot))}`",
                        inline=False)
        embed.add_field(name="레이테 서버 정보", value=f"CPU `{psutil.cpu_percent()}`% 사용중\n램 `{memory.percent}`% 사용중",
                        inline=False)
        """
        embed.add_field(name="Lavalink 정보",
                        value=f"총 `{node.players}`개 노드 (`{node.playing_players}`개 노드에서 재생중)\n노드 부하: `{round(node.lavalink_load * 100)}`%",
                        inline=False)
        """
        codenu = Button(style=ButtonStyles.LINK, label="CodeNU Web", emoji="<:codenu:919133992236765234>", url="https://codenu.github.io/")
        github = Button(style=ButtonStyles.LINK, label="GitHub", emoji="<:github:872322613987389441>", url="https://github.com/codenu/laythe-v2")
        row = ActionRow(codenu, github)
        await ctx.send(embed=embed, components=[row])

    @slash("유저정보", description="유저의 정보를 보여줘요.")
    async def user_info(self, ctx: InteractionContext, member: GuildMember = None):
        member = member or ctx.author
        as_user_object = member.user
        join_time = int(member.joined_at.timestamp())
        embed = Embed(title="유저 정보", color=utils.EmbedColor.DEFAULT, timestamp=ctx.id.timestamp)
        embed.add_field(name="닉네임", value=f"{str(member)}", inline=False)
        embed.add_field(name="ID", value=f"{member.id}", inline=False)
        embed.add_field(name="계정 생성일", value=f"<t:{int(as_user_object.id.timestamp.timestamp())}>", inline=False)
        embed.add_field(name="서버 입장일", value=f"<t:{join_time}> (<t:{join_time}:R>)", inline=False)
        # embed.add_field(name="최고 역할", value=f"<@&{int(member.role_ids[0])}>", inline=False)
        # TODO: top role finder
        embed.set_thumbnail(url=as_user_object.avatar_url())
        embed.set_author(name=str(as_user_object), icon_url=member.avatar_url())
        await ctx.send(embed=embed)

    @on("ready")
    async def on_ready(self, ready: Ready):
        print(f"{f'Shard #{ready.shard_id}' if self.bot.monoshard else 'Bot'} dispatched READY event, "
              f"and this {'shard' if self.bot.monoshard else 'bot'} is managing {ready.guild_count} guilds.")

    @on("shards_ready")
    async def on_shards_ready(self):
        print("All shards ready.")


def load(bot: "LaytheBot"):
    bot.load_addons(Utils)


def unload(bot: "LaytheBot"):
    bot.unload_addons(Utils)
