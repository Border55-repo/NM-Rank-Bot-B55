from __future__ import annotations

import json
import threading
import zipfile
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

from .observer import PageObserver
from .selectors import SelectorRegistry
from .state import StateStore


ACTIVITY_LABELS = {
    "fight_club": ("fight club", "trening", "tren"),
    "crime": ("kriminalitet", "crime"),
    "car_theft": ("biltyveri", "stjel bil", "car theft"),
    "extortion": ("utpressing", "extortion"),
}


class BrowserWorker:
    def __init__(self, root: Path, state: StateStore, log) -> None:
        self.root = root
        self.state = state
        self.log = log
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.driver = None
        self.registry = SelectorRegistry(root / "data" / "selectors.json")
        self.config = self._load_config()
        self.enabled_activities = dict(self.config.get("enabled_activities", {}))

    def _load_config(self) -> dict:
        path = self.root / "config.json"
        source = path if path.exists() else self.root / "config.example.json"
        return json.loads(source.read_text(encoding="utf-8"))

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="nm-browser", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.state.update(running=False, work_mode=False)

    def set_work_mode(self, enabled: bool) -> None:
        self.state.update(work_mode=enabled)
        self.log("Work Mode aktivert" if enabled else "Work Mode pauset")

    def set_activity(self, name: str, enabled: bool) -> bool:
        if name not in ACTIVITY_LABELS:
            return False
        self.enabled_activities[name] = enabled
        self.log(f"{name.replace('_', ' ').title()}: {'på' if enabled else 'av'}")
        return True

    def activity_state(self) -> dict[str, bool]:
        return dict(self.enabled_activities)

    def export_diagnostics(self) -> Path:
        target_dir = self.root / "diagnostics"
        target_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        json_path = target_dir / f"status-{stamp}.json"
        safe_state = self.state.snapshot()
        json_path.write_text(json.dumps({
            "version": "0.4.2",
            "state": safe_state,
            "activities": self.activity_state(),
            "selectors": self.registry.data,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        zip_path = target_dir / f"NM-diagnostikk-{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(json_path, json_path.name)
            for source in (self.root / "data" / "selectors.json", self.root / "data" / "observations.jsonl"):
                if source.exists():
                    archive.write(source, source.name)
        self.log(f"Diagnostikk lagret: {zip_path.name}")
        return zip_path

    def _open_driver(self):
        options = Options()
        profile = self.root / "chrome-profile"
        options.add_argument(f"--user-data-dir={profile}")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.config.get("base_url", "https://nordicmafia.org/"))

    def _run(self) -> None:
        self.state.update(running=True)
        try:
            self._open_driver()
            observer = PageObserver(
                self.driver, self.state, self.registry,
                self.root / "data" / "observations.jsonl",
            )
            self.log("Nettleseren er klar. Logg inn manuelt dersom det trengs.")
            while not self.stop_event.is_set():
                observation = observer.read()
                snap = self.state.snapshot()
                if snap["captcha"]:
                    self.state.update(work_mode=False)
                    self.log("CAPTCHA oppdaget. Work Mode er pauset til du løser den manuelt.")
                self.stop_event.wait(float(self.config.get("observer_interval_seconds", 2)))
        except WebDriverException as exc:
            self.state.increment("errors")
            self.log(f"Nettleserfeil: {exc.msg[:180] if getattr(exc, 'msg', None) else exc}")
        except Exception as exc:
            self.state.increment("errors")
            self.log(f"Feil: {exc}")
        finally:
            self.state.update(running=False, work_mode=False)

    def close(self) -> None:
        self.stop()
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
