#!/usr/bin/env python3
"""
Builds the expected-results list from the XULE unit test source files and
compares it against the actual output of a test run, reporting any rule
whose actual result doesn't match its expected `/* ... */` comment.

Two subcommands:
  extract  - scan unitTests/source/base/*.xule (alphabetized, minus any
             --exclude files) for "output RULE" lines followed by a
             "/* expected value */" comment, and write them to a CSV.
  compare  - read that CSV plus a test run's output.txt, and report any
             rule whose actual result doesn't match, saved to a CSV.
"""
import argparse
import csv
import os
import re


NUMBER_RE = re.compile(r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?')
TAXONOMY_ERROR_MARKERS = (
    'concept {',
    'error while processing factset aspect',
)

OUTPUT_COMMENT_RE = re.compile(r'^output\s+(\S+)\s*\n\s*/\*(.*?)\*/', re.MULTILINE | re.DOTALL)
LINE_RE = re.compile(r'^\[([A-Za-z0-9_]+)(?:\.[^\]]*)?\]\s?(.*)$')
ERROR_RE = re.compile(r'^\[xule:error\]\s+rule\s+([A-Za-z0-9_]+):\s?(.*)$')
CONTAINER_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*)\s*\((.*)\)$', re.DOTALL)


def build_expected(source_dir, exclude):
    """Returns an ordered list of (rule, expected) from the alphabetized .xule files."""
    files = sorted(f for f in os.listdir(source_dir) if f.endswith('.xule') and f not in exclude)
    rows = []
    seen = set()
    for fname in files:
        text = open(os.path.join(source_dir, fname), encoding='utf-8').read()
        for m in OUTPUT_COMMENT_RE.finditer(text):
            name, comment = m.group(1), m.group(2).strip()
            if name in seen:
                continue
            seen.add(name)
            rows.append((name, comment))
    return rows


def cmd_extract(args):
    rows = build_expected(args.source_dir, set(args.exclude))
    with open(args.out, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['rule', 'expected'])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} expected rule results to {args.out}")


# --- comparison (order-insensitive for list/set/dictionary values) ---

def protect_number_commas(s):
    """Thousands-separator commas (e.g. 42,144,000) aren't list/dict separators."""
    return NUMBER_RE.sub(lambda m: m.group(0).replace(',', '\x00'), s)


def split_top_level(s):
    parts, depth, current = [], 0, []
    for ch in s:
        if ch in '({':
            depth += 1
            current.append(ch)
        elif ch in ')}':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(ch)
    parts.append(''.join(current))
    return [p for p in parts if p.strip()]


def unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


# `flags` controls which of the three post-fix normalizations are active:
# (strip_commas, strip_trailing_period, json_normalize). FULL is the current
# behavior; ablating one flag at a time (see explain_normalizations) lets us
# tell, per rule, exactly which normalization made a raw-differing value
# count as a match -- reported as MATCH_NORMALIZED with the specific reason
# instead of a generic "some formatting difference" statement.
FULL = (True, True, True)

NORMALIZATION_LABELS = [
    'thousands-separator commas',
    'a trailing period',
    'JSON key order and/or quoting',
]


def parse_node(s, flags=FULL):
    strip_commas, strip_period, json_normalize = flags
    s = s.strip()
    m = CONTAINER_RE.match(s)
    if m:
        name = m.group(1).lower()
        parts = split_top_level(m.group(2))
        if name == 'dictionary':
            children = [parse_dict_entry(p, flags) for p in parts]
        else:
            children = [parse_node(p, flags) for p in parts]
        return ('container', name, children)
    if json_normalize and s.startswith('{') and s.endswith('}'):
        parts = split_top_level(s[1:-1])
        return ('container', '{}', [parse_brace_entry(p, flags) for p in parts])
    atom = s.replace('\x00', ',')
    return ('atom', unquote(atom) if json_normalize else atom)


def parse_dict_entry(s, flags=FULL):
    _, _, json_normalize = flags
    depth = 0
    for idx, ch in enumerate(s):
        if ch in '({':
            depth += 1
        elif ch in ')}':
            depth -= 1
        elif ch == '=' and depth == 0:
            key = s[:idx].strip().replace('\x00', ',')
            return ('dictentry', unquote(key) if json_normalize else key, parse_node(s[idx + 1:].strip(), flags))
    atom = s.replace('\x00', ',')
    return ('atom', unquote(atom) if json_normalize else atom)


