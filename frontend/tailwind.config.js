/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        ink: {
          50: "#f7f8fa",
          100: "#eef0f3",
          200: "#e2e5ea",
          300: "#cbd0d8",
          400: "#9aa2af",
          500: "#6b7280",
          600: "#4b5563",
          700: "#374151",
          800: "#1f2430",
          900: "#12151c",
          950: "#0a0c10",
        },
        auto: {
          DEFAULT: "#0d9488",
          soft: "#ecfdf9",
          border: "#99f0e4",
          text: "#0f766e",
        },
        approval: {
          DEFAULT: "#b45309",
          soft: "#fef6e7",
          border: "#fbd897",
          text: "#92400e",
        },
        assist: {
          DEFAULT: "#2563eb",
          soft: "#eff4ff",
          border: "#bfd4fe",
          text: "#1d4ed8",
        },
        escalate: {
          DEFAULT: "#be123c",
          soft: "#fef1f3",
          border: "#fbc9d3",
          text: "#9f1239",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(16, 20, 28, 0.04), 0 1px 1px 0 rgba(16, 20, 28, 0.02)",
        popover: "0 4px 16px -4px rgba(16, 20, 28, 0.12), 0 2px 6px -2px rgba(16, 20, 28, 0.06)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "check-pop": {
          "0%": { opacity: "0", transform: "scale(0.7)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.28s ease-out",
        "check-pop": "check-pop 0.22s cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [],
};
