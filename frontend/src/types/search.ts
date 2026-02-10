/**
 * Search-related type definitions
 */

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
