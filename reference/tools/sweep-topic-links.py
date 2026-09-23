#!/usr/bin/env python3
r"""`목록의 **NN번 주제**` 표기를 폴더 링크로 일괄 전환한다.

왜 메인이 하나 — 워커에게 「제출 직전 전환」을 시키면 동시 배치에서 경쟁 조건이 된다.
여러 묶음이 같이 도는 동안 폴더가 계속 생겨 워커마다 결과가 달라진다(실측).
그래서 워커는 `목록의 **NN번 주제**` 한 형태로만 적고, 배치가 끝난 뒤 이 스크립트가 한 번에 쓸어 담는다.

다루는 형태 — 굵게 있고 없고 · `주제` 붙고 안 붙고 · `·` 나열 · `~`/`\~` 범위.

★★ 실측 함정 — `**목록의 NN번 주제**` 처럼 **여는 `**` 가 「목록의」 앞에 있으면**
패턴이 뒤의 닫는 `**` 만 삼켜 **짝이 깨진다**(실제로 3건 났다).
치환 뒤에는 반드시 `check-md-rendering.mjs` 를 돌리고, **이미 볼드 span 안인 자리에는
안쪽 `**` 를 넣지 않는다**(중첩 볼드는 CommonMark 에서 안 닫힌다).
폴더가 없는 번호와 자기 자신을 가리키는 번호는 **그대로 둔다**(아직 걸 곳이 없다).
"""
import re, os, sys, glob, collections

# 굵게 · 「주제」 유무 · 나열(·) · 범위(~ 또는 \~) 를 한 패턴으로
# 앞뒤 대괄호를 함께 잡는다. 「이미 링크인가」는 닫는 `]` 뒤에 `(` 가 오는지로 판정한다.
# ★ 실측 버그: 대괄호만 있고 `(...)` 가 없는 `[목록의 **20번 주제**]` 를
#   「이미 링크」로 보고 통째로 건너뛰었다. 대괄호는 링크가 아니다 — 뒤에 URL 이 와야 링크다.
PAT = re.compile(
    r'(?P<lead>\[)?'
    r'목록의 (?P<b1>\*\*)?'
    r'(?P<nums>\d{1,2}(?:\s*[·]\s*\d{1,2}|\s*\\?~\s*\d{1,2})*)번'
    r'(?P<suf> 주제)?(?P<b2>\*\*)?'
    r'(?P<close>\])?')

def sweep(root, apply=False):
    folders = {d[:2]: d for d in os.listdir(root)
               if os.path.isdir(os.path.join(root, d)) and re.match(r'^\d\d-', d)}
    total = 0
    hits = collections.Counter()
    for f in sorted(glob.glob(os.path.join(root, '*', '[123]-*.md'))):
        src = open(f, encoding='utf-8').read()
        own = os.path.basename(os.path.dirname(f))[:2]
        out, last, n = [], 0, 0
        for m in PAT.finditer(src):
            # 닫는 `]` 뒤에 `(` 가 오면 진짜 링크다 — 건너뛴다
            if m.group('lead') and m.group('close') and src[m.end():m.end() + 1] == '(':
                continue
            # 대괄호가 한쪽만 있으면 우리 표기가 아니다 — 건드리지 않는다
            if bool(m.group('lead')) != bool(m.group('close')):
                continue
            raw = m.group('nums')
            sep = '·' if '·' in raw else ('~' if '~' in raw else None)
            nums = [x.strip().lstrip('\\') for x in re.split(r'[·~\\]+', raw) if x.strip()]
            nums = [x.zfill(2) for x in nums]
            if any(x not in folders for x in nums) or all(x == own for x in nums):
                continue                                   # 걸 곳이 없다
            suf = m.group('suf') or ''
            # 링크 아닌 대괄호(`[목록의 …]`)는 통째로 바꿔치우므로 닫는 `]` 까지 소비된 상태다
            if len(nums) == 1:
                rep = '[목록의 **%s번%s**](../%s/)' % (nums[0], suf, folders[nums[0]])
            else:
                joined = sep.join('[**%s**](../%s/)' % (x, folders[x]) for x in nums)
                rep = '목록의 %s번%s' % (joined, suf)
            out.append(src[last:m.start()]); out.append(rep); last = m.end(); n += 1
        if n:
            out.append(src[last:])
            if apply:
                open(f, 'w', encoding='utf-8').write(''.join(out))
            hits[os.path.basename(os.path.dirname(f))] = n
            total += n
    return total, hits

if __name__ == '__main__':
    apply = '--apply' in sys.argv
    grand = 0
    for root in sorted(glob.glob('cs/foundations/languages/*/syntax')) + ['cs/foundations/web-api']:
        if not os.path.isdir(root):
            continue
        t, h = sweep(root, apply)
        if t:
            print('%-48s %4d곳 (%d파일)' % (root, t, len(h)))
            grand += t
    print('---- 전환 %d곳 %s' % (grand, '(적용)' if apply else '(예행)'))
