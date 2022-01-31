import json

import aiomysql

from typing import Dict, Optional


class BaseDatabase:
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    @classmethod
    async def login(
        cls, host: str, port: int, login_id: str, login_pw: str, db_name: str
    ):
        connection = dict(
            host=host,
            port=port,
            user=login_id,
            password=login_pw,
            cursorclass=aiomysql.DictCursor,
            db=db_name,
        )
        pool = await aiomysql.create_pool(**connection, autocommit=True)
        return cls(pool)

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute(self, sql: str, param: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, param)

    async def fetch(self, sql: str, param: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, param)
                return await cur.fetchall()


class BaseFlag:
    def __init__(self, *args, **kwargs):
        self.values = {
            x: getattr(self, x) for x in dir(self) if isinstance(getattr(self, x), int)
        }
        self.value = 0
        for x in args:
            if x.upper() not in self.values:
                raise AttributeError(f"invalid name: `{x}`")
            self.value |= self.values[x.upper()]
        for k, v in kwargs.items():
            if k.upper() not in self.values:
                raise AttributeError(f"invalid name: `{k}`")
            if v:
                self.value |= self.values[k.upper()]

    def __int__(self):
        return self.value

    def __getattr__(self, item):
        return self.has(item)

    def __iter__(self):
        for k, v in self.values.items():
            if self.has(k):
                yield v

    def has(self, name: str):
        if name.upper() not in self.values:
            raise AttributeError(f"invalid name: `{name}`")
        return (self.value & self.values[name.upper()]) == self.values[name.upper()]

    def __setattr__(self, key, value):
        orig = key
        key = key.upper()
        if orig in ["value", "values"] or key not in self.values.keys():
            return super().__setattr__(orig, value)
        if not isinstance(value, bool):
            raise TypeError(f"only type `bool` is supported.")
        has_value = self.has(key)
        if value and not has_value:
            self.value |= self.values[key]
        elif not value and has_value:
            self.value &= ~self.values[key]

    def add(self, value):
        return self.__setattr(value, True)

    def remove(self, value):
        return self.__setattr(value, False)

    @classmethod
    def from_value(cls, value: int):
        ret = cls()
        ret.value = value
        return ret


class JSONStrInt:
    def __init__(self, data: str):
        self.__data: Dict[str, int] = json.loads(data)

    def __getitem__(self, item) -> Optional[int]:
        return self.__data.get(str(item))

    def __setitem__(self, key, value):
        self.__data[str(key)] = int(value)

    def as_dict(self) -> dict:
        return self.__data

    def to_str(self) -> str:
        return json.dumps(self.__data)
