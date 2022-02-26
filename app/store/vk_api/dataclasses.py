from dataclasses import dataclass


@dataclass
class UpdateObject:
    id: int
    user_id: int
    peer_id: int
    body: str
    type_chat: str


class UpdateStatus:
    INVITE_CHAT = 'chat_invite_user'
    START_GAME = 'start_game'
    FINISH_GAME = 'finish_game'
    RESULT_GAME = 'result_game'

@dataclass
class Update:
    type: str
    action: str
    object: UpdateObject


@dataclass
class Message:
    peer_id: int
    text: str

# @dataclass
# class Winner:
#     vk_id: int
#     points: int
#
# @dataclass
# class Game:
#     id: int
#     chat_id: int
#     started_at: str
#     finished_at: str
#     winner: Winner

