FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV NAME magic-judge-telegram-bot

COPY . .

CMD ["python", "magic-judge-telegram-bot.py"]
