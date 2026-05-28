import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  salary: string | null;
  status: "open" | "closed";
  created_at: string;
  updated_at: string;
};

export type ApplicationCreate = {
  full_name: string;
  email: string;
  cover_letter?: string;
};

export const fetchJobs = async (): Promise<Job[]> => {
  const { data } = await api.get<Job[]>("/api/jobs");
  return data;
};

export const fetchJob = async (id: string | number): Promise<Job> => {
  const { data } = await api.get<Job>(`/api/jobs/${id}`);
  return data;
};

export const applyToJob = async (
  id: string | number,
  payload: ApplicationCreate,
) => {
  const { data } = await api.post(`/api/jobs/${id}/apply`, payload);
  return data;
};
