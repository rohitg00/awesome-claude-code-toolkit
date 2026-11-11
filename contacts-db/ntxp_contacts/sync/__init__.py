"""Bi-directional CRM sync: engine, adapter interface, and adapters."""
from .base import CrmAdapter, RemoteRecord, LocalChange, PushResult

__all__ = ["CrmAdapter", "RemoteRecord", "LocalChange", "PushResult"]
