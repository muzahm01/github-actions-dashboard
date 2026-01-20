<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkflowsStore } from '@/stores/workflows'
import { RouterLink } from 'vue-router'

const route = useRoute()
const store = useWorkflowsStore()

const workflowId = () => Number(route.params.id)

onMounted(() => {
  store.fetchWorkflow(workflowId())
  store.fetchWorkflowRuns(workflowId())
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      store.fetchWorkflow(Number(newId))
      store.fetchWorkflowRuns(Number(newId))
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
              {{ store.currentWorkflow?.name || 'Loading...' }}
            </span>
          </div>
        </li>
      </ol>
    </nav>

    <!-- Workflow Header -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-xl font-bold text-gray-900">
              {{ store.currentWorkflow?.name }}
            </h1>
            <p class="mt-1 text-sm text-gray-500">{{ store.currentWorkflow?.path }}</p>
          </div>
          <span
            v-if="store.currentWorkflow"
            :class="[
              'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium',
              store.currentWorkflow.state === 'active'
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700',
            ]"
          >
            {{ store.currentWorkflow.state }}
          </span>
        </div>
      </div>
    </div>

    <!-- Runs List -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <div class="px-4 py-5 sm:px-6">
        <h2 class="text-lg font-medium text-gray-900">Recent Runs</h2>
      </div>
      <div class="border-t border-gray-200">
        <ul role="list" class="divide-y divide-gray-200">
          <li
            v-for="run in store.workflowRuns"
            :key="run.id"
            class="hover:bg-gray-50"
          >
            <RouterLink :to="`/runs/${run.id}`" class="block px-4 py-4">
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-3">
                    <span
                      :class="[
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        statusColor(run.conclusion || run.status),
                      ]"
                    >
                      {{ run.conclusion || run.status }}
                    </span>
                    <p class="text-sm font-medium text-gray-900">
                      {{ run.display_title || run.name }}
                    </p>
                  </div>
                  <div class="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                    <span>#{{ run.run_number }}</span>
                    <span>{{ run.head_branch }}</span>
                    <span>{{ run.head_sha?.substring(0, 7) }}</span>
                    <span>{{ formatDuration(run.duration_seconds) }}</span>
                  </div>
                </div>
                <div class="ml-4 flex items-center space-x-4">
                  <span class="text-sm text-gray-500">{{ formatDate(run.created_at) }}</span>
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
          <li v-if="store.workflowRuns.length === 0 && !store.isLoading" class="px-4 py-8 text-center text-gray-500">
            No runs found for this workflow
          </li>
        </ul>
      </div>
    </div>

    <!-- Pagination -->
    <div
      v-if="store.pagination.pages > 1"
      class="flex items-center justify-between"
    >
      <button
        :disabled="store.pagination.page === 1"
        class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
        @click="store.previousPage()"
      >
        Previous
      </button>
      <span class="text-sm text-gray-500">
        Page {{ store.pagination.page }} of {{ store.pagination.pages }}
      </span>
      <button
        :disabled="!store.hasMorePages"
        class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
        @click="store.nextPage()"
      >
        Next
      </button>
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
