from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QSlider, QLineEdit, QCheckBox, QMessageBox, QInputDialog,
    QFrame
)
from .models import Profile
from . import autostart


class MainWindow(QWidget):
    apply_requested = Signal(str)
    profiles_changed = Signal()
    support_check_requested = Signal()

    def __init__(self, store, monitor_controller):
        super().__init__()
        self.store = store
        self.monitor_controller = monitor_controller
        self.setWindowTitle("Contrast Manager")
        self.setMinimumSize(560, 430)
        self.resize(620, 470)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Contrast Manager")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.status_label = QLabel("Проверка монитора не выполнялась")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(230)
        header.addWidget(self.status_label)
        root.addLayout(header)

        body = QHBoxLayout()
        self.profile_list = QListWidget()
        self.profile_list.setMinimumWidth(190)
        self.profile_list.currentItemChanged.connect(self._selection_changed)
        body.addWidget(self.profile_list, 2)

        editor = QVBoxLayout()
        editor.setSpacing(10)
        editor.addWidget(QLabel("Название режима"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например, Игры")
        self.name_edit.setMaxLength(40)
        editor.addWidget(self.name_edit)

        self.contrast_label = QLabel("Контрастность: 50%")
        editor.addWidget(self.contrast_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(lambda value: self.contrast_label.setText(f"Контрастность: {value}%"))
        editor.addWidget(self.slider)

        row = QHBoxLayout()
        self.new_button = QPushButton("Новый")
        self.save_button = QPushButton("Сохранить")
        self.delete_button = QPushButton("Удалить")
        self.new_button.clicked.connect(self.new_profile)
        self.save_button.clicked.connect(self.save_profile)
        self.delete_button.clicked.connect(self.delete_profile)
        row.addWidget(self.new_button)
        row.addWidget(self.save_button)
        row.addWidget(self.delete_button)
        editor.addLayout(row)

        self.default_button = QPushButton("Сделать режимом по умолчанию")
        self.default_button.clicked.connect(self.set_default)
        editor.addWidget(self.default_button)
        self.apply_button = QPushButton("Применить сейчас")
        self.apply_button.setObjectName("primary")
        self.apply_button.clicked.connect(self.apply_current)
        editor.addWidget(self.apply_button)
        editor.addStretch()
        body.addLayout(editor, 3)
        root.addLayout(body, 1)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        root.addWidget(separator)

        footer = QHBoxLayout()
        self.check_button = QPushButton("Проверить монитор")
        self.check_button.clicked.connect(self.check_support)
        footer.addWidget(self.check_button)
        self.autostart_check = QCheckBox("Запускать с Windows")
        self.autostart_check.setChecked(autostart.is_enabled())
        self.autostart_check.toggled.connect(self.toggle_autostart)
        footer.addWidget(self.autostart_check)
        root.addLayout(footer)

        self.refresh_profiles()
        self.setStyleSheet("""
            QWidget { background: #f7f7f8; color: #202124; font-size: 13px; }
            QLabel#title { font-size: 21px; font-weight: 600; }
            QLabel#muted { color: #6b7280; font-size: 11px; }
            QListWidget { background: white; border: 1px solid #e0e1e4; border-radius: 8px; padding: 5px; }
            QListWidget::item { padding: 10px 8px; border-radius: 5px; }
            QListWidget::item:selected { background: #e8ecf8; color: #172554; }
            QLineEdit { background: white; border: 1px solid #d6d8dd; border-radius: 6px; padding: 9px; }
            QPushButton { background: white; border: 1px solid #d6d8dd; border-radius: 6px; padding: 9px 10px; }
            QPushButton:hover { background: #eff0f2; }
            QPushButton#primary { background: #252a34; color: white; border-color: #252a34; font-weight: 600; }
            QPushButton#primary:hover { background: #3b414d; }
            QSlider::groove:horizontal { height: 4px; background: #d9dce2; border-radius: 2px; }
            QSlider::handle:horizontal { background: #343b49; width: 14px; margin: -5px 0; border-radius: 7px; }
            QCheckBox { spacing: 7px; }
            QFrame#separator { color: #e1e2e5; }
        """)

    def refresh_profiles(self, select_id=None):
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        for profile in self.store.profiles:
            suffix = "  · по умолчанию" if profile.id == self.store.default_profile_id else ""
            item = QListWidgetItem(profile.name + suffix)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self.profile_list.addItem(item)
            if profile.id == (select_id or self.store.active_profile_id):
                self.profile_list.setCurrentItem(item)
        if self.profile_list.currentRow() < 0 and self.profile_list.count():
            self.profile_list.setCurrentRow(0)
        self.profile_list.blockSignals(False)
        self._selection_changed(self.profile_list.currentItem(), None)

    def selected_profile(self):
        item = self.profile_list.currentItem()
        return self.store.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _selection_changed(self, current, previous):
        profile = self.selected_profile()
        if not profile:
            self.name_edit.clear()
            self.slider.setValue(50)
            return
        self.name_edit.setText(profile.name)
        self.slider.setValue(profile.contrast)

    def new_profile(self):
        self.profile_list.clearSelection()
        self.name_edit.clear()
        self.name_edit.setFocus()
        self.slider.setValue(50)

    def save_profile(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Название режима", "Введите название режима.")
            return
        current = self.selected_profile()
        if self.store.name_exists(name, current.id if current else None):
            QMessageBox.warning(self, "Название режима", "Режим с таким названием уже существует.")
            return
        if current:
            current.name = name
            current.contrast = self.slider.value()
            profile = current
        else:
            profile = Profile.create(name, self.slider.value())
            self.store.profiles.append(profile)
            if not self.store.default_profile_id:
                self.store.default_profile_id = profile.id
        self.store.save()
        self.refresh_profiles(profile.id)
        self.profiles_changed.emit()

    def delete_profile(self):
        profile = self.selected_profile()
        if not profile:
            return
        if len(self.store.profiles) <= 1:
            QMessageBox.information(self, "Удаление режима", "Должен остаться хотя бы один режим.")
            return
        answer = QMessageBox.question(self, "Удалить режим", f"Удалить «{profile.name}»?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.store.profiles = [p for p in self.store.profiles if p.id != profile.id]
        if self.store.default_profile_id == profile.id:
            self.store.default_profile_id = self.store.profiles[0].id
        if self.store.active_profile_id == profile.id:
            self.store.active_profile_id = None
        self.store.save()
        self.refresh_profiles()
        self.profiles_changed.emit()

    def set_default(self):
        profile = self.selected_profile()
        if not profile:
            return
        self.store.default_profile_id = profile.id
        self.store.save()
        self.refresh_profiles(profile.id)
        self.profiles_changed.emit()

    def apply_current(self):
        profile = self.selected_profile()
        if profile:
            self.apply_requested.emit(profile.id)

    def check_support(self):
        self.check_button.setEnabled(False)
        self.status_label.setText("Проверка…")
        from PySide6.QtCore import QTimer
        # Defer blocking hardware access until after the UI has repainted.
        QTimer.singleShot(50, self._run_support_check)

    def _run_support_check(self):
        status = self.monitor_controller.check_support()
        self.status_label.setText(status.message)
        self.check_button.setEnabled(True)
        QMessageBox.information(self, "Поддержка монитора", status.message)

    def toggle_autostart(self, enabled):
        ok, message = autostart.set_enabled(enabled)
        if not ok:
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(not enabled)
            self.autostart_check.blockSignals(False)
            QMessageBox.warning(self, "Автозапуск", message)

    def show_status(self, message, success):
        self.status_label.setText(message)
        if not success:
            QMessageBox.warning(self, "Contrast Manager", message)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
