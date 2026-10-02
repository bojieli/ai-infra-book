from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.build_pdf import BuildError, build_preview, prepare_markdown

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("missing_last_chapter", [False, True])
def test_full_cli_requires_all_chapters_and_removes_preview_label(
    tmp_path: Path, missing_last_chapter: bool
) -> None:
    book = tmp_path / "book"
    book.mkdir()
    names = ["preface.md", *(f"chapter{i}.md" for i in range(1, 13))]
    (book / "preface.md").write_text("# Предисловие\n\nВведение.\n")
    for index in range(1, 13):
        if missing_last_chapter and index == 12:
            continue
        (book / f"chapter{index}.md").write_text(
            f"# Глава {index}. Раздел\n\nChapterMarker{index}End.\n"
        )
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "markdown": [
                    {"path": f"book/{name}", "original_path": f"manuscripts/{name}"}
                    for name in names
                ],
            }
        )
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_pdf.py"), "--full", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if missing_last_chapter:
        assert result.returncode == 1
        assert "chapter12.md" in result.stderr
        assert not (tmp_path / ".tmp/pdf-build/AI-Infra-in-Depth-RU.pdf").exists()
        return
    assert result.returncode == 0, result.stderr
    pdf = Path(result.stdout.strip())
    assert pdf.name == "AI-Infra-in-Depth-RU.pdf"
    text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    assert "ознакомительный" not in text.lower() + info.lower()
    for index in range(1, 13):
        assert f"ChapterMarker{index}End" in text
    manifest = json.loads(pdf.with_suffix(".json").read_text())
    assert manifest["chapters"] == names
    assert manifest["scope"] == "full: preface and chapters 1-12"
    assert manifest["pdf_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()


@pytest.mark.parametrize("extra", [["--preview"], ["--through-chapter", "8"]])
def test_full_cli_rejects_ambiguous_or_partial_scope(tmp_path: Path, extra: list[str]) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_pdf.py"),
            "--full",
            *extra,
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert not (tmp_path / ".tmp/pdf-build").exists()


def test_preview_keeps_same_named_footnotes_local_to_each_chapter(tmp_path: Path) -> None:
    book = tmp_path / "book"
    book.mkdir()
    texts = {
        "preface.md": "# Предисловие\n\nВведение.\n",
        "chapter1.md": (
            "# Глава 1. Первая\n\n## 1.1 Раздел\n\n"
            "Первый якорь текста[^shared]. [Вернуться](#раздел).\n\n"
            "Код: `[^shared]`.\n\n[^shared]: AlphaFootnoteUnique.\n"
        ),
        "chapter2.md": (
            "# Глава 2. Вторая\n\n## 2.1 Раздел\n\n"
            "Второй якорь текста[^shared]. [Вернуться](#раздел).\n\n"
            "[^shared]: BetaFootnoteUnique.\n"
        ),
    }
    for name, text in texts.items():
        (book / name).write_text(text, encoding="utf-8")
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "markdown": [
                    {"path": f"book/{name}", "original_path": f"manuscripts/{name}"}
                    for name in texts
                ],
            }
        ),
        encoding="utf-8",
    )
    pdf = build_preview(tmp_path, through_chapter=2)
    pages = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True).split("\f")
    first = next(p for p in pages if "Первый якорь" in p)
    second = next(p for p in pages if "Второй якорь" in p)
    assert "AlphaFootnoteUnique" in first and "BetaFootnoteUnique" not in first
    assert "BetaFootnoteUnique" in second and "AlphaFootnoteUnique" not in second
    assert "[^shared]" in first
    log = (tmp_path / ".tmp/pdf-build/pandoc.log").read_text()
    assert "Duplicate note reference" not in log
    tex = (tmp_path / ".tmp/pdf-build/preview.tex").read_text()
    links = re.findall(r"\\hyperlink\{([^}]+)\}\{Вернуться\}", tex)
    assert len(links) == 2 and links[0] != links[1]
    assert all(f"\\hypertarget{{{link}}}" in tex for link in links)
    assert all((book / name).read_text() == text for name, text in texts.items())


