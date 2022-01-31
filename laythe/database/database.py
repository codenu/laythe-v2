from typing import Optional

from .base import BaseDatabase
from .models import LaytheSetting, Warn


class LaytheDB(BaseDatabase):
    async def request_guild_setting(self, guild_id: int) -> Optional[LaytheSetting]:
        resp = await self.fetch("SELECT * FROM settings WHERE guild_id=%s", (guild_id,))
        if resp:
            return LaytheSetting(resp[0])

    async def update_guild_setting(self, data: LaytheSetting):
        data = data.to_dict()
        guild_id = data.pop("guild_id")

        # TODO: better method?
        inject = ", ".join([f"{x}=%s" for x in data.keys()])
        await self.execute(
            f"UPDATE settings SET {inject} WHERE guild_id=%s",
            (*data.values(), guild_id),
        )

    async def request_guild_warns(self, guild_id: int, user_id: Optional[int] = None):
        query = "SELECT * FROM warns WHERE guild_id=%s" + (
            " AND user_id=%s" if user_id else ""
        )
        args = (guild_id, user_id) if user_id else (guild_id,)
        return await self.fetch(query, args)

    async def add_guild_warns(self, data: Warn):
        data = data.to_dict()
        await self.execute(
            "INSERT INTO warns VALUES (%s, %s, %s, %s, %s)", (*data.values(),)
        )
