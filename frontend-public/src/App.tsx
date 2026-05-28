import { Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white text-sm font-bold">
              JB
            </span>
            <span className="text-lg font-semibold tracking-tight">Job Board</span>
          </Link>
          <a
            href="https://github.com"
            className="text-sm text-slate-500 hover:text-slate-900"
            target="_blank"
            rel="noreferrer"
          >
            About
          </a>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-5xl px-6 py-10">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-6 text-sm text-slate-500">
          Built with FastAPI · React · PostgreSQL · Redis · Telegram
        </div>
      </footer>
    </div>
  );
}
