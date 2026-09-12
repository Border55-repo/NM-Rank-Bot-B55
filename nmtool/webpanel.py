from __future__ import annotations

import socket
import secrets
import threading

from flask import Flask, jsonify, render_template_string, request
from waitress import serve


PAGE = """<!doctype html><html lang=\"no\"><head><meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"theme-color\" content=\"#07111d\"><link rel=\"manifest\" href=\"/manifest.webmanifest\">
<title>NM-verktøy B55</title><style>
:root{color-scheme:dark;--bg:#07111d;--card:#102238;--line:#244562;--cyan:#53d8fb;--red:#ff5577;--muted:#9fb2c7}
*{box-sizing:border-box}body{margin:0;font:16px system-ui;background:linear-gradient(145deg,#07111d,#112941);color:#fff;min-height:100vh}
main{max-width:760px;margin:auto;padding:18px}.top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.badge{padding:7px 12px;border-radius:999px;background:#243f59;color:var(--muted)}.on{background:#0d614f;color:#8effd7}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:18px 0}.card{background:rgba(16,34,56,.94);border:1px solid var(--line);border-radius:18px;padding:16px}
.value{font-size:1.25rem;font-weight:750;margin-top:6px;word-break:break-word}.muted{color:var(--muted);font-size:.85rem}
button{width:100%;padding:17px;border:0;border-radius:15px;background:var(--cyan);color:#052031;font-weight:800;font-size:1rem;margin:6px 0}
button.stop{background:var(--red);color:white}#log{max-height:260px;overflow:auto;white-space:pre-wrap;font-size:.85rem}
@media(max-width:560px){main{padding:12px}.grid{grid-template-columns:1fr}.top h1{font-size:1.35rem}.card{border-radius:14px}}
</style></head><body><main><div class=\"top\"><h1>NM-verktøy B55 v0.4.2</h1><span id=\"status\" class=\"badge\">Kobler til</span></div>
<div class=\"grid\"><div class=\"card\"><div class=\"muted\">Cooldown</div><div id=\"cooldown\" class=\"value\">–</div></div>
<div class=\"card\"><div class=\"muted\">Siste resultat</div><div id=\"result\" class=\"value\">–</div></div>
<div class=\"card\"><div class=\"muted\">Penger</div><div id=\"money\" class=\"value\">–</div></div>
<div class=\"card\"><div class=\"muted\">Rank</div><div id=\"rank\" class=\"value\">–</div></div></div>
<div id=\"activities\" class=\"card\"></div><button id=\"work\" onclick=\"work()\">Aktiver Work Mode</button><button onclick=\"diagnostics()\">Eksporter diagnostikk</button><button class=\"stop\" onclick=\"stopTool()\">Stopp verktøyet</button>
<div class=\"card\"><div class=\"muted\">Live-logg</div><div id=\"log\"></div></div></main>
<script>let state={};const token=new URLSearchParams(location.search).get('token')||'';const api=p=>p+(p.includes('?')?'&':'?')+'token='+encodeURIComponent(token);
async function refresh(){try{state=await(await fetch(api('/api/state'))).json();
status.textContent=state.running?(state.work_mode?'Work Mode aktiv':'Klar'):'Stoppet';status.className='badge '+(state.work_mode?'on':'');
cooldown.textContent=state.cooldown_text+(state.cooldown_seconds!=null?' ('+state.cooldown_seconds+' s)':'');result.textContent=state.last_result;
money.textContent=state.money;rank.textContent=state.rank;work.textContent=state.work_mode?'Pause Work Mode':'Aktiver Work Mode';
log.textContent=state.messages.slice().reverse().join('\\n');activities.innerHTML='<div class="muted">Aktiviteter</div>'+Object.entries(state.activities||{}).map(([k,v])=>'<label style="display:block;padding:8px 0"><input type="checkbox" '+(v?'checked':'')+' onchange="activity(\\''+k+'\\',this.checked)"> '+k.replaceAll('_',' ')+'</label>').join('');}catch(e){status.textContent='Ingen kontakt'}}
async function work(){await fetch(api('/api/work'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!state.work_mode})});refresh()}
async function activity(name,enabled){await fetch(api('/api/activity'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,enabled})});refresh()}
async function diagnostics(){await fetch(api('/api/diagnostics'),{method:'POST'});refresh()}
async function stopTool(){await fetch(api('/api/stop'),{method:'POST'});refresh()}if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js');setInterval(refresh,1500);refresh();</script></body></html>"""


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def start_web_panel(state, worker, port: int, log) -> str:
    app = Flask(__name__)
    token = secrets.token_urlsafe(18)

    @app.before_request
    def protect_api():
        if request.path.startswith("/api/") and request.args.get("token") != token:
            return jsonify({"error": "ugyldig tilgang"}), 403

    @app.get("/")
    def index():
        return render_template_string(PAGE)

    @app.get("/api/state")
    def get_state():
        result = state.snapshot()
        result["activities"] = worker.activity_state()
        return jsonify(result)

    @app.post("/api/work")
    def set_work():
        worker.set_work_mode(bool((request.get_json(silent=True) or {}).get("enabled")))
        return jsonify(state.snapshot())

    @app.post("/api/activity")
    def set_activity():
        values = request.get_json(silent=True) or {}
        if not worker.set_activity(str(values.get("name", "")), bool(values.get("enabled"))):
            return jsonify({"error": "ukjent aktivitet"}), 400
        return jsonify({"ok": True})

    @app.post("/api/diagnostics")
    def diagnostics():
        path = worker.export_diagnostics()
        return jsonify({"ok": True, "file": path.name})

    @app.post("/api/stop")
    def stop():
        worker.stop()
        return jsonify({"ok": True})

    @app.get("/manifest.webmanifest")
    def manifest():
        return jsonify({"name": "NM-verktøy B55", "short_name": "NM B55", "start_url": f"/?token={token}", "display": "standalone", "background_color": "#07111d", "theme_color": "#07111d"})

    @app.get("/sw.js")
    def service_worker():
        return "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',()=>{});", 200, {"Content-Type": "application/javascript"}

    thread = threading.Thread(target=lambda: serve(app, host="0.0.0.0", port=port, threads=4), daemon=True)
    thread.start()
    url = f"http://{local_ip()}:{port}/?token={token}"
    log(f"Mobilpanel: {url}")
    return url
