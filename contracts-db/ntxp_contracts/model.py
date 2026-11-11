"""In-memory dataclasses passed between importers, the repository and the API.

These mirror — but stay decoupled from — the SQL schema, so importers and
callers never touch SQL. Anything irreducibly variable per contract lives in
the ``attrs`` JSON bag, keeping the table itself stable while the model stays
adaptable (the "modular" requirement).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import DEFAULT_RECIPIENT


@dataclass
class OwnerEntity:
    """The contracting authority / owner that issued the contract — and the
    contact info the per-contract profile screen needs (website plus customer
    service and accounting lines for click-to-call/text and a contact file)."""
    name: str
    name_norm: str = ""
    website: str | None = None
    main_phone: str | None = None
    customer_service_phone: str | None = None
    accounting_phone: str | None = None
    email: str | None = None
    address: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Contract:
    """One Job Order / Cooperative / Master Subcontract Agreement."""
    # Identity / classification
    contract_title: str
    contract_no: str | None = None          # contract / RFP #
    contract_type: str | None = None        # see config.CONTRACT_TYPES

    # Parties
    owner_entity: str | None = None         # name of issuing authority
    recipient: str = DEFAULT_RECIPIENT      # always NTXP LLC by default

    # Where / how big
    location: str | None = None
    estimated_budget: float | None = None

    # Lifecycle
    award_date: str | None = None           # ISO yyyy-mm-dd
    duration: str | None = None             # free text, e.g. "1 yr + 4 renewals"
    expiration_date: str | None = None      # ISO yyyy-mm-dd

    # Commercials
    coefficient_multiplier: float | None = None
    cooperative_fee: str | None = None      # e.g. "2%" or "$0"

    # Scope + freeform
    allowable_scope: str | None = None      # comma/segmented scope terms
    notes: str | None = None

    # Signed copy
    pdf_url: str | None = None              # live link to the signed PDF
    is_executed: bool = False              # False => flagged as unexecuted

    # Anything extra without a schema change.
    attrs: dict[str, Any] = field(default_factory=dict)

    # Provenance
    source: str = "manual"
    source_pk: str | None = None


@dataclass
class Job:
    """A job performed under a contract — the unit the profile screen rolls up
    into a job list and total-sales figure. Synced from the jobs system
    (JobTread) into a local cache so the DB stays pollable offline."""
    contract_no: str
    name: str
    customer: str | None = None
    status: str | None = None
    contract_value: float | None = None
    sales_amount: float | None = None       # invoiced / recognized sales
    source: str = "jobtread"
    external_id: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
