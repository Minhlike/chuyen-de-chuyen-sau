# -*- coding: utf-8 -*-
"""Package huấn luyện cho mô hình tự giám sát (self-supervised model) (self-supervised model) (self-supervised model) Chương 3."""

from .stage_a2_trainer import (
    StageA2Trainer,
    EmpiricalExecutionNotAuthorizedError,
    CheckpointBoundaryViolationError
)

__all__ = [
    "StageA2Trainer",
    "EmpiricalExecutionNotAuthorizedError",
    "CheckpointBoundaryViolationError"
]
