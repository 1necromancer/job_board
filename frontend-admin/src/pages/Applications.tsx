import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchApplications, fetchJobs } from "../api";

export default function Applications() {
  const [jobId, setJobId] = useState<number | "">("");
  const { data: jobs } = useQuery({ queryKey: ["admin-jobs"], queryFn: fetchJobs });
  const { data, isLoading } = useQuery({
    queryKey: ["admin-applications", jobId],
    queryFn: () => fetchApplications(jobId === "" ? undefined : jobId),
  });

  const total = data?.length ?? 0;
  const summary = useMemo(() => {
    const counts: Record<number, number> = {};
    (data ?? []).forEach((a) => {
      counts[a.job_id] = (counts[a.job_id] ?? 0) + 1;
    });
    return counts;
  }, [data]);

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Applications</h1>
          <p className="text-sm text-slate-500">{total} total</p>
        </div>
        <select
          className="input max-w-xs"
          value={jobId}
          onChange={(e) =>
            setJobId(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">All jobs</option>
          {jobs?.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title} ({summary[j.id] ?? 0})
            </option>
          ))}
        </select>
      </div>

      {isLoading && <div className="card animate-pulse h-24" />}

      <div className="grid gap-3">
        {data?.map((a) => (
          <div key={a.id} className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold">{a.full_name}</h3>
                <a
                  href={`mailto:${a.email}`}
                  className="text-sm text-slate-600 hover:underline"
                >
                  {a.email}
                </a>
                <p className="mt-1 text-sm text-slate-500">
                  Applied to{" "}
                  <span className="font-medium text-slate-700">
                    {a.job.title}
                  </span>{" "}
                  · {a.job.company}
                </p>
              </div>
              <time className="text-xs text-slate-400" dateTime={a.created_at}>
                {new Date(a.created_at).toLocaleString()}
              </time>
            </div>
            {a.cover_letter && (
              <p className="mt-3 whitespace-pre-wrap text-sm text-slate-600 border-t border-slate-100 pt-3">
                {a.cover_letter}
              </p>
            )}
          </div>
        ))}
        {data && data.length === 0 && (
          <div className="card text-center text-slate-500">No applications yet.</div>
        )}
      </div>
    </section>
  );
}
