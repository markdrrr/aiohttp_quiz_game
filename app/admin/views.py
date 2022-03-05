from aiohttp_apispec import request_schema, response_schema, querystring_schema
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema, ListGameSchema, ListGameStatsSchema, ListGamePageSchema, \
    ListGameStatsPageSchema
from app.quiz.models import StatusGame
from app.web.app import View
from aiohttp.web import HTTPForbidden, HTTPUnauthorized

from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        email, password = self.data["email"], self.data["password"]
        admin = await self.store.admins.get_by_email(email)
        if not admin or not admin.is_password_valid(password):
            raise HTTPForbidden
        admin_data = AdminSchema().dump(admin)
        response = json_response(data=admin_data)
        session = await new_session(request=self.request)
        session["admin"] = admin_data
        return response


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        if self.request.admin:
            return json_response(data=AdminSchema().dump(self.request.admin))
        raise HTTPUnauthorized


class FetchGamesView(View):
    @querystring_schema(ListGamePageSchema)
    @response_schema(ListGameSchema)
    async def get(self):
        page = self.data.get("page", 0)
        limit = 5
        offset = 5 * page
        games_db = await self.store.game.list_games(status=StatusGame.FINISHED, limit=limit, offset=offset)
        games = []
        for game in games_db:
            winners = sorted(game.users, key=lambda x: x.points, reverse=True) if game.users else None
            winner = {
                    "vk_id": winners[0].vk_id,
                    "points": winners[0].points,
                }
            games.append({
                "id": game.id,
                "chat_id": game.chat_id,
                "started_at": game.started_at,
                "duration": (game.finished_at - game.started_at).seconds,
                "winner": winner,
                "finished_at": game.finished_at,
            })
        total = await self.store.game.count_games(status=StatusGame.FINISHED)
        return json_response(
            data=ListGameSchema().dump(
                {
                    "total": total,
                    "games": games,
                }
            )
        )


class FetchGameStatsView(View):
    @querystring_schema(ListGameStatsPageSchema)
    @response_schema(ListGameStatsSchema)
    async def get(self):
        page = self.data.get("page", 0)
        limit = 5
        offset = 5 * page
        winners = await self.store.game.list_winners(limit=limit, offset=offset)
        winners_top = [el.to_dict() for el in winners]
        total = await self.store.game.count_games(status=StatusGame.FINISHED)
        duration_total = await self.store.game.duration_total()
        duration_average = await self.store.game.duration_average()
        games_average_per_day = await self.store.game.games_average_per_day()
        return json_response(
            data=ListGameStatsSchema().dump(
                {
                    "winners_top": winners_top,
                    "games_total": total,
                    "duration_total": duration_total.total_seconds(),
                    "duration_average": duration_average.total_seconds(),
                    "games_average_per_day": games_average_per_day,
                }
            )
        )