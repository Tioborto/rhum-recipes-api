## Context

Users create multiple batches of the same rhum recipe over time. Each batch has its own start date, volume, and phase (e.g., in preparation vs. ready). The previous assumption that we could just sum up all "ready" and "in prep" quantities under a single flat `StockEntry` row breaks down because it destroys the timeline of when individual batches were started and when they will be ready. 

## Goals / Non-Goals

**Goals:**
- Allow multiple distinct `StockEntry` batches for the same recipe.
- Store a `preparation_date` for batches in preparation.
- Provide a way to associate a required `maceration_time_days` with a `Recipe`.
- Offload the responsibility of calculating the estimated ready date to the frontend UI.

**Non-Goals:**
- Tracking historical state transitions for a single jar.
- Backend calculation of estimated ready dates (this simplifies the API).

## Decisions

- **Decision: `StockEntry` represents a physical Batch, not the entire Product.**
  - **Rationale:** By allowing multiple `StockEntry` rows to share the same `recipe_id`, we naturally support tracking separate batches started at different times. No complex schema migrations to add `quantity_ready` and `quantity_in_prep` are needed. The UI will handle grouping these individual batches into a unified "Product" view.

- **Decision: Add `maceration_time_days` to `Recipe` and `preparation_date` to `StockEntry`.**
  - **Rationale:** Maceration time is an inherent property of the recipe (e.g. "let this sit for 3 months"). The specific start date is tied to the batch (`StockEntry`). By providing both of these raw values via the API, the UI client has all the information it needs to dynamically compute and display the "min date to be ready" without burdening the backend with date arithmetic and timezone complexities.

## Risks / Trade-offs

- [Risk: UI Grouping Complexity] → Mitigation: The frontend must do the heavy lifting to group `StockEntry` items by `recipe_id` to show a clean list, as well as calculating the readiness dates. This is generally an acceptable tradeoff as the backend remains simple and purely data-driven.
