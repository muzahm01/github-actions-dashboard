<script setup lang="ts">
import { onMounted } from 'vue'
import { useWorkflowsStore } from '@/stores/workflows'
import { RouterLink } from 'vue-router'

const store = useWorkflowsStore()

onMounted(() => {
  store.fetchWorkflows()
  store.fetchWorkflowRuns()
})

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
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Workflows</h1>
        <p class="mt-1 text-sm text-gray-500">View all workflow runs across repositories</p>
      </div>
    </div>

    <!-- Workflow Filter Pills -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="workflow in store.workflows"
        :key="workflow.id"
        :class="[
          'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium transition-colors',
          store.currentWorkflow?.id === workflow.id
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        ]"
        @click="store.fetchWorkflow(workflow.id); store.fetchWorkflowRuns(workflow.id)"
      >
        {{ workflow.name }}
      </button>
      <button
        v-if="store.currentWorkflow"
        class="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-200"
        @click="store.currentWorkflow = null; store.fetchWorkflowRuns()"
      >
        Clear filter
      </button>
    </div>

    <!-- Workflow Runs Table -->
    <div class="overflow-hidden rounded-lg bg-white shadow">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Run
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Status
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Branch
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Duration
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Started
            </th>
            <th scope="col" class="relative px-6 py-3">
              <span class="sr-only">View</span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-for="run in store.workflowRuns" :key="run.id" class="hover:bg-gray-50">
            <td class="whitespace-nowrap px-6 py-4">
              <div class="flex items-center">
                <div>
                  <div class="text-sm font-medium text-gray-900">
                    {{ run.display_title || run.name }}
                  </div>
                  <div class="text-sm text-gray-500">#{{ run.run_number }}</div>
                </div>
              </div>
            </td>
            <td class="whitespace-nowrap px-6 py-4">
              <span
                :class="[
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                  statusColor(run.conclusion || run.status),
                ]"
              >
                {{ run.conclusion || run.status }}
              </span>
            </td>
            <td class="whitespace-nowrap px-6 py-4">
              <div class="text-sm text-gray-900">{{ run.head_branch }}</div>
              <div class="text-sm text-gray-500">{{ run.head_sha?.substring(0, 7) }}</div>
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
              {{ formatDuration(run.duration_seconds) }}
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
              {{ formatDate(run.created_at) }}
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
              <RouterLink
                :to="`/runs/${run.id}`"
                class="text-indigo-600 hover:text-indigo-900"
              >
                View
              </RouterLink>
            </td>
          </tr>
          <tr v-if="store.workflowRuns.length === 0 && !store.isLoading">
            <td colspan="6" class="px-6 py-12 text-center text-gray-500">
              No workflow runs found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="store.pagination.pages > 1"
      class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6"
    >
      <div class="flex flex-1 justify-between sm:hidden">
        <button
          :disabled="store.pagination.page === 1"
          class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          @click="store.previousPage()"
        >
          Previous
        </button>
        <button
          :disabled="!store.hasMorePages"
          class="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          @click="store.nextPage()"
        >
          Next
        </button>
      </div>
      <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p class="text-sm text-gray-700">
            Showing page
            <span class="font-medium">{{ store.pagination.page }}</span>
            of
            <span class="font-medium">{{ store.pagination.pages }}</span>
            (<span class="font-medium">{{ store.pagination.total }}</span> total runs)
          </p>
        </div>
        <div>
          <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm">
            <button
              :disabled="store.pagination.page === 1"
              class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 disabled:opacity-50"
              @click="store.previousPage()"
            >
              <span class="sr-only">Previous</span>
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
            <button
              :disabled="!store.hasMorePages"
              class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 disabled:opacity-50"
              @click="store.nextPage()"
            >
              <span class="sr-only">Next</span>
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </nav>
        </div>
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
