/**
 * Type definitions for GitHub Actions Dashboard
 */

export interface Repository {
  id: number
  github_id: number
  name: string
  full_name: string
  owner: string
  description: string | null
  default_branch: string
  is_active: boolean
  webhook_configured: boolean
  last_synced_at: string | null
  created_at: string
  updated_at: string
}

export interface Workflow {
  id: number
  github_id: number
  name: string
  path: string
  state: 'active' | 'disabled_manually' | 'disabled_inactivity'
  repo_id: number
  created_at: string
  updated_at: string
}

export type WorkflowRunStatus = 'queued' | 'in_progress' | 'completed' | 'waiting'
export type WorkflowRunConclusion = 'success' | 'failure' | 'cancelled' | 'skipped' | 'timed_out' | 'action_required' | null

export interface WorkflowRun {
  id: number
  github_id: number
  run_number: number
  run_attempt: number
  name: string
  display_title: string | null
  status: WorkflowRunStatus
  conclusion: WorkflowRunConclusion
  head_branch: string
  head_sha: string
  event: string
  actor: string
  triggering_actor: string | null
  html_url: string
  workflow_id: number
  duration_seconds: number | null
  created_at: string
  updated_at: string
  run_started_at: string | null
}

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

export interface Log {
  id: number
  log_content: string
  content: string
  error_content: string | null
  log_hash: string
  category: string | null
  step_name: string | null
  has_error: boolean
  job_id: number
  created_at: string
}

export interface TestResult {
  framework: string
  total: number
  passed: number
  failed: number
  skipped: number
  duration_seconds: number | null
  success_rate: number
}

export interface ErrorAnalysis {
  id: number
  root_cause: string
  summary: string
  error_summary: string
  suggested_fix: string | null
  suggested_fixes: string[]
  prevention_tips: string[]
  confidence: number
  confidence_score: number
  tokens_used: number
  log_id: number
  created_at: string
}

export interface DashboardStats {
  total_repositories: number
  total_workflows: number
  total_runs_24h: number
  success_rate: number
  success_rate_24h: number
  failed_runs_24h: number
  avg_duration_seconds: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface SearchResultMetadata {
  repository?: string
  branch?: string
  job_id?: number
}

export interface SearchResult {
  id: number
  type: 'workflow' | 'run' | 'job' | 'log'
  title: string
  description: string | null
  score: number
  metadata: SearchResultMetadata
  log_id?: number
  similarity?: number
  error_summary?: string
  repository?: string
  workflow?: string
  created_at: string
}
