import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtGui import QIcon
from .profile_store import ProfileStore
from .monitor import MonitorController
from .window import MainWindow
from .tray import TrayController


def main():
    if sys.platform != "win32":
        print("Contrast Manager рассчитан на Windows 10/11.")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("ContrastManager")
    app.setOrganizationName("ContrastManager")
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "Contrast Manager",
            "Системный трей недоступен. Приложение не может работать в фоне."
        )
        return 1

    store = ProfileStore()
    monitor_controller = MonitorController()

    # Сохраняем исходную контрастность до переключения профилей.
    monitor_controller.remember_original_contrast()

    # Восстанавливаем её при штатном завершении приложения.
    app.aboutToQuit.connect(
        monitor_controller.restore_original_contrast
    )

    window = MainWindow(store, monitor_controller)
    tray = TrayController(app, store, window)
    tray.apply_requested.connect(lambda profile_id: apply_profile(
        profile_id, store, monitor_controller, window, tray
    ))
    window.apply_requested.connect(lambda profile_id: apply_profile(
        profile_id, store, monitor_controller, window, tray
    ))
    window.profiles_changed.connect(tray.refresh_menu)

    default = store.get(store.default_profile_id) if store.default_profile_id else None
    if default:
        # Startup applies the default profile only when the user has explicitly enabled
        # autostart or selected a profile. We don't change monitor hardware on first launch.
        pass

    window.show()
    return app.exec()


def apply_profile(profile_id, store, monitor_controller, window, tray):
    profile = store.get(profile_id)
    if not profile:
        return
    ok, message = monitor_controller.set_contrast(profile.contrast)
    if ok:
        store.active_profile_id = profile.id
        store.save()
        tray.refresh_menu()
        window.show_status(f"{profile.name}: {message}", True)
    else:
        window.show_status(message, False)


if __name__ == "__main__":
    raise SystemExit(main())
