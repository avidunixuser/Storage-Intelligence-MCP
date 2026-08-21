"""Generate the editable and rendered Storage Intelligence architecture diagrams."""

from __future__ import annotations

import base64
import io
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "architecture"
SVG_PATH = OUTPUT / "storage-intelligence-architecture.svg"
DRAWIO_PATH = OUTPUT / "storage-intelligence-architecture.drawio"
VSDX_PATH = OUTPUT / "storage-intelligence-architecture.vsdx"

ICON_ARCHIVE = "https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V24.zip"
VSDX_TEMPLATE = (
    "https://raw.githubusercontent.com/dave-howard/vsdx/master/"
    "tests/test9_rect_and_line.vsdx"
)

WIDTH = 1800
HEIGHT = 1140
VISIO_WIDTH = 24.0
VISIO_HEIGHT = 15.0


@dataclass(frozen=True)
class Node:
    id: str
    x: int
    y: int
    width: int
    height: int
    title: str
    detail: str
    icon: str
    fill: str = "#ffffff"
    stroke: str = "#9fb3c8"


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int
    title: str
    subtitle: str
    fill: str
    stroke: str
    dashed: bool = False


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str
    color: str = "#52738f"
    dashed: bool = False
    width: int = 2


ICONS = {
    "user": "10230-icon-service-Users.svg",
    "entra": "10231-icon-service-Entra-ID-Protection.svg",
    "identity": "10227-icon-service-Entra-Managed-Identities.svg",
    "container": "02884-icon-service-Worker-Container-App.svg",
    "foundry": "038470523-icon-service-Foundry-Agent-Service.svg",
    "function": "10029-icon-service-Function-Apps.svg",
    "private": "02579-icon-service-Private-Endpoints.svg",
    "dns": "10064-icon-service-DNS-Zones.svg",
    "cosmos": "10121-icon-service-Azure-Cosmos-DB.svg",
    "search": "10044-icon-service-Cognitive-Search.svg",
    "storage": "10086-icon-service-Storage-Accounts.svg",
    "keyvault": "10245-icon-service-Key-Vaults.svg",
    "registry": "10105-icon-service-Container-Registries.svg",
    "appinsights": "00012-icon-service-Application-Insights.svg",
    "logs": "00009-icon-service-Log-Analytics-Workspaces.svg",
    "vnet": "10061-icon-service-Virtual-Networks.svg",
}


REGIONS = [
    Region(
        20,
        82,
        1760,
        970,
        "Azure subscription c82406dd... / rg-storage-intel-mcpa2a",
        "Sweden Central | Infrastructure as Code: Bicep",
        "#f8fbff",
        "#0078d4",
    ),
    Region(
        45,
        125,
        1710,
        245,
        "Primary request path",
        "1 Send request  |  2 Authenticate  |  3 Route REST, MCP, or A2A  |  4 Query or persist in Cosmos DB",
        "#eef7ff",
        "#5ea0d6",
    ),
    Region(
        45,
        395,
        1710,
        245,
        "Optional Foundry tool path",
        "A Select agent tool  |  B Invoke Foundry agent  |  C Call private Function tool and dependencies",
        "#f2f3ff",
        "#7f77c5",
    ),
    Region(
        45,
        665,
        1070,
        360,
        "Private network boundary",
        "vnet-storage-intel-nladau77 | 192.168.0.0/16 | Private Link and Private DNS",
        "#f4faff",
        "#3a96dd",
    ),
    Region(
        1140,
        665,
        615,
        360,
        "Identity and operations",
        "User-assigned managed identities, least-privilege RBAC, delivery, and monitoring",
        "#faf7ff",
        "#8064a2",
    ),
]


