<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/api/client'
import type { SearchResult } from '@/types'

const query = ref('')
const results = ref<SearchResult[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

async function search() {
  if (!query.value.trim()) return

  isLoading.value = true
  error.value = null
  hasSearched.value = true

  try {
    results.value = await api.search(query.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Search failed'
    results.value = []
  } finally {
    isLoading.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    search()
  }
}

const typeIcon = (type: string) => {
  switch (type) {
    case 'workflow':
      return 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'run':
      return 'M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z'
    case 'job':
      return 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'
    case 'log':
      return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
    default:
      return 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
  }
}

const typeColor = (type: string) => {
  switch (type) {
    case 'workflow':
      return 'bg-purple-100 text-purple-800'
    case 'run':
      return 'bg-blue-100 text-blue-800'
    case 'job':
      return 'bg-green-100 text-green-800'
    case 'log':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getLink = (result: SearchResult) => {
  switch (result.type) {
    case 'workflow':
      return `/workflows/${result.id}`
    case 'run':
      return `/runs/${result.id}`
    case 'job':
      return `/jobs/${result.id}`
    case 'log':
      return `/jobs/${result.metadata?.job_id || result.id}`
    default:
      return '/'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Search</h1>
      <p class="mt-1 text-sm text-gray-500">Search across workflows, runs, jobs, and logs</p>
    </div>

    <!-- Search Input -->
    <div class="relative">
      <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
        <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <input
        v-model="query"
        type="text"
        class="block w-full rounded-lg border-0 py-3 pl-10 pr-24 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        placeholder="Search for errors, workflow names, commit messages..."
        @keydown="handleKeydown"
      />
      <div class="absolute inset-y-0 right-0 flex items-center pr-3">
        <button
          class="rounded-md bg-indigo-600 px-4 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
          :disabled="isLoading || !query.trim()"
          @click="search"
        >
          {{ isLoading ? 'Searching...' : 'Search' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="hasSearched" class="space-y-4">
      <p class="text-sm text-gray-500">
        {{ results.length }} result{{ results.length !== 1 ? 's' : '' }} found
      </p>

      <div class="overflow-hidden rounded-lg bg-white shadow">
        <ul role="list" class="divide-y divide-gray-200">
          <li
            v-for="result in results"
            :key="`${result.type}-${result.id}`"
            class="hover:bg-gray-50"
          >
            <RouterLink :to="getLink(result)" class="block px-4 py-4">
              <div class="flex items-start space-x-4">
                <div
                  :class="[
                    'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg',
                    typeColor(result.type),
                  ]"
                >
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      :d="typeIcon(result.type)"
                    />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center space-x-2">
                    <span
                      :class="[
                        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                        typeColor(result.type),
                      ]"
                    >
                      {{ result.type }}
                    </span>
                    <p class="truncate text-sm font-medium text-gray-900">{{ result.title }}</p>
                  </div>
                  <p v-if="result.description" class="mt-1 truncate text-sm text-gray-500">
                    {{ result.description }}
                  </p>
                  <div class="mt-2 flex items-center space-x-4 text-xs text-gray-400">
                    <span v-if="result.score">
                      Relevance: {{ (result.score * 100).toFixed(0) }}%
                    </span>
                    <span v-if="result.metadata?.repository">
                      {{ result.metadata.repository }}
                    </span>
                    <span v-if="result.metadata?.branch">
                      {{ result.metadata.branch }}
                    </span>
                  </div>
                </div>
                <svg
                  class="h-5 w-5 flex-shrink-0 text-gray-400"
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
            </RouterLink>
          </li>
          <li v-if="results.length === 0 && !isLoading" class="px-4 py-12 text-center">
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
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No results found</h3>
            <p class="mt-1 text-sm text-gray-500">
              Try adjusting your search terms or try a different query
            </p>
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Search your workflows</h3>
        <p class="mt-1 text-sm text-gray-500">
          Find errors, workflows, runs, and logs using semantic search
        </p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
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

    <!-- Error State -->
    <div v-if="error" class="rounded-md bg-red-50 p-4">
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
  </div>
</template>
