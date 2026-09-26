#!/usr/bin/env python3
r"""닫는 `**` 앞이 문장부호라 **볼드가 안 닫히는** 자리를 고친다.

왜 필요한가 — CommonMark 는 닫는 `**` 가 **오른쪽 밀착**일 때만 볼드를 닫는다.
닫는 `**` 바로 앞이 문장부호이고 뒤가 글자면 밀착이 깨져 **별표가 그대로 보인다.**
한국어에서 이 조합이 자연스럽게 나온다 — `**「보장」**이다` · `**이동(move)**이고`.

실측 — 한 세션에서 같은 치환을 **네 번**(40 · 26 · 22 · 26건) 손으로 돌렸다. 도구로 올린다.

두 단계로 고친다.

  ① **볼드가 낫표만 감쌀 때** — `**「X」**다` → `「**X**」다`
     인용부호를 볼드 밖으로 빼면 닫는 `**` 앞이 글자가 되어 닫힌다. 강조 범위도 그대로다.
  ② **볼드가 인용부호보다 넓을 때** — `**A「X」**다` → `**A「X」다**`
     꼬리 조사를 볼드 안으로 넣는다. ①로는 못 고치는 자리다.

★★ **①을 먼저 돌려라.** ②만 돌리면 ①로 깔끔히 고칠 것까지 조사를 삼켜 강조 범위가 넓어진다.

★★★ **판단은 정규식이 아니라 렌더로 한다.** 이 스크립트는 **고칠 후보를 줄이는 도구**이지
    합격 판정기가 아니다. **돌린 뒤 반드시 `check-md-rendering.mjs` 로 확인**하고,
    남은 것은 손으로 고쳐라(인용부호가 둘 이상인 자리는 이 패턴이 못 잡는다).

★★ **오탐율을 정직하게 적어 둔다.** 방어 둘(코드 스팬 마스킹 · 여는 `**` 판정)을 넣은 뒤
    저장소 전수에서 **후보 3곳**이 나왔는데 **렌더 검사로는 0건**이었다 — **셋 다 오탐**이다.
    남은 오탐 꼴은 **마스킹이 코드 스팬을 접으면서** 없던 짝이 생기는 것이다.
    ★ 그러니 **이 도구의 출력을 그대로 적용하지 마라.** 렌더가 깨졌다고 말한 파일에만 돌리고,
    돌린 뒤 다시 렌더로 확인해라. **깨진 것을 고치는 데는 쓰고, 합격 판정에는 쓰지 않는다.**

★ 강조 범위가 달라지면 그건 표기 수정이 아니라 **개작**이다(§2-1) — ②는 조사 한 덩이만 옮긴다.

사용:
    fix-bold-punct.py <파일.md> [파일.md ...]          # 고친다
    fix-bold-punct.py --dry-run <파일.md> ...          # 세어만 본다
"""
import pathlib
import re
import sys

# ① 볼드가 낫표만 감싼 것 — 닫는 `**` 뒤가 한글일 때만 손댄다(그 자리만 깨지므로).
PASS1 = re.compile(r'\*\*「([^」\n]*)」\*\*(?=[가-힣])')
# ② 볼드가 더 넓고 끝이 문장부호인 것 — 꼬리 한글을 볼드 안으로.
PASS2 = re.compile(r'\*\*([^*\n]*[」』）\)”\]`])\*\*([가-힣]+)')


CODE = re.compile(r'(`+)(?:[^`]|(?!\1)`)*?\1')


def _mask_code(text: str):
    """코드 스팬을 자리표로 가린다.

    ★★★ 안 가리면 **정본 문서의 예시를 망가뜨린다** — 이 문서는 깨진 꼴을
    `` `**이동(move)**이고` `` 처럼 **코드로 인용**해 두었고, 그것까지 고치면 교재가 상한다(실측 4건).
    """
    spans = []

    def keep(m):
        spans.append(m.group(0))
        return '\x00%d\x00' % (len(spans) - 1)

    return CODE.sub(keep, text), spans


def _unmask(text: str, spans) -> str:
    for i, s in enumerate(spans):
        text = text.replace('\x00%d\x00' % i, s)
    return text


def _pass2(text: str) -> tuple:
    """②를 적용하되 **여는 `**` 를 닫는 것으로 오인하지 않는다.**

    `**앞말**([링크](…))**뒷말**` 에서 둘째 `**` 는 **여는** 쪽인데
    그 뒤 내용이 `)` 로 끝나 ②의 패턴에 걸린다(실측). 줄 머리부터 센 `**` 개수가
    **짝수일 때만** 그 자리가 여는 자리다.
    """
    out, last, n = [], 0, 0
    for m in PASS2.finditer(text):
        bol = text.rfind('\n', 0, m.start()) + 1
        if text.count('**', bol, m.start()) % 2:      # 홀수 = 이미 볼드 안 = 여는 자리가 아니다
            continue
        out.append(text[last:m.start()])
        out.append('**%s%s**' % (m.group(1), m.group(2)))
        last = m.end()
        n += 1
    out.append(text[last:])
    return ''.join(out), n


def fix(text: str):
    masked, spans = _mask_code(text)
    masked, n1 = PASS1.subn(r'「**\1**」', masked)
    masked, n2 = _pass2(masked)
    return _unmask(masked, spans), n1, n2


def main() -> None:
    args = [a for a in sys.argv[1:] if a != '--dry-run']
    dry = '--dry-run' in sys.argv
    if not args:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    t1 = t2 = files = 0
    for a in args:
        p = pathlib.Path(a)
        src = p.read_text(encoding='utf-8')
        out, n1, n2 = fix(src)
        if n1 or n2:
            files += 1
            t1 += n1
            t2 += n2
            print('  %-60s ①%d ②%d' % (a, n1, n2))
            if not dry:
                p.write_text(out, encoding='utf-8')
    print('[볼드 치환] %d파일 · ① 낫표 밖으로 %d곳 · ② 조사 안으로 %d곳%s'
          % (files, t1, t2, ' (예행)' if dry else ''))
    print('  ★ 반드시 check-md-rendering.mjs 로 확인해라 — 이 도구는 후보를 줄일 뿐이다.')


if __name__ == '__main__':
    main()
