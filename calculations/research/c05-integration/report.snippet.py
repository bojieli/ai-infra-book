# Copy ub_scope_markdown() from renderer.py into report.py, importing Fraction there.
# Dispatch at the VERY START of markdown(result), before result['summary'] access:
# if result.get('calculation') == 'ub-scope':
#     return ub_scope_markdown(result)
# This early branch is required: ub_scope intentionally keeps summaries per candidate
# and has no top-level summary. No reshaping of raw result/CLI JSON is necessary.