NODES = [
    Node(
        "clients",
        75,
        195,
        260,
        135,
        "External clients",
        "Browser UI\nMCP Streamable HTTP /mcp/\nA2A Agent Card + /a2a\nHTTPS only",
        "user",
        "#eef6ff",
        "#0078d4",
    ),
    Node(
        "entra",
        380,
        195,
        250,
        135,
        "Microsoft Entra ID",
        "Easy Auth\nOAuth 2.0 bearer token\nApp registration (SPN)\nAdmin app role",
        "entra",
        "#f2f9ff",
        "#0078d4",
    ),
    Node(
        "web",
        675,
        185,
        365,
        155,
        "Azure Container App",
        "React UI + FastAPI/Uvicorn\nREST /api/v1\nMCP 2.0 /mcp/\nA2A Agent Card + /a2a",
        "container",
        "#eaf5ff",
        "#0078d4",
    ),
    Node(
        "service",
        1085,
        195,
        285,
        135,
        "Shared application service",
        "StorageIntelligenceService\nDeterministic analytics\nAzure discovery connectors\nOne result contract",
        "storage",
        "#f7fbf3",
        "#6a8e3a",
    ),
    Node(
        "cosmos",
        1415,
        195,
        290,
        135,
        "Azure Cosmos DB",
        "storage-intelligence database\nInventory + saved questions\n/subscription_id partition scope\n400 RU/s shared throughput",
        "cosmos",
    ),
    Node(
        "agententry",
        100,
        470,
        280,
        130,
        "Agent tool request",
        "Optional path selected by\nStorageIntelligenceService\nSame deterministic\nbusiness logic",
        "storage",
        "#f7fbf3",
        "#6a8e3a",
    ),
    Node(
        "foundry",
        465,
        470,
        300,
        130,
        "Microsoft Foundry Agent",
        "Private account + project\nAgent Service capability host\nAI Search + Cosmos + Storage",
        "foundry",
        "#f0efff",
        "#6b5fb5",
    ),
    Node(
        "function",
        850,
        470,
        300,
        130,
        "Private Azure Function",
        "Python 3.13 / FC1\nManaged OpenAPI tool auth\nDurable Functions orchestration",
        "function",
        "#f4efff",
        "#8064a2",
    ),
    Node(
        "funcdeps",
        1235,
        455,
        470,
        160,
        "Private Function dependencies",
        "Function storage: Blob + Queue + Table\nADLS Gen2 lake + Azure Key Vault\nDurable Task Scheduler\nApp Insights + Log Analytics through AMPLS",
        "keyvault",
        "#f7f7fb",
        "#65758b",
    ),
    Node(
        "agentsubnet",
        70,
        745,
        235,
        105,
        "Agent subnet",
        "192.168.0.0/24\nFoundry network\ninjection",
        "foundry",
    ),
    Node(
        "containersubnet",
        325,
        745,
        235,
        105,
        "Container Apps",
        "192.168.2.0/24\nMicrosoft.App delegation",
        "container",
    ),
    Node(
        "functionsubnet",
        580,
        745,
        235,
        105,
        "Functions subnet",
        "192.168.3.0/24\nRegional VNet\nintegration",
        "function",
    ),
    Node(
        "pesubnet",
        835,
        745,
        235,
        105,
        "Private endpoints",
        "192.168.1.0/24\nInbound Function\nand PaaS endpoints",
        "private",
    ),
    Node(
        "dns",
        70,
        875,
        620,
        110,
        "Private DNS and Private Link",
        "VNet-linked zones resolve Foundry, Search, Cosmos, Storage, ACR,\nFunctions, Key Vault, Durable Task, and Azure Monitor to private endpoints.",
        "dns",
        "#f2f9ff",
        "#3a96dd",
    ),
    Node(
        "networkpolicy",
        715,
        875,
        355,
        110,
        "Network policy",
        "Public access disabled where supported\nPrivate east-west traffic\nNo inbound access to Function tools",
        "vnet",
        "#edf9f3",
        "#25855a",
    ),
    Node(
        "webmi",
        1165,
        745,
        565,
        105,
        "Web user-assigned managed identity",
        "Cosmos database-scoped data contributor\nFoundry User + AcrPull + Function Website Contributor",
        "identity",
        "#f1f8ff",
        "#2674b8",
    ),
    Node(
        "funcmi",
        1165,
        870,
        565,
        125,
        "Function user-assigned managed identity",
        "Blob Owner/Contributor + Queue/Table Contributor\nKey Vault Secrets User + Durable Task Contributor\nMonitoring Metrics Publisher",
        "identity",
        "#f6f2ff",
        "#7252aa",
    ),
]


