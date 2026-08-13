import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages*.{js,ts,jsx,tsx,mdx}",
    "./src/components*.{js,ts,jsx,tsx,mdx}",
    "./src/app*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0F172A",
        surface: "#1E293B",
        border: "#334155",
        crimson: {
          500: "#D6162F",
          600: "#B81026",
        },
        gold: {
          400: "#F5D345",
          500: "#E0BD2B",
        },
        amber: {
          500: "#F59E0B",
          600: "#D97706",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
