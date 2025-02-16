# PantryPal

## Overview
PantryPal combines three powerful systems to help you manage your kitchen and nutrition more effectively:

### 1. Smart Macro & Pantry Management 
<div align="center">
  <img src="docs/1.png" alt="Macro Tracking Interface" width="800"/>
</div>

PantryPal provides comprehensive nutritional insights:
- 🔄 Real-time macro-nutrient calculations
- 📊 USDA FoodData Central integration
- 📱 UPC barcode scanning support
- 🔍 Smart ingredient auto-completion
- ⚖️ Per-serving nutritional scaling
- 📈 Full pantry nutritional analytics

### 2. AI-Powered Recipe Generation
<div align="center">
  <img src="docs/2.png" alt="Recipe Generation Interface" width="800"/>
</div>

Intelligent meal planning system featuring:
- 🧠 Context-aware recipe suggestions
- 🎯 Macro-nutrient target optimization
- 🥗 Dietary restriction compliance
- 🔄 Dynamic serving size adjustments
- 🕒 Timezone-aware meal planning

### 3. Secure User Management
<div align="center">
  <img src="docs/3.png" alt="Authentication Interface" width="800"/>
</div>

Enterprise-grade security features:
- 🔐 JWT-based authentication
- 🔒 Secure token management
- ⏱️ Configurable session handling
- 🚫 Data isolation per user
- 🔑 Role-based access control

## Technical Overview

PantryPal is a microservices-based AI-powered kitchen management system that demonstrates modern software architecture and AI integration patterns. The system combines inventory tracking with intelligent recipe generation through Ollama LLM integration.

## Technical Architecture

PantryPal uses a modern microservices architecture with four key service layers:

```
+-------------------------PantryPal Architecture-------------------------+
|                                                                      |
|                        [Client Layer]                                |
|  +-------------+                                                     |
|  |  Streamlit  |    Real-time UI, Recipe Browsing, Inventory Mgmt   |
|  |     UI      |                                                     |
|  +------+------+                                                     |
|         |                                                            |
|         v                                                            |
|    [API Layer]        FastAPI Backend Services                       |
|  +-------------+     +--------------+    +---------------+           |
|  |   Auth &    |     |   Pantry &   |    |     AI &      |          |
|  |   Users     |     |   Inventory  |    |    Recipes    |          |
|  +-------------+     +--------------+    +---------------+           |
|         |                  |                    |                    |
|         v                  v                    v                    |
|    [Service Layer]    Core Business Logic                           |
|  +-------------+     +--------------+    +---------------+           |
|  | JWT Auth    |     | USDA Food    |    |   Ollama      |          |
|  | Sessions    |<--->| Data Central |<-->|   LLM Model   |          |
|  | User Mgmt   |     | API Client   |    |   Generation  |          |
|  +-------------+     +--------------+    +---------------+           |
|         |                  |                    |                    |
|         v                  v                    v                    |
|    [Storage Layer]    Persistent Data                               |
|  +--------------------------------------------------+              |
|  |                   JSON Storage                     |              |
|  |  • Users  • Inventory  • Recipes  • Auth Sessions  |              |
|  +--------------------------------------------------+              |
|                                                                      |
+----------------------------------------------------------------------+

Flow:
→ HTTP/REST   ⇢ Internal Calls   ⇣ Data Access   ↺ Background Tasks
```

### Core Components

#### Authentication & Users
- JWT-based security
- Session management
- User data isolation

#### Pantry & Inventory
- USDA nutritional data
- Async macro processing
- Inventory tracking

#### AI & Recipes
- Ollama LLM integration
- Recipe generation
- Macro-aware planning

## Development Setup

### Prerequisites
- Docker and docker-compose
- Ollama installed locally (for non-Docker development)
- Python 3.8+

### Environment Configuration
```bash
AI_OLLAMA_MODEL=mistral
LLM_CLIENT_BASE=http://ollama:11434
USDA_API_KEY=your_api_key_here  # Required for nutritional data
SECRET_KEY=your_secret_key      # Required for JWT encryption
ACCESS_TOKEN_EXPIRE_MINUTES=30  # JWT token expiry time
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

