from __future__ import annotations

from typing import Any, Dict

from dataclasses import dataclass

@dataclass
class WorkerResponse:
    summary: str
    artifacts: Dict[str, Any]
