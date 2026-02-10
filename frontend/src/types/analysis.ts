/**
 * Log, test result, and error analysis type definitions
 */

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
