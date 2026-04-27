from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DIR = DATA_DIR / "demo"
KNOWLEDGE_ROOT = DATA_DIR / "knowledge_base" / "brands"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic demo campaign data and brand knowledge files."
    )
    parser.add_argument(
        "--brand-slug",
        default="demo-atlas-glow",
        help="Directory slug to create under data/knowledge_base/brands/.",
    )
    parser.add_argument(
        "--campaign-slug",
        default="spring-repair-launch",
        help="Directory slug to create under the demo brand campaigns folder.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing generated demo files.",
    )
    return parser.parse_args()


def ensure_writable(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(
            f"Refusing to overwrite existing file: {path.relative_to(PROJECT_ROOT)}. "
            "Re-run with --overwrite if you want to replace it."
        )
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, overwrite: bool) -> None:
    ensure_writable(path, overwrite)
    rows = [
        {
            "campaign_id": "AGLOW-IG-01",
            "platform": "Instagram",
            "audience": "first-time skincare buyers",
            "impressions": 18000,
            "clicks": 756,
            "spend": 920,
            "conversions": 54,
            "revenue": 3240,
        },
        {
            "campaign_id": "AGLOW-META-02",
            "platform": "Facebook",
            "audience": "ingredient-conscious beauty shoppers",
            "impressions": 22000,
            "clicks": 704,
            "spend": 1100,
            "conversions": 38,
            "revenue": 2090,
        },
        {
            "campaign_id": "AGLOW-LI-03",
            "platform": "LinkedIn",
            "audience": "retail partners and boutique buyers",
            "impressions": 9000,
            "clicks": 279,
            "spend": 780,
            "conversions": 21,
            "revenue": 2340,
        },
        {
            "campaign_id": "AGLOW-GA-04",
            "platform": "Google Ads",
            "audience": "high-intent argan serum searchers",
            "impressions": 16000,
            "clicks": 992,
            "spend": 1360,
            "conversions": 82,
            "revenue": 4510,
        },
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "campaign_id",
                "platform",
                "audience",
                "impressions",
                "clicks",
                "spend",
                "conversions",
                "revenue",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, content: str, overwrite: bool) -> None:
    ensure_writable(path, overwrite)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    brand_root = KNOWLEDGE_ROOT / args.brand_slug
    campaign_root = brand_root / "campaigns" / args.campaign_slug
    csv_path = DEMO_DIR / "demo_atlas_glow_campaigns.csv"

    write_csv(csv_path, args.overwrite)
    write_markdown(
        brand_root / "idea_overview.md",
        """
        # Demo Atlas Glow

        Demo Atlas Glow is a premium Moroccan argan-serum concept used for local demos.

        ## Business Goal

        Launch a skincare campaign that balances premium positioning with conversion clarity.

        ## Audience Summary

        - First-time skincare buyers looking for a simple routine
        - Ingredient-conscious beauty shoppers
        - Boutique buyers evaluating premium self-care brands
        """,
        args.overwrite,
    )
    write_markdown(
        brand_root / "brand_guidelines.md",
        """
        # Demo Atlas Glow Brand Guidelines

        ## Brand Role

        A premium but accessible skincare brand built around Moroccan argan care rituals.

        ## Voice Attributes

        - Calm
        - Credible
        - Sensory
        - Premium
        - Clear

        ## Tone Rules

        - Lead with skin-comfort and ritual language, not hype.
        - Keep claims grounded and avoid miracle wording.
        - Make premium feel welcoming rather than exclusive.
        - Use concise, modern phrasing suitable for paid social.

        ## Avoid

        - Guaranteed results
        - Medical claims
        - Before-and-after exaggeration
        - Luxury cliches without product substance
        """,
        args.overwrite,
    )
    write_markdown(
        campaign_root / "brief.md",
        """
        # Spring Repair Launch

        ## Objective

        Increase first-purchase conversions for a spring launch of Atlas Glow Argan Serum.

        ## Offer

        Position the serum as a lightweight daily repair ritual for stressed, dull skin.

        ## Messaging Priorities

        - Emphasize hydration, softness, and routine simplicity
        - Show Moroccan origin cues without turning them into stereotypes
        - Use premium visual language with room for direct-response CTA

        ## CTA Guidance

        Focus on discovery, trial intent, and first-purchase momentum.
        """,
        args.overwrite,
    )

    created = [
        csv_path,
        brand_root / "idea_overview.md",
        brand_root / "brand_guidelines.md",
        campaign_root / "brief.md",
    ]
    for path in created:
        print(path.relative_to(PROJECT_ROOT).as_posix())


if __name__ == "__main__":
    main()
