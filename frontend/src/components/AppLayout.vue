<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const isSidebarOpen = ref(true)

const navigation = [
  { name: 'Dashboard', href: '/', icon: 'home' },
  { name: 'Repositories', href: '/repositories', icon: 'folder' },
  { name: 'Workflows', href: '/workflows', icon: 'play' },
  { name: 'Trends', href: '/trends', icon: 'chart' },
  { name: 'Search', href: '/search', icon: 'search' },
  { name: 'Notifications', href: '/notifications', icon: 'bell' },
]

function isActive(href: string): boolean {
  return route.path === href || (href !== '/' && route.path.startsWith(href))
}

function toggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-gray-900 transition-all duration-300',
        isSidebarOpen ? 'w-64' : 'w-16',
      ]"
    >
      <!-- Logo -->
      <div class="flex h-16 items-center justify-between px-4">
        <div class="flex items-center space-x-3" v-if="isSidebarOpen">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
            <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <span class="text-lg font-semibold text-white">GHA Dashboard</span>
        </div>
        <button
          @click="toggleSidebar"
          class="flex h-10 w-10 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 space-y-1 px-2 py-4">
        <RouterLink
          v-for="item in navigation"
          :key="item.name"
          :to="item.href"
          :class="[
            'group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive(item.href)
              ? 'bg-gray-800 text-white'
              : 'text-gray-400 hover:bg-gray-800 hover:text-white',
          ]"
        >
          <!-- Icons -->
          <svg
            v-if="item.icon === 'home'"
            class="mr-3 h-5 w-5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
            />
          </svg>
          <svg
            v-else-if="item.icon === 'folder'"
            class="mr-3 h-5 w-5 flex-shrink-0"
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
          <svg
            v-else-if="item.icon === 'play'"
            class="mr-3 h-5 w-5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <svg
            v-else-if="item.icon === 'search'"
            class="mr-3 h-5 w-5 flex-shrink-0"
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
          <svg
            v-else-if="item.icon === 'chart'"
            class="mr-3 h-5 w-5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <svg
            v-else-if="item.icon === 'bell'"
            class="mr-3 h-5 w-5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <span v-if="isSidebarOpen">{{ item.name }}</span>
        </RouterLink>
      </nav>
    </aside>

    <!-- Main content -->
    <main
      :class="['min-h-screen transition-all duration-300', isSidebarOpen ? 'ml-64' : 'ml-16']"
    >
      <div class="px-4 py-6 sm:px-6 lg:px-8">
        <slot />
      </div>
    </main>
  </div>
</template>
