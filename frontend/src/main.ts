/**
 * Main entry point for Vue application
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// Plugins
app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin)

// Mount
app.mount('#app')
