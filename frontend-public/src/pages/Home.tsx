import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchJobs, type Job } from "../api";

function JobCard({ job }: { job: Job }) {
  return (
    <Link to={`/jobs/${job.id}`} className="card flex flex-col gap-2 group">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 group-hover:underline">
            {job.title}
          </h3>
          <p className="text-sm text-slate-600">
            {job.company} · {job.location}
          </p>
        </div>
        {job.salary && (
          <span className="shrink-0 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            {job.salary}
          </span>
        )}
      </div>
      <p className="line-clamp-2 text-sm text-slate-600">{job.description}</p>
    </Link>
  );
}

export default function Home() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["jobs"],
    queryFn: fetchJobs,
  });

  return (
    <section>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Open positions
        </h1>
        <p className="mt-2 text-slate-600">
          Browse current openings and apply in seconds.
        </p>
      </div>

      {isLoading && (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-5 w-1/3 rounded bg-slate-200" />
              <div className="mt-3 h-4 w-2/3 rounded bg-slate-100" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="card border-red-200 bg-red-50 text-red-800">
          Failed to load jobs. Please try again later.
        </div>
      )}

      {data && data.length === 0 && (
        <div className="card text-center text-slate-500">
          No open positions right now. Check back soon.
        </div>
      )}

      <div className="grid gap-4">
        {data?.map((job) => <JobCard key={job.id} job={job} />)}
      </div>
    </section>
  );
}
