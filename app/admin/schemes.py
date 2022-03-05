from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(required=False)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class WinnerSchema(Schema):
    vk_id = fields.Int()
    points = fields.Int()


class GameSchema(Schema):
    id = fields.Int()
    chat_id = fields.Str()
    started_at = fields.Date()
    duration = fields.Int()
    winner = fields.Nested("WinnerSchema", required=True)
    finished_at = fields.Date()


class ListGameSchema(Schema):
    total = fields.Int()
    games = fields.Nested(GameSchema, many=True)


class WinnersSchema(Schema):
    vk_id = fields.Int()
    win_count = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()


class ListGameStatsSchema(Schema):
    games_average_per_day = fields.Int()
    winners_top = fields.Nested(WinnersSchema, many=True)
    duration_total = fields.Int()
    games_total = fields.Int()
    duration_average = fields.Int()


class ListGamePageSchema(Schema):
    page = fields.Int()


class ListGameStatsPageSchema(Schema):
    page = fields.Int()
