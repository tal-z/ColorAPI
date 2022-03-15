from tortoise import fields
from tortoise.models import Model
from passlib.hash import bcrypt
from tortoise.contrib.pydantic import pydantic_model_creator

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)

    @classmethod
    async def get_user(cls, username):
        return cls.get(username=username)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)


User_Pydantic = pydantic_model_creator(User, name='User')
UserIn_Pydantic = pydantic_model_creator(User, name='UserIn', exclude_readonly=True)


class Color(Model):
    #user = fields.ForeignKeyField()
    name = fields.CharField(50)
    url = fields.CharField(1000)
    num_colors = fields.IntField()
    dominant_colors = fields.CharField(1000)
    avg_inertia = fields.FloatField()
