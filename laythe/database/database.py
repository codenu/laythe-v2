import json
import time
from typing import Any, List, Optional

from .base import BaseDatabase
from .models import Level, Setting, Warn


class LaytheDB(BaseDatabase):
    MAX_CACHE_VALID = 60 * 5  # 5 min

    async def on_cache_load(self):
        await self.cache.execute(
            """CREATE TABLE IF NOT EXISTS settings_cache
        ("guild_id" INTEGER NOT NULL PRIMARY KEY,
         "data" TEXT NOT NULL,
         "last_update_at" INTEGER NOT NULL)"""
        )
        await self.cache.execute(
            """CREATE TABLE IF NOT EXISTS level_cache ("guild_id" INTEGER NOT NULL, "user_id"INTEGER NOT NULL, "last_message_timestamp"INTEGER NOT NULL)"""
        )

    async def maybe_cache(self, key: str, value: Any, table: str) -> Optional[Any]:
        resp = await self.cache.fetch(
            f"""SELECT * FROM {table}_cache WHERE {key}=?""", (value,)
        )
        if not resp:
            return
        resp = resp[0]
        last_update_at = resp["last_update_at"]
        if time.time() - last_update_at > self.MAX_CACHE_VALID:
            return
        return resp["data"]

    async def update_cache(self, value: Any, table: str, data: Any):
        await self.cache.execute(
            f"""INSERT OR REPLACE INTO {table}_cache VALUES(?, ?, ?)""",
            (value, data, int(time.time())),
        )

    async def reset_cache(self, key: str, value: Any, table: str):
        await self.cache.execute(
            f"""DELETE FROM {table}_cache WHERE {key}=?""", (value,)
        )

    async def request_guild_setting(
        self, guild_id: int, bypass_cache: bool = False
    ) -> Optional[Setting]:
        if not bypass_cache:
            maybe_cache = await self.maybe_cache("guild_id", guild_id, "settings")
            if maybe_cache:
                return Setting(json.loads(maybe_cache))
        resp = await self.fetch("SELECT * FROM settings WHERE guild_id=%s", (guild_id,))
        if resp:
            await self.update_cache(guild_id, "settings", json.dumps(resp[0]))
            return Setting(resp[0])
        else:
            await self.reset_guild_setting(guild_id)
            return await self.request_guild_setting(guild_id)

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
        resp = await self.fetch(
            "SELECT *, RANK() OVER (PARTITION BY guild_id ORDER BY exp DESC) AS _rank FROM levels WHERE guild_id=%s ORDER BY exp DESC",
            (guild_id,),
        )
        if resp:
            return [Level(x) for x in resp]

    async def request_level(self, guild_id: int, user_id: int) -> Optional[Level]:
        resp = await self.fetch(
            "SELECT * FROM (SELECT *, RANK() OVER (PARTITION BY guild_id ORDER BY exp DESC) AS _rank FROM levels WHERE guild_id=%s) _levels WHERE user_id=%s",
            (guild_id, user_id),
        )
        if resp:
            return Level(resp[0])
        else:
            await self.execute(
                "INSERT INTO levels VALUES (%s, %s, %s, %s)", (user_id, guild_id, 0, 0)
            )
            return Level.create(user_id, guild_id, 0, 0)

    async def update_level(self, data: Level):
        data = data.to_dict()
        guild_id = data.pop("guild_id")
        user_id = data.pop("user_id")

        # TODO: better method?
        inject = ", ".join([f"{x}=%s" for x in data.keys()])
        await self.execute(
            f"UPDATE levels SET {inject} WHERE guild_id=%s AND user_id=%s",
            (*data.values(), guild_id, user_id),
        )

    async def reset_level(self, guild_id: int, user_id: int = None):
        param = [guild_id]
        if user_id:
            param.append(user_id)
        await self.execute(
            f"DELETE FROM levels WHERE guild_id=%s{' AND user_id=%s' if user_id else ''}",
            tuple(param),
        )

    async def get_last_message_timestamp(
        self, guild_id: int, user_id: int
    ) -> Optional[int]:
        resp = await self.cache.fetch(
            "SELECT last_message_timestamp FROM level_cache WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        if resp:
            return resp[0]["last_message_timestamp"]

    async def update_last_message_timestamp(self, guild_id: int, user_id: int):
        await self.cache.execute(
            "DELETE FROM level_cache WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        await self.cache.execute(
            "INSERT INTO level_cache VALUES (?, ?, ?)",
            (guild_id, user_id, int(time.time())),
        )
