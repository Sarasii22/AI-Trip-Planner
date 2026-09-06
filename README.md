# 🌍 AI Trip Planner

An **agentic AI-powered travel planning application** built with LangGraph, FastAPI, and Streamlit. The agent engages in a natural conversation to understand your travel preferences and then generates a complete, personalised trip itinerary — with real-time weather, places, restaurants, activities, transportation, cost breakdowns, and currency conversions — all in a single comprehensive response.

---

## ✨ Features

- 🗺️ **Day-by-day itinerary** for any destination worldwide
- 🏨 **Hotel recommendations** with approximate nightly costs
- 🍽️ **Restaurant discovery** with links and price ranges
- 🎭 **Attractions & activities** (tourist + off-beat options)
- 🚌 **Transportation modes** available at the destination
- 🌤️ **Real-time weather** (current conditions + multi-day forecast)
- 💱 **Live currency conversion** for budget estimates
- 🧮 **Accurate expense calculation** (no manual totalling — tool-verified)
- 📥 **Export itinerary** as a styled Markdown (`.md`) or PDF file
- 💬 **Multi-turn conversation memory** with SQLite persistence (survives server restarts)
- 🔗 **Clickable links** for every hotel, restaurant, and attraction
- 🧭 **Interactive clarify buttons** in the UI for guided preference selection
- 📜 **Conversation history API** — retrieve past sessions by `thread_id`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│               Streamlit UI                  │
│           (streamlit_app.py)                │
└──────────────────┬──────────────────────────┘
                   │ HTTP (REST)
