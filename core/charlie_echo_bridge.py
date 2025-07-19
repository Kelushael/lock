"""CharlieEchoBridge - Pulse and cross-module communication bus."""

import time
from typing import Any, Dict


class CharlieEchoBridge:
    """Stores module pulses and allows querying the latest data."""

    def __init__(self):
        self._state: Dict[str, Dict[str, Any]] = {}

    def pulse(self, module_name: str, status: str, data: Dict[str, Any] | None = None) -> None:
        self._state[module_name] = {
            "status": status,
            "data": data or {},
            "timestamp": time.time(),
        }

    def query(self, module_name: str) -> Dict[str, Any] | None:
        return self._state.get(module_name)
