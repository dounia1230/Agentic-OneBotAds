import { PLATFORM_TO_CHANNEL } from "../../../lib/platforms";
import type {
  AssistantResponse,
  CampaignBrief,
  PublicationPackage,
} from "../../../types/api";

export type PublicationFormValues = {
  productName: string;
  companyName: string;
  companyWebsite: string;
  platform: string;
  audience: string;
  goal: string;
  useCompanyResearch: boolean;
  generateImage: boolean;
};

export const defaultPublicationForm: PublicationFormValues = {
  productName: "Agentic OneBotAds",
  companyName: "",
  companyWebsite: "",
  platform: "LinkedIn",
  audience: "SMEs and marketing teams",
  goal: "Increase qualified demo bookings",
  useCompanyResearch: false,
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
    form.companyName
      ? `Base the publication on current public information about ${form.companyName}.`
      : null,
    form.companyWebsite
      ? `Company website: ${form.companyWebsite}.`
      : null,
    `Target audience: ${form.audience}.`,
    `Goal: ${form.goal}.`,
    form.useCompanyResearch
      ? "Use live company web research to ground the publication ideas."
      : "Use only the existing private knowledge base and request context.",
    form.generateImage
      ? "Create the image for the publication if the backend stack allows it."
      : "Text-only output is fine.",
  ]
    .filter((part): part is string => Boolean(part))
    .join(" ");
}

export function buildCampaignDraftPayload(form: PublicationFormValues): CampaignBrief {
  return {
    product_name: form.productName,
    audience: form.audience,
    goal: form.goal,
    channels: [PLATFORM_TO_CHANNEL[form.platform] ?? "linkedin"],
    source_context_query: `${form.productName} ${form.audience} ${form.goal}`,
    generate_image_prompt: form.generateImage,
    generate_image: false,
    compose_publication_image: false,
  };
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
    image_url: image?.image_url ?? null,
    alt_text: image?.alt_text ?? `Promotional visual for ${form.productName} targeting ${form.audience}.`,
    recommended_schedule: "Review backend recommendation",
    compliance_status: compliance ? (compliance.approved ? "approved" : "needs_revision") : "pending_review",
    optimization_notes: response.optimization?.quick_wins.map((item) => item.recommendation) ?? [],
    status: response.status,
  };
}