EDGES = [
    Edge("clients", "entra", "1", "#0078d4", width=3),
    Edge("entra", "web", "2", "#0078d4", width=3),
    Edge("web", "service", "3", "#0078d4", width=3),
    Edge("service", "cosmos", "4", "#0078d4", width=3),
    Edge("agententry", "foundry", "A", "#6b5fb5", width=3),
    Edge("foundry", "function", "B", "#6b5fb5", width=3),
    Edge("function", "funcdeps", "C", "#6b5fb5", width=3),
]


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Storage-Intelligence-MCP"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def locate_icons(archive_bytes: bytes, destination: Path) -> dict[str, Path]:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive.extractall(destination)

    found: dict[str, Path] = {}
    for key, filename in ICONS.items():
        matches = list(destination.rglob(filename))
        if not matches:
            raise FileNotFoundError(f"Official Azure icon was not found: {filename}")
        found[key] = matches[0]
    return found


def svg_data_uri(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{payload}"


def node_lookup() -> dict[str, Node]:
    return {node.id: node for node in NODES}


def anchor(node: Node, toward: Node) -> tuple[float, float]:
    cx = node.x + node.width / 2
    cy = node.y + node.height / 2
    tx = toward.x + toward.width / 2
    ty = toward.y + toward.height / 2
    dx = tx - cx
    dy = ty - cy
    if abs(dx / node.width) > abs(dy / node.height):
        return (node.x + node.width if dx > 0 else node.x, cy)
    return (cx, node.y + node.height if dy > 0 else node.y)


def svg_edge_path(source: Node, target: Node) -> tuple[str, float, float]:
    x1, y1 = anchor(source, target)
    x2, y2 = anchor(target, source)
    return f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}", (x1 + x2) / 2, (y1 + y2) / 2 - 5


def validate_layout() -> None:
    for node in NODES:
        icon_size = min(46, node.height - 24)
        available_width = node.width - icon_size - 40
        if len(node.title) * 7.3 > available_width:
            raise ValueError(f"Title exceeds its card boundary: {node.id}: {node.title}")
        for line in node.detail.splitlines():
            if len(line) * 6.2 > available_width:
                raise ValueError(f"Detail exceeds its card boundary: {node.id}: {line}")
        final_baseline = node.y + 48 + 16 * (len(node.detail.splitlines()) - 1)
        if final_baseline > node.y + node.height - 12:
            raise ValueError(f"Text is too tall for its card boundary: {node.id}")


