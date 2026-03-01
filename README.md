# Family Cookbook

A searchable static website of family recipes extracted from photos of cookbooks,
magazine clippings, and handwritten recipe cards — powered by OpenAI GPT-4o Vision
and published to GitHub Pages.

**Live site:** https://scottsaenz.github.io/family_cookbook *(update after setup)*

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for package management
- An [OpenAI API key](https://platform.openai.com/api-keys) (GPT-4o is used for vision)

---

## Local Development

```bash
# Install dependencies
uv sync

# Set your OpenAI API key (or add to .env file)
export OPENAI_API_KEY="sk-..."

# Process recipe images into Markdown
uv run python -m family_cookbook.process_recipes images/

# Regenerate the recipe index and tags page
uv run python -m family_cookbook.build_index

# Preview the site locally
uv run zensical serve
```

Open <http://127.0.0.1:8000> to browse your recipes.

---

## Deploying to GitHub Pages

### 1. Create the GitHub repository

1. Go to <https://github.com/new>
2. Name it `family_cookbook` (or any name you like)
3. Set it to **Public** (required for free GitHub Pages)
4. Do **not** add a README or .gitignore — the repo should be empty

### 2. Update `site_url` in `mkdocs.yml`

Open `mkdocs.yml` and set `site_url` to your GitHub Pages URL:

```yaml
site_url: https://<your-github-username>.github.io/family_cookbook
```

Commit the change:

```bash
git add mkdocs.yml
git commit -m "Set site_url for GitHub Pages"
```

### 3. Push to GitHub

```bash
git remote add origin https://github.com/<your-github-username>/family_cookbook.git
git push -u origin main
```

### 4. Enable GitHub Pages

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Set the branch to **`gh-pages`** / **`/ (root)`**
4. Click **Save**

The GitHub Actions workflow (`.github/workflows/deploy.yml`) will automatically
build and deploy the site to `gh-pages` on every push to `main`. The first
deployment takes about 2-3 minutes.

---

## Adding New Recipes

```bash
# 1. Put new recipe images in images/
# 2. Process them (skips already-processed images by default)
uv run python -m family_cookbook.process_recipes images/

# 3. Rebuild the index
uv run python -m family_cookbook.build_index

# 4. Commit and push — GitHub Actions deploys automatically
git add docs/
git commit -m "Add new recipes"
git push
```

---

## CLI Reference

### `process-recipes`

```bash
uv run python -m family_cookbook.process_recipes <image-directory> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-o`, `--output` | `docs/recipes` | Output directory for Markdown files |
| `--model` | `gpt-4o` | OpenAI model to use |
| `--api-key` | `$OPENAI_API_KEY` | API key (or set the env var / `.env` file) |
| `--no-skip` | off | Re-process images that already have Markdown |

Supported formats: JPG, PNG, WebP, GIF, TIFF, BMP, HEIC.

### `build-index`

```bash
uv run python -m family_cookbook.build_index
```

Regenerates `docs/recipes/index.md` (grouped by meal type) and `docs/tags.md`
(alphabetical tag listing). Run this after adding new recipes.

---

## Project Structure

```
family_cookbook/
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions → GitHub Pages
├── family_cookbook/
│   ├── process_recipes.py   # Image → Markdown pipeline
│   └── build_index.py       # Recipe index + tags page generator
├── docs/
│   ├── index.md             # Site home page
│   ├── tags.md              # Tag browsing page (auto-generated)
│   ├── recipes/             # Generated recipe Markdown files
│   └── stylesheets/
│       └── extra.css
├── images/                  # Source recipe photos (git-ignored)
├── mkdocs.yml               # Zensical site configuration
└── pyproject.toml           # uv project & dependencies
```
