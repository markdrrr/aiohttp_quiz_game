from typing import List
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Theme,
    Question,
    Answer,
    ThemeModel,
    QuestionModel,
    AnswerModel, User, UserModel, GameModel, StatusGame, Game, Score, ScoreModel, UserScore,
)
from app.store.database.gino import db


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        res = await ThemeModel.create(title=title)
        return Theme(id=res.id, title=res.title)

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        res = await ThemeModel.query.where(ThemeModel.title == title).gino.first()
        if res:
            return Theme(id=res.id, title=res.title)

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        res = await ThemeModel.query.where(ThemeModel.id == id_).gino.first()
        if res:
            return Theme(id=res.id, title=res.title)

    async def list_themes(self) -> List[Theme]:
        results = await ThemeModel.query.gino.all()
        themes = [Theme(id=el.id, title=el.title) for el in results]
        return themes

    async def create_answers(self, question_id, answers: List[Answer]) -> List[Answer]:
        result = []
        for answer in answers:
            res = await AnswerModel.create(title=answer.title, is_correct=answer.is_correct, question_id=question_id)
            result.append(Answer(title=res.title, is_correct=res.is_correct))
        return result

    async def create_question(
            self, title: str, theme_id: int, answers: List[Answer]
    ) -> Question:
        res = await QuestionModel.create(title=title, theme_id=theme_id)
        el_answers = await self.create_answers(res.id, answers)
        return Question(id=res.id, title=res.title, theme_id=res.theme_id, answers=el_answers)

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        res = await QuestionModel.query.where(QuestionModel.title == title).gino.first()
        if res:
            answer_models = await AnswerModel.query.where(AnswerModel.question_id == res.id).gino.all()
            answers = [Answer(title=el.title, is_correct=el.is_correct) for el in answer_models]
            return Question(id=res.id, title=res.title, theme_id=res.theme_id, answers=answers)

    async def get_question_by_id(self, _id: int) -> Optional[Question]:
        res = await QuestionModel.query.where(QuestionModel.id == _id).gino.first()
        if res:
            answer_models = await AnswerModel.query.where(AnswerModel.question_id == res.id).gino.all()
            answers = [Answer(title=el.title, is_correct=el.is_correct) for el in answer_models]
            return Question(id=res.id, title=res.title, theme_id=res.theme_id, answers=answers)

    async def list_questions(self, theme_id: Optional[int] = None) -> List[Question]:
        if theme_id:

            query = QuestionModel.outerjoin(AnswerModel, QuestionModel.id == AnswerModel.question_id).select()
            questions = await query.where(QuestionModel.theme_id == theme_id).gino.load(
                QuestionModel.distinct(QuestionModel.id).load(answers=AnswerModel.distinct(AnswerModel.id))
            ).all()
        else:
            query = QuestionModel.outerjoin(AnswerModel, QuestionModel.id == AnswerModel.question_id).select()
            questions = await query.gino.load(
                QuestionModel.distinct(QuestionModel.id).load(answers=AnswerModel.distinct(AnswerModel.id))).all()

        return [
            Question(
                id=el.id,
                title=el.title,
                theme_id=el.theme_id,
                answers=[Answer(title=el.title, is_correct=el.is_correct) for el in el.answers])
            for el in questions]


