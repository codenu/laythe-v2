import time
import random

from contextlib import suppress

from dico import (
    Message,
    GuildMember,
    Embed,
    ApplicationCommandOptionType,
    Button,
    ButtonStyles,
    ActionRow,
)
from dico.exception import HTTPError
from dico_command import on
from dico_interaction import slash, InteractionContext, option, component_callback

from laythe import LaytheAddonBase, LaytheBot
from laythe.utils import EmbedColor, create_index_bar


class Level(LaytheAddonBase, name="레벨"):
    @staticmethod
    def calc_exp_required(level: int) -> float:
        return 5 / 6 * level * (2 * level * level + 27 * level + 91)

    @slash("레벨", description="자신 또는 해당 유저의 레벨을 보여줘요.", connector={"유저": "user"})
    @option(ApplicationCommandOptionType.USER, name="유저", description="레벨 정보를 볼 유저")
    async def level(self, ctx: InteractionContext, user: GuildMember = None):
        await ctx.defer()
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        if not setting.flags.use_level:
            return await ctx.send("❌ 이 서버에서는 레벨 기능을 사용하지 않아요.")
        user = user or ctx.member
        level = await self.bot.database.request_level(int(ctx.guild_id), int(user))
        if not level:
            return await ctx.send("ℹ 해당 유저의 레벨 기록이 존재하지 않아요.")
        exp_req = self.calc_exp_required(level.level + 1)
        level_bar = create_index_bar(
            exp_req,
            level.exp,
            "<:01:955002128328425522>",
            "<:06:957278813941825576>",
            "<:02:955002128294871061>",
            "<:03:955002129246994435>",
            "<:04:955002128265519114>",
            "<:05:955002128257150988>",
            "<:07:957278813824352276>",
            12,
        )
        embed = Embed(
            title=f"레벨 {level.level} (#{level.rank})",
            description=f"> {level_bar} [**{level.exp}**/**{int(exp_req)}**]",
            color=EmbedColor.DEFAULT,
            timestamp=ctx.id.timestamp,
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url())
        embed.set_thumbnail(url=user.avatar_url())
        # embed.add_field(name="레벨", value=str(level.level))
        # embed.add_field(name="EXP", value=str(level.exp))
        # embed.add_field(name="다음 레벨까지 필요한 EXP", value=str(int(exp_req - level.exp)))
        await ctx.send(embed=embed)

    @slash("리더보드", description="이 서버의 레벨 리더보드를 보여줘요.")
    async def leaderboard(self, ctx: InteractionContext):
        await ctx.defer()
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        if not setting.flags.use_level:
            return await ctx.send("❌ 이 서버에서는 레벨 기능을 사용하지 않아요.")
        levels = await self.bot.database.request_guild_rank(int(ctx.guild_id))
        if not levels:
            return await ctx.send(
                "ℹ 아직 이 서버에서 레벨 기록이 존재하지 않아요. 레벨 기록이 쌓일 때 까지 조금만 더 기다려주세요."
            )
        await ctx.send("이런! ~~게으른 개발자 때문에~~ 아직 구현되지 않은 기능이에요.. 조금만 더 기다려주세요..")

    @slash("레벨리셋", description="이 서버 또는 해당 유저의 레벨을 리셋해요.", connector={"유저": "user"})
    @option(ApplicationCommandOptionType.USER, name="유저", description="레벨을 리셋할 유저")
    async def reset_level(self, ctx: InteractionContext, user: GuildMember = None):
        yes_button = Button(
            style=ButtonStyles.SUCCESS,
            emoji="⭕",
            custom_id=f"lvlresety{user.id if user else ''}",
        )
        no_button = Button(style=ButtonStyles.DANGER, emoji="❌", custom_id="lvlresetn")
        row = ActionRow(yes_button, no_button)
        await ctx.send(
            f"ℹ 정말로 {'이 서버의 전체' if not user else f'{user.mention}의'} 레벨을 리셋할까요?",
            components=[row],
            ephemeral=True,
        )

    @component_callback("lvlreset")
    async def reset_level_callback(self, ctx: InteractionContext):
        custom_id = ctx.data.custom_id.lstrip("lvlreset")
        if custom_id == "n":
            return await ctx.send("✅ 레벨 리셋을 취소했어요.", components=[], update_message=True)
        await ctx.defer(update_message=True)
        await self.bot.database.reset_level(
            int(ctx.guild_id), int(custom_id.lstrip("y") or "0")
        )
        await ctx.edit_original_response(content="✅ 성공적으로 레벨을 리셋했어요.", components=[])

    @slash("레벨제외", description="특정 채널을 레벨 시스템에서 제외시키는 방법을 알려줘요.")
    async def exclude_level(self, ctx: InteractionContext):
        await ctx.send(
            "ℹ 현재 자동 설정은 사용할 수 없어요. 원하시는 채널을 레벨에서 제외하기 위해서는 해당 채널의 주제에 다음 문구를 추가해주세요.\n> `laythe:leveloff`"
        )

    @on("message_create")
    async def on_message_create(self, message: Message):
        if (
            message.author.bot
            or not message.channel.guild_id
            or "laythe:leveloff" in (message.channel.topic or "")
        ):
            return

        setting = await self.bot.database.request_guild_setting(int(message.guild_id))
        if not setting.flags.use_level:
            return

        cached = await self.bot.database.get_last_message_timestamp(
            int(message.guild_id), int(message.author)
        )
        time_now = round(time.time())
        if cached and cached + 60 > time_now:
            return
        await self.bot.database.update_last_message_timestamp(
            int(message.guild_id), int(message.author)
        )

        current = await self.bot.database.request_level(
            int(message.guild_id), int(message.author)
        )
        level = current.level
        level_up = False

        current.exp += random.randint(5, 25)
        required_exp = self.calc_exp_required(level + 1)
        if required_exp < current.exp:
            current.level += 1
            level_up = True
            await message.channel.send(
                f"🎉 {message.author.mention}님의 레벨이 올라갔어요! (`{level}` -> `{current.level}`)"
            )
        await self.bot.database.update_level(current)
        if level_up:
            if not setting.reward_roles:
                return
            reward_roles = setting.reward_roles.as_dict()
            for k, v in sorted(reward_roles.items(), key=lambda n: n[0]):
                if current.level >= int(k):
                    if v in message.member.role_ids:
                        continue
                    with suppress(HTTPError):
                        await self.bot.add_guild_member_role(
                            message.guild_id, message.author, v, reason="레벨업 보상"
                        )
                else:
                    break


def load(bot: LaytheBot):
    bot.load_addons(Level)


def unload(bot: LaytheBot):
    bot.unload_addons(Level)
