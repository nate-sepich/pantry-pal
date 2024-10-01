import functools
from typing import Annotated, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from services.document_manager import DocumentManager, EditOperation, DocumentContent
from langgraph.graph import END, StateGraph, START
import operator
from dotenv import load_dotenv
from utils import prelude  # Updated import

load_dotenv()

# Document writing team graph state
class DocWritingState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    team_members: str
    next: str
    current_files: str

# Function to set up the authoring graph
def setup_authoring_graph(authoring_graph):
    from agents.agents import doc_writing_node, note_taking_node, chart_generating_node, doc_writing_supervisor
    authoring_graph.add_node("DocWriter", doc_writing_node)
    authoring_graph.add_node("NoteTaker", note_taking_node)
    authoring_graph.add_node("ChartGenerator", chart_generating_node)
    authoring_graph.add_node("supervisor", doc_writing_supervisor)
    # Add other nodes and edges as needed
    return authoring_graph

# Create the shared state graph with the input of a DocWritingState
authoring_graph = StateGraph(DocWritingState)
authoring_graph = setup_authoring_graph(authoring_graph)

# Add the edges that always occur
authoring_graph.add_edge("DocWriter", "supervisor")
authoring_graph.add_edge("NoteTaker", "supervisor")
authoring_graph.add_edge("ChartGenerator", "supervisor")

# Add the edges where routing applies
authoring_graph.add_conditional_edges(
    "supervisor",
    lambda x: x["next"],
    {
        "DocWriter": "DocWriter",
        "NoteTaker": "NoteTaker",
        "ChartGenerator": "ChartGenerator",
        "FINISH": END,
    },
)

authoring_graph.add_edge(START, "supervisor")
chain = authoring_graph.compile()

def enter_chain(message: str, members: List[str]) -> DocWritingState:
    results = {
        "messages": [message],
        "team_members": members,
        "next": "",
        "current_files": ""
    }
    return DocWritingState(**results)

# We reuse the enter/exit functions to wrap the graph
authoring_chain = (
    functools.partial(enter_chain, members=authoring_graph.nodes)
    | authoring_graph.compile()
)


# Example usage
if __name__ == "__main__":
    manager = DocumentManager()
    
    for s in authoring_chain.stream(
        "Write an outline for a SUPER spooky poem and then write the poem to disk.",
        {"recursion_limit": 100},
    ):
        if "__end__" not in s:
            print(s)
            print("---")