from pathlib import Path
import tempfile,shutil,subprocess,difflib
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent
stage=O/'candidate';stage.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)
 for name in ['units.py','schema.py','sources.py']:
  p=root/'calculations/src/infra_calc'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'src/infra_calc'/name,p)
 subprocess.run(['patch','-p0','-d',str(root),'-i',str(O/'proposed-foundation.patch')],check=True,capture_output=True)
 for name in ['units.py','schema.py','sources.py']:shutil.copy2(root/'calculations/src/infra_calc'/name,stage/name)
p=stage/'units.py';s=p.read_text().replace('not math.isfinite(value)', '(isinstance(value, float) and not math.isfinite(value))');p.write_text(s)
p=stage/'schema.py';s=p.read_text().replace('positive_int(dimension, "weight shape dimension", allow_zero=True)','positive_int(dimension, "weight shape dimension")');s=s.replace('        return asdict(self)', '        self.__post_init__()\n        return asdict(self)');p.write_text(s)
p=stage/'sources.py';s=p.read_text().replace('import tempfile','import tempfile\nimport re');s=s.replace('"""Re-download the locked bytes; never silently follow a new main revision."""','"""Re-download exact model source group (not transitive dependencies) or all groups."""');start=s.index('        headers = {"User-Agent"');end=s.index('        if hashlib.sha256(data)',start)
s=s[:start]+'''        expected_bytes = positive_int(row["bytes"], "locked source bytes", allow_zero=True)
        headers = {"User-Agent": "ai-infra-book-calculations/0.1"}
        interval = None
        if row.get("http_range"):
            match = re.fullmatch(r"bytes=(\\d+)-(\\d+)", row["http_range"])
            if match is None:
                raise ValueError("Locked source requires a bounded byte range")
            start, end = map(int, match.groups())
            if end < start or end - start + 1 != expected_bytes:
                raise ValueError("Locked source range and byte count disagree")
            interval = (start, end)
            headers["Range"] = row["http_range"]
        request = Request(row["url"], headers=headers)
        with urlopen(request, timeout=60) as response:
            length = response.headers.get("Content-Length")
            if length is not None:
                if re.fullmatch(r"\\d+", length) is None or int(length) != expected_bytes:
                    raise ValueError("Response Content-Length disagrees with locked bytes")
            content_range = response.headers.get("Content-Range")
            if interval is not None:
                match = re.fullmatch(r"bytes (\\d+)-(\\d+)/(\\d+)", content_range or "")
                if response.status != 206 or match is None:
                    raise ValueError("Server did not honor locked header byte range")
                start, end, total = map(int, match.groups())
                if (start, end) != interval or total <= end:
                    raise ValueError("Response Content-Range disagrees with locked byte range")
            elif response.status != 200 or content_range is not None:
                raise ValueError("Full source request returned a partial or invalid response")
            data = response.read(expected_bytes + 1)
        if len(data) != expected_bytes:
            raise ValueError(f"Remote length mismatch: {row['url']}")
''' +s[end:];p.write_text(s)
for name in ['cli.py','reproduce.py']:
 s=(R/'src/infra_calc'/name).read_text();s=s.replace('json.dumps(result, ensure_ascii=False, indent=2)','json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)')
 if name=='cli.py':s=s.replace('Re-download pinned sources, preserving their checksum','Re-download a pinned source group, preserving checksum; no dependency expansion').replace('fetch.add_argument("--model")','fetch.add_argument("--model", help="Exact source group; omit for all groups (not transitive model dependencies)")')
 else:
  s=s.replace('    paths = [','    paths = [PROJECT / "calc.py", ',1)
  s=s.replace('    for artifact in manifest["artifacts"]:', '''    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Result manifest must contain a nonempty artifact list")
    names = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("file"), str):
            raise ValueError("Invalid result artifact record")
        name = artifact["file"]
        relative = Path(name)
        if name != relative.as_posix() or relative.is_absolute() or ".." in relative.parts or len(relative.parts) < 2 or relative.parts[0] != "results":
            raise ValueError("Result artifact must be a relative path inside results")
        if name in names or not isinstance(artifact.get("sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None:
            raise ValueError("Duplicate or invalid result artifact record")
        names.add(name)
    if "results/README.md" not in names:
        raise ValueError("Result manifest lacks its required README index")
    for artifact in artifacts:''')
  s=s.replace('import hashlib','import hashlib\nimport re\nfrom pathlib import Path',1)
 (stage/name).write_text(s)
patch=''
for p in sorted(stage.glob('*.py')):
 compile(p.read_text(),str(p),'exec');target=R/'src/infra_calc'/p.name;label='calculations/src/infra_calc/'+p.name;patch+=''.join(difflib.unified_diff(target.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=label,tofile=label))
(O/'final-foundation.patch').write_text(patch)
print('Five-file candidate generated; no shared files changed')