def test_prepare_later_chapter_removes_manual_number(tmp_path: Path) -> None:
    chapter = tmp_path / "chapter2.md"
    chapter.write_text("# Глава 2. Архитектура\n\n## 2.1 Внимание\n", encoding="utf-8")
    prepared, _ = prepare_markdown(
        chapter,
        original_path="manuscripts/02.md",
        repository="https://github.com/example/book",
        commit="abc123",
    )
    assert prepared == "# Архитектура\n\n## Внимание\n"


def test_prepare_preserves_html_section_anchor_in_latex(tmp_path: Path) -> None:
    chapter = tmp_path / "chapter2.md"
    chapter.write_text(
        '# Глава 2. Архитектура\n\n[Таблицы](#model-matrix-tables).\n\n'
        '<a id="model-matrix-tables"></a>\n\n## Справочные таблицы\n',
        encoding="utf-8",
    )
    prepared, _ = prepare_markdown(
        chapter,
        original_path="manuscripts/02.md",
        repository="https://github.com/example/book",
        commit="abc123",
    )
    chapter.write_text(prepared, encoding="utf-8")
    tex = subprocess.check_output(
        ["pandoc", str(chapter), "--file-scope", "--to=latex"], text=True
    )
    target = re.search(r"\\hyperref\[([^\]]+)\]", tex)
    if target is not None:
        assert "model-matrix-tables" in target[1]
        assert f"\\label{{{target[1]}}}" in tex
    else:
        # Pandoc 3.1 emits hyperlink/hypertarget for standalone span anchors.
        target = re.search(r"\\hyperlink\{([^}]+)\}", tex)
        assert target is not None, tex
        assert "model-matrix-tables" in target[1]
        assert f"\\hypertarget{{{target[1]}}}" in tex


