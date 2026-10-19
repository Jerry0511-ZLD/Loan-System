from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


def _upgrade_schema(conn) -> None:
    """给已存在的表补上模型里新增的列。

    MVP 没有引入 Alembic，而 create_all 只会建新表、不会给老表加字段。
    这里做一个最小可用的「补列」逻辑：对比 ORM 模型与库里实际的列，缺哪列补哪列。
    SQLite 的 ALTER TABLE 只支持 ADD COLUMN，对本项目的增量演进够用；
    真正需要改类型 / 删列 / 加约束时，应当引入 Alembic 做版本化迁移。
    """
    inspector = inspect(conn)
    added: list[str] = []
    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            col_type = column.type.compile(dialect=conn.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
            default = column.default
            if default is not None and getattr(default, "is_scalar", False):
                value = default.arg
                if isinstance(value, bool):
                    ddl += f" DEFAULT {1 if value else 0}"
                elif isinstance(value, (int, float)):
                    ddl += f" DEFAULT {value}"
                elif isinstance(value, str):
                    escaped = value.replace("'", "''")
                    ddl += f" DEFAULT '{escaped}'"
            print(f"[init_db] 检测到新增字段，已补充：{table.name}.{column.name}")
            conn.execute(text(ddl))
            added.append(f"{table.name}.{column.name}")

    # 数据回填：新增字段对老记录一律取默认值。review_required 默认 False，
    # 会把历史上「已转人工、还没人处理」的单子漏掉（管理端待办列表就看不到它们）。
    # 所以补完列后按决策记录反查一次，把这类单子标记回 True。
    # 这条语句是幂等的：人工处理过的单子状态已不是 PENDING，不会被误改。
    if "applications.review_required" in added:
        conn.execute(
            text(
                """
                UPDATE applications
                   SET review_required = 1
                 WHERE status = 'PENDING'
                   AND id IN (
                       SELECT application_id FROM decisions
                        WHERE status IN ('MANUAL', 'manual')
                   )
                """
            )
        )
        print("[init_db] 已按历史决策记录回填 review_required")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_upgrade_schema)
