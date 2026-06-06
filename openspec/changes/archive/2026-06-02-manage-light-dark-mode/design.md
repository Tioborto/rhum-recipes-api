## Context

The application currently lacks the ability to persist user preferences for UI themes (light vs. dark mode). As a result, users cannot maintain a consistent visual experience across sessions and devices.

## Goals / Non-Goals

**Goals:**
- Store the user's theme preference securely in the backend.
- Allow users to retrieve and update their theme preference (`light`, `dark`, `system`).
- Ensure the preference is included in the standard user profile/settings response.

**Non-Goals:**
- Handling the frontend implementation of CSS variables and toggles (this design focuses on the backend capability to store the preference).
- Support for complex custom themes beyond light/dark/system.

## Decisions

- **Storage Location:** We will store the `theme` preference as a field on the user settings or user profile entity in the database.
  - *Rationale:* It's a standard user-level configuration that is typically loaded upon application initialization. Adding it to the existing user record or settings avoids unnecessary joins.
- **Allowed Values:** The field will be restricted to an enum-like validation: `light`, `dark`, and `system`.
  - *Rationale:* `system` allows the frontend to fallback to `prefers-color-scheme` media queries, while `light` and `dark` force a specific theme.

## Risks / Trade-offs

- [Risk: Invalid values submitted by clients] → Mitigation: Implement strict payload validation on the API endpoint to reject any values other than `light`, `dark`, or `system`.
