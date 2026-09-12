from __future__ import annotations

import json
import queue
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from nmtool import __version__
from nmtool.browser import BrowserWorker
from nmtool.state import StateStore
from nmtool.webpanel import start_web_panel


ROOT = Path(__file__).resolve().parent


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"NM-verktøy B55 v{__version__}")
        self.root.geometry("820x620")
        self.root.minsize(680, 520)
        self.state = StateStore()
        self.logs: queue.Queue[str] = queue.Queue()
        self.worker = BrowserWorker(ROOT, self.state, self.write_log)
        self.mobile_url = ""
        self._build()
        self._start_mobile()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

    def _build(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Work.TButton", font=("Segoe UI", 12, "bold"), padding=12)
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=f"NM-verktøy B55 v{__version__}", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(container, text="Kontinuerlig sideavlesning, cooldown og mobil kontroll").pack(anchor="w", pady=(0, 14))
        stats = ttk.Frame(container)
        stats.pack(fill="x")
        self.labels = {}
        for index, key in enumerate(("status", "cooldown", "money", "rank", "actions", "errors")):
            box = ttk.LabelFrame(stats, text=key.capitalize(), padding=9)
            box.grid(row=index // 3, column=index % 3, sticky="nsew", padx=4, pady=4)
            self.labels[key] = ttk.Label(box, text="–", font=("Segoe UI", 11, "bold"))
            self.labels[key].pack(anchor="w")
        for col in range(3):
            stats.columnconfigure(col, weight=1)
        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=12)
        ttk.Button(controls, text="Start nettleser", command=self.worker.start).pack(side="left", expand=True, fill="x", padx=4)
        self.work_button = ttk.Button(controls, text="Aktiver Work Mode", style="Work.TButton", command=self.toggle_work)
        self.work_button.pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(controls, text="Åpne mobilpanel", command=self.open_mobile).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(container, text="Eksporter diagnostikk", command=self.worker.export_diagnostics).pack(fill="x", padx=4, pady=(0, 10))
        self.log_widget = tk.Text(container, height=18, wrap="word", state="disabled", bg="#081521", fg="#d7e7f5", insertbackground="white")
        self.log_widget.pack(fill="both", expand=True)
        self.write_log("Klar. Trykk Start nettleser, logg inn og aktiver deretter Work Mode.")

    def _start_mobile(self) -> None:
        config_path = ROOT / ("config.json" if (ROOT / "config.json").exists() else "config.example.json")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("mobile_panel", True):
            self.mobile_url = start_web_panel(self.state, self.worker, int(config.get("mobile_panel_port", 8765)), self.write_log)

    def write_log(self, message: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {message}"
        self.logs.put(line)
        self.state.message(line)

    def toggle_work(self) -> None:
        snap = self.state.snapshot()
        if not snap["running"]:
            self.write_log("Start nettleseren før Work Mode aktiveres.")
            return
        self.worker.set_work_mode(not snap["work_mode"])

    def open_mobile(self) -> None:
        if self.mobile_url:
            webbrowser.open(self.mobile_url)

    def refresh(self) -> None:
        snap = self.state.snapshot()
        status = "Work Mode" if snap["work_mode"] else ("Klar" if snap["running"] else "Stoppet")
        if snap["captcha"]:
            status = "CAPTCHA – trenger deg"
        self.labels["status"].configure(text=status)
        self.labels["cooldown"].configure(text=snap["cooldown_text"])
        self.labels["money"].configure(text=snap["money"])
        self.labels["rank"].configure(text=snap["rank"])
        self.labels["actions"].configure(text=str(snap["actions"]))
        self.labels["errors"].configure(text=str(snap["errors"]))
        self.work_button.configure(text="Pause Work Mode" if snap["work_mode"] else "Aktiver Work Mode")
        while True:
            try:
                line = self.logs.get_nowait()
            except queue.Empty:
                break
            self.log_widget.configure(state="normal")
            self.log_widget.insert("end", line + "\n")
            self.log_widget.see("end")
            self.log_widget.configure(state="disabled")
        self.root.after(750, self.refresh)

    def close(self) -> None:
        self.worker.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
