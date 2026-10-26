"""An optional background lookup must retain a useful failure reason."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkResult:
    value: object = None
    error: str = ''
    stage: str = ''

    @classmethod
    def perform(cls, stage, operation):
        try:
            return cls(operation(), stage=stage)
        except Exception as error:
            return cls(error=f'{type(error).__name__}: {error}', stage=stage)
