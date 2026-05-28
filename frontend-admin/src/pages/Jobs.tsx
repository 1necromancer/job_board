import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import {
  createJob,
  deleteJob,
  fetchJobs,
  updateJob,
  type Job,
  type JobInput,
} from "../api";

const empty: JobInput = {
  title: "",
  company: "",
  location: "",
  description: "",
  salary: "",
  status: "open",
};

export default function Jobs() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["admin-jobs"], queryFn: fetchJobs });

  const [editing, setEditing] = useState<Job | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<JobInput>(empty);

  const openCreate = () => {
    setEditing(null);
    setForm(empty);
    setCreating(true);
  };
  const openEdit = (j: Job) => {
    setCreating(false);
    setEditing(j);
    setForm({
      title: j.title,
      company: j.company,
      location: j.location,
      description: j.description,
      salary: j.salary ?? "",
      status: j.status,
    });
  };
  const close = () => {
    setCreating(false);
    setEditing(null);
  };

  const onSuccess = (msg: string) => {
    qc.invalidateQueries({ queryKey: ["admin-jobs"] });
    toast.success(msg);
    close();
  };

  const create = useMutation({
    mutationFn: (p: JobInput) => createJob(p),
    onSuccess: () => onSuccess("Job created"),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed"),
  });
  const update = useMutation({
    mutationFn: ({ id, p }: { id: number; p: Partial<JobInput> }) => updateJob(id, p),
    onSuccess: () => onSuccess("Job updated"),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed"),
  });
  const remove = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: () => onSuccess("Job deleted"),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed"),
  });

  const isOpen = creating || editing !== null;

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          <p className="text-sm text-slate-500">Create, edit and close openings.</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          + New job
        </button>
      </div>

      {isLoading && <div className="card animate-pulse h-24" />}

      <div className="grid gap-3">
        {data?.map((j) => (
          <div key={j.id} className="card flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">{j.title}</h3>
                <span className={j.status === "open" ? "badge-open" : "badge-closed"}>
                  {j.status}
                </span>
              </div>
              <p className="text-sm text-slate-500">
                {j.company} · {j.location}
                {j.salary ? ` · ${j.salary}` : ""}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => openEdit(j)} className="btn-ghost">
                Edit
              </button>
              <button
                onClick={() => {
                  if (confirm(`Delete "${j.title}"? This cannot be undone.`)) {
                    remove.mutate(j.id);
                  }
                }}
                className="btn-danger"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {data && data.length === 0 && (
          <div className="card text-center text-slate-500">No jobs yet — create one.</div>
        )}
      </div>

      {isOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-20 flex items-center justify-center bg-slate-900/40 p-4"
          onClick={close}
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={(e) => {
              e.preventDefault();
              const payload: JobInput = {
                ...form,
                salary: form.salary?.trim() ? form.salary : null,
              };
              if (editing) update.mutate({ id: editing.id, p: payload });
              else create.mutate(payload);
            }}
            className="card w-full max-w-lg grid gap-3 max-h-[90vh] overflow-auto"
          >
            <h2 className="text-lg font-semibold">
              {editing ? "Edit job" : "New job"}
            </h2>
            <input
              required
              className="input"
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                required
                className="input"
                placeholder="Company"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
              />
              <input
                required
                className="input"
                placeholder="Location"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
              />
            </div>
            <input
              className="input"
              placeholder="Salary (optional, e.g. $80k–$110k)"
              value={form.salary ?? ""}
              onChange={(e) => setForm({ ...form, salary: e.target.value })}
            />
            <textarea
              required
              minLength={10}
              rows={6}
              className="input resize-none"
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <select
              className="input"
              value={form.status}
              onChange={(e) =>
                setForm({ ...form, status: e.target.value as "open" | "closed" })
              }
            >
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button type="button" onClick={close} className="btn-ghost">
                Cancel
              </button>
              <button
                type="submit"
                disabled={create.isPending || update.isPending}
                className="btn-primary"
              >
                {editing ? "Save changes" : "Create job"}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
