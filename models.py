import datetime
from tortoise import Model, fields
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator


class User(Model):
    id = fields.IntField(pk=True, index=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    password = fields.CharField(max_length=100)
    is_verified = fields.BooleanField(default=False)
    join_date = fields.DatetimeField(default=datetime.datetime.now(datetime.UTC).date())


class Business(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=100, unique=True)
    city = fields.CharField(max_length=100, default='Unspecified')
    region = fields.CharField(max_length=100, default='Unspecified')
    description = fields.TextField(default='Unspecified')
    logo = fields.CharField(max_length=255, default='default.jpg')
    owner = fields.ForeignKeyField('models.User', related_name='business_owner', on_delete=fields.CASCADE)


class ProductImage(Model):
    id = fields.IntField(pk=True, index=True)
    image = fields.CharField(max_length=255, default='productDefault.jpg')


class Product(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=100, unique=True)
    category = fields.CharField(max_length=100, default='Unspecified')
    description = fields.TextField()
    original_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    percentage_discount = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    offer_expiration_date = fields.DateField(default=datetime.datetime.now(datetime.UTC).date())
    featured_image = fields.ForeignKeyField('models.ProductImage', related_name='featured_in_products', null=True)
    product_images = fields.ManyToManyField('models.ProductImage', related_name='product_images')
    business = fields.ForeignKeyField('models.Business', related_name='products', on_delete=fields.CASCADE)


user_pydantic = pydantic_model_creator(User, name='User', exclude=('is_verified', 'join_date'))
user_pydanticIn = pydantic_model_creator(User, name='UserIn', exclude_readonly=True,
                                         exclude=('is_verified', 'join_date'))
user_pydanticOut = pydantic_model_creator(User, name='UserOut', exclude=('password',))

business_pydantic = pydantic_model_creator(Business, name='Business')
business_pydanticIn = pydantic_model_creator(Business, name='BusinessIn', exclude_readonly=True)

productImage_pydantic = pydantic_model_creator(ProductImage, name='ProductImage')

product_pydanticIn = pydantic_model_creator(Product, name='ProductIn', exclude=('percentage_discount', 'id'))
product_pydanticOut = pydantic_model_creator(Product, name='ProductOut', exclude=('product_images',))
product_pydantic_with_featuredOut = pydantic_model_creator(Product, name='Product')