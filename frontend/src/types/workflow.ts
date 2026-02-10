/**
 * Workflow and run type definitions
 */

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
