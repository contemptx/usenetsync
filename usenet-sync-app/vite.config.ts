import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => ({
  plugins: [react()],

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      // 3. tell vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
  
  // Add resolve alias for Tauri API when not in Tauri environment
  resolve: {
    alias: mode === 'test' || !process.env.TAURI_ENV ? {
      '@tauri-apps/api/tauri': '/src/test/mocks/tauri.ts',
      '@tauri-apps/api/event': '/src/test/mocks/event.ts',
      '@tauri-apps/api': '/src/test/mocks/api.ts',
    } : {},
  },
  
  // Define global variable for Tauri environment
  define: {
    '__TAURI_ENV__': JSON.stringify(process.env.TAURI_ENV || false),
  },
}));
