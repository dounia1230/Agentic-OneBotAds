export function canPreviewImage(path: string | null | undefined): boolean {
  if (!path) {
    return false;
  }

  return path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:");
}
