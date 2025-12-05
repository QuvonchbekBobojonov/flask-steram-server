FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt ./
RUN apt-get update && apt-get install -y \
libglib2.0-0 libsm6 libxrender1 libxext6 \
&& pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["python", "app.py"]
