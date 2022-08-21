import datetime
from contextlib import suppress
from logging import Logger
from typing import Optional, Union

from dico import AllowedMentions, Embed, Guild, GuildMember, Intents, User
from dico.exception import HTTPError
from dico_command import Bot, Message
from dico_interaction import AutoComplete, ComponentCallback
from dico_interaction import InteractionClient as InteractionBase
from dico_interaction import InteractionCommand, InteractionContext

from config import Config

from .database import LaytheDB, Warn
from .utils import EmbedColor, kstnow

try:
    from extlib.klist import KListClient
    from extlib.nugrid import NUgridClient, NUgridHandler
    from extlib.spellchecker import SpellChecker
except ImportError:
    import sys

    print("extlib missing, `/맞춤법` command and klist-related features disabled.")
    KListClient = None
    SpellChecker = None
    NUgridClient = None
    NUgridHandler = None


class InteractionClient(InteractionBase):
    async def handle_interaction(
        self,
        target: Union[InteractionCommand, ComponentCallback, AutoComplete],
        interaction: InteractionContext,
    ):
        if isinstance(target, InteractionCommand) and not interaction.guild_id:
            return await interaction.send("❌ 명령어는 DM에서 사용할 수 없어요.")
        return await super().handle_interaction(target, interaction)


