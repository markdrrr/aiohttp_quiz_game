from app.quiz.models import StatusGame, Game
from app.store.bot.consts import BotMessage
from app.store.vk_api.accessor import Keyboard
from app.store.vk_api.dataclasses import Message, Update


class GameLogic:

    WIN_SCORE = 100

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

    async def action_start_game(self, update: Update, chat_id: str) -> bool:
        users = await self.app.store.vk_api.get_users_from_chat(peer_id=update.object.peer_id)
        game = await self.app.store.game.create_game(chat_id=chat_id, users=users)
        current_question = await game.get_question_for_chat()

        await self.app.store.game.set_current_question_for_game(question_id=current_question.id,
                                                                game_id=game.id)
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=BotMessage.START_GAME_TEXT.substitute(question_title=current_question.title),
            ),
            keyboard=Keyboard.navigate
        )
        return True

    async def action_result_game(self, update: Update, game: Game) -> bool:
        text_message = BotMessage.NO_RESULT_GAME
        if game is not None and game.status == StatusGame.STARTED:
            text_message = BotMessage.RESULT_GAME.substitute(game_id=game.id)
            user_scores = await self.app.store.game.get_user_score_by_game(game_id=game.id)
            text_score = '\n'.join([f'Игрок {el.name}: {el.score_count} очков' for el in user_scores])
            text_message += text_score
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=text_message,
            ),
            keyboard=Keyboard.navigate
        )
        return True

    async def action_check_answer(self, update: Update, game: Game) -> bool:
        current_question = await game.get_current_question()
        correct_answer = await current_question.get_correct_answer()
        user = await game.get_user(vk_id=str(update.object.user_id))
        user_answer = update.object.body
        is_correct = correct_answer.title.lower() == user_answer.lower()
        if is_correct:
            # Если ответ верный обновляем игру и записываем очки юзеру
            user.count_score += self.WIN_SCORE
            await self.app.store.game.create_level_game(game=game, user=user)
            current_question = await game.get_question_for_chat()
            if current_question:
                # если еще остались вопросы берем следующий
                await self.app.store.game.set_current_question_for_game(
                    question_id=current_question.id,
                    game_id=game.id
                )
                text_message = f"Правильный ответ! {user.name} зачисленно {self.WIN_SCORE} баллов. " \
                               f"Следующий вопрос '{current_question.title}'"
            else:
                # вопросов не осталось завершаем игру
                text_message = f"Правильный ответ! {user.name} зачисленно {self.WIN_SCORE} баллов." \
                               f"Игра завершена, вопросов не осталось" \
                               f"Результаты"
                user_scores = await self.app.store.game.get_user_score_by_game(game_id=game.id)
                text_score = '\n'.join([f'Игрок {el.name}: {el.score_count} очков' for el in user_scores])
                text_message += text_score
                await self.app.store.game.set_status_for_game(
                    status=StatusGame.FINISHED,
                    game_id=game.id
                )
        else:
            text_message = BotMessage.WRONG_ANSWER

        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.peer_id,
                text=text_message,
            )
        )
        return True
