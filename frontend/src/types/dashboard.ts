/**
 * Dashboard and common type definitions
 */

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
