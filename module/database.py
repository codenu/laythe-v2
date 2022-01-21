import aiomysql


class LaytheDB:
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
