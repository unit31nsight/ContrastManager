
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QApplication,
)


def create_tray_icon():
    """Создаёт видимую иконку без отдельного файла изображения."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QPen(QColor("#343b49"), 2))
    painter.setBrush(QColor("#e8ecf8"))
    painter.drawRoundedRect(3, 3, 26, 26, 6, 6)

    painter.setPen(QPen(QColor("#343b49"), 3))
    painter.drawLine(9, 11, 23, 11)
    painter.drawLine(9, 16, 23, 16)
    painter.drawLine(9, 21, 23, 21)

    painter.end()
    return QIcon(pixmap)


class TrayController(QObject):
    apply_requested = Signal(str)

    def __init__(self, app, store, window):
        super().__init__()
        self.app = app
        self.store = store
        self.window = window

        self.tray = QSystemTrayIcon(create_tray_icon(), self)
        self.tray.setToolTip("Contrast Manager")

        self.menu = QMenu()
        self.profile_menu = self.menu.addMenu("Режимы")

        self.menu.addSeparator()

        open_action = QAction("Открыть настройки", self.menu)
        open_action.triggered.connect(self.show_window)
        self.menu.addAction(open_action)

        self.menu.addSeparator()

        quit_action = QAction("Выход", self.menu)
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activated)
        self.tray.show()

        self.hotkeys = None

        from .hotkeys import HotkeyFilter
        import sys

        if sys.platform == "win32":
            self.hotkeys = HotkeyFilter()
            self.app.installNativeEventFilter(self.hotkeys)
            self.hotkeys.activated.connect(self._hotkey_activated)

        self.refresh_menu()

    def refresh_menu(self):
        self.profile_menu.clear()

        for index, profile in enumerate(self.store.profiles):
            label = profile.name

            if profile.id == self.store.active_profile_id:
                label = "✓  " + label

            action = QAction(label, self.profile_menu)
            action.triggered.connect(
                lambda checked=False, pid=profile.id:
                    self.apply_requested.emit(pid)
            )

            if index < 9:
                action.setToolTip(f"Ctrl+Alt+{index + 1}")

            self.profile_menu.addAction(action)

        if self.hotkeys is not None:
            self.hotkeys.register(len(self.store.profiles))

    def _hotkey_activated(self, index):
        if index < len(self.store.profiles):
            self.apply_requested.emit(
                self.store.profiles[index].id
            )

    def _activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_window()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def quit(self):
        if self.hotkeys is not None:
            self.hotkeys.unregister()
            self.app.removeNativeEventFilter(self.hotkeys)

        self.tray.hide()
        self.app.quit()
