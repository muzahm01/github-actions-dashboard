<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/client'

type NotificationChannel = 'slack' | 'discord' | 'webhook'

interface NotificationConfig {
  channel: string
  enabled: boolean
  events: string[]
  repository_filter: string[]
  webhook_configured: boolean
}

const configs = ref<NotificationConfig[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)
const showAddModal = ref(false)
const testResult = ref<{ success: boolean; message: string; channel: string } | null>(null)

const newConfig = ref({
  channel: 'slack' as NotificationChannel,
  webhook_url: '',
  enabled: true,
  events: [] as string[],
})

const availableEvents = [
  { value: 'workflow_failed', label: 'Workflow Failed' },
  { value: 'workflow_succeeded', label: 'Workflow Succeeded' },
  { value: 'error_analysis_complete', label: 'Error Analysis Complete' },
  { value: 'daily_summary', label: 'Daily Summary' },
  { value: 'trend_alert', label: 'Trend Alert' },
]

onMounted(async () => {
  await fetchConfigs()
})

async function fetchConfigs() {
  isLoading.value = true
  error.value = null

  try {
    configs.value = await api.getNotificationConfigs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load configurations'
  } finally {
    isLoading.value = false
  }
}

async function saveConfig() {
  try {
    await api.createNotificationConfig(newConfig.value)
    showAddModal.value = false
    newConfig.value = { channel: 'slack', webhook_url: '', enabled: true, events: [] }
    await fetchConfigs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to save configuration'
  }
}

async function deleteConfig(channel: NotificationChannel) {
  if (!confirm(`Are you sure you want to delete the ${channel} configuration?`)) {
    return
  }

  try {
    await api.deleteNotificationConfig(channel)
    await fetchConfigs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to delete configuration'
  }
}

async function testNotification(channel: NotificationChannel) {
  try {
    testResult.value = null
    const result = await api.testNotification(channel)
    testResult.value = result
  } catch (e) {
    testResult.value = {
      success: false,
      message: e instanceof Error ? e.message : 'Test failed',
      channel: channel,
    }
  }
}

const channelIcon = (channel: string) => {
  switch (channel) {
    case 'slack':
      return 'M14.8 4.6c0-1.1-.9-2-2-2s-2 .9-2 2 .9 2 2 2h2V4.6zm0 .4h2c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2v2zM4.6 9.2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2v-2h-2zm.4 0v2c0 1.1.9 2 2 2s2-.9 2-2-.9-2-2-2H5z'
    case 'discord':
      return 'M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z'
    default:
      return 'M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14'
  }
}

const channelColor = (channel: string) => {
  switch (channel) {
    case 'slack':
      return 'bg-purple-100 text-purple-800'
    case 'discord':
      return 'bg-indigo-100 text-indigo-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Notifications</h1>
        <p class="mt-1 text-sm text-gray-500">Configure notification channels for workflow alerts</p>
      </div>
      <button
        class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        @click="showAddModal = true"
      >
        <svg class="-ml-0.5 mr-1.5 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Add Channel
      </button>
    </div>

    <!-- Test Result Banner -->
    <div
      v-if="testResult"
      :class="[
        'rounded-md p-4',
        testResult.success ? 'bg-green-50' : 'bg-red-50',
      ]"
    >
      <div class="flex">
        <svg
          :class="['h-5 w-5', testResult.success ? 'text-green-400' : 'text-red-400']"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            v-if="testResult.success"
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clip-rule="evenodd"
          />
          <path
            v-else
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clip-rule="evenodd"
          />
        </svg>
        <div class="ml-3">
          <p :class="['text-sm font-medium', testResult.success ? 'text-green-800' : 'text-red-800']">
            {{ testResult.success ? 'Test notification sent successfully!' : `Failed: ${testResult.message}` }}
          </p>
        </div>
        <button
          class="ml-auto"
          @click="testResult = null"
        >
          <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
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

    <!-- Configurations List -->
    <div v-else class="overflow-hidden rounded-lg bg-white shadow">
      <ul role="list" class="divide-y divide-gray-200">
        <li
          v-for="config in configs"
          :key="config.channel"
          class="px-4 py-5 sm:px-6"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <span
                :class="[
                  'inline-flex items-center justify-center h-10 w-10 rounded-lg',
                  channelColor(config.channel),
                ]"
              >
                <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path :d="channelIcon(config.channel)" />
                </svg>
              </span>
              <div class="ml-4">
                <p class="text-sm font-medium text-gray-900">
                  {{ config.channel.charAt(0).toUpperCase() + config.channel.slice(1) }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ config.enabled ? 'Enabled' : 'Disabled' }}
                  <span v-if="config.events.length > 0">
                    - {{ config.events.length }} event{{ config.events.length !== 1 ? 's' : '' }}
                  </span>
                </p>
              </div>
            </div>
            <div class="flex items-center space-x-3">
              <span
                :class="[
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                  config.webhook_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800',
                ]"
              >
                {{ config.webhook_configured ? 'Configured' : 'Not Configured' }}
              </span>
              <button
                v-if="config.webhook_configured"
                class="text-sm text-indigo-600 hover:text-indigo-900"
                @click="testNotification(config.channel as NotificationChannel)"
              >
                Test
              </button>
              <button
                class="text-sm text-red-600 hover:text-red-900"
                @click="deleteConfig(config.channel as NotificationChannel)"
              >
                Delete
              </button>
            </div>
          </div>
          <div v-if="config.events.length > 0" class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="event in config.events"
              :key="event"
              class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
            >
              {{ event.replace(/_/g, ' ') }}
            </span>
          </div>
        </li>
        <li v-if="configs.length === 0" class="px-4 py-12 text-center">
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
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No notification channels</h3>
          <p class="mt-1 text-sm text-gray-500">Get started by adding a notification channel.</p>
          <div class="mt-6">
            <button
              class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
              @click="showAddModal = true"
            >
              <svg class="-ml-0.5 mr-1.5 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Add Channel
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Add Channel Modal -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-10 overflow-y-auto"
      @click.self="showAddModal = false"
    >
      <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
          <div>
            <h3 class="text-lg font-medium leading-6 text-gray-900">Add Notification Channel</h3>
            <div class="mt-4 space-y-4">
              <div>
                <label for="channel" class="block text-sm font-medium text-gray-700">Channel</label>
                <select
                  id="channel"
                  v-model="newConfig.channel"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="slack">Slack</option>
                  <option value="discord">Discord</option>
                  <option value="webhook">Custom Webhook</option>
                </select>
              </div>
              <div>
                <label for="webhook_url" class="block text-sm font-medium text-gray-700">Webhook URL</label>
                <input
                  id="webhook_url"
                  v-model="newConfig.webhook_url"
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Events</label>
                <div class="mt-2 space-y-2">
                  <div v-for="event in availableEvents" :key="event.value" class="flex items-center">
                    <input
                      :id="event.value"
                      v-model="newConfig.events"
                      :value="event.value"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label :for="event.value" class="ml-2 text-sm text-gray-700">
                      {{ event.label }}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
            <button
              type="button"
              class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 sm:col-start-2"
              @click="saveConfig"
            >
              Save
            </button>
            <button
              type="button"
              class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
              @click="showAddModal = false"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