def render_svg(icons: dict[str, Path]) -> None:
    validate_layout()
    nodes = node_lookup()
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-labelledby="diagram-title diagram-description">',
        '<title id="diagram-title">Storage Intelligence MCP and A2A Azure architecture</title>',
        '<desc id="diagram-description">End-to-end architecture from authenticated clients through '
        "Container Apps, Microsoft Foundry, private Azure Functions, Private Link, and data services.</desc>",
        """
<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#16324f" flood-opacity=".14"/>
  </filter>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
    <path d="M0,0 L8,4 L0,8 z" fill="context-stroke"/>
  </marker>
  <style>
    .title { font: 700 27px "Segoe UI", Arial, sans-serif; fill: #15324a; }
    .subtitle { font: 14px "Segoe UI", Arial, sans-serif; fill: #52697d; }
    .region-title { font: 700 15px "Segoe UI", Arial, sans-serif; fill: #173b5e; }
    .region-subtitle { font: 12px "Segoe UI", Arial, sans-serif; fill: #64798a; }
    .node-title { font: 700 14px "Segoe UI", Arial, sans-serif; fill: #17324d; }
    .node-detail { font: 12px "Segoe UI", Arial, sans-serif; fill: #4f6475; }
    .step-label { font: 700 13px "Segoe UI", Arial, sans-serif; fill: #ffffff; }
    .legend { font: 12px "Segoe UI", Arial, sans-serif; fill: #40596f; }
  </style>
</defs>
<rect width="1800" height="1140" fill="#ffffff"/>
<text x="28" y="42" class="title">Storage Intelligence — MCP &amp; A2A Azure Architecture</text>
<text x="28" y="68" class="subtitle">Two request lanes make execution explicit;
support panels document private networking, managed identity, RBAC, delivery, and monitoring.</text>
""",
    ]
    parts.append("<defs>")
    for node in NODES:
        icon_size = min(46, node.height - 24)
        text_x = node.x + icon_size + 27
        parts.append(
            f'<clipPath id="clip-{node.id}"><rect x="{text_x}" y="{node.y + 8}" '
            f'width="{node.x + node.width - text_x - 10}" height="{node.height - 16}"/></clipPath>'
        )
    parts.append("</defs>")

    for region in REGIONS:
        dash = ' stroke-dasharray="8 6"' if region.dashed else ""
        parts.append(
            f'<rect x="{region.x}" y="{region.y}" width="{region.width}" height="{region.height}" '
            f'rx="12" fill="{region.fill}" stroke="{region.stroke}" stroke-width="2"{dash}/>'
        )
        parts.append(
            f'<text x="{region.x + 16}" y="{region.y + 24}" class="region-title">'
            f"{escape(region.title)}</text>"
        )
        parts.append(
            f'<text x="{region.x + 16}" y="{region.y + 43}" class="region-subtitle">'
            f"{escape(region.subtitle)}</text>"
        )

    for edge in EDGES:
        source = nodes[edge.source]
        target = nodes[edge.target]
        path, lx, ly = svg_edge_path(source, target)
        dash = ' stroke-dasharray="7 5"' if edge.dashed else ""
        parts.append(
            f'<path d="{path}" fill="none" '
            f'stroke="{edge.color}" stroke-width="{edge.width}" marker-end="url(#arrow)"{dash}/>'
        )
        if not edge.label:
            continue
        parts.append(
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="14" fill="{edge.color}" '
            'stroke="#ffffff" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="middle" '
            f'class="step-label">{escape(edge.label)}</text>'
        )

    for node in NODES:
        parts.append(
            f'<g id="{node.id}" filter="url(#shadow)">'
            f'<rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" '
            f'rx="9" fill="{node.fill}" stroke="{node.stroke}" stroke-width="1.6"/>'
        )
        icon_size = min(46, node.height - 24)
        icon_y = node.y + (node.height - icon_size) / 2
        parts.append(
            f'<image x="{node.x + 13}" y="{icon_y:.1f}" width="{icon_size}" height="{icon_size}" '
            f'href="{svg_data_uri(icons[node.icon])}"/>'
        )
        text_x = node.x + icon_size + 27
        parts.append(f'<g clip-path="url(#clip-{node.id})">')
        parts.append(f'<text x="{text_x}" y="{node.y + 27}" class="node-title">{escape(node.title)}</text>')
        parts.append(f'<text x="{text_x}" y="{node.y + 48}" class="node-detail">')
        for index, line in enumerate(node.detail.split("\n")):
            dy = "0" if index == 0 else "16"
            parts.append(f'<tspan x="{text_x}" dy="{dy}">{escape(line)}</tspan>')
        parts.append("</text></g></g>")

    parts.append(
        """
<g transform="translate(28 1080)">
  <line x1="0" y1="12" x2="48" y2="12" stroke="#0078d4" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="58" y="16" class="legend">Blue 1–4: primary UI, MCP, and A2A request path</text>
  <line x1="430" y1="12" x2="478" y2="12" stroke="#6b5fb5" stroke-width="3" marker-end="url(#arrow)"/>
  <text x="488" y="16" class="legend">Purple A–C: optional Foundry tool path</text>
  <text x="850" y="16" class="legend">Panels below: controls and placement, not additional request hops</text>
</g>
<text x="1772" y="1125" text-anchor="end" class="region-subtitle">
Source of truth: Bicep, application code, and deployed rg-storage-intel-mcpa2a topology</text>
</svg>
"""
    )
    SVG_PATH.write_text("".join(parts), encoding="utf-8")


