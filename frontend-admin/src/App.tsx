import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { auth } from "./api";

export default function App() {
  const navigate = useNavigate();
  const logout = () => {
    auth.clear();
    navigate("/login", { replace: true });
  };
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white text-sm font-bold">
                JB
              </span>
              <span className="text-sm font-semibold tracking-tight">Admin</span>
            </div>
            <nav className="flex items-center gap-1">
              <NavLink
                to="/jobs"
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium ${
                    isActive
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-600 hover:text-slate-900"
                  }`
                }
              >
                Jobs
              </NavLink>
              <NavLink
                to="/applications"
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium ${
                    isActive
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-600 hover:text-slate-900"
                  }`
                }
              >
                Applications
              </NavLink>
            </nav>
          </div>
          <button onClick={logout} className="btn-ghost">
            Sign out
          </button>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
