/**
 * Job and step type definitions
 */

export type JobConclusion = 'success' | 'failure' | 'cancelled' | 'skipped' | null

export interface JobStep {
  number: number
  name: string
  status: string
  conclusion: string | null
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
}

export interface Job {
  id: number
  github_id: number
  name: string
  status: string
  conclusion: JobConclusion
  started_at: string | null
  completed_at: string | null
  runner_name: string | null
  runner_os: string | null
  workflow_run_id: number
  run_id: number
  duration_seconds: number | null
  steps: JobStep[]
  created_at: string
  updated_at: string
}
