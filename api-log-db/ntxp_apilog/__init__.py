"""NTXP API Log — one shared registry of API endpoints, credentials, and cost.

A single source of truth for every API used across NTXP tools: base URL, key
number, login info, and running cost. Three access layers over one SQLite file:
a Python API, the ``ntxp-apilog`` CLI, an NTXP-branded HTML dashboard, and an
MCP server so Claude can look up (and fill in) credentials the moment a system,
skill, or user asks for an API.
"""

__version__ = "0.1.0"
