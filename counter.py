# counter.py
from __future__ import annotations
from datetime import datetime, date
from dateutil import tz
import re
from typing import Optional

TZ = tz.gettz("Europe/Moscow")

PRESETS: dict[str, str] = {
    "тимоха": "2026-11-07",
    "сезон":  "2026-07-15",
    "зхд":    "2026-05-20",
    "рома":   "2026-09-10",
    # "нграница": "2026-01-01",
}

def _parse_date(text: str) -> Optional[date]:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text.strip())
    if m:
        y, mth, d = map(int, m.groups())
        return date(y, mth, d)
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text.strip())
    if m:
        d, mth, y = map(int, m.groups())
        return date(y, mth, d)
    return None

def _days_until(target: date, *, inclusive: bool = False) -> int:
    today = datetime.now(TZ).date()
    delta = (target - today).days
    if inclusive:
        delta += 1
    return delta

CMD_RE = re.compile(r"!([A-Za-zА-Яа-яЁё0-9_-]+)")

def _extract_bang_word(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    m = CMD_RE.search(text)
    return m.group(1) if m else None

def _lookup_word(word: str) -> Optional[date]:
    raw = PRESETS.get(word.strip().lower())
    return _parse_date(raw) if raw else None

def get_days_reply(message_text: str, *, inclusive: bool = False) -> Optional[str]:
    """
    Возвращает строку с числом дней ИЛИ None.
    None означает: команда не найдена или неизвестное слово — НЕ ОТВЕЧАТЬ.
    """
    word = _extract_bang_word(message_text)
    if not word:
        return None
    target = _lookup_word(word)
    if target is None:
        return None
    return str(_days_until(target, inclusive=inclusive))

if __name__ == "__main__":
    tests = ["!тимоха", "!сезон", "!зхд", "!рома"]
    for t in tests:
        print(t, "->", get_days_reply(t))
