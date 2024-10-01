from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str) -> AgentExecutor:
    """Create a function-calling agent and add it to the graph."""
    system_prompt += "\nWork autonomously according to your specialty, using the tools available to you."
    " Do not ask for clarification."
    " Your other team members (and other teams) will collaborate with you with their own specialties."
    " You are chosen for a reason! You are one of the following team members: {team_members}."
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor

def create_team_supervisor(llm: ChatOpenAI, members: list, system_prompt: str) -> JsonOutputFunctionsParser:
    """An LLM-based router."""
    if not isinstance(members, list):
        raise TypeError("members must be a list")
    
    options = ["FINISH"] + members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "type": "string",
                    "enum": options,
                    "description": "The next role to execute.",
                }
            },
            "required": ["next"],
        },
    }
    
    system_prompt += "\nWork autonomously according to your specialty, using the tools available to you."
    system_prompt += " Do not ask for clarification."
    system_prompt += " Your other team members (and other teams) will collaborate with you with their own specialties."
    system_prompt += " You are chosen for a reason! You are one of the following team members: {team_members}."
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    
    agent = create_openai_functions_agent(llm, [], prompt)
    executor = AgentExecutor(agent=agent, tools=[])
    return executor