import os

from viberbot import Api, BotConfiguration

VIBER_TOKEN = os.environ["VIBER_TOKEN"]

api = Api(BotConfiguration(
    auth_token=VIBER_TOKEN,
    name="e_svitlo_bot",
    avatar=None
))
