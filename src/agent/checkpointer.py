from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver

from agent.config import settings


@contextmanager
def get_checkpointer():
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        checkpointer.setup()  # idempotent: creates tables on first run, no-ops after
        yield checkpointer
