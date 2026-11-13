"""Turn the docs splits into Confluence-friendly HTML pages."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "confluence"

PAGES = [
    ("01-overview", "Overview", DOCS / "overview.md"),
    ("02-concepts", "Concepts", DOCS / "concepts.md"),
    ("03-architecture", "Architecture", DOCS / "architecture.md"),
    ("04-ontology", "Ontology", DOCS / "ontology.md"),
    ("05-agents", "Agents", DOCS / "agents.md"),
    ("06-retrieval", "Retrieval", DOCS / "retrieval.md"),
    ("07-evaluation", "Evaluation", DOCS / "evaluation.md"),
    ("08-adrs", "ADRs", None),
    ("09-tools", "Tools", DOCS / "tools.md"),
    ("10-security-governance", "Security and governance", DOCS / "security-governance.md"),
    ("11-target-architecture", "Target architecture", DOCS / "target-architecture.md"),
]


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda match: (
            f'<img alt="{match.group(1)}" src="{_asset(html.unescape(match.group(2)))}"/>'
        ),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{html.unescape(match.group(2))}">{match.group(1)}</a>',
        text,
    )
    return text


def _asset(url: str) -> str:
    if url.startswith("assets/"):
        return "../" + url
    if url.startswith("../assets/"):
        return url
    return url


def convert(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            buff: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buff.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buff)) + "</code></pre>")
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*-+", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            header = [cell.strip() for cell in rows[0].strip("|").split("|")]
            body_rows = rows[2:]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in header) + "</tr></thead><tbody>")
            for row in body_rows:
                cells = [cell.strip() for cell in row.strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in cells) + "</tr>")
            out.append("</tbody></table>")
            continue
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif line.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(out)


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)} — AgriTrace</title>
  <style>
    body {{ font-family: Georgia, serif; color: #1C1408; background: #F7F3E8; margin: 2rem auto; max-width: 920px; line-height: 1.5; }}
    h1, h2, h3 {{ color: #14352A; }}
    code, pre {{ font-family: ui-monospace, monospace; background: #E7F0EA; }}
    pre {{ padding: 1rem; overflow: auto; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #1F4D3A; padding: 0.4rem 0.6rem; text-align: left; }}
    th {{ background: #1F4D3A; color: #F7F3E8; }}
    img {{ max-width: 100%; }}
    a {{ color: #1F4D3A; }}
  </style>
</head>
<body>
<p><em>AgriTrace. Fictional data. Canonical write-up: the repository README. Images: docs/assets, referenced relatively from this file.</em></p>
{body}
</body>
</html>
"""


def adr_markdown() -> str:
    parts = ["# Architecture decision records", ""]
    for path in sorted((DOCS / "adr").glob("*.md")):
        parts.append(path.read_text(encoding="utf-8"))
        parts.append("")
    return "\n".join(parts)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, title, source in PAGES:
        if source is None:
            raw = adr_markdown()
        else:
            raw = source.read_text(encoding="utf-8")
        (OUT / f"{slug}.html").write_text(page(title, convert(raw)), encoding="utf-8")
        print(slug)


if __name__ == "__main__":
    main()
