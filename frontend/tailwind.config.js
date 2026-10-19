/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        verdion: {
          950: "#060913",
          900: "#0b0f19",
          850: "#101626",
          800: "#151e34",
          700: "#1e293b",
          600: "#334155",
          accent: "#10b981", // Emerald verified
          cyan: "#06b6d4",   // Prediction markets
          indigo: "#6366f1", // Agent swarm
          rose: "#f43f5e",   // Contradiction / Challenge
          amber: "#f59e0b",  // Uncertainty / Pending
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(16, 185, 129, 0.25)",
        "glow-cyan": "0 0 25px -5px rgba(6, 182, 212, 0.25)",
        "glow-rose": "0 0 25px -5px rgba(244, 63, 94, 0.25)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
    },
  },
  plugins: [],
};
