FROM python:3.9-alpine

COPY . .

RUN pip3 install -r requirements.txt

RUN crontab crontab

CMD ["crond", "-f"]
