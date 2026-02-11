"""
Dependency Injection Module
============================

Exports the DI container.
"""

from .container import Container, get_container

__all__ = ["Container", "get_container"]