def test_preview_can_include_second_chapter(tmp_path: Path) -> None:
    book = tmp_path / "book"
    book.mkdir()
    strategy_svg = book / "strategy.svg"
    strategy_svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400pt" height="180pt">'
        '<rect width="400" height="180" fill="#137f8a"/></svg>',
        encoding="utf-8",
    )
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(book / "strategy.pdf"), str(strategy_svg)],
        check=True,
    )
    for name, text in {
        "preface.md": "# Предисловие\n\nВведение.\n",
        "chapter1.md": "# Глава 1. Начало\n\nПервая глава.\n",
        "chapter2.md": (
            "# Глава 2. Архитектура\n\n## 2.1 Внимание\n\nВторая глава.\n\n"
            "$$\n"
            r"E_{\mathrm{weights}}=15.137\times10^9\times31.76\ \mathrm{pJ}"
            r"\approx0.481\ \mathrm{J},\quad"
            "\n"
            r"E_{\mathrm{KV}}\approx0.038\ \mathrm{J},\quad"
            "\n"
            r"E_{\mathrm{compute}}=19.97\times10^9\times0.75\ \mathrm{pJ}\approx0.015\ \mathrm{J},"
            "\n$$\n\n"
            "$$\n"
            r"C_{effective}=\frac{\text{общая стоимость за период измерения}}"
            r"{\text{число запросов или задач, удовлетворяющих требованиям к качеству и сроку}}."
            "\n$$\n\n$$\n"
            r"\text{Потребность в ресурсе в единицу времени}="
            r"\text{скорость поступления задач}\times"
            r"\text{средняя потребность в ресурсе на задачу}."
            "\n$$\n\n**Упражнение ★★.**\n\n"
            "Разность: 1 и −1. Время: $15\\ \\mathrm{\\mu s}$.\n\n"
            "```python\nif ready:\n    return True\n```\n\n"
            "Перед таблицей стратегий.\n\n"
            "| Стратегия | Однократная подготовка P | Выполнение одной группы T | "
            "Способ обработки форм |\n"
            "| --- | --- | --- | --- |\n"
            "| Универсальная | 100 ms | 17,0 ms | 5632 строки |\n\n"
            "Результат сравнения стратегий изображён ниже.\n\n"
            "![График стратегий](strategy.svg)\n\n"
            "*Рисунок 2-S. Сравнение стратегий [128,12288], 1≈1.*\n\n"
            "Перед таблицей измеренных задержек.\n\n"
            "| Фактическое наблюдение | Равномерная смесь | Сначала 9:1, затем 1:9 |\n"
            "| --- | --- | --- |\n"
            "| p95 TTFT | 242.9 s | 258.9 s |\n\n"
            "**Таблица 2-A. Сравнение архитектур**\n\n"
            "| Параметр архитектуры | DeepSeek V4.1 Flash | Qwen3-8B | Qwen3.6-35B-A3B | "
            "DeepSeek V4-Flash | Kimi K3 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| Вычислительная ширина маршрутизируемого эксперта | "
            "5120 | 4096 | 2048 | 4096 | 3584 |\n\n"
            "| Модель | Эмбеддинги и выходная голова | Проекции внимания | Плотные / общие FFN | "
            "Маршрутизируемые эксперты | Engram | Прочее |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| DeepSeek V4.1 Flash | 1.324 | 5.126 | 1.416 | 543.582 | 196.929 | 0.118 |\n\n"
            "| Модуль и назначение | Вход → выход (число строк × ширина) | "
            "Матрица весов (ширина входа × ширина выхода) | Матричные FLOPs | "
            "Число слоёв/вызовов |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Маршрутизируемый эксперт | $m\\times4096\\to m\\times12288$ | $4096\\times12288$ | "
            "$6\\times m\\times4096\\times12288$ | 40 |\n\n"
            "| Модуль и назначение | Вход → выход | Матрица весов | "
            "Матричные FLOPs | Число слоёв/вызовов |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| AttnRes | Представления | Параметры | По числу блоков | "
            "Суммируется по числу блоков, участвующих в смешивании |\n\n"
            "```{=latex}\n\\clearpage\n\\setcounter{page}{110}\n```\n\n## 2.2 Конец\n"
        ),
    }.items():
        (book / name).write_text(text, encoding="utf-8")
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "markdown": [
                    {"path": "book/preface.md", "original_path": "manuscripts/00.md"},
                    {"path": "book/chapter1.md", "original_path": "manuscripts/01.md"},
                    {"path": "book/chapter2.md", "original_path": "manuscripts/02.md"},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_pdf.py"),
            "--preview",
            "--through-chapter",
            "2",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    pdf = Path(result.stdout.strip())
    text = " ".join(subprocess.check_output(["pdftotext", str(pdf), "-"], text=True).split())
    assert "Предисловие и главы 1–2" in text
    assert "Вторая глава." in text
    for value in ("0.481", "0.038", "0.015"):
        assert value in text
    assert "Глава 2. Архитектура" not in text
    data = json.loads(pdf.with_suffix(".json").read_text())
    assert data["chapters"] == ["preface.md", "chapter1.md", "chapter2.md"]
    assert "book/chapter2.md" in data["inputs"]
    assert "book/strategy.pdf" in data["inputs"]
    tex = (tmp_path / ".tmp/pdf-build/preview.tex").read_text()
    assert "\\includesvg" not in tex
    assert "\\includegraphics" in tex
    assert "[128,12288]" in text
    assert "★★" in text and "≈" in text
    for phrase in (
        "общая стоимость за период измерения",
        "число запросов или задач,",
        "удовлетворяющих требованиям к качеству и сроку",
        "Потребность в ресурсе в единицу времени",
        "скорость поступления задач",
        "средняя потребность в ресурсе на задачу",
    ):
        assert phrase in text
    assert r"\begin{gathered}" in tex
    assert "DejaVuSansMono-Bold" in data["embedded_font_names"]
    bold_font = data["fonts"]["mono_bold"]
    assert bold_font["sha256"] == hashlib.sha256(Path(bold_font["path"]).read_bytes()).hexdigest()
    pages = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True).split("\f")
    assert any("Таблица 2-A" in page and "5120" in page for page in pages)
    before = next(i for i, page in enumerate(pages) if "Перед таблицей измеренных" in page)
    measured = next(i for i, page in enumerate(pages) if "Фактическое наблюдение" in page)
    assert measured > before
    strategy_before = next(i for i, page in enumerate(pages) if "Перед таблицей стратегий" in page)
    strategy_table = next(i for i, page in enumerate(pages) if "Однократная подготовка" in page)
    assert strategy_table > strategy_before
    assert text.index("Однократная подготовка") < text.index("Рисунок 2-S.")
    assert text.index("Результат сравнения") < text.index("Рисунок 2-S.")
    assert "−1" in text
    assert "𝜇" in text


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    workspace_tmp = ROOT / ".tmp"
    workspace_tmp.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="test-pdf-", dir=workspace_tmp) as directory:
        yield Path(directory)


