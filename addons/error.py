import sys
import traceback

from dico import Embed
from dico_command import Addon, on
from dico_interaction import InteractionContext

from config import Config
from laythe import (
    PermissionUnavailable,
    PermissionNotFound,
    BotPermissionNotFound,
    permission_translates,
    LaytheBot,
    LaytheAddonBase,
)
from laythe.utils import EmbedColor


class Error(LaytheAddonBase, name="오류"):
    @on("interaction_error")
    async def on_interaction_error(self, ctx: InteractionContext, ex: Exception):
        if not ctx.deferred:
            await ctx.defer()
        tb = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        base = Embed(
            title="이런! ", color=EmbedColor.NEGATIVE, timestamp=ctx.id.timestamp
        )
        if Config.DEBUG:
            print(tb, file=sys.stderr)
        edited_tb = ("..." + tb[-1979:]) if len(tb) > 1982 else tb
        if isinstance(ex, BotPermissionNotFound):
            base.title += "이 서버에서 제 권한이 이 명령어를 실행하기에는 부족해요."
            base.description = f"`{'`, `'.join([permission_translates.get(x, x) for x in ex])}` 권한을 저에게 부여해주세요."
        elif isinstance(ex, PermissionNotFound):
            base.title += "이 명령어를 실행할 권한이 부족해요."
            base.description = f"이 명령어를 실행하기 위해 `{'`, `'.join([permission_translates.get(x, x) for x in ex])}` 권한이 필요해요."
        elif isinstance(ex, PermissionUnavailable):
            base.title += "권한 정보를 가져오지 못했어요."
            base.description = "명령어를 다시 사용해주세요. 그래도 문제가 계속된다면, [CodeNU](https://discord.gg/gqJBhar) 디스코드 서버에서 문의해주세요."
        else:
            base.title += "예기치 못한 오류가 발생했어요..."
            base.description = f"디버깅용 메시지: ```py\n{edited_tb}\n```"
            base.add_field(
                name="잠시만요!",
                value="이 오류 정보를 개발자에게 전송할까요? 오류 전송 시 오류 내용과 명령어를 실행한 메시지 내용이 전달돼요.",
            )
            report_required = True
        await ctx.send(embed=base)


def load(bot: LaytheBot):
    bot.load_addons(Error)


def unload(bot: LaytheBot):
    bot.unload_addons(Error)
