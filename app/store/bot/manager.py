import typing
from logging import getLogger

from app.quiz.models import StatusGame, UserAnswer
from app.store.vk_api.accessor import Keyboard
from app.store.vk_api.dataclasses import Update, Message, UpdateStatus

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        if updates:
            for update in updates:
                chat_id = str(update.object.peer_id)
                if update.action == UpdateStatus.INVITE_CHAT:
                    await self.app.store.vk_api.send_message(
                        Message(
                            peer_id=update.object.peer_id,
                            text="Вы пригласили бота 'Своя игра' \n Сделайте бота админом и воспользуетесь кнопками ниже что бы начать играть",
                        ),
                        keyboard=Keyboard.navigate
                    )
                elif update.action == UpdateStatus.START_GAME:
                    # нажали кнопку старт игры
                    users_from_chat = await self.app.store.vk_api.get_users_from_chat(peer_id=update.object.peer_id)
                    users = await self.app.store.quizzes.get_or_create_users(users=users_from_chat)
                    game = await self.app.store.quizzes.get_or_create_game(chat_id=chat_id,
                                                                           users=users)
                    current_question = await self.app.store.quizzes.get_question_for_chat(chat_id=chat_id)
                    await self.app.store.quizzes.set_current_question_for_game(question_id=current_question.id,
                                                                               game_id=game.id)
                    await self.app.store.vk_api.send_message(
                        Message(
                            peer_id=update.object.peer_id,
                            text=f"Игра началась. Первый вопрос: '{current_question.title}'",
                        ),
                        keyboard=Keyboard.navigate
                    )
                elif update.action == UpdateStatus.RESULT_GAME:
                    text_message = 'Нет текущей игры'
                    game = await self.app.store.quizzes.get_game_by_chat_id(chat_id=chat_id)
                    if game is not None and game.status == StatusGame.STARTED:
                        text_message = f'Результаты текущей игры №{game.id}'
                        user_score = await self.app.store.quizzes.get_user_score_by_game(game_id=game.id)
                        text_score = '\n'.join([f'Игрок {el.name}: {el.score_count} очков' for el in user_score])
                        text_message += text_score
                    await self.app.store.vk_api.send_message(
                        Message(
                            peer_id=update.object.peer_id,
                            text=text_message,
                        ),
                        keyboard=Keyboard.navigate
                    )

                else:
                    game = await self.app.store.quizzes.get_game_by_chat_id(chat_id=chat_id)
                    if game is not None and game.status == StatusGame.STARTED and game.current_question_id is not None:
                        correct_answer = await self.app.store.quizzes.get_correct_answer(question_id=game.current_question_id)
                        user = await self.app.store.quizzes.get_user_by_vk_id(vk_id=str(update.object.user_id))
                        user_answer = update.object.body
                        is_correct = correct_answer.title.lower() == user_answer.lower()
                        # Записываем объект ответа от юзера
                        user_answer = UserAnswer(user_id=user.id, chat_id=chat_id, is_correct=is_correct, answer=user_answer)
                        # print('correct_answer', correct_answer)
                        # print('user_answer', user_answer)
                        # print('user', user)
                        # print('game', game)
                        if is_correct:
                            # Если ответ верный обновляем игру и записываем очки юзеру
                            level_score = await self.app.store.quizzes.create_level_game(game=game, user=user)
                            user_count_score = await self.app.store.quizzes.get_count_score_by_game_and_user_id(game_id=game.id)
                            current_question = await self.app.store.quizzes.get_question_for_chat(chat_id=chat_id)
                            if current_question:
                                # если еще остались вопросы берем следующий
                                await self.app.store.quizzes.set_current_question_for_game(
                                    question_id=current_question.id,
                                    game_id=game.id
                                )
                                await self.app.store.vk_api.send_message(
                                    Message(
                                        peer_id=update.object.peer_id,
                                        text=f"Правильный ответ! {user.name} зачисленно {level_score.count} баллов."
                                             f"Общее количество очков {user_count_score}"
                                             f"Следующий вопрос '{current_question.title}'",
                                    )
                                )
                            else:
                                # вопросов не осталось завершаем игру
                                text_message = f"Правильный ответ! {user.name} зачисленно {level_score.count} баллов." \
                                               f"Игра завершена, вопросов не осталось"
                                await self.app.store.quizzes.set_status_for_game(
                                    status=StatusGame.FINISHED,
                                    game_id=game.id
                                )
                                await self.app.store.vk_api.send_message(
                                    Message(
                                        peer_id=update.object.peer_id,
                                        text=text_message,
                                    )
                                )
                        else:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text="неверный ответ",
                                )
                            )
                    else:
                        await self.app.store.vk_api.send_message(
                            Message(
                                peer_id=update.object.peer_id,
                                text="Привет!",
                            )
                        )
