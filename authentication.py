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
        user = await User.get(id=payload.get('id'))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found',
                headers={
                    'WWW-Authenticate': 'Bearer'
                }
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired',
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
