# Batch Tracking

## Purpose
Track multiple independent stock batches (jars/bottles) concurrently for the same recipe or product. Each batch has its own preparation date, enabling the frontend to compute estimated readiness based on the recipe's maceration time.

## Requirements

### Requirement: Define Maceration Time for Recipes
The system SHALL allow users to define a required maceration time for a recipe.

#### Scenario: Creating a recipe with maceration time
- **WHEN** a user creates or updates a recipe with `maceration_time_days = 90`
- **THEN** the system stores the maceration time on the recipe

### Requirement: Track Preparation Date for Stock Entries
The system SHALL allow users to define the date a stock batch was put into preparation.

#### Scenario: Starting a new batch
- **WHEN** a user creates a stock entry with `state = in_preparation` and `preparation_date = 2026-01-01`
- **THEN** the system saves the preparation date, allowing frontend clients to compute estimated ready dates based on the recipe's maceration time.

### Requirement: Group Batches by Recipe (Client-side enabling)
The system SHALL allow fetching multiple distinct stock batches for the same recipe to enable unified product views on the frontend.

#### Scenario: Fetching all batches for a recipe
- **WHEN** a user fetches stock entries filtered by `recipe_id`
- **THEN** the system returns all batches (both `ready` and `in_preparation`) associated with that recipe
