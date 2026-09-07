#!/usr/bin/env python3
"""Public GitHub issue forecasts. No user-supplied code or credentials are executed."""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import statistics
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOSS_FIELDS = ('p_total_loss', 'p_partial_loss', 'partial_severity')
FIELDS = ('p_go', *LOSS_FIELDS)


def timestamp(value):
    value = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Timezone required')
    return value


def validate(payload, question, submitted_at):
    if not timestamp(question['opens_at']) <= timestamp(submitted_at) < timestamp(question['closes_at']):
        raise ValueError('Outside forecast period')
    if payload.get('version') != 1 or payload.get('question_id') != question['id']:
        raise ValueError('Unknown format or question')
    if payload.get('vote') not in ('GO', 'NO-GO'):
        raise ValueError('Choose GO or NO-GO')
    has_loss = any(k in payload for k in LOSS_FIELDS)
    for name in (FIELDS if has_loss else ('p_go',)):
        n = payload.get(name)
        if type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 100:
            raise ValueError(f'{name} must be 0–100')
    if has_loss and payload['p_total_loss'] + payload['p_partial_loss'] > 100:
        raise ValueError('Loss probabilities exceed 100%')
    reason = payload.get('reason', '')
    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 600:
        raise ValueError('Give 10–600 characters of reasoning')
    source = payload.get('source_url', '')
    if not isinstance(source, str) or len(source) > 300 or (source and not re.match(r'^https://[^\s]+$', source)):
        raise ValueError('Source must be an HTTPS URL')
    return {k: payload[k] for k in ('version', 'question_id', 'vote', 'p_go', 'reason', *(LOSS_FIELDS if has_loss else ()))} | {'source_url': source}


def reconcile(issues, previous, questions, now):
    """Keep observed pre-cutoff versions; ignore late edits. Latest per author is aggregated."""
    known = {q['id']: q for q in questions}
    records = {r['issue_number']: r for r in previous}
    rejected = []
    present = set()
    for issue in issues:
        if 'pull_request' in issue:
            continue
        number = issue['number']
        present.add(number)
        labels = {x['name'] for x in issue.get('labels', [])}
        if 'crowd-exclude' in labels:
            records.pop(number, None)
            continue
        if issue.get('user', {}).get('type') != 'User':
            continue
        # GitHub metadata, not fields claimed in the submitted JSON, provides identity and time.
        submitted = issue['updated_at']
        old = records.get(number)
        if old and old['question_id'] in known and timestamp(submitted) >= timestamp(known[old['question_id']]['closes_at']):
            continue
        records.pop(number, None)
        if not issue.get('title', '').startswith('[CrowdLaunch forecast]'):
            continue
        try:
            body = issue.get('body') or ''
            if len(body) > 6000:
                raise ValueError('Submission too large')
            match = re.fullmatch(r'\s*```json\s*\n(.*?)\n```\s*', body, re.S)
            if not match:
                raise ValueError('Expected the generated JSON block')
            payload = json.loads(match[1])
            if not isinstance(payload, dict) or payload.get('question_id') not in known:
                raise ValueError('Unknown question')
            if timestamp(submitted) > now:
                raise ValueError('Future timestamp')
            row = validate(payload, known[payload['question_id']], submitted)
            row.update(issue_number=number, author=issue['user']['login'], author_id=issue['user']['id'], submitted_at=submitted)
            records[number] = row
        except (ValueError, TypeError, KeyError) as exc:
            rejected.append({'issue_number': number, 'reason': str(exc)})
    # Deleted issues are withdrawn. All API pages must be fetched successfully first.
    return sorted((r for n, r in records.items() if n in present), key=lambda r: r['issue_number']), rejected


def summarize(records, question):
    latest = {}
    for r in sorted(records, key=lambda r: (r['submitted_at'], r['issue_number'])):
        if r['question_id'] == question['id']:
            latest[r['author_id']] = r
    rows = list(latest.values())
    n = len(rows)
    result = {'n': n, 'go_votes': sum(r['vote'] == 'GO' for r in rows)}
    if not n:
        return result
    result['p_go'] = statistics.mean(r['p_go'] for r in rows)
    result['go_median'] = statistics.median(r['p_go'] for r in rows)
    result['go_min'] = min(r['p_go'] for r in rows)
    result['go_max'] = max(r['p_go'] for r in rows)
    # Each person's joint estimate is calculated BEFORE averaging (preserves their dependence).
    loss_rows = [r for r in rows if all(k in r for k in LOSS_FIELDS)]
    result['loss_n'] = len(loss_rows)
    if loss_rows:
        loss = [r['p_total_loss']/100 + r['p_partial_loss']/100 * r['partial_severity']/100 for r in loss_rows]
        result['conditional_loss_rate'] = statistics.mean(loss)
        result['window_loss_rate'] = statistics.mean(r['p_go']/100 * e for r, e in zip(loss_rows, loss))
    resolution = question.get('resolution')
    if resolution and resolution.get('go') in (0, 1) and resolution.get('source_url', '').startswith('https://'):
        result['go_brier'] = statistics.mean((r['p_go']/100-resolution['go'])**2 for r in rows)
    return result


def fetch_issues(repository):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Invalid repository')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'CrowdLaunch', 'X-GitHub-Api-Version': '2022-11-28'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    result = []
    for page in range(1, 1001):
        url = f'https://api.github.com/repos/{repository}/issues?state=all&per_page=100&page={page}'
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError('Unexpected GitHub response; retaining previous snapshot')
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise ValueError('Pagination limit reached; refusing partial snapshot')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--issues', help='Local API fixture for tests/offline builds')
    parser.add_argument('--repository', default='rcamp004/CrowdLaunch')
    args = parser.parse_args()
    questions = json.loads((ROOT/'config/questions.json').read_text())
    target = ROOT/'site/data/crowd.json'
    previous = json.loads(target.read_text()).get('forecasts', []) if target.exists() else []
    issues = json.loads(Path(args.issues).read_text()) if args.issues else fetch_issues(args.repository)
    now = dt.datetime.now(dt.timezone.utc)
    records, rejected = reconcile(issues, previous, questions, now)
    output = {'updated_at': now.isoformat(), 'questions': questions, 'forecasts': records,
              'summaries': {q['id']: summarize(records, q) for q in questions}, 'rejected': rejected}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    temporary.replace(target)
    print(f'{len(records)} accepted submissions; {len(rejected)} rejected')


if __name__ == '__main__':
    main()