def parse_brace_entry(s, flags=FULL):
    """A brace-wrapped entry is either a JSON-style "key: value" pair or a
    plain value (used by the {v1},{v2} "set of results" representation)."""
    depth = 0
    for idx, ch in enumerate(s):
        if ch in '({':
            depth += 1
        elif ch in ')}':
            depth -= 1
        elif ch == ':' and depth == 0:
            key = s[:idx].strip().replace('\x00', ',')
            return ('dictentry', unquote(key), parse_node(s[idx + 1:].strip(), flags))
    return parse_node(s, flags)


NUMERIC_ATOM_RE = re.compile(r'^-?\d{1,3}(,\d{3})*(\.\d+)?$')


def normalize_atom(s, flags=FULL):
    strip_commas, strip_period, json_normalize = flags
    s = re.sub(r'\s+', ' ', s).strip()
    if strip_period and s.endswith('.'):
        s = s[:-1]
    if strip_commas and NUMERIC_ATOM_RE.match(s):
        s = s.replace(',', '')
    return s.lower()


def canonical(node, flags=FULL):
    kind = node[0]
    if kind == 'atom':
        return normalize_atom(node[1], flags)
    if kind == 'dictentry':
        _, key, value_node = node
        return f"{normalize_atom(key, flags)}={canonical(value_node, flags)}"
    _, name, children = node
    return f"{name}({','.join(sorted(canonical(c, flags) for c in children))})"


def canonicalize_text(s, flags=FULL):
    return canonical(parse_node(protect_number_commas(s).strip(), flags), flags)


def explain_normalizations(cand, expected_text):
    """Given a candidate that only matches expected_text under FULL flags,
    return the human-readable label(s) for whichever normalization(s) were
    actually necessary -- found by disabling one flag at a time and checking
    whether the match still holds."""
    reasons = []
    for i, label in enumerate(NORMALIZATION_LABELS):
        ablated = list(FULL)
        ablated[i] = False
        ablated = tuple(ablated)
        try:
            still_matches = canonicalize_text(cand, ablated) == canonicalize_text(expected_text, ablated)
        except Exception:
            still_matches = False
        if not still_matches:
            reasons.append(label)
    return reasons