def drawio_style(node: Node, icon_uri: str) -> str:
    return (
        "rounded=1;whiteSpace=wrap;html=1;shadow=1;align=left;verticalAlign=middle;"
        "spacingLeft=66;fontFamily=Segoe UI;fontSize=12;fontStyle=0;"
        f"fillColor={node.fill};strokeColor={node.stroke};"
        f"shape=label;image={icon_uri};imageWidth=42;imageHeight=42;imageAlign=left;"
        "imageVerticalAlign=middle;spacing=10;overflow=hidden;"
    )


def render_drawio(icons: dict[str, Path]) -> None:
    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]
    for index, region in enumerate(REGIONS, start=1):
        style = (
            "rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingTop=8;"
            "spacingLeft=10;fontFamily=Segoe UI;fontStyle=1;fontSize=14;"
            f"fillColor={region.fill};strokeColor={region.stroke};"
            f"dashed={1 if region.dashed else 0};"
        )
        value = f"<b>{escape(region.title)}</b><br><font size='2'>{escape(region.subtitle)}</font>"
        cells.append(
            f'<mxCell id="region-{index}" value={quoteattr(value)} style={quoteattr(style)} '
            f'vertex="1" parent="1"><mxGeometry x="{region.x}" y="{region.y}" '
            f'width="{region.width}" height="{region.height}" as="geometry"/></mxCell>'
        )

    for node in NODES:
        value = f"<b>{escape(node.title)}</b><br><font size='2'>{escape(node.detail).replace(chr(10), '<br>')}</font>"
        cells.append(
            f'<mxCell id="{node.id}" value={quoteattr(value)} '
            f'style={quoteattr(drawio_style(node, svg_data_uri(icons[node.icon])))} '
            f'vertex="1" parent="1"><mxGeometry x="{node.x}" y="{node.y}" '
            f'width="{node.width}" height="{node.height}" as="geometry"/></mxCell>'
        )

    for index, edge in enumerate(EDGES, start=1):
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeColor={edge.color};strokeWidth={edge.width};endArrow=block;"
            f"dashed={1 if edge.dashed else 0};fontFamily=Segoe UI;fontSize=11;"
        )
        cells.append(
            f'<mxCell id="edge-{index}" value={quoteattr(edge.label.replace(chr(10), "<br>"))} '
            f'style={quoteattr(style)} edge="1" parent="1" source="{edge.source}" target="{edge.target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    document = (
        '<mxfile host="app.diagrams.net" modified="2026-08-21T00:00:00.000Z" agent="Copilot" '
        'version="24.7.17" type="device"><diagram id="storage-intelligence" '
        'name="Storage Intelligence Architecture"><mxGraphModel dx="1800" dy="1100" grid="1" '
        'gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        'pageScale="1" pageWidth="1800" pageHeight="1100" math="0" shadow="0"><root>'
        + "".join(cells)
        + "</root></mxGraphModel></diagram></mxfile>"
    )
    DRAWIO_PATH.write_text(document, encoding="utf-8")


VISIO_NS = "http://schemas.microsoft.com/office/visio/2012/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def visio_xy(x: float, y: float) -> tuple[float, float]:
    return (x / WIDTH * VISIO_WIDTH, VISIO_HEIGHT - y / HEIGHT * VISIO_HEIGHT)


def add_cell(parent: ET.Element, name: str, value: str | float, formula: str | None = None) -> None:
    attributes = {"N": name, "V": str(value)}
    if formula is not None:
        attributes["F"] = formula
    ET.SubElement(parent, f"{{{VISIO_NS}}}Cell", attributes)


