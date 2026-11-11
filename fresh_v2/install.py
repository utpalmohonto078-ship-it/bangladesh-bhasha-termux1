#!/usr/bin/env python3
import os
import platform
import sys
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = "https://codeload.github.com/utpalmohonto078-ship-it/bangladesh-bhasha/zip/refs/heads/main"
APP = "bangladesh-bhasha"

def stop(message):
    raise SystemExit("\nERROR: " + message)

def run(args):
    print("+", " ".join(map(str, args)))
    subprocess.run(args, check=True)

if sys.version_info < (3, 10):
    stop("Python 3.10 বা নতুন সংস্করণ প্রয়োজন।")

home = Path.home()
windows = os.name == "nt"
termux = bool(os.environ.get("PREFIX")) and "com.termux" in os.environ.get("PREFIX", "")

if windows:
    data = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "BangladeshBhasha"
    bindir = data / "bin"
    venv = data / "venv"
    launcher = bindir / "bhasha.cmd"
    python_venv = venv / "Scripts/python.exe"
    command = venv / "Scripts/bhasha.exe"
elif termux:
    data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / APP
    bindir = Path(os.environ["PREFIX"]) / "bin"
    venv = data / "venv"
    launcher = bindir / "bhasha"
    python_venv = venv / "bin/python"
    command = venv / "bin/bhasha"
else:
    data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / APP
    bindir = home / ".local/bin"
    venv = data / "venv"
    launcher = bindir / "bhasha"
    python_venv = venv / "bin/python"
    command = venv / "bin/bhasha"

source = data / "source"
backup = data / "previous-bhasha-launcher"

# নিরাপদ path পরীক্ষা
for path in (data, bindir, source, venv, launcher):
    if path.is_symlink():
        stop(f"Symlink path গ্রহণ করা হয়নি: {path}")

for path in (data, bindir, source, venv):
    if path.exists() and not path.is_dir():
        stop(f"Directory নয়: {path}")

if launcher.exists() and not launcher.is_file():
    stop(f"Launcher regular file নয়: {launcher}")

data.mkdir(parents=True, exist_ok=True)
bindir.mkdir(parents=True, exist_ok=True)

# বর্তমান project directory থাকলে local source; নইলে GitHub archive
here = Path(__file__).resolve().parent
local = (here / "pyproject.toml").is_file() and (here / "bhasha_cli.py").is_file()
temp = Path(tempfile.mkdtemp(prefix="bhasha-install-"))

try:
    if local:
        print("Local project source ব্যবহার করা হচ্ছে।")
        extracted = temp / "project"
        shutil.copytree(
            here, extracted,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "venv", "__pycache__", "*.pyc",
                "build", "dist", "*.egg-info", "bb-release-backups"
            )
        )
    else:
        print("GitHub থেকে source download হচ্ছে...")
        archive = temp / "source.zip"
        request = urllib.request.Request(
            REPO, headers={"User-Agent": "Bangladesh-Bhasha-Installer"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            archive.write_bytes(response.read())

        with zipfile.ZipFile(archive) as zf:
            root = temp.resolve()
            for member in zf.infolist():
                target = (temp / member.filename).resolve()
                if os.path.commonpath((str(root), str(target))) != str(root):
                    stop("Archive-এ অনিরাপদ path পাওয়া গেছে।")
            zf.extractall(temp)

        candidates = [
            p for p in temp.iterdir()
            if p.is_dir() and (p / "pyproject.toml").is_file()
        ]
        if len(candidates) != 1:
            stop("GitHub archive থেকে project root শনাক্ত করা যায়নি।")
        extracted = candidates[0]

    if not (extracted / "bhasha_cli.py").is_file():
        stop("bhasha_cli.py পাওয়া যায়নি।")
    if not (extracted / "pyproject.toml").is_file():
        stop("pyproject.toml পাওয়া যায়নি।")

    staged = data / "source-new"
    old = data / "source-old"

    for path in (staged, old):
        if path.is_symlink():
            stop(f"Unsafe staging path: {path}")
        if path.exists():
            shutil.rmtree(path)

    shutil.copytree(extracted, staged)

    if source.exists():
        source.rename(old)
    staged.rename(source)
    if old.exists():
        shutil.rmtree(old)

finally:
    shutil.rmtree(temp, ignore_errors=True)

# Virtual environment তৈরি
if not venv.exists():
    run([sys.executable, "-m", "venv", str(venv)])

if not python_venv.is_file():
    stop("Virtual environment Python পাওয়া যায়নি।")

run([str(python_venv), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"])
run([
    str(python_venv), "-m", "pip", "install",
    "--no-deps", "--no-build-isolation", "--upgrade", str(source)
])

if not command.exists():
    stop("bhasha command তৈরি হয়নি।")

# আগের launcher ব্যাকআপ রাখা
if launcher.exists():
    try:
        old_text = launcher.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        old_text = ""
    if str(venv) not in old_text and not backup.exists():
        shutil.copy2(launcher, backup)

# নতুন launcher
if windows:
    launcher.write_text(
        '@echo off\r\n'
        f'"{command}" %*\r\n'
        'exit /b %ERRORLEVEL%\r\n',
        encoding="utf-8"
    )
else:
    launcher.write_text(
        "#!/bin/sh\n"
        f'exec "{command}" "$@"\n',
        encoding="utf-8"
    )
    launcher.chmod(0o755)

# Uninstaller সংরক্ষণ
uninstaller = source / "uninstall.py"
if uninstaller.is_file():
    shutil.copy2(uninstaller, data / "uninstall.py")
shutil.copy2(Path(__file__).resolve(), data / "install.py")

# Windows PATH-এ dedicated bin যোগ
if windows:
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE
    )
    try:
        try:
            old_path, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            old_path, kind = "", winreg.REG_EXPAND_SZ
        parts = [p for p in old_path.split(";") if p]
        if str(bindir) not in parts:
            parts.append(str(bindir))
            winreg.SetValueEx(key, "Path", 0, kind, ";".join(parts))
    finally:
        winreg.CloseKey(key)
    print("Windows User PATH আপডেট হয়েছে। নতুন Terminal খুলুন।")
else:
    if str(bindir) not in os.environ.get("PATH", "").split(os.pathsep):
        print("\nPATH-এ যোগ করুন:")
        print(f'export PATH="{bindir}:$PATH"')

print("\n======================================")
print("BANGLADESH BHASHA INSTALLATION SUCCESS")
print("======================================")
print("Platform:", platform.system(), "Termux" if termux else "")
print("Command:", launcher)
print("Data:", data)
print("\nপরীক্ষা:")
print("bhasha version")
print("bhasha help")
