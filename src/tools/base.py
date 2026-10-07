"""Tool registry and helper functions."""

from typing import List
from langchain_core.tools import BaseTool
from src.tools.knowledge_tools import lookup_knowledge_base
from src.tools.system_tools import check_system_status


def get_triage_tools() -> List[BaseTool]:
    """Returns the list of available tools bound to the triage agent."""
    return [lookup_knowledge_base, check_system_status]
