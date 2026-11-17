import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#0f1117",
        surface: "#16181f",
        "surface-2": "#1e2130",
        border: "#2a2d3a",
        "border-active": "#3a3f52",
        muted: "#4a5068",
        text: "#e2e8f0",
        "text-muted": "#8892a4",
        accent: "#4f8ef7",
        "accent-hover": "#6ba3f8",
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444",
        strong: "#22c55e",
        good: "#4f8ef7",
        review: "#f59e0b",
        low: "#6b7280",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Cascadia Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;