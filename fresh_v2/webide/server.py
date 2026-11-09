import os, sys, glob, tempfile, subprocess, resource
from flask import Flask, request, jsonify, send_from_directory

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
BB = os.path.join(ROOT, "bb.py")
CLI = os.path.join(ROOT, "bhasha")
TIMEOUT = 5
MAX_CODE = 20000
MAX_OUT = 20000

app = Flask(__name__)

def limits():
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, TIMEOUT))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))
    except Exception:
        pass

def execute(cmd_prefix, code):
    if len(code) > MAX_CODE:
        return {"ok": False, "output": "কোড অনেক বড় (সর্বোচ্চ %d অক্ষর)" % MAX_CODE}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "main.bb")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            p = subprocess.run(
                [sys.executable, *cmd_prefix, path],
                capture_output=True, text=True, timeout=TIMEOUT,
                cwd=d, preexec_fn=limits)
        except subprocess.TimeoutExpired:
            return {"ok": False, "output": "সময় শেষ (%d সেকেন্ডের বেশি লেগেছে)" % TIMEOUT}
        out = (p.stdout or "") + (p.stderr or "")
        if not out and p.returncode != 0:
            out = "প্রোগ্রাম ত্রুটি নিয়ে বন্ধ হয়েছে (exit %d)" % p.returncode
        if p.returncode != 0 and "Traceback" in out:
            out = out.strip().splitlines()[-1] + "\n"
        if len(out) > MAX_OUT:
            out = out[:MAX_OUT] + "\n...(আউটপুট কাটা হয়েছে)"
        return {"ok": p.returncode == 0, "output": out}

@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")

@app.post("/api/run")
def run():
    code = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(execute([BB], code))

@app.post("/api/check")
def check():
    code = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(execute([CLI, "check"], code))

@app.get("/api/examples")
def examples():
    items = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "examples", "*.bb"))):
        with open(p, encoding="utf-8") as f:
            items[os.path.basename(p)] = f.read()
    return jsonify(items)

@app.get("/api/version")
def version():
    return jsonify({"name": "BANGLADESH BHASHA", "version": "2.0"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8800)
