export const PLATFORM_OPTIONS = ["LinkedIn", "Instagram", "Facebook", "Google Ads"] as const;

export const PLATFORM_TO_CHANNEL: Record<string, string> = {
  LinkedIn: "linkedin",
  Instagram: "meta",
  Facebook: "meta",
  "Google Ads": "google",
};
