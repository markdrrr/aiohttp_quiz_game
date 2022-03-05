import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.bot.manager import BotManager
        from app.store.admin.accessor import AdminAccessor
        from app.store.quiz.accessor import QuizAccessor
        from app.store.quiz.accessor import GameAccessor
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.bot.accessor import UserAccessor
        from app.store.bot.game_logic import GameLogic

        self.quizzes = QuizAccessor(app)
        self.users = UserAccessor(app)
        self.game = GameAccessor(app)
        self.admins = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.game_logic = GameLogic(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)

    app.store = Store(app)
