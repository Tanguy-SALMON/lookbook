# Admin Dashboard Guide

## Overview

The Lookbook MPC Admin Dashboard is a modern Next.js application that provides comprehensive monitoring and management capabilities for your fashion recommendation system.

## Quick Start

```bash
cd shadcn
npm install
npm run dev
# Available at http://localhost:3000
```

## Features

### Core Pages

- **Dashboard** (`/dashboard`): System overview with real-time metrics
- **Items Management** (`/admin/items`): Product catalog with full attribute editing
- **Chat History** (`/admin/chat-history`): Conversation monitoring
- **System Status** (`/admin/system-status`): Service health monitoring
- **Settings** (`/admin/settings`): Configuration management

### Key Capabilities

- **Real-time Monitoring**: Live status of all services
- **Product Management**: Comprehensive item editing with all fashion attributes
- **Performance Analytics**: Processing times, success rates, error tracking
- **Visual Statistics**: Category distribution, trend analysis
- **One-click Operations**: Ingestion triggers, system controls

## Items Management Features

The Items page includes comprehensive product attribute editing:

### Basic Attributes
- SKU, title, price, image key
- Stock status and availability

### Fashion Attributes
- **Category**: Top, Bottom, Dress, Outerwear, Shoes, etc.
- **Material**: Cotton, Silk, Denim, Leather, etc.
- **Pattern**: Plain, Striped, Floral, Print, etc.
- **Season**: Spring, Summer, Autumn, Winter
- **Occasion**: Casual, Business, Formal, Sport, etc.
- **Fit**: Slim, Regular, Relaxed, Oversized, etc.
- **Style**: Free text for style descriptions
- **Color**: Color specification
- **Brand**: Product brand
- **Plus Size**: Boolean indicator
- **Description**: Item description

### Size Management
- Multi-size support with comma-separated values
- Size range validation

## Technical Architecture

### Frontend Stack
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Component library
- **Lucide React**: Icons

### API Integration
- Connects to Main API (port 8000)
- Real-time data fetching
- Proxy configuration for CORS handling

## Configuration

### Environment Variables

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_REFRESH_INTERVAL=30000
```

### API Proxy

Next.js rewrites in `next.config.js`:
```javascript
async rewrites() {
  return [
    {
      source: '/api/python/:path*',
      destination: 'http://localhost:8000/:path*',
    },
  ];
}
```

## Common Issues & Solutions

### Build/Runtime Errors

**Problem**: Complex component dependencies causing compilation errors
**Solution**: Simplified component architecture with minimal dependencies

**Problem**: Client-side hydration issues
**Solution**: Removed heavy state management from layout components

### API Connection Issues

**Problem**: Dashboard shows "disconnected" status
**Solution**: 
1. Verify Main API is running on port 8000
2. Check CORS configuration
3. Ensure proxy routes are correctly configured

### Performance Issues

**Problem**: Slow loading or high memory usage
**Solution**:
1. Increase refresh intervals
2. Optimize component rendering
3. Use React.memo for expensive components

## Development

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

### Component Development

Key components:
- `app/layout.tsx`: Root layout with navigation
- `app/dashboard/page.tsx`: Main dashboard
- `app/admin/items/page.tsx`: Items management with full editing
- `components/ui/`: Reusable UI components

### Adding New Features

1. Create new page in `app/` directory
2. Add navigation link in layout
3. Implement API calls for data fetching
4. Add error handling and loading states

## Best Practices

### Performance
- Use React Query for data fetching
- Implement proper loading states
- Add error boundaries
- Optimize re-renders with React.memo

### User Experience
- Provide visual feedback for all actions
- Implement proper form validation
- Add confirmation dialogs for destructive actions
- Include helpful error messages

### Code Quality
- Use TypeScript for type safety
- Follow Next.js best practices
- Implement proper error handling
- Add comprehensive comments

## Troubleshooting

### Dashboard Won't Load
1. Check Node.js version (18+ required)
2. Clear node_modules and reinstall
3. Verify no port conflicts on 3000
4. Check browser console for errors

### No Data Showing
1. Verify Main API is running on port 8000
2. Check network tab for failed requests
3. Verify API proxy configuration
4. Check CORS settings

### Items Page Issues
1. Ensure backend uses `/v1/ingest/products` endpoint
2. Verify response format matches expected schema
3. Check attribute validation in edit forms
4. Test individual API endpoints

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Support

- Check browser console for detailed error messages
- Review network requests in developer tools
- Verify backend API connectivity
- Consult main project documentation for API details

The dashboard provides a comprehensive interface for managing your fashion recommendation system with modern UI/UX patterns and robust error handling.