class GameAccessor(BaseAccessor):
    async def get_game_by_chat_id(self, chat_id: str, _all: bool = False) -> Optional[Game]:
        """
            Получаем игру из БД по chat_id
            по умолчанию вытаскиваем только не завершенные игры
        """
        query = GameModel.outerjoin(ScoreModel).outerjoin(UserModel).select()
        if _all:
            res_query = await query.where(GameModel.chat_id == chat_id).gino.load(
                GameModel.distinct(GameModel.id).load(add_user=UserModel.distinct(UserModel.id)).load(
                    add_score=ScoreModel.distinct(ScoreModel.id))).all()
        else:
            res_query = await query.where(GameModel.chat_id == chat_id).where(
                GameModel.status != StatusGame.FINISHED).gino.load(
                GameModel.distinct(GameModel.id).load(add_user=UserModel.distinct(UserModel.id)).load(
                    add_score=ScoreModel.distinct(ScoreModel.id))).all()

        if not res_query:
            return None

        res = res_query[0]
        questions = await self.app.store.quizzes.list_questions()
        scores = {el.user_id: el.count for el in res.scores}
        if res:
            return Game(id=res.id,
                        chat_id=res.chat_id,
                        status=res.status,
                        users=[User(
                            id=el.id,
                            vk_id=el.vk_id,
                            name=el.name,
                            is_admin=el.is_admin,
                            count_score=scores.get(el.id, 0),
                        ) for el in res.users],
                        questions=[
                            Question(
                                id=el.id,
                                title=el.title,
                                theme_id=el.theme_id,
                                answers=[Answer(title=el.title, is_correct=el.is_correct) for el in el.answers])
                            for el in questions],
                        current_question_id=res.current_question_id,
                        finish_question_ids=res.question_ids if res.question_ids else [])

    async def create_game(self, chat_id: str, users: list) -> Game:
        """ Создаем игру """
        res_game = await GameModel.create(chat_id=chat_id, status=StatusGame.STARTED)
        for user in users:
            await ScoreModel.create(game_id=res_game.id, user_id=user.id, count=0)
        return Game(
            id=res_game.id,
            chat_id=res_game.chat_id,
            status=res_game.status,
            users=users,
            finish_question_ids=[],
            current_question_id=res_game.current_question_id,
            questions=await self.app.store.quizzes.list_questions(),
        )

    async def set_current_question_for_game(self, question_id: int, game_id: int) -> None:
        """ Обновляем текущий вопрос для игры """
        await GameModel.update.values(current_question_id=question_id).where(GameModel.id == game_id).gino.status()

    async def set_status_for_game(self, status: int, game_id: int) -> None:
        """ Обновляем статус игры """
        await GameModel.update.values(status=status).where(GameModel.id == game_id).gino.status()

    async def add_finished_question_ids_for_game(self,
                                                 current_question_ids: list,
                                                 new_finished_question_id: int,
                                                 game_id: int) -> None:
        """ Обновляем массив пройденных вопросов в игре """
        current_question_ids.append(new_finished_question_id)
        await GameModel.update.values(question_ids=current_question_ids).where(GameModel.id == game_id).gino.status()

    async def update_score(self, user_id: int, game_id: int, count: int) -> Score:
        """ Записываем игроку очки за верный ответ """
        await ScoreModel.update.values(count=count). \
            where(ScoreModel.user_id == user_id).where(ScoreModel.game_id == game_id).gino.status()

    async def create_level_game(self, game: Game, user: User) -> Score:
        """
            Записываем импровизированный уровень игры
            в объект game добавляем пройденные вопросы
            и создаем объект Score c информацией по игроку
         """
        await self.add_finished_question_ids_for_game(
            game_id=game.id,
            current_question_ids=game.finish_question_ids,
            new_finished_question_id=game.current_question_id)
        return await self.update_score(user_id=user.id, game_id=game.id, count=user.count_score)

    async def get_count_score_by_game_and_user_id(self, game_id: int, user_id: int) -> Optional[int]:
        """ Получаем общее количество очков юзера (user_id) из игры (game_id)"""
        select = db.func.sum(ScoreModel.count)
        result = await db.select([select]).where(ScoreModel.game_id == game_id).where(
            ScoreModel.user_id == user_id).gino.scalar()
        return result

    async def get_user_score_by_game(self, game_id: int) -> List[UserScore]:
        """ Получаем общее количество очков юзера (user_id) из игры (game_id)"""
        query = UserModel.outerjoin(ScoreModel, UserModel.id == ScoreModel.user_id).select()
        query_res = await query.where(ScoreModel.game_id == game_id).gino.load(
            UserModel.distinct(UserModel.id).load(add_score=ScoreModel.distinct(ScoreModel.id))).all()
        return [UserScore(
            user_id=el.id,
            name=el.name,
            score_count=sum([x.count for x in el.scores])
        ) for el in query_res]
