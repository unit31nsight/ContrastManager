from dataclasses import dataclass
from monitorcontrol import get_monitors


@dataclass
class MonitorStatus:
    supported: int
    detected: int
    message: str


class MonitorController:
    """DDC/CI access. Hardware calls happen only when the user requests them."""

    def __init__(self):
        self.original_contrasts = None

    def remember_original_contrast(self):
        """Запоминает исходную контрастность мониторов."""
        self.original_contrasts = []

        try:
            monitors = self._monitors()
        except Exception:
            return

        for index, monitor in enumerate(monitors):
            try:
                with monitor:
                    value = monitor.get_contrast()

                if isinstance(value, (int, float)):
                    self.original_contrasts.append((index, value))
            except Exception:
                continue

    def restore_original_contrast(self):
        """Восстанавливает исходные значения при выходе."""
        if self.original_contrasts is None:
            return

        try:
            monitors = self._monitors()
        except Exception:
            return

        for index, value in self.original_contrasts:
            if index >= len(monitors):
                continue

            try:
                with monitors[index]:
                    monitors[index].set_contrast(value)
            except Exception:
                continue

    @staticmethod
    def _monitors():
        return list(get_monitors())

    def check_support(self) -> MonitorStatus:
        try:
            monitors = self._monitors()
        except Exception as exc:
            return MonitorStatus(0, 0, f"Не удалось обнаружить мониторы: {exc}")

        supported = 0
        for monitor in monitors:
            try:
                with monitor:
                    value = monitor.get_contrast()
                    if isinstance(value, (int, float)):
                        supported += 1
            except Exception:
                continue

        if not monitors:
            message = "Мониторы через DDC/CI не обнаружены."
        elif supported:
            message = f"Контрастность доступна: {supported} из {len(monitors)} мониторов."
        else:
            message = ("Физическая контрастность не подтверждена. Проверьте DDC/CI "
                       "в меню монитора и подключение без несовместимого переходника.")
        return MonitorStatus(supported, len(monitors), message)

    def set_contrast(self, value: int) -> tuple[bool, str]:
        try:
            monitors = self._monitors()
        except Exception as exc:
            return False, f"Не удалось обнаружить мониторы: {exc}"

        if not monitors:
            return False, "Мониторы через DDC/CI не обнаружены."

        changed = 0
        errors = []
        for index, monitor in enumerate(monitors, start=1):
            try:
                with monitor:
                    # Reading first verifies that the contrast VCP feature responds.
                    monitor.get_contrast()
                    monitor.set_contrast(int(value))
                    changed += 1
            except Exception as exc:
                errors.append(f"Монитор {index}: {exc}")

        if changed and not errors:
            return True, f"Контрастность установлена на {value}%."
        if changed:
            return True, f"Изменено мониторов: {changed}. Не все мониторы поддержали команду."
        detail = errors[0] if errors else "Устройство не поддерживает изменение контрастности."
        return False, f"Не удалось изменить контрастность. {detail}"
