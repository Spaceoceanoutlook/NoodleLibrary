# Настройка проекта NoodleLibrary


Клонирование репозитория
```bash
git clone https://github.com/Spaceoceanoutlook/NoodleLibrary.git
```
Открыть проект в редакторе, в корне проекта создать файл `.env` и дополнить переменные окружения
```bash
POSTGRES_DB=noodlesdb
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=db
POSTGRES_PORT=5432

NOODLE_PASSWORD=

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
```
Запуск приложения
```bash 
docker compose up --build -d
```
В браузере
```bash 
http://127.0.0.1:8001
```
