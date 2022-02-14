import time
import json

from typing import Optional, List, Any

from .base import BaseDatabase
from .models import Setting, Warn, Level


class LaytheDB(BaseDatabase):
    MAX_CACHE_VALID = 60 * 5  # 5 min

    async def on_cache_load(self):
        await self.cache.execute("""CREATE TABLE IF NOT EXISTS settings_cache
        ("guild_id" INTEGER NOT NULL PRIMARY KEY,
         "data" TEXT NOT NULL,
         "last_update_at" INTEGER NOT NULL)""")

    async def maybe_cache(self, key: str, value: Any, table: str) -> Optional[Any]:
        resp = await self.cache.fetch(f"""SELECT * FROM {table}_cache WHERE {key}=?""", (value,))
        if not resp:
            return
        resp = resp[0]
        last_update_at = resp["last_update_at"]
        if time.time() - last_update_at > self.MAX_CACHE_VALID:
            return
        return resp["data"]

    async def update_cache(self, value: Any, table: str, data: Any):
        await self.cache.execute(f"""INSERT OR REPLACE INTO {table}_cache VALUES(?, ?, ?)""",
                                 (value, data, time.time()))

    async def request_guild_setting(self, guild_id: int, bypass_cache: bool = False) -> Optional[Setting]:
        if not bypass_cache:
            maybe_cache = await self.maybe_cache("guild_id", guild_id, "settings")
            if maybe_cache:
                return Setting(json.loads(maybe_cache))
        resp = await self.fetch("SELECT * FROM settings WHERE guild_id=%s", (guild_id,))
        if resp:
            await self.update_cache(guild_id, "settings", json.dumps(resp[0]))
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
        resp = await self.fetch(
            "SELECT * FROM levels WHERE guild_id=%s AND user_id=%s", (guild_id, user_id)
        )
        if resp:
            return Level(resp[0])

    async def update_level(self, data: Level):
        data = data.to_dict()
        guild_id = data.pop("guild_id")

        # TODO: better method?
        inject = ", ".join([f"{x}=%s" for x in data.keys()])
        await self.execute(
            f"UPDATE levels SET {inject} WHERE guild_id=%s", (*data.values(), guild_id)
        )
