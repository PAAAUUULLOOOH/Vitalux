"""Authenticated GitHub CLI calls used only by release workflows."""
from pathlib import Path
import subprocess


def gh(*args,check=True):
    result=subprocess.run(['gh',*args],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
    if check and result.returncode:raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result
