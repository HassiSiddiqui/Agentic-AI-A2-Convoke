import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password: str = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from: str = os.getenv("SMTP_FROM", "").strip()
    smtp_allowlist: str = os.getenv("SMTP_ALLOWLIST", "").strip()

    @property
    def allowlist(self) -> set[str]:
        if not self.smtp_allowlist:
            return set()
        return {item.strip().lower() for item in self.smtp_allowlist.split(",") if item.strip()}


def settings_from_overrides(**kwargs) -> Settings:
    base = Settings()
    for key, value in kwargs.items():
        if value is None or value == "":
            continue
        setattr(base, key, value)
    return base
