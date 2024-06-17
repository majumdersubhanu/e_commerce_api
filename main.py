import jwt
from fastapi import FastAPI, Request, status, Depends, Form
from tortoise.contrib.fastapi import register_tortoise
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from emails import send_email
from models import *
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
templates = Jinja2Templates(directory='templates')


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
        await send_email([instance.email], instance)


register_tortoise(
    app,
    db_url='postgres://postgres:postgres@localhost:5432/ecommerce',
    modules={'models': ['models']},
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


@app.post('/upload/image/profile')
async def upload_profile_image(file: UploadFile = File(...), user: user_pydanticIn = Depends(get_current_user)):
    FILEPATH = './static/images/'
    filename = file.filename
    extension = filename.split('.')[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        return {'status': 'error', 'message': 'Image must be JPG, JPEG, or PNG'}

    token_name = secrets.token_hex(10) + '.' + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

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
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return {'message': 'Email verification error'}


@app.post('/upload/image/product/{product_id}')
async def upload_product_image(product_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user)):
    FILEPATH = './static/images/'
    filename = file.filename
    extension = filename.split('.')[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        return {'status': 'error', 'message': 'Image must be JPG, JPEG, or PNG'}

    token_name = secrets.token_hex(10) + '.' + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, 'wb') as f:
        f.write(file_content)

    image = Image.open(generated_name)
    image = image.resize((800, 800))
    image.save(generated_name)

    product = await Product.get(id=product_id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        product_image = await ProductImage.create(image=token_name)
        await product.product_images.add(product_image)
        await product.save()
        return {'status': 'success', 'file_url': config_credentials['BASE_URL'] + generated_name[1:]}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to upload an image',
            headers={'WWW-Authenticate': 'Bearer'}
        )


@app.post('/upload/image/product/featured/{product_id}')
async def upload_featured_image(product_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user)):
    FILEPATH = './static/images/'
    filename = file.filename
    extension = filename.split('.')[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        return {'status': 'error', 'message': 'Image must be JPG, JPEG, or PNG'}

    token_name = secrets.token_hex(10) + '.' + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, 'wb') as f:
        f.write(file_content)

    image = Image.open(generated_name)
    image = image.resize((800, 800))
    image.save(generated_name)

    product = await Product.get(id=product_id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        product_image = await ProductImage.create(image=token_name)
        product.featured_image = product_image
        await product.save()
        return {'status': 'success', 'file_url': config_credentials['BASE_URL'] + generated_name[1:]}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to upload an image',
            headers={'WWW-Authenticate': 'Bearer'}
        )


@app.post('/products/create')
async def create_product(product: product_pydanticIn, user: user_pydanticIn = Depends(get_current_user)):
    product = product.dict(exclude_unset=True)

    if product['original_price'] > 0:
        product['percentage_discount'] = (product['original_price'] - product['current_price']) / product[
            'original_price'] * 100

        product_obj = await Product.create(**product, business=user)
        product_obj = await product_pydanticIn.from_tortoise_orm(product_obj)

        return {
            'status': 'success',
            'data': product_obj,
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to upload a product',
            headers={'WWW-Authenticate': 'Bearer'}
        )


@app.get('/products')
async def get_products():
    response = await Product.all()
    return {
        'status': 'ok',
        'data': response,
    }


@app.get('/products/{product_id}')
async def get_product(product_id: int):
    response = await Product.get(id=product_id)
    return {
        'status': 'ok',
        'data': response
    }


@app.get('/products/images/{product_id}')
async def get_product_images(product_id: int):
    product = await Product.get(id=product_id).prefetch_related('product_images')
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_images = await productImage_pydantic.from_queryset(product.product_images.all())
    return {
        'status': 'ok',
        'product_images': [(config_credentials['BASE_URL'] + '/static/images/' + x.image) for x in product_images]
    }


@app.get('/product/images/featured/{product_id}')
async def get_featured_image(product_id: int):
    product = await Product.get(id=product_id).prefetch_related('featured_image')

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    featured_image = product.featured_image
    return {
        'status': 'ok',
        'featured_image': config_credentials['BASE_URL'] + '/static/images/' + featured_image.image
    }


@app.delete('/products/{product_id}')
async def delete_product(product_id: int, user: user_pydanticIn = Depends(get_current_user)):
    response = await Product.get(id=product_id)

    product = await Product.get(id=product_id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        await response.delete()

        return {
            'status': 'ok',
            'message': 'Product deleted',
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to delete this product',
            headers={'WWW-Authenticate': 'Bearer'}
        )


@app.put('/products/{product_id}')
async def update_product(product_id: int, product: product_pydanticIn, user: User = Depends(get_current_user)):
    response = await Product.get(id=product_id)

    product_info = await Product.get(id=product_id)
    business = await product_info.business
    owner = await business.owner

    if owner == user:
        product_data = product.dict(exclude_unset=True)  # Use exclude_unset=True to allow partial updates
        await response.update_from_dict(product_data)
        await response.save()

        return {
            'status': 'ok',
            'message': 'Product updated',
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not allowed to update this product',
            headers={'WWW-Authenticate': 'Bearer'}
        )
