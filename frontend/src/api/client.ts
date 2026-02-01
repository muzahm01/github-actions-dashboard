/**
 * API client for GitHub Actions Dashboard backend
 */
import axios, { type AxiosInstance } from 'axios'
import type {
  DashboardStats,
  ErrorAnalysis,
  Job,
  Log,
  PaginatedResponse,
  Repository,
  SearchResult,
  Workflow,
  WorkflowRun,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor for adding auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token')
        }
        return Promise.reject(error)
      }
    )
  }

  // Health endpoints
  async getHealth(): Promise<{ status: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  // Repository endpoints
  async getRepositories(): Promise<Repository[]> {
    const response = await this.client.get<Repository[]>('/repositories')
    return response.data
  }

  async getRepository(id: number): Promise<Repository> {
    const response = await this.client.get<Repository>(`/repositories/${id}`)
    return response.data
  }

  // Workflow endpoints
  async getWorkflows(repoId?: number): Promise<Workflow[]> {
    const params = repoId ? { repo_id: repoId } : {}
    const response = await this.client.get<Workflow[]>('/workflows', { params })
    return response.data
  }

  async getWorkflow(id: number): Promise<Workflow> {
    const response = await this.client.get<Workflow>(`/workflows/${id}`)
    return response.data
  }

  // Workflow Run endpoints
  async getWorkflowRuns(
    workflowId?: number,
    page: number = 1,
    perPage: number = 20
  ): Promise<PaginatedResponse<WorkflowRun>> {
    const params: Record<string, unknown> = { page, per_page: perPage }
    if (workflowId) params.workflow_id = workflowId
    const response = await this.client.get<PaginatedResponse<WorkflowRun>>('/runs', { params })
    return response.data
  }

  async getWorkflowRun(id: number): Promise<WorkflowRun> {
    const response = await this.client.get<WorkflowRun>(`/runs/${id}`)
    return response.data
  }

  async getRecentFailures(limit: number = 10): Promise<WorkflowRun[]> {
    const response = await this.client.get<WorkflowRun[]>('/runs/failures', {
      params: { limit },
    })
    return response.data
  }

  // Job endpoints
  async getJobs(runId: number): Promise<Job[]> {
    const response = await this.client.get<Job[]>('/jobs', {
      params: { run_id: runId },
    })
    return response.data
  }

  async getJob(id: number): Promise<Job> {
    const response = await this.client.get<Job>(`/jobs/${id}`)
    return response.data
  }

  async getJobLogs(jobId: number): Promise<Log[]> {
    const response = await this.client.get<Log[]>(`/jobs/${jobId}/logs`)
    return response.data
  }

  // Analysis endpoints
  async getAnalysis(logId: number): Promise<ErrorAnalysis | null> {
    try {
      const response = await this.client.get<ErrorAnalysis>(`/analysis/${logId}`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async requestAnalysis(logId: number): Promise<{ task_id: string }> {
    const response = await this.client.post<{ task_id: string }>('/analysis/analyze', {
      log_id: logId,
    })
    return response.data
  }

  // Search endpoints
  async search(query: string, limit: number = 20): Promise<SearchResult[]> {
    const response = await this.client.post<SearchResult[]>('/search/similar', {
      query,
      limit,
    })
    return response.data
  }

  async searchSimilarErrors(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await this.client.post<SearchResult[]>('/search/similar', {
      query,
      limit,
    })
    return response.data
  }

  async searchByText(query: string, limit: number = 20): Promise<Log[]> {
    const response = await this.client.get<Log[]>('/search/text', {
      params: { q: query, limit },
    })
    return response.data
  }

  // Dashboard stats
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/dashboard/stats')
    return response.data
  }

  // Trends endpoints
  async getTrendSummary(): Promise<TrendSummary> {
    const response = await this.client.get<TrendSummary>('/trends/summary')
    return response.data
  }

  async getSuccessRateTrend(
    period: 'daily' | 'weekly' | 'monthly' = 'daily',
    days: number = 30
  ): Promise<SuccessRateTrend> {
    const response = await this.client.get<SuccessRateTrend>('/trends/success-rate', {
      params: { period, days },
    })
    return response.data
  }

  async getFailureAnalysis(days: number = 30): Promise<FailureAnalysis> {
    const response = await this.client.get<FailureAnalysis>('/trends/failures', {
      params: { days },
    })
    return response.data
  }

  // Notification endpoints
  async getNotificationConfigs(): Promise<NotificationConfig[]> {
    const response = await this.client.get<NotificationConfig[]>('/notifications/configs')
    return response.data
  }

  async createNotificationConfig(config: {
    channel: string
    webhook_url: string
    enabled: boolean
    events: string[]
  }): Promise<NotificationConfig> {
    const response = await this.client.post<NotificationConfig>('/notifications/configs', config)
    return response.data
  }

  async deleteNotificationConfig(channel: string): Promise<void> {
    await this.client.delete(`/notifications/configs/${channel}`)
  }

  async testNotification(channel: string): Promise<TestNotificationResult> {
    const response = await this.client.post<TestNotificationResult>('/notifications/test', {
      channel,
    })
    return response.data
  }
}

// Type definitions for new endpoints
interface TrendSummary {
  total_runs_today: number
  total_runs_yesterday: number
  runs_change_percent: number
  success_rate_today: number
  success_rate_yesterday: number
  success_rate_direction: string
  total_failures_today: number
  total_failures_yesterday: number
  failures_change_percent: number
  avg_duration_seconds: number
  duration_change_percent: number
  most_active_repositories: Array<{ id: number; name: string; runs: number }>
  most_failing_workflows: Array<{ id: number; name: string; failures: number }>
}

interface TrendPoint {
  timestamp: string
  value: number
  count: number
}

interface SuccessRateTrend {
  period: string
  points: TrendPoint[]
  average_rate: number
  direction: string
  change_percent: number
}

interface FailureAnalysis {
  total_failures: number
  unique_errors: number
  top_failing_workflows: Array<{ id: number; name: string; count: number }>
  top_failing_repositories: Array<{ id: number; name: string; count: number }>
  most_common_errors: Array<{ error: string; count: number }>
}

interface NotificationConfig {
  channel: string
  enabled: boolean
  events: string[]
  repository_filter: string[]
  webhook_configured: boolean
}

interface TestNotificationResult {
  success: boolean
  channel: string
  message: string
  error: string | null
}

export const api = new ApiClient()
export default api
