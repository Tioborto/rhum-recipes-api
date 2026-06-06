## Why

Users often create multiple distinct batches of the same rhum recipe at different times. For example, a user might have 5 liters macerating from January, another 4 liters started in June, and 5 bottles that are already ready to drink. A single flattened quantity cannot track these distinct timelines. Furthermore, knowing when a maceration is "ready" requires calculating an estimated date based on the recipe's specific maceration time.

## What Changes

- Add a `maceration_time_days` field to the `Recipe` model.
- Treat `StockEntry` conceptually as an individual "Batch" (a physical jar or set of bottles) rather than aggregating all inventory for a recipe into a single row.
- The API will dynamically calculate and return an `estimated_ready_date` for `in_preparation` stock entries, based on their start date (e.g., `purchase_date` or `created_at`) and the recipe's `maceration_time_days`.
- Add functionality to group and aggregate these individual `StockEntry` batches by `recipe_id` or `name`, providing a unified "Product Inventory" view for the frontend.

## Capabilities

### New Capabilities
- `batch-tracking`: Track multiple independent stock batches (jars/bottles) concurrently for the same recipe or product.
- `maceration-timer`: Define maceration times on recipes and calculate estimated ready dates for stock in preparation.

### Modified Capabilities

## Impact

- **Database Schema**: Add `maceration_time_days` to the `recipes` table.
- **API Endpoints**: 
  - Update recipe CRUD to handle `maceration_time_days`.
  - Update stock schemas to include `estimated_ready_date`.
  - (Optional) Provide a grouped `/api/v1/stock/grouped` endpoint or ensure the frontend can easily group by `recipe_id`.
- **Frontend Clients**: Will shift from a "one row per recipe" mental model to a "Product -> Batches" hierarchy.
