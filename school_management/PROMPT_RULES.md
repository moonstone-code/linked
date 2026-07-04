# Prompt Rules

Use these rules for all implementation and data-access tasks in this project.

## Mandatory Rules

1. Never return all records.
2. Always filter data using the logged-in user's role, reference_id, and assignment mappings.

## Enforcement Notes

- Apply these filters in every list/query endpoint, report, and dashboard dataset.
- Restrict visibility by role:
  - Admin: full scope as per assigned admin capabilities.
  - Teacher: assigned classes/students only.
  - Parent: linked child data only.
  - Student: own data only.
- If role mapping or reference_id is missing, return no data by default (fail closed).
