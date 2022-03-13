from app.quiz.models import Game, GameModel, User, \
    Winner, UserScore, UserModel
from app.store import Store
from tests.utils import check_empty_table_exists
from tests.utils import ok_response


class TestGamesStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "game")

    async def test_create_game(
            self, cli, store: Store
    ):
        chat_id = 1
        game = await store.game.create_game(
            chat_id=chat_id, users=[]
        )
        assert type(game) is Game

        games = await GameModel.query.gino.all()
        assert len(games) == 1
        assert game.chat_id == chat_id and game.id == 1

    async def test_get_game_by_chat_id(self, cli, store: Store, game_1: Game):
        assert game_1 == await store.game.get_game_by_chat_id(game_1.chat_id)

    async def test_list_games(self, cli, store: Store, game_3: Game):
        games = await store.game.list_finish_games()
        assert games == [game_3]

    async def test_list_winners(self, cli, store: Store, game_3: Game, user_1: User):
        winners = await store.game.list_winners()
        winner = Winner(vk_id=user_1.vk_id, win_count=1, first_name=user_1.first_name, last_name=user_1.last_name)
        assert winners == [winner]

    async def test_get_user_score_by_game(self, cli, store: Store, game_3: Game, user_1: User):
        scores = await store.game.get_user_score_by_game(game_3.id)
        score = UserScore(user_id=user_1.id, points=0, first_name=user_1.first_name, last_name=user_1.last_name)
        assert scores == [score]


class TestUsersStore:

    async def test_create_user(
            self, cli, store: Store
    ):
        vk_id = 111
        user = await store.users.create_user(
            vk_id=111, first_name='Михаил', last_name='Шишкин'
        )
        assert type(user) is User

        users = await UserModel.query.gino.all()
        assert len(users) == 1
        assert user.vk_id == vk_id and user.id == 1

    async def test_get_user_by_vk_id(self, cli, store: Store, user_1: User):
        assert user_1 == await store.users.get_user_by_vk_id(user_1.vk_id)


class TestGameListView:
    async def test_empty(self, cli):
        resp = await cli.get("/admin.fetch_games")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data={'games': [], 'total': 0})

    async def test_one_game(self, cli, game_4: Game, user_2: User):
        resp = await cli.get("/admin.fetch_games")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data={
                'total': 1,
                'games': [
                    {
                        'started_at': game_4.started_at.isoformat(),
                        'finished_at': game_4.finished_at.isoformat(),
                        'id': game_4.id,
                        'duration': int((game_4.finished_at - game_4.started_at).total_seconds()),
                        'chat_id': game_4.chat_id,
                        'winner': {
                            'vk_id': user_2.vk_id,
                            'points': user_2.points,
                        }
                    }
                ]
            }
        )

    async def test_several_games(self, cli, game_4: Game, game_5: Game, user_2: User):
        resp = await cli.get("/admin.fetch_games")
        assert resp.status == 200
        data = await resp.json()
        games = []
        for game in [game_4, game_5]:
            games.append({
                'started_at': game.started_at.isoformat(),
                'finished_at': game.finished_at.isoformat(),
                'id': game.id,
                'duration': int((game.finished_at - game.started_at).total_seconds()),
                'chat_id': game.chat_id,
                'winner': {
                    'vk_id': user_2.vk_id,
                    'points': user_2.points,
                }
            })
        assert data == ok_response(
            data={
                'total': 2,
                'games': games,
            }
        )


class TestFetchGameListView:
    async def test_emptympty(self, cli):
        resp = await cli.get("/admin.fetch_game_stats")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data={
            'winners_top': [],
            'games_total': 0,
            'duration_total': None,
            'duration_average': None,
            'games_average_per_day': 0
        })

    async def test_one_fetch_game(self, cli, game_4: Game, user_2: User):
        games = [game_4]
        resp = await cli.get("/admin.fetch_game_stats")
        assert resp.status == 200
        data = await resp.json()
        duration_total = None
        for el in games:
            if duration_total is None:
                duration_total = el.finished_at - el.started_at
            else:
                duration_total += el.finished_at - el.started_at
        duration_average = duration_total / len(games)
        assert data == ok_response(
            data={
                'winners_top': [
                    {
                        'last_name': user_2.last_name,
                        'first_name': user_2.first_name,
                        'vk_id': user_2.vk_id,
                        'win_count': len(games),
                    }
                ],
                'games_average_per_day': len(games),
                'duration_total': int(duration_total.total_seconds()),
                'duration_average': int(duration_average.total_seconds()),
                'games_total': len(games),
            }
        )

    async def test_several_fetch_games(self, cli, game_4: Game, game_5: Game, user_2: User):
        resp = await cli.get("/admin.fetch_game_stats")
        assert resp.status == 200
        data = await resp.json()
        games = [game_4, game_5]
        duration_total = None
        for el in games:
            if duration_total is None:
                duration_total = el.finished_at - el.started_at
            else:
                duration_total += el.finished_at - el.started_at
        duration_average = duration_total / len(games)
        assert data == ok_response(
            data={
                'winners_top': [
                    {
                        'last_name': user_2.last_name,
                        'first_name': user_2.first_name,
                        'vk_id': user_2.vk_id,
                        'win_count': len(games),
                    }
                ],
                'games_average_per_day': len(games),
                'duration_total': int(duration_total.total_seconds()),
                'duration_average': int(duration_average.total_seconds()),
                'games_total': len(games),
            }
        )
