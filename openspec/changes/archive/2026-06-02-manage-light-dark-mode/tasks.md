## 1. Database & Schema Updates

- [x] 1.1 Update user schema/model to include a `theme` string field with a default value of `system`
- [x] 1.2 Create and apply database migration if necessary

## 2. API Implementation

- [x] 2.1 Update user profile payload response to include the `theme` field
- [x] 2.2 Create or update the user settings endpoint (e.g., `PATCH /api/users/me` or `/api/users/me/settings`) to accept a `theme` property
- [x] 2.3 Add payload validation to the endpoint to strictly enforce `light`, `dark`, or `system` values
- [x] 2.4 Ensure the updated `theme` preference is correctly saved to the database

## 3. Testing

- [x] 3.1 Write unit tests for the endpoint validation logic
- [x] 3.2 Write integration tests to ensure the theme preference is successfully updated and correctly retrieved in subsequent requests
