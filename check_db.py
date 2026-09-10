import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5435")
DB_NAME = os.environ.get("DB_NAME", "avantages_sportifs")

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM distances_domicile_bureau")).scalar()
    print("Lignes dans distances_domicile_bureau :", n)