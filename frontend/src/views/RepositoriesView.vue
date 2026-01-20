<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useWorkflowsStore } from '@/stores/workflows'
import { RouterLink } from 'vue-router'

const dashboardStore = useDashboardStore()
const workflowsStore = useWorkflowsStore()

const selectedRepoId = ref<number | null>(null)

onMounted(() => {
  dashboardStore.fetchRepositories()
})

function selectRepository(repoId: number) {
  selectedRepoId.value = repoId
  workflowsStore.fetchWorkflows(repoId)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Repositories</h1>
      <p class="mt-1 text-sm text-gray-500">Manage your monitored GitHub repositories</p>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Repository List -->
      <div class="lg:col-span-1">
        <div class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h3 class="text-lg font-medium leading-6 text-gray-900">All Repositories</h3>
          </div>
          <div class="border-t border-gray-200">
            <ul role="list" class="divide-y divide-gray-200">
              <li
                v-for="repo in dashboardStore.repositories"
                :key="repo.id"
                :class="[
                  'cursor-pointer px-4 py-4 transition-colors',
                  selectedRepoId === repo.id ? 'bg-indigo-50' : 'hover:bg-gray-50',
                ]"
                @click="selectRepository(repo.id)"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p
                      :class="[
                        'text-sm font-medium',
                        selectedRepoId === repo.id ? 'text-indigo-700' : 'text-gray-900',
                      ]"
                    >
                      {{ repo.full_name }}
                    </p>
                    <p class="text-sm text-gray-500">{{ repo.default_branch }}</p>
                  </div>
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium',
                      repo.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700',
                    ]"
                  >
                    {{ repo.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </li>
              <li
                v-if="dashboardStore.repositories.length === 0"
                class="px-4 py-8 text-center text-gray-500"
              >
                No repositories found
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Repository Details / Workflows -->
      <div class="lg:col-span-2">
        <div v-if="selectedRepoId" class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:px-6">
            <h3 class="text-lg font-medium leading-6 text-gray-900">Workflows</h3>
            <p class="mt-1 text-sm text-gray-500">
              Workflows for {{ dashboardStore.repositories.find((r) => r.id === selectedRepoId)?.full_name }}
            </p>
          </div>
          <div class="border-t border-gray-200">
            <ul role="list" class="divide-y divide-gray-200">
              <li
                v-for="workflow in workflowsStore.workflows"
                :key="workflow.id"
                class="hover:bg-gray-50"
              >
                <RouterLink
                  :to="`/workflows/${workflow.id}`"
                  class="block px-4 py-4"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-indigo-600">{{ workflow.name }}</p>
                      <p class="text-sm text-gray-500">{{ workflow.path }}</p>
                    </div>
                    <div class="flex items-center space-x-4">
                      <span
                        :class="[
                          'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium',
                          workflow.state === 'active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700',
                        ]"
                      >
                        {{ workflow.state }}
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
              <li
                v-if="workflowsStore.workflows.length === 0 && !workflowsStore.isLoading"
                class="px-4 py-8 text-center text-gray-500"
              >
                No workflows found for this repository
              </li>
            </ul>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else
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
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Select a repository</h3>
            <p class="mt-1 text-sm text-gray-500">Choose a repository to view its workflows</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="dashboardStore.isLoading || workflowsStore.isLoading"
      class="flex items-center justify-center py-12"
    >
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
