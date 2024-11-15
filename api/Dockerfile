FROM python:3.12-slim

COPY . .

RUN pip install -r ./requirements.txt

CMD ["uvicorn", "api:app", "--reload", "--host", "0.0.0.0"]
