# Armaturenbrett UI

A modern Next.js frontend application that serves as the visual dashboard for the Franz Ticketing Service. The name "armaturenbrett" (German for "dashboard") reflects its role as the central hub for monitoring and administrating tickets.

## Features

- **Next.js App Router:** Built with React Server Components for optimal performance and modern routing.
- **Visual Analytics:** Integrates `recharts` to render real-time KPIs:
  - Total Tickets processed
  - Ticket distribution by Priority (Critical, High, Medium, Low)
  - Ticket breakdown by Category (e.g., Technical, Billing)
  - Origin comparison (Discord vs Email)
- **Live Feed Table:** Displays the latest annotated tickets in an interactive data table.
- **Premium Aesthetics:** Uses Shadcn UI components and Tailwind CSS entirely styled in Dark Mode.

## Architecture

1.  **Backend Target:** Reaches out to the `armaturenbrett-api` backend to fetch raw analytical data and paginated tickets.
2.  **State Management:** Utilizes React hooks (`useEffect`, `useState`) to poll the API on an interval, keeping the UI perpetually synchronized without manual refreshes.

## Configuration

The frontend connects directly to the API endpoint. In a standard Docker Compose deployment, this is typically resolved to the local mapping (e.g., `http://localhost:8000/api`).

## Local Development

Ensure the `armaturenbrett-api` is running, then you can start the UI in development mode:

```bash
npm install
npm run dev
```

The server will be available at `http://localhost:3000`.
