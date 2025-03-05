import os
import django
from django.conf import settings
from django.contrib.auth import get_user_model

# Устанавливаем путь к проекту вручную
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stripe_project.settings")

# Добавляем путь к проекту в sys.path, если он не находится в PYTHONPATH
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

django.setup()

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Суперпользователь {username} создан!")
else:
    print(f"Суперпользователь {username} уже существует.")
