import functools
from langchain_core.messages import HumanMessage
from langchain_openai.chat_models import ChatOpenAI
from agents.agent_utils import create_agent, create_team_supervisor
from services.document_tools import write_document, edit_document, read_document, create_outline, python_repl
from utils import prelude

def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

doc_writer_agent = create_agent(
    llm,
    [write_document, edit_document, read_document],
    "You are an expert writing a research document.\n"
    "Below are files currently in your directory:\n{current_files}",
)
context_aware_doc_writer_agent = prelude | doc_writer_agent
doc_writing_node = functools.partial(
    agent_node, agent=context_aware_doc_writer_agent, name="DocWriter"
)

note_taking_agent = create_agent(
    llm,
    [write_document, edit_document, read_document],
    "You are an expert taking notes for a research document.\n"
    "Below are files currently in your directory:\n{current_files}",
)
note_taking_node = functools.partial(
    agent_node, agent=note_taking_agent, name="NoteTaker"
)

chart_generating_agent = create_agent(
    llm,
    [create_outline, python_repl],
    "You are an expert generating charts for a research document.\n"
    "Below are files currently in your directory:\n{current_files}",
)
context_aware_chart_generating_agent = prelude | chart_generating_agent
chart_generating_node = functools.partial(
    agent_node, agent=context_aware_chart_generating_agent, name="ChartGenerator"
)

doc_writing_supervisor_agent = create_team_supervisor(
    llm,
    [doc_writer_agent, note_taking_agent, chart_generating_agent],
    "You are supervising the document writing process.\n"
    "Below are files currently in your directory:\n{current_files}",
)
context_aware_doc_writing_supervisor_agent = prelude | doc_writing_supervisor_agent
doc_writing_supervisor = functools.partial(
    agent_node, agent=context_aware_doc_writing_supervisor_agent, name="DocWritingSupervisor"
)

# Export the nodes
__all__ = [
    "doc_writing_node",
    "note_taking_node",
    "chart_generating_node",
    "doc_writing_supervisor"
]