import typing

from app.admin.views import AdminCurrentView, FetchGamesView, FetchGameStatsView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.admin.views import AdminLoginView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.fetch_games", FetchGamesView)
    app.router.add_view("/admin.fetch_game_stats", FetchGameStatsView)
