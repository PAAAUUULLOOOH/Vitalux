"""Resolve the preferred physical GPU without hiding any other device."""
from . import settings
from .monitoring import GpuHistory


def ordered(gpus):
    result = list(gpus or [])
    preferred = settings.observed('primary_gpu', '')
    for index, gpu in enumerate(result):
        if preferred and GpuHistory.identity(gpu, index) == preferred:
            result.insert(0, result.pop(index))
            break
    return result
