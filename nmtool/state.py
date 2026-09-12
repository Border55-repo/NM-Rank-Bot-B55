from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import RLock
from time import time


@dataclass
class RuntimeState:
    running: bool = False
    work_mode: bool = False
    learning_mode: bool = True
    captcha: bool = False
    logged_in: bool = False
    in_jail: bool = False
    url: str = ""
    title: str = ""
    money: str = "Ukjent"
    rank: str = "Ukjent"
    cooldown_text: str = "Ingen lest"
    cooldown_seconds: int | None = None
    last_result: str = "Ikke startet"
    observed_at: float = 0.0
    actions: int = 0
    errors: int = 0
    learned_selectors: int = 0
    messages: list[str] = field(default_factory=list)


class StateStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._state = RuntimeState()

    def update(self, **values) -> None:
        with self._lock:
            for key, value in values.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
            self._state.observed_at = time()

    def increment(self, field_name: str) -> None:
        with self._lock:
            setattr(self._state, field_name, getattr(self._state, field_name) + 1)

    def message(self, value: str) -> None:
        with self._lock:
            self._state.messages = (self._state.messages + [value])[-80:]
            self._state.last_result = value

    def snapshot(self) -> dict:
        with self._lock:
            return asdict(self._state)

