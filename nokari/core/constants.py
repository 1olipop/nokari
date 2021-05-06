"""A module that contains constants for consistency."""

from enum import Enum


class FieldType(Enum):
    opt = 0
    req = 1


def format_(s_: str, fmt: FieldType) -> str:
    if fmt is FieldType.req:
        return f"<{s_}>"

    return f"[{s_}]"


BASE = "name|id|mention"

types = ["user", "member", "role", "channel"]

for t in types:
    constant = t.upper()
    globals()[constant] = base = f"{t} {BASE}"
    globals()[f"{constant}_REQUIRED"] = format_(base, FieldType.req)
    globals()[f"{constant}_OPTIONAL"] = format_(base, FieldType.opt)
    constant_with_caret = f"{constant}_CARET"
    globals()[constant_with_caret] = base = f"{base}|^"
    globals()[f"{constant_with_caret}_REQUIRED"] = format_(base, FieldType.req)
    globals()[f"{constant_with_caret}_OPTIONAL"] = format_(base, FieldType.opt)

TEXT = "text"
TEXT_REQUIRED = "<text>"
TEXT_OPTIONAL = "[text]"
TEXT_CARET = "text|^"
TEXT_CARET_REQUIRED = "<text|^>"
TEXT_CARET_OPTIONAL = "[text|^]"

EMOJI = "emoji name|id"
EMOJI_REQUIRED = format_(EMOJI, FieldType.req)
EMOJI_OPTIONAL = format_(EMOJI, FieldType.opt)