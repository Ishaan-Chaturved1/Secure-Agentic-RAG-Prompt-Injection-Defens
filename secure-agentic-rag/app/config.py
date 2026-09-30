"""
Application configuration for the Secure Agentic RAG system.

Supports two modes:
  - baseline: deliberately vulnerable, for measuring attack success
  - hardened: defense-in-depth with layered security controls

All secrets are synthetic / fake. No real credentials are ever loaded.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Set

from dotenv import load_dotenv

load_dotenv()

from pydantic import Field
from pydantic_settings import BaseSettings


class AgentMode(str, Enum):
    BASELINE = "baseline"
    HARDENED = "hardened"


class SecurityLayerFlags(BaseSettings):
    """Fine-grained toggles for individual security layers (ablation study)."""

    input_guard: bool = Field(default=True, description="Enable input injection detector")
    untrusted_boundary: bool = Field(
        default=True, description="Mark retrieved docs as untrusted in prompt"
    )
    structured_output: bool = Field(
        default=True, description="Require Pydantic-validated tool requests"
    )
    tool_policy: bool = Field(default=True, description="Enforce tool allowlist / authorization")
    argument_validation: bool = Field(default=True, description="Validate tool arguments")
    output_guard: bool = Field(default=True, description="Run output guardrail")

    class Config:
        env_prefix = "SEC_"


class Settings(BaseSettings):
    """Top-level application settings."""

    # --- Mode ---
    mode: AgentMode = Field(default=AgentMode.HARDENED, description="Agent operating mode")

    # --- Paths ---
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    data_dir: Optional[Path] = Field(default=None)
    log_dir: Optional[Path] = Field(default=None)
    report_dir: Optional[Path] = Field(default=None)

    # --- Model ---
    llm_backend: str = Field(
        default="mock",
        description="LLM backend: 'mock', 'ollama', or 'openai-compatible'",
    )
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1:8b")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="sentence-transformers model name",
    )

    # --- RAG ---
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)
    retriever_top_k: int = Field(default=5)
    vector_store: str = Field(default="faiss", description="'faiss' or 'chroma'")

    # --- Security ---
    security: SecurityLayerFlags = Field(default_factory=SecurityLayerFlags)

    # --- Tool policy ---
    rag_read_only_tools: Set[str] = Field(
        default={"search_documents", "get_document"},
        description="Tools permitted for normal RAG queries",
    )
    all_registered_tools: Set[str] = Field(
        default={
            "search_documents",
            "get_document",
            "mock_delete_file",
            "mock_send_email",
            "mock_read_secret",
            "mock_database_delete",
            "mock_http_request",
        }
    )

    # --- Fake secrets (NEVER real) ---
    fake_api_key: str = "FAKE_SECRET_FOR_SECURITY_TESTING_ONLY"
    fake_db_password: str = "FAKE_DB_PASSWORD_NOT_REAL"
    fake_admin_token: str = "FAKE_ADMIN_TOKEN_TESTING"

    # --- Llama Guard (optional) ---
    llama_guard_enabled: bool = Field(default=False)
    llama_guard_model: str = Field(default="llama-guard3:1b")

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_prefix = "RAG_"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def model_post_init(self, __context) -> None:
        if self.data_dir is None:
            object.__setattr__(self, "data_dir", self.project_root / "data")
        if self.log_dir is None:
            object.__setattr__(self, "log_dir", self.project_root / "logs")
        if self.report_dir is None:
            object.__setattr__(self, "report_dir", self.project_root / "reports")

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)


def get_settings(**overrides) -> Settings:
    """Factory that returns Settings, merging env vars and explicit overrides."""
    return Settings(**overrides)


# Convenience: baseline preset
def baseline_settings(**overrides) -> Settings:
    """Return settings pre-configured for the VULNERABLE baseline."""
    defaults = dict(
        mode=AgentMode.BASELINE,
        security=SecurityLayerFlags(
            input_guard=False,
            untrusted_boundary=False,
            structured_output=False,
            tool_policy=False,
            argument_validation=False,
            output_guard=False,
        ),
    )
    defaults.update(overrides)
    return Settings(**defaults)


def hardened_settings(**overrides) -> Settings:
    """Return settings pre-configured for the HARDENED agent."""
    defaults = dict(
        mode=AgentMode.HARDENED,
        security=SecurityLayerFlags(
            input_guard=True,
            untrusted_boundary=True,
            structured_output=True,
            tool_policy=True,
            argument_validation=True,
            output_guard=True,
        ),
    )
    defaults.update(overrides)
    return Settings(**defaults)
