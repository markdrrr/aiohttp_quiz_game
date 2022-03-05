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
    user_ids: list
    question_ids: list
    current_question_id: int


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
        self._users.add(user)
        user._games.add(self)

    @property
    def scores(self):
        return self._scores

    @scores.setter
    def add_score(self, score):
        self._games.add(score)


@dataclass
class UserAnswer:
    user_id: str
    chat_id: str
    answer: str
    is_correct: bool

@dataclass
class User:
    id: int
    vk_id: str
    name: str
    is_admin: bool


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
