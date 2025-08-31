# AIRMS Frontend

A modern, responsive frontend application for the AI Risk Management System (AIRMS) built with Next.js, TypeScript, and Chakra UI.

## Features

- **Modern UI/UX**: Built with Chakra UI for a professional, accessible interface
- **Responsive Design**: Mobile-first approach with responsive navigation
- **TypeScript**: Full type safety and better development experience
- **Real-time Monitoring**: Live risk detection and mitigation tracking
- **Comprehensive Dashboard**: Overview of system health, risks, and performance
- **Risk Analysis**: Detailed risk assessment with mitigation strategies
- **System Settings**: Configurable parameters for risk detection and system behavior

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **UI Library**: Chakra UI
- **Icons**: Lucide React
- **State Management**: React Query (TanStack Query)
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios
- **Styling**: CSS-in-JS with Chakra UI (no Tailwind CSS)

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Dashboard (home page)
│   │   ├── risk-analysis/     # Risk analysis page
│   │   ├── settings/          # System settings page
│   │   ├── layout.tsx         # Root layout with navigation
│   │   └── globals.css        # Global styles
│   ├── components/             # Reusable components
│   │   ├── Navigation.tsx     # Main navigation component
│   │   └── providers.tsx      # Chakra UI and React Query providers
│   └── ...
├── public/                     # Static assets
├── package.json               # Dependencies and scripts
└── README.md                  # This file
```

## Pages

### Dashboard (`/`)
- System overview with key metrics
- Real-time risk monitoring
- Quick action buttons
- System status indicators

### Risk Analysis (`/risk-analysis`)
- Comprehensive risk assessment
- Risk detection tables
- Mitigation strategy tracking
- Analytics and trends

### Settings (`/settings`)
- General system configuration
- Risk detection parameters
- Data source management
- Security settings

## Components

### Navigation
- Responsive sidebar navigation
- Mobile drawer for small screens
- Active page highlighting
- Branded header with logo

### Providers
- Chakra UI theme configuration
- React Query client setup
- Custom color scheme and components

## Customization

### Theme
The application uses a custom Chakra UI theme with:
- Brand colors (blue-based palette)
- Consistent component styling
- Light/dark mode support (configurable)

### Adding New Pages
1. Create a new directory in `src/app/`
2. Add a `page.tsx` file
3. Update the navigation in `components/Navigation.tsx`
4. Follow the existing page structure and styling patterns

### Adding New Components
1. Create components in `src/components/`
2. Use Chakra UI components for consistency
3. Follow TypeScript best practices
4. Include proper prop interfaces

## API Integration

The frontend is designed to integrate with the AIRMS backend API. Key areas for integration:

- Risk detection endpoints
- System configuration
- Data source management
- User authentication
- Real-time updates

## Development Guidelines

### Code Style
- Use TypeScript for all components
- Follow React best practices
- Use Chakra UI components consistently
- Implement proper error handling
- Add loading states for async operations

### Performance
- Use React Query for data fetching
- Implement proper memoization
- Optimize bundle size
- Use Next.js Image component for images

### Accessibility
- Follow WCAG guidelines
- Use semantic HTML
- Implement proper ARIA labels
- Ensure keyboard navigation

## Troubleshooting

### Common Issues

1. **Build Errors**: Ensure all dependencies are installed
2. **TypeScript Errors**: Check type definitions and imports
3. **Styling Issues**: Verify Chakra UI theme configuration
4. **Navigation Problems**: Check routing configuration

### Getting Help

- Check the Next.js documentation
- Review Chakra UI component library
- Check TypeScript configuration
- Verify all imports and dependencies

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Implement proper error handling
4. Add appropriate tests
5. Update documentation as needed

## License

This project is part of the AIRMS system. Please refer to the main project license.
