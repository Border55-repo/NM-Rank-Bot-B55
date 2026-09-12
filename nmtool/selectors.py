from __future__ import annotations

import json
from pathlib import Path
from threading import RLock


DEFAULT_SELECTORS = {
    "cooldown": [
        "#cooldown", "[id*='cooldown']", "[class*='cooldown']",
        "[data-cooldown]", "time"
    ],
    "money": ["#money", "[id*='money']", "[class*='money']"],
    "rank": ["#rank", "[id*='rank']", "[class*='rank']"],
    "jail": ["[id*='jail']", "[class*='jail']", "[class*='fengsel']"],
    "fight_club": [
        "#rowid_table_select_fcworkout3", "[name*='workout']",
        "button[data-action*='fight']", "input[value*='Tren']"
    ],
    "crime": ["button[data-action*='crime']", "input[value*='Kriminalitet']"],
    "car_theft": ["button[data-action*='car']", "input[value*='Biltyveri']"],
    "extortion": ["button[data-action*='extort']", "input[value*='Utpressing']"],
}


class SelectorRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        self.data = {key: [{"css": css, "hits": 0} for css in values]
                     for key, values in DEFAULT_SELECTORS.items()}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                for key, values in saved.items():
                    if isinstance(values, list):
                        self.data[key] = values
        except (OSError, ValueError):
            pass

    def candidates(self, key: str) -> list[str]:
        with self._lock:
            values = sorted(self.data.get(key, []), key=lambda item: item.get("hits", 0), reverse=True)
            return [item["css"] for item in values if item.get("css")]

    def record_hit(self, key: str, css: str) -> None:
        with self._lock:
            values = self.data.setdefault(key, [])
            for item in values:
                if item.get("css") == css:
                    item["hits"] = int(item.get("hits", 0)) + 1
                    break
            else:
                values.append({"css": css, "hits": 1})
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def learned_count(self) -> int:
        return sum(1 for values in self.data.values() for item in values if item.get("hits", 0) > 0)

