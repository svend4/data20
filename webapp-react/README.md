# Data20 React Web UI

Enhanced React-based web interface for Data20 Knowledge Base.

## Features

✅ **Modern React Stack**:
- React 18.2
- Vite 5.0 (blazing fast development)
- React Router 6 (client-side routing)
- Context API (state management)
- Custom Hooks (reusable logic)

✅ **User Interface**:
- Login/Register with JWT authentication
- Tools catalog with search and filters
- Dynamic parameter forms
- Real-time job status tracking
- Job history with filters
- Responsive design

✅ **Developer Experience**:
- Fast HMR (Hot Module Replacement)
- Component-based architecture
- Reusable hooks and utilities
- Clean separation of concerns
- ESLint configuration

## Quick Start

### Install Dependencies

```bash
npm install
```

### Development Server

Start the development server with hot reload:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

API requests will be proxied to `http://localhost:8001` (configure in `vite.config.js`).

### Build for Production

```bash
npm run build
```

The optimized production build will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
webapp-react/
├── src/
│   ├── components/          # Reusable React components
│   │   ├── ToolCard.jsx     # Tool display card
│   │   ├── ParameterForm.jsx # Dynamic parameter form
│   │   └── JobResult.jsx    # Job result display
│   ├── pages/               # Page components (routes)
│   │   ├── Login.jsx        # Login/Register page
│   │   ├── Home.jsx         # Tools catalog
│   │   ├── RunTool.jsx      # Tool execution page
│   │   └── Jobs.jsx         # Job history page
│   ├── contexts/            # React contexts
│   │   └── AuthContext.jsx  # Authentication state
│   ├── hooks/               # Custom React hooks
│   │   ├── useTools.js      # Tools data hook
│   │   └── useJobs.js       # Jobs data hook
│   ├── utils/               # Utility functions
│   │   └── api.js           # API configuration & helpers
│   ├── App.jsx              # Main app component with routing
│   ├── main.jsx             # React entry point
│   └── index.css            # Global styles
├── index.html               # HTML entry point
├── package.json             # Dependencies and scripts
├── vite.config.js           # Vite configuration
└── README.md                # This file
```

## Key Components

### Authentication (AuthContext)

Manages user authentication state across the app:

```jsx
const { user, isAuthenticated, login, register, logout } = useAuth();
```

### Custom Hooks

#### useTools

```jsx
const { tools, loading, error, reload } = useTools();
```

#### useJob

```jsx
const { job, loading, error, reload } = useJob(jobId, autoPoll, pollInterval);
```

#### useJobs

```jsx
const { jobs, loading, error, reload, runTool } = useJobs(autoRefresh, refreshInterval);
```

### Routing

- `/login` - Login/Register page (public)
- `/` - Home page with tools catalog (protected)
- `/run/:toolName` - Run tool page (protected)
- `/jobs` - Job history page (protected)

## Configuration

### API Proxy

Development server proxies API requests. Configure in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': 'http://localhost:8001',
    '/auth': 'http://localhost:8001',
  },
}
```

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8001
```

## Development Workflow

1. **Start backend server**:
   ```bash
   cd /home/user/data20
   python run_standalone.py
   ```

2. **Start React dev server**:
   ```bash
   cd webapp-react
   npm run dev
   ```

3. **Open browser**: `http://localhost:3000`

## Building for Production

### Standalone Build

Build React app and serve with backend:

```bash
# Build React app
npm run build

# Copy dist to backend static folder
cp -r dist ../backend/static

# Update backend to serve static files
# (configure in backend/server.py)
```

### Docker Build

```dockerfile
# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Comparison with Plain HTML/CSS/JS Version

### Advantages of React Version

✅ **Better Developer Experience**:
- Component reusability
- Type safety with PropTypes/TypeScript
- Hot module replacement
- Better tooling and debugging

✅ **Better Performance**:
- Virtual DOM for efficient updates
- Code splitting
- Optimized builds

✅ **Better State Management**:
- Context API for global state
- Custom hooks for logic reuse
- Predictable state updates

✅ **Better Scalability**:
- Modular architecture
- Easy to add new features
- Better code organization

### Trade-offs

❌ **More Complex**:
- Build step required
- More dependencies
- Steeper learning curve

❌ **Larger Bundle**:
- React runtime (~45KB gzipped)
- Total bundle: ~150KB gzipped
- Plain version: ~15KB gzipped

## Next Steps

### Phase 6.7: Electron Desktop App

Wrap React app in Electron for desktop distribution:

```bash
npm install --save-dev electron electron-builder
```

### Phase 6.8: Flutter Mobile App

Create mobile app using Flutter with same backend API.

## Troubleshooting

### Port Already in Use

Change port in `vite.config.js`:

```javascript
server: {
  port: 3001,
}
```

### API Connection Issues

Check that backend is running:

```bash
curl http://localhost:8001/api/tools
```

Update proxy configuration in `vite.config.js`.

### Build Errors

Clear cache and reinstall:

```bash
rm -rf node_modules dist
npm install
npm run build
```

## License

Same as Data20 Knowledge Base project.
