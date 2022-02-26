from typing import List
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Theme,
    Question,
    Answer,
    ThemeModel,
    QuestionModel,
    AnswerModel, User, UserModel, GameModel, StatusGame, Game, GameUserModel, Score, ScoreModel, UserScore,
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

    async def get_correct_answer(self, question_id: int) -> Optional[Answer]:
        """ Получаем верный ответ от вопроса по question_id """
        question = await self.get_question_by_id(_id=question_id)
        print('question', question)
        correct_answers = [answer for answer in question.answers if answer.is_correct]
        if len(correct_answers) > 0:
            return correct_answers[0]

    async def list_questions(self, theme_id: Optional[int] = None) -> List[Question]:
        if theme_id:
            res = await (
                QuestionModel.outerjoin(AnswerModel, QuestionModel.id == AnswerModel.question_id)
                    .select()
                    .where(QuestionModel.theme_id == theme_id)
                    .gino
                    .load(QuestionModel.load(answers=AnswerModel))
                    .all()
            )
        else:
            res = await (
                QuestionModel.outerjoin(AnswerModel, QuestionModel.id == AnswerModel.question_id)
                    .select()
                    .gino
                    .load(QuestionModel.load(answers=AnswerModel))
                    .all()
            )

        result = []
        for question in res:
            uniq = True
            answer = question.answers[0]
            for el in result:
                if question.id == el.id:
                    uniq = False
                    el.answers.append(Answer(answer.title, answer.is_correct))

            if uniq:
                result.append(
                    Question(question.id, question.title, question.theme_id, [Answer(answer.title, answer.is_correct)]))
        return result

    async def get_user_by_vk_id(self, vk_id: str) -> Optional[User]:
        """ Достаем юзера из БД по vk_id """
        res = await UserModel.query.where(UserModel.vk_id == vk_id).gino.first()
        if res:
            return User(id=res.id, vk_id=res.vk_id, name=res.name, is_admin=res.is_admin)

    async def create_user(self, vk_id: str, name: str, is_admin: bool) -> User:
        """ Создаем либо вытаскиваем юзера из бд """
        user = await self.get_user_by_vk_id(vk_id)
        # print('user', user)
        if user:
            return user
        res = await UserModel.create(vk_id=vk_id, name=name, is_admin=is_admin)
        return User(id=res.id, vk_id=res.vk_id, name=res.name, is_admin=res.is_admin)

    async def get_or_create_users(self, users: List[User]) -> List[User]:
        """ Создаем либо вытаскиваем из спиоск юзеров БД """
        result = []
        for user in users:
            created_user = await self.create_user(vk_id=user.vk_id, name=user.name, is_admin=user.is_admin)
            result.append(created_user)
        return result

    async def get_game_by_chat_id(self, chat_id: str, _all: bool = False) -> Optional[Game]:
        """
            Получаем игру из БД по chat_id
            по умолчанию вытаскиваем только не завершенные игры
        """
        query = GameModel.outerjoin(GameUserModel).outerjoin(UserModel).select()
        if _all:
            res = await query.where(GameModel.chat_id == chat_id).gino.load(
                GameModel.distinct(GameModel.id).load(add_user=UserModel.distinct(UserModel.id))).first()
        else:
            res = await query.where(GameModel.chat_id == chat_id).where(GameModel.status != StatusGame.FINISHED). \
                gino.load(GameModel.distinct(GameModel.id).load(add_user=UserModel.distinct(UserModel.id))).first()
        if res:
            return Game(id=res.id,
                        chat_id=res.chat_id,
                        status=res.status,
                        user_ids=[x.id for x in res.users],
                        question_ids=res.question_ids if res.question_ids else [],
                        current_question_id=res.current_question_id)

    async def get_or_create_game(self, chat_id: str, users: list) -> Game:
        """ Создаем или вытаскиваем не "завершенную" игру из бд """
        game = await self.get_game_by_chat_id(chat_id)
        if game:
            return game
        res_game = await GameModel.create(chat_id=chat_id, status=StatusGame.STARTED)
        user_ids = []
        for user in users:
            await GameUserModel.create(game_id=res_game.id, user_id=user.id)
            user_ids.append(user.id)
        return Game(id=res_game.id, chat_id=res_game.chat_id, status=res_game.status, user_ids=user_ids,
                    question_ids=[], current_question_id=res_game.current_question_id)

    async def get_question_for_chat(self, chat_id: str) -> Optional[Question]:
        """ Достаем вопрос который еще не был в игре """
        questions = await self.list_questions(theme_id=1)
        game = await self.get_game_by_chat_id(chat_id)
        finish_questions = game.question_ids
        # отфильтровываем вопросы которые уже были в игре
        res_questions = list(filter(lambda x: x.id not in finish_questions, questions))
        return res_questions[0] if len(res_questions) > 0 else None

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

    async def get_status_game_from_chat(self, chat_id: str):
        game = await self.get_game_by_chat_id(chat_id)
        if game is not None:
            return game.status
        return StatusGame.NO_STARTED

    async def create_score(self, user_id: int, game_id: int, count: int = 100) -> Score:
        """ Записываем игроку очки за верный ответ """
        res = await ScoreModel.create(user_id=user_id, game_id=game_id, count=count)
        return Score(id=res.id, user_id=res.user_id, game_id=res.game_id, count=res.count)

    async def create_level_game(self, game: Game, user: User) -> Score:
        """
            Записываем импровизированный уровень игры
            в объект game добавляем пройденные вопросы
            и создаем объект Score c информацией по игроку
         """
        await self.add_finished_question_ids_for_game(
            game_id=game.id,
            current_question_ids=game.question_ids,
            new_finished_question_id=game.current_question_id)
        return await self.create_score(user_id=user.id, game_id=game.id)

    async def get_scores_by_game_id(self, game_id: int) -> List[Score]:
        """ Получаем список объектов score из БД по game_id """
        scores_models = await ScoreModel.query.where(ScoreModel.game_id == game_id).gino.all()
        return [Score(id=el.id, count=el.count, user_id=el.user_id, game_id=el.game_id) for el in scores_models]

    async def get_count_score_by_game_and_user_id(self, game_id: int, user_id: int) -> Optional[int]:
        """ Получаем общее количество очков юзера (user_id) из игры (game_id)"""
        select = db.func.sum(ScoreModel.count)
        result = await db.select([select]).where(ScoreModel.game_id == game_id).where(
            ScoreModel.user_id == user_id).gino.scalar()
        return result

    async def get_user_score_by_game(self, game_id: int) -> List[UserScore]:
        """ Получаем общее количество очков юзера (user_id) из игры (game_id)"""
        # count_sum = db.func.sum(ScoreModel.count)
        # result = await ScoreModel.join(UserModel, ScoreModel.user_id == UserModel.id).
        # select([ScoreModel.user_id, UserModel.name, count_sum]).where(ScoreModel.game_id == game_id).
        # where(ScoreModel.user_id == user_id).gino.scalar()

        query = UserModel.outerjoin(ScoreModel, UserModel.id == ScoreModel.user_id).select()
        query_res = await query.where(ScoreModel.game_id == game_id).gino.load(
            UserModel.distinct(UserModel.id).load(add_score=ScoreModel.distinct(ScoreModel.id))).all()

        return [UserScore(
            user_id=el.id,
            name=el.name,
            score_count=sum([x.count for x in el.scores])
        ) for el in query_res]
