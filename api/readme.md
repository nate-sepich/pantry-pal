# Pantry API

This is a FastAPI application for managing pantry inventory items.

## Setup

1. **Clone the repository:**

    ```sh
    git clone <repository_url>
    cd pantry
    ```

2. **Create a virtual environment:**

    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment:**

    - On Windows:

        ```sh
        venv\Scripts\activate
        ```

    - On macOS/Linux:

        ```sh
        source venv/bin/activate
        ```

4. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Running the Application

1. **Start the FastAPI server:**

    ```sh
    uvicorn api:app --reload
    ```

    This will start the server on `http://127.0.0.1:8000`.

2. **Access the API documentation:**

    Open your browser and go to `http://127.0.0.1:8000/docs` to see the interactive API documentation provided by Swagger UI.

## Running Tests

1. **Run the tests using pytest:**

    ```sh
    pytest
    ```

## Additional Information

- **FastAPI Documentation:** [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **Uvicorn Documentation:** [https://www.uvicorn.org/](https://www.uvicorn.org/)