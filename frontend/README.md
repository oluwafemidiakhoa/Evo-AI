# Evo-AI Frontend

Next.js 14 frontend for the Evo-AI experimental evolution platform.

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** (strict mode)
- **Tailwind CSS** for styling
- **shadcn/ui** component library
- **SWR** for data fetching
- **Recharts** for charts
- **D3.js** for lineage visualization

## Getting Started

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   └── types/            # TypeScript types
├── public/               # Static assets
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking

## Environment Variables

See `.env.example` for required environment variables.

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000` by default.

Configure via `NEXT_PUBLIC_API_URL` environment variable.
