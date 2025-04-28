from fastapi import FastAPI
from ai.openai_service import openai_router

app = FastAPI()

# Include the OpenAI router
app.include_router(openai_router)

# Additional routers and middleware can be added here