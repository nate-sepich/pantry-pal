import datetime
from dotenv import load_dotenv
from models.document_models import DocumentContent, EditOperation
from typing import Dict, List
from pathlib import Path
import os

class DocumentManager:
    def __init__(self):
        load_dotenv()
        self.working_directory = Path(os.getcwd()) / 'doc_writing' / datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.working_directory.mkdir(parents=True, exist_ok=True)
        self.agents = {}

    def write_document(self, document: DocumentContent) -> str:
        file_path = self.working_directory / document.file_name
        with file_path.open("w") as file:
            file.write(document.content)
        return f"Document saved to {file_path}"

    def edit_document(self, edit: EditOperation) -> str:
        file_path = self.working_directory / edit.file_name
        with file_path.open("r+") as file:
            lines = file.readlines()
            for line_num, text in edit.inserts.items():
                lines.insert(line_num, text + "\n")
            file.seek(0)
            file.writelines(lines)
        return f"Document {file_path} edited successfully"

    def add_agent(self, agent_id: str, agent_name: str) -> str:
        self.agents[agent_id] = agent_name
        return f"Agent {agent_name} added with ID {agent_id}"

    def remove_agent(self, agent_id: str) -> str:
        if agent_id in self.agents:
            agent_name = self.agents.pop(agent_id)
            return f"Agent {agent_name} removed"
        else:
            return f"Agent ID {agent_id} not found"

    def list_agents(self) -> List[str]:
        return [f"{agent_id}: {agent_name}" for agent_id, agent_name in self.agents.items()]

    def assign_task(self, agent_id: str, task: str) -> str:
        if agent_id in self.agents:
            # Here you can implement task assignment logic
            return f"Task '{task}' assigned to agent {self.agents[agent_id]}"
        else:
            return f"Agent ID {agent_id} not found"