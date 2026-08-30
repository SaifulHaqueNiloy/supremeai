import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
from alembic.config import main

main(["upgrade", "head"])
