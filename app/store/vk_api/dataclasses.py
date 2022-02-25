from dataclasses import dataclass


@dataclass
class UpdateObject:
    id: int
    user_id: int
    body: str
    type_chat: str


@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass
class Message:
    user_id: int
    text: str

@dataclass
class Winner:
    vk_id: int
    points: int

@dataclass
class Game:
    id: int
    chat_id: int
    started_at: str
    finished_at: str
    winner: Winner

