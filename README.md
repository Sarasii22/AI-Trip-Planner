# 🌍 AI Trip Planner

An **agentic AI-powered travel planning application** built with LangGraph, FastAPI, and Streamlit. The agent engages in a natural conversation to understand your travel preferences and then generates a complete, personalised trip itinerary — with real-time weather, places, restaurants, activities, transportation, cost breakdowns, and currency conversions — all in a single comprehensive response.

**🔗 Live demo:** [ceylonbliss-ai-trip-planner.streamlit.app](https://ceylonbliss-ai-trip-planner.streamlit.app/)

> The demo is hosted on free-tier services — see [Known Limitations](#-known-limitations) below before judging response times or persistence.

---

## ✨ Features

- 🗺️ **Day-by-day itinerary** for any destination worldwide (classic + off-beat tracks)
- 🏨 **Hotel recommendations** with approximate nightly costs
- 🍽️ **Restaurant discovery** with links and price ranges
- 🎭 **Attractions & activities** (tourist + off-beat options)
- 🚌 **Transportation modes** available at the destination
- 🌤️ **Real-time weather** (current conditions + multi-day forecast)
- 💱 **Dual-currency cost breakdown** — totals shown in USD *and* the traveler's home currency when they differ, using live exchange rates
- 🧮 **Accurate expense calculation** (no manual totalling — tool-verified)
- 📥 **Export itinerary** as a styled Markdown (`.md`) or PDF file (Unicode-safe, no system dependencies required)
- 💬 **Multi-turn conversation memory** with SQLite persistence (survives server restarts, not guaranteed across every hosting redeploy — see limitations)
- 🗂️ **Multiple chat sessions** — sidebar UI to start new trip conversations and switch between past ones, each with isolated memory
- 🔗 **Clickable links** for every hotel, restaurant, and attraction (direct source link, or a Google Maps search fallback)
- 🧭 **Interactive clarifying questions** — single-choice pill buttons, multi-select for things like interests/dietary needs, and a "✏️ Other" free-text option when the presets don't fit
- 📜 **Conversation history API** — retrieve past sessions by `thread_id`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│               Streamlit UI                   │
│           (streamlit_app.py)                  │
│   Sidebar: multi-chat · Chat: clarify buttons │
└──────────────────┬────────────────────────────┘
                    │ HTTP (REST)
┌──────────────────▼────────────────────────────┐
│             FastAPI Backend                    │
│               (main.py)                        │
│  POST /query  |  GET /history/{thread_id}      │
│  GET /threads |  GET /health                   │
└──────────────────┬────────────────────────────┘
                    │
┌──────────────────▼────────────────────────────┐
│         LangGraph ReAct Agent                  │
│       (agent/agentic_workflow.py)              │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐    │
│  │  agent   │◄─│  tools   │  │SqliteSaver│    │
│  │  (LLM)   │─►│   node   │  │(per thread)│    │
│  └──────────┘  └──────────┘  └───────────┘    │
└─────────────────────────────────────────────────┘
```

The agent follows a **ReAct loop** (Reason → Act → Observe) powered by LangGraph's `StateGraph`. A `SqliteSaver` checkpointer persists conversation history per `thread_id` in `checkpoints.sqlite`, enabling multi-turn sessions that survive server restarts on a persistent filesystem.

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
| `convert_currency` | Live currency conversion for dual-currency totals | ExchangeRate API |

> Place search uses **Google Places** as the primary source and automatically falls back to **Tavily** web search if Google fails or the key is invalid/quota-exceeded.

---

## 📁 Project Structure

```
AI-Trip-Planner/
└── trip_planner/
    ├── main.py                  # FastAPI backend entry point
    ├── streamlit_app.py         # Streamlit chat UI
    ├── pyproject.toml           # Project metadata & build config (must list ALL deps — see note below)
    ├── requirements.txt         # Python dependencies
    ├── .env.name                # Environment variable template
    ├── checkpoints.sqlite       # SQLite conversation memory (gitignored, generated at runtime)
    │
    ├── agent/
    │   └── agentic_workflow.py  # LangGraph GraphBuilder (ReAct agent + SqliteSaver)
    │
    ├── tools/                   # LangChain tool wrappers
    │   ├── weather_info_tool.py
    │   ├── place_search_tool.py
    │   ├── expense_calculator_tool.py
    │   └── currency_conversion_tool.py
    │   └── arithmatic_op_tool.py
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
    ├── assets/
    │   └── fonts/                # (Optional) embedded fonts for PDF export
    │
    └── output/                  # Generated itinerary files (.md / .pdf) — gitignored
```

> ⚠️ **Important:** some hosting platforms (e.g. FastAPI Cloud) install dependencies from `pyproject.toml` rather than `requirements.txt` when both are present. Make sure `pyproject.toml`'s `dependencies` list is kept in sync with `requirements.txt`, or deployment will silently install an incomplete set of packages.

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
# Using uv (recommended for this project)
uv pip install -r requirements.txt

# OR using pip
pip install -r requirements.txt
```

> If you're in a `uv`-managed virtual environment, `pip`/`python -m pip` may not be available — use `uv pip install` instead.

### 4. Configure environment variables

Copy `.env.name` to `.env` and fill in your own API keys:

```bash
cp .env.name .env
```

```env
# LLM providers (use at least one)
OPENAI_API_KEY=""
GROQ_API_KEY=""

# Places search
GPLACES_API_KEY=""            # Google Places API
TAVILY_API_KEY=""             # Tavily web search (fallback)

# Weather — variable name MUST match exactly, this has caused real bugs before
OPENWEATHERMAP_API_KEY=""

# Currency
EXCHANGE_RATE_API_KEY=""      # exchangerate-api.com

# Observability (optional)
LANGCHAIN_API_KEY=""          # LangSmith tracing
LANGCHAIN_TRACING_V2="true"   # enable tracing if the key above is set
LANGCHAIN_PROJECT="ai-trip-planner"
```

> 🔒 **Never commit `.env`.** Confirm it's listed in `.gitignore` alongside `checkpoints.sqlite` and `output/`. If any real keys were ever pasted into a chat, commit, or shared document, rotate them immediately — treat them as compromised the moment they leave your local `.env` file.

### 5. Configure the LLM model

Edit [`config/config.yaml`](trip_planner/config/config.yaml) to choose your model:

```yaml
llm:
  openai:
    provider: openai
    model_name: o4-mini
  groq:
    provider: groq
    model_name: openai/gpt-oss-120b
```

The default provider used in `main.py` is **Groq**. To switch to OpenAI, change `model_provider="groq"` → `model_provider="openai"` in [`main.py`](trip_planner/main.py).

**On choosing a Groq model:** Groq's free tier enforces a *daily* token cap (TPD) that varies significantly by model — this app makes several tool calls per response, so it's easy to hit the daily limit during active development. If you're iterating quickly, a higher-TPD model (e.g. `llama-3.1-8b-instant`) leaves more room for testing; for the strongest reasoning quality (e.g. a live demo), a stronger model like `openai/gpt-oss-120b` is worth the smaller daily budget. Check current limits at [console.groq.com](https://console.groq.com/docs/rate-limits) before committing to one, since these change.

---

## 🚀 Running Locally

You need **two terminal windows** — one for the backend and one for the UI.

### Terminal 1 — FastAPI backend

```bash
cd trip_planner
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`

### Terminal 2 — Streamlit UI

```bash
cd trip_planner
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser. `BASE_URL` defaults to `http://localhost:8000` when no `st.secrets["BASE_URL"]` is set.

---

## ☁️ Deployment

This project is deployed as two separate services:

| Component | Platform | Notes |
|---|---|---|
| Backend (FastAPI) | [FastAPI Cloud](https://fastapicloud.com) | Free Hobby tier, no credit card required |
| Frontend (Streamlit) | [Streamlit Community Cloud](https://share.streamlit.io) | Free, deploys directly from GitHub |

### Deploying the backend

```bash
uv pip install "fastapi-cli[standard]"
fastapi deploy
```

Then set each environment variable (see step 4 above) via the CLI or dashboard:
```bash
fastapi cloud env set GROQ_API_KEY --secret
```
Redeploy after setting variables (`fastapi deploy`) — setting a variable does not auto-trigger a redeploy.

### Deploying the frontend

On [share.streamlit.io](https://share.streamlit.io), point the app at `trip_planner/streamlit_app.py`, then under **Advanced settings → Secrets**, add:
```toml
BASE_URL = "https://your-backend-url.fastapicloud.com"
```

---

## ⚠️ Known Limitations

Being upfront about these matters more than hiding them:

- **Response time**: a full itinerary can take anywhere from ~30 seconds to several minutes, since the agent makes multiple sequential tool calls (weather, 4× place searches, currency conversion, cost calculations) per response. This is inherent to the multi-tool agentic design, not a bug.
- **Free-tier LLM rate limits**: Groq's free tier caps total tokens *per day*, not just per minute — heavy testing/demoing can exhaust the daily quota, which surfaces as a `429` error with a clear message rather than a raw crash.
- **Conversation persistence on free hosting**: `checkpoints.sqlite` lives on the backend's local filesystem. Depending on the hosting platform's storage model, this may not survive every redeploy (though it does survive normal restarts/idling). Conversation memory should not be treated as a permanent database on the free-tier deployment.
- **PDF font coverage**: PDF export uses `xhtml2pdf` (pure Python, no system dependencies) with a character sanitizer that maps most typographic characters (smart quotes, dashes, common currency symbols) to safe equivalents, and silently drops anything outside that range to avoid rendering artifacts. Extremely rare characters not yet covered may be omitted from the PDF (though never from the Markdown export, which preserves the original text).

---

## 💬 Usage

1. Open the Streamlit app.
2. Type your destination or travel query (e.g. *"Plan a trip to Sri Lanka for 4 days"*).
3. The agent asks 1–2 clarifying questions (departure city, interests, budget, currency, etc.) — answer via the interactive buttons, multi-select, or free-text "Other" option.
4. Once enough context is gathered, it generates the **full itinerary** in one response, with both currencies shown if relevant.
5. Download the plan as **Markdown** or **PDF** from the buttons below the response.
6. Use the sidebar to start a **new chat** or switch between previous trip conversations.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Send a message to the travel agent |
| `GET` | `/history/{thread_id}` | Retrieve conversation history for a session |
| `GET` | `/threads` | List all thread IDs with saved state |
| `GET` | `/health` | Lightweight health check (used for uptime monitoring) |

**Example request:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Plan a 5-day trip to Paris", "thread_id": "my-session"}'
```

**Example response:**

```json
{
  "answer": "## Your 5-Day Paris Itinerary ...",
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
| `fastapi-cli` | Deployment tooling for FastAPI Cloud |
| `streamlit` | Chat UI |
| `xhtml2pdf` + `markdown` | PDF & Markdown export (pure Python, no system deps) |
| `python-dotenv` | Environment variable loading |

---

## 📄 Output

Generated itinerary files are saved to `trip_planner/output/` and are also available to download directly from the chat UI:

- `AI_Trip_Planner_<timestamp>.md` — Markdown format
- `AI_Trip_Planner_<timestamp>.pdf` — Styled PDF (A4)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 👤 Author

**Sarasi** — [sarasimadahasi@gmail.com](mailto:sarasimadahasi@gmail.com)