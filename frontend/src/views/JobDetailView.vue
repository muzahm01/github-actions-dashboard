<script setup lang="ts">
import { onMounted, watch, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkflowsStore } from '@/stores/workflows'
import { RouterLink } from 'vue-router'

const route = useRoute()
const store = useWorkflowsStore()
const selectedLogId = ref<number | null>(null)

const jobId = () => Number(route.params.id)

onMounted(() => {
  store.fetchJob(jobId())
  store.fetchJobLogs(jobId())
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      store.fetchJob(Number(newId))
      store.fetchJobLogs(Number(newId))
      selectedLogId.value = null
      store.analysis = null
    }
  }
)

const selectedLog = computed(() => {
  if (!selectedLogId.value) return null
  return store.logs.find((l) => l.id === selectedLogId.value) || null
})

function selectLog(logId: number) {
  selectedLogId.value = logId
  store.fetchAnalysis(logId)
}

function requestNewAnalysis() {
  if (selectedLogId.value) {
    store.requestAnalysis(selectedLogId.value)
  }
}

const statusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failure':
      return 'bg-red-100 text-red-800'
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800'
    case 'skipped':
      return 'bg-gray-100 text-gray-600'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const formatDuration = (seconds: number | null) => {
  if (!seconds) return 'N/A'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Breadcrumb -->
    <nav class="flex" aria-label="Breadcrumb">
      <ol role="list" class="flex items-center space-x-4">
        <li>
          <RouterLink to="/workflows" class="text-gray-400 hover:text-gray-500">
            <svg class="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-3a1 1 0 00-1-1H9a1 1 0 00-1 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z"
                clip-rule="evenodd"
              />
            </svg>
          </RouterLink>
        </li>
        <li>
          <div class="flex items-center">
            <svg class="h-5 w-5 flex-shrink-0 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
            </svg>
            <RouterLink to="/workflows" class="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">
              Workflows
            </RouterLink>
          </div>
        </li>
        <li v-if="store.currentJob?.workflow_run_id">
          <div class="flex items-center">
            <svg class="h-5 w-5 flex-shrink-0 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
            </svg>
            <RouterLink
              :to="`/runs/${store.currentJob.workflow_run_id}`"
              class="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              Run
            </RouterLink>
          </div>
        </li>
        <li>
          <div class="flex items-center">
            <svg class="h-5 w-5 flex-shrink-0 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
            </svg>
            <span class="ml-4 text-sm font-medium text-gray-500">
              {{ store.currentJob?.name || 'Loading...' }}
            </span>
          </div>
        </li>
      </ol>
    </nav>

    <!-- Job Header -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-3">
              <span
                v-if="store.currentJob"
                :class="[
                  'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium',
                  statusColor(store.currentJob.conclusion || store.currentJob.status),
                ]"
              >
                {{ store.currentJob.conclusion || store.currentJob.status }}
              </span>
              <h1 class="text-xl font-bold text-gray-900">{{ store.currentJob?.name }}</h1>
            </div>
            <div class="mt-2 flex items-center space-x-4 text-sm text-gray-500">
              <span v-if="store.currentJob?.runner_name">
                Runner: {{ store.currentJob.runner_name }}
              </span>
              <span v-if="store.currentJob?.runner_os">
                OS: {{ store.currentJob.runner_os }}
              </span>
            </div>
          </div>
          <div class="text-right text-sm text-gray-500">
            <p v-if="store.currentJob?.started_at">Started: {{ formatDate(store.currentJob.started_at) }}</p>
            <p v-if="store.currentJob?.duration_seconds">
              Duration: {{ formatDuration(store.currentJob.duration_seconds) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Steps -->
    <div v-if="store.currentJob?.steps?.length" class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <h2 class="text-lg font-medium text-gray-900">Steps</h2>
      </div>
      <div class="border-t border-gray-200">
        <ul role="list" class="divide-y divide-gray-200">
          <li
            v-for="step in store.currentJob.steps"
            :key="step.number"
            class="px-4 py-3"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <span class="text-sm font-medium text-gray-500">{{ step.number }}.</span>
                <span
                  :class="[
                    'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                    statusColor(step.conclusion || step.status),
                  ]"
                >
                  {{ step.conclusion || step.status }}
                </span>
                <span class="text-sm text-gray-900">{{ step.name }}</span>
              </div>
              <span class="text-sm text-gray-500">
                {{ formatDuration(step.duration_seconds) }}
              </span>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- Logs Section -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Log List -->
      <div class="overflow-hidden rounded-lg bg-white shadow">
        <div class="px-4 py-5 sm:px-6">
          <h2 class="text-lg font-medium text-gray-900">Logs</h2>
        </div>
        <div class="border-t border-gray-200">
          <ul role="list" class="divide-y divide-gray-200">
            <li
              v-for="log in store.logs"
              :key="log.id"
              :class="[
                'cursor-pointer px-4 py-3 transition-colors',
                selectedLogId === log.id ? 'bg-indigo-50' : 'hover:bg-gray-50',
              ]"
              @click="selectLog(log.id)"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ log.step_name || 'Log' }}</p>
                  <p class="text-xs text-gray-500">{{ formatDate(log.created_at) }}</p>
                </div>
                <span
                  v-if="log.has_error"
                  class="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                >
                  Error
                </span>
              </div>
            </li>
            <li v-if="store.logs.length === 0 && !store.isLoading" class="px-4 py-8 text-center text-gray-500">
              No logs available
            </li>
          </ul>
        </div>
      </div>

      <!-- Log Content / Analysis -->
      <div class="space-y-6">
        <!-- Log Content -->
        <div v-if="selectedLog" class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h2 class="text-lg font-medium text-gray-900">Log Content</h2>
          </div>
          <div class="border-t border-gray-200 p-4">
            <pre class="max-h-64 overflow-auto rounded-lg bg-gray-900 p-4 text-sm text-gray-100">{{ selectedLog.content }}</pre>
          </div>
        </div>

        <!-- AI Analysis -->
        <div v-if="selectedLog" class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-medium text-gray-900">AI Analysis</h2>
              <button
                class="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
                :disabled="store.isLoading"
                @click="requestNewAnalysis"
              >
                {{ store.analysis ? 'Re-analyze' : 'Analyze' }}
              </button>
            </div>
          </div>
          <div class="border-t border-gray-200 p-4">
            <div v-if="store.analysis" class="space-y-4">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Summary</h3>
                <p class="mt-1 text-sm text-gray-600">{{ store.analysis.summary }}</p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-gray-900">Root Cause</h3>
                <p class="mt-1 text-sm text-gray-600">{{ store.analysis.root_cause }}</p>
              </div>
              <div v-if="store.analysis.suggested_fix">
                <h3 class="text-sm font-medium text-gray-900">Suggested Fix</h3>
                <pre class="mt-1 overflow-auto rounded-lg bg-gray-100 p-3 text-sm text-gray-800">{{ store.analysis.suggested_fix }}</pre>
              </div>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <span>Confidence: {{ (store.analysis.confidence * 100).toFixed(0) }}%</span>
                <span>Analyzed: {{ formatDate(store.analysis.created_at) }}</span>
              </div>
            </div>
            <div v-else-if="store.isLoading" class="flex items-center justify-center py-8">
              <svg class="h-6 w-6 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <p v-else class="text-center text-sm text-gray-500">
              Click "Analyze" to get AI-powered insights about this log
            </p>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="!selectedLog"
          class="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white"
        >
          <div class="text-center">
            <svg
              class="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Select a log</h3>
            <p class="mt-1 text-sm text-gray-500">Choose a log to view its content and analysis</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading && !selectedLog" class="flex items-center justify-center py-12">
      <svg class="h-8 w-8 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  </div>
</template>
