from typing import List

import pytest

from app.quiz.models import Theme, Question, Answer, User, Game, StatusGame


@pytest.fixture
def answers(store) -> List[Answer]:
    return [
        Answer(title="1", is_correct=True),
        Answer(title="2", is_correct=False),
        Answer(title="3", is_correct=False),
        Answer(title="4", is_correct=False),
    ]


@pytest.fixture
async def user_1(store) -> User:
    user = await store.users.create_user(vk_id=1111, first_name='Иван', last_name='Иванов')
    yield user


@pytest.fixture
async def user_2(store) -> User:
    user = await store.users.create_user(vk_id=2222, first_name='Петр', last_name='Петров')
    yield user


@pytest.fixture
async def game_1(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=1, users=[user_1, user_2])
    yield game


@pytest.fixture
async def game_2(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=1, users=[user_1, user_2])
    yield game


@pytest.fixture
async def game_3(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=2, users=[user_1])
    game = await store.game.set_status_for_game(
        status=StatusGame.FINISHED,
        game=game,
        winner_user_id=user_1.id
    )
    yield game


@pytest.fixture
async def game_4(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=3, users=[user_1, user_2])
    user_2.points = 100
    await store.game.create_level_game(game=game, user=user_2)
    game = await store.game.set_status_for_game(
        status=StatusGame.FINISHED,
        game=game,
        winner_user_id=user_2.id
    )
    yield game


@pytest.fixture
async def game_5(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=4, users=[user_1, user_2])
    user_2.points = 100
    await store.game.create_level_game(game=game, user=user_2)
    game = await store.game.set_status_for_game(
        status=StatusGame.FINISHED,
        game=game,
        winner_user_id=user_2.id
    )
    yield game


@pytest.fixture
async def game_score(store, user_1, user_2) -> Game:
    game = await store.game.create_game(chat_id=1, users=[user_1, user_2])
    yield game


@pytest.fixture
async def theme_1(store) -> Theme:
    theme = await store.quizzes.create_theme(title="web-development")
    yield theme


@pytest.fixture
async def theme_2(store) -> Theme:
    theme = await store.quizzes.create_theme(title="backend")
    yield theme


@pytest.fixture
async def question_1(store, theme_1) -> Question:
    question = await store.quizzes.create_question(
        title="how are you?",
        theme_id=theme_1.id,
        answers=[
            Answer(
                title="well",
                is_correct=True,
            ),
            Answer(
                title="bad",
                is_correct=False,
            ),
        ],
    )
    yield question


@pytest.fixture
async def question_2(store, theme_1) -> Question:
    question = await store.quizzes.create_question(
        title="are you doing fine?",
        theme_id=theme_1.id,
        answers=[
            Answer(
                title="yep",
                is_correct=True,
            ),
            Answer(
                title="nop",
                is_correct=False,
            ),
        ],
    )
    yield question
