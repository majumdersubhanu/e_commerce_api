import jwt
from fastapi import FastAPI, Request, status, Depends, Form
from tortoise.contrib.fastapi import register_tortoise

from emails import send_email
from models import *
# from starlette.responses import HTMLResponse
from authentication import *
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_schema = OAuth2PasswordBearer(tokenUrl='token')


@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    auth_token = await token_generator(request_form.username, request_form.password)
    return {'access_token': auth_token, 'token_type': 'Bearer'}


async def get_current_user(auth_token: str = Depends(oauth2_schema)):
    try:
        payload = jwt.decode(auth_token, config_credentials['SECRET'], algorithms=['HS256'])
        user = await User.get(id=payload['id'])
        return await user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired',
                            headers={'WWW-Authenticate': 'Bearer'})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token',
                            headers={'WWW-Authenticate': 'Bearer'})


@app.post('/user/me')
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    business = await Business.get(owner=user)
    return {
        'status': 'OK',
        'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_verified': user.is_verified,
            'joined_date': user.join_date.strftime('%b %d %Y'),
            'business': {
                'id': business.id,
                'name': business.name,
                'logo': config_credentials['BASE_URL'] + '/static/images/' + business.logo,
            }
        },
    }


@post_save(User)
async def create_business(
        sender: '',
        instance: User,
        created: bool,
        using_db: 'Optional[BaseDBAsyncClient]',
        update_fields: List[str],
) -> None:
    if created:
        business_obj = await Business.create(
            name=f'Business by {instance.username}',
            owner=instance,
        )
        await business_pydantic.from_tortoise_orm(business_obj)
        # send email
        await send_email([instance.email], instance)


register_tortoise(
    app,
    db_url='postgres://postgres:postgres@localhost:5432/ecommerce',
    modules={
        'models': ['models']
    },
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get('/')
async def landing_page():
    return {'message': 'Hello World'}


@app.post('/registration')
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info['password'] = generate_hashed_password(user_info['password'])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return {
        'status': 'ok',
        'user': f'Hello {new_user.username}, welcome to the Bee store. Please click on the link sent to your registered '
                f'email address to verify your account and continuing shopping.',
    }


templates = Jinja2Templates(directory='templates')


@app.post('/upload/image/profile')
async def upload_image(file: UploadFile = File(...), user: user_pydanticIn = Depends(get_current_user)):
    FILEPATH = './static/images/'
    filename = file.filename
    extension = filename.split('.')[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        return {'status': 'error', 'message': 'Image must be JPG, JPEG, or PNG'}

    token_name = secrets.token_hex(10) + '.' + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    # Open the file in write mode and save the content
    with open(generated_name, 'wb') as f:
        f.write(file_content)

    image = Image.open(generated_name)
    image = image.resize((200, 200))
    image.save(generated_name)

    business = await Business.get(owner=user)
    owner = await business.owner

    if owner == user:
        business.logo = token_name
        await business.save()
        return {'status': 'success', 'file_url': config_credentials['BASE_URL'] + generated_name[1:]}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to upload an image',
            headers={'WWW-Authenticate': 'Bearer'}
        )


@app.get('/verification', response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    try:
        user = await verify_token(token)
        if user and not user.is_verified:
            user.is_verified = True
            await user.save()
            return templates.TemplateResponse('verification.html', {'request': request, 'username': user.username})
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail),
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
    return {'message': 'Email verification error'}


@app.post('/upload/image/product/{product_id}')
async def upload_product_image(product_id: int, file: UploadFile = File(...),
                               user: user_pydanticIn = Depends(get_current_user)):
    FILEPATH = './static/images/products/'
    filename = file.filename
    extension = filename.split('.')[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        return {'status': 'error', 'message': 'Image must be JPG, JPEG, or PNG'}

    token_name = secrets.token_hex(10) + '.' + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    # Open the file in write mode and save the content
    with open(generated_name, 'wb') as f:
        f.write(file_content)

    image = Image.open(generated_name)
    image = image.resize((800, 800))  # Adjust size as per your requirements
    image.save(generated_name)

    product = await Product.get(id=product_id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        product_image = await ProductImage.create(image=token_name)
        await product.product_images.add(product_image)
        return {'status': 'success', 'filename': token_name}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to upload an image',
            headers={'WWW-Authenticate': 'Bearer'}
        )