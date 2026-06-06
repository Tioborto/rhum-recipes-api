## ADDED Requirements

### Requirement: Update Theme Preference
The system SHALL allow authenticated users to update their theme preference to one of the supported values: `light`, `dark`, or `system`.

#### Scenario: Valid theme update
- **WHEN** an authenticated user submits a request to update their theme to `dark`
- **THEN** the system updates the user's stored preference
- **THEN** the system returns a success response with the updated preference

#### Scenario: Invalid theme update
- **WHEN** an authenticated user submits a request to update their theme to an unsupported value (e.g., `neon`)
- **THEN** the system rejects the request with a 400 Bad Request error
- **THEN** the system's stored preference remains unchanged

### Requirement: Retrieve Theme Preference
The system SHALL return the user's configured theme preference when their profile or settings are requested.

#### Scenario: Fetch user profile
- **WHEN** an authenticated user fetches their profile information
- **THEN** the system includes the `theme` preference in the response payload
- **THEN** the `theme` value is either `light`, `dark`, or `system` (defaulting to `system` if not previously set)
