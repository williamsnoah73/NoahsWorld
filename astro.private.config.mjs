// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://family.noahwilliams.me',
  srcDir: './private-site',
  publicDir: './private-site/public',
  outDir: './dist-private',
  output: 'static',
  build: {
    format: 'directory',
  },
});
