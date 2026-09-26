#!/usr/bin/env python3
r"""`목록의 **NN번 주제**` 표기를 폴더 링크로 일괄 전환한다.

왜 메인이 하나 — 워커에게 「제출 직전 전환」을 시키면 동시 배치에서 경쟁 조건이 된다.
여러 묶음이 같이 도는 동안 폴더가 계속 생겨 워커마다 결과가 달라진다(실측).
그래서 워커는 `목록의 **NN번 주제**` 한 형태로만 적고, 배치가 끝난 뒤 이 스크립트가 한 번에 쓸어 담는다.

다루는 형태 — 굵게 있고 없고 · `주제` 붙고 안 붙고 · `·` 나열 · `~`/`\~` 범위.

★★ 실측 함정 — `**앞말 목록의 NN번 주제**` 처럼 **여는 `**` 가 「목록의」 앞에 있으면**
패턴이 뒤의 닫는 `**` 만 삼켜 **짝이 깨진다**(1차 3건 · 2차 4건 — 주석만으로는 못 막았다).
★ 이제 **코드가 막는다** — 줄 머리부터 매치 시작까지 `**` 개수가 홀수면 볼드 안이므로
안쪽 굵게를 넣지 않고 삼킨 닫는 `**` 를 링크 뒤에 되돌려 놓는다.
★★ 이 사고가 무서운 이유 — 깨진 `**` 가 **문단 뒤쪽의 다른 `**` 와 짝이 맞아 버리면**
본문에 별표가 안 남아 `check-md-rendering.mjs` 도 통과한다. **엉뚱한 범위가 조용히 굵어진다.**
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
            # ★★★ 앞에 「X 갈래」가 붙은 표기는 **다른 갈래의 번호**다 — 같은 갈래 폴더로 이으면
            #   링크 검사로도 안 걸리는 오전환이 된다(실측: 1,229곳 전환에서 4곳 — 「Java 갈래 목록의 11번」이
            #   C# 11번 폴더로 걸렸다). 규칙 8 이 표기를 같은 갈래 전용으로 정한 이유 그대로다. 건너뛴다.
            #   「같은 목록의」처럼 갈래 이름 없이 다른 갈래를 가리킨 자리는 기계로 못 가린다 — 사람이 본다.
            bol0 = src.rfind('\n', 0, m.start()) + 1
            if '갈래' in src[max(bol0, m.start() - 40):m.start()]:
                continue
            suf = m.group('suf') or ''
            # ★★ 삼킨 닫는 `**` 를 되돌린다 — 이 도구가 실제로 두 번 낸 사고다.
            #   `**앞말 목록의 NN번 주제**(…)` 에서 볼드는 「앞말」에서 열렸고 뒤의 `**` 가 그 닫는 짝이다.
            #   그걸 우리 표기의 일부로 삼키면 볼드가 안 닫히고, 문단 뒤쪽 `**` 와 짝이 맞아
            #   **글자가 안 남아 검사기도 조용히 넘어간다**(엉뚱한 범위가 굵어질 뿐).
            #   판정 — 매치 시작 전까지 그 줄의 `**` 개수가 홀수면 우리는 볼드 안에 있다.
            bol = src.rfind('\n', 0, m.start()) + 1
            inside_bold = src.count('**', bol, m.start()) % 2 == 1
            start = m.start()
            # ★ 볼드가 **정확히 우리 표기만** 감싼 꼴(`**목록의 NN번 주제**`) 인가.
            #   그러면 여는 `**` 까지 같이 삼켜 링크 텍스트 안으로 옮긴다.
            #   밖에 두면 `**[…](url)**다` 가 되는데, 닫는 `**` 앞이 `)` 이고 뒤가 한글이라
            #   CommonMark 가 안 닫는다(§2-1 「닫는 ** 앞이 문장부호」와 같은 사고).
            wraps_exactly = inside_bold and m.group('b2') and src[start - 2:start] == '**'
            if wraps_exactly:
                start -= 2
            # 링크 아닌 대괄호(`[목록의 …]`)는 통째로 바꿔치우므로 닫는 `]` 까지 소비된 상태다
            if len(nums) == 1:
                if wraps_exactly:
                    rep = '[**목록의 %s번%s**](../%s/)' % (nums[0], suf, folders[nums[0]])
                elif inside_bold:
                    # 볼드가 앞말에서 열렸다 — 안쪽에 `**` 를 또 넣으면 중첩이라 안 닫힌다.
                    # 링크만 만들고 삼킨 닫는 `**` 를 제자리에 돌려놓는다.
                    rep = '[목록의 %s번%s](../%s/)%s' % (
                        nums[0], suf, folders[nums[0]], '**' if m.group('b2') else '')
                else:
                    rep = '[목록의 **%s번%s**](../%s/)' % (nums[0], suf, folders[nums[0]])
            else:
                fmt = '[%s](../%s/)' if inside_bold else '[**%s**](../%s/)'
                joined = sep.join(fmt % (x, folders[x]) for x in nums)
                tail = '**' if (inside_bold and m.group('b2') and not wraps_exactly) else ''
                rep = '%s목록의 %s번%s%s' % ('**' if wraps_exactly else '', joined, suf,
                                            '**' if wraps_exactly else tail)
            out.append(src[last:start]); out.append(rep); last = m.end(); n += 1
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
