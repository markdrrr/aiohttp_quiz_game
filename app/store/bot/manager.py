import typing
from logging import getLogger

from app.quiz.models import StatusGame
from app.store.vk_api.dataclasses import Update, UpdateStatus

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]) -> bool:
        if updates:
            for update in updates:
                chat_id = str(update.object.peer_id)
                sent_answer = False
                active_game = await self.app.store.game.get_game_by_chat_id(chat_id=chat_id)
                if active_game is None:
                    if update.action == UpdateStatus.INVITE_CHAT:
                        # бота пригласили в чат
                        sent_answer = await self.app.store.game_logic.action_invite(update=update)
                    elif update.action == UpdateStatus.FINISH_GAME:
                        # нажали кнопку завершить игру, но нет активной игры
                        sent_answer = await self.app.store.game_logic.already_finished(update=update)
                    elif update.action == UpdateStatus.START_GAME:
                        # нажали кнопку старт игры
                        sent_answer = await self.app.store.game_logic.action_start_game(update=update, chat_id=chat_id)
                else:
                    if update.action == UpdateStatus.START_GAME:
                        # нажали кнопку старт игры, но игра уже началась
                        sent_answer = await self.app.store.game_logic.already_started(update=update)
                    if update.action == UpdateStatus.FINISH_GAME:
                        # нажали кнопку завершить игру, завершаем игру
                        sent_answer = await self.app.store.game_logic.action_finish_game(update=update,
                                                                                         game=active_game)
                    if update.action not in UpdateStatus.KEYBOARD_ACTION and \
                            active_game.status == StatusGame.STARTED:
                        sent_answer = await self.app.store.game_logic.action_check_answer(update=update,
                                                                                          game=active_game)
                if update.action == UpdateStatus.RESULT_GAME:
                    # нажали кнопку результат игры
                    sent_answer = await self.app.store.game_logic.action_result_game(update=update, game=active_game)

                return sent_answer
