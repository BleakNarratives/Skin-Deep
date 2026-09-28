import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        // Performance optimization: Split large vendor dependencies (react, recharts) into
        // separate cacheable chunks to prevent single monolithic bundle downloads, improve initial page load,
        // and eliminate Vite bundle size warnings (>500kB limit).
        manualChunks(id) {
          if (id.includes('node_modules/recharts')) {
            return 'recharts';
          }
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom') || id.includes('node_modules/scheduler')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
