from typing import List, Optional


class Config:
    # Bot
    TOKEN: str = ""
    DEBUG: bool = False
    MONO_SHARD: bool = False
    TESTING_GUILDS: Optional[List[int]] = None

    # Bot List
    KBOT_TOKEN: str = ""
    UBOT_TOKEN: str = ""

    # Lavalink
    LAVA_HOST: str = ""
    LAVA_PORT: int = 0000
    LAVA_PW: str = ""

    # Database
    DB_HOST: str = ""
    DB_PORT: int = 0000
    DB_ID: str = ""
    DB_PW: str = ""
    DB_NAME: str = ""
