# BANGLADESH BHASHA — Universal Installer

Supported platforms:
- Android Termux
- Linux
- macOS
- Windows PowerShell / Windows Terminal

Requirement: Python 3.10 or newer.

## Termux / Linux / macOS

From the project directory:

```bash
chmod +x install.sh uninstall.sh
./install.sh
```

After installation:

```bash
bhasha version
bhasha help
bhasha run app.bb
bhasha check app.bb
bhasha repl
```

On Linux/macOS, if the command is not found, add `~/.local/bin` to PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

For persistence, add that line to your shell profile.

## Windows

Open PowerShell in the project directory:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Open a new terminal after installation:

```powershell
bhasha version
bhasha help
bhasha run app.bb
bhasha check app.bb
bhasha repl
```

## Uninstall

Termux / Linux / macOS:

```bash
./uninstall.sh
```

Windows:

```powershell
.\uninstall.ps1
```

The uninstaller removes installer-managed files only. It does not delete your separate `.bb` programs or project folders.

## Installation design

- Uses a dedicated Python virtual environment.
- Does not require Git for archive-based installation.
- Does not require administrator/root privileges.
- Keeps a backup of an existing `bhasha` launcher before replacing it.
- Uses the GitHub `main` branch archive when run outside the source project.
- Proprietary project license remains unchanged.
