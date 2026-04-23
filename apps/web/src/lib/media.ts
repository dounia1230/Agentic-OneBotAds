const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function getAssetOrigin(): string {
  if (!API_BASE_URL) {
    return "";
  }

  try {
    return new URL(API_BASE_URL).origin;
  } catch {
    return "";
  }
}

export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }

  const normalized = path.replace(/\\/g, "/").trim();
  if (!normalized) {
    return null;
  }

  if (
    normalized.startsWith("http://") ||
    normalized.startsWith("https://") ||
    normalized.startsWith("data:")
  ) {
    return normalized;
  }

  const assetOrigin = getAssetOrigin();
  if (normalized.startsWith("/outputs/")) {
    return assetOrigin ? `${assetOrigin}${normalized}` : normalized;
  }

  if (normalized.startsWith("outputs/")) {
    const relativeOutputsPath = `/${normalized}`;
    return assetOrigin ? `${assetOrigin}${relativeOutputsPath}` : relativeOutputsPath;
  }

  return null;
}

export function canPreviewImage(path: string | null | undefined): boolean {
  return resolveMediaUrl(path) !== null;
}
