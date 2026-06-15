from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


class SchedulerTaskRun(SQLModel, table=True):
    __tablename__ = "scheduler_task_runs"

    function_path: str = Field(primary_key=True, max_length=512)
    last_run_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
