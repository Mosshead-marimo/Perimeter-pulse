import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";

export default function Signup() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSignup = async () => {
    setError("");
    try {
      await api.post("/auth/signup", {
        username,
        password,
      });
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.error || "Signup failed"
      );
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
      <h2 style={styles.title}>Create Account</h2>
      <p style={styles.subtitle}>Start monitoring uploaded firewall logs with report navigation.</p>

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

      <button style={styles.button} onClick={handleSignup}>Signup</button>

      {error && <p style={styles.error}>{error}</p>}

      <p style={styles.footer}>
        Already have an account? <Link to="/">Login</Link>
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
