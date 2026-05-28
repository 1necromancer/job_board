import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import { login } from "../api";

export default function Login() {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(password);
      navigate("/jobs", { replace: true });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Invalid password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <form onSubmit={submit} className="card w-full max-w-sm grid gap-4">
        <div>
          <h1 className="text-xl font-semibold">Admin sign in</h1>
          <p className="text-sm text-slate-500">
            Enter the admin password to continue.
          </p>
        </div>
        <input
          autoFocus
          required
          type="password"
          className="input"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button disabled={loading} className="btn-primary">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
