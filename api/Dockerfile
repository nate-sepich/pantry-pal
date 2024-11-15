FROM python:3.12-slim

COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY . .

CMD ["uvicorn", "api:app", "--reload", "--host", "0.0.0.0"]
