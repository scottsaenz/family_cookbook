"""
Process a directory of recipe images into tagged Markdown files using OpenAI Vision.

Handles printed cookbook pages, magazine clippings, and handwritten recipe cards.
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import frontmatter
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff", ".bmp", ".heic"}

SYSTEM_PROMPT = """You are a recipe extraction assistant. You will be given an image of a recipe.
The image may be from a printed cookbook, a magazine article, a handwritten recipe card, or a
screenshot. Your job is to extract the recipe into a structured JSON format.

Respond with ONLY valid JSON matching this schema:
{
  "title": "Recipe Title",
  "source_type": "cookbook" | "magazine" | "handwritten" | "other",
  "source_name": "Name of cookbook or magazine if visible, otherwise null",
  "prep_time": "prep time if mentioned, otherwise null",
  "cook_time": "cook time if mentioned, otherwise null",
  "total_time": "total time if mentioned, otherwise null",
  "servings": "servings/yield if mentioned, otherwise null",
  "tags": ["list", "of", "tags"],
  "ingredients": [
    "ingredient line 1",
    "ingredient line 2"
  ],
  "instructions": [
    "Step 1 text",
    "Step 2 text"
  ],
  "notes": "Any additional notes, tips, or variations mentioned. null if none."
}

For the "tags" field, include all that apply from these categories:
- Protein: chicken, beef, pork, lamb, turkey, fish, seafood, tofu
- Meal type: breakfast, lunch, dinner, snack, dessert, appetizer, side-dish, soup, salad, bread, beverage, sauce
- Cuisine: italian, mexican, asian, chinese, japanese, thai, indian, french, mediterranean, american, southern, cajun, greek
- Diet: vegetarian, vegan, gluten-free, dairy-free, keto, low-carb, paleo
- Method: grilling, baking, slow-cooker, instant-pot, stovetop, no-cook, frying
- Other: quick, comfort-food, holiday, one-pot, meal-prep, kid-friendly

Also add any other descriptive tags that fit. Use lowercase, hyphenated where multi-word.

Be thorough in transcribing ingredients and instructions. Preserve quantities and measurements exactly.
If the handwriting or text is partially illegible, do your best and add "[unclear]" where uncertain."""

USER_PROMPT = "Please extract the recipe from this image into the JSON format specified."


def encode_image(image_path: Path) -> tuple[str, str]:
    suffix = image_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
        ".heic": "image/heic",
    }
    media_type = media_types.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    return data, media_type


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_recipe(client: OpenAI, image_path: Path, model: str) -> dict:
    image_data, media_type = encode_image(image_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        max_tokens=4096,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if the model wraps its response
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def recipe_to_markdown(recipe: dict, source_image: str) -> str:
    metadata = {
        "title": recipe["title"],
        "tags": recipe.get("tags", []),
        "source_type": recipe.get("source_type", "other"),
        "source_image": source_image,
    }
    if recipe.get("source_name"):
        metadata["source_name"] = recipe["source_name"]
    if recipe.get("prep_time"):
        metadata["prep_time"] = recipe["prep_time"]
    if recipe.get("cook_time"):
        metadata["cook_time"] = recipe["cook_time"]
    if recipe.get("total_time"):
        metadata["total_time"] = recipe["total_time"]
    if recipe.get("servings"):
        metadata["servings"] = recipe["servings"]

    body_parts = [f'# {recipe["title"]}\n']

    time_parts = []
    if recipe.get("prep_time"):
        time_parts.append(f"**Prep:** {recipe['prep_time']}")
    if recipe.get("cook_time"):
        time_parts.append(f"**Cook:** {recipe['cook_time']}")
    if recipe.get("total_time"):
        time_parts.append(f"**Total:** {recipe['total_time']}")
    if recipe.get("servings"):
        time_parts.append(f"**Servings:** {recipe['servings']}")
    if time_parts:
        body_parts.append(" | ".join(time_parts) + "\n")

    if recipe.get("ingredients"):
        body_parts.append("## Ingredients\n")
        for item in recipe["ingredients"]:
            body_parts.append(f"- {item}")
        body_parts.append("")

    if recipe.get("instructions"):
        body_parts.append("## Instructions\n")
        for i, step in enumerate(recipe["instructions"], 1):
            body_parts.append(f"{i}. {step}")
        body_parts.append("")

    if recipe.get("notes"):
        body_parts.append("## Notes\n")
        body_parts.append(recipe["notes"] + "\n")

    post = frontmatter.Post("\n".join(body_parts), **metadata)
    return frontmatter.dumps(post) + "\n"


def find_images(directory: Path) -> list[Path]:
    images = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(f)
    return images


def process_directory(
    input_dir: Path,
    output_dir: Path,
    model: str,
    api_key: str | None = None,
    skip_existing: bool = True,
):
    client = OpenAI(api_key=api_key) if api_key else OpenAI()
    images = find_images(input_dir)

    if not images:
        print(f"No images found in {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Found {len(images)} image(s) in {input_dir}\n")

    for i, image_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Processing {image_path.name}...")

        tentative_slug = slugify(image_path.stem)
        if skip_existing:
            existing = list(output_dir.glob(f"{tentative_slug}.md")) + list(
                output_dir.glob(f"{tentative_slug}-*.md")
            )
            if existing:
                print(f"  Skipping (markdown already exists: {existing[0].name})")
                continue

        try:
            recipe = extract_recipe(client, image_path, model)
        except json.JSONDecodeError as e:
            print(f"  ERROR: Failed to parse JSON response: {e}")
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        slug = slugify(recipe.get("title", image_path.stem))
        md_path = output_dir / f"{slug}.md"

        counter = 1
        while md_path.exists():
            md_path = output_dir / f"{slug}-{counter}.md"
            counter += 1

        md_content = recipe_to_markdown(recipe, image_path.name)
        md_path.write_text(md_content)
        print(f"  -> {md_path.name}  ({recipe['title']})")
        print(f"     Tags: {', '.join(recipe.get('tags', []))}")

    print(f"\nDone! Markdown files written to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract recipes from images into tagged Markdown files."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing recipe images",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs/recipes"),
        help="Output directory for Markdown files (default: docs/recipes)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (default: uses OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Re-process images even if markdown already exists",
    )

    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f"Error: {args.input_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    process_directory(
        input_dir=args.input_dir,
        output_dir=args.output,
        model=args.model,
        api_key=args.api_key,
        skip_existing=not args.no_skip,
    )


if __name__ == "__main__":
    main()
