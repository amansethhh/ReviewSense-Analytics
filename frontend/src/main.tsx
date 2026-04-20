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

// BUG-6 FIX: Disable StrictMode in production to prevent
// double-mount animation flickering. StrictMode causes React
// to mount→unmount→remount every component, which resets
// CSS keyframe animations and causes a visible flicker.
const isDev = import.meta.env.DEV

const AppTree = isDev ? (
  <React.StrictMode>
    <App />
  </React.StrictMode>
) : (
  <App />
)

ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
).render(AppTree)
