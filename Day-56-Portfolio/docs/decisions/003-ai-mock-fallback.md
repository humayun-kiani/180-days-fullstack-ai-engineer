# ADR-003: Keyword Mock Fallback for AI Features

**Date:** 2025-05-27  
**Status:** Accepted

## Context

AI features require an Anthropic API key. Requiring it for local dev,
CI, and demos creates friction and cost.

## Decision

All AI functions check for API key first. If absent or if the call fails,
return a keyword-based mock response.

## Mock Logic