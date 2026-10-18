# 0012 — Retire classic and keep the v2 runtime

Date: 2026-10-18 (Asia/Bangkok).
Status: **Accepted user instruction; implementation awaits normal human PR review.**
Human approval reference: the repository owner's answer in the cleanup chat: “Retire classic; make the repo v2-only”.

## Context and evidence

V2 is the judging entry point, but the browser still bundled classic routes and fixtures, and every room
constructed a classic MemoryStore and FloodReplay. These paths retained the old review/dispatch UI,
solver, ADK triage agent and notebook dependencies. V2 itself uses its own intake, pipeline, plans and
persistence, plus shared Gemini/budget/usage, Pinpoint and room infrastructure.

## Decision

Remove classic frontend screens, API handlers, stores, exclusive tests, fixture payloads and offline
classic scenario/solver tools. Stop loading classic state during server startup and room construction.
Keep v2 routes and behavior, shared health/config endpoints, security limits, browser voice, room
persistence, flood inputs, source provenance and data preparation/evaluation tools required by v2.
Move the shared key-model list out of classic extraction into the Gemini module.

Historical specifications, decisions, research and QA reports remain available. Links to removed files
point to the pre-cleanup revision where appropriate. The geography catalogue fixture remains because
retained geography preparation/tests still consume it. The earlier v2 trip page is also v2 code and
remains at its existing route; it does not load classic code.

## Rationale and alternatives

Keeping disabled classic handlers would preserve two implementations and unnecessary dependencies.
Removing only browser navigation would leave backend startup and bundled fixtures behind. The user
chose the v2-only alternative explicitly; removing v2 features or historical source evidence is outside
this cleanup.

## Consequences and affected documents

Classic URLs no longer provide their former workflows: browser paths fall back to the v2 overview,
and retired API paths return 404. Restore historical code from Git if needed. No deployment, provider,
paid feature, state semantics or public-data permission is introduced by this decision.

The current runtime is documented in the [v2 code map](../planning/v2-code-map.md), root README,
web README and requirements. Implementation changes remain on the cleanup branch for review.
