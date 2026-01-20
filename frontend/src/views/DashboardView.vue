<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { RouterLink } from 'vue-router'

const store = useDashboardStore()

onMounted(() => {
  store.fetchStats()
  store.fetchRepositories()
  store.fetchRecentFailures()
})

const statusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failure':
      return 'bg-red-100 text-red-800'
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-1 text-sm text-gray-500">Overview of your GitHub Actions workflows</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
        <dt class="truncate text-sm font-medium text-gray-500">Total Repositories</dt>
        <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
          {{ store.stats?.total_repositories ?? 0 }}
        </dd>
      </div>
      <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
        <dt class="truncate text-sm font-medium text-gray-500">Total Workflows</dt>
        <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
          {{ store.stats?.total_workflows ?? 0 }}
        </dd>
      </div>
      <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
        <dt class="truncate text-sm font-medium text-gray-500">Total Runs (24h)</dt>
        <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
          {{ store.stats?.total_runs_24h ?? 0 }}
        </dd>
      </div>
      <div class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
        <dt class="truncate text-sm font-medium text-gray-500">Success Rate</dt>
        <dd class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
          {{ store.stats?.success_rate ? `${(store.stats.success_rate * 100).toFixed(1)}%` : 'N/A' }}
        </dd>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Active Repositories -->
      <div class="overflow-hidden rounded-lg bg-white shadow">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg font-medium leading-6 text-gray-900">Active Repositories</h3>
        </div>
        <div class="border-t border-gray-200">
          <ul role="list" class="divide-y divide-gray-200">
            <li
              v-for="repo in store.repositories"
              :key="repo.id"
              class="px-4 py-4 hover:bg-gray-50"
            >
              <RouterLink
                :to="`/repositories?id=${repo.id}`"
                class="flex items-center justify-between"
              >
                <div>
                  <p class="text-sm font-medium text-indigo-600">{{ repo.full_name }}</p>
                  <p class="text-sm text-gray-500">{{ repo.default_branch }}</p>
                </div>
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
              </RouterLink>
            </li>
            <li v-if="store.repositories.length === 0" class="px-4 py-8 text-center text-gray-500">
              No repositories found
            </li>
          </ul>
        </div>
      </div>

      <!-- Recent Failures -->
      <div class="overflow-hidden rounded-lg bg-white shadow">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg font-medium leading-6 text-gray-900">Recent Failures</h3>
        </div>
        <div class="border-t border-gray-200">
          <ul role="list" class="divide-y divide-gray-200">
            <li
              v-for="failure in store.recentFailures"
              :key="failure.id"
              class="px-4 py-4 hover:bg-gray-50"
            >
              <RouterLink :to="`/runs/${failure.id}`" class="block">
                <div class="flex items-center justify-between">
                  <p class="truncate text-sm font-medium text-indigo-600">
                    {{ failure.display_title || failure.name }}
                  </p>
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      statusColor(failure.conclusion || failure.status),
                    ]"
                  >
                    {{ failure.conclusion || failure.status }}
                  </span>
                </div>
                <div class="mt-2 flex justify-between text-sm text-gray-500">
                  <p>{{ failure.head_branch }}</p>
                  <p>{{ formatDate(failure.created_at) }}</p>
                </div>
              </RouterLink>
            </li>
            <li v-if="store.recentFailures.length === 0" class="px-4 py-8 text-center text-gray-500">
              No recent failures
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading" class="flex items-center justify-center py-12">
      <svg
        class="h-8 w-8 animate-spin text-indigo-600"
        fill="none"
        viewBox="0 0 24 24"
      >
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

    <!-- Error State -->
    <div
      v-if="store.error"
      class="rounded-md bg-red-50 p-4"
    >
      <div class="flex">
        <svg
          class="h-5 w-5 text-red-400"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clip-rule="evenodd"
          />
        </svg>
        <div class="ml-3">
          <p class="text-sm font-medium text-red-800">{{ store.error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
