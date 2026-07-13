import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "#f97316",
        ink: {
          base: "#09090b",
          surface: "#111113",
          elevated: "#1a1a1e",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui"],
        display: ["var(--font-instrument)", "ui-serif", "Georgia"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        accent: "0 0 40px -12px var(--accent)",
      },
    },
  },
  plugins: [],
};
export default config;
