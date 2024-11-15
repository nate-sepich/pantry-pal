# Panty Pal

## Overview

A pal for your pantry! Inventory and capture your pantry, build recipies and details based on this.

## Getting Started

### Running with Docker

- Ensure `docker` and `docker-compose` are installed.

```bash
docker compose up 
```

[Access the UI over port 8501](http://127.0.0.1:8501)

### Running locally

#### To run the FastAPI app using Uvicorn, you can use the following command:

```bash
cd api
pip install -r requirements.txt
uvicorn api:app --reload
```

This assumes that your `api.py` file is located in the `pantry` folder and that your Flask app object is named `app`.

#### Running the Flask UI
```bash
cd Flask
pip install -r requirements.txt
python main.py
```

#### Running the Pantry Streamlit UI

```bash
cd Streamlit
pip install -r requirements.txt
python -m streamlit app.py
```

This assumes that your `main.py` file is located in the `Flask` folder.

Remember to make sure that you have all the necessary dependencies installed and that you are in the correct directory before running these commands.
