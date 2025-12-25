import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import "../styles/App.css";

export default function LoginPage({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  async function handleLogin() {
    try {
      const res = await api.post("/auth/login", { username, password });
      localStorage.setItem("token", res.data.token);
      setToken(res.data.token);
      navigate("/select"); // 🔥 THIS WAS THE MISSING PIECE
    } catch {
      alert("Invalid credentials");
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h2 className="login-title">Login</h2>

        <input
          className="input"
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />

        <input
          className="input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />

        <button className="button" onClick={handleLogin}>
          Login
        </button>
      </div>
    </div>
  );
}
