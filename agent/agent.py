# agent.py — Medical-necessity appeals CHATBOT agent (LangGraph ResponsesAgent)
# Scope: the interactive follow-up assistant ONLY. The appeal-letter generation is a
# separate declarative ai_query batch (no framework). LangGraph is used here because the
# chatbot is genuinely agentic (multi-turn + dynamic tool choice) and the org standardizes
# on LangGraph for chatbots.
import uuid
from typing import Annotated, Generator, Sequence, TypedDict

import mlflow
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest, ResponsesAgentResponse, ResponsesAgentStreamEvent,
)
from databricks_langchain import ChatDatabricks, UCFunctionToolkit, VectorSearchRetrieverTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode

CATALOG, SCHEMA = "appeals_hackathon_catalog", "fe_bar_appeals"
LLM_ENDPOINT = "databricks-claude-sonnet-4-6"   # no AI-Gateway safety guardrail on surgical/oncology language
VS_INDEX     = f"{CATALOG}.{SCHEMA}.med_nec_criteria_index"
UC_FUNCTIONS = [
    f"{CATALOG}.{SCHEMA}.get_appeal",        # recommendation + cheat sheet + letter for an encounter
    f"{CATALOG}.{SCHEMA}.get_encounter",     # claim facts + clinical digest + MPFS context
    f"{CATALOG}.{SCHEMA}.mpfs_lookup",       # MPFS indicators + meaning for a CPT
    f"{CATALOG}.{SCHEMA}.descriptor_lookup", # plain-English MPFS indicator meanings
]

SYSTEM_PROMPT = """You are a hospital Revenue Cycle appeals assistant. You help a human reviewer ask follow-up questions about a specific medical-necessity appeal that was already drafted (denial codes CO50/CO55/CO57/CO150/CO186).

The recommendation is one of WARRANTED, NOT WARRANTED or NEEDS REVIEW. NEEDS REVIEW means the evidence was insufficient, ambiguous or contradictory; explain the documentation gaps from needs_review_reason and never draft an appeal for it. The cheat sheet is LLM reasoning: label it "AI reasoning". The claim facts, criteria routing, dated note excerpts and deadline facts come from the deterministic data sheet (get_encounter); treat them as the source of record.

Ground every answer in the tools — never invent claim facts, criteria, or coding values:
- Use get_appeal(fac, pcn, enc) to fetch the recommendation, needs_review_reason, the AI reasoning worksheet, and the appeal letter for an encounter.
- Use get_encounter(fac, pcn, enc) for the claim facts, diagnoses/procedures, clinical-notes digest, and MPFS context.
- Use med_nec_search to pull the exact BCBS or CMS medical-necessity criteria language (filter by payer_type when relevant).
- Use mpfs_lookup(code) / descriptor_lookup(term) for CPT/HCPCS coding and MPFS indicator questions.

When the reviewer refers to "this appeal" / "this patient", use the encounter key from the conversation. Cite what you relied on (the cheat sheet, a specific note, or the criteria/source file). If a tool returns nothing, say so plainly rather than guessing. Be concise and factual."""


class State(TypedDict):
    messages: Annotated[Sequence, add_messages]


class AppealsChatAgent(ResponsesAgent):
    def __init__(self):
        self.llm = ChatDatabricks(endpoint=LLM_ENDPOINT)
        self.tools = list(UCFunctionToolkit(function_names=UC_FUNCTIONS).tools)
        self.tools.append(VectorSearchRetrieverTool(
            index_name=VS_INDEX,
            num_results=5,
            columns=["chunk_id", "payer_type", "source_file", "chunk_to_retrieve"],
            tool_name="med_nec_search",
            tool_description=(
                "Retrieve BCBS or CMS medical-necessity criteria text. Query with the clinical "
                "question; filter by payer_type ('BCBS' or 'CMS') to match the payer."
            ),
        ))
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _graph(self):
        def call_model(state):
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
            return {"messages": [self.llm_with_tools.invoke(msgs)]}

        def should_continue(state):
            last = state["messages"][-1]
            return "tools" if isinstance(last, AIMessage) and last.tool_calls else "end"

        g = StateGraph(State)
        g.add_node("agent", RunnableLambda(call_model))
        g.add_node("tools", ToolNode(self.tools))
        g.set_entry_point("agent")
        g.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
        g.add_edge("tools", "agent")
        return g.compile()

    def _to_lc(self, req):
        out = []
        for m in req.input:
            d = m.model_dump()
            role, content = d.get("role"), d.get("content")
            if isinstance(content, list):
                content = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
            if role == "system":
                # Client-supplied system messages are dropped: the instructions come only from SYSTEM_PROMPT.
                continue
            elif role == "assistant":
                out.append(AIMessage(content=content or ""))
            else:
                out.append(HumanMessage(content=content or ""))
        return out

    def predict(self, req: ResponsesAgentRequest) -> ResponsesAgentResponse:
        result = self._graph().invoke({"messages": self._to_lc(req)})
        final = ""
        for m in reversed(result["messages"]):
            if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                final = m.content if isinstance(m.content, str) else str(m.content)
                break
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=final, id=str(uuid.uuid4()))]
        )

    def predict_stream(self, req: ResponsesAgentRequest) -> Generator[ResponsesAgentStreamEvent, None, None]:
        for item in self.predict(req).output:
            yield ResponsesAgentStreamEvent(type="response.output_item.done", item=item)


mlflow.langchain.autolog()
mlflow.models.set_model(AppealsChatAgent())
