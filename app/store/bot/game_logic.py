import asyncio

from app.quiz.models import StatusGame, Game, User
from app.store.bot.consts import BotMessage
from app.store.vk_api.accessor import Keyboard
from app.store.vk_api.dataclasses import Message, Update


class GameLogic:
    WIN_SCORE = 100
    TIME_FOR_QUESTION = 30  # секунд

    def __init__(self, app: "Application"):
        self.app = app

    async def action_invite(self, update: Update) -> bool:
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.INVITE_TEXT
            ),
            keyboard=Keyboard.navigate
        )
        return True

    async def already_started(self, update: Update) -> bool:
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.ALREADY_STARTED
            )
        )
        return True

    async def already_finished(self, update: Update) -> bool:
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.ALREADY_FINISHED
            )
        )
        return True

    async def action_finish_game(self, update: Update, game: Game) -> bool:
        await self.app.store.game.set_status_for_game(game_id=game.id, status=StatusGame.FINISHED)
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.FINISHED
            )
        )
        return True

    async def update_game_without_answer(self, game: Game) -> Game:
        await self.app.store.game.add_finished_question_ids_for_game(
            game_id=game.id,
            current_question_ids=game.finish_question_ids,
            new_finished_question_id=game.current_question_id
        )
        game.finish_question_ids.append(game.current_question_id)
        return game

    async def check_time_question(self, question_id: int, chat_id: int) -> bool:
        await asyncio.sleep(self.TIME_FOR_QUESTION)
        game = await self.app.store.game.get_game_by_chat_id(chat_id=chat_id)
        current_question = game.get_current_question()
        # если до сих пор текущий вопрос тот же, переходим к следующему вопросу
        if question_id == current_question.id:
            game = await self.update_game_without_answer(game=game)
            text_message = await self.next_question(game=game, answered=False)
            await self.app.store.vk_api.send_message(
                Message(
                    peer_id=chat_id,
                    text=text_message,
                ),
                keyboard=Keyboard.navigate
            )
        return True

    async def action_start_game(self, update: Update, chat_id: int) -> bool:
        users = await self.app.store.vk_api.get_users_from_chat(peer_id=update.object.peer_id)
        game = await self.app.store.game.create_game(chat_id=chat_id, users=users)
        current_question = game.get_question_for_chat()
        await self.app.store.game.set_current_question_for_game(question_id=current_question.id,
                                                                game_id=game.id)
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.START_GAME_TEXT.format(question_title=current_question.title),
            ),
            keyboard=Keyboard.navigate
        )
        # запускаем в фоне проверку если выйдет время на ответ
        asyncio.create_task(self.check_time_question(question_id=current_question.id, chat_id=chat_id))
        return True

    async def action_result_game(self, update: Update, game: Game) -> bool:
        text_message = BotMessage.NO_RESULT_GAME
        if game is not None and game.status == StatusGame.STARTED:
            text_message = BotMessage.RESULT_GAME.format(game_id=game.id)
            user_scores = await self.app.store.game.get_user_score_by_game(game_id=game.id)
            text_score = '\n'.join([f'Игрок {el.first_name}: {el.points} очков' for el in user_scores])
            text_message += text_score
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=text_message,
            ),
            keyboard=Keyboard.navigate
        )
        return True

    async def next_question(self, game: Game, answered: bool = True, user: User = None) -> str:
        current_question = game.get_question_for_chat()
        if current_question:
            # если еще остались вопросы берем следующий
            await self.app.store.game.set_current_question_for_game(
                question_id=current_question.id,
                game_id=game.id
            )
            if answered and user:
                text_message = f"Правильный ответ! {user.first_name} зачисленно {self.WIN_SCORE} баллов. " \
                               f"Следующий вопрос '{current_question.title}'"
            else:
                text_message = BotMessage.NO_ANSWER_FOR_TIME + f"Следующий вопрос '{current_question.title}'"

            # запускаем в фоне проверку на время для следующего вопроса
            asyncio.create_task(self.check_time_question(question_id=current_question.id, chat_id=game.chat_id))
        else:
            # вопросов не осталось завершаем игру
            if answered and user:
                text_message = f"Правильный ответ! {user.first_name} зачисленно {self.WIN_SCORE} баллов."
            else:
                text_message = BotMessage.NO_ANSWER_FOR_TIME
            text_message += f"Игра завершена, вопросов не осталось " \
                            f"Результаты"
            user_scores = await self.app.store.game.get_user_score_by_game(game_id=game.id)
            text_score = '\n'.join([f'Игрок {el.first_name}: {el.points} очков' for el in user_scores])
            text_message += text_score
            user_winner = game.get_winner()
            await self.app.store.game.set_status_for_game(
                status=StatusGame.FINISHED,
                game_id=game.id,
                winner_user_id=user_winner.id,
            )
        return text_message

    async def action_check_answer(self, update: Update, game: Game) -> bool:
        current_question = game.get_current_question()
        correct_answer = current_question.get_correct_answer()
        user = game.get_user(vk_id=update.object.user_id)
        user_answer = update.object.body
        is_correct = correct_answer.title.lower() == user_answer.lower()
        if is_correct:
            # Если ответ верный обновляем игру и записываем очки юзеру
            user.points += self.WIN_SCORE
            await self.app.store.game.create_level_game(game=game, user=user)
            text_message = await self.next_question(game=game, user=user, answered=True)
        else:
            text_message = BotMessage.WRONG_ANSWER

        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=text_message,
            )
        )
        return True
