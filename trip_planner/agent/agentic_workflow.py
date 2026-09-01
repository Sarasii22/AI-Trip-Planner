
from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

class GraphBuilder():
    def __init__(self,model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()
        
        self.tools = []
        
        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConverterTool()
        
        self.tools.extend([* self.weather_tools.weather_tool_list, 
                           * self.place_search_tools.place_search_tool_list,
                           * self.calculator_tools.calculator_tool_list,
                           * self.currency_converter_tools.currency_converter_tool_list])
        
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        
        self.graph = None
        
        self.system_prompt = SYSTEM_PROMPT

        # in-memory checkpointer: keeps conversation state per thread_id
        # NOTE: resets when the server restarts. Fine for a portfolio demo;
        # swap for SqliteSaver/PostgresSaver for persistence across restarts.
        self.checkpointer = MemorySaver()
    
    def agent_function(self, state: MessagesState):
        """Main agent function"""
        user_question = state["messages"]
        input_question = [self.system_prompt] + user_question

        try:
            response = self.llm_with_tools.invoke(input_question)
        except Exception as e:
            # Tool call validation failed at the API level — retry once with a corrective nudge
            print(f"Tool call generation failed, retrying: {e}")
            correction = SystemMessage(
                content="Your previous tool call used incorrect parameter names. "
                        "Carefully match the exact parameter names defined in each tool's schema "
                        "(e.g. use 'place', not 'city' or 'location')."
            )
            response = self.llm_with_tools.invoke(input_question + [correction])

        return {"messages": [response]}
    
    def build_graph(self):
        graph_builder=StateGraph(MessagesState)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_edge(START,"agent")
        graph_builder.add_conditional_edges("agent",tools_condition)
        graph_builder.add_edge("tools","agent")
        graph_builder.add_edge("agent",END)
        self.graph = graph_builder.compile(checkpointer=self.checkpointer)
        return self.graph
        
    def __call__(self):
        return self.build_graph()

    def get_thread_history(self, thread_id: str):
        """Return the list of messages stored for a given thread_id, or [] if none exist yet."""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        if state and "messages" in state.values:
            return state.values["messages"]
        return []