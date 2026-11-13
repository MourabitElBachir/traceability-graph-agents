"""Draw the README figures as SVG and PNG. No external diagram service."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
FOREST = "#1F4D3A"
DEEP = "#14352A"
WHEAT = "#C4A35A"
CREAM = "#F7F3E8"
INK = "#1C1408"
CLAY = "#8C4A3A"
MIST = "#E7F0EA"
WHITE = "#FFFCF7"


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _bold(size: int) -> ImageFont.ImageFont:
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return _font(size)


def save_svg(name: str, body: str, width: int, height: int) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">\n{body}\n</svg>\n'
    )
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")


def new_png(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), CREAM)
    return image, ImageDraw.Draw(image)


def save_png(name: str, image: Image.Image) -> None:
    image.save(OUT / f"{name}.png", "PNG")


def hero() -> None:
    width, height = 1400, 420
    save_svg(
        "hero-banner",
        f"""
        <rect width="1400" height="420" fill="{DEEP}"/>
        <rect x="0" y="0" width="14" height="420" fill="{WHEAT}"/>
        <text x="72" y="150" fill="{CREAM}" font-family="Georgia, serif" font-size="64">AgriTrace</text>
        <text x="72" y="210" fill="{WHEAT}" font-family="Georgia, serif" font-size="28">Wheat BLE-0457 → flour FAR-118 → biscuits BIS-031</text>
        <text x="72" y="258" fill="{CREAM}" font-family="Georgia, serif" font-size="22">Certificate CERT-77 · knowledge graph · GraphRAG · multi-agent recall</text>
        <text x="72" y="330" fill="{MIST}" font-family="Georgia, serif" font-size="18">Fictional agrifood data. No real company. No allocated GS1 keys.</text>
        <circle cx="1120" cy="150" r="18" fill="{WHEAT}"/>
        <circle cx="1220" cy="150" r="18" fill="{CREAM}"/>
        <circle cx="1320" cy="150" r="18" fill="{WHEAT}"/>
        <line x1="1138" y1="150" x2="1202" y2="150" stroke="{WHEAT}" stroke-width="3"/>
        <line x1="1238" y1="150" x2="1302" y2="150" stroke="{WHEAT}" stroke-width="3"/>
        <text x="1090" y="210" fill="{CREAM}" font-family="Georgia, serif" font-size="16">BLE-0457</text>
        <text x="1190" y="210" fill="{CREAM}" font-family="Georgia, serif" font-size="16">FAR-118</text>
        <text x="1290" y="210" fill="{CREAM}" font-family="Georgia, serif" font-size="16">BIS-031</text>
        <text x="1160" y="270" fill="{WHEAT}" font-family="Georgia, serif" font-size="16">CERT-77</text>
        """,
        width,
        height,
    )
    image, draw = new_png(width, height)
    draw.rectangle((0, 0, width, height), fill=DEEP)
    draw.rectangle((0, 0, 14, height), fill=WHEAT)
    draw.text((72, 110), "AgriTrace", font=_bold(64), fill=CREAM)
    draw.text((72, 190), "Wheat BLE-0457  →  flour FAR-118  →  biscuits BIS-031", font=_font(28), fill=WHEAT)
    draw.text((72, 240), "Certificate CERT-77 · knowledge graph · GraphRAG · multi-agent recall", font=_font(22), fill=CREAM)
    draw.text((72, 320), "Fictional agrifood data. No real company. No allocated GS1 keys.", font=_font(18), fill=MIST)
    for x, label in ((1120, "BLE-0457"), (1220, "FAR-118"), (1320, "BIS-031")):
        draw.ellipse((x - 18, 132, x + 18, 168), fill=WHEAT)
        draw.text((x - 36, 188), label, font=_font(16), fill=CREAM)
    draw.line((1138, 150, 1202, 150), fill=WHEAT, width=3)
    draw.line((1238, 150, 1302, 150), fill=WHEAT, width=3)
    save_png("hero-banner", image)


def boxes_svg(title: str, nodes: list[tuple[int, int, str, str]], edges: list[tuple[int, int]]) -> str:
    parts = [f'<rect width="1200" height="640" fill="{CREAM}"/>', f'<text x="40" y="48" fill="{DEEP}" font-family="Georgia, serif" font-size="28">{title}</text>']
    for x, y, label, fill in nodes:
        parts.append(f'<rect x="{x}" y="{y}" width="220" height="72" rx="10" fill="{fill}" stroke="{DEEP}"/>')
        parts.append(f'<text x="{x + 16}" y="{y + 42}" fill="{WHITE if fill in {FOREST, DEEP, CLAY} else INK}" font-family="Georgia, serif" font-size="16">{label}</text>')
    for a, b in edges:
        x1, y1, _, _ = nodes[a]
        x2, y2, _, _ = nodes[b]
        parts.append(f'<line x1="{x1 + 220}" y1="{y1 + 36}" x2="{x2}" y2="{y2 + 36}" stroke="{WHEAT}" stroke-width="3"/>')
    return "\n".join(parts)


def worked() -> None:
    nodes = [
        (40, 120, "Ferme des Collines", FOREST),
        (320, 120, "BLE-0457 wheat", WHEAT),
        (600, 120, "Moulin du Val", FOREST),
        (880, 120, "FAR-118 flour", WHEAT),
        (320, 280, "Fournil Lumière", FOREST),
        (600, 280, "BIS-031 biscuits", WHEAT),
        (880, 280, "Épicerie Rive", FOREST),
        (600, 440, "CERT-77 valid", MIST),
    ]
    # custom svg because the generic edge helper assumes left-to-right only
    body = f"""
    <rect width="1200" height="620" fill="{CREAM}"/>
    <text x="40" y="48" fill="{DEEP}" font-family="Georgia, serif" font-size="28">Running example</text>
    <text x="40" y="84" fill="{INK}" font-family="Georgia, serif" font-size="16">One genealogy. CERT-77 covers all three lots. The clock is 2026-11-13.</text>
    """
    for x, y, label, fill in nodes:
        color = WHITE if fill in {FOREST, DEEP} else INK
        body += f'<rect x="{x}" y="{y}" width="240" height="70" rx="12" fill="{fill}" stroke="{DEEP}"/>'
        body += f'<text x="{x + 16}" y="{y + 42}" fill="{color}" font-family="Georgia, serif" font-size="18">{label}</text>'
    lines = [(280, 155, 320, 155), (560, 155, 600, 155), (840, 155, 880, 155), (1000, 190, 720, 280), (560, 315, 600, 315), (840, 315, 880, 315), (720, 350, 720, 440)]
    for x1, y1, x2, y2 in lines:
        body += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{WHEAT}" stroke-width="3"/>'
    save_svg("worked-example", body, 1200, 620)
    image, draw = new_png(1200, 620)
    draw.text((40, 24), "Running example", font=_bold(28), fill=DEEP)
    draw.text((40, 64), "BLE-0457 → FAR-118 → BIS-031, covered by CERT-77.", font=_font(18), fill=INK)
    for x, y, label, fill in nodes:
        draw.rounded_rectangle((x, y, x + 240, y + 70), radius=12, fill=fill, outline=DEEP)
        fill_text = WHITE if fill == FOREST else INK
        draw.text((x + 16, y + 22), label, font=_font(18), fill=fill_text)
    save_png("worked-example", image)


def architecture() -> None:
    body = f"""
    <rect width="1200" height="520" fill="{CREAM}"/>
    <text x="40" y="46" fill="{DEEP}" font-family="Georgia, serif" font-size="28">What this repository runs</text>
    """
    labels = [
        (40, 100, "SQLite ERP"),
        (280, 100, "Ingestion"),
        (520, 100, "Neo4j graph"),
        (760, 100, "Vector chunks"),
        (40, 250, "GraphRAG"),
        (280, 250, "LangGraph"),
        (520, 250, "FastAPI"),
        (760, 250, "MCP + A2A"),
        (280, 390, "Human approval"),
    ]
    for x, y, label in labels:
        body += f'<rect x="{x}" y="{y}" width="200" height="70" rx="10" fill="{FOREST}"/>'
        body += f'<text x="{x + 16}" y="{y + 42}" fill="{CREAM}" font-family="Georgia, serif" font-size="18">{label}</text>'
    for x1, x2, y in ((240, 280, 135), (480, 520, 135), (720, 760, 135), (140, 140, 170), (380, 380, 170)):
        body += f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y if y == 135 else 250}" stroke="{WHEAT}" stroke-width="3"/>'
    body += f'<line x1="140" y1="170" x2="140" y2="250" stroke="{WHEAT}" stroke-width="3"/>'
    body += f'<line x1="380" y1="170" x2="380" y2="250" stroke="{WHEAT}" stroke-width="3"/>'
    body += f'<line x1="380" y1="320" x2="380" y2="390" stroke="{CLAY}" stroke-width="3"/>'
    save_svg("architecture", body, 1200, 520)
    image, draw = new_png(1200, 520)
    draw.text((40, 20), "What this repository runs", font=_bold(28), fill=DEEP)
    for x, y, label in labels:
        draw.rounded_rectangle((x, y, x + 200, y + 70), radius=10, fill=FOREST)
        draw.text((x + 16, y + 22), label, font=_font(18), fill=CREAM)
    save_png("architecture", image)


def ontology() -> None:
    body = f'<rect width="1200" height="640" fill="{CREAM}"/><text x="40" y="46" fill="{DEEP}" font-family="Georgia, serif" font-size="28">Ontology to property graph</text>'
    nodes = [
        (40, 90, "Actor"),
        (280, 90, "Site"),
        (520, 90, "Lot"),
        (760, 90, "Product"),
        (40, 240, "ProcessStep"),
        (280, 240, "Shipment"),
        (520, 240, "Certificate"),
        (760, 240, "Audit"),
        (520, 390, "Document"),
        (760, 390, "Chunk"),
    ]
    for x, y, label in nodes:
        body += f'<rect x="{x}" y="{y}" width="180" height="64" rx="10" fill="{MIST}" stroke="{FOREST}"/>'
        body += f'<text x="{x + 16}" y="{y + 38}" fill="{DEEP}" font-family="Georgia, serif" font-size="18">{label}</text>'
    body += f'<text x="40" y="540" fill="{INK}" font-family="Georgia, serif" font-size="16">INPUT_OF is derived from consumes/produces. CERT-77 COVERS BLE-0457, FAR-118 and BIS-031.</text>'
    body += f'<text x="40" y="575" fill="{INK}" font-family="Georgia, serif" font-size="16">EPCIS alignment: what = lot, when = eventTime, where = site, why = bizStep.</text>'
    save_svg("ontology-schema", body, 1200, 640)
    image, draw = new_png(1200, 640)
    draw.text((40, 20), "Ontology to property graph", font=_bold(28), fill=DEEP)
    for x, y, label in nodes:
        draw.rounded_rectangle((x, y, x + 180, y + 64), radius=10, fill=MIST, outline=FOREST)
        draw.text((x + 16, y + 20), label, font=_font(18), fill=DEEP)
    draw.text((40, 520), "INPUT_OF is derived. CERT-77 covers BLE-0457, FAR-118, BIS-031.", font=_font(16), fill=INK)
    save_png("ontology-schema", image)


def agents() -> None:
    body = f'<rect width="1200" height="420" fill="{CREAM}"/><text x="40" y="46" fill="{DEEP}" font-family="Georgia, serif" font-size="28">LangGraph supervisor</text>'
    labels = [(40, 120, "route"), (250, 120, "trace"), (460, 120, "compliance"), (700, 120, "documents"), (250, 270, "recall"), (520, 270, "approval"), (790, 270, "compose")]
    for x, y, label in labels:
        fill = CLAY if label == "approval" else FOREST
        body += f'<rect x="{x}" y="{y}" width="170" height="64" rx="10" fill="{fill}"/>'
        body += f'<text x="{x + 16}" y="{y + 38}" fill="{CREAM}" font-family="Georgia, serif" font-size="18">{label}</text>'
    save_svg("langgraph", body, 1200, 420)
    image, draw = new_png(1200, 420)
    draw.text((40, 20), "LangGraph supervisor", font=_bold(28), fill=DEEP)
    for x, y, label in labels:
        fill = CLAY if label == "approval" else FOREST
        draw.rounded_rectangle((x, y, x + 170, y + 64), radius=10, fill=fill)
        draw.text((x + 16, y + 20), label, font=_font(18), fill=CREAM)
    save_png("langgraph", image)


def sequence() -> None:
    body = f"""
    <rect width="1200" height="560" fill="{CREAM}"/>
    <text x="40" y="46" fill="{DEEP}" font-family="Georgia, serif" font-size="28">Recall of BLE-0457, with a person in the loop</text>
    """
    lanes = [(80, "User"), (320, "Supervisor"), (560, "Trace"), (800, "Human")]
    for x, label in lanes:
        body += f'<text x="{x}" y="100" fill="{FOREST}" font-family="Georgia, serif" font-size="18">{label}</text>'
        body += f'<line x1="{x + 30}" y1="120" x2="{x + 30}" y2="520" stroke="{MIST}" stroke-width="2"/>'
    steps = [
        (150, "Ask recall impact"),
        (210, "Downstream FAR-118, BIS-031"),
        (270, "CERT-77 still valid"),
        (340, "Interrupt: do not issue yet"),
        (410, "Approve"),
        (470, "Recall issued"),
    ]
    for y, label in steps:
        body += f'<text x="140" y="{y}" fill="{INK}" font-family="Georgia, serif" font-size="16">{label}</text>'
    save_svg("sequence-recall", body, 1200, 560)
    image, draw = new_png(1200, 560)
    draw.text((40, 20), "Recall of BLE-0457, with a person in the loop", font=_bold(26), fill=DEEP)
    for x, label in lanes:
        draw.text((x, 70), label, font=_bold(18), fill=FOREST)
        draw.line((x + 30, 100, x + 30, 520), fill=MIST, width=2)
    y = 140
    for _, label in steps:
        draw.text((140, y), label, font=_font(18), fill=INK)
        y += 50
    save_png("sequence-recall", image)


def target() -> None:
    body = f"""
    <rect width="1400" height="720" fill="{CREAM}"/>
    <text x="40" y="46" fill="{DEEP}" font-family="Georgia, serif" font-size="28">Target platform, not what this repo deploys</text>
    <rect x="40" y="80" width="640" height="600" rx="16" fill="{WHITE}" stroke="{FOREST}"/>
    <rect x="720" y="80" width="640" height="600" rx="16" fill="{WHITE}" stroke="{FOREST}"/>
    <text x="64" y="120" fill="{FOREST}" font-family="Georgia, serif" font-size="22">Business view</text>
    <text x="744" y="120" fill="{FOREST}" font-family="Georgia, serif" font-size="22">Technical view</text>
    """
    left = ["Producers", "Processors", "Certification bodies", "Auditors", "Retailers", "Use cases: trace, recall, certify, audit"]
    right = ["Event stream", "SQL + graph + vectors", "GraphRAG and LangGraph", "MCP / A2A", "API gateway and Kubernetes", "CI/CD, observability, governance"]
    for index, label in enumerate(left):
        body += f'<text x="64" y="{180 + index * 70}" fill="{INK}" font-family="Georgia, serif" font-size="20">{label}</text>'
    for index, label in enumerate(right):
        body += f'<text x="744" y="{180 + index * 70}" fill="{INK}" font-family="Georgia, serif" font-size="20">{label}</text>'
    save_svg("target-architecture", body, 1400, 720)
    image, draw = new_png(1400, 720)
    draw.text((40, 16), "Target platform, not what this repo deploys", font=_bold(26), fill=DEEP)
    draw.rounded_rectangle((40, 70, 680, 680), radius=16, fill=WHITE, outline=FOREST)
    draw.rounded_rectangle((720, 70, 1360, 680), radius=16, fill=WHITE, outline=FOREST)
    draw.text((64, 90), "Business view", font=_bold(22), fill=FOREST)
    draw.text((744, 90), "Technical view", font=_bold(22), fill=FOREST)
    for index, label in enumerate(left):
        draw.text((64, 160 + index * 70), label, font=_font(20), fill=INK)
    for index, label in enumerate(right):
        draw.text((744, 160 + index * 70), label, font=_font(20), fill=INK)
    save_png("target-architecture", image)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hero()
    worked()
    architecture()
    ontology()
    agents()
    sequence()
    target()
    print("wrote", sorted(path.name for path in OUT.iterdir()))


if __name__ == "__main__":
    main()
