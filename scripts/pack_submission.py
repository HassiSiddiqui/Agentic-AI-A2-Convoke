"""Build the Classroom ZIP. Secrets and the class workbook stay out."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "A2_23i-2654_AbdulHaseebSiddiqui_Convoke.zip"

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
SKIP_FILES = {
    ".env",
    "Agentic_AI_assignment-2_Ideas.xlsx",
}
SKIP_SUFFIX = {".pyc", ".zip"}


def keep(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        return False
    if path.name in SKIP_FILES:
        return False
    if path.name.startswith(".") and path.name not in {".env.example", ".gitignore"}:
        return False
    if path.suffix.lower() in SKIP_SUFFIX:
        return False
    return True


def main() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    files = [p for p in ROOT.rglob("*") if p.is_file() and keep(p)]
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path.relative_to(ROOT).as_posix())
    print(f"Wrote {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()
