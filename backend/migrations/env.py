from alembic import context
from sqlalchemy import create_engine

from app.config import Settings
from app.models import Base

settings = Settings()
settings.require_database()
if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
