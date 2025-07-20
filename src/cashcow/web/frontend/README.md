# CashCow Web Frontend

A React-based web interface for the CashCow financial modeling and cash flow management system.

## Features

- **Dashboard**: Overview of key financial metrics and KPIs
- **Entity Management**: Create, edit, and manage financial entities (revenue sources, expenses, projects)
- **Reports & Analysis**: Cash flow forecasting, Monte Carlo analysis, what-if scenarios
- **Real-time Updates**: WebSocket integration for live data updates
- **Responsive Design**: Mobile-friendly interface using Material-UI
- **Mock Data Mode**: Development mode with sample data for frontend development

## Tech Stack

- **React 18** with TypeScript
- **Material-UI v6** for UI components and theming
- **React Router** for navigation
- **Chart.js** with react-chartjs-2 for data visualization
- **React Hook Form** for form management and validation
- **Axios** for API communication
- **WebSocket** support for real-time updates

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- CashCow backend API running (optional - mock mode available)

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Configure environment variables in `.env`:
   - Set `REACT_APP_API_BASE_URL` to your backend API URL
   - Set `REACT_APP_MOCK_MODE=true` for development without backend

### Development

Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`.

### Production Build

Create a production build:
```bash
npm run build
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Layout/          # Layout components (Header, Sidebar, etc.)
│   ├── Forms/           # Form components and field types
│   ├── Charts/          # Chart and visualization components
│   └── *.tsx            # Other shared components
├── pages/               # Page components
├── services/            # API and data services
├── types/               # TypeScript type definitions
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
└── App.tsx             # Main application component
```

## Entity Types

The application supports revenue entities (grants, investments, sales, services), expense entities (employees, facilities, software, equipment), and project entities.

## Configuration

Configure the application using environment variables in `.env`:
- `REACT_APP_API_BASE_URL`: Backend API URL
- `REACT_APP_MOCK_MODE`: Enable mock data mode for development

## Available Scripts

### `npm start`

Runs the app in the development mode at [http://localhost:3000](http://localhost:3000).

### `npm test`

Launches the test runner in interactive watch mode.

### `npm run build`

Builds the app for production to the `build` folder with optimized performance.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

Ejects from Create React App to expose configuration files.
