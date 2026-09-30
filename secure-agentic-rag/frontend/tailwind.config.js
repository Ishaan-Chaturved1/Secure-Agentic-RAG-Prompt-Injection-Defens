/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#090d16",
          panel: "#0f172a",
          card: "#1e293b",
          border: "#334155",
          accent: "#38bdf8",
          cyber: "#06b6d4",
          danger: "#ef4444",
          warning: "#f59e0b",
          success: "#10b981",
          purple: "#a855f7"
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
};
