import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = process.env.VITE_API ?? "http://localhost:8010";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": api, "/agent": api } },
});
