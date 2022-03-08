from typing import List
from typing import Optional

from sqlalchemy.dialects.postgresql import insert

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    User, UserModel, )


class UserAccessor(BaseAccessor):
    async def get_user_by_vk_id(self, vk_id: str) -> Optional[User]:
        """ Достаем юзера из БД по vk_id """
        res = await UserModel.query.where(UserModel.vk_id == vk_id).gino.first()
        if res:
            return User(
                id=res.id,
                vk_id=res.vk_id,
                first_name=res.first_name,
                last_name=res.last_name,
                points=0,
            )

    async def create_user(self, vk_id: int, first_name: str, last_name: str) -> User:
        """ Создаем либо вытаскиваем юзера из бд """
        stmt = insert(UserModel).values(
            vk_id=vk_id,
            first_name=first_name,
            last_name=last_name
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[UserModel.vk_id], set_=dict(first_name=stmt.excluded.first_name, last_name=stmt.excluded.last_name)
        ).returning(*UserModel)
        res = await stmt.gino.model(UserModel).first()
        return User(
            id=res.id,
            vk_id=res.vk_id,
            first_name=res.first_name,
            last_name=res.last_name,
            points=0,
        )

    async def get_users(self, users: List[User]) -> List[User]:
        """ Создаем либо вытаскиваем из спиоск юзеров БД """
        result = []
        for user in users:
            created_user = await self.create_user(
                vk_id=user.vk_id,
                first_name=user.first_name,
                last_name=user.last_name
            )
            result.append(created_user)
        return result
