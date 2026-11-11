#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

APP = "bangladesh-bhasha"
home = Path.home()
windows = os.name == "nt"
termux = bool(os.environ.get("PREFIX")) and "com.termux" in os.environ.get("PREFIX", "")

if windows:
    data = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "BangladeshBhasha"
    bindir = data / "bin"
    launcher = bindir / "bhasha.cmd"
else:
    data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / APP
    bindir = Path(os.environ["PREFIX"]) / "bin" if termux else home / ".local/bin"
    launcher = bindir / "bhasha"

backup = data / "previous-bhasha-launcher"
venv = data / "venv"

if data.is_symlink() or launcher.is_symlink():
    raise SystemExit("নিরাপত্তার কারণে symlink path-এ কাজ বন্ধ করা হয়েছে।")

if not data.exists():
    print("BANGLADESH BHASHA installer data পাওয়া যায়নি।")
    raise SystemExit(0)

answer = input("BANGLADESH BHASHA সরাতে চান? yes লিখুন: ").strip()
if answer != "yes":
    print("বাতিল করা হয়েছে।")
    raise SystemExit(0)

owned = False
if launcher.is_file():
    try:
        content = launcher.read_text(encoding="utf-8", errors="ignore")
        owned = str(venv) in content
    except OSError:
        pass

if owned:
    if backup.is_file():
        shutil.copy2(backup, launcher)
        print("আগের launcher পুনরুদ্ধার করা হয়েছে।")
    else:
        launcher.unlink()
        print("Installer launcher সরানো হয়েছে।")
else:
    print("Launcher installer-এর তৈরি নয়; অপরিবর্তিত রাখা হয়েছে।")

if windows:
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE
        )
        try:
            path, kind = winreg.QueryValueEx(key, "Path")
            parts = [p for p in path.split(";") if p != str(bindir)]
            winreg.SetValueEx(key, "Path", 0, kind, ";".join(parts))
        finally:
            winreg.CloseKey(key)
    except FileNotFoundError:
        pass

shutil.rmtree(data)
print("BANGLADESH BHASHA installer data সরানো হয়েছে।")
print("ব্যবহারকারীর .bb প্রোগ্রাম ও আলাদা project folder মুছে ফেলা হয়নি।")
