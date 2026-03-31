export interface ScoreBreakdown {
  skills: number;
  experience: number;
  education: number;
  overall: number;
}

export interface NEREntities {
  companies: string[];
  degrees: string[];
  tools: string[];
  locations: string[];
  misc: string[];
}

export interface Candidate {
  resume_id: string;
  filename: string;
  overall_score: number;
  breakdown: ScoreBreakdown;
  entities: NEREntities;
  summary: string;
}

export interface UploadResponse {
  job_id: string;
  message: string;
}

export type JobStatus = 'pending' | 'processing' | 'done' | 'failed';

export interface Job {
  job_id: string;
  status: JobStatus;
  job_description: string;
  created_at?: string;
}
