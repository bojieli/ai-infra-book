"""Idempotently merge reviewed primary deliveries without modifying raw bytes."""
from pathlib import Path
import copy
import csv
import json
from verify_asplos_parallel_identity import verify

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "references/proceedings/ASPLOS/2025"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    identities = {r["program_order"]: r for r in verify()["records"]}
    manifest = json.loads((D / "manifest.json").read_text())
    papers = {p["program_order"]: p for p in manifest["papers"]}
    abstracts = json.loads((D / "public-abstracts.json").read_text())
    records = {r["program_order"]: r for r in abstracts["records"]}
    sources = {s["id"]: s for s in json.loads((D / "selected-sources.json").read_text())}
    screen_path = ROOT / "research/2026-infra-survey/screening-asplos-2025.tsv"
    with screen_path.open() as f:
        screens = {int(r["number"]): r for r in csv.DictReader(f, delimiter="\t")}
    errors = []
    for batch in ("077-090", "091-110"):
        path = D / "pending-077-110" / batch / "bundle.json"
        bundle = json.loads(path.read_text())
        local_sources = {s["id"]: copy.deepcopy(s) for s in bundle["sources"]}
        for original in bundle["records"]:
            record = copy.deepcopy(original)
            n = record["program_order"]
            paper = papers[n]
            if n not in (78, 80) and paper.get("reading_status") == "selected_sections_read":
                raise RuntimeError(f"Paper {n} has later body-reading work; update this historical merge before rerunning it")
            record["source_title"] = record["title"]
            record["title"] = paper["title"]
            record["parallel_bundle"] = str(path.relative_to(ROOT))
            record["qualified_identity"] = identities[n]
            decision = {"不采用": "排除", "背景备查": "备查"}.get(record["screening"]["decision"], record["screening"]["decision"])
            reason = record["screening"]["rationale"]
            paper["reading_status"] = "abstract_screened"
            if n in (78, 80):
                decision = "重点阅读并整合"
                if n == 78:
                    proof = json.loads((ROOT / "references/framework-history/2026-09-09/neusight-calibration/neusight-reading.json").read_text())
                    paper["selected_reading"] = proof["reading"]
                    reason = "NeuSight 的已声明正文与固定源码范围用于 13.5.1 的阶段预测校准；精度、tile 数据、库版本和执行图边界保留，不新增核心实验。"
                else:
                    folder = ROOT / "references/framework-history/2026-09-09/partir-shardy"
                    proof = json.loads((folder / "reading.json").read_text())
                    paper["selected_reading"] = {
                        "date": "2026-09-09", "scope": "Only physical pages3–5; viewed3/5. Evaluation, proof appendices and remaining saved pages unread. Fixed source scopes in linked proof.",
                        "individual_pdf": original["representative_pdf"]["file"],
                        "physical_pdf_pages": [3, 4, 5],
                        "page_text_sha256": {str(p["physical_page"]): p["sha256"] for p in proof["pages"]},
                        "extraction": "pdftotext -layout; trailing formfeed removed",
                        "proof_file": str((folder / "reading.json").relative_to(ROOT)),
                    }
                    reason = "PartIR 方法页3–5与固定 Shardy 路径用于6.2.2核对局部形状和集合载荷；不采纳未读性能评估，不把传播与全局最优策略等同。"
                paper["reading_status"] = "selected_sections_read"
            screens[n] = {"number": str(n), "decision": decision, "reason": reason}
            paper["screening"] = {"basis": "title_and_full_primary_public_abstract", "decision": decision, "reason": reason}
            paper["public_abstract"] = {"file": str((D / "public-abstracts.json").relative_to(ROOT)), "program_order": n, "sha256": record["abstract_sha256"], "source_id": record["source_id"]}
            paper["public_version_note"] = " ".join(record["version_notes"]) or record["history"]
            if "representative_pdf" in original:
                pdf = original["representative_pdf"]
                source = next(s for s in local_sources.values() if s["file"] == pdf["file"])
                source.update(program_order=n, pdf_pages=pdf["pages"], derived_text=pdf["text"], first_page_text=pdf["first_page_text"], first_page_raw=batch == "077-090", parallel_bundle=str(path.relative_to(ROOT)))
                paper["pdf"] = {k: source[k] for k in ("file", "url", "final_url", "bytes", "sha256", "retrieved_at")}
                paper["text"] = pdf["text"]
                paper["pages"] = pdf["pages"]
                paper["full_text_status"] = "public_copy_archived_identity_matched"
            else:
                paper["full_text_status"] = "primary_abstract_only_representative_pdf_unavailable"
            record["body_reading_status"] = "selected_sections_read" if n in (78, 80) else "not_read"
            records[n] = record
        for source in local_sources.values():
            if isinstance(source.get("status_code"), int):
                sources[source["id"]] = source
            else:
                errors.append(source)
    abstracts["records"] = [records[n] for n in sorted(records)]
    manifest["public_abstracts_available"] = manifest["abstracts_screened"] = len(records)
    manifest["public_pdfs_archived"] = sum("pdf" in p for p in papers.values())
    manifest["selected_sections_read"] = sum(p["reading_status"] == "selected_sections_read" for p in papers.values())
    assert (len(records), manifest["public_pdfs_archived"], manifest["selected_sections_read"]) == (98, 90, 17)
    assert len(sources) == 177 and len(errors) == 1
    write(D / "public-abstracts.json", abstracts)
    write(D / "selected-sources.json", list(sources.values()))
    write(D / "manifest.json", manifest)
    write(D / "pending-077-110/transport-errors.json", errors)
    with screen_path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=["number", "decision", "reason"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(screens[n] for n in sorted(screens))
    print("Merged 30 abstracts, 25 representative PDFs and 2 declared selected scopes")


if __name__ == "__main__":
    main()
