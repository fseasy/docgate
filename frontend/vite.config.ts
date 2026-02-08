import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

const getWebsitePath = ({ mode }: { mode: string; }) => {
  const dotEnv = loadEnv(mode, process.cwd()); // - Need manually load the env at the config stage.
  const basePath = dotEnv.VITE_WEBSITE_REACT_BASE_PATH;

  if (!basePath || basePath.trim() === '') {
    throw new Error('`VITE_WEBSITE_REACT_BASE_PATH` is required in .env.[mode] file.');
  }

  // Normalize: ensure leading slash and trailing slash (vite requires a trailing slash, whereas supertokens does not)
  let normalizedBasePath = basePath.trim();
  if (!normalizedBasePath.startsWith('/')) {
    normalizedBasePath = '/' + normalizedBasePath;
  }
  if (!normalizedBasePath.endsWith('/')) {
    normalizedBasePath += '/';
  }

  const domain = dotEnv.VITE_WEBSITE_DOMAIN;
  const normalizedDomain = new URL(domain).host; // it only accept the host
  return {
    normDomain: normalizedDomain,
    normBasePath: normalizedBasePath
  };
};


// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const websitePath = getWebsitePath({ mode: mode });
  return {
    base: websitePath.normBasePath,
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
    },
    server: {
      allowedHosts: [websitePath.normDomain],
    }
  };
});
