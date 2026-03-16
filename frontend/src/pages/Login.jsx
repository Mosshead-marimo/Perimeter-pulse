import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError("");
    try {
      await api.post("/auth/login", {
        username,
        password,
      });
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.error || "Login failed"
      );
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
      <h2 style={styles.title}>Welcome Back</h2>
      <p style={styles.subtitle}>Sign in to access firewall reports and risk analytics.</p>

      <input
        placeholder="Username"
        style={styles.input}
        onChange={(e) => setUsername(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        style={styles.input}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button style={styles.button} onClick={handleLogin}>Login</button>

      {error && <p style={styles.error}>{error}</p>}

      <p style={styles.footer}>
        No account? <Link to="/signup">Signup</Link>
      </p>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: 16,
  },
  container: {
    width: "100%",
    maxWidth: "360px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
    padding: 20,
    borderRadius: 14,
    border: "1px solid #dbe3ef",
    background: "#ffffff",
    boxShadow: "0 14px 30px rgba(15,23,42,0.08)",
  },
  title: {
    marginBottom: 0,
  },
  subtitle: {
    marginTop: 0,
    color: "#64748b",
    marginBottom: 8,
  },
  input: {
    width: "100%",
    border: "1px solid #cbd5e1",
    borderRadius: 10,
    padding: "10px 12px",
  },
  button: {
    border: "1px solid #1d4ed8",
    background: "#2563eb",
    color: "#fff",
    fontWeight: 700,
    borderRadius: 10,
    padding: "9px 12px",
  },
  error: {
    color: "#b91c1c",
    margin: "2px 0 0",
  },
  footer: {
    margin: "2px 0 0",
  },
};