┌──────────────────▼──────────────────────────┐
│             FastAPI Backend                  │
│               (main.py)                     │
│  POST /query  |  GET /history/{thread_id}   │
│  GET /threads                               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         LangGraph ReAct Agent               │
│       (agent/agentic_workflow.py)           │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  agent   │◄─│  tools   │  │SqliteSaver│ │
│  │ (LLM)   │──►│  node    │  │(per thread)│ │
│  └──────────┘  └──────────┘  └───────────┘ │
└─────────────────────────────────────────────┘
```

The agent follows a **ReAct loop** (Reason → Act → Observe) powered by LangGraph's `StateGraph`. A `SqliteSaver` checkpointer persists conversation history per `thread_id` in `checkpoints.sqlite`, enabling multi-turn sessions that survive server restarts.

---

## 🛠️ Tools

| Tool | Description | API |
|---|---|---|
| `get_current_weather` | Live weather conditions for a city | OpenWeatherMap |
| `get_weather_forecast` | Multi-day weather forecast | OpenWeatherMap |
| `search_attractions` | Top attractions at a destination | Google Places → Tavily (fallback) |
| `search_restaurants` | Restaurants with details & links | Google Places → Tavily (fallback) |
| `search_activities` | Activities in and around a place | Google Places → Tavily (fallback) |
| `search_transportation` | Available transport modes | Google Places → Tavily (fallback) |
| `estimate_total_hotel_cost` | price × nights calculation | Built-in |
| `calculate_total_expense` | Sum of all trip cost items | Built-in |
| `calculate_daily_expense_budget` | total ÷ days budget breakdown | Built-in |
| `arithmetic_operation` | General arithmetic for cost calculations | Built-in |
| `convert_currency` | Live currency conversion | ExchangeRate API |

> Place search uses **Google Places** as the primary source and automatically falls back to **Tavily** web search if Google fails.

---

## 📁 Project Structure

```
AI-Trip-Planner/
└── trip_planner/
    ├── main.py                  # FastAPI backend entry point
    ├── streamlit_app.py         # Streamlit chat UI
    ├── pyproject.toml           # Project metadata & build config
    ├── requirements.txt         # Python dependencies
    ├── .env.name                # Environment variable template
    ├── my_graph.png             # Auto-generated LangGraph diagram
    │
    ├── agent/
    │   └── agentic_workflow.py  # LangGraph GraphBuilder (ReAct agent + SqliteSaver)
    │
    ├── tools/                   # LangChain tool wrappers
    │   ├── weather_info_tool.py
    │   ├── place_search_tool.py
    │   ├── expense_calculator_tool.py
    │   ├── arithmatic_op_tool.py
    │   └── currency_conversion_tool.py
    │
    ├── utils/                   # Core service implementations
    │   ├── model_loader.py      # LLM loader (Groq / OpenAI)
    │   ├── config_loader.py     # YAML config loader
    │   ├── place_info_search.py # Google Places + Tavily search
    │   ├── weather_info.py      # OpenWeatherMap API client
    │   ├── currency_converter.py# ExchangeRate API client
    │   ├── expense_calculator.py# Arithmetic helpers
    │   └── save_to_document.py  # Markdown & PDF export
    │
    ├── prompt_library/
    │   └── prompt.py            # System prompt for the travel agent
    │
    ├── config/
    │   └── config.yaml          # LLM model configuration
    │
    ├── exception/
    │   └── exceptionhandling.py # Custom exception handling
    │
    ├── logger/
    │   └── logging.py           # Application logger setup
    │
    ├── notebook/                # Jupyter notebooks (experimentation)
    ├── assets/                  # Static assets (fonts, etc.)
    └── output/                  # Generated itinerary files (.md / .pdf)
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python **3.12+**
- [uv](https://github.com/astral-sh/uv) (recommended) **or** pip

### 2. Clone the repository

```bash
git clone https://github.com/Sarasii22/AI-Trip-Planner.git
cd AI-Trip-Planner/trip_planner
```

### 3. Install dependencies

```bash
# Using pip
pip install -r requirements.txt

# OR using uv
uv sync
```

### 4. Configure environment variables

Copy `.env.name` to `.env` and fill in your API keys:

```bash
cp .env.name .env
```

```env
# LLM providers (use at least one)
OPENAI_API_KEY=""
GROQ_API_KEY=""

# Places search
GPLACES_API_KEY=""        # Google Places API
TAVILY_API_KEY=""         # Tavily web search (fallback)

# Weather
OPENWEATHER_API_KEY=""    # OpenWeatherMap

# Currency
EXCHANGE_RATE_API_KEY=""  # ExchangeRate API

# Observability (optional)
LANGCHAIN_API_KEY=""      # LangSmith tracing
GOOGLE_API_KEY=""         # General Google API key
```

> **Note:** The `.env.name` template also contains `FOURSQUARE_API_KEY` for future place-discovery expansion, though it is not used by the current tool implementations.

### 5. Configure the LLM model

Edit [`config/config.yaml`](trip_planner/config/config.yaml) to choose your model:

```yaml
llm:
  groq:
    provider: "groq"
    model_name: "openai/gpt-oss-120b"   # or any Groq-hosted model
  openai:
    provider: "openai"
    model_name: "o4-mini"
```

The default provider used in `main.py` is **groq**. To switch to OpenAI, change `model_provider="groq"` → `model_provider="openai"` in [`main.py`](trip_planner/main.py).

---

## 🚀 Running the Application

You need **two terminal windows** — one for the backend and one for the UI.

### Terminal 1 — FastAPI backend

```bash
cd trip_planner
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Terminal 2 — Streamlit UI

```bash
cd trip_planner
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## 💬 Usage

1. Open the Streamlit app in your browser.
2. Type your destination or travel query (e.g. *"Plan a trip to Canada for 5 days"*).
3. The agent may ask 1–2 clarifying questions (departure city, budget, interests, dates) — answer via the interactive buttons or free-text input.
4. Once you answer, it generates the **full itinerary** in one response.
5. Download the plan as a **Markdown** or **PDF** file using the buttons below the response.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Send a message to the travel agent |
| `GET` | `/history/{thread_id}` | Retrieve conversation history for a session |
| `GET` | `/threads` | List all thread IDs with saved state |

**Example request:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Plan a 5-day trip to Paris", "thread_id": "my-session"}'
```

**Example response:**

```json
{
  "answer": "## 🗺️ Your 5-Day Paris Itinerary ...",
  "saved_file": "output/AI_Trip_Planner_20260906_123456.md",
  "saved_pdf": "output/AI_Trip_Planner_20260906_123456.pdf"
}
```

> `saved_file` and `saved_pdf` are `null` when the response is a clarifying question rather than a completed itinerary.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `langgraph` | Agentic workflow / state graph |
| `langgraph-checkpoint-sqlite` | SQLite-backed conversation persistence |
| `langchain`, `langchain-community` | LLM orchestration & tools |
| `langchain-groq` | Groq LLM provider |
| `langchain-openai` | OpenAI LLM provider |
| `langchain-google-community[places]` | Google Places integration |
| `langchain-tavily` | Tavily web search |
| `fastapi` + `uvicorn` | REST API backend |
| `streamlit` | Chat UI |
| `xhtml2pdf` + `markdown` | PDF & Markdown export |
| `python-dotenv` | Environment variable loading |

---

## 📄 Output

Generated itinerary files are saved to `trip_planner/output/` and are also available to download directly from the chat UI:

- `AI_Trip_Planner_<timestamp>.md` — Markdown format
- `AI_Trip_Planner_<timestamp>.pdf` — Styled PDF (A4, print-ready)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 👤 Author

**Sarasi** — [eg245387@engug.ruh.ac.lk](mailto:eg245387@engug.ruh.ac.lk)
