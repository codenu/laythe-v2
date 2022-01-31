from dico.utils import rgb


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
