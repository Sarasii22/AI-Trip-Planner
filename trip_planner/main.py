from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document
from starlette.responses import JSONResponse
import os
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set specific origins in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def query_travel_agent(query: QueryRequest):
    try:
        messages = {"messages": [query.question]}
        output = react_app.invoke(messages)
        final_output = output["messages"][-1].content if isinstance(output, dict) and "messages" in output else str(output)
        return {"answer": final_output}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})