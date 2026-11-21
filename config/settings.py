import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPICS = {
    "meteo": "energie.meteo.raw",
    "pannes": "energie.pannes.raw",
    "alertes": "energie.alertes.xml",
}

PG_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "energie_qc"),
    "user": os.getenv("POSTGRES_USER", "admin_ia"),
    "password": os.getenv("POSTGRES_PASSWORD", "password_dev"),
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin_ia:password_dev@localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "energie_qc_raw")
