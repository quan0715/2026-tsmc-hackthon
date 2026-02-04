import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 啟用 dark mode
document.documentElement.classList.add('dark')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)
