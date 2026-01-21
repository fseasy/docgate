import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("react-router")) {
              return "router-vendor";
            }
            if (id.includes("supertokens")) {
              return "supertokens-vendor";
            }
            if (id.includes("react")) {
              return "react-vendor";
            }
            return "vendor";
          }
        }
      }
    }
  }
});
