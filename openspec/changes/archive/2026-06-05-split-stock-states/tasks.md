## 1. Database Model Updates

- [x] 1.1 Add `maceration_time_days: int | None` to the `Recipe` model in `models.py`.
- [x] 1.2 Add `preparation_date: date | None` to the `StockEntry` model in `models.py` (defaults to today for new `in_preparation` entries).
- [x] 1.3 Create and apply an Alembic migration (or handle via SQLModel) to add these columns.

## 2. API Schema Updates

- [x] 2.1 Update `RecipeCreate`, `RecipeUpdate`, and `RecipeRead` to include `maceration_time_days`.
- [x] 2.2 Update `StockEntryCreate`, `StockEntryUpdate`, and `StockEntryRead` to include `preparation_date`.

## 3. Endpoints Updates

- [x] 3.1 Ensure the `/api/v1/stock/` endpoints properly accept and persist `preparation_date`.

## 4. Testing & Validation

- [x] 4.1 Update `tests/test_recipes.py` to cover `maceration_time_days`.
- [x] 4.2 Update `tests/test_stock.py` to verify that `preparation_date` is properly saved and returned.
