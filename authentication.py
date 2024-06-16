import jwt
from fastapi.exceptions import HTTPException
from passlib.context import CryptContext
from dotenv import dotenv_values
from fastapi import status

from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

config_credentials = dotenv_values('.env')


def generate_hashed_password(password):
    return pwd_context.hash(password)


async def verify_token(token: str):
    try:
        payload = jwt.decode(token, config_credentials['SECRET'], algorithms=['HS256'])
        user = await User.get(payload.get('id'))

    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )

    return user
