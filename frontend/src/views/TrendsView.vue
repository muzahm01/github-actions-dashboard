<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/client'

interface TrendPoint {
  timestamp: string
  value: number
  count: number
}

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

interface SuccessRateTrend {
  period: string
  points: TrendPoint[]
  average_rate: number
  direction: string
  change_percent: number
}

const summary = ref<TrendSummary | null>(null)
const successRateTrend = ref<SuccessRateTrend | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)
const selectedPeriod = ref<'daily' | 'weekly' | 'monthly'>('daily')
const selectedDays = ref(30)

onMounted(async () => {
  await fetchTrends()
})

async function fetchTrends() {
  isLoading.value = true
  error.value = null

  try {
    const [summaryData, trendData] = await Promise.all([
      api.getTrendSummary(),
      api.getSuccessRateTrend(selectedPeriod.value, selectedDays.value),
    ])
    summary.value = summaryData
    successRateTrend.value = trendData
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load trends'
  } finally {
    isLoading.value = false
  }
}

async function changePeriod(period: 'daily' | 'weekly' | 'monthly') {
  selectedPeriod.value = period
  await fetchTrends()
}

const directionIcon = (direction: string) => {
  if (direction === 'up') return '↑'
  if (direction === 'down') return '↓'
  return '→'
}

const directionColor = (direction: string, isGood: boolean = true) => {
  if (direction === 'up') return isGood ? 'text-green-600' : 'text-red-600'
  if (direction === 'down') return isGood ? 'text-red-600' : 'text-green-600'
  return 'text-gray-500'
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
}

const formatPercent = (value: number) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Trends & Analytics</h1>
        <p class="mt-1 text-sm text-gray-500">Monitor workflow performance over time</p>
      </div>
      <div class="flex space-x-2">
        <button
          v-for="period in ['daily', 'weekly', 'monthly']"
          :key="period"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-md',
            selectedPeriod === period
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50',
          ]"
          @click="changePeriod(period as 'daily' | 'weekly' | 'monthly')"
        >
          {{ period.charAt(0).toUpperCase() + period.slice(1) }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <svg class="h-8 w-8 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-md bg-red-50 p-4">
      <div class="flex">
        <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clip-rule="evenodd"
          />
        </svg>
        <div class="ml-3">
          <p class="text-sm font-medium text-red-800">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <template v-else-if="summary">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Total Runs -->
        <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
          <dt class="truncate text-sm font-medium text-gray-500">Total Runs (Today)</dt>
          <dd class="mt-1 flex items-baseline justify-between">
            <span class="text-3xl font-semibold tracking-tight text-gray-900">
              {{ summary.total_runs_today }}
            </span>
            <span
              :class="[
                'text-sm font-medium',
                summary.runs_change_percent >= 0 ? 'text-green-600' : 'text-red-600',
              ]"
            >
              {{ formatPercent(summary.runs_change_percent) }}
            </span>
          </dd>
          <dd class="mt-1 text-xs text-gray-500">vs {{ summary.total_runs_yesterday }} yesterday</dd>
        </div>

        <!-- Success Rate -->
        <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
          <dt class="truncate text-sm font-medium text-gray-500">Success Rate</dt>
          <dd class="mt-1 flex items-baseline justify-between">
            <span class="text-3xl font-semibold tracking-tight text-gray-900">
              {{ summary.success_rate_today.toFixed(1) }}%
            </span>
            <span :class="['text-sm font-medium', directionColor(summary.success_rate_direction)]">
              {{ directionIcon(summary.success_rate_direction) }}
            </span>
          </dd>
          <dd class="mt-1 text-xs text-gray-500">
            vs {{ summary.success_rate_yesterday.toFixed(1) }}% yesterday
          </dd>
        </div>

        <!-- Failures -->
        <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
          <dt class="truncate text-sm font-medium text-gray-500">Failures (Today)</dt>
          <dd class="mt-1 flex items-baseline justify-between">
            <span class="text-3xl font-semibold tracking-tight text-gray-900">
              {{ summary.total_failures_today }}
            </span>
            <span
              :class="[
                'text-sm font-medium',
                summary.failures_change_percent <= 0 ? 'text-green-600' : 'text-red-600',
              ]"
            >
              {{ formatPercent(summary.failures_change_percent) }}
            </span>
          </dd>
          <dd class="mt-1 text-xs text-gray-500">vs {{ summary.total_failures_yesterday }} yesterday</dd>
        </div>

        <!-- Average Duration -->
        <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
          <dt class="truncate text-sm font-medium text-gray-500">Avg Duration</dt>
          <dd class="mt-1 flex items-baseline justify-between">
            <span class="text-3xl font-semibold tracking-tight text-gray-900">
              {{ formatDuration(summary.avg_duration_seconds) }}
            </span>
            <span
              :class="[
                'text-sm font-medium',
                summary.duration_change_percent <= 0 ? 'text-green-600' : 'text-red-600',
              ]"
            >
              {{ formatPercent(summary.duration_change_percent) }}
            </span>
          </dd>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Success Rate Trend -->
        <div class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h3 class="text-lg font-medium leading-6 text-gray-900">Success Rate Trend</h3>
            <p class="mt-1 text-sm text-gray-500">
              Average: {{ successRateTrend?.average_rate.toFixed(1) }}%
              <span :class="directionColor(successRateTrend?.direction || 'stable')">
                ({{ formatPercent(successRateTrend?.change_percent || 0) }})
              </span>
            </p>
          </div>
          <div class="border-t border-gray-200 px-4 py-5 sm:p-6">
            <!-- Simple bar visualization -->
            <div class="flex items-end space-x-1 h-32">
              <div
                v-for="(point, index) in successRateTrend?.points.slice(-14)"
                :key="index"
                class="flex-1 bg-indigo-500 rounded-t"
                :style="{ height: `${point.value * 100}%` }"
                :title="`${new Date(point.timestamp).toLocaleDateString()}: ${(point.value * 100).toFixed(1)}%`"
              />
            </div>
            <div class="mt-2 flex justify-between text-xs text-gray-500">
              <span>{{ successRateTrend?.points[0]?.timestamp.slice(0, 10) }}</span>
              <span>{{ successRateTrend?.points[successRateTrend.points.length - 1]?.timestamp.slice(0, 10) }}</span>
            </div>
          </div>
        </div>

        <!-- Most Active Repositories -->
        <div class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h3 class="text-lg font-medium leading-6 text-gray-900">Most Active Repositories</h3>
          </div>
          <div class="border-t border-gray-200">
            <ul role="list" class="divide-y divide-gray-200">
              <li
                v-for="repo in summary.most_active_repositories"
                :key="repo.id"
                class="px-4 py-3 flex items-center justify-between"
              >
                <span class="text-sm font-medium text-gray-900">{{ repo.name }}</span>
                <span class="text-sm text-gray-500">{{ repo.runs }} runs</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Most Failing Workflows -->
        <div class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h3 class="text-lg font-medium leading-6 text-gray-900">Most Failing Workflows</h3>
          </div>
          <div class="border-t border-gray-200">
            <ul role="list" class="divide-y divide-gray-200">
              <li
                v-for="workflow in summary.most_failing_workflows"
                :key="workflow.id"
                class="px-4 py-3 flex items-center justify-between"
              >
                <span class="text-sm font-medium text-gray-900">{{ workflow.name }}</span>
                <span class="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                  {{ workflow.failures }} failures
                </span>
              </li>
              <li v-if="summary.most_failing_workflows.length === 0" class="px-4 py-8 text-center text-gray-500">
                No failures recorded
              </li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
