import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import "../styles/App.css";

export default function LoginPage({ setToken }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  async function handleLogin() {
    try {
      const res = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", res.data.token);
      setToken(res.data.token);
      navigate("/select"); 
    } catch (err) {
      alert("Invalid credentials");
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h2 className="login-title">Login</h2>

        <input
          className="input"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
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
