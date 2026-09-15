const storyModules = import.meta.glob('../content/stories/legacy/**/*.json', { eager: true });
const albumModules = import.meta.glob('../content/albums/legacy/**/*.json', { eager: true });

const legacyRoutes = new Map<string, string>();

for (const module of Object.values(storyModules)) {
  const story = (module as any).default ?? module;
  if (story?.privacy === 'public') legacyRoutes.set(story.sourceFile, `/journal/${story.slug}/`);
}

for (const module of Object.values(albumModules)) {
  const album = (module as any).default ?? module;
  if (album?.privacy === 'public') legacyRoutes.set(album.sourceFile, `/albums/${album.slug}/`);
}

export function resolveContentLink(link: any) {
  if (link.kind === 'internal') return legacyRoutes.get(link.resolved) ?? null;
  return link.href;
}
