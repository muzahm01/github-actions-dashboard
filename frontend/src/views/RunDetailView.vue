<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkflowsStore } from '@/stores/workflows'
import { RouterLink } from 'vue-router'

const route = useRoute()
const store = useWorkflowsStore()

const runId = () => Number(route.params.id)

onMounted(() => {
  store.fetchWorkflowRun(runId())
  store.fetchJobs(runId())
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      store.fetchWorkflowRun(Number(newId))
      store.fetchJobs(Number(newId))
    }
  }
)

const statusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failure':
      return 'bg-red-100 text-red-800'
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800'
    case 'queued':
      return 'bg-blue-100 text-blue-800'
    case 'skipped':
      return 'bg-gray-100 text-gray-600'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const statusIcon = (status: string) => {
  switch (status) {
    case 'success':
      return 'M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z'
    case 'failure':
      return 'M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
    default:
      return 'M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z'
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
            <svg
              class="h-5 w-5 flex-shrink-0 text-gray-300"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
            </svg>
            <RouterLink to="/workflows" class="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">
              Workflows
            </RouterLink>
          </div>
        </li>
        <li>
          <div class="flex items-center">
            <svg
              class="h-5 w-5 flex-shrink-0 text-gray-300"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
            </svg>
            <span class="ml-4 text-sm font-medium text-gray-500">
              Run #{{ store.currentRun?.run_number || '...' }}
            </span>
          </div>
        </li>
      </ol>
    </nav>

    <!-- Run Header -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-3">
              <span
                v-if="store.currentRun"
                :class="[
                  'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium',
                  statusColor(store.currentRun.conclusion || store.currentRun.status),
                ]"
              >
                {{ store.currentRun.conclusion || store.currentRun.status }}
              </span>
              <h1 class="text-xl font-bold text-gray-900">
                {{ store.currentRun?.display_title || store.currentRun?.name }}
              </h1>
            </div>
            <div class="mt-2 flex items-center space-x-4 text-sm text-gray-500">
              <span v-if="store.currentRun">#{{ store.currentRun.run_number }}</span>
              <span v-if="store.currentRun?.head_branch">
                <svg class="mr-1 inline h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                {{ store.currentRun.head_branch }}
              </span>
              <span v-if="store.currentRun?.head_sha">
                {{ store.currentRun.head_sha.substring(0, 7) }}
              </span>
            </div>
          </div>
          <div class="text-right text-sm text-gray-500">
            <p v-if="store.currentRun?.created_at">Started: {{ formatDate(store.currentRun.created_at) }}</p>
            <p v-if="store.currentRun?.duration_seconds">
              Duration: {{ formatDuration(store.currentRun.duration_seconds) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Jobs List -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <h2 class="text-lg font-medium text-gray-900">Jobs</h2>
      </div>
      <div class="border-t border-gray-200">
        <ul role="list" class="divide-y divide-gray-200">
          <li
            v-for="job in store.jobs"
            :key="job.id"
            class="hover:bg-gray-50"
          >
            <RouterLink :to="`/jobs/${job.id}`" class="block px-4 py-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <span
                    :class="[
                      'flex h-8 w-8 items-center justify-center rounded-full',
                      job.conclusion === 'success'
                        ? 'bg-green-100'
                        : job.conclusion === 'failure'
                          ? 'bg-red-100'
                          : 'bg-gray-100',
                    ]"
                  >
                    <svg
                      :class="[
                        'h-5 w-5',
                        job.conclusion === 'success'
                          ? 'text-green-600'
                          : job.conclusion === 'failure'
                            ? 'text-red-600'
                            : 'text-gray-600',
                      ]"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" :d="statusIcon(job.conclusion || job.status)" clip-rule="evenodd" />
                    </svg>
                  </span>
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ job.name }}</p>
                    <p class="text-sm text-gray-500">{{ job.runner_name || 'No runner assigned' }}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-4">
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      statusColor(job.conclusion || job.status),
                    ]"
                  >
                    {{ job.conclusion || job.status }}
                  </span>
                  <span class="text-sm text-gray-500">
                    {{ formatDuration(job.duration_seconds) }}
                  </span>
                  <svg
                    class="h-5 w-5 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </RouterLink>
          </li>
          <li v-if="store.jobs.length === 0 && !store.isLoading" class="px-4 py-8 text-center text-gray-500">
            No jobs found for this run
          </li>
        </ul>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading" class="flex items-center justify-center py-12">
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
