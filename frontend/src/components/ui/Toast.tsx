import { useApp } from '@/context/AppContext'

export function ToastContainer() {
  const { state, dispatch } = useApp()
  return (
    <div className="toast-container" aria-live="polite">
      {state.toasts.map(toast => (
        <div
          key={toast.id}
          className={`toast toast--${toast.type}`}
          role="alert"
        >
          <span className="toast__message">
            {toast.message}
          </span>
          <button
            className="toast__close"
            onClick={() => dispatch({
              type: 'REMOVE_TOAST',
              payload: toast.id,
            })}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
