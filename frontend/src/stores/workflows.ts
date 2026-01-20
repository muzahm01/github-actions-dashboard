/**
 * Workflows store for managing workflow-related state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Workflow, WorkflowRun, Job, Log, ErrorAnalysis } from '@/types'
import api from '@/api/client'

export const useWorkflowsStore = defineStore('workflows', () => {
  // State
  const workflows = ref<Workflow[]>([])
  const currentWorkflow = ref<Workflow | null>(null)
  const workflowRuns = ref<WorkflowRun[]>([])
  const currentRun = ref<WorkflowRun | null>(null)
  const jobs = ref<Job[]>([])
  const currentJob = ref<Job | null>(null)
  const logs = ref<Log[]>([])
  const analysis = ref<ErrorAnalysis | null>(null)

  const pagination = ref({
    page: 1,
    perPage: 20,
    total: 0,
    pages: 0,
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const failedRuns = computed(() =>
    workflowRuns.value.filter((run) => run.conclusion === 'failure')
  )

  const successfulRuns = computed(() =>
    workflowRuns.value.filter((run) => run.conclusion === 'success')
  )

  const failedJobs = computed(() =>
    jobs.value.filter((job) => job.conclusion === 'failure')
  )

  const hasMorePages = computed(() => pagination.value.page < pagination.value.pages)

  // Actions
  async function fetchWorkflows(repoId?: number) {
    isLoading.value = true
    error.value = null

    try {
      workflows.value = await api.getWorkflows(repoId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch workflows'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorkflow(id: number) {
    isLoading.value = true
    error.value = null

    try {
      currentWorkflow.value = await api.getWorkflow(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch workflow'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorkflowRuns(workflowId?: number, page: number = 1) {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.getWorkflowRuns(workflowId, page, pagination.value.perPage)
      workflowRuns.value = response.items
      pagination.value = {
        page: response.page,
        perPage: response.per_page,
        total: response.total,
        pages: response.pages,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch workflow runs'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorkflowRun(id: number) {
    isLoading.value = true
    error.value = null

    try {
      currentRun.value = await api.getWorkflowRun(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch workflow run'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchJobs(runId: number) {
    isLoading.value = true
    error.value = null

    try {
      jobs.value = await api.getJobs(runId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch jobs'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchJob(id: number) {
    isLoading.value = true
    error.value = null

    try {
      currentJob.value = await api.getJob(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch job'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchJobLogs(jobId: number) {
    isLoading.value = true
    error.value = null

    try {
      logs.value = await api.getJobLogs(jobId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch job logs'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAnalysis(logId: number) {
    isLoading.value = true
    error.value = null

    try {
      analysis.value = await api.getAnalysis(logId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch analysis'
    } finally {
      isLoading.value = false
    }
  }

  async function requestAnalysis(logId: number) {
    isLoading.value = true
    error.value = null

    try {
      await api.requestAnalysis(logId)
      // Poll for result after requesting
      await new Promise((resolve) => setTimeout(resolve, 2000))
      await fetchAnalysis(logId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to request analysis'
    } finally {
      isLoading.value = false
    }
  }

  function nextPage() {
    if (hasMorePages.value) {
      fetchWorkflowRuns(currentWorkflow.value?.id, pagination.value.page + 1)
    }
  }

  function previousPage() {
    if (pagination.value.page > 1) {
      fetchWorkflowRuns(currentWorkflow.value?.id, pagination.value.page - 1)
    }
  }

  function reset() {
    workflows.value = []
    currentWorkflow.value = null
    workflowRuns.value = []
    currentRun.value = null
    jobs.value = []
    currentJob.value = null
    logs.value = []
    analysis.value = null
    pagination.value = { page: 1, perPage: 20, total: 0, pages: 0 }
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    workflows,
    currentWorkflow,
    workflowRuns,
    currentRun,
    jobs,
    currentJob,
    logs,
    analysis,
    pagination,
    isLoading,
    error,
    // Getters
    failedRuns,
    successfulRuns,
    failedJobs,
    hasMorePages,
    // Actions
    fetchWorkflows,
    fetchWorkflow,
    fetchWorkflowRuns,
    fetchWorkflowRun,
    fetchJobs,
    fetchJob,
    fetchJobLogs,
    fetchAnalysis,
    requestAnalysis,
    nextPage,
    previousPage,
    reset,
  }
})
