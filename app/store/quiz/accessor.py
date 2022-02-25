from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Theme,
    Question,
    Answer,
    ThemeModel,
    QuestionModel,
    AnswerModel,
)
from typing import List


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
                result.append(Question(question.id, question.title, question.theme_id, [Answer(answer.title, answer.is_correct)]))
        return result
