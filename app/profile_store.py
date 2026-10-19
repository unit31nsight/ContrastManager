import json
from pathlib import Path
from PySide6.QtCore import QStandardPaths
from .models import Profile


class ProfileStore:
    def __init__(self):
        base = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        ))
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "profiles.json"
        self.profiles: list[Profile] = []
        self.default_profile_id: str | None = None
        self.active_profile_id: str | None = None
        self.load()

    def load(self):
        if not self.path.exists():
            self.profiles = [
                Profile.create("Работа", 60),
                Profile.create("Игры", 75),
                Profile.create("Фильмы", 70),
            ]
            self.default_profile_id = self.profiles[0].id
            self.save()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.profiles = [Profile.from_dict(item) for item in raw.get("profiles", [])]
            if not self.profiles:
                self.profiles = [Profile.create("Стандартный", 50)]
            ids = {p.id for p in self.profiles}
            self.default_profile_id = raw.get("default_profile_id")
            if self.default_profile_id not in ids:
                self.default_profile_id = self.profiles[0].id
            self.active_profile_id = raw.get("active_profile_id")
            if self.active_profile_id not in ids:
                self.active_profile_id = None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Keep the application usable if the config file was damaged.
            self.profiles = [Profile.create("Стандартный", 50)]
            self.default_profile_id = self.profiles[0].id
            self.active_profile_id = None

    def save(self):
        payload = {
            "profiles": [p.to_dict() for p in self.profiles],
            "default_profile_id": self.default_profile_id,
            "active_profile_id": self.active_profile_id,
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, profile_id: str) -> Profile | None:
        return next((p for p in self.profiles if p.id == profile_id), None)

    def name_exists(self, name: str, except_id: str | None = None) -> bool:
        return any(p.name.casefold() == name.casefold() and p.id != except_id
                   for p in self.profiles)
