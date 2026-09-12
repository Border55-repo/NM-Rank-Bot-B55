from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from urllib.parse import urlsplit, urlunsplit

from selenium.common.exceptions import JavascriptException, WebDriverException

from .selectors import SelectorRegistry
from .state import StateStore
from .cooldown import parse_cooldown


@dataclass
class Observation:
    url: str
    title: str
    body: str
    cooldown_text: str
    money: str
    rank: str


class PageObserver:
    def __init__(self, driver, state: StateStore, selectors: SelectorRegistry, observation_path: Path | None = None) -> None:
        self.driver = driver
        self.state = state
        self.selectors = selectors
        self.observation_path = observation_path
        self._last_signature = None

    def _record_safe_observation(self, observation: Observation, **signals) -> None:
        if not self.observation_path:
            return
        parts = urlsplit(observation.url)
        safe_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        event = {
            "timestamp": int(time()), "url": safe_url,
            "title": observation.title[:160],
            "cooldown_text": observation.cooldown_text[:160],
            "money": observation.money[:100], "rank": observation.rank[:100],
            **signals,
        }
        signature = json.dumps(event | {"timestamp": 0}, sort_keys=True, ensure_ascii=False)
        if signature == self._last_signature:
            return
        self._last_signature = signature
        self.observation_path.parent.mkdir(parents=True, exist_ok=True)
        with self.observation_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _first_text(self, key: str) -> str:
        for css in self.selectors.candidates(key):
            try:
                elements = self.driver.find_elements("css selector", css)
                for element in elements:
                    value = (element.text or element.get_attribute("textContent") or "").strip()
                    if value:
                        self.selectors.record_hit(key, css)
                        return value[:250]
            except WebDriverException:
                continue
        return ""

    def read(self) -> Observation:
        body = self.driver.execute_script("return document.body ? document.body.innerText : ''") or ""
        observation = Observation(
            url=self.driver.current_url,
            title=self.driver.title,
            body=body[:100_000],
            cooldown_text=self._first_text("cooldown"),
            money=self._first_text("money") or "Ukjent",
            rank=self._first_text("rank") or "Ukjent",
        )
        lowered = observation.body.lower()
        captcha = any(word in lowered for word in ("captcha", "jeg er ikke en robot", "recaptcha"))
        in_jail = any(word in lowered for word in ("du sitter i fengsel", "fengselstid", "bryt ut"))
        logged_in = not any(word in lowered for word in ("logg inn", "brukernavn")) or "logg ut" in lowered
        cooldown = parse_cooldown(observation.cooldown_text or lowered[:4000])
        self.state.update(
            url=observation.url, title=observation.title, captcha=captcha,
            in_jail=in_jail, logged_in=logged_in, money=observation.money,
            rank=observation.rank, cooldown_text=observation.cooldown_text or "Ingen synlig cooldown",
            cooldown_seconds=cooldown, learned_selectors=self.selectors.learned_count(),
        )
        self._record_safe_observation(
            observation, captcha=captcha, in_jail=in_jail,
            logged_in=logged_in, cooldown_seconds=cooldown,
        )
        return observation
