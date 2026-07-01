# ADR 001: Retrieval Strategy Agent

## Context
The current retrieval flow sends every query through all available retrievers. That is simple, but it creates unnecessary work, increases latency, and makes the retrieval layer harder to evolve as the system grows.

As more retrievers are added, the cost of always running everything becomes more obvious:
- queries pay for strategies they do not need,
- retrievers become tightly coupled to the orchestration flow,
- and it becomes harder to introduce smarter routing logic without rewriting the retrieval pipeline.

## Problem
We need a way to decide which retrieval strategy should handle a query before the actual retrieval step runs.

The key requirement is that this component should only choose the strategy. It should not fetch documents, rank results, or merge outputs. Keeping that responsibility narrow makes the design easier to reason about and prepares the system for later orchestration features.

## Decision
Introduce a Retrieval Strategy Agent whose sole job is to select the most appropriate retrieval strategy for a given query.

This agent will:
- inspect the user query and any lightweight context available at routing time,
- choose one retrieval strategy or routing path,
- and pass that decision to the downstream retrieval pipeline.

This agent will not:
- execute the retrievers itself,
- combine retrieval results,
- or perform response generation.

## Why this approach
This design gives us a clean separation between decision-making and execution.

Benefits include:
- lower coupling between retrievers and the orchestration layer,
- easier addition of new retrievers or routing rules,
- reduced wasted work on queries that only need one strategy,
- and a foundation for future planning, reflection, and adaptive routing agents.

## Consequences
### Positive
- The retrieval layer becomes more modular.
- Strategy selection can improve independently from retrieval execution.
- The system can evolve toward more intelligent query routing over time.

### Trade-offs
- The agent adds one more step to the request path.
- Strategy selection logic must be maintained and evaluated.
- Incorrect routing could reduce retrieval quality if the agent makes poor choices.

## Notes
This ADR intentionally keeps the first version of the agent narrow. The goal is not to build a full planner yet, but to establish a stable abstraction for future enhancements.
