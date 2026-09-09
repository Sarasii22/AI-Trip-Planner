from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document
from starlette.responses import JSONResponse
from utils.save_to_document import save_document
import os
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from utils.save_to_document import save_document, save_document_pdf
import traceback
import json
import queue
import threading
import time
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set specific origins in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    thread_id: str = "default"   # identifies which conversation this belongs to

graph_builder = GraphBuilder(model_provider="groq")
react_app = graph_builder()  # build once, reuse across requests


@app.on_event("startup")
async def save_graph_diagram():
    try:
        png_graph = react_app.get_graph().draw_mermaid_png()
        with open("my_graph.png", "wb") as f:
            f.write(png_graph)
        print("Graph diagram saved.")
    except Exception as e:
        print(f"Could not save graph diagram (non-fatal): {e}")

@app.post("/query")
def query_travel_agent(query: QueryRequest):
    try:
        config = {"configurable": {"thread_id": query.thread_id}}
        messages = {"messages": [query.question]}
        output = react_app.invoke(messages, config=config)
        final_output = output["messages"][-1].content if isinstance(output, dict) and "messages" in output else str(output)

        saved_md = None
        saved_pdf = None

        # only export when the response looks like a completed itinerary, not a clarifying question
        if len(final_output) > 800 and "?" not in final_output[-100:]:
            saved_md = save_document(final_output)
            saved_pdf = save_document_pdf(final_output)

        return {"answer": final_output, "saved_file": saved_md, "saved_pdf": saved_pdf}
    except Exception as e:
        error_str = str(e)
        if "rate_limit_exceeded" in error_str or "429" in error_str:
            return JSONResponse(status_code=429, content={
                "error": "Daily AI usage limit reached for this model. Try again later, or switch to a different model in config.yaml."
            })
        print("=== /query failed ===")
        traceback.print_exc()
        print("======================")
        return JSONResponse(status_code=500, content={"error": error_str})
    
@app.get("/history/{thread_id}")
def get_history(thread_id: str):
    try:
        messages = graph_builder.get_thread_history(thread_id)
        formatted = []
        for m in messages:
            role = "user" if m.type == "human" else "assistant"
            # skip empty assistant messages that were just tool-call triggers
            if m.content:
                formatted.append({"role": role, "content": m.content})
        return {"messages": formatted}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/threads")
def list_threads():
    try:
        return {"thread_ids": graph_builder.list_thread_ids()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


def _stream_agent_response(question: str, thread_id: str):
    """Runs the agent in a background thread and yields small JSON chunks as it
    progresses. Chunks are sent at least every ~8 seconds (heartbeats if the
    agent is still mid-step), which keeps the connection alive through
    Cloudflare's 100-second no-data timeout — a single long blocking response
    gets killed at 100s regardless of client-side timeout settings; a response
    that keeps emitting bytes does not."""
    q = queue.Queue()

    def worker():
        try:
            config = {"configurable": {"thread_id": thread_id}}
            for step in react_app.stream({"messages": [question]}, config=config, stream_mode="updates"):
                node_name = list(step.keys())[0] if step else "agent"
                q.put(("step", node_name))
            q.put(("done", None))
        except Exception as e:
            q.put(("error", str(e)))

    t = threading.Thread(target=worker)
    t.start()

    yield json.dumps({"type": "status", "message": "Starting..."}) + "\n"

    while True:
        try:
            kind, payload = q.get(timeout=8)
        except queue.Empty:
            yield json.dumps({"type": "heartbeat"}) + "\n"
            continue

        if kind == "step":
            yield json.dumps({"type": "status", "message": f"Working: {payload}..."}) + "\n"
        elif kind == "error":
            yield json.dumps({"type": "error", "message": payload}) + "\n"
            return
        elif kind == "done":
            config = {"configurable": {"thread_id": thread_id}}
            state = react_app.get_state(config)
            final_output = state.values["messages"][-1].content if state and "messages" in state.values else ""

            saved_md, saved_pdf = None, None
            if len(final_output) > 800 and "?" not in final_output[-100:]:
                saved_md = save_document(final_output)
                saved_pdf = save_document_pdf(final_output)

            yield json.dumps({
                "type": "final",
                "answer": final_output,
                "saved_file": saved_md,
                "saved_pdf": saved_pdf,
            }) + "\n"
            return


@app.post("/query/stream")
def query_travel_agent_stream(query: QueryRequest):
    return StreamingResponse(
        _stream_agent_response(query.question, query.thread_id),
        media_type="application/x-ndjson",
    )