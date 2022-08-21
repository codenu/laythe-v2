import asyncio

from aiohttp.web import (
    Application,
    Request,
    AppRunner,
    TCPSite,
    json_response,
    Response,
)
from dico.exception import HTTPError

from laythe import LaytheAddonBase, LaytheBot, Setting


class Dashboard(LaytheAddonBase):
    app: Application
    runner: AppRunner

    def on_load(self):
        self.app = Application()
        self.app.router.add_post("/userinfos", self.get_user_infos)
        self.app.router.add_post("/levels", self.get_required_levels)
        self.app.router.add_get("/guild/{id}", self.get_guild)
        self.app.router.add_post("/settings", self.set_settings)
        self.bot.loop.create_task(self.start())

    def on_unload(self):
        self.bot.loop.create_task(self.stop())

    async def start(self):
        self.runner = AppRunner(self.app)
        await self.runner.setup()
        site = TCPSite(self.runner, host="0.0.0.0", port=3001)
        await site.start()

    async def stop(self):
        await self.runner.cleanup()

    async def get_user_infos(self, request: Request):
        guild_ids = None
        user_ids = None
        if request.body_exists:
            body = await request.json()
            guild_ids = body.get("guilds")
            user_ids = body.get("users")
        if not guild_ids or not user_ids:
            return json_response({"reason": "Invalid form."}, status=400)

        users = {}

        for guild_id in guild_ids:
            guild_users = {"unresolved": []}
            for user_id in user_ids:
                cached = self.bot.cache.get_guild_container(guild_id)
                member = cached.get(user_id, "member")
                if member:
                    guild_users[str(member.id)] = {
                        "avatar_url": member.avatar_url(),
                        "nick": member.nick or member.user.username,
                        "name": str(member.user),
                        "permissions": str(member.permissions.value),
                    }
                    continue
                try:
                    member = await self.bot.request_guild_member(guild_id, user_id)
                    guild_users[str(member.id)] = {
                        "avatar_url": member.avatar_url(),
                        "nick": member.nick or member.user.username,
                        "name": str(member.user),
                        "permissions": str(member.permissions.value),
                    }
                except HTTPError:
                    guild_users["unresolved"].append(user_id)
            users[guild_id] = guild_users

        return json_response(users)

    async def get_required_levels(self, request: Request):
        levels = None
        exps = None
        if request.body_exists:
            body = await request.json()
            levels = body.get("levels")
            exps = body.get("exps")
        if not levels or not exps:
            return json_response({"reason": "Invalid form."}, status=400)

        level_addon = self.bot.addons[self.bot.addon_names.index("레벨")]

        resp = []

        for i, level in enumerate(levels):
            exp = level_addon.calc_exp_required(int(level) + 1)
            exp_before = level_addon.calc_exp_required(int(level))
            before = int(exps[i])
            resp.append(
                [
                    str(round(exp)),
                    str(round(((before - exp_before) / (exp - exp_before)) * 100)),
                ]
            )

        return json_response(resp)

    async def get_guild(self, request: Request):
        guild_id = request.match_info["id"]
        force = request.query.get("force")
        guild = self.bot.cache.get(guild_id, "guild") if not force else None
        """
        if not guild:
            try:
                guild = await self.bot.request_guild(guild_id)
            except HTTPError:
                guild = {}
        """
        return json_response(guild.raw if guild else guild)

    async def set_settings(self, request: Request):
        if not request.body_exists:
            return json_response({"reason": "Invalid form."}, status=400)
        try:
            body = await request.json()
            setting = Setting(body)
        except KeyError:
            return json_response({"reason": "Invalid body."}, status=400)
        await self.bot.database.update_guild_setting(setting)
        return Response(status=204)


def load(bot: LaytheBot):
    bot.load_addons(Dashboard)


def unload(bot: LaytheBot):
    bot.unload_addons(Dashboard)
