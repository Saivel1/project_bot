from db.db_model import DatabaseManager
from config_data.config import load_config_db


db_config = load_config_db('.env')
db_manager = DatabaseManager(db_config)