# ADR 0001: Start with a modular monolith

- Status: accepted
- Date: 2026-07-16

## Decision

Deploy one FastAPI service while enforcing bounded-context and Clean Architecture boundaries in code. Use asynchronous jobs for slow and failure-prone workflows.

## Rationale

Early domain rules and data ownership will change. A modular monolith provides strong transactions, lower operating cost, and faster refactoring without preventing later extraction. A module may become a service only when measured scaling, availability, ownership, or regulatory needs justify the cost.

## Consequences

Architecture tests and code ownership must prevent cross-module coupling. Background work requires a durable outbox once persistence arrives in Phase 3.
