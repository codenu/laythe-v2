import datetime
from math import floor
from typing import Dict, List, Optional

from dico import Overwrite, PermissionFlags, Snowflake
from dico.utils import rgb

permission_names = {
    getattr(PermissionFlags, x): x.lower()
    for x in dir(PermissionFlags)
    if isinstance(getattr(PermissionFlags, x), int)
}


class EmbedColor:
    NEUTRAL = 0x95A5A6
    NEGATIVE = 0xE74C3C
    POSITIVE = 0x2ECC71
    DEFAULT = rgb(225, 225, 225)


def parse_second(time: int, as_kor: bool = False) -> str:
    parsed_time = ""
    hour = time // (60 * 60)
    time -= hour * (60 * 60)
    minute = time // 60
    time -= minute * 60
    if hour:
        parsed_time += f"{hour:02d}{'시간 ' if as_kor else ':'}"
    parsed_time += (
        f"{minute:02d}{'분 ' if as_kor else ':'}"
        if minute
        else ("" if as_kor else "00:")
    )
    parsed_time += f"{time:02d}{'초' if as_kor else ''}"
    return parsed_time


def parse_second_with_date(time: int):
    parsed_time = ""
    day = time // (24 * 60 * 60)
    time -= day * (24 * 60 * 60)
    hour = time // (60 * 60)
    time -= hour * (60 * 60)
    minute = time // 60
    time -= minute * 60
    if day:
        parsed_time += f"{day}일 "
    if hour:
        parsed_time += f"{hour}시간 "
    if minute:
        parsed_time += f"{minute}분 "
    parsed_time += f"{time}초"
    return parsed_time


def create_index_bar(
    length: float,
    now: float,
    start_text_no_icon: str = "=",
    start_text_with_icon: str = "🔴",
    middle_bar_bright: str = "=",
    middle_bar_icon: str = "🔴",
    middle_bar_dim: str = "=",
    end_text_no_icon: str = "=",
    end_text_with_icon: str = "🔴",
    size: int = 30,
):
    percent = now / length
    pos = floor(percent * size)
    if pos == 0:
        base = start_text_with_icon + middle_bar_dim * (size - 2) + end_text_no_icon
    elif pos >= size - 1:
        base = start_text_no_icon + middle_bar_bright * (size - 2) + end_text_with_icon
    else:
        base = (
            start_text_no_icon
            + middle_bar_bright * (pos - 1)
            + middle_bar_icon
            + middle_bar_dim * (size - pos - 2)
            + end_text_no_icon
        )
    return f"{''.join(base)}"


def kstnow() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))


def restrict_length(text: str, max_length: int) -> str:
    if not text:
        return ""
    return ("..." + text[: max_length - 3]) if len(text) > max_length else text


def to_readable_bool(tf: bool):
    return "네" if tf else "아니요"


def overwrites_diff(original: List[Overwrite], current: List[Overwrite]):
    raise NotImplementedError
    resp = {}
    before: Dict[Snowflake, Overwrite] = {o.id: o for o in original}
    for overwrite in current:
        if overwrite.id not in before:
            # If this is new
            diff = {x: True for x in overwrite.allow}
            diff.update({x: False for x in overwrite.deny})
            resp[overwrite.id] = diff
            continue
        before_overwrite = before[overwrite.id]
        diff = {}
        for x in before_overwrite.allow:
            if x not in overwrite.allow:
                diff[x] = False if x in overwrite.deny else None
        # for x in before_overwrite.deny
