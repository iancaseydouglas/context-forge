from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from pathlib import Path

class RepoConfig(BaseModel):
    """
    Immutable configuration for a single repository target.
    Defines where the code lives and how it should be processed.
    """
    model_config = ConfigDict(frozen=True)
    
    path: Path
    role: str = Field(..., description="'active' for read/write, 'reference' for read-only")
    strategy: str = Field(..., description="'full' (fidelity), 'stub' (python interface), or 'compress' (tree-sitter)")
    language: str = Field(..., description="'python' or 'typescript'")

class ForgeState(BaseModel):
    """
    The Global State Monad.
    
    In the Split-State Functional architecture, this object represents the 
    entire reality of the application at a single moment in time. 
    It is never mutated in place; functions return a new copy (a state transition).
    """
    model_config = ConfigDict(frozen=True)

    # --- Inputs ---
    active_repo: RepoConfig
    vbt_repo: RepoConfig
    charts_repo: RepoConfig
    
    # --- Artifact Paths (Computed during pipeline execution) ---
    vbt_stub_path: Optional[Path] = None
    charts_interface_path: Optional[Path] = None
    merged_context_path: Optional[Path] = None
    
    # --- Remote State (Gemini API) ---
    google_api_key: Optional[str] = None
    cache_name: Optional[str] = None
    cache_expire_time: Optional[str] = None
    
    # --- Diagnostics ---
    logs: List[str] = Field(default_factory=list)
    error: Optional[str] = None

    def add_log(self, message: str) -> ForgeState:
        """Functional appender: Returns a NEW state with the log added."""
        new_logs = self.logs + [message]
        return self.model_copy(update={"logs": new_logs})

    def fail(self, error_msg: str) -> ForgeState:
        """Short-circuit mechanism: Returns a NEW state marked as failed."""
        return self.model_copy(update={"error": error_msg})

    @property
    def is_valid(self) -> bool:
        """Predicate to check if the pipeline should continue."""
        return self.error is None