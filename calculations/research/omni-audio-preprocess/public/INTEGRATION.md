# Omni PCM frontend public migration

Copy src/infra_calc/topics/omni_audio_preprocess.py to the matching public src location and tests/test_omni_audio_preprocess.py into tests. Add the four flat scenarios from book.append.json to a dedicated group/CLI. calculate(sample_lengths=None, sampling_rate=16000, encoder_element_bytes=4) and markdown(result) are unchanged; scenario is directly replayable. The dedicated Markdown renderer retains all stage/source/interface fields.

## Official original files and local source lock

Copy all entries in copy-manifest.json from this public candidate directory into the matching paths below calculations/. The runtime module sets HERE = PROJECT / "sources/omni-audio-preprocess" and validates its local sources.lock.json before reading config. The internal sources/ subdirectory is deliberately retained, so every source_file locator and every function AST remain unchanged. Thus an original relative locator sources/feature_extraction_whisper.py resolves to PROJECT/sources/omni-audio-preprocess/sources/feature_extraction_whisper.py. This small nesting avoids rewriting source fields in frozen results.

local-lock-path-map.json explicitly maps each frozen relative file to its public project path. The local lock retains original SHA, byte size, URL and revision exactly; it is not a global configs/sources.lock.json append patch. If global source catalog registration is desired, map file to project_file and add the catalog's required model/status/timestamp fields using existing download evidence; do not claim a new download timestamp. Local runtime checksum verification already covers all originals. No weights or new sources were downloaded for this migration.

## Verification and portability

Six portable tests run from this directory with the real public infra_calc.paths import. Before files are installed, the tests redirect only module.HERE to the staged exact source bundle. Once copied into public tests, this candidate fixture path is absent and the normal PROJECT source root is used. There are no research module imports or runtime path searches in the production module.

verify_migration.py is a migration audit utility, not a production dependency. It compares every top-level function AST with the accepted original (including calculate, evidence and markdown), verifies every copied source hash, and compares all four result objects and renderings byte-for-byte/field-for-field. The sole production source edit is the module-level import/root definition. Calculation functions and all result fields are unchanged. Original numerical/independent review evidence stays in the accepted research directories; this migration does not substitute new fake numerical validation.

The selected frontend still has the accepted 30-second effective constructor cap, max-indices output correction, explicit FFT primitive boundary and caller BF16 bridge. This is not full audio decoding, resampling, encoder arithmetic or whole processor runtime. Use existing encoder bridge fields without counting encoder matrices twice.
