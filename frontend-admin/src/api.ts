import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "jb_admin_token";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (location.pathname !== "/login") location.href = "/login";
    }
    return Promise.reject(err);
  },
);

export const auth = {
  setToken: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  getToken: () => localStorage.getItem(TOKEN_KEY),
  clear: () => localStorage.removeItem(TOKEN_KEY),
  isAuthed: () => !!localStorage.getItem(TOKEN_KEY),
};

export type JobStatus = "open" | "closed";
export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  salary: string | null;
  status: JobStatus;
  created_at: string;
  updated_at: string;
};

export type JobInput = {
  title: string;
  company: string;
  location: string;
  description: string;
  salary?: string | null;
  status?: JobStatus;
};

export type Application = {
  id: number;
  job_id: number;
  full_name: string;
  email: string;
  cover_letter: string | null;
  created_at: string;
  job: Job;
};

export const login = async (password: string) => {
  const { data } = await api.post<{ access_token: string; expires_in: number }>(
    "/api/admin/login",
    { password },
  );
  auth.setToken(data.access_token);
  return data;
};

export const fetchJobs = async (): Promise<Job[]> => {
  const { data } = await api.get<Job[]>("/api/admin/jobs");
  return data;
};

export const createJob = async (payload: JobInput): Promise<Job> => {
  const { data } = await api.post<Job>("/api/admin/jobs", payload);
  return data;
};

export const updateJob = async (
  id: number,
  payload: Partial<JobInput>,
): Promise<Job> => {
  const { data } = await api.patch<Job>(`/api/admin/jobs/${id}`, payload);
  return data;
};

export const deleteJob = async (id: number) => {
  await api.delete(`/api/admin/jobs/${id}`);
};

export const fetchApplications = async (jobId?: number): Promise<Application[]> => {
  const { data } = await api.get<Application[]>("/api/admin/applications", {
    params: jobId ? { job_id: jobId } : undefined,
  });
  return data;
};
