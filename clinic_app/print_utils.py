from __future__ import annotations

import os
import subprocess
from pathlib import Path


def has_connected_printer() -> bool:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Printer | Where-Object {$_.Type -ne 'Fax'} | Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return len(names) > 0
    except Exception:
        return False


def print_pdf(file_path: str | Path) -> None:
    os.startfile(str(file_path), "print")  # type: ignore[attr-defined]
