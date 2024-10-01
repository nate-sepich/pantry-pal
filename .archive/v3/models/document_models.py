from pydantic import BaseModel, Field
from typing import Dict, List

class DocumentContent(BaseModel):
    content: str = Field(..., description="Text content to be written into the document.")
    file_name: str = Field(..., description="File path to save the document.")

class EditOperation(BaseModel):
    file_name: str = Field(..., description="Path of the document to be edited.")
    inserts: Dict[int, str] = Field(..., description="Dictionary of line numbers and text to insert.")

class DocWritingState(BaseModel):
    messages: List[str]
    team_members: List[str]