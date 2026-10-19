"""Generate the profile hero images and bilingual README from data/profile.json."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "profile.json"
ASSETS = ROOT / "assets"

F_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
F_ZH = "C:/Windows/Fonts/msyh.ttc"
F_EN = "C:/Windows/Fonts/segoeui.ttf"

W, H = 1920, 1200
PX, PW, PH = 800, 1120, 1000


def zh_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(F_BOLD if bold else F_ZH, size)


def body_font(lang: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(F_EN if lang == "en" else F_ZH, size)


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CARD_W, CARD_H = 560, 360
CARD_SANS = "'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif"
CARD_MONO = "SFMono-Regular, Consolas, 'Courier New', monospace"


def project_card(project: dict, lang: str, index: int) -> str:
    lines = project.get(f"lines_{lang}") or [project[f"desc_{lang}"]]
    rows = "".join(
        f'<text x="36" y="{172 + i * 38}" font-family="{CARD_SANS}" font-size="26" '
        f'fill="#A39A8C">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    view = "View" if lang == "en" else "查看仓库"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img">
<title>{esc(project["name"])}</title>
<desc>{esc(project[f"desc_{lang}"])}</desc>
<rect width="{CARD_W}" height="{CARD_H}" rx="16" fill="#1A1714" stroke="#2E2921" stroke-width="1"/>
<circle cx="42" cy="42" r="6" fill="{project["accent"]}"/>
<text x="60" y="48" font-family="{CARD_MONO}" font-size="18" fill="#6B665E">0{index}</text>
<text x="36" y="116" font-family="{CARD_MONO}" font-size="34" font-weight="600" fill="#F5F1EA">{esc(project["name"])}</text>
{rows}
<path d="M36 252H524" stroke="#2E2921" stroke-width="1"/>
<text x="36" y="294" font-family="{CARD_MONO}" font-size="17" fill="#6B665E">{esc(project["tags"])}</text>
<text x="524" y="294" text-anchor="end" font-family="{CARD_SANS}" font-size="22" fill="{project["accent"]}">{view} →</text>
</svg>
"""


def build_hero(profile: dict, lang: str) -> Image.Image:
    t = profile["theme"]["dark"]
    canvas = Image.new("RGB", (W, H), t["bg"])

    photo = Image.open(ROOT / profile["hero_photo"]).convert("RGB")
    s = max(PW / photo.width, PH / photo.height)
    photo = photo.resize(
        (int(photo.width * s) + 1, int(photo.height * s) + 1), Image.LANCZOS
    )
    photo = photo.crop((0, 200, PW, 200 + PH))
    photo = Image.eval(photo, lambda v: int(v * 0.86))
    canvas.paste(photo, (PX, 0))

    overlay = Image.new("RGB", (W, PH), t["bg"])
    mask = Image.new("L", (W, PH), 0)
    md = ImageDraw.Draw(mask)
    for x in range(PX, PX + 300):
        md.line([(x, 0), (x, PH)], fill=int(255 * (1 - (x - PX) / 300)))
    canvas.paste(overlay, (0, 0), mask)

    d = ImageDraw.Draw(canvas)
    name_f = zh_font(124, bold=True)
    sub_f = body_font(lang, 40)
    txt_f = body_font(lang, 34)
    tag_f = body_font(lang, 28)

    d.text((96, 340), profile["name"][lang], font=name_f, fill=t["fg"])
    d.text((100, 502), profile["tagline"][lang], font=sub_f, fill=t["sub"])
    d.line([(100, 582), (700, 582)], fill=t["line"], width=2)

    for i, line in enumerate(profile["summary_lines"][lang]):
        d.text((100, 634 + i * 52), line, font=txt_f, fill=t["sub"])

    tx = 100
    for label in profile["tags"][lang]:
        lw = d.textlength(label, font=tag_f)
        bw = int(lw + 48)
        d.rounded_rectangle([tx, 758, tx + bw, 818], radius=11, fill=t["tag_bg"])
        d.text((tx + 24, 770), label, font=tag_f, fill=t["tag_fg"])
        tx += bw + 14

    d.line([(96, 1052), (1824, 1052)], fill=t["line"], width=1)
    step = 1728 // len(profile["stats"])
    num_f = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 58)
    lab_f = body_font(lang, 20)
    sx = 96
    for st in profile["stats"]:
        d.text((sx, 1088), st["num"], font=num_f, fill=t["accent"])
        d.text((sx + 2, 1160), st[lang], font=lab_f, fill=t["muted"])
        sx += step

    return canvas


def build_badges(profile: dict) -> str:
    parts = []
    for item in profile["contact"]:
        label = quote(item["label"])
        src = (
            f"https://img.shields.io/badge/{label}--{item['color']}"
            f"?style=for-the-badge&logo={item['logo']}&logoColor=white"
        )
        parts.append(f'<a href="{item["url"]}"><img src="{src}" alt="{item["label"]}"></a>')
    return "\n  ".join(parts)


