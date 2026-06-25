#!/usr/bin/env bash
# Render build script — runs on every deploy
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'pramilatmg.np@gmail.com', 'SparkleWash@2024')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