@pytest.mark.parametrize("pdf_bytes", [b"%PDF-1.4\nfixture", b"invalid", None])
def test_caption_brackets_do_not_bypass_vector_asset_validation(
    tmp_path: Path, pdf_bytes: bytes | None
) -> None:
    chapter = tmp_path / "chapter10.md"
    caption = (
        r"Рисунок 10-12. [128,12288], $\frac{1}{2}\times x\approx y$, "
        r"**форма** `h` и [источник](https://example.com)."
    )
    original = f"# Глава 10. Пример\n\n![Схема](chart.svg)\n\n*{caption}*\n"
    chapter.write_text(original, encoding="utf-8")
    pdf = tmp_path / "chart.pdf"
    if pdf_bytes is not None:
        pdf.write_bytes(pdf_bytes)
    kwargs = {
        "original_path": "manuscripts/10.md",
        "repository": "https://github.com/example/book",
        "commit": "abc123",
    }
    if pdf_bytes != b"%PDF-1.4\nfixture":
        with pytest.raises(BuildError, match="Нет готового векторного PDF"):
            prepare_markdown(chapter, **kwargs)
    else:
        prepared, assets = prepare_markdown(chapter, **kwargs)
        assert f"![{caption}]({pdf.as_posix()})" in prepared
        assert assets == [pdf]
        assert "chart.svg" not in prepared
    assert chapter.read_text(encoding="utf-8") == original


def test_prepare_uses_vector_figure_and_upstream_links(tmp_path: Path) -> None:
    book = tmp_path / "book"
    figures = book / "ch01"
    figures.mkdir(parents=True)
    (figures / "diagram.svg").write_text("<svg/>", encoding="utf-8")
    (figures / "diagram.pdf").write_bytes(b"%PDF-1.4\nfixture")
    original = (
        "# Глава 1. Пример\n\n"
        "## 1.1 Анализ\n\n"
        "![Кратко](ch01/diagram.svg)\n\n"
        "*Рисунок 1-1. Полная подпись.*\n\n"
        "См. [источник](../references/specs/a.pdf) и [рисунок](#figure-1).\n"
    )
    chapter = book / "chapter1.md"
    chapter.write_text(original, encoding="utf-8")
    prepared, assets = prepare_markdown(
        chapter,
        original_path="manuscripts/01-Исходник.md",
        repository="https://github.com/example/book",
        commit="abc123",
    )

    assert chapter.read_text(encoding="utf-8") == original
    assert "# Пример" in prepared
    assert "## Анализ" in prepared
    assert "Рисунок 1-1. Полная подпись." in prepared
    assert "*Рисунок 1-1" not in prepared
    assert str(figures / "diagram.pdf") in prepared
    assert assets == [figures / "diagram.pdf"]
    assert "https://github.com/example/book/blob/abc123/references/specs/a.pdf" in prepared
    assert "[рисунок](#figure-1)" in prepared


@pytest.mark.parametrize("formula", [r"989.4/312\approx3.17", r"6\times N", r"\frac{1}{2}"])
def test_prepare_preserves_math_commands_in_figure_caption(tmp_path: Path, formula: str) -> None:
    chapter = tmp_path / "chapter3.md"
    (tmp_path / "chart.pdf").write_bytes(b"%PDF-1.4\nfixture")
    caption = f"Рис. 3-31. Формула ${formula}$."
    original = f"# Глава 3. Нагрузка\n\n![График](chart.svg)\n\n*{caption}*\n"
    chapter.write_text(original, encoding="utf-8")
    prepared, _ = prepare_markdown(
        chapter,
        original_path="manuscripts/03.md",
        repository="https://github.com/example/book",
        commit="abc123",
    )
    assert f"![{caption}]" in prepared
    assert chapter.read_text(encoding="utf-8") == original


