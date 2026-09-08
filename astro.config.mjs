// @ts-check
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://noahwilliams.me',
  output: 'static',
  integrations: [sitemap()],
  build: {
    format: 'directory',
  },
});
