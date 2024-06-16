import datetime

from tortoise import Model, fields
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator


class User(Model):
    id = fields.IntField(pk=True, index=True)
    username = fields.CharField(max_length=100, null=False, unique=True)
    email = fields.CharField(max_length=100, null=False, unique=True)
    password = fields.CharField(max_length=100, null=False)
    is_verified = fields.BooleanField(default=False)
    join_date = fields.DatetimeField(default=datetime.datetime.now(datetime.UTC))


class Business(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=100, null=False, unique=True)
    city = fields.CharField(max_length=100, null=False, default='Unspecified')
    region = fields.CharField(max_length=100, null=False, default='Unspecified')
    description = fields.TextField(null=False, default='Unspecified')
    logo = fields.CharField(max_length=255, null=False, default='default.jpg')
    owner = fields.ForeignKeyField('models.User', related_name='business_owner', on_delete=fields.CASCADE)


class ProductImage(Model):
    id = fields.IntField(pk=True, index=True)
    image = fields.CharField(max_length=255, null=False, default='productDefault.jpg')


class Product(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=100, null=False, unique=True)
    category = fields.CharField(max_length=100, null=False, default='Unspecified')
    description = fields.TextField(null=False)
    original_price = fields.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    current_price = fields.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    percentage_discount = fields.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    offer_expiration_date = fields.DateField(default=datetime.datetime.now(datetime.UTC).date())
    product_images = fields.ManyToManyField('models.ProductImage', related_name='product_images')
    business = fields.ForeignKeyField('models.Business', related_name='products', on_delete=fields.CASCADE)


user_pydantic = pydantic_model_creator(User, name='User', exclude=('is_verified', 'join_date'))
user_pydanticIn = pydantic_model_creator(User, name='UserIn', exclude_readonly=True, exclude=('is_verified', 'join_date'))
user_pydanticOut = pydantic_model_creator(User, name='UserOut', exclude=('password',))

business_pydantic = pydantic_model_creator(Business, name='Business')
business_pydanticIn = pydantic_model_creator(Business, name='BusinessIn', exclude_readonly=True)

productImage_pydantic = pydantic_model_creator(ProductImage, name='ProductImage')

product_pydantic = pydantic_model_creator(Product, name='Product')
product_pydanticIn = pydantic_model_creator(Product, name='ProductIn', exclude=('percentage_discount', 'id'))
