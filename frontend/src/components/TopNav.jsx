import { NavLink, useNavigate } from "react-router-dom";
import api from "../api/client";

const links = [
  { to: "/dashboard/analyze", label: "Analyze" },
  { to: "/dashboard/reports", label: "Reports" },
];

export default function TopNav() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Continue navigation even if backend returns error.
    }
    navigate("/");
  };

  return (
    <header style={styles.header}>
      <div style={styles.brand}>Firewall Log Intelligence</div>
      <nav style={styles.nav}>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive ? styles.linkActive : {}),
            })}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <button style={styles.logoutButton} onClick={handleLogout}>
        Logout
      </button>
    </header>
  );
}

const styles = {
  header: {
    position: "sticky",
    top: 0,
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 14,
    padding: "12px 20px",
    borderBottom: "1px solid #dbe3ef",
    background:
      "linear-gradient(90deg, rgba(255,255,255,0.98) 0%, rgba(241,245,249,0.98) 60%, rgba(238,242,255,0.98) 100%)",
    backdropFilter: "blur(6px)",
  },
  brand: {
    fontWeight: 800,
    letterSpacing: 0.3,
    color: "#0f172a",
    whiteSpace: "nowrap",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    flexWrap: "wrap",
    justifyContent: "center",
  },
  link: {
    padding: "7px 12px",
    borderRadius: 999,
    border: "1px solid transparent",
    color: "#334155",
    textDecoration: "none",
    fontWeight: 600,
    fontSize: 14,
  },
  linkActive: {
    border: "1px solid #93c5fd",
    background: "#dbeafe",
    color: "#1d4ed8",
  },
  logoutButton: {
    border: "1px solid #fecaca",
    background: "#fff1f2",
    color: "#b91c1c",
    borderRadius: 10,
    padding: "7px 12px",
    fontWeight: 600,
  },
};
