import axios from 'axios';
import type { Candidate, UploadResponse } from '../types';

const upload = axios.create({
  baseURL: import.meta.env.VITE_UPLOAD_URL ?? '/api/upload',
});

const screener = axios.create({
  baseURL: import.meta.env.VITE_SCREENER_URL ?? '/api/screener',
});

/**
 * Upload one or more resume files with a job description.
 * Returns a job_id for each uploaded file.
 */
export async function uploadResumes(
  files: File[],
  jobDescription: string
): Promise<UploadResponse[]> {
  const results: UploadResponse[] = [];
  for (const file of files) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('job_description', jobDescription);
    const { data } = await upload.post<UploadResponse>('/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    results.push(data);
  }
  return results;
}

/**
 * Poll job status from upload-service.
 */
export async function pollJob(jobId: string): Promise<{ status: string }> {
  const { data } = await upload.get(`/jobs/${jobId}`);
  return data;
}

/**
 * Fetch ranked candidate results for a job from ai-screener-service.
 */
export async function getResults(jobId: string): Promise<Candidate[]> {
  const { data } = await screener.get<Candidate[]>(`/results/${jobId}`);
  return data;
}
