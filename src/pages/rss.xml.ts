const storyModules = import.meta.glob('../content/stories/legacy/**/*.json', { eager: true });

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

export const prerender = true;

export function GET() {
  const site = 'https://noahwilliams.me';
  const stories = Object.values(storyModules)
    .map((mod) => (mod as any).default ?? mod)
    .filter((story) => story?.privacy === 'public' && story?.date)
    .sort((a, b) => b.date.localeCompare(a.date));

  const items = stories.map((story) => {
    const link = `${site}/journal/${story.slug}/`;
    return `<item>
      <title>${escapeXml(story.title)}</title>
      <link>${link}</link>
      <guid>${link}</guid>
      <pubDate>${new Date(`${story.date}T12:00:00Z`).toUTCString()}</pubDate>
      <description>${escapeXml(story.summary || '')}</description>
    </item>`;
  }).join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Noah&apos;s World</title>
    <link>${site}/</link>
    <description>Stories, travels, photographs, and memories from Noah&apos;s World.</description>
    <language>en-us</language>
    ${items}
  </channel>
</rss>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' },
  });
}
