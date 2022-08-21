from typing import Dict

from dico import (
    ActionRow,
    ApplicationCommandOptionChoice,
    ApplicationCommandOptionType,
    Button,
    ButtonStyles,
    Channel,
    Embed,
    Guild,
    Role,
    SelectMenu,
    SelectOption,
    Snowflake,
    TextInput,
    TextInputStyles,
)
from dico_interaction import (
    InteractionContext,
    checks,
    component_callback,
    modal_callback,
    option,
    slash,
)

from laythe import LaytheAddonBase, LaytheBot
from laythe import Setting as SettingData
from laythe import has_perm
from laythe.utils import EmbedColor, kstnow, restrict_length

SETTING_METADATA = {"name": "설정", "description": "이 서버에서 레이테의 설정을 확인하거나 설정을 변경해요."}
SETTING_MODIFY_METADATA = {
    **SETTING_METADATA,
    "subcommand_group": "변경",
    "subcommand_group_description": "이 서버에서 레이테의 설정을 변경해요.",
}


class Setting(LaytheAddonBase, name="설정"):
    buffer: Dict[Snowflake, SettingData]
    VOTE_AD: str = "혹시 레이테를 유용하게 사용하고 있으신가요? 잠깐 [여기](https://koreanbots.dev/bots/872349051620831292/vote)서 레이테에게 투표를 해주세요!"

    def on_load(self):
        self.buffer = {}

    @staticmethod
    def get_enabled_functions(setting: SettingData):
        if not setting.flags:
            return
        returns = []
        if setting.flags.use_level:
            returns.append("레벨")
        return returns

    def create_setting_view_embed(self, setting: SettingData) -> Embed:
        embed = Embed(
            title="Laythe 설정 정보", color=EmbedColor.DEFAULT, timestamp=kstnow()
        )
        embed.add_field(
            name="활성화된 기능",
            value=", ".join(self.get_enabled_functions(setting)) or "(없음)",
        )
        embed.add_field(
            name="뮤트 역할",
            value=f"<@&{setting.mute_role}>" if setting.mute_role else "(없음)",
        )
        embed.add_field(
            name="로그 채널",
            value=f"<#{setting.log_channel}>" if setting.log_channel else "(없음)",
        )
        embed.add_field(
            name="환영 채널",
            value=f"<#{setting.welcome_channel}>"
            if setting.welcome_channel
            else "(없음)",
        )
        embed.add_field(
            name="고정 채널",
            value=f"<#{setting.starboard_channel}>"
            if setting.starboard_channel
            else "(없음)",
        )
        embed.add_field(name="환영 메시지", value=setting.greet or "(없음)")
        embed.add_field(name="DM 환영 메시지", value=setting.greet_dm or "(없음)")
        embed.add_field(name="작별 인사 메시지", value=setting.bye or "(없음)")
        return embed

    @staticmethod
    def create_level_reward_embed(setting: SettingData) -> Embed:
        embed = Embed(title="레벨 보상 역할", color=EmbedColor.DEFAULT, timestamp=kstnow())
        embed.description = "\n".join(
            (f"레벨 **{k}**: <@&{v}>" for k, v in setting.reward_roles.as_dict().items())
        )
        embed.set_footer(text='추가 또는 삭제는 "/설정 변경 레벨보상" 명령어를 사용해주세요.')
        return embed

    @slash(
        **SETTING_METADATA,
        subcommand="확인",
        subcommand_description="이 서버에서 레이테의 설정을 확인해요.",
    )
    @checks(has_perm(manage_guild=True))
    async def setting_view(self, ctx: InteractionContext):
        await ctx.defer()
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        embed = self.create_setting_view_embed(setting)
        row = ActionRow(
            Button(
                style=ButtonStyles.SECONDARY,
                label="레벨 보상 역할 보기",
                custom_id="view-level-reward",
            )
        )
        await ctx.send(embed=embed, components=[row] if setting.reward_roles else [])
        await ctx.send(
            "혹시 더 편한 설정 방법을 찾고 있으신가요? [대시보드에서](https://laythe.codenu.kr/dashboard) 설정을 해보세요!"
        )

    @component_callback("view-guild-setting")
    async def view_guild_setting(self, ctx: InteractionContext):
        if ctx.author != ctx.message.interaction.user:
            return await ctx.send("❌ 이 버튼은 사용하실 수 없어요.", ephemeral=True)
        await ctx.defer(update_message=True)
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        embed = self.create_setting_view_embed(setting)
        row = ActionRow()
        if setting.reward_roles:
            row.components.append(
                Button(
                    style=ButtonStyles.SECONDARY,
                    label="레벨 보상 역할 보기",
                    custom_id="view-level-reward",
                )
            )
        await ctx.edit_original_response(embed=embed, components=[row])

    @component_callback("view-level-reward")
    async def view_level_reward(self, ctx: InteractionContext):
        if ctx.author != ctx.message.interaction.user:
            return await ctx.send("❌ 이 버튼은 사용하실 수 없어요.", ephemeral=True)
        await ctx.defer(update_message=True)
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        embed = self.create_level_reward_embed(setting)
        row = ActionRow()
        if setting.reward_roles:
            row.components.append(
                Button(
                    style=ButtonStyles.SECONDARY,
                    label="서버 설정 보기",
                    custom_id="view-guild-setting",
                )
            )
        await ctx.edit_original_response(embed=embed, components=[row])

    async def send_end_message(self, ctx: InteractionContext, as_update: bool = True):
        if as_update:
            await ctx.edit_original_response(
                content=f"✅ 설정을 종료했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}",
                components=[],
            )
        else:
            await ctx.send(f"✅ 설정을 종료했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}")

    @staticmethod
    def create_flags_menu(setting: SettingData):
        options = [
            SelectOption(
                label="레벨",
                description="활성화됨" if setting.flags.use_level else "비활성화됨",
                value="level",
            ),
            SelectOption(label="저장", value="save"),
        ]
        row = ActionRow(SelectMenu(custom_id="toggle-option", options=options))
        return row

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="기능",
        subcommand_description="레이테의 기능을 활성화하거나 비활성화해요.",
    )
    @checks(has_perm(manage_guild=True))
    async def start_toggle_option_setting(self, ctx: InteractionContext):
        if ctx.guild_id in self.buffer:
            return await ctx.send(
                "❌ 이미 다른 설정이 진행중인 것 같아요. 해당 설정을 마무리하고 재시도 해주세요.", ephemeral=True
            )
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        self.buffer[ctx.guild_id] = setting
        await ctx.send(
            content="활성화 또는 비활성화하고 싶은 기능을 선택해주세요.",
            components=[self.create_flags_menu(setting)],
        )

    @component_callback("toggle-option")
    async def setting_toggle_option(self, ctx: InteractionContext):
        # if ctx.author != ctx.message.interaction.user:
        #     return await ctx.send("❌ 이 메뉴는 사용하실 수 없어요.", ephemeral=True)
        if ctx.guild_id not in self.buffer:
            return await ctx.send(
                "⚠ 이런! 그 사이에 설정 기능에 변경사항이 있었던 것 같아요. 설정 명령어를 다시 사용해주세요.",
                components=[],
                update_message=True,
                ephemeral=True,
            )
        await ctx.defer(update_message=True)
        value = ctx.data.values[0]
        setting = self.buffer[ctx.guild_id]
        if value == "level":
            setting.flags.use_level = not setting.flags.use_level
            await ctx.send(
                f"✅ 레벨 기능을 {'활성화' if setting.flags.use_level else '비활성화'} 했어요.",
                ephemeral=True,
            )
        elif value == "save":
            await self.bot.database.update_guild_setting(setting)
            del self.buffer[ctx.guild_id]
            return await self.send_end_message(ctx)
        await ctx.edit_original_response(components=[self.create_flags_menu(setting)])

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="레벨보상",
        subcommand_description="레벨 보상을 추가하거나 삭제해요.",
        connector={"액션": "action", "레벨": "level", "역할": "role"},
    )
    @checks(has_perm(manage_guild=True))
    @option(
        ApplicationCommandOptionType.STRING,
        name="액션",
        description="보상을 추가하거나 삭제할 것인지 선택",
        required=True,
        choices=[
            ApplicationCommandOptionChoice("추가", "add"),
            ApplicationCommandOptionChoice("삭제", "remove"),
        ],
    )
    @option(
        ApplicationCommandOptionType.INTEGER,
        name="레벨",
        description="역할을 지급할 레벨",
        required=True,
    )
    @option(
        ApplicationCommandOptionType.ROLE,
        name="역할",
        description="레벨 보상을 추가할 경우 지급할 역할",
        required=False,
    )
    async def setting_reward_role(
        self, ctx: InteractionContext, action: str, level: int, role: Role = None
    ):
        if action == "add" and role is None:
            return await ctx.send("❌ 레벨 보상을 추가하는 경우 `역할` 옵션을 지정해주세요.", ephemeral=True)
        elif level < 1:
            return await ctx.send("❌ 레벨은 1 이상만 가능해요.", ephemeral=True)
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        if action == "add":
            setting.reward_roles[str(level)] = int(role)
        elif action == "remove":
            del setting.reward_roles[str(level)]
        await self.bot.database.update_guild_setting(setting)
        await ctx.send(
            f"✅ 성공적으로 레벨 **{level}** 보상을 {'추가' if action == 'add' else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="뮤트역할",
        subcommand_description="뮤트 역할을 설정해요.",
        connector={"역할": "role"},
    )
    @option(
        ApplicationCommandOptionType.ROLE,
        name="역할",
        description="뮤트 역할로 사용할 역할, 만약에 삭제를 원한다면 이 옵션을 지정하지 마세요.",
        required=False,
    )
    @checks(has_perm(manage_guild=True))
    async def setting_mute_role(self, ctx: InteractionContext, role: Role = None):
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        setting.mute_role = int(role) if role else role
        await self.bot.database.update_guild_setting(setting)
        await ctx.send(
            f"✅ 성공적으로 뮤트 역할을 {f'<@&{role.id}>으로 설정' if role else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="로그채널",
        subcommand_description="로그 채널을 설정해요.",
        connector={"채널": "channel"},
    )
    @option(
        ApplicationCommandOptionType.CHANNEL,
        name="채널",
        description="로그 채널로 사용할 채널, 만약에 삭제를 원한다면 이 옵션을 지정하지 마세요.",
        required=False,
    )
    @checks(has_perm(manage_guild=True))
    async def setting_log_channel(
        self, ctx: InteractionContext, channel: Channel = None
    ):
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        setting.log_channel = int(channel) if channel else channel
        await self.bot.database.update_guild_setting(setting)
        await ctx.send(
            f"✅ 성공적으로 로그 채널을 {f'<#{channel.id}>으로 설정' if channel else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="환영채널",
        subcommand_description="환영 채널을 설정해요.",
        connector={"채널": "channel"},
    )
    @option(
        ApplicationCommandOptionType.CHANNEL,
        name="채널",
        description="환영 채널로 사용할 채널, 만약에 삭제를 원한다면 이 옵션을 지정하지 마세요.",
        required=False,
    )
    @checks(has_perm(manage_guild=True))
    async def setting_welcome_channel(
        self, ctx: InteractionContext, channel: Channel = None
    ):
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        setting.welcome_channel = int(channel) if channel else channel
        await self.bot.database.update_guild_setting(setting)
        await ctx.send(
            f"✅ 성공적으로 환영 채널을 {f'<#{channel.id}>으로 설정' if channel else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="고정채널",
        subcommand_description="고정 채널을 설정해요.",
        connector={"채널": "channel"},
    )
    @option(
        ApplicationCommandOptionType.CHANNEL,
        name="채널",
        description="고정 채널로 사용할 채널, 만약에 삭제를 원한다면 이 옵션을 지정하지 마세요.",
        required=False,
    )
    @checks(has_perm(manage_guild=True))
    async def setting_log_channel(
        self, ctx: InteractionContext, channel: Channel = None
    ):
        await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        setting.log_channel = int(channel) if channel else channel
        await self.bot.database.update_guild_setting(setting)
        await ctx.send(
            f"✅ 성공적으로 고정 채널을 {f'<#{channel.id}>으로 설정' if channel else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )

    @slash(
        **SETTING_MODIFY_METADATA,
        subcommand="인사",
        subcommand_description="새 유저가 들어오거나 기존 유저가 나갈 때 전송할 인사말을 설정해요.",
        connector={"종류": "welcome_type"},
    )
    @option(
        ApplicationCommandOptionType.STRING,
        name="종류",
        description="설정할 인사의 종류를 설정해요.",
        required=True,
        choices=[
            ApplicationCommandOptionChoice("환영 메시지", "greet"),
            ApplicationCommandOptionChoice("DM 환영 메시지", "greet_dm"),
            ApplicationCommandOptionChoice("작별 인사 메시지", "bye"),
        ],
    )
    @checks(has_perm(manage_guild=True))
    async def setting_welcome(self, ctx: InteractionContext, welcome_type: str):
        # await ctx.defer(ephemeral=True)
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        value = getattr(setting, welcome_type)
        names = {"greet": "환영 메시지", "greet_dm": "DM 환영 메시지", "bye": "작별 인사 메시지"}
        text_input = TextInput(
            custom_id="welcome",
            style=TextInputStyles.PARAGRAPH,
            label=f"{names[welcome_type]}를 작성해주세요. 삭제를 원하시면 내용을 비워주세요.",
            max_length=1000,
            required=False,
            value=value,
            placeholder="환영 메시지에 '{mention}'을 널으면 그 부분에 유저 맨션이 들어가고, DM 환영/작별 인사 메시지에 '{name}'을 넣으면 유저의 이름이 들어가게 할 수 있어요.",
        )
        row = ActionRow(text_input)
        await ctx.send(
            title=f"{names[welcome_type]} 설정",
            custom_id=f"welcome_{welcome_type}",
            components=[row],
        )

    @modal_callback("welcome_")
    async def welcome_callback(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)
        welcome_type = ctx.data.custom_id.lstrip("welcome_")
        setting = await self.bot.database.request_guild_setting(
            int(ctx.guild_id), bypass_cache=True
        )
        value = ctx.get_value("welcome")
        setattr(setting, welcome_type, value)
        await self.bot.database.update_guild_setting(setting)
        names = {"greet": "환영 메시지", "greet_dm": "DM 환영 메시지", "bye": "작별 인사 메시지"}
        await ctx.send(
            f"✅ 성공적으로 {names[welcome_type]}를 {'설정' if value else '삭제'}했어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.\n{self.VOTE_AD}"
        )


def load(bot: LaytheBot):
    bot.load_addons(Setting)


def unload(bot: LaytheBot):
    bot.unload_addons(Setting)
