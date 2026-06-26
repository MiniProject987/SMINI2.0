import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Prevent Vite from watching server-side data files and backend sources
      // which are frequently written by the Express routes. This avoids
      // triggering HMR / full page reload loops when JSON data is updated.
      watch: process.env.DISABLE_HMR === 'true' ? null : {
        ignored: [
          '**/data/**',
          '**/.server_data/**',
          '**/server/**',
          '**/datasets/**'
        ]
      }
    },
  };
});
