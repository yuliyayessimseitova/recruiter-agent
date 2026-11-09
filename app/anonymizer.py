"""Обезличивание текста перед отправкой в LLM. Личные данные -> метки, словарь хранится локально."""
import re
from dataclasses import dataclass, field

PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("URL", re.compile(r"(?:https?://|www\.|t\.me/|linkedin\.com/|instagram\.com/)\S+", re.I)),
    ("IIN", re.compile(r"(?<!\d)\d{12}(?!\d)")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?7|8)[\s(-]*\d{3}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")),
    ("USERNAME", re.compile(r"(?<![\w@])@[A-Za-z][\w]{3,31}")),
]


@dataclass
class Anonymizer:
    mapping: dict = field(default_factory=dict)  # метка -> оригинал (хранить только в БД на сервере РК)
    _rev: dict = field(default_factory=dict)
    _count: dict = field(default_factory=dict)

    def _label(self, kind: str, value: str) -> str:
        if value in self._rev:
            return self._rev[value]
        n = self._count[kind] = self._count.get(kind, 0) + 1
        label = f"[{kind}_{n}]"
        self.mapping[label] = value
        self._rev[value] = label
        return label

    def add_known(self, kind: str, value: str):
        """Известные данные (например имя кандидата из анкеты) -> метка во всех вхождениях."""
        if value:
            self._label(kind, value)

    def anonymize(self, text: str) -> str:
        for value, label in sorted(self._rev.items(), key=lambda x: -len(x[0])):
            text = re.sub(re.escape(value), label, text, flags=re.I)
        for kind, rx in PATTERNS:
            text = rx.sub(lambda m, k=kind: self._label(k, m.group(0)), text)
        return text

    def restore(self, text: str) -> str:
        for label, value in self.mapping.items():
            text = text.replace(label, value)
        return text
