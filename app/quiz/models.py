import enum
from dataclasses import dataclass
from typing import Optional

from app.store.database.gino import db
from sqlalchemy_utils.types.choice import ChoiceType

@dataclass
class Theme:
    id: Optional[int]
    title: str


class ThemeModel(db.Model):
    __tablename__ = "themes"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(120), unique=True)


@dataclass
class Question:
    id: Optional[int]
    title: str
    theme_id: int
    answers: list["Answer"]

    async def get_correct_answer(self) -> "Answer":
        answer = list(filter(lambda x: x.is_correct, self.answers))
        return answer[0] if len(answer) > 0 else None


class QuestionModel(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(120), unique=True)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._answers = list()

    @property
    def answers(self):
        return self._answers

    @answers.setter
    def answers(self, val):
        if val:
            self._answers.append(val)


class AnswerModel(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(120))
    is_correct = db.Column(db.Boolean())
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)


@dataclass
class Answer:
    title: str
    is_correct: bool


@dataclass
class Game:
    id: int
    chat_id: str
    status: int
    current_question_id: int
    users: list["User"]
    questions: list[Question]
    finish_question_ids: list

    async def get_user(self, vk_id: str) -> "User":
        print('self.users', self.users)
        user = list(filter(lambda x: x.vk_id == vk_id, self.users))
        return user[0] if len(user) > 0 else None

    async def get_current_question(self) -> Question:
        print('self.questions', self.questions)
        question = list(filter(lambda x: x.id == self.current_question_id, self.questions))
        print('question', question)
        return question[0] if len(question) > 0 else None

    async def get_question_for_chat(self) -> Question:
        question = list(filter(lambda x: x.id not in self.finish_question_ids, self.questions))
        return question[0] if len(question) > 0 else None


class StatusGame(enum.Enum):
    NO_STARTED = 1
    STARTED = 2
    FINISHED = 3


class GameModel(db.Model):
    __tablename__ = "game"

    id = db.Column(db.Integer(), primary_key=True)
    chat_id = db.Column(db.String(120))
    question_ids = db.Column(db.ARRAY(db.Integer))
    status = db.Column(ChoiceType(StatusGame, impl=db.Integer()))
    current_question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='SET NULL'), nullable=True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._users = set()
        self._scores = set()

    @property
    def users(self):
        return self._users

    @users.setter
    def add_user(self, user):
        print('add_user', user)
        self._users.add(user)
        user._games.add(self)

    @property
    def scores(self):
        return self._scores

    @scores.setter
    def add_score(self, score):
        self._scores.add(score)


@dataclass
class User:
    id: int
    vk_id: str
    name: str
    is_admin: bool
    count_score: int


class UserModel(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer(), primary_key=True)
    vk_id = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    dt_created = db.Column(db.DateTime, server_default='now()')

    def __init__(self, **kw):
        super().__init__(**kw)
        self._games = set()
        self._scores = set()

    @property
    def games(self):
        return self._games

    @games.setter
    def add_game(self, game):
        self._games.add(game)
        game._users.add(self)

    @property
    def scores(self):
        return self._scores

    @scores.setter
    def add_score(self, score):
        self._scores.add(score)


@dataclass
class UserScore:
    user_id: int
    score_count: int
    name: str


@dataclass
class Score:
    id: int
    count: int
    user_id: int
    game_id: int


class ScoreModel(db.Model):
    __tablename__ = "score"

    id = db.Column(db.Integer(), primary_key=True)
    count = db.Column(db.Integer(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id'),
    )
