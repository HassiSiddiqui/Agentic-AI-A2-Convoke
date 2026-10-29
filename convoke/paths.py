from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STORE = DATA / "store"
SAMPLES = DATA / "samples"
UPLOADS = DATA / "uploads"
LOGS = ROOT / "logs"
OUTPUTS = ROOT / "outputs"
NOTICES = OUTPUTS / "notices"
REPORTS = ROOT / "reports"


def ensure_dirs() -> None:
    for path in (STORE, SAMPLES, UPLOADS, LOGS, OUTPUTS, NOTICES, REPORTS):
        path.mkdir(parents=True, exist_ok=True)