def add_text_format(shape: ET.Element, color: str, size: float, align: int = 1) -> None:
    character = ET.SubElement(shape, f"{{{VISIO_NS}}}Section", {"N": "Character"})
    row = ET.SubElement(character, f"{{{VISIO_NS}}}Row", {"IX": "0"})
    add_cell(row, "Color", color)
    add_cell(row, "Size", size)
    paragraph = ET.SubElement(shape, f"{{{VISIO_NS}}}Section", {"N": "Paragraph"})
    row = ET.SubElement(paragraph, f"{{{VISIO_NS}}}Row", {"IX": "0"})
    add_cell(row, "HorzAlign", align)
    add_cell(row, "SpAfter", "0")


def add_geometry(shape: ET.Element, width: float, height: float, no_fill: bool = False) -> None:
    geometry = ET.SubElement(shape, f"{{{VISIO_NS}}}Section", {"N": "Geometry", "IX": "0"})
    add_cell(geometry, "NoFill", "1" if no_fill else "0")
    add_cell(geometry, "NoLine", "0")
    points = [(0, 0), (width, 0), (width, height), (0, height), (0, 0)]
    for index, (x, y) in enumerate(points, start=1):
        row_type = "MoveTo" if index == 1 else "LineTo"
        row = ET.SubElement(
            geometry,
            f"{{{VISIO_NS}}}Row",
            {"T": row_type, "IX": str(index)},
        )
        add_cell(row, "X", x)
        add_cell(row, "Y", y)


def add_visio_rectangle(
    shapes: ET.Element,
    shape_id: int,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    fill: str,
    stroke: str,
    font_size: float = 0.12,
    dashed: bool = False,
    transparent: bool = False,
    icon_gutter: bool = False,
) -> None:
    pin_x, pin_y = visio_xy(x + width / 2, y + height / 2)
    visio_width = width / WIDTH * VISIO_WIDTH
    visio_height = height / HEIGHT * VISIO_HEIGHT
    shape = ET.SubElement(
        shapes,
        f"{{{VISIO_NS}}}Shape",
        {"ID": str(shape_id), "Type": "Shape", "LineStyle": "3", "FillStyle": "3", "TextStyle": "3"},
    )
    add_cell(shape, "PinX", pin_x)
    add_cell(shape, "PinY", pin_y)
    add_cell(shape, "Width", visio_width)
    add_cell(shape, "Height", visio_height)
    add_cell(shape, "LocPinX", visio_width / 2)
    add_cell(shape, "LocPinY", visio_height / 2)
    add_cell(shape, "Angle", "0")
    if icon_gutter:
        gutter = 68 / WIDTH * VISIO_WIDTH
        text_width = visio_width - gutter - 0.12
        text_height = visio_height - 0.12
        add_cell(shape, "TxtPinX", gutter + text_width / 2)
        add_cell(shape, "TxtPinY", visio_height / 2)
        add_cell(shape, "TxtWidth", text_width)
        add_cell(shape, "TxtHeight", text_height)
        add_cell(shape, "TxtLocPinX", text_width / 2)
        add_cell(shape, "TxtLocPinY", text_height / 2)
    add_cell(shape, "FillForegnd", fill)
    add_cell(shape, "FillPattern", "0" if transparent else "1")
    add_cell(shape, "LineColor", stroke)
    add_cell(shape, "LineWeight", "0.012")
    if dashed:
        add_cell(shape, "LinePattern", "10")
    add_cell(shape, "Rounding", "0.10")
    add_geometry(shape, visio_width, visio_height)
    add_text_format(shape, "#17324d", font_size)
    ET.SubElement(shape, f"{{{VISIO_NS}}}Text").text = text


