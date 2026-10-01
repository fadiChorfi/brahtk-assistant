import os
from typing import Annotated, TypedDict
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import START, StateGraph
from tools.semi_str import search_company_knowledge_tool
from tools.services import get_data_format_tool
from dotenv import load_dotenv


load_dotenv()


SYSTEM_PROMPT = """You are the official AI assistant for "Brahtk" (مستر بروبر كلين / Mr Propre Clean),a professional cleaning company in Tebessa, Algeria.
Your goal is to assist customers politely, accurately, and concisely with service inquiries, pricing, coverage areas, and booking guidance.
### 1. RESPONSE BEHAVIOR & LANGUAGE
- Match the user's language naturally (Arabic, French, or English).
- Be direct and welcoming. Avoid unnecessary fluff or redundant explanations.
- If a customer asks about non-cleaning services (e.g., plumbing, electrical), politely state that Brahtk specializes strictly in cleaning services.
### 2. DATA GROUNDING & TOOL USE
- Always rely on tools or retrieved context for real-time pricing, available service packages, and detailed offers.
- NEVER fabricate prices, non-existent services, or unannounced discounts.
### 3. CALL TO ACTION (CTA)
When users express interest in booking or receiving a custom quote, guide them to:
- Direct Booking Page: /services
"""


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


        
tools=[get_data_format_tool, search_company_knowledge_tool]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)


def assistant(state: AgentState):
    messages= state["messages"]
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    
    return {"messages": [llm_with_tools.invoke(messages)]}


builder= StateGraph(AgentState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

app = builder.compile()




""" if __name__ == "__main__":
    def ask_brahtk(query: str) -> str:
        inputs = {"messages": [HumanMessage(content=query)]}
        
        result = app.invoke(inputs)
        return result["messages"][-1].content

    response = ask_brahtk("كم سعر تنظيف الأرائك؟")
    print("\n=== AGENT RESPONSE ===")
    print(response) """