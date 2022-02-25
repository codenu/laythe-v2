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
)
from dico_command import on
from dico_interaction import InteractionContext

from laythe import LaytheAddonBase, LaytheBot
from laythe.utils import kstnow, EmbedColor


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
        if message.author.bot:
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
        resp = await self.bot.execute_log(message.guild, embed=embed)
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
        embed = Embed(title="채널 생성", color=EmbedColor.POSITIVE, timestamp=kstnow())
        embed.add_field(
            name="채널 이름", value=f"{channel.mention} (`#{channel.name}`)", inline=False
        )
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_log(channel.guild, embed=embed)

    @on("channel_delete")
    async def on_channel_delete(self, channel: ChannelDelete):
        embed = Embed(title="채널 삭제", color=EmbedColor.NEGATIVE, timestamp=kstnow())
        embed.add_field(name="채널 이름", value=f"`#{channel.name}`", inline=False)
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_log(channel.guild, embed=embed)


def load(bot: LaytheBot):
    bot.load_addons(Log)


def unload(bot: LaytheBot):
    bot.unload_addons(Log)
