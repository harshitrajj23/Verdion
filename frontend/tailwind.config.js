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
        cream: {
          50: "#FDFCF9",   // Crisp Pearl Milk
          100: "#FAF7F2",  // Primary 70% Canvas
          200: "#F4EFEA",  // Apple Parchment
          300: "#EAE3D8",  // Hairline Border
          400: "#DFD6C7",  // Muted Border
          500: "#C6B9A5",  // Subtle Warm Gray
          600: "#9E907B",
          700: "#756A59",
        },
        lavender: {
          50: "#F8F6FD",   // Ultra Soft Lavender Tint
          100: "#F1ECFB",  // Soft Chip & Badge Surface
          200: "#E0D5F6",  // Lavender Hairline Border
          300: "#C7B5EE",  // Lavender Focus & Ring
          400: "#A78FE0",  // Light Accent
          500: "#8969D3",  // Luminous Accent
          600: "#6E50BD",  // Apple Action Lavender (Primary CTA)
          700: "#5A3EA2",  // Pressed / Active Lavender
          800: "#452E80",  // Deep Royal Lavender
          900: "#31205F",
        },
        ink: {
          DEFAULT: "#1D1B1E", // Apple Near-Black Espresso Ink
          secondary: "#635E6B", // Secondary Body Ink
          muted: "#8E8896",     // Micro-legal / Caption Ink
          hairline: "#EAE3D8",
          dark: "#FAF7F2",      // Body on dark tiles
          darkMuted: "#B8B2C4", // Muted on dark tiles
        },
        tile: {
          dark: "#191720",  // Apple Contrast Dark Tile 1
          dark2: "#221E2C", // Apple Dark Tile 2
          dark3: "#2B2737", // Apple Dark Tile 3
          border: "#332E41",
        },
        // Compatibility palette tailored to match the cream/lavender ecosystem
        verdion: {
          950: "#FAF7F2",   // Redirect dark background to Cream 100
          900: "#F4EFEA",   // Redirect to Parchment
          850: "#EAE3D8",   // Redirect to Hairline
          800: "#DFD6C7",
          700: "#635E6B",
          600: "#8E8896",
          accent: "#6E50BD", // Primary Lavender
          cyan: "#5A3EA2",   // Deep Lavender
          indigo: "#6E50BD", // Lavender Swarm
          rose: "#E11D48",   // Clean Crimson
          amber: "#D97706",  // Refined Amber
        }
      },
      fontFamily: {
        appleDisplay: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro",
          "Inter",
          "system-ui",
          "sans-serif"
        ],
        appleText: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "SF Pro",
          "Inter",
          "system-ui",
          "sans-serif"
        ],
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "SF Pro",
          "Inter",
          "system-ui",
          "sans-serif"
        ],
        mono: ["var(--font-jetbrains)", "SFMono-Regular", "Menlo", "monospace"],
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
        apple: "0 2px 10px rgba(35, 25, 50, 0.03), 0 8px 30px -4px rgba(35, 25, 50, 0.05)",
        "apple-hover": "0 4px 14px rgba(35, 25, 50, 0.05), 0 16px 40px -8px rgba(35, 25, 50, 0.08)",
        "apple-product": "3px 5px 30px 0px rgba(30, 20, 50, 0.12)",
        "apple-pill": "0 2px 8px -1px rgba(110, 80, 189, 0.25)",
        glow: "0 0 20px -3px rgba(110, 80, 189, 0.2)",
        "glow-cyan": "0 0 20px -3px rgba(110, 80, 189, 0.2)",
        "glow-rose": "0 0 20px -3px rgba(225, 29, 72, 0.15)",
        glass: "0 8px 32px 0 rgba(35, 25, 50, 0.06)",
      },
    },
  },
  plugins: [],
};

