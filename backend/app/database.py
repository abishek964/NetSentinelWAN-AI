from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from app.config import settings

# A connection pool keeps a small set of open connections to Neon ready to go,
# instead of opening a brand new connection for every single request
# (opening connections is slow — pooling avoids paying that cost every time).
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},  # rows come back as dicts, e.g. {"site_id": 1, "site_name": "Chennai HQ"}
)


def get_db():
    """
    FastAPI dependency: hands a route function a live database connection,
    and guarantees it's returned to the pool afterward (even if an error happens).
    """
    with pool.connection() as conn:
        yield conn
