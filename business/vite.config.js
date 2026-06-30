import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === "production" ? "/workblox/workblox-business/" : "/",
  server: {
    port: 5174,
    proxy: {
      "/api": "http://localhost:5000",
    },
  },
});