def test_prepare_requires_real_vector_pdf(tmp_path: Path) -> None:
    chapter = tmp_path / "chapter1.md"
    (tmp_path / "chart.svg").write_text("<svg/>", encoding="utf-8")
    chapter.write_text("# Глава 1. Пример\n\n![График](chart.svg)\n", encoding="utf-8")

    with pytest.raises(BuildError, match="chart.pdf"):
        prepare_markdown(
            chapter,
            original_path="manuscripts/01.md",
            repository="https://github.com/example/book",
            commit="abc123",
        )


def test_preview_build_has_provenance_and_frontmatter(tmp_path: Path) -> None:
    book = tmp_path / "book"
    book.mkdir()
    figures = book / "ch01"
    figures.mkdir()
    svg = figures / "diagram.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
        '<rect width="400" height="200" fill="#137f8a"/></svg>',
        encoding="utf-8",
    )
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(figures / "diagram.pdf"), str(svg)],
        check=True,
    )
    (book / "preface.md").write_text("# Предисловие\n\nПробное предисловие.\n", encoding="utf-8")
    (book / "chapter1.md").write_text(
        "# Глава 1. Проверка\n\n## 1.1 Раздел\n\nПроверочный текст: 2 ≤ 3, 2 × 3 → 6; ③.\n\n"
        "BodyProbeAlpha проверка кириллицы ё.  \nBodyProbeBeta вторая строка.\n\n"
        "*Курсивная проверка τ* и ***полужирная курсивная проверка***. γ и σ.\n\n"
        "**Пример: почему при использовании одного и того же инструмента "
        "AI-программирования разные команды получают разное общее ускорение?** "
        "Предположим, что выполнение задачи разработки состоит из последовательных "
        "этапов коммуникации, написания кода, проверки и согласования.\n\n"
        "![Схема](ch01/diagram.svg)\n\n"
        "*Рисунок 1-1. Схема проверки с длинной русской подписью, которая должна "
        "целиком поместиться под векторным рисунком и не оказаться за пределами "
        "страницы: ①, ②.*\n\n"
        "| Операция | Значение |\n| --- | --- |\n| Проверка таблицы | 42 |\n",
        encoding="utf-8",
    )
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "pilot_sources": [
                    {"target_path": "book/preface.md", "original_path": "manuscripts/00.md"},
                    {"target_path": "book/chapter1.md", "original_path": "manuscripts/01.md"},
                ],
            }
        ),
        encoding="utf-8",
    )
    verification = tmp_path / "verification/assets"
    verification.mkdir(parents=True)
    (verification / "layout-main.json").write_text('{"pilot": true}\n', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_pdf.py"), "--preview", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    pdf = tmp_path / ".tmp/pdf-build/AI-Infra-in-Depth-RU-preview.pdf"
    manifest = tmp_path / ".tmp/pdf-build/AI-Infra-in-Depth-RU-preview.json"
    assert pdf.read_bytes().startswith(b"%PDF-")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["scope"] == "preview: preface and chapter 1 only"
    assert data["upstream_commit"] == "abc123"
    assert "scripts/build_pdf.py" in data["inputs"]
    assert "book/preamble.tex" in data["inputs"]
    assert "book/cover.tex" in data["inputs"]
    assert data["figure_count"] == 1
    assert "book/ch01/diagram.pdf" in data["inputs"]
    assert data["pdf_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert (
        data["inputs"]["book/ch01/diagram.pdf"]
        == hashlib.sha256((figures / "diagram.pdf").read_bytes()).hexdigest()
    )
    assert "verification/assets/layout-main.json" in data["inputs"]
    assert data["toolchain"]["pandoc_version"].startswith("pandoc ")
    assert "XeTeX" in data["toolchain"]["xelatex_version"]
    assert len(data["toolchain"]["pandoc_latex_template_sha256"]) == 64
    for role in (
        "main",
        "main_bold",
        "main_italic",
        "main_bold_italic",
        "sans",
        "sans_bold",
        "mono",
        "symbols",
        "math",
    ):
        font = data["fonts"][role]
        assert Path(font["path"]).is_file()
        assert font["sha256"] == hashlib.sha256(Path(font["path"]).read_bytes()).hexdigest()
    for name in ("PTSerif-Regular", "PTSerif-Bold", "PTSerif-Italic", "PTSerif-BoldItalic"):
        assert name in data["embedded_font_names"]
    structured = ET.fromstring(
        subprocess.check_output(
            ["mutool", "draw", "-q", "-F", "stext", "-o", "-", str(pdf)],
            stderr=subprocess.DEVNULL,
        )
    )
    probe_lines = [
        line
        for line in structured.iter("line")
        if "BodyProbe" in "".join(char.attrib["c"] for char in line.iter("char"))
    ]
    assert len(probe_lines) == 2
    for line in probe_lines:
        font = next(line.iter("font"))
        assert "PTSerif-Regular" in font.attrib["name"]
        assert abs(float(font.attrib["size"]) - 11 * 72 / 72.27) < 0.02
    baselines = [float(next(line.iter("char")).attrib["y"]) for line in probe_lines]
    assert abs(baselines[1] - baselines[0] - 15 * 72 / 72.27) < 0.03
    assert "LatinModernMath-Regular-Identity-H" in data["embedded_font_names"]
    assert any(path.endswith(".sty") for path in data["tex_external_inputs"])
    assert not any("/.tmp/" in path for path in data["tex_external_inputs"])
    text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    assert "AI-инфраструктура изнутри: количественный анализ и проектирование систем" in " ".join(
        text.split()
    )
    assert "Только предисловие и глава 1" in text
    assert "Предисловие" in text
    assert text.count("Предисловие") == 2
    assert "Проверка" in text
    assert "Схема проверки" in text
    for glyph in ("≤", "×", "→", "①", "②", "③"):
        assert glyph in text
    for glyph in ("γ", "σ", "τ"):
        assert glyph in unicodedata.normalize("NFKC", text)
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    page_count = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
    assert page_count is not None
    assert int(page_count.group(1)) <= 6
    latex_log = (tmp_path / ".tmp/pdf-build/preview.log").read_text(encoding="utf-8")
    assert "Overfull \\hbox" not in latex_log
    if shutil.which("mutool"):
        trace = subprocess.check_output(
            ["mutool", "draw", "-F", "trace", "-o", "-", str(pdf)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        document = ET.fromstring(trace)
        expected_color = (19 / 255, 127 / 255, 138 / 255)
        vector_fills = [
            fill
            for fill in document.iter("fill_path")
            if len(fill.attrib.get("color", "").split()) == 3
            and all(
                abs(actual - expected) < 0.001
                for actual, expected in zip(
                    map(float, fill.attrib["color"].split()), expected_color, strict=True
                )
            )
        ]
        assert len(vector_fills) == 1
        fill = vector_fills[0]
        scale_x, _, _, scale_y, offset_x, offset_y = map(float, fill.attrib["transform"].split())
        assert 70 < offset_x < 100
        assert offset_x + 300 * scale_x < 525
        assert 250 < offset_y < 600
        assert offset_y + 150 * scale_y < 770
    (book / "chapter1.md").write_text(
        "# Глава 1. Проверка\n\n![нет рисунка](ch01/missing.svg)\n", encoding="utf-8"
    )
    with pytest.raises(BuildError, match="missing.pdf"):
        build_preview(tmp_path)
    assert not pdf.exists()
    assert not manifest.exists()


def test_preview_rejects_overfull_layout_before_publishing(tmp_path: Path) -> None:
    book = tmp_path / "book"
    book.mkdir()
    (book / "preface.md").write_text("# Предисловие\n\nКороткий текст.\n", encoding="utf-8")
    (book / "chapter1.md").write_text(
        "# Глава 1. Проверка\n\n$$\n\\mathrm{" + "W" * 300 + "}\n$$\n",
        encoding="utf-8",
    )
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "pilot_sources": [
                    {"target_path": "book/preface.md", "original_path": "manuscripts/00.md"},
                    {"target_path": "book/chapter1.md", "original_path": "manuscripts/01.md"},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BuildError, match="Overfull"):
        build_preview(tmp_path)
    assert not (tmp_path / ".tmp/pdf-build/AI-Infra-in-Depth-RU-preview.pdf").exists()
    assert not (tmp_path / ".tmp/pdf-build/AI-Infra-in-Depth-RU-preview.json").exists()


def test_rom_table_starts_new_page_without_hiding_following_engram_text(tmp_path: Path) -> None:
    book = tmp_path / "book"
    figures = book / "ch06"
    figures.mkdir(parents=True)
    for name in (
        "figure-6-supernode-inference",
        "figure-6-weight-placement",
        "figure-6-rom-token-time",
        "figure-6-engram-placement",
    ):
        shutil.copyfile(ROOT / "book/ch06" / f"{name}.pdf", figures / f"{name}.pdf")

    chapter = (ROOT / "book/chapter6.md").read_text(encoding="utf-8")
    start = chapter.index("**Размер суперузла и число сеансов на карту.**")
    end = chapter.index("Для пластины ROM компромисс меняется.", start)
    (book / "preface.md").write_text("# Предисловие\n\nПроверка.\n", encoding="utf-8")
    (book / "chapter1.md").write_text(
        "# Глава 1. Проверка таблиц\n\n" + chapter[start:end], encoding="utf-8"
    )
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "pilot_sources": [
                    {"target_path": "book/preface.md", "original_path": "manuscripts/00.md"},
                    {"target_path": "book/chapter1.md", "original_path": "manuscripts/01.md"},
                ],
            }
        ),
        encoding="utf-8",
    )

    pdf = build_preview(tmp_path)
    pages = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True).split("\f")
    formula_page = next(i for i, page in enumerate(pages) if "Коэффициент 0,9" in page)
    rom_table_page = next(i for i, page in enumerate(pages) if "Хранение и вы-" in page)
    assert rom_table_page > formula_page
    text = " ".join(" ".join(pages).split())
    assert text.index("После переноса весов") < text.index("Рисунок 6-55.")
    assert "58 карт B200" in text
    assert "Размещение" in text and "Занимаемая ёмкость" in text
    assert "Масочная ROM" in text and "21 651" in text
    assert "На H100 обе траектории получения данных" in text


