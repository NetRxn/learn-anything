"""Application entry point. The learning engine is outside this checkpoint."""
from app.config import Settings
from app.foundation import create_app

app = create_app(Settings())
