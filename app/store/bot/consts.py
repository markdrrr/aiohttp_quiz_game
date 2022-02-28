from string import Template


class BotMessage:
    WRONG_ANSWER = 'Неверный ответ'
    already_started = 'Неверный ответ'
    ALREADY_STARTED = 'Игра уже началась'
    ALREADY_FINISHED = 'Игра уже завершена'
    FINISHED = 'Игра завершена'
    START_GAME_TEXT = Template('Игра началась. Первый вопрос: $question_title')
    INVITE_TEXT = "Вы пригласили бота 'Своя игра' \n" \
                  " Сделайте бота админом и воспользуетесь кнопками ниже что бы начать играть"
    RESULT_GAME = Template('Результаты текущей игры № $game_id')
    NO_RESULT_GAME = 'Нет текущей игры'
