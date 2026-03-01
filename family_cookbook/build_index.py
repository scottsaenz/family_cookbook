"""
Generate docs/recipes/index.md and docs/tags.md from all recipe markdown files.

- Recipe index: grouped by meal type with links to every recipe.
- Tags page: alphabetical tag listing with links to recipes per tag.
  (Zensical does not yet support auto-generated tag listings, so we build it.)
"""

from collections import defaultdict
from pathlib import Path

import frontmatter


MEAL_TYPES = {
    "breakfast", "lunch", "dinner", "snack", "dessert",
    "appetizer", "side-dish", "soup", "salad", "bread",
    "beverage", "sauce",
}

MEAL_ORDER = [
    "breakfast", "appetizer", "soup", "salad", "lunch",
    "dinner", "side-dish", "bread", "sauce", "dessert",
    "snack", "beverage", "other",
]


def _load_recipes(recipes_dir: Path) -> list[tuple[str, str, list[str]]]:
    """Return (title, filename, tags) for every recipe markdown file."""
    recipe_files = sorted(
        f for f in recipes_dir.glob("*.md") if f.name != "index.md"
    )
    recipes = []
    for md_path in recipe_files:
        post = frontmatter.load(md_path)
        title = post.get("title", md_path.stem.replace("-", " ").title())
        tags = post.get("tags", [])
        recipes.append((title, md_path.name, tags))
    return recipes


def build_recipe_index(recipes_dir: Path) -> None:
    recipes = _load_recipes(recipes_dir)

    if not recipes:
        print("No recipe files found. Run process-recipes first.")
        return

    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for title, filename, tags in recipes:
        categorized = False
        for tag in tags:
            if tag in MEAL_TYPES:
                by_category[tag].append((title, filename))
                categorized = True
        if not categorized:
            by_category["other"].append((title, filename))

    lines = [
        "---",
        "title: All Recipes",
        "---",
        "",
        "# All Recipes",
        "",
        f"**{len(recipes)} recipes** in the collection.",
        "",
    ]

    for category in MEAL_ORDER:
        if category not in by_category:
            continue
        label = category.replace("-", " ").title()
        lines.append(f"## {label}")
        lines.append("")
        for title, filename in sorted(by_category[category]):
            lines.append(f"- [{title}]({filename})")
        lines.append("")

    index_path = recipes_dir / "index.md"
    index_path.write_text("\n".join(lines))
    print(f"Built recipe index: {index_path} ({len(recipes)} recipes)")


def build_tags_page(recipes_dir: Path, tags_path: Path) -> None:
    """Build a static tags listing page since Zensical doesn't support it yet."""
    recipes = _load_recipes(recipes_dir)

    if not recipes:
        return

    by_tag: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for title, filename, tags in recipes:
        for tag in tags:
            by_tag[tag].append((title, filename))

    lines = [
        "---",
        "title: Tags",
        "---",
        "",
        "# Recipe Tags",
        "",
        "Browse all recipes by tag.",
        "",
    ]

    for tag in sorted(by_tag):
        label = tag.replace("-", " ").title()
        lines.append(f"## {label}")
        lines.append("")
        for title, filename in sorted(by_tag[tag]):
            lines.append(f"- [{title}](recipes/{filename})")
        lines.append("")

    tags_path.write_text("\n".join(lines))
    unique_tags = len(by_tag)
    print(f"Built tags page: {tags_path} ({unique_tags} unique tags)")


def build_index(recipes_dir: Path | None = None):
    if recipes_dir is None:
        recipes_dir = Path("docs/recipes")

    build_recipe_index(recipes_dir)
    build_tags_page(recipes_dir, recipes_dir.parent / "tags.md")


if __name__ == "__main__":
    build_index()
