# LEGACY

LEGACY is a real estate intelligence platform for managing properties, importing county/property data, researching markets, tracking buyer activity, and turning deal evidence into better decisions.

## First Build Goal

The first version should stay simple and stable:

1. Login-ready app structure
2. Leads dashboard
3. Add/edit/delete leads
4. Pipeline stages
5. Lead detail page with notes
6. PDF upload placeholder
7. Clean backend API foundation

Advanced features like AI parsing, maps, SMS, phone calls, and property intelligence should come after the core CRM works.

## Project Structure

```text
legacy/
  frontend/   React + Vite app
  backend/    FastAPI app
  docs/       planning notes and blueprint breakdown
```

## Beginner Notes

- The frontend is what you see and click.
- The backend is the server that stores and sends data.
- The database will hold leads, users, notes, reminders, and imported files.
- We will build this in phases so problems are easier to find and fix.
