import type { AssistantResponse, PublicationPackage } from "../../../types/api";

export type PublicationFormValues = {
  productName: string;
  platform: string;
  audience: string;
  goal: string;
  generateImage: boolean;
};

export const defaultPublicationForm: PublicationFormValues = {
  productName: "Agentic OneBotAds",
  platform: "LinkedIn",
  audience: "SMEs and marketing teams",
  goal: "Increase qualified demo bookings",
  generateImage: true,
};

function buildHashtags(productName: string, platform: string): string[] {
  const cleaned = productName.replace(/[^a-zA-Z0-9]+/g, " ").trim();
  const branded = cleaned
    ? `#${cleaned
        .split(/\s+/)
        .map((part) => `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`)
        .join("")}`
    : "#OneBotAds";

  return [branded, "#MarketingAutomation", "#AdvertisingAI", `#${platform.replace(/\s+/g, "")}`];
}

export function buildPublicationRequestMessage(form: PublicationFormValues): string {
  return [
    `Create a ${form.platform} publication for ${form.productName}.`,
    `Target audience: ${form.audience}.`,
    `Goal: ${form.goal}.`,
    form.generateImage ? "Include an image concept and visual guidance." : "Text-only output is fine.",
  ].join(" ");
}

export function derivePublicationOutput(
  response: AssistantResponse,
  form: PublicationFormValues,
): PublicationPackage | null {
  if (response.publication) {
    return response.publication;
  }

  const creative = response.creative;
  const image = response.image;
  const compliance = response.compliance;

  if (!creative) {
    return null;
  }

  return {
    platform: form.platform,
    headline: compliance?.final_safe_version.headline ?? creative.headline,
    caption: compliance?.final_safe_version.caption ?? creative.primary_text,
    cta: creative.cta,
    hashtags: creative.hashtags.length > 0 ? creative.hashtags : buildHashtags(form.productName, form.platform),
    image_prompt: image?.image_prompt ?? null,
    image_path: image?.image_path ?? null,
    alt_text: image?.alt_text ?? `Promotional visual for ${form.productName} targeting ${form.audience}.`,
    recommended_schedule: "Review backend recommendation",
    compliance_status: compliance ? (compliance.approved ? "approved" : "needs_revision") : "pending_review",
    optimization_notes: response.optimization?.quick_wins.map((item) => item.recommendation) ?? [],
    status: response.status,
  };
}
