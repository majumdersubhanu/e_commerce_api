# E-Commerce API

This is an E-Commerce API built using FastAPI. The project provides endpoints to manage an e-commerce platform, including user authentication, product management, and order processing.

## Table of Contents
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Server](#running-the-server)
- [Application Flow](#application-flow)
- [Models](#models)
- [Functions and Endpoints](#functions-and-endpoints)
- [Static Files](#static-files)
- [License](#license)

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL
- Git

### Clone the Repository
```bash
git clone https://github.com/majumdersubhanu/e_commerce_api.git
cd e_commerce_api
```

### Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory of the project and add the following variables:

```env
DB_USERNAME='your_db_username'
DB_PASSWORD='your_db_password'
DB_HOST='localhost'
DB_PORT='5432'
DB_NAME='ecommerce'
USERNAME='your_username'
PASSWORD='your_password'
SECRET='your_secret_key'
BASE_URL='http://127.0.0.1:8000'
```

## Database Setup

### Create Database
Make sure PostgreSQL is running and create a database named `ecommerce`:

```sql
CREATE DATABASE ecommerce;
```

## Running the Server

### Start the Server
```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

## Application Flow

### 1. User Authentication
- Users must be authenticated to access most endpoints.
- Token-based authentication is used.
- Users can obtain a token by providing valid credentials.

### 2. Product Management
- Admin users can create, update, and delete products.
- All users can view product listings and details.

### 3. Order Processing
- Authenticated users can create orders.
- Users can view their own orders.

## Models

### User
Represents a user in the system.

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
```

### Product
Represents a product available for purchase.

```python
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float)
    inventory_count = Column(Integer)
```

### Order
Represents an order placed by a user.

```python
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    order_date = Column(DateTime, default=datetime.utcnow)
```

## Functions and Endpoints

### Authentication
- **POST** `/token` - Obtain a token
  - **Function**: `create_token`
  - **Request Body**: `username`, `password`
  - **Response**: `access_token`

### Users
- **POST** `/users` - Create a new user
  - **Function**: `create_user`
  - **Request Body**: `username`, `email`, `password`
  - **Response**: `User`

- **GET** `/users/me` - Get current user details
  - **Function**: `read_users_me`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: `User`

### Products
- **GET** `/products` - List all products
  - **Function**: `get_products`
  - **Response**: List of `Product`

- **POST** `/products` - Create a new product
  - **Function**: `create_product`
  - **Request Body**: `name`, `description`, `price`, `inventory_count`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: `Product`

- **GET** `/products/{product_id}` - Get product details
  - **Function**: `get_product`
  - **Path Parameter**: `product_id`
  - **Response**: `Product`

### Orders
- **POST** `/orders` - Create a new order
  - **Function**: `create_order`
  - **Request Body**: `product_id`, `quantity`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: `Order`

- **GET** `/orders` - List all orders for the current user
  - **Function**: `get_orders`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: List of `Order`

## Static Files

The `static/images/` folder is used to store product images. Make sure this directory exists in your project structure:

```bash
mkdir -p static/images/
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
