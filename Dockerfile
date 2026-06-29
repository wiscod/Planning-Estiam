FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY public/ public/
COPY tests/ tests/

# The CMD should start your python app, e.g. web server or scraper loop, but in a real web app it might start a server.
# Here we'll just set it to run the scraper as a simple entrypoint.
CMD ["python", "src/scraper.py"]
