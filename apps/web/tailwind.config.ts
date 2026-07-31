import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: "oklch(0.55 0.11 250)",
        warning: "oklch(0.65 0.13 65)",
        danger: "oklch(0.55 0.11 25)",
        success: "oklch(0.5 0.13 145)",
        ink: "#1a1d21",
        subtleText: "#6b7280",
        mutedText: "#9aa1ab",
        borderLine: "#e7e9ee",
        canvas: "#f4f5f7",
        cardBg: "#ffffff",
      },
      fontFamily: {
        serif: [
          "var(--font-source-serif)",
          "Source Serif 4",
          "Georgia",
          "serif",
        ],
        sans: ["var(--font-ibm-plex)", "IBM Plex Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
