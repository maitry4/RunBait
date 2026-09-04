"""
Phase 1 — Repo Context Extraction

Uses the GitHub REST API (no cloning required) to build a lean, structured
summary of the repository. This summary is fed to the AI instead of raw files.

Key signals extracted:
- README content (trimmed)
- Full file tree (filtered to meaningful paths)
- package.json / framework detection
- Detected URL routes from directory structure
- Content snippets of key page/route files
"""

import re
import json
import base64
import requests
from typing import Optional
from schemas import RepoContext


# File patterns that indicate routing / pages (framework-agnostic)
ROUTE_PATTERNS = [
    r"pages/.*\.(tsx?|jsx?|vue|svelte)$",
    r"app/.*\.(tsx?|jsx?|vue|svelte)$",
    r"src/pages/.*\.(tsx?|jsx?|vue|svelte)$",
    r"src/app/.*\.(tsx?|jsx?|vue|svelte)$",
    r"src/routes/.*\.(tsx?|jsx?|vue|svelte)$",
    r"src/views/.*\.(tsx?|jsx?|vue|svelte)$",
]

# Files worth reading a snippet of for AI context
SNIPPET_TARGETS = [
    "package.json",
    "next.config.js", "next.config.ts", "next.config.mjs",
    "vite.config.ts", "vite.config.js",
    "nuxt.config.ts",
    "astro.config.mjs",
]

# Maximum characters to include per file snippet
SNIPPET_MAX_CHARS = 2000
README_MAX_CHARS = 4000


def _github_get(url: str, token: Optional[str]) -> dict | list:
    """Make an authenticated GET request to the GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _decode_content(data: dict) -> str:
    """Decode base64-encoded file content from GitHub API response."""
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return data.get("content", "")


def _detect_framework(file_tree: list[str], package_json_content: Optional[str]) -> str:
    """Heuristically detect the frontend framework."""
    if package_json_content:
        try:
            pkg = json.loads(package_json_content)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "Next.js"
            if "nuxt" in deps or "@nuxt/core" in deps:
                return "Nuxt.js"
            if "astro" in deps:
                return "Astro"
            if "vite" in deps:
                return "React+Vite" if "react" in deps else "Vue+Vite"
            if "gatsby" in deps:
                return "Gatsby"
            if "react" in deps:
                return "React (CRA)"
            if "vue" in deps:
                return "Vue.js"
            if "svelte" in deps:
                return "SvelteKit"
        except json.JSONDecodeError:
            pass

    # Fallback: check file tree hints
    tree_str = "\n".join(file_tree)
    if "next.config" in tree_str:
        return "Next.js"
    if "nuxt.config" in tree_str:
        return "Nuxt.js"
    if "astro.config" in tree_str:
        return "Astro"
    return "Unknown"


def _infer_routes(file_tree: list[str], framework: str) -> list[str]:
    """Convert file paths into URL routes based on framework conventions."""
    routes = set()

    for path in file_tree:
        # Next.js pages directory
        if re.search(r"(src/)?pages/(.+)\.(tsx?|jsx?)$", path):
            match = re.search(r"(src/)?pages/(.+)\.(tsx?|jsx?)$", path)
            page = match.group(2)
            # Strip index, _app, _document
            if page in ("index", "_app", "_document", "_error", "404", "500"):
                if page == "index":
                    routes.add("/")
                continue
            # Dynamic routes: [param] -> :param
            page = re.sub(r"\[([^\]]+)\]", r":\1", page)
            routes.add("/" + page)

        # Next.js app directory
        elif re.search(r"(src/)?app/(.+)/page\.(tsx?|jsx?)$", path):
            match = re.search(r"(src/)?app/(.+)/page\.(tsx?|jsx?)$", path)
            segment = match.group(2)
            segment = re.sub(r"\(([^\)]+)\)", "", segment)  # strip route groups
            segment = re.sub(r"\[([^\]]+)\]", r":\1", segment)
            segment = segment.strip("/")
            routes.add("/" + segment if segment else "/")

    # Always add home
    routes.add("/")
    return sorted(routes)


def _filter_tree(all_files: list[str]) -> list[str]:
    """Keep only files relevant for AI context (drop build artifacts, node_modules, etc.)."""
    skip_prefixes = (
        "node_modules/", ".next/", ".nuxt/", "dist/", "build/",
        ".git/", ".cache/", "coverage/", "out/", ".turbo/",
    )
    skip_extensions = (
        ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".woff", ".woff2", ".ttf", ".eot", ".map",
    )
    result = []
    for f in all_files:
        if any(f.startswith(p) for p in skip_prefixes):
            continue
        if any(f.endswith(e) for e in skip_extensions):
            continue
        result.append(f)
    return result


def extract_repo_context(owner: str, repo: str, token: Optional[str] = None) -> RepoContext:
    """
    Main entry point for Phase 1.
    Returns a RepoContext object with all signals needed for AI flow discovery.
    """
    base = f"https://api.github.com/repos/{owner}/{repo}"

    # ── 1. README ─────────────────────────────────────────────────────────────
    readme_text = ""
    try:
        readme_data = _github_get(f"{base}/readme", token)
        readme_text = _decode_content(readme_data)[:README_MAX_CHARS]
    except Exception:
        readme_text = "(README not found)"

    # ── 2. Full file tree (recursive) ─────────────────────────────────────────
    all_files = []
    try:
        tree_data = _github_get(f"{base}/git/trees/HEAD?recursive=1", token)
        all_files = [
            item["path"] for item in tree_data.get("tree", [])
            if item["type"] == "blob"
        ]
    except Exception:
        all_files = []

    filtered_tree = _filter_tree(all_files)

    # ── 3. Key file snippets ───────────────────────────────────────────────────
    key_files = {}
    package_json_content = None

    # First pass: collect config files and package.json
    for target in SNIPPET_TARGETS:
        # Find in tree (could be nested)
        matches = [f for f in all_files if f == target or f.endswith("/" + target)]
        if matches:
            path = matches[0]  # take root-level first
            try:
                data = _github_get(f"{base}/contents/{path}", token)
                content = _decode_content(data)[:SNIPPET_MAX_CHARS]
                key_files[path] = content
                if target == "package.json" and path in ("package.json",):
                    package_json_content = content
            except Exception:
                pass

    # Second pass: collect route/page file snippets (up to 8 files)
    route_file_count = 0
    for path in filtered_tree:
        if route_file_count >= 8:
            break
        if any(re.search(pattern, path) for pattern in ROUTE_PATTERNS):
            try:
                data = _github_get(f"{base}/contents/{path}", token)
                content = _decode_content(data)[:SNIPPET_MAX_CHARS]
                key_files[path] = content
                route_file_count += 1
            except Exception:
                pass

    # ── 4. Framework detection + route inference ───────────────────────────────
    framework = _detect_framework(filtered_tree, package_json_content)
    detected_routes = _infer_routes(filtered_tree, framework)

    return RepoContext(
        repo_url=f"https://github.com/{owner}/{repo}",
        readme=readme_text,
        file_tree=filtered_tree,
        package_json=package_json_content,
        framework=framework,
        detected_routes=detected_routes,
        key_files=key_files,
    )
