import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3eee4",
        card: "#fffdf8",
        ink: "#1c1914",
        line: "#e3d9c6",
        green: {
          DEFAULT: "#0c6b4d",
          deep: "#084536",
        },
        marigold: "#e3902d",
        clay: "#b5523a",
      },
      fontFamily: {
        display: ["Fraunces", "Noto Sans Tamil", "serif"],
        sans: ["Outfit", "Noto Sans Tamil", "sans-serif"],
      },
      boxShadow: {
        ticket: "0 1px 0 rgba(28,25,20,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
