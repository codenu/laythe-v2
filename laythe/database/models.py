from .base import BaseFlag, JSONStrInt


class LaytheSettingFlags(BaseFlag):
    USE_LEVEL = 1 << 0


class RewardRoles(JSONStrInt):
    pass


class WarnActions(JSONStrInt):
    pass


class Setting:
    def __init__(self, data: dict):
        self.guild_id: int = data["guild_id"]
        self.accepted: bool = data["accepted"]
        self.custom_prefix: str = data["custom_prefix"]
        self.flags: LaytheSettingFlags = LaytheSettingFlags.from_value(data["flags"])
        self.mute_role: int = data["mute_role"]
        self.log_channel: int = data["log_channel"]
        self.welcome_channel: int = data["welcome_channel"]
        self.starboard_channel: int = data["starboard_channel"]
        self.greet: str = data["greet"]
        self.greet_dm: str = data["greet_dm"]
        self.bye: str = data["bye"]
        self.reward_roles: RewardRoles = RewardRoles(data["reward_roles"] or "{}")
        self.warn_actions: WarnActions = WarnActions(data["warn_actions"] or "{}")

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "accepted": self.accepted,
            "custom_prefix": self.custom_prefix,
            "flags": self.flags.value,
            "mute_role": self.mute_role,
            "log_channel": self.log_channel,
            "welcome_channel": self.welcome_channel,
            "starboard_channel": self.starboard_channel,
            "greet": self.greet,
            "greet_dm": self.greet_dm,
            "bye": self.bye,
            "reward_roles": self.reward_roles.to_str(),
            "warn_actions": self.warn_actions.to_str(),
        }


class Warn:
    def __init__(self, data: dict):
        self.guild_id: int = data["guild_id"]
        self.date: int = data["date"]
        self.user_id: int = data["user_id"]
        self.mod_id: int = data["mod_id"]
        self.reason: str = data["reason"]

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "date": self.date,
            "user_id": self.user_id,
            "mod_id": self.mod_id,
            "reason": self.reason,
        }

    @classmethod
    def create(cls, guild_id: int, date: int, user_id: int, mod_id: int, reason: str):
        return cls(
            {
                "guild_id": guild_id,
                "date": date,
                "user_id": user_id,
                "mod_id": mod_id,
                "reason": reason,
            }
        )


class Level:
    def __init__(self, data: dict):
        self.user_id: int = data["user_id"]
        self.guild_id: int = data["guild_id"]
        self.exp: int = data["exp"]
        self.level: int = data["level"]

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "exp": self.exp,
            "level": self.level,
        }
