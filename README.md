# PantryPal

## Technical Overview

PantryPal is a microservices-based AI-powered kitchen management system that demonstrates modern software architecture and AI integration patterns. The system combines inventory tracking with intelligent recipe generation through Ollama LLM integration.

## Technical Architecture

### AI Components

#### Recipe Generation Engine
- Leverages Ollama's Mistral model for contextual recipe creation based on:
  - Available ingredients with nutritional information
  - User dietary restrictions
  - Macro-nutrient targets
  - Real-time inventory state

#### AI Service Features
- Streaming LLM responses
- Context-aware recipe generation
- Macro-nutrient aware meal planning
- Timezone-aware suggestions

### Backend Architecture

#### API Layer (FastAPI)
- Async request handling
- Ollama client integration
- Structured prompt engineering
- Error handling and logging

#### Service Layer
- Modular microservices design
- Asynchronous operations
- Inventory management
- Recipe parsing and generation

### Frontend Implementations

#### Streamlit Interface
- Real-time data visualization
- Interactive recipe browsing
- Inventory management dashboard

## Technical Stack

### Core Technologies
- Python 3.8+
- FastAPI
- Streamlit
- Docker/Docker Compose

### AI Integration
- Ollama LLM
- Mistral model
- Async API orchestration

### Data Management
- JSON-based persistent storage
- Structured prompt templates
- Macro-nutrient tracking

## Development Setup

### Prerequisites
- Docker and docker-compose
- Ollama installed locally (for non-Docker development)
- Python 3.8+

### Environment Configuration
```bash
AI_OLLAMA_MODEL=mistral
LLM_CLIENT_BASE=http://ollama:11434
```

### Running with Docker

Ensure `docker` and `docker-compose` are installed, then run:

```bash
docker compose up
```

The UI will be available at [http://127.0.0.1:8501](http://127.0.0.1:8501)

### Running Locally

For local development, first install Ollama from [ollama.ai](https://ollama.ai) and run:

```bash
ollama pull mistral
ollama serve
```

Then you can run each component separately:

#### FastAPI Backend

```bash
cd api
pip install -r requirements.txt
uvicorn api:app --reload
```

#### Flask UI

```bash
cd Flask
pip install -r requirements.txt
python main.py
```

#### Streamlit UI

```bash
cd Streamlit
pip install -r requirements.txt
streamlit run app.py
```

Make sure you have all required dependencies installed before running any component.

## Architecture Diagram

```
+----------------------------------------------------------------------------------------+
|                                     PantryPal System                                   |
+----------------------------------------------------------------------------------------+

+-------------+     +-------------+     +-------------+     +-------------+
|  Streamlit  |     |    Flask    |     |   FastAPI   |     |   Ollama    |
|     UI      |<--->|      UI     |<--->|   Backend   |<--->|   LLM Server|
|  Port:8501  |     |  Port:5000  |     |  Port:8000  |     |  Port:11434 |
+-------------+     +-------------+     +-------------+     +-------------+
                                |
                                v
        +------------------------[API Routes]------------------------+
        |                                                            |
+-------------+  +---------------+  +------------------------+       |
|    /ai/     |  |  /inventory/  |  |      /recipes/        |        |
+-------------+  +---------------+  +------------------------+       |
        |               |                       |                    |
        v               v                       v                    |
+-----------+  +--------------+  +-------------------------+         |
|  Prompts  |  |  Item CRUD   |  |   Recipe Generation    |          |
+-----------+  +--------------+  +-------------------------+         |
        |               |                       |                    |
        +---------------+-----------------------+--------------------+
                                |
                                v
                        +------------------+
                        |  Data Storage    |
                        |  (JSON Files)    |
                        +------------------+

     [Data Flow]
     ---------->  HTTP/REST API Calls
     - - - - ->  Internal Service Communication


Key Features:
┌─────────────────────┐
│ • Async Processing  │
│ • LLM Integration   │
│ • Macro Tracking    │
│ • Recipe Gen        │
└─────────────────────┘
```

## Future Enhancements
- Custom model fine-tuning for recipe generation
- Enhanced nutritional analysis
- Multi-model AI pipeline
- Collaborative recipe development
- Advanced inventory optimization