def add_visio_image(
    shapes: ET.Element,
    shape_id: int,
    node: Node,
    relationship_id: str,
) -> None:
    size = min(46, node.height - 24)
    x = node.x + 13
    y = node.y + (node.height - size) / 2
    pin_x, pin_y = visio_xy(x + size / 2, y + size / 2)
    visio_width = size / WIDTH * VISIO_WIDTH
    visio_height = size / HEIGHT * VISIO_HEIGHT
    shape = ET.SubElement(
        shapes,
        f"{{{VISIO_NS}}}Shape",
        {"ID": str(shape_id), "Type": "Foreign", "LineStyle": "0", "FillStyle": "0", "TextStyle": "0"},
    )
    add_cell(shape, "PinX", pin_x)
    add_cell(shape, "PinY", pin_y)
    add_cell(shape, "Width", visio_width)
    add_cell(shape, "Height", visio_height)
    add_cell(shape, "LocPinX", visio_width / 2)
    add_cell(shape, "LocPinY", visio_height / 2)
    add_cell(shape, "Angle", "0")
    foreign = ET.SubElement(shape, f"{{{VISIO_NS}}}ForeignData", {"ForeignType": "Bitmap"})
    ET.SubElement(foreign, f"{{{VISIO_NS}}}Rel", {f"{{{REL_NS}}}id": relationship_id})


def add_visio_connector(
    shapes: ET.Element,
    shape_id: int,
    source: Node,
    target: Node,
    edge: Edge,
) -> None:
    x1, y1 = anchor(source, target)
    x2, y2 = anchor(target, source)
    begin_x, begin_y = visio_xy(x1, y1)
    end_x, end_y = visio_xy(x2, y2)
    shape = ET.SubElement(
        shapes,
        f"{{{VISIO_NS}}}Shape",
        {"ID": str(shape_id), "Type": "Shape", "LineStyle": "3", "FillStyle": "3", "TextStyle": "3"},
    )
    add_cell(shape, "PinX", (begin_x + end_x) / 2)
    add_cell(shape, "PinY", (begin_y + end_y) / 2)
    add_cell(shape, "Width", abs(end_x - begin_x))
    add_cell(shape, "Height", abs(end_y - begin_y))
    add_cell(shape, "BeginX", begin_x)
    add_cell(shape, "BeginY", begin_y)
    add_cell(shape, "EndX", end_x)
    add_cell(shape, "EndY", end_y)
    add_cell(shape, "LineColor", edge.color)
    add_cell(shape, "LineWeight", str(0.012 * edge.width))
    add_cell(shape, "EndArrow", "4")
    if edge.dashed:
        add_cell(shape, "LinePattern", "10")
    geometry = ET.SubElement(shape, f"{{{VISIO_NS}}}Section", {"N": "Geometry", "IX": "0"})
    add_cell(geometry, "NoFill", "1")
    row = ET.SubElement(geometry, f"{{{VISIO_NS}}}Row", {"T": "MoveTo", "IX": "1"})
    add_cell(row, "X", "0")
    add_cell(row, "Y", "0")
    row = ET.SubElement(geometry, f"{{{VISIO_NS}}}Row", {"T": "LineTo", "IX": "2"})
    add_cell(row, "X", abs(end_x - begin_x))
    add_cell(row, "Y", abs(end_y - begin_y))
    add_text_format(shape, "#40596f", 0.085)
    ET.SubElement(shape, f"{{{VISIO_NS}}}Text").text = edge.label


