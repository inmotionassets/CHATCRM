import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.jsx";
import "./styles.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      const errorMessage = this.state.error?.message || String(this.state.error || "Unknown display error");
      return (
        <main style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
          <h1>ChatCRM recovery</h1>
          <p>The app hit a browser-side display error, but your uploaded leads are still saved in the backend.</p>
          <p style={{ opacity: 0.8 }}>Error: {errorMessage}</p>
          <p style={{ opacity: 0.8 }}>Build: cache-recovery-2</p>
          <button
            onClick={() => {
              Object.keys(localStorage)
                .filter((key) => key.startsWith("chatcrm."))
                .forEach((key) => localStorage.removeItem(key));
              window.location.reload();
            }}
            style={{ cursor: "pointer", fontWeight: 700, padding: "10px 14px" }}
          >
            Reload Saved Leads
          </button>
        </main>
      );
    }

    return this.props.children;
  }
}

if (!sessionStorage.getItem("chatcrm.cacheRecovery2")) {
  sessionStorage.setItem("chatcrm.cacheRecovery2", "1");
  Object.keys(localStorage)
    .filter((key) => key.startsWith("chatcrm."))
    .forEach((key) => localStorage.removeItem(key));
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
