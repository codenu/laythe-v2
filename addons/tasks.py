from asyncio import Task, sleep

from dico import Activity, ActivityTypes

from laythe import LaytheAddonBase, LaytheBot


class Tasks(LaytheAddonBase):
    loop_status_task: Task

    def on_load(self):
        self.loop_status_task = self.bot.loop.create_task(self.loop_status())

    def on_unload(self):
        self.loop_status_task.cancel()

    async def loop_status(self):
        while True:
            try:
                await self.bot.wait_ready()

                texts = [
                    "'laythe.codenu.kr'을 방문해보세요!",
                    f"{self.bot.guild_count}개 서버에서 사용",
                ]
                for x in texts:
                    await self.bot.update_presence(
                        activities=[Activity(name=x, activity_type=ActivityTypes.GAME)]
                    )
                    await sleep(15)
            except:
                from traceback import print_exc

                print_exc()
                await sleep(15)


def load(bot: LaytheBot):
    bot.load_addons(Tasks)


def unload(bot: LaytheBot):
    bot.unload_addons(Tasks)
