# Настройка проекта NoodleLibrary


Клонирование репозитория
```bash
git clone git@github.com:Spaceoceanoutlook/NoodleLibrary.git
```
Открыть проект в редакторе, в корне проекта создать файл `.env` и добавить данные

Для создание виртуального окружения и установки библиотек:
```bash 
poetry install
```
Для активации виртуального окружения:
```bash 
poetry env activate
```
Запуск Postgres
```bash 
docker compose -f "docker-compose.dev.yml" up -d
```
Применить миграции:
```bash 
alembic upgrade head
```
Запуск приложения:
```bash 
python noodlelibrary/main.py
```
API будет доступен в браузере по `http://127.0.0.1:8000/docs`