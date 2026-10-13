import os
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings
    SettingsConfigDict = None

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # LLM API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_temperature: float = 0.3
    
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    anthropic_temperature: float = 0.3
    
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "AIzaSyDXMLyi7xHYvEeCvED9bs_cdblWIjIxFnE")
    google_model: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro-latest")
    google_temperature: float = 0.3
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/deepclaw.db")
    database_echo: bool = False
    
    # Search Engine Configuration
    brave_search_api_key: str = os.getenv("BRAVE_SEARCH_API_KEY", "BSAfZjZHZ6VDXzam7NnEA-MWaMhz8JL")
    duckduckgo_user_agent: str = os.getenv("DUCKDUCKGO_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Server & CORS
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: List[str] = ["*"]
    
    # WebSocket Configuration
    websocket_ping_interval: int = 30
    websocket_max_connections: int = 1000
    
    # PDF Output Configuration
    playwright_executable_path: str = os.getenv("PLAYWRIGHT_EXECUTABLE_PATH", "")
    pdf_output_dir: str = os.getenv("PDF_OUTPUT_DIR", str(BASE_DIR / "reports"))
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "deepclaw.log"))

    # Research Configuration
    max_depth: int = int(os.getenv("MAX_DEPTH", "3"))
    max_sources_per_query: int = int(os.getenv("MAX_SOURCES_PER_QUERY", "10"))
    min_relevance_score: float = float(os.getenv("MIN_RELEVANCE_SCORE", "0.5"))

    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=str(BASE_DIR / ".env"),
            env_prefix="DEEPCLAW_",
            extra="ignore"
        )
    else:
        class Config:
            env_file = str(BASE_DIR / ".env")
            env_prefix = "DEEPCLAW_"
            extra = "ignore"

# Global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
os.makedirs(settings.pdf_output_dir, exist_ok=True)
