"""Global hotkeys via the built-in Windows RegisterHotKey API."""
import ctypes
import sys
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND), ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD), ("pt_x", wintypes.LONG), ("pt_y", wintypes.LONG),
    ]


class HotkeyFilter(QObject, QAbstractNativeEventFilter):
    activated = Signal(int)

    def __init__(self):
        QObject.__init__(self)
        QAbstractNativeEventFilter.__init__(self)
        self.user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self.registered = []

    def register(self, profile_count: int):
        if not self.user32:
            return
        self.unregister()
        # Ctrl+Alt+1 ... Ctrl+Alt+9 apply the first nine profiles in list order.
        for index in range(min(profile_count, 9)):
            hotkey_id = 7100 + index
            vk = 0x31 + index
            if self.user32.RegisterHotKey(None, hotkey_id, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk):
                self.registered.append(hotkey_id)

    def unregister(self):
        if self.user32:
            for hotkey_id in self.registered:
                self.user32.UnregisterHotKey(None, hotkey_id)
        self.registered.clear()

    def nativeEventFilter(self, event_type, message):
        if not self.user32:
            return False, 0
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents
            if msg.message == WM_HOTKEY and msg.wParam in self.registered:
                self.activated.emit(int(msg.wParam) - 7100)
                return True, 0
        except BaseException:
            return False, 0
        return False, 0
