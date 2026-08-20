# ============================================================
# app/main.py
# AI Safety Guardrails API — Day 38
# ============================================================

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.validators import InputValidator
from app.filters import OutputFilter
from app.red_team import RedTeamRunner
from app.bias_tests import BiasTestRunner
from app.guardrail_pipeline import GuardrailPipeline
from app.schemas import GuardrailCheckRequest, AIRequestWithGuardrails

_validator: InputValidator = None
_filter: OutputFilter = None
_red_team: RedTeamRunner = None
_bias_runner: BiasTestRunner = None
_pipeline: GuardrailPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _validator, _filter, _red_team, _bias_runner, _pipeline

    print("\n" + "=" * 60)
    print("  AI Safety: Guardrails & Red-Teaming — Day 38")
    print("=" * 60)

    _validator = InputValidator()
    _filter = OutputFilter()
    _red_team = RedTeamRunner()
    _bias_runner = BiasTestRunner()
    _pipeline = GuardrailPipeline()

    mode = "Mock LLM" if _pipeline.mock else "Real Claude API"
    print(f"\n  LLM mode: {mode}")
    print(f"  Red-team suite: 25 cases")
    print(f"  Bias test suite: {8} pairs")
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="AI Safety: Guardrails & Red-Teaming",
    description="""
## 🛡️ AI Safety System — Day 38

Production-grade guardrail system with red-team testing.

### Architecture