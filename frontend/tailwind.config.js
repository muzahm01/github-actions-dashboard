/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // GitHub Actions colors
        success: {
          50: '#ecfdf5',
          100: '#d1fae5',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        failure: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        pending: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
        },
        queued: {
          50: '#f5f5f5',
          100: '#e5e5e5',
          500: '#737373',
          600: '#525252',
          700: '#404040',
        },
      },
    },
  },
  plugins: [],
}
