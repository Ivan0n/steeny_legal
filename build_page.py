"""Build the standalone legal page from the Markdown source documents.

Run: python legal/build_page.py
Upload legal/index.html and both PDF files to a static host.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
DOCUMENTS = (
    ("agreement", "Пользовательское соглашение", ROOT / "user-agreement-site.md"),
    ("privacy", "Политика конфиденциальности", ROOT / "privacy-policy-site.md"),
)
LOCAL_LINKS = {
    "user-agreement-site.md": "#agreement",
    "privacy-policy-site.md": "#privacy",
}


def inline_html(value: str) -> str:
    parts: list[str] = []
    last = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", value):
        parts.append(escape(value[last : match.start()]))
        target = LOCAL_LINKS.get(match.group(2), match.group(2))
        parts.append(
            f'<a href="{escape(target, quote=True)}">{escape(match.group(1))}</a>'
        )
        last = match.end()
    parts.append(escape(value[last:]))
    return "".join(parts)


def render_document(key: str, title: str, path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    sections: list[tuple[str, str]] = []
    content: list[str] = []
    in_section = False
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                content.append("</ul>")
                in_list = False
            continue
        if line.startswith("# ") or line.startswith("**Редакция "):
            continue
        if line.startswith("## "):
            if in_list:
                content.append("</ul>")
                in_list = False
            if in_section:
                content.append("</section>")
            heading = re.fullmatch(r"(\d+)\. (.+)", line[3:])
            if heading is None:
                raise ValueError(f"Unexpected heading in {path.name}: {line}")
            number, label = heading.groups()
            section_id = f"{key}-{number}"
            sections.append((section_id, f"{number}. {label}"))
            content.append(
                f'<section class="legal-section" id="{section_id}">'
                f'<h3>{escape(number)}. {escape(label)}</h3>'
            )
            in_section = True
            continue
        if line.startswith("- "):
            if not in_list:
                content.append("<ul>")
                in_list = True
            content.append(f"<li>{inline_html(line[2:])}</li>")
            continue
        if in_list:
            content.append("</ul>")
            in_list = False
        clause = re.fullmatch(r"(\d+\.\d+\.)\s+(.+)", line)
        if clause:
            content.append(
                f'<p><span class="clause-number">{escape(clause.group(1))}</span> '
                f'{inline_html(clause.group(2))}</p>'
            )
        else:
            content.append(f"<p>{inline_html(line)}</p>")

    if in_list:
        content.append("</ul>")
    if in_section:
        content.append("</section>")

    contents = "\n".join(
        f'<li><a href="#{section_id}">{escape(label)}</a></li>'
        for section_id, label in sections
    )
    return (
        f'<article class="document" id="{key}" aria-labelledby="{key}-title">\n'
        f'  <h2 id="{key}-title">{escape(title)}</h2>\n'
        '  <div class="document-tools">\n'
        '    <p class="update-date">Последнее обновление: 30 сентября 2026 г.</p>\n'
        f'    <a class="pdf-link" href="{path.stem}.pdf" target="_blank" rel="noopener" '
        f'aria-label="Открыть как PDF: {escape(title)} (в новой вкладке)">Открыть как PDF</a>\n'
        '  </div>\n'
        f'  <nav class="contents" aria-label="Разделы: {escape(title)}">\n'
        f'    <ol>\n{contents}\n    </ol>\n'
        '  </nav>\n'
        + "\n".join(content)
        + "\n</article>"
    )


documents = "\n".join(render_document(*item) for item in DOCUMENTS)

page = r'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="description" content="Пользовательское соглашение и политика конфиденциальности сайта Steeny.">
  <title>Правовые документы — Steeny</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;600;700&family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: light;
      --black: #111;
      --text: #181818;
      --muted: #555;
      --line: #d9d9d9;
      --paper: #fff;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-width: 320px;
      background: var(--paper);
      color: var(--text);
      font: 16px/1.55 'Nunito', sans-serif;
    }
    a { color: var(--black); text-decoration: underline; text-underline-offset: 2px; }
    a:hover { text-decoration-thickness: 2px; }
    a:focus-visible { outline: 2px solid var(--black); outline-offset: 3px; }
    .skip-link {
      position: fixed; top: -60px; left: 16px; z-index: 10;
      padding: 9px 13px; color: var(--paper); background: var(--black);
    }
    .skip-link:focus { top: 10px; }
    .container { width: min(1140px, calc(100% - 48px)); margin: 0 auto; }
    .site-header { background: #111; color: #fff; }
    .site-header .container {
      min-height: 104px; display: flex; justify-content: space-between;
      align-items: center; gap: 28px;
    }
    .brand-block { display: flex; align-items: center; gap: 25px; }
    .brand { color: #fff; text-decoration: none; font: 700 30px 'Comfortaa', sans-serif; letter-spacing: -.8px; }
    .brand:hover { color: #fff; }
    .brand-caption { color: #b5b5b5; font-size: 13px; line-height: 1.4; border-left: 1px solid #414141; padding-left: 25px; }
    .site-header a:focus-visible, .site-footer a:focus-visible { outline-color: #fff; }
    .legal-nav { background: #fff; border-bottom: 1px solid var(--line); }
    .legal-nav .container { display: flex; align-items: center; flex-wrap: wrap; column-gap: 28px; row-gap: 8px; padding-top: 15px; padding-bottom: 15px; }
    .legal-nav-label { color: var(--muted); font-size: 12px; font-weight: 800; letter-spacing: .07em; text-transform: uppercase; margin-right: 25px; }
    .legal-nav a { color: var(--black); text-decoration: none; padding: 9px 0; font-size: 14px; font-weight: 700; }
    .legal-nav a:hover, .legal-nav a[aria-current="page"] { text-decoration: underline; text-underline-offset: 5px; }
    main { padding-top: 52px; padding-bottom: 96px; }
    .document { scroll-margin-top: 25px; }
    .document + .document { border-top: 1px solid var(--line); margin-top: 88px; padding-top: 76px; }
    .document h2 {
      margin: 0 0 8px; color: var(--black);
      font-size: clamp(33px, 4vw, 43px); line-height: 1.14;
      font-family: 'Comfortaa', sans-serif; letter-spacing: -.035em; font-weight: 700;
      hyphens: auto; overflow-wrap: anywhere;
    }
    .document-tools { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px 24px; margin-bottom: 24px; }
    .update-date { margin: 0; color: var(--muted); }
    .pdf-link { display: inline-flex; align-items: center; min-height: 40px; padding: 8px 15px; border: 1px solid #bcbcbc; border-radius: 6px; background: #fff; color: #111; font-size: 14px; font-weight: 700; text-decoration: none; }
    .pdf-link:hover { border-color: #111; text-decoration: underline; }
    .contents { margin: 0 0 31px; }
    .contents ol { list-style: none; margin: 0; padding: 0; }
    .contents li { margin: 0 0 13px; }
    .contents a { text-decoration: none; }
    .contents a:hover { text-decoration: underline; }
    .legal-section { scroll-margin-top: 25px; }
    .legal-section h3 {
      margin: 28px 0 12px; color: var(--black);
      font-size: clamp(23px, 2.5vw, 29px); line-height: 1.2;
      font-family: 'Comfortaa', sans-serif; letter-spacing: -.02em; font-weight: 700;
    }
    .legal-section p { margin: 0 0 16px; }
    .legal-section ul { margin: 0 0 18px; padding-left: 26px; }
    .legal-section li { margin-bottom: 8px; }
    .clause-number { font-weight: 700; }
    .site-footer { background: #111; color: #fff; padding: 62px 0 25px; }
    .footer-grid { display: grid; grid-template-columns: 1.2fr 1fr 1.1fr; gap: 42px; padding-bottom: 52px; }
    .footer-brand { display: inline-block; color: #fff; text-decoration: none; font: 700 34px 'Comfortaa', sans-serif; letter-spacing: -1px; }
    .footer-description { color: #aaa; margin: 15px 0 0; max-width: 230px; font-size: 14px; }
    .footer-label { margin: 0 0 18px; color: #aaa; font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    .footer-links { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; }
    .footer-links a { color: #eee; text-decoration: none; font-size: 14px; }
    .footer-links a:hover { text-decoration: underline; }
    .footer-app-links { margin-top: 18px; }
    .footer-email { color: #fff; font-size: clamp(18px, 2vw, 23px); font-weight: 700; text-decoration-thickness: 1px; text-underline-offset: 6px; }
    .footer-support-note { color: #aaa; font-size: 13px; margin: 15px 0 0; }
    .footer-bottom { border-top: 1px solid #363636; padding-top: 23px; display: flex; align-items: center; justify-content: space-between; gap: 20px; font-size: 13px; }
    .footer-bottom a { color: #b5b5b5; text-decoration: none; }
    .footer-bottom a:hover { color: #fff; text-decoration: underline; }
    @media (max-width: 900px) {
      .brand-caption { display: none; }
      .legal-nav-label { flex-basis: 100%; margin: 0 0 3px; }
      .footer-grid { grid-template-columns: 1fr 1fr; gap: 35px; }
      .footer-intro { grid-column: 1 / -1; }
      .footer-description { max-width: none; }
    }
    @media (max-width: 650px) {
      .container { width: min(100% - 32px, 1140px); }
      .site-header .container { min-height: 86px; gap: 18px; }
      .brand { font-size: 25px; }
      .legal-nav .container { gap: 6px; padding-top: 16px; padding-bottom: 16px; }
      .legal-nav a { font-size: 13px; padding: 8px 0; }
      main { padding-top: 36px; padding-bottom: 62px; }
      .document h2 { font-size: clamp(24px, 7.5vw, 29px); }
      .document + .document { margin-top: 62px; padding-top: 53px; }
      .site-footer { padding-top: 44px; }
      .footer-grid { grid-template-columns: 1fr; gap: 31px; padding-bottom: 37px; }
      .footer-intro { grid-column: auto; }
      .footer-brand { font-size: 30px; }
      .footer-label { margin-bottom: 12px; }
      .footer-support-note { margin-top: 12px; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
    @media print {
      .site-header, .legal-nav, .site-footer, .skip-link, .pdf-link { display: none; }
      .container { width: 100%; }
      main { padding: 0; }
      .document + .document { break-before: page; border: 0; margin: 0; padding: 0; }
      .legal-section { break-inside: avoid-page; }
    }
  </style>
</head>
<body>
  <a class="skip-link" href="#documents">Перейти к документам</a>
  <header class="site-header" id="top">
    <div class="container">
      <div class="brand-block">
        <a class="brand" href="https://steeny.xyz" aria-label="Steeny — на главную">Steeny</a>
        <span class="brand-caption">Правовая информация<br>и поддержка</span>
      </div>
    </div>
  </header>
  <nav class="legal-nav" aria-label="Правовые документы">
    <div class="container">
      <span class="legal-nav-label">Юридическая информация</span>
      <a href="#agreement">Пользовательское соглашение</a>
      <a href="#privacy">Политика конфиденциальности</a>
    </div>
  </nav>
  <main class="container" id="documents">
    {{DOCUMENTS}}
  </main>
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-intro">
          <a class="footer-brand" href="https://steeny.xyz">Steeny</a>
          <p class="footer-description">Условия использования сервиса и информация о ваших данных.</p>
          <nav class="footer-links footer-app-links" aria-label="Сервис и приложение">
            <a href="https://music.steeny.xyz">music.steeny.xyz</a>
            <a href="https://github.com/Ivan0n/SteenyClient/releases">Скачать приложение</a>
          </nav>
        </div>
        <nav aria-label="Документы в подвале">
          <p class="footer-label">Документы</p>
          <div class="footer-links">
            <a href="#agreement">Пользовательское соглашение</a>
            <a href="#privacy">Политика конфиденциальности</a>
          </div>
        </nav>
        <div>
          <p class="footer-label">Поддержка</p>
          <a class="footer-email" href="mailto:support@steeny.xyz">support@steeny.xyz</a>
          <p class="footer-support-note">По вопросам сервиса и правовых документов.</p>
        </div>
      </div>
      <div class="footer-bottom">
        <a href="https://steeny.xyz">steeny.xyz</a>
        <a href="#top">Вернуться наверх ↑</a>
      </div>
    </div>
  </footer>
  <script>
    (() => {
      const links = [...document.querySelectorAll('.legal-nav a[href^="#"]')];
      const update = () => {
        const active = location.hash.startsWith('#privacy') ? '#privacy' : '#agreement';
        for (const link of links) {
          if (link.getAttribute('href') === active) link.setAttribute('aria-current', 'page');
          else link.removeAttribute('aria-current');
        }
      };
      addEventListener('hashchange', update);
      update();
    })();
  </script>
</body>
</html>
'''

(ROOT / "index.html").write_text(
    page.replace("{{DOCUMENTS}}", documents), encoding="utf-8"
)
print(f"Built {ROOT / 'index.html'}")
