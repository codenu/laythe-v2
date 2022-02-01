from typing import Optional, List

from .base import BaseDatabase
from .models import Setting, Warn, Level


class LaytheDB(BaseDatabase):
    async def request_guild_setting(self, guild_id: int) -> Optional[Setting]:
        resp = await self.fetch("SELECT * FROM settings WHERE guild_id=%s", (guild_id,))
        if resp:
            return Setting(resp[0])

    async def update_guild_setting(self, data: Setting):
        data = data.to_dict()
        guild_id = data.pop("guild_id")

        # TODO: better method?
        inject = ", ".join([f"{x}=%s" for x in data.keys()])
        await self.execute(
            f"UPDATE settings SET {inject} WHERE guild_id=%s",
            (*data.values(), guild_id),
        )

    async def delete_guild_setting(self, guild_id: int):
        await self.execute("DELETE FROM settings WHERE guild_id=%s", (guild_id,))

    async def reset_guild_setting(self, guild_id: int):
        await self.delete_guild_setting(guild_id)
        await self.execute("INSERT INTO settings(guild_id) VALUES (%s)", (guild_id,))

    async def request_guild_warns(
        self, guild_id: int, user_id: Optional[int] = None
    ) -> Optional[List[Warn]]:
        query = "SELECT * FROM warns WHERE guild_id=%s" + (
            " AND user_id=%s" if user_id else ""
        )
        args = (guild_id, user_id) if user_id else (guild_id,)
        resp = await self.fetch(query, args)
        if resp:
            return [Warn(x) for x in resp]

    async def request_guild_warn(self, guild_id: int, date: int) -> Optional[Warn]:
        resp = await self.fetch(
            "SELECT * FROM warns WHERE guild_id=%s AND date=%s", (guild_id, date)
        )
        if resp:
            return Warn(resp[0])

    async def add_guild_warn(self, data: Warn):
        data = data.to_dict()
        await self.execute(
            "INSERT INTO warns VALUES (%s, %s, %s, %s, %s)", (*data.values(),)
        )

    async def remove_guild_warn(self, data: Warn):
        await self.execute(
            "DELETE FROM warns WHERE guild_id=%s AND user_id=%s AND mod_id=%s AND date=%s",
            (data.guild_id, data.user_id, data.mod_id, data.date),
        )

    async def request_guild_rank(self, guild_id: int) -> Optional[List[Level]]:
        resp = await self.fetch("SELECT * FROM levels WHERE guild_id=%s", (guild_id,))
        if resp:
            return [Level(x) for x in resp]

    async def request_level(self, guild_id: int, user_id: int) -> Optional[Level]:
        resp = await self.fetch("SELECT * FROM levels WHERE guild_id=%s AND user_id=%s", (guild_id, user_id))
        if resp:
            return Level(resp[0])

    async def update_level(self, data: Level):
        data = data.to_dict()
        guild_id = data.pop("guild_id")

        # TODO: better method?
        inject = ", ".join([f"{x}=%s" for x in data.keys()])
        await self.execute(f"UPDATE levels SET {inject} WHERE guild_id=%s", (*data.values(), guild_id))
