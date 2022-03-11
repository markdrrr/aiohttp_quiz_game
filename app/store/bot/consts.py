class BotMessage:
    WRONG_ANSWER = 'Неверный ответ %0A'
    CORRECT_ANSWER = 'Правильный ответ! %0A'
    IS_NOT_ADMIN = 'Назначьте бота администратором %0A'
    HAVE_NOT_QUESTIONS = 'В боте отсутствуют вопросы %0A'
    ALREADY_STARTED = 'Игра уже началась %0A'
    ALREADY_FINISHED = 'Игра уже завершена %0A'
    FINISHED = 'Игра завершена %0A'
    START_GAME_TEXT = 'Игра началась. Первый вопрос: {question_title} %0A'
    INVITE_TEXT = "Вы пригласили бота 'Своя игра' %0A" \
                  "Сделайте бота админом и воспользуетесь кнопками ниже что бы начать играть %0A" \
                  "Кто первый отвечает тому начисляется 100 очков %0A" \
                  "В конце подводится результат %0A"
    RESULT_GAME = 'Результаты текущей игры № {game_id} %0A'
    NO_RESULT_GAME = 'Нет текущей игры %0A'
    NO_ANSWER_FOR_TIME = 'Время на ответ вышло %0A'
