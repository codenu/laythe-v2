from dico import Embed, Guild, Button, ActionRow, ButtonStyles, SelectMenu, SelectOption
from dico_interaction import InteractionContext, slash, component_callback, modal_callback, checks

from laythe import (
    LaytheBot,
    LaytheAddonBase,
    has_perm,
    Setting as SettingData
)
from laythe.utils import EmbedColor, kstnow, restrict_length


SETTING_METADATA = {"name": "설정", "description": "이 서버에서 레이테의 설정을 확인하거나 설정을 변경해요."}


class Setting(LaytheAddonBase, name="설정"):
    @staticmethod
    def get_enabled_functions(setting: SettingData):
        if not setting.flags:
            return
        returns = []
        if setting.flags.use_level:
            returns.append("레벨")
        return returns

    def create_setting_view_embed(self, setting: SettingData) -> Embed:
        embed = Embed(title="Laythe 설정 정보", color=EmbedColor.DEFAULT, timestamp=kstnow())
        embed.add_field(name="활성화된 기능", value=', '.join(self.get_enabled_functions(setting)) or "(없음)")
        embed.add_field(name="뮤트 역할", value=f"<@&{setting.mute_role}>" if setting.mute_role else "(없음)")
        embed.add_field(name="로그 채널", value=f"<#{setting.log_channel}>" if setting.log_channel else "(없음)")
        embed.add_field(name="환영 채널", value=f"<#{setting.welcome_channel}>" if setting.welcome_channel else "(없음)")
        embed.add_field(name="고정 채널", value=f"<#{setting.starboard_channel}>" if setting.starboard_channel else "(없음)")
        embed.add_field(name="환영 메시지", value=setting.greet or "(없음)")
        embed.add_field(name="DM 환영 메시지", value=setting.greet_dm or "(없음)")
        embed.add_field(name="작별 인사 메시지", value=setting.bye or "(없음)")
        return embed
    
    @staticmethod
    def create_level_reward_embed(setting: SettingData) -> Embed:
        embed = Embed(title="레벨 리워드 역할", color=EmbedColor.DEFAULT, timestamp=kstnow())
        embed.description = "\n".join((f"레벨 **{k}**: <@&{v}>" for k, v in setting.reward_roles.as_dict().items()))
        embed.set_footer(text="추가 또는 삭제는 \"/설정 변경\" 명령어를 사용해주세요.")
        return embed

    @slash(**SETTING_METADATA, subcommand="확인", subcommand_description="이 서버에서 레이테의 설정을 확인해요.")
    @checks(has_perm(manage_guild=True))
    async def setting_view(self, ctx: InteractionContext):
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        embed = self.create_setting_view_embed(setting)
        row = ActionRow()
        if setting.reward_roles:
            row.components.append(Button(style=ButtonStyles.SECONDARY, label="레벨 리워드 역할 보기", custom_id="view-level-reward"))
        await ctx.send(embed=embed, components=[row])

    @component_callback("view-guild-setting")
    async def view_guild_setting(self, ctx: InteractionContext):
        if ctx.author != ctx.message.interaction.user:
            return await ctx.send("❌ 이 버튼은 사용하실 수 없어요.", ephemeral=True)
        await ctx.defer(update_message=True)
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        embed = self.create_setting_view_embed(setting)
        row = ActionRow()
        if setting.reward_roles:
            row.components.append(Button(style=ButtonStyles.SECONDARY, label="레벨 리워드 역할 보기", custom_id="view-level-reward"))
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
            row.components.append(Button(style=ButtonStyles.SECONDARY, label="서버 설정 보기", custom_id="view-guild-setting"))
        await ctx.edit_original_response(embed=embed, components=[row])

    @slash(**SETTING_METADATA, subcommand="변경", subcommand_description="이 서버에서 레이테의 설정을 변경해요.")
    @checks(has_perm(manage_guild=True))
    async def setting_modify(self, ctx: InteractionContext):
        await ctx.defer()
        setting = await self.bot.database.request_guild_setting(int(ctx.guild_id))
        options = [SelectOption(label="기능 활성화", value="flags", description=f"활성화된 기능: {', '.join(self.get_enabled_functions(setting)) or '(없음)'}"),
                   SelectOption(label="뮤트 역할", value="mute_role", description=f"현재 설정: {setting.mute_role or '(없음)'}"),
                   SelectOption(label="로그 채널", value="log_channel", description=f"현재 설정: {setting.log_channel or '(없음)'}"),
                   SelectOption(label="환영 채널", value="welcome_channel", description=f"현재 설정: {setting.welcome_channel or '(없음)'}"),
                   SelectOption(label="고정 채널", value="starboard_channel", description=f"현재 설정: {setting.starboard_channel or '(없음)'}"),
                   SelectOption(label="환영 메시지", value="greet", description=f"현재 설정: {restrict_length(setting.greet, 50) or '(없음)'}"),
                   SelectOption(label="DM 환영 메시지", value="greet_dm", description=f"현재 설정: {restrict_length(setting.greet_dm, 50) or '(없음)'}"),
                   SelectOption(label="작별 인사 메시지", value="bye", description=f"현재 설정: {restrict_length(setting.bye, 50) or '(없음)'}"),
                   SelectOption(label="레벨 리워드 역할", value="reward_roles", description=f"현재 설정: {f'총 {len(setting.reward_roles.as_dict())}개' if setting.reward_roles else '(없음)'}"),
                   SelectOption(label="종료", value="exit")]
        row = ActionRow(SelectMenu(custom_id="setting-modify", options=options))
        await ctx.send("다음 중 변경하고 싶으신 기능을 선택해주세요.", components=[row])

    @component_callback("setting-modify")
    async def setting_modify_callback(self, ctx: InteractionContext):
        if ctx.author != ctx.message.interaction.user:
            return await ctx.send("❌ 이 메뉴는 사용하실 수 없어요.", ephemeral=True)


def load(bot: LaytheBot):
    bot.load_addons(Setting)


def unload(bot: LaytheBot):
    bot.unload_addons(Setting)
