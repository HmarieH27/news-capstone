FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY manage.py ./
COPY news_site ./news_site
COPY news ./news
RUN mkdir /data && chown appuser:appuser /data
ENV SQLITE_PATH=/data/db.sqlite3
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000 --noreload"]
