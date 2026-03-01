# Cookbook From Physical

Extract recipes from photos of cookbooks, magazine clippings, and handwritten recipe cards into
tagged Markdown files — then serve them as a searchable static website.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for package management
- An [OpenAI API key](https://platform.openai.com/api-keys) (GPT-4o is used for vision)

## Quick Start

```bash
# Install dependencies
uv sync

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Put recipe images in the images/ directory, then process them
uv run python -m cookbook_from_physical.process_recipes images/

# Build the recipe index page
uv run python -m cookbook_from_physical.build_index

# Preview the site locally
uv run zensical serve
```

Open <http://127.0.0.1:8000> to browse your recipes.

## Usage

### 1. Process recipe images

```bash
uv run python -m cookbook_from_physical.process_recipes <image-directory> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-o`, `--output` | `docs/recipes` | Output directory for Markdown files |
| `--model` | `gpt-4o` | OpenAI model to use |
| `--api-key` | `$OPENAI_API_KEY` | API key (or set the env var) |
| `--no-skip` | off | Re-process images that already have markdown |

Supported image formats: JPG, PNG, WebP, GIF, TIFF, BMP, HEIC.

The script sends each image to OpenAI's vision model, extracts the recipe, and writes a
Markdown file with YAML frontmatter containing title, tags, source type, and timing info.

### 2. Build the recipe index

```bash
uv run python -m cookbook_from_physical.build_index
```

Generates `docs/recipes/index.md` with all recipes grouped by meal type.

### 3. Serve or build the site

```bash
# Local development server with hot reload
uv run zensical serve

# Build static site for deployment
uv run zensical build
```

The built site goes to `site/` and can be deployed to any static host (GitHub Pages,
Netlify, Vercel, etc.).

## Project Structure

```
cookbook_from_physical/
├── images/              # Drop recipe images here
├── docs/
│   ├── index.md         # Site home page
│   ├── tags.md          # Auto-generated tag index
│   ├── recipes/         # Generated recipe markdown files
│   └── stylesheets/
│       └── extra.css
├── cookbook_from_physical/
│   ├── process_recipes.py   # Image → Markdown pipeline
│   └── build_index.py       # Recipe index page generator
├── mkdocs.yml           # Zensical/MkDocs configuration
└── pyproject.toml       # Project & dependency config (uv)
```

## Recipe Markdown Format

Each generated recipe looks like:

```markdown
---
title: Chicken Parmesan
tags:
- chicken
- dinner
- italian
- baking
source_type: cookbook
source_name: "Joy of Cooking"
prep_time: 20 minutes
cook_time: 35 minutes
servings: "4"
source_image: IMG_1234.jpg
---

# Chicken Parmesan

**Prep:** 20 minutes | **Cook:** 35 minutes | **Servings:** 4

## Ingredients

- 4 boneless chicken breasts
- 1 cup breadcrumbs
- ...

## Instructions

1. Preheat oven to 400°F.
2. ...

## Notes

Great with spaghetti and garlic bread.
```

## Deploying to GitHub Pages

Build the site then push the `site/` directory to your `gh-pages` branch:

```bash
uv run zensical build
```