def parse_actual(output_path):
    values, raw_lines = {}, {}
    with open(output_path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.rstrip('\n')
            m = LINE_RE.match(line)
            if m:
                values.setdefault(m.group(1), []).append(m.group(2))
                raw_lines.setdefault(m.group(1), []).append(line)
                continue
            m = ERROR_RE.match(line)
            if m:
                full = f"rule {m.group(1)}: {m.group(2)}"
                values.setdefault(m.group(1), []).append(full)
                raw_lines.setdefault(m.group(1), []).append(line)
    return values, raw_lines


def looks_like_taxonomy_error(vals):
    return any(marker in v.lower() for v in vals for marker in TAXONOMY_ERROR_MARKERS)


def is_xule_error(expected_text, actual_repr):
    return expected_text.startswith('[xule:error]') or actual_repr.startswith('[xule:error]')


def candidate_representations(vals, raw_lines):
    cands = {'\n'.join(vals), '\n'.join(raw_lines),
              '{' + ','.join('{' + v + '}' for v in vals) + '}'}
    if len(vals) == 1:
        cands.add(vals[0])
    return cands


def classify(expected_text, actual_values, actual_raw_lines, name):
    vals = actual_values.get(name)
    if vals is None:
        if normalize_atom(expected_text) == 'skip':
            return 'MATCH', '', []
        return 'REQUIRES_INSTANCE_OR_TAXONOMY', '', []

    raw_lines = actual_raw_lines[name]
    actual_repr = '\n'.join(raw_lines)
    if looks_like_taxonomy_error(vals):
        return 'REQUIRES_INSTANCE_OR_TAXONOMY', actual_repr, []

    try:
        exp_canon = canonicalize_text(expected_text)
    except Exception:
        exp_canon = normalize_atom(expected_text)

    for cand in candidate_representations(vals, raw_lines):
        try:
            cand_canon = canonicalize_text(cand)
        except Exception:
            cand_canon = normalize_atom(cand)
        if cand_canon == exp_canon:
            reasons = explain_normalizations(cand, expected_text)
            if not reasons:
                return 'MATCH', actual_repr, []
            return 'MATCH_NORMALIZED', actual_repr, reasons

    return 'MISMATCH', actual_repr, []


GROUP_ORDER = ['REQUIRES_INSTANCE_OR_TAXONOMY', 'MISMATCH', 'MATCH_NORMALIZED', 'MATCH']
GROUP_HEADINGS = {
    'REQUIRES_INSTANCE_OR_TAXONOMY': 'REQUIRES INSTANCE/TAXONOMY',
    'MISMATCH': 'MISMATCH',
    'MATCH_NORMALIZED': 'MATCH AFTER NORMALIZING A COSMETIC DIFFERENCE',
    'MATCH': 'MATCH',
}


def partition_xule_error(rows):
    """Splits a group's rows into (xule_error_rows, other_rows), preserving
    each subset's existing relative order. A row is xule_error if its
    expected or actual text begins with "[xule:error]"."""
    xule_error_rows = [r for r in rows if is_xule_error(r[2], r[3])]
    other_rows = [r for r in rows if not is_xule_error(r[2], r[3])]
    return xule_error_rows, other_rows


def print_row(status, name, expected_text, actual_repr, reason):
    if status == 'MATCH_NORMALIZED':
        print(f"[MATCH_NORMALIZED] {name}: {reason}")
        print(f"expected={expected_text!r}")
        print(f"actual={actual_repr!r}\n ")
    elif status == 'MISMATCH':
        print(f"[MISMATCH] {name}:")
        print(f"expected={expected_text!r}")
        print(f"actual={actual_repr!r}\n ")
    else:
        print(f"[{status}] {name}: expected={expected_text!r} actual={actual_repr!r}")


def cmd_compare(args):
    expected_rows = []
    with open(args.expected, encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            expected_rows.append((row['rule'], row['expected']))

    actual_values, actual_raw_lines = parse_actual(args.output)

    counts = {'MATCH': 0, 'MATCH_NORMALIZED': 0, 'MISMATCH': 0, 'REQUIRES_INSTANCE_OR_TAXONOMY': 0}
    grouped = {status: [] for status in GROUP_ORDER}
    for name, expected_text in expected_rows:
        status, actual_repr, reasons = classify(expected_text, actual_values, actual_raw_lines, name)
        counts[status] += 1
        grouped[status].append((name, status, expected_text, actual_repr, ', '.join(reasons)))

    with open(args.csv, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['rule', 'status', 'expected', 'actual', 'reason'])
        for status in GROUP_ORDER:
            rows = grouped[status]
            writer.writerow([f"=== {GROUP_HEADINGS[status]} ({len(rows)}) ==="])
            xule_error_rows, other_rows = partition_xule_error(rows)
            if xule_error_rows and other_rows:
                writer.writerow([f"--- xule_error ({len(xule_error_rows)}) ---"])
                writer.writerows(xule_error_rows)
                writer.writerow([f"--- other ({len(other_rows)}) ---"])
                writer.writerows(other_rows)
            else:
                writer.writerows(rows)

    for status in GROUP_ORDER:
        rows = grouped[status]
        print(f"\n \n=== {GROUP_HEADINGS[status]} ({len(rows)}) ===")
        xule_error_rows, other_rows = partition_xule_error(rows)
        if xule_error_rows and other_rows:
            print(f"--- xule_error ({len(xule_error_rows)}) ---")
            for name, row_status, expected_text, actual_repr, reason in xule_error_rows:
                print_row(row_status, name, expected_text, actual_repr, reason)
            print(f"--- other ({len(other_rows)}) ---")
            for name, row_status, expected_text, actual_repr, reason in other_rows:
                print_row(row_status, name, expected_text, actual_repr, reason)
        else:
            for name, row_status, expected_text, actual_repr, reason in rows:
                print_row(row_status, name, expected_text, actual_repr, reason)

    problem_count = counts['MISMATCH'] + counts['REQUIRES_INSTANCE_OR_TAXONOMY']
    print(f"\nSummary: {counts['MATCH']} match, {counts['MATCH_NORMALIZED']} match after normalizing a "
          f"cosmetic difference (commas/trailing period/JSON formatting), {counts['MISMATCH']} mismatch, "
          f"{counts['REQUIRES_INSTANCE_OR_TAXONOMY']} require instance/taxonomy, "
          f"{len(expected_rows)} total rules checked.")

    if problem_count == 0:
        print("No errors found in unit test output.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)

    p_extract = sub.add_parser('extract', help='Build the expected-results CSV from XULE source comments.')
    p_extract.add_argument('--source-dir', required=True)
    p_extract.add_argument('--exclude', nargs='*', default=[])
    p_extract.add_argument('--out', required=True)
    p_extract.set_defaults(func=cmd_extract)

    p_compare = sub.add_parser('compare', help='Compare actual test output against the expected-results CSV.')
    p_compare.add_argument('--expected', required=True)
    p_compare.add_argument('--output', required=True)
    p_compare.add_argument('--csv', required=True)
    p_compare.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
