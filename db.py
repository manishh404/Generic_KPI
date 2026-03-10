from sqlalchemy import create_engine

DB_USER = "dtwinuser"
DB_PASS = "bAnVojEFJSpYW9W0"
DB_HOST = "114.143.58.70"
DB_PORT = "8503"
DB_NAME = "poc-digital-twin"

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


schema = "Methanol_KPI_Gen"
