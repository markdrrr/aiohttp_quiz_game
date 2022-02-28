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
            return User(id=res.id, vk_id=res.vk_id, name=res.name, is_admin=res.is_admin)

    async def create_user(self, vk_id: str, name: str, is_admin: bool) -> User:
        """ Создаем либо вытаскиваем юзера из бд """
        stmt = insert(UserModel).values(vk_id=vk_id, name=name, is_admin=is_admin)
        stmt = stmt.on_conflict_do_update(
            index_elements=[UserModel.vk_id], set_=dict(name=stmt.excluded.name, is_admin=stmt.excluded.is_admin)
        ).returning(*UserModel)
        res = await stmt.gino.model(UserModel).first()
        return User(id=res.id, vk_id=res.vk_id, name=res.name, is_admin=res.is_admin, count_score=0)

    async def get_users(self, users: List[User]) -> List[User]:
        """ Создаем либо вытаскиваем из спиоск юзеров БД """
        result = []
        for user in users:
            created_user = await self.create_user(vk_id=user.vk_id, name=user.name, is_admin=user.is_admin)
            result.append(created_user)
        return result
