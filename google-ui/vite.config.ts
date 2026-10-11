import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss(), {
      name: 'distribution-module-inventory',
      generateBundle(_options, bundle) {
        const modules = new Set<string>();
        for (const output of Object.values(bundle)) {
          if (output.type !== 'chunk') continue;
          for (const id of Object.keys(output.modules)) {
            const normalized = id.replaceAll('\\', '/');
            const marker = '/node_modules/';
            const offset = normalized.lastIndexOf(marker);
            if (offset >= 0) modules.add(normalized.slice(offset + marker.length).replace(/\?.*$/, ''));
          }
        }
        this.emitFile({type: 'asset', fileName: 'BUNDLED-MODULES.json',
          source: JSON.stringify({schema: 1, modules: [...modules].sort()}, null, 2) + '\n'});
      },
    }],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify—file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
