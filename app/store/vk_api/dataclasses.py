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

    KEYBOARD_ACTION = [START_GAME, FINISH_GAME, RESULT_GAME]


@dataclass
class Update:
    type: str
    action: str
    object: UpdateObject


@dataclass
class Message:
    peer_id: int
    text: str
