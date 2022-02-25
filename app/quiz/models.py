from dataclasses import dataclass
from typing import Optional

from app.store.database.gino import db


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