def render_vsdx(icons: dict[str, Path], template_bytes: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="storage-intelligence-vsdx-") as temp_name:
        temp = Path(temp_name)
        source = temp / "source.vsdx"
        source.write_bytes(template_bytes)
        package = temp / "package"
        with zipfile.ZipFile(source) as archive:
            archive.extractall(package)

        media = package / "visio" / "media"
        media.mkdir(parents=True, exist_ok=True)
        icon_media: dict[str, str] = {}
        for key, icon_path in icons.items():
            target_name = f"azure-{key}.svg"
            (media / target_name).write_bytes(icon_path.read_bytes())
            icon_media[key] = target_name

        ET.register_namespace("", CONTENT_NS)
        content_path = package / "[Content_Types].xml"
        content_tree = ET.parse(content_path)
        content_root = content_tree.getroot()
        if not any(item.get("Extension") == "svg" for item in content_root):
            ET.SubElement(
                content_root,
                f"{{{CONTENT_NS}}}Default",
                {"Extension": "svg", "ContentType": "image/svg+xml"},
            )
        content_tree.write(content_path, encoding="utf-8", xml_declaration=True)

        ET.register_namespace("", PKG_REL_NS)
        rels_path = package / "visio" / "pages" / "_rels" / "page1.xml.rels"
        rels_tree = ET.parse(rels_path)
        rels_root = rels_tree.getroot()
        relationship_ids: dict[str, str] = {}
        for index, (key, target_name) in enumerate(icon_media.items(), start=100):
            relationship_id = f"rId{index}"
            relationship_ids[key] = relationship_id
            ET.SubElement(
                rels_root,
                f"{{{PKG_REL_NS}}}Relationship",
                {
                    "Id": relationship_id,
                    "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                    "Target": f"../media/{target_name}",
                },
            )
        rels_tree.write(rels_path, encoding="utf-8", xml_declaration=True)

        ET.register_namespace("", VISIO_NS)
        ET.register_namespace("r", REL_NS)
        page_root = ET.Element(f"{{{VISIO_NS}}}PageContents", {"{http://www.w3.org/XML/1998/namespace}space": "preserve"})
        shapes = ET.SubElement(page_root, f"{{{VISIO_NS}}}Shapes")
        shape_id = 1
        add_visio_rectangle(
            shapes,
            shape_id,
            20,
            18,
            1760,
            64,
            "Storage Intelligence - MCP & A2A Azure Architecture\n"
            "Explicit primary and optional agent request paths with separate support controls",
            "#ffffff",
            "#ffffff",
            0.22,
            transparent=True,
        )
        shape_id += 1
        for region in REGIONS:
            add_visio_rectangle(
                shapes,
                shape_id,
                region.x,
                region.y,
                region.width,
                region.height,
                f"{region.title}\n{region.subtitle}",
                region.fill,
                region.stroke,
                0.11,
                region.dashed,
            )
            shape_id += 1

        nodes = node_lookup()
        for edge in EDGES:
            add_visio_connector(shapes, shape_id, nodes[edge.source], nodes[edge.target], edge)
            shape_id += 1

        for node in NODES:
            add_visio_rectangle(
                shapes,
                shape_id,
                node.x,
                node.y,
                node.width,
                node.height,
                f"{node.title}\n{node.detail}",
                node.fill,
                node.stroke,
                0.105,
                icon_gutter=True,
            )
            shape_id += 1
            add_visio_image(shapes, shape_id, node, relationship_ids[node.icon])
            shape_id += 1

        ET.ElementTree(page_root).write(
            package / "visio" / "pages" / "page1.xml",
            encoding="utf-8",
            xml_declaration=True,
        )

        pages_path = package / "visio" / "pages" / "pages.xml"
        pages_tree = ET.parse(pages_path)
        page_sheet = pages_tree.find(f".//{{{VISIO_NS}}}PageSheet")
        if page_sheet is None:
            raise RuntimeError("The Visio template does not contain a PageSheet.")
        for cell in page_sheet.findall(f"{{{VISIO_NS}}}Cell"):
            if cell.get("N") == "PageWidth":
                cell.set("V", str(VISIO_WIDTH))
            elif cell.get("N") == "PageHeight":
                cell.set("V", str(VISIO_HEIGHT))
        pages_tree.write(pages_path, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(VSDX_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(package.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(package).as_posix())


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="azure-architecture-icons-") as temp_name:
        icons = locate_icons(download(ICON_ARCHIVE), Path(temp_name))
        render_svg(icons)
        render_drawio(icons)
        render_vsdx(icons, download(VSDX_TEMPLATE))

    print(f"Generated {SVG_PATH.relative_to(ROOT)}")
    print(f"Generated {DRAWIO_PATH.relative_to(ROOT)}")
    print(f"Generated {VSDX_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
