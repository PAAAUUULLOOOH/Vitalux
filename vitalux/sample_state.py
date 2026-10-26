"""Shared identities and freshness states for sampled data, independent of Qt."""
from dataclasses import dataclass, replace
import math


@dataclass(frozen=True)
class SamplingState:
    received: float|None = None
    error: str = ''

    def success(self, now):return SamplingState(now)
    def failed(self, error):return replace(self,error=str(error))
    def stale(self, now, interval):
        return bool(self.error) or self.received is not None and now-self.received>max(4.5,interval*2.5)


@dataclass(frozen=True)
class SensorReading:
    identity: str
    name: str
    value: float|None
    unit: str
    source: str

    @classmethod
    def from_record(cls, row):
        value=row.get('value')
        try:value=float(value) if not isinstance(value,bool) else None
        except (ValueError,TypeError,OverflowError):value=None
        if value is not None and not math.isfinite(value):value=None
        return cls(str(row.get('id') or row['name']),str(row['name']),value,
                   str(row.get('unit','')),str(row.get('source','')))
