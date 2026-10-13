#!/usr/bin/env python3
"""Parse CSS syntax; this is not a rendered/browser layout audit.

Optional QA dependency (not used by the site):
python3 -m pip install --target /tmp/isnp-css-qa tinycss2==1.4.0
PYTHONPATH=/tmp/isnp-css-qa python3 scripts/check_styles.py
"""
from pathlib import Path
import tinycss2

ROOT = Path(__file__).resolve().parents[1]
errors = []

def inspect(rules, filename):
    for rule in rules:
        if rule.type == 'error':
            errors.append(f'{filename}: {rule.message}')
        elif rule.type == 'qualified-rule' or (rule.type == 'at-rule' and rule.lower_at_keyword == 'font-face'):
            for declaration in tinycss2.parse_declaration_list(rule.content, skip_whitespace=True, skip_comments=True):
                if declaration.type == 'error':
                    errors.append(f'{filename}:{declaration.source_line}: {declaration.message}')
        elif rule.type == 'at-rule' and rule.content:
            inspect(tinycss2.parse_rule_list(rule.content, skip_whitespace=True, skip_comments=True), filename)

for path in sorted(ROOT.glob('*.css')):
    inspect(tinycss2.parse_stylesheet(path.read_text(), skip_whitespace=True, skip_comments=True), path.name)
if errors:
    raise SystemExit('\n'.join(errors))
print('PASS — CSS syntax parsed across both stylesheets. Browser QA is separate.')
