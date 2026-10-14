from alembic import context
from sqlalchemy import create_engine

from app.config import Settings
from app.models import Base

settings = Settings()
url = context.config.attributes.get("database_url") or settings.database_url
if not url:
    settings.require_database()
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
