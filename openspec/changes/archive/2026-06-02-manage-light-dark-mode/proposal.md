## Why

Users currently cannot persist their preference for light or dark mode across sessions or devices. Supporting user preferences for themes improves accessibility and overall user experience by allowing them to choose a theme that suits their needs and environment.

## What Changes

- Add capability to store and retrieve user theme preferences (e.g., 'light', 'dark', 'system').
- Expose an API endpoint to update the theme preference.
- Include the theme preference in the user profile or settings payload.

## Capabilities

### New Capabilities
- `theme-preferences`: Manage user preferences for UI themes (light, dark, system).

### Modified Capabilities
- (None)

## Impact

- Database schema: Add a field or related table for user settings/theme preference.
- API endpoints: Update user profile and settings endpoints.
- Potential impact on frontend clients that need to consume this preference to apply the theme.
