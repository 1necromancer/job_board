import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { applyToJob, fetchJob, type ApplicationCreate } from "../api";

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading, error } = useQuery({
    queryKey: ["job", id],
    queryFn: () => fetchJob(id!),
    enabled: !!id,
  });

  const [form, setForm] = useState<ApplicationCreate>({
    full_name: "",
    email: "",
    cover_letter: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: (payload: ApplicationCreate) => applyToJob(id!, payload),
    onSuccess: () => {
      setSubmitted(true);
      toast.success("Application sent! Check your email for confirmation.");
    },
    onError: (err: any) => {
      const detail =
        err?.response?.data?.detail ?? "Something went wrong. Please try again.";
      toast.error(detail);
    },
  });

  if (isLoading) return <div className="card animate-pulse h-40" />;
  if (error || !job)
    return (
      <div className="card border-red-200 bg-red-50 text-red-800">
        Job not found.{" "}
        <Link to="/" className="underline">
          Back to listings
        </Link>
      </div>
    );

  return (
    <article className="grid gap-8 md:grid-cols-[1fr_360px]">
      <div>
        <Link to="/" className="text-sm text-slate-500 hover:text-slate-900">
          ← All openings
        </Link>
        <header className="mt-3">
          <h1 className="text-3xl font-bold tracking-tight">{job.title}</h1>
          <p className="mt-1 text-slate-600">
            {job.company} · {job.location}
          </p>
          {job.salary && (
            <span className="mt-3 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
              {job.salary}
            </span>
          )}
        </header>
        <div className="prose prose-slate mt-6 max-w-none whitespace-pre-wrap text-slate-700">
          {job.description}
        </div>
      </div>

      <aside className="card h-fit md:sticky md:top-24">
        {submitted ? (
          <div className="text-center py-6">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              ✓
            </div>
            <h3 className="font-semibold">Application sent</h3>
            <p className="mt-1 text-sm text-slate-600">
              We've emailed you a confirmation. The team will reach out soon.
            </p>
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate(form);
            }}
            className="grid gap-3"
          >
            <div>
              <h3 className="font-semibold">Apply for this role</h3>
              <p className="text-sm text-slate-500">It only takes a minute.</p>
            </div>
            <input
              required
              minLength={2}
              className="input"
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
            <input
              required
              type="email"
              className="input"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <textarea
              rows={5}
              className="input resize-none"
              placeholder="Cover letter (optional)"
              value={form.cover_letter}
              onChange={(e) =>
                setForm({ ...form, cover_letter: e.target.value })
              }
            />
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn-primary"
            >
              {mutation.isPending ? "Sending…" : "Send application"}
            </button>
          </form>
        )}
      </aside>
    </article>
  );
}
