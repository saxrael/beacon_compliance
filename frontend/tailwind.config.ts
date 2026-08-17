import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/utils/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          crimson: {
            DEFAULT: "#D6162F",
            50: "#FEF2F2",
            100: "#FEE2E2",
            200: "#FECACA",
            500: "#D6162F",
            600: "#B81026",
            700: "#990C1F",
            900: "#5C0511",
          },
          gold: {
            DEFAULT: "#D97706",
            50: "#FFFBEB",
            100: "#FEF3C7",
            200: "#FDE68A",
            400: "#F59E0B",
            500: "#D97706",
            600: "#B45309",
            700: "#92400E",
          },
        },
        parchment: {
          50: "#FCFCFA",
          100: "#FBF9F5",
          200: "#EFECE6",
          300: "#E3DFD5",
          400: "#C9C3B5",
        },
      },
      fontFamily: {
        serif: ["Cinzel", "Playfair Display", "Georgia", "serif"],
        display: ["Cinzel", "serif"],
        editorial: ["Playfair Display", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "Roboto Mono", "monospace"],
      },
      boxShadow: {
        "card-light": "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
        "card-elevated": "0 12px 30px -4px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04)",
        "card-gold": "0 10px 25px -5px rgba(217, 119, 6, 0.15), 0 8px 10px -6px rgba(217, 119, 6, 0.08)",
        "card-crimson": "0 10px 25px -5px rgba(214, 22, 47, 0.18), 0 8px 10px -6px rgba(214, 22, 47, 0.08)",
      },
    },
  },
  plugins: [],
};
export default config;
