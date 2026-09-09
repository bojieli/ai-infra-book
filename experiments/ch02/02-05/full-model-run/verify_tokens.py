"""CPU-only offline token verification. Never loads weights, runs inference, or downloads.

Exit 0: required token/text checks pass and metadata fields are present.
Exit 1: an input/output evidence consistency check failed.
Exit 2: required records or metadata are missing (not a model-quality judgment).
Completion/EOS count relationships are observations, not hard assertions: the
saved tokenizer-manager source forwards scheduler counters and output IDs via
separate fields, insufficient to establish whether EOS must be retained in both.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def valid_ids(value):
    return isinstance(value, list) and all(type(x) is int and x >= 0 for x in value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Actual run directory')
    parser.add_argument('--output', type=Path, required=True, help='Fresh report JSON path; never overwrite')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output must not exist')
    # Set before transformers import: this script needs tokenizer code only.
    os.environ.update(CUDA_VISIBLE_DEVICES='', USE_TORCH='0', USE_TF='0', USE_FLAX='0', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    import transformers
    from transformers import AutoTokenizer
    run = args.out.resolve()
    frozen = read(run / 'cases.json')
    requests = read(run / 'requests.json')
    candidate = read(run / 'candidate.json')
    model = Path(candidate['model_path'])
    if not model.is_dir():
        parser.error('Original cached model directory is unavailable; no downloads permitted')
    tokenizer_evidence = read(run / 'preparation-evidence/tokenizer-evidence.json')
    actual_sha = sha(model / 'tokenizer.json')
    hash_matches = actual_sha == tokenizer_evidence['tokenizer_json_sha256']
    # Refuse to use a tokenizer that differs from the pre-execution frozen hash.
    if not hash_matches:
        report = dict(scope='offline_token_evidence_verification_not_quality_scoring', status='evidence_mismatch', tokenizer_json_sha256=actual_sha, expected_tokenizer_json_sha256=tokenizer_evidence['tokenizer_json_sha256'], transformers_version=transformers.__version__, error='Cached tokenizer hash differs from frozen preparation; decoding was not attempted')
        with args.output.open('x') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
        raise SystemExit(1)
    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True, trust_remote_code=False)
    generation = read(model / 'generation_config.json') if (model / 'generation_config.json').is_file() else {}
    eos = generation.get('eos_token_id', tokenizer.eos_token_id)
    eos_ids = eos if isinstance(eos, list) else [eos] if type(eos) is int else []
    by = {}
    malformed = []
    for i, row in enumerate(requests):
        if not isinstance(row, dict) or not isinstance(row.get('case_id'), str):
            malformed.append(i)
        else:
            by.setdefault(row['case_id'], []).append(row)
    case_ids = [case['id'] for case in frozen['cases']]
    missing_cases = [key for key in case_ids if key not in by]
    duplicates = [key for key, values in by.items() if len(values) > 1]
    unexpected = [key for key in by if key not in case_ids]
    mismatch = bool(malformed or duplicates or unexpected or len(case_ids) != 8 or len(set(case_ids)) != 8)
    incomplete = bool(missing_cases)
    checks = []
    for case in frozen['cases']:
        encoded = tokenizer.encode(case['prompt'], add_special_tokens=False)
        item = dict(case_id=case['id'], prompt_tokens=len(encoded), prompt_encode_matches_frozen=valid_ids(case['input_ids']) and encoded == case['input_ids'], frozen_prompt_count_matches=len(encoded) == case['prompt_tokens'], record_count=len(by.get(case['id'], [])))
        mismatch |= not item['prompt_encode_matches_frozen'] or not item['frozen_prompt_count_matches']
        if item['record_count'] != 1:
            item['status'] = 'record_missing_or_nonunique'; checks.append(item); continue
        row = by[case['id']][0]
        item['returned'] = row.get('status') == 'returned'
        item['request_input_matches_frozen'] = valid_ids(row.get('input_ids')) and row['input_ids'] == case['input_ids']
        mismatch |= not item['request_input_matches_frozen']
        incomplete |= not item['returned']
        response = row.get('response')
        response = response if isinstance(response, dict) else {}
        meta = response.get('meta_info')
        meta = meta if isinstance(meta, dict) else {}
        ids = response.get('output_ids')
        text = response.get('text')
        item['output_ids_valid'] = valid_ids(ids)
        item['missing_metadata'] = [key for key in ('completion_tokens', 'finish_reason') if key not in meta or meta[key] is None]
        incomplete |= bool(item['missing_metadata'])
        item['completion_tokens_metadata_valid'] = type(meta.get('completion_tokens')) is int and meta['completion_tokens'] >= 0
        item['finish_metadata_valid'] = isinstance(meta.get('finish_reason'), dict) and isinstance(meta['finish_reason'].get('type'), str)
        if 'completion_tokens' not in item['missing_metadata']:
            mismatch |= not item['completion_tokens_metadata_valid']
        if 'finish_reason' not in item['missing_metadata']:
            mismatch |= not item['finish_metadata_valid']
        if ids is None or text is None:
            incomplete = True
            item['status'] = 'response_fields_missing'
        elif not valid_ids(ids) or not isinstance(text, str):
            mismatch = True
            item['status'] = 'invalid_response_fields'
        else:
            decoded = tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            item.update(output_id_count=len(ids), decoded_text=decoded, original_text=text, decoded_text_exact_match=decoded == text, completion_tokens=meta.get('completion_tokens'), completion_count_equals_output_id_count=(meta['completion_tokens'] == len(ids) if type(meta.get('completion_tokens')) is int else None), output_eos_positions=[i for i, token in enumerate(ids) if token in eos_ids], output_last_id=ids[-1] if ids else None)
            mismatch |= decoded != text
            finish = meta.get('finish_reason')
            matched = finish.get('matched') if isinstance(finish, dict) else None
            matched_ids = [matched] if type(matched) is int else matched if valid_ids(matched) else None
            item.update(finish_reason=finish, finish_matched=matched, finish_matched_ids=matched_ids, finish_matched_is_eos=(any(t in eos_ids for t in matched_ids) if matched_ids is not None else None), output_last_matches_finish=(ids[-1] in matched_ids if ids and matched_ids is not None else None), finish_matched_string_present_in_raw_text=(matched in text if isinstance(matched, str) else None), eos_completion_relationship_scope='Observed only: finish matched token/string may be removed from returned output IDs/text; no assumed EOS count adjustment')
            if isinstance(finish, dict) and finish.get('type') == 'stop' and 'matched' not in finish:
                item['missing_metadata'].append('finish_reason.matched'); incomplete = True
            item['status'] = 'consistent_token_text' if decoded == text else 'decode_text_mismatch'
        checks.append(item)
    frozen_sha_matches = sha(run / 'cases.json') == tokenizer_evidence['cases_sha256']
    mismatch |= not frozen_sha_matches
    status = 'evidence_mismatch' if mismatch else 'incomplete_metadata_or_records' if incomplete else 'token_checks_passed'
    report = dict(scope='CPU-only offline token evidence verification; not answer-quality scoring and not numerical clearance', status=status, cpu_only=True, model_loaded=False, inference_requests=0, local_files_only=True, transformers_version=transformers.__version__, tokenizer_class=type(tokenizer).__name__, tokenizer_json_sha256=actual_sha, tokenizer_hash_matches_preparation=hash_matches, frozen_cases_sha256=sha(run / 'cases.json'), frozen_cases_hash_matches_preparation=frozen_sha_matches, requests_sha256=sha(run / 'requests.json'), verifier_sha256=sha(Path(__file__)), tokenizer_eos_token_id=tokenizer.eos_token_id, generation_eos_ids=eos_ids, decode_options=dict(skip_special_tokens=True, clean_up_tokenization_spaces=False), missing_case_ids=missing_cases, duplicate_case_ids=duplicates, unexpected_case_ids=unexpected, malformed_record_indices=malformed, checks=checks, strict_numerical_clearance=False, count_contract='Completion/output/EOS relationships are raw observations, not hard assertions; no trimming, count correction, or replacement of engine text was performed.')
    with args.output.open('x') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(dict(status=status, cases=len(checks), output=str(args.output))))
    raise SystemExit(1 if mismatch else 2 if incomplete else 0)


if __name__ == '__main__':
    main()
