"""NTXP Master Contracts database.

One adaptable, modular SQLite source of truth for every contract NTXP works
under — Job Order Contracts, Cooperative Contracts, and Master Subcontract
Agreements — that any other NTXP tool can poll for reference data (coefficient
multipliers, cooperative fees, expiration dates, allowable scope, the signed
PDF, owner-entity contact info, and jobs/sales rolled up per contract).

Access layers over one core: Python API, the ``ntxp-contracts`` CLI, an MCP
server (so Claude-based NTXP tools query it directly), and a zero-dependency
web dashboard with an inline-editable contract log and per-contract profile.
"""
from __future__ import annotations

__version__ = "0.1.0"