class LaytheBot(Bot):
    interaction: InteractionClient
    database: LaytheDB
    nugrid: NUgridClient

    def __init__(self, *, logger: Logger):
        intents = Intents.no_privileged()
        intents.guild_members = True
        super().__init__(
            Config.TOKEN,
            self.get_prefix,
            intents=intents,
            default_allowed_mentions=AllowedMentions(everyone=False),
            monoshard=Config.MONO_SHARD,
        )
        self.laythe_logger = logger
        InteractionClient(
            client=self,
            guild_ids_lock=Config.TESTING_GUILDS,
            auto_register_commands=bool(Config.TESTING_GUILDS),
        )
        self.loop.create_task(self.setup_bot())
        self.klist = (
            KListClient(self, Config.KBOT_TOKEN, self.http.session)
            if KListClient
            else KListClient
        )  # noqa
        self.spell = (
            SpellChecker(self.http.session) if SpellChecker else SpellChecker
        )  # noqa
        self.nugrid = NUgridClient(
            Config.NUGRID_HOST, session=self.http.session, loop=self.loop
        )
        self.nugrid_handler = NUgridHandler(self.nugrid)

    async def setup_bot(self):
        await self.wait_ready()
        self.database = await LaytheDB.login(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            login_id=Config.DB_ID,
            login_pw=Config.DB_PW,
            db_name=Config.DB_NAME,
        )
        if self.klist and not Config.DEBUG:
            self.klist.create_guild_count_task()
        if self.nugrid:
            self.nugrid.headers = {
                "Authentication": Config.NUGRID_PASSWORD,
                "Client": str(self.user.id),
            }
            self.loop.create_task(self.nugrid.start())

    async def get_prefix(self, message: Message):
        await self.wait_ready()
        if message.content.split()[0] in [f"<@{self.user.id}>", f"<@!{self.user.id}>"]:
            return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]
        else:
            return [f"<@{self.user.id}>", f"<@!{self.user.id}>"]

    async def execute_log(self, guild: Guild, **kwargs):
        setting = await self.database.request_guild_setting(int(guild))
        if not setting.log_channel:
            return
        with suppress(HTTPError):  # ignore sending failure
            # TODO: use cache?
            webhooks = await self.request_channel_webhooks(setting.log_channel)
            filtered = [
                *filter(lambda w: w.user == self.user and w.name == "서버 로깅", webhooks)
            ]
            if not filtered:
                webhook = await self.create_webhook(setting.log_channel, name="서버 로깅")
            else:
                webhook = webhooks[0]
            kwargs["username"] = guild.name
            kwargs["avatar_url"] = guild.icon_url()
            return await webhook.execute(**kwargs)

    async def add_warn(
        self,
        guild: Guild.TYPING,
        date: datetime.datetime,
        user: Union[User.TYPING, GuildMember.TYPING],
        mod: Union[User.TYPING, GuildMember.TYPING],
        reason: str,
    ) -> Embed:
        data = Warn.create(
            guild_id=int(guild),
            date=int(date.timestamp()),
            user_id=int(user),
            mod_id=int(mod),
            reason=reason,
        )
        await self.database.add_guild_warn(data)
        settings = await self.database.request_guild_setting(int(guild))
        warn_action = ""
        if settings.warn_actions:
            warns = await self.database.request_guild_warns(int(guild), int(user))
            actions = settings.warn_actions.as_dict()
            action = actions.get(str(len(warns)), "")
            with suppress(HTTPError):
                if action == "mute" and settings.mute_role:
                    await self.add_guild_member_role(
                        guild, user, settings.mute_role, reason="경고 액션"
                    )
                    warn_action = "뮤트 역할 추가"
                elif action.startswith("timeout"):
                    days = action.lstrip("timeout")
                    delta = (
                        datetime.timedelta(days=int(days))
                        if days
                        else datetime.timedelta(hours=1)
                    )
                    end_at = datetime.datetime.utcnow() + delta
                    await self.modify_guild_member(
                        guild, user, communication_disabled_until=end_at
                    )
                    warn_action = f"{f'{days}일' if days else '1시간'} 타임아웃"
                elif action == "kick":
                    await self.remove_guild_member(guild, user)
                    warn_action = "추방"
                elif action == "ban":
                    await self.create_guild_ban(guild, user)
                    warn_action = "차단"
        cached_guild = self.get_guild(int(guild))
        cached_target, cached_manager = None, None
        if cached_guild:
            cached_target = cached_guild.get(int(user), "member") or self.get_user(
                int(user)
            )
            cached_manager = cached_guild.get(int(mod), "member") or self.get_user(
                int(mod)
            )
        embed = Embed(title="유저 경고 추가", color=EmbedColor.NEGATIVE, timestamp=date)
        embed.add_field(
            name="경고 대상",
            value=f"<@!{int(user)}> (`{str(cached_target) if cached_target else '(알 수 없음)'}` (ID: `{int(user)}`))",
            inline=False,
        )
        embed.add_field(
            name="경고를 추가한 관리자",
            value=f"<@!{int(mod)}> (`{str(cached_manager) if cached_manager else '(알 수 없음)'}` (ID: `{int(mod)}`))",
            inline=False,
        )
        embed.add_field(name="경고 ID", value=f"`{data.date}`", inline=False)
        embed.add_field(name="경고 사유", value=reason, inline=False)
        if warn_action:
            embed.add_field(name="경고 액션", value=warn_action, inline=False)
        if cached_guild:
            await self.execute_log(cached_guild, embed=embed)
        return embed

    async def remove_warn(self, guild: Guild.TYPING, warn_id: int) -> Optional[Warn]:
        target = await self.database.request_guild_warn(int(guild), warn_id)
        if not target:
            return None
        await self.database.remove_guild_warn(target)
        cached_guild = self.get_guild(int(guild))
        if cached_guild:
            cached_target = cached_guild.get(target.user_id, "member") or self.get_user(
                int(target.user_id)
            )
            cached_manager = cached_guild.get(target.mod_id, "member") or self.get_user(
                int(target.mod_id)
            )
            embed = Embed(
                title="유저 경고 삭제", color=EmbedColor.NEGATIVE, timestamp=kstnow()
            )
            embed.add_field(name="삭제된 경고 ID", value=f"`{target.date}`", inline=False)
            embed.add_field(
                name="경고 대상",
                value=f"<@!{target.user_id}> (`{str(cached_target) if cached_target else '(알 수 없음)'}` (ID: `{target.user_id}`))",
                inline=False,
            )
            embed.add_field(
                name="경고를 추가한 관리자",
                value=f"<@!{target.mod_id}> (`{str(cached_manager) if cached_manager else '(알 수 없음)'}` (ID: `{target.mod_id}`))",
                inline=False,
            )
            embed.add_field(name="경고 사유", value=target.reason or "없음", inline=False)
            await self.execute_log(cached_guild, embed=embed)
        return target

    async def close(self):
        await self.database.close()
        await self.nugrid.close()
        await super().close()
