/**
 * Dashboard store for managing global dashboard state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DashboardStats, Repository, WorkflowRun } from '@/types'
import api from '@/api/client'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref<DashboardStats | null>(null)
  const repositories = ref<Repository[]>([])
  const recentFailures = ref<WorkflowRun[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Getters
  const activeRepositories = computed(() =>
    repositories.value.filter((repo) => repo.is_active)
  )

  const failureCount = computed(() => recentFailures.value.length)

  const successRate = computed(() => stats.value?.success_rate_24h ?? 0)

  // Actions
  async function fetchDashboardData() {
    isLoading.value = true
    error.value = null

    try {
      const [statsData, reposData, failuresData] = await Promise.all([
        api.getDashboardStats(),
        api.getRepositories(),
        api.getRecentFailures(10),
      ])

      stats.value = statsData
      repositories.value = reposData
      recentFailures.value = failuresData
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch dashboard data'
      // Error is captured in error.value for UI display
    } finally {
      isLoading.value = false
    }
  }

  async function refreshStats() {
    try {
      stats.value = await api.getDashboardStats()
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to refresh stats'
    }
  }

  async function refreshFailures() {
    try {
      recentFailures.value = await api.getRecentFailures(10)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to refresh failures'
    }
  }

  async function fetchStats() {
    isLoading.value = true
    error.value = null
    try {
      stats.value = await api.getDashboardStats()
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch stats'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRepositories() {
    isLoading.value = true
    error.value = null
    try {
      repositories.value = await api.getRepositories()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch repositories'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRecentFailures() {
    isLoading.value = true
    error.value = null
    try {
      recentFailures.value = await api.getRecentFailures(10)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch recent failures'
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    stats.value = null
    repositories.value = []
    recentFailures.value = []
    isLoading.value = false
    error.value = null
    lastUpdated.value = null
  }

  return {
    // State
    stats,
    repositories,
    recentFailures,
    isLoading,
    error,
    lastUpdated,
    // Getters
    activeRepositories,
    failureCount,
    successRate,
    // Actions
    fetchDashboardData,
    fetchStats,
    fetchRepositories,
    fetchRecentFailures,
    refreshStats,
    refreshFailures,
    reset,
  }
})
