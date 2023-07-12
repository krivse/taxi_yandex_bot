from dataclasses import dataclass

from environs import Env

from sqlalchemy.engine import URL


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int

    def construct_sqlalchemy_url(self) -> URL:
        return URL.create(
            drivername='postgresql+asyncpg',
            username=self.user,
            password=self.password,
            host=self.host,
            database=self.database,
            port=self.port
        )


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    X_Client_ID: dict
    X_API_Key: dict
    X_Park_ID: dict
    X_Idempotency_Token: dict


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            port=env.str('DP_PORT'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            X_Client_ID=env.str('X_Client_ID'),
            X_API_Key=env.str('X_API_Key'),
            X_Park_ID=env.str('X_Park_ID'),
            X_Idempotency_Token=env.str('X_Idempotency_Token')
        )
    )
