FROM python:3.11-slim

WORKDIR /app

# Копируем файл зависимостей и код бота в контейнер
COPY requirements.txt ./
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
