const imageModules = import.meta.glob('../assets/public/**/*.{jpg,jpeg,png}', {
  eager: true,
  import: 'default',
});

const images = new Map<string, any>(
  Object.entries(imageModules).map(([path, image]) => [path.replace('../assets/public/', ''), image]),
);

export function resolvePublicImage(asset: string | null | undefined) {
  if (!asset) return undefined;
  const image = images.get(asset);
  if (!image) throw new Error(`Missing public image asset: ${asset}`);
  return image;
}
