import os
import sys
import logging

from dico import __version__ as dico_version
from dico_command import __version__ as command_version
from dico_interaction import __version__ as interaction_version

from module import LaytheBot

print(
    r"""
 _                    _    _           
| |                  | |  | |          
| |      __ _  _   _ | |_ | |__    ___ 
| |     / _` || | | || __|| '_ \  / _ \
| |____| (_| || |_| || |_ | | | ||  __/
\_____/ \__,_| \__, | \__||_| |_| \___|
                __/ |                  
               |___/                   
"""
)

print(
    f"""Laythe v2
Powered by dico {dico_version}, dico-command {command_version}, and dico-interaction {interaction_version}.
Please wait..."""
)


logger = logging.getLogger("laythe")
logging.basicConfig(level=logging.DEBUG)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
handler = logging.FileHandler(filename="laythe.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

bot = LaytheBot(logger=logger)

[
    bot.load_module(f"addons.{x[:-3]}")
    for x in os.listdir("addons")
    if not x.startswith("_")
]
bot.load_module("dp")
bot.run()
