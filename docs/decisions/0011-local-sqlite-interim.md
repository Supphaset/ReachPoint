# 0011 — Temporary local SQLite persistence

Date: 2026-10-13 (Asia/Bangkok). Status: **Accepted by the user for local development.**
Human approval reference: the user asked to use SQLite until an actual database is added, then chose to persist all changing demo state, including coordinator approvals, team actions and status updates.

## Decision

An explicit `REACHPOINT_DB_PATH` enables a local SQLite file. The API saves the current operational snapshot and retry results after each accepted write, the deterministic flood replay cursor, and unfinished caller conversations. It restores them after a process restart. The browser still stores only a session identifier. Without this setting, the existing in-memory demo behavior remains.

This is a single-process local bridge, not a change to the selected shared deployment database in [0009](0009-implementation-start-and-technical-direction.md). The file stays outside Git and contains synthetic demo information only. The demo reset clears it. Raw audio is streamed to Gemini Live but not saved by this adapter.

## Why and limits

The caller's confirmed report and its status link need to remain usable after restarting the local server. Saving the full operational snapshot keeps coordinator and team updates consistent with that report while the final database is unfinished. The API routes and rule methods stay the same.

SQLite on a local Cloud Run filesystem is not durable across instance replacement and cannot coordinate multiple server processes. Authentication, retention policy for submitted reports, and the role-filtered shared views remain deployment work. The local demo must not receive real household or medical information.
