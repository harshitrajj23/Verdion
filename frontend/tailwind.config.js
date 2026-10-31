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
        marshmallow: {
          DEFAULT: "#FFFDFB",
          white: "#FFFDFB",
        },
        cloud: {
          DEFAULT: "#FFF6F9",
          surface: "#FFF6F9",
          50: "#FFF6F9",
          100: "#FFF0F5",
        },
        bubblegum: {
          DEFAULT: "#FF8FB1",
          hover: "#FF6FA0",
          deep: "#E8567F",
          soft: "#FFE4EE",
          50: "#FFF6F9",
          100: "#FFE4EE",
          200: "#FFC9DA",
          300: "#FFAEC6",
          400: "#FF8FB1",
          500: "#FF6FA0",
          600: "#E8567F",
          700: "#C93D64",
          800: "#A8294D",
          900: "#751833",
        },
        ink: {
          DEFAULT: "#2A1F26",
          secondary: "#7A6670",
          muted: "#7A6670",
          hairline: "#F5DCE6",
          dark: "#FFFDFB",
          darkMuted: "#FFE4EE",
        },
        muted: {
          DEFAULT: "#7A6670",
          text: "#7A6670",
        },
        hairline: "#F5DCE6",
        // Backward-compatibility aliases mapped to the new marshmallow & bubblegum system
        cream: {
          50: "#FFFDFB",
          100: "#FFFDFB",
          200: "#FFF6F9",
          300: "#F5DCE6",
          400: "#F0CFDC",
          500: "#7A6670",
          600: "#7A6670",
          700: "#2A1F26",
        },
        lavender: {
          50: "#FFF6F9",
          100: "#FFE4EE",
          200: "#F5DCE6",
          300: "#FFC9DA",
          400: "#FFAEC6",
          500: "#FF8FB1",
          600: "#FF8FB1",
          700: "#E8567F",
          800: "#C93D64",
          900: "#751833",
        },
        verdion: {
          950: "#FFFDFB",
          900: "#FFF6F9",
          850: "#F5DCE6",
          800: "#F0CFDC",
          700: "#7A6670",
          600: "#7A6670",
          accent: "#FF8FB1",
          cyan: "#E8567F",
          indigo: "#FF8FB1",
          rose: "#E8567F",
          amber: "#D97706",
        }
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        fraunces: ["var(--font-fraunces)", "serif"],
        appleDisplay: ["var(--font-fraunces)", "serif"],
        sans: ["var(--font-inter)", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        inter: ["var(--font-inter)", "sans-serif"],
        appleText: ["var(--font-inter)", "-apple-system", "sans-serif"],
        mono: ["SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        "apple-card": "18px", // Apple design.md {rounded.lg} 18px
        pill: "9999px",      // Apple signature full-pill
      },
      letterSpacing: {
        "apple-tight": "-0.025em",
        "apple-display": "-0.015em",
      },
      boxShadow: {
        soft: "0 8px 30px rgba(232, 86, 127, 0.08)",
        bubblegum: "0 8px 30px rgba(232, 86, 127, 0.08)",
        "bubblegum-hover": "0 12px 36px rgba(232, 86, 127, 0.16)",
        "apple-card": "0 8px 30px rgba(232, 86, 127, 0.08)",
        "apple-sm": "0 2px 10px rgba(232, 86, 127, 0.04)",
        apple: "0 8px 30px rgba(232, 86, 127, 0.08)",
        "apple-hover": "0 12px 36px rgba(232, 86, 127, 0.14)",
        "apple-product": "3px 5px 30px 0px rgba(232, 86, 127, 0.12)",
        "apple-pill": "0 2px 8px -1px rgba(232, 86, 127, 0.25)",
        glow: "0 0 20px -3px rgba(255, 143, 177, 0.3)",
        "glow-cyan": "0 0 20px -3px rgba(232, 86, 127, 0.25)",
        "glow-rose": "0 0 20px -3px rgba(232, 86, 127, 0.2)",
        glass: "0 8px 32px 0 rgba(232, 86, 127, 0.06)",
      },
    },
  },
  plugins: [],
};

