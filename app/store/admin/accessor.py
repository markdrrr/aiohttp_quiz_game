import typing
from hashlib import sha256
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.admin.models import Admin, AdminModel

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        await super().connect(app)
        await self.create_admin(
            email=app.config.admin.email, password=app.config.admin.password
        )

    async def get_by_email(self, email: str) -> Optional[Admin]:
        res = await AdminModel.query.where(AdminModel.email == email).gino.first()
        if res:
            return Admin(id=res.id, email=res.email, password=res.password)

    async def create_admin(self, email: str, password: str) -> Admin:
        admin = await self.get_by_email(email)
        if admin:
            return admin
        res = await AdminModel.create(
            email=email,
            password=sha256(password.encode()).hexdigest()
        )
        admin = Admin(id=res.id, email=res.email, password=res.password)
        return admin
