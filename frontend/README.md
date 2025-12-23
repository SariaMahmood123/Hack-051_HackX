# Frontend

Next.js frontend for LUMEN video chatbot interface.

## Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with metadata
│   ├── page.tsx             # Home page
│   └── globals.css          # Global styles & animations
├── components/
│   ├── ChatInterface.tsx    # Main chat orchestrator
│   ├── MessageList.tsx      # Message display with auto-scroll
│   ├── VideoPlayer.tsx      # Video playback with error handling
│   ├── InputBox.tsx         # User input with validation
│   ├── Toast.tsx            # Toast notifications
│   ├── LoadingSpinner.tsx   # Loading states
│   ├── StatusIndicator.tsx  # Backend connection status
│   └── SettingsPanel.tsx    # Settings & configuration
├── lib/
│   ├── api.ts              # Backend API client
│   ├── hooks.ts            # Custom React hooks
│   ├── utils.ts            # Helper functions
│   └── constants.ts        # App constants
├── types/
│   └── index.ts            # TypeScript type definitions
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── next.config.js          # Next.js config
├── .eslintrc.js            # ESLint config
├── .env.local              # Environment variables
└── test-frontend.js        # API testing script
```

## Features

✅ **Modern UI** - Gradient backgrounds with smooth animations
✅ **Real-time Status** - Backend connection indicator
✅ **Type Safety** - Full TypeScript support
✅ **Input Validation** - Client-side prompt validation
✅ **Error Handling** - Toast notifications for errors
✅ **Auto-scroll** - Message list auto-scrolls to latest
✅ **Responsive** - Desktop and tablet optimized
✅ **Loading States** - Visual feedback during generation
✅ **Settings Panel** - Backend status and temperature control
✅ **Keyboard Shortcuts** - Enter to send, Shift+Enter for newline
✅ **Custom Hooks** - Backend health monitoring, local storage
✅ **Video Error Handling** - Graceful fallbacks for missing videos

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Start Development Server

**Option A: Using start script (Windows)**
```powershell
cd ..
.\start_frontend.bat
```

**Option B: Using npm directly**
```bash
npm run dev
```

### 4. Access Application

Open http://localhost:3000 in your browser.

## Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Test API connection
node test-frontend.js
```

## Environment Variables

Create `.env.local`:

```bash
# Backend API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Optional: Debug mode
NEXT_PUBLIC_DEBUG=false

# Optional: Custom branding
NEXT_PUBLIC_APP_NAME=LUMEN
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Components

### ChatInterface
Main orchestrator component that manages:
- Conversation state
- API calls to backend
- Video playback coordination
- Toast notifications
- Clear chat functionality

**Props:** None (self-contained)

### MessageList
Scrollable message history with:
- Auto-scroll to latest message
- User/assistant message styling
- Timestamps
- Video indicators
- Empty state placeholder

**Props:**
- `messages: Message[]` - Array of conversation messages

### VideoPlayer
Video display component with:
- Loading states
- Error handling
- Auto-play functionality
- Video controls
- Placeholder when idle

**Props:**
- `videoPath: string | null` - Path to video file
- `isGenerating: boolean` - Generation status

### InputBox
User input component with:
- Multi-line text input
- Character count (when approaching limit)
- Input validation
- Keyboard shortcuts
- Auto-resize
- Error display

**Props:**
- `onSend: (message: string) => void` - Send callback
- `disabled: boolean` - Disable input
- `isGenerating: boolean` - Show generating state

### Toast
Notification component:
- Success/error/info/warning types
- Auto-dismiss after duration
- Slide-up animation

**Props:**
- `message: string` - Toast message
- `type?: 'success' | 'error' | 'info' | 'warning'` - Toast type
- `duration?: number` - Display duration (default: 3000ms)

### StatusIndicator
Backend connection status:
- Green dot = Connected
- Red dot = Offline
- Gray dot = Connecting

**Props:** None (uses health hook)

### SettingsPanel
Settings overlay with:
- Backend status display
- GPU information
- Temperature control
- Collapsible panel

**Props:** None (self-contained)

## Custom Hooks

### useBackendHealth
Monitor backend health at intervals.

```typescript
const { health, isHealthy, loading, error, refetch } = useBackendHealth(30000)
```

### useLocalStorage
Persist data in browser localStorage.

```typescript
const [messages, setMessages] = useLocalStorage<Message[]>('messages', [])
```

### useMediaQuery
Detect media query matches.

```typescript
const isMobile = useMediaQuery('(max-width: 768px)')
```

### useKeyboardShortcut
Register keyboard shortcuts.

```typescript
useKeyboardShortcut('/', () => focusInput(), { ctrl: true })
```

## API Client

The `lib/api.ts` module provides typed API functions:

```typescript
import { generateFullPipeline, healthCheck } from '@/lib/api'

// Full pipeline
const response = await generateFullPipeline({
  prompt: "Hello!",
  conversation_history: []
})

// Health check
const health = await healthCheck()
```

## Styling

Uses Tailwind CSS utility classes with custom styles in `globals.css`:

- **Custom animations**: slide-up, fade-in, pulse-glow
- **Custom scrollbar**: Purple themed
- **Loading skeleton**: Gradient animation
- **Focus styles**: Purple outline

## Type Definitions

All TypeScript types are defined in `types/index.ts`:

```typescript
import type { Message, GenerationResponse, HealthCheckResponse } from '@/types'
```

## Error Handling

Errors are handled at multiple levels:
1. **API client**: Axios interceptors
2. **Components**: Try-catch blocks
3. **UI**: Toast notifications
4. **Validation**: Input validation before submission

## Keyboard Shortcuts

- **Enter** - Send message
- **Shift+Enter** - New line in message
- **Escape** - Close settings panel

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- **Code splitting**: Automatic with Next.js App Router
- **Image optimization**: Next.js Image component (not used in MVP)
- **Bundle size**: ~200KB gzipped (production build)

## Development Tips

1. **Hot Reload**: Changes auto-reload in dev mode
2. **Type Checking**: Run `npm run build` to check types
3. **Linting**: Run `npm run lint` for code quality
4. **API Testing**: Use `node test-frontend.js` to test backend
5. **Console Logs**: Check browser console for debug info

## Troubleshooting

### Frontend won't start

```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run dev
```

### API connection fails

```bash
# Check backend is running
curl http://localhost:8000/health

# Verify .env.local has correct API URL
cat .env.local
```

### Type errors

```bash
# Regenerate TypeScript definitions
npm run build
```

### Styling issues

```bash
# Clear Tailwind cache
rm -rf .next
npm run dev
```

## Production Build

```bash
# Build for production
npm run build

# Start production server
npm start

# Or use a process manager
pm2 start npm --name "lumen-frontend" -- start
```

## Deployment

For production deployment:

1. **Build the app**: `npm run build`
2. **Set environment variables** in hosting platform
3. **Deploy** to Vercel, Netlify, or similar
4. **Configure CORS** on backend for production URL

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
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

## Testing

```bash
# Test API connection
node test-frontend.js

# Manual testing checklist:
# - [ ] Send a message
# - [ ] Check video playback
# - [ ] Verify status indicator
# - [ ] Test settings panel
# - [ ] Check error handling
# - [ ] Verify keyboard shortcuts
# - [ ] Test responsive design
```

## Future Improvements

- [ ] Add conversation persistence
- [ ] Implement user authentication
- [ ] Add dark/light theme toggle
- [ ] Support multiple personas
- [ ] Add voice input
- [ ] Implement streaming responses
- [ ] Add message reactions
- [ ] Support file uploads
- [ ] Add conversation export
- [ ] Implement search functionality
