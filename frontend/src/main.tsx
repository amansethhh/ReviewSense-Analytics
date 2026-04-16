import React from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource/geist/400.css'
import '@fontsource/geist/500.css'
import '@fontsource/geist/700.css'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/animations.css'
import App from './App'

// SPA redirect restore (for 404.html-based hosting)
const redirect = sessionStorage.getItem('redirect')
if (redirect) {
  sessionStorage.removeItem('redirect')
  window.history.replaceState(null, '', redirect)
}

ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
