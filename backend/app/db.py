from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# The regulatory scheduler uses a distinct least-privilege database login.
# Its login role is granted membership in toolkit_regulatory_scheduler.
scheduler_engine = None
SchedulerSessionLocal = None
if settings.scheduler_database_url:
    scheduler_engine = create_engine(settings.scheduler_database_url, pool_pre_ping=True)

    @event.listens_for(scheduler_engine, "connect")
    def _set_regulatory_scheduler_role(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET ROLE toolkit_regulatory_scheduler")
        finally:
            cursor.close()

    SchedulerSessionLocal = sessionmaker(bind=scheduler_engine, autoflush=False, autocommit=False)