def readme_md(profile: dict, lang: str) -> str:
    if lang == "en":
        switch = '<a href="README.zh-CN.md">中文</a> · <b>English</b>'
        labels = {
            "about": "About",
            "doing": "What I'm working on",
            "stack": "Tech stack",
            "connect": "Connect",
            "qr": "WeChat official account — scan to follow",
        }
        hint = (
            '<!-- Add a project: put {"name","url","desc_zh","desc_en"} into the projects '
            "array in data/profile.json, then run scripts/build.py -->"
        )
    else:
        switch = '<b>中文</b> · <a href="README.md">English</a>'
        labels = {
            "about": "关于我",
            "doing": "我在做的事",
            "stack": "技术栈",
            "connect": "联系",
            "qr": "微信公众号 · 扫码关注",
        }
        hint = (
            '<!-- 添加项目：在 data/profile.json 的 projects 数组里填入 '
            '{"name","url","desc_zh","desc_en"}，重新运行 scripts/build.py -->'
        )

    lines = [
        '<p align="center">',
        f'  <img src="assets/hero-{lang}.jpg" alt="{profile["name"][lang]}" width="100%">',
        "</p>",
        "",
        f'<p align="center">{switch}</p>',
        "",
        "---",
        "",
        f"### {labels['about']}",
        "",
        profile["about"][lang],
        "",
        "---",
        "",
        f"### {labels['doing']}",
        "",
    ]

    doing = profile["doing"]
    lines.append("| " + " | ".join(f"0{i}" for i in range(1, len(doing) + 1)) + " |")
    lines.append("|:---|:---|:---|")
    lines.append("| " + " | ".join(f"**{d[lang]}**" for d in doing) + " |")
    lines.append("| " + " | ".join(d[f"desc_{lang}"] for d in doing) + " |")
    lines.append("")

    stack_block = [
        "---",
        "",
        f"### {labels['stack']}",
        "",
        '<p align="center">',
        "  <picture>",
        '    <source media="(prefers-color-scheme: dark)" '
        'srcset="https://skillicons.dev/icons?i=python,pytorch,git,github,vscode&theme=dark">',
        '    <img src="https://skillicons.dev/icons?i=python,pytorch,git,github,vscode&theme=light" '
        'alt="Tech stack icons">',
        "  </picture>",
        "</p>",
        "",
    ]
    for group in profile["stack"]:
        items = " ".join(
            f"`{i if isinstance(i, str) else i.get(lang) or i.get('en')}`"
            for i in group["items"]
        )
        stack_block.append(f"**{group[lang]}** · {items}")
        stack_block.append("")

    project_block = []
    if profile["projects"]:
        projs = profile["projects"]
        project_block += ["---", "", f"### {'Projects' if lang == 'en' else '项目'}", "", "<table>"]
        for i in range(0, len(projs), 3):
            project_block.append("<tr>")
            for p in projs[i : i + 3]:
                desc = p.get(f"desc_{lang}") or p.get("desc_en", "")
                project_block.append('<td width="33%" valign="top">')
                project_block.append(
                    f'<a href="{p["url"]}"><img src="assets/proj-{p["name"]}-{"cn" if lang == "zh" else "en"}.svg" '
                    f'width="100%" alt="{p["name"]} — {desc}"></a>'
                )
                project_block.append("</td>")
            project_block.append("</tr>")
        project_block.append("</table>")
        project_block.append("")
        note = profile.get("projects_note", {}).get(lang)
        if note:
            project_block += [f"<sub>{note}</sub>", ""]

    lines += project_block + stack_block

    lines += [
        "---",
        "",
        f"### {labels['connect']}",
        "",
        '<p align="center">',
        "  " + build_badges(profile),
        "</p>",
        "",
        f'<p align="center"><sub>{labels["qr"]}</sub></p>',
        '<p align="center"><img src="assets/wechat-qrcode.png" width="160" alt="WeChat QR"></p>',
        "",
    ]

    if not profile["projects"]:
        lines += [hint, ""]

    return "\n".join(lines)


def main() -> None:
    profile = json.loads(DATA.read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)

    for lang in ("zh", "en"):
        img = build_hero(profile, lang)
        img.save(ASSETS / f"hero-{lang}.jpg", quality=90, optimize=True, subsampling=1)

    qr = Image.open(ROOT / profile["wechat_qrcode"]).convert("RGB")
    qr.resize((360, 360), Image.LANCZOS).save(ASSETS / "wechat-qrcode.png", optimize=True)

    for lang in ("zh", "en"):
        for i, project in enumerate(profile["projects"], 1):
            (ASSETS / f'proj-{project["name"]}-{"cn" if lang == "zh" else "en"}.svg').write_text(
                project_card(project, lang, i), encoding="utf-8"
            )

    (ROOT / "README.md").write_text(readme_md(profile, "en"), encoding="utf-8")
    (ROOT / "README.zh-CN.md").write_text(readme_md(profile, "zh"), encoding="utf-8")

    print("generated: hero-zh.jpg, hero-en.jpg, wechat-qrcode.png, README.md, README.zh-CN.md")


if __name__ == "__main__":
    main()
