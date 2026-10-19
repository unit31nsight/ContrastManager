from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Profile:
    id: str
    name: str
    contrast: int

    @classmethod
    def create(cls, name: str, contrast: int) -> "Profile":
        return cls(id=uuid4().hex, name=name.strip(), contrast=int(contrast))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "contrast": self.contrast}

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        name = str(data.get("name", "")).strip()[:40]
        contrast = max(0, min(100, int(data.get("contrast", 50))))
        profile_id = str(data.get("id") or uuid4().hex)
        if not name:
            raise ValueError("У профиля должно быть название.")
        return cls(profile_id, name, contrast)
