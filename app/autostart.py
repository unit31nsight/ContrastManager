import sys
from pathlib import Path

APP_NAME = "ContrastManager"


def is_enabled() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\\Microsoft\\Windows\\CurrentVersion\\Run") as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except (OSError, ImportError):
        return False


def set_enabled(enabled: bool) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Автозапуск доступен только в Windows."
    try:
        import winreg
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
            if enabled:
                # For a packaged EXE this is the EXE path. In source mode use python + run.py.
                exe = Path(sys.executable).resolve()
                if getattr(sys, "frozen", False):
                    command = f'"{exe}"'
                else:
                    script = Path(sys.argv[0]).resolve()
                    command = f'"{exe}" "{script}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True, "Автозапуск обновлён."
    except OSError as exc:
        return False, f"Не удалось изменить автозапуск: {exc}"
