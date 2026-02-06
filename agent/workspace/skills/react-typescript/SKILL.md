---
name: react-typescript-setup
description: Use this skill to set up React + TypeScript development environment, create components, manage state, and configure build tools. Use when user requests React project setup, using TypeScript, or developing frontend applications.
---

# React + TypeScript Environment Setup Skill

## Overview

This skill guides you on how to set up and manage a React + TypeScript development environment in the workspace.

## Environment Check

### 1. Check Node.js Version

First, use the `bash` tool to check the installed Node.js version:

```
bash(command="node --version")
```

Expected output similar to: `v18.x.x` or higher

### 2. Check npm/yarn Version

```
bash(command="npm --version")
bash(command="yarn --version")
```

## Create New Project

### Using Vite (Recommended)

Vite offers fast development experience and optimized builds:

```
bash(command="npm create vite@latest my-app -- --template react-ts")
bash(command="cd my-app && npm install")
```

### Using Create React App

```
bash(command="npx create-react-app my-app --template typescript")
bash(command="cd my-app && npm install")
```

### Using Next.js (SSR/SSG)

```
bash(command="npx create-next-app@latest my-app --typescript")
bash(command="cd my-app && npm install")
```

## Project Structure

Typical React + TypeScript project structure:

```
my-app/
├── src/
│   ├── components/      # React components
│   ├── hooks/          # Custom Hooks
│   ├── types/          # TypeScript definitions
│   ├── utils/          # Utility functions
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry file
├── public/             # Static assets
├── package.json
└── tsconfig.json       # TypeScript configuration
```

## TypeScript Configuration

### Basic tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## React Component Development

### Functional Components (Recommended)

```typescript
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false }) => {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
};

export default Button;
```

### Using Hooks

#### useState

```typescript
import { useState } from 'react';

const Counter: React.FC = () => {
  const [count, setCount] = useState<number>(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
};
```

#### useEffect

```typescript
import { useEffect, useState } from 'react';

interface User {
  id: number;
  name: string;
}

const UserList: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setUsers(data));
  }, []);

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
};
```

#### Custom Hook

```typescript
import { useState, useEffect } from 'react';

function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [url]);

  return { data, loading, error };
}

// Usage
const MyComponent: React.FC = () => {
  const { data, loading, error } = useFetch<User[]>('/api/users');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>{/* Render data */}</div>;
};
```

## State Management

### Context API

```typescript
import { createContext, useContext, useState, ReactNode } from 'react';

interface AuthContextType {
  user: string | null;
  login: (username: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<string | null>(null);

  const login = (username: string) => setUser(username);
  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Using Zustand (Lightweight)

Install:
```
bash(command="npm install zustand")
```

Usage:
```typescript
import create from 'zustand';

interface Store {
  count: number;
  increment: () => void;
  decrement: () => void;
}

const useStore = create<Store>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}));

// Usage in component
const Counter: React.FC = () => {
  const { count, increment, decrement } = useStore();
  
  return (
    <div>
      <p>{count}</p>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  );
};
```

## Common Package Installation

### UI Frameworks

```
bash(command="npm install @mui/material @emotion/react @emotion/styled")  # Material-UI
bash(command="npm install antd")  # Ant Design
bash(command="npm install tailwindcss postcss autoprefixer")  # Tailwind CSS
```

### Routing

```
bash(command="npm install react-router-dom")
bash(command="npm install -D @types/react-router-dom")
```

### Form Handling

```
bash(command="npm install react-hook-form")
bash(command="npm install yup @hookform/resolvers")  # Validation
```

### HTTP Requests

```
bash(command="npm install axios")
bash(command="npm install @tanstack/react-query")  # Data fetching/caching
```

### Testing

```
bash(command="npm install -D vitest @testing-library/react @testing-library/jest-dom")
bash(command="npm install -D @testing-library/user-event")
```

## Development & Build

### Start Dev Server

Vite:
```
bash(command="npm run dev")
```

Create React App:
```
bash(command="npm start")
```

### Build for Production

```
bash(command="npm run build")
```

### Preview Production Build

```
bash(command="npm run preview")
```

## Testing

### Component Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Button from './Button';

describe('Button', () => {
  it('renders with correct label', () => {
    render(<Button label="Click me" onClick={() => {}} />);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button label="Click me" onClick={handleClick} />);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Run Tests

```
bash(command="npm test")
bash(command="npm run test:coverage")  # Coverage report
```

## Code Quality

### ESLint Config

```
bash(command="npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin")
```

### Prettier Config

```
bash(command="npm install -D prettier eslint-config-prettier")
```

### Run Checks

```
bash(command="npm run lint")
bash(command="npm run format")
```

## Troubleshooting

### TypeScript Type Errors

1. Ensure necessary type definitions are installed: `npm install -D @types/react @types/react-dom`
2. Check `tsconfig.json` configuration
3. Use `// @ts-ignore` to suppress specific errors temporarily (not recommended)

### Module Not Found

1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Check dependency versions in `package.json`
3. Verify import paths

### Build Errors

Use verbose output to diagnose:
```
bash(command="npm run build -- --verbose")
```

### Dev Server Issues

Clear cache and restart:
```
bash(command="rm -rf node_modules/.vite")
bash(command="npm run dev")
```

## Best Practices

1. **Use Functional Components & Hooks** - Avoid class components
2. **Strict TypeScript Config** - Enable `strict` mode
3. **Component Splitting** - Keep components small and focused
4. **Use TypeScript Interfaces** - Define types for props and state
5. **Test-Driven Development** - Write tests for key components
6. **Use ESLint and Prettier** - Maintain code consistency
7. **Lazy Loading** - Use `React.lazy()` and `Suspense` for performance
8. **Use memo** - Optimize re-render performance

## React Router Example

```typescript
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/users/:id" element={<UserDetail />} />
      </Routes>
    </BrowserRouter>
  );
};
```

## Environment Variables

### Vite

Create `.env` file:
```
VITE_API_URL=https://api.example.com
```

Usage:
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

### Create React App

Create `.env` file:
```
REACT_APP_API_URL=https://api.example.com
```

Usage:
```typescript
const apiUrl = process.env.REACT_APP_API_URL;
```
