# 🚀 Stripe Django Store  

Этот проект — интернет-магазин на Django с интеграцией **Stripe** для онлайн-платежей.  
Позволяет добавлять товары в заказ и оплачивать их через Stripe Checkout.  

---

## 📌 **Технологии**  
- **Python 3.13+**  
- **Django 5.1+**  
- **Django Rest Framework**  
- **Stripe API**  
- **PostgreSQL**  
- **Docker + Docker Compose**  

---

## ⚡ **Запуск проекта (локально)**  

### 1️⃣ **Склонируйте репозиторий**  
```bash
git clone https://github.com/Baklachok/Stripe.git
cd Stripe
```

### 2️⃣ **Создайте виртуальное окружение и установите зависимости**

```bash
python -m venv .venv
source .venv/bin/activate  # Для macOS/Linux
# или
.venv\Scripts\activate  # Для Windows

pip install -r requirements.txt
```

### 3️⃣ **Настройте .env файл**

Создайте .env из шаблона:

```bash
cp .env.template .env
```

Заполните .env своими данными:

```ini
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Stripe API Keys
STRIPE_SECRET_KEY_USD=your-stripe-secret-key-usd
STRIPE_SECRET_KEY_EUR=your-stripe-secret-key-eur
STRIPE_PUBLIC_KEY_USD=your-stripe-public-key-usd
STRIPE_PUBLIC_KEY_EUR=your-stripe-public-key-eur
```

### 4️⃣ **Запустите миграции и создайте суперпользователя**
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5️⃣ **Запустите сервер**
```bash
python manage.py runserver
```

## 🐳 **Запуск через Docker**

### 1️⃣ **Заполните .env своими данными**

```ini
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Stripe API Keys
STRIPE_SECRET_KEY_USD=your-stripe-secret-key-usd
STRIPE_SECRET_KEY_EUR=your-stripe-secret-key-eur
STRIPE_PUBLIC_KEY_USD=your-stripe-public-key-usd
STRIPE_PUBLIC_KEY_EUR=your-stripe-public-key-eur
```

### 2️ **Запустите контейнеры**

```bash
docker-compose up --build
```

### 3️⃣ **Готово!**

Django сервер запущен на http://localhost:8000/, база данных PostgreSQL работает внутри Docker.