def test_native_fullwidth_slash_font_has_file_provenance(tmp_path: Path) -> None:
    book = tmp_path / "book"
    figures = book / "ch01"
    figures.mkdir(parents=True)
    svg = figures / "parallel-map.svg"
    shutil.copyfile(ROOT / "book/ch06/figure-6-parallel-map.svg", svg)
    assert "SP／CP" in svg.read_text(encoding="utf-8")
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(figures / "parallel-map.pdf"), str(svg)],
        check=True,
    )
    (book / "preface.md").write_text("# Предисловие\n\nПроверка.\n", encoding="utf-8")
    (book / "chapter1.md").write_text(
        "# Глава 1. Проверка шрифтов\n\n![Параллелизм](ch01/parallel-map.svg)\n\n"
        "*Рисунок 1-1. Подпись к схеме.*\n",
        encoding="utf-8",
    )
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/book",
                "commit": "abc123",
                "pilot_sources": [
                    {"target_path": "book/preface.md", "original_path": "manuscripts/00.md"},
                    {"target_path": "book/chapter1.md", "original_path": "manuscripts/01.md"},
                ],
            }
        ),
        encoding="utf-8",
    )

    pdf = build_preview(tmp_path)
    manifest = json.loads(pdf.with_suffix(".json").read_text(encoding="utf-8"))
    assert "DroidSansFallback" in manifest["embedded_font_names"]
    punctuation = manifest["fonts"]["diagram_punctuation"]
    assert punctuation["pdf_name"] == "DroidSansFallback"
    assert Path(punctuation["path"]).is_file()
    assert (
        punctuation["sha256"] == hashlib.sha256(Path(punctuation["path"]).read_bytes()).hexdigest()
    )
