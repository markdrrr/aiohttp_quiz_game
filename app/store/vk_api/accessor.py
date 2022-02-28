import json
import random
import typing
from typing import Optional, List

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.quiz.models import User
from app.store.vk_api.dataclasses import Update, Message, UpdateObject, UpdateStatus
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"


class Keyboard:
    navigate = {
        # "one_time": False,
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": {"button": UpdateStatus.START_GAME},
                        "label": "Начать игру"
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "text",
                        "payload": {"button": UpdateStatus.FINISH_GAME},
                        "label": "Завершить игру"
                    },
                    "color": "negative"
                },
                {
                    "action": {
                        "type": "text",
                        "payload": {"button": UpdateStatus.RESULT_GAME},
                        "label": "Результаты"
                    },
                    "color": "primary"
                },
            ]
        ]
    }


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method="groups.getLongPollServer",
                    params={
                        "group_id": self.app.config.bot.group_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def _get_users_chat(self, peer_id: int):
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method="messages.getConversationMembers",
                    params={
                        "peer_id": peer_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = (await resp.json())["response"]
            return data.get("profiles", [])

    async def get_users_from_chat(self, peer_id: int) -> List[User]:
        """ Получаем список юзеров из чата по peer_id """
        users = []
        try:
            profiles = await self._get_users_chat(peer_id=peer_id)
        except Exception as e:
            profiles = []
            self.logger.error("Exception", exc_info=e)
        for profile in profiles:
            user = await self.app.store.users.create_user(
                vk_id=str(profile['id']),
                name=f'{profile["first_name"]} {profile["last_name"]}',
                is_admin=False,
            )
            users.append(user)
        return users

    async def poll(self):
        async with self.session.get(
                self._build_query(
                    host=self.server,
                    method="",
                    params={
                        "act": "a_check",
                        "key": self.key,
                        "ts": self.ts,
                        "wait": 30,
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                type_chat = 'public' if update["object"]["message"]["peer_id"] > 2000000000 else 'privat'
                action = update.get("object", {}).get("message", {}).get("action", {}).get("type")
                if action is None:
                    payload = update.get("object", {}).get("message", {}).get("payload")
                    action = json.loads(payload).get('button') if payload is not None else None

                updates.append(
                    Update(
                        type=update["type"],
                        action=action,
                        object=UpdateObject(
                            id=update["object"]["message"]["id"],
                            user_id=update["object"]["message"]["from_id"],
                            peer_id=update["object"]["message"]["peer_id"],
                            body=update["object"]["message"]["text"],
                            type_chat=type_chat,
                        ),
                    )
                )
            await self.app.store.bots_manager.handle_updates(updates)

    async def send_message(self, message: Message, keyboard: str = None) -> None:
        params = {
            # "user_id": message.user_id,
            "random_id": random.randint(1, 2 ** 32),
            # "peer_id": "-" + str(self.app.config.bot.group_id),
            "peer_id": message.peer_id,
            "message": message.text,
            "access_token": self.app.config.bot.token,
            # "one_time": 'false',
            # "keyboard": json.dumps(keyboard),
        }
        if keyboard:
            params["keyboard"] = json.dumps(keyboard)

        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "messages.send",
                    params=params,
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
