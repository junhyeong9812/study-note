# python/syntax/42-modules-packages-and-import — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **줄의 순서**가 답이다 — 어느 파일의 어느 줄이 몇 번째로 찍히나.
> ★★★ 2번은 **격자 24칸을 하나씩** 채우고 마지막 줄의 숫자까지 적는다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 파일이 여럿인 문항은 **실험 디렉토리에 `cd` 해서** 주어진 명령으로 던진다.
> ★ 선행 — 목록의 선행 칸은 비어 있다. 가까운 이웃은 [21](../21-scope-legb-global-nonlocal/1-question.md)(스코프).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 서로를 import 하는 두 파일의 로그 (예측)

```text
세 파일이 한 디렉토리에 있다. 그 디렉토리에서 python3 -m omain 을 던진다.
```

```python
# oa.py
print("oa : 몸통 시작")
import ob
print("oa : import ob 다음 줄")


def f():
    return "f>" + ob.g()


TAG = "A"
print("oa : 몸통 끝")
```

```python
# ob.py
import sys

print("ob : 몸통 시작")
print("ob : 'oa' in sys.modules =", "oa" in sys.modules)
half = sys.modules["oa"]
print("ob : 그 oa 에 든 이름 =", sorted(k for k in vars(half) if not k.startswith("__")))
import oa
print("ob : import oa 가 준 것 is sys.modules['oa'] =", oa is half)


def g():
    return "g>" + oa.TAG
```

```python
# omain.py
import oa

print("omain : oa 에 든 이름 =", sorted(k for k in vars(oa) if not k.startswith("__")))
print("omain :", oa.f())
```

### 2. ★★★ 가져오는 방식 × 진입점 (예측)

```text
두 표의 칸마다 출력(f>g>A 따위) 또는 예외 종류를 적는다. "--- 예외 문구 ---" 아래 줄들과 마지막 줄의 N / M 도 적는다.
```

```python
# e42_grid.py
import os
import subprocess
import sys
import tempfile

# ca.py 가 cb 를 가져오는 방식 셋
A_STYLES = [
    ("맨 위 import cb", "import cb\ndef f():\n    return 'f>' + cb.g()\nTAG = 'A'\n"),
    ("맨 위 from cb import g", "from cb import g\ndef f():\n    return 'f>' + g()\nTAG = 'A'\n"),
    ("함수 안 import cb", "def f():\n    import cb\n    return 'f>' + cb.g()\nTAG = 'A'\n"),
]
# cb.py 가 ca 를 가져오는 방식 넷
B_STYLES = [
    ("맨 위 import ca · 함수에서 씀", "import ca\ndef g():\n    return 'g>' + ca.TAG\n"),
    ("맨 위 import ca · 맨 위에서 씀", "import ca\nSEEN = ca.TAG\ndef g():\n    return 'g>' + SEEN\n"),
    ("맨 위 from ca import TAG", "from ca import TAG\ndef g():\n    return 'g>' + TAG\n"),
    ("함수 안 import ca", "def g():\n    import ca\n    return 'g>' + ca.TAG\n"),
]
ENTRIES = ["import ca", "import cb"]


def cell(tmp, a_src, b_src, entry):
    with open(os.path.join(tmp, "ca.py"), "w") as fh:
        fh.write(a_src)
    with open(os.path.join(tmp, "cb.py"), "w") as fh:
        fh.write(b_src)
    code = entry + "\nimport ca\nprint(ca.f())"
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if r.returncode == 0:
        return r.stdout.strip(), None
    last = r.stderr.strip().splitlines()[-1].replace(tmp, ".")
    return last.split(":")[0], last


broken = total = 0
messages = []
with tempfile.TemporaryDirectory() as tmp:
    for entry in ENTRIES:
        print("--- 들어가는 문 : %s ---" % entry)
        print("%-30s | %-22s | %-22s | %s" % ("cb 쪽 \\ ca 쪽", *[a for a, _ in A_STYLES]))
        for b_label, b_src in B_STYLES:
            row = []
            for a_label, a_src in A_STYLES:
                shown, msg = cell(tmp, a_src, b_src, entry)
                total += 1
                if msg:
                    broken += 1
                    if msg not in messages:
                        messages.append(msg)
                row.append(shown)
            print("%-30s | %-22s | %-22s | %s" % (b_label, *row))
print("--- 예외 문구 ---")
for m in messages:
    print(m)
print("깨진 칸 %d / %d" % (broken, total))
```

### 3. ★★ 받아 넘긴 뒤의 대장 (예측)

```text
세 파일이 한 디렉토리에 있다. 그 디렉토리에서 python3 -m pmain 을 던진다.
```

```python
# pa.py
print("pa : 몸통 시작")
import pb
TAG = "A"
```

```python
# pb.py
print("pb : 몸통 시작")
from pa import TAG
print("pb : from pa import TAG 다음 줄")
```

```python
# pmain.py
import os
import sys

for attempt in (1, 2):
    try:
        import pa
    except ImportError as exc:
        print("pmain %d :" % attempt, type(exc).__name__ + ":", str(exc).replace(os.getcwd(), "."))
    print("pmain %d : 'pa' in sys.modules =" % attempt, "pa" in sys.modules, "· 'pb' =", "pb" in sys.modules)
```

### 4. ★★★ 진입 모듈을 다시 import 하면 (예측)

```text
e42_twice/ 아래에 pkgm/__init__.py(빈 파일) · pkgm/mainmod.py · pkgm/usemod.py 가 있다.
e42_twice/ 에서 두 명령을 각각 던진다.  ①  python3 -m pkgm.mainmod   ②  python3 pkgm/mainmod.py
```

```python
# mainmod.py
import sys

print("mainmod 몸통 실행 : __name__ =", __name__, file=sys.stderr)


class Token:
    pass


if __name__ == "__main__":
    import pkgm.usemod
    tok = Token()
    print("usemod.check(Token()) =", pkgm.usemod.check(tok), file=sys.stderr)
    print("sys.modules['__main__'] is sys.modules['pkgm.mainmod'] =",
          sys.modules["__main__"] is sys.modules["pkgm.mainmod"], file=sys.stderr)
```

```python
# usemod.py
from pkgm.mainmod import Token


def check(obj):
    return isinstance(obj, Token)
```

### 5. ★★ 같은 파일을 두 방식으로 (예측)

```text
e42_rel/ 아래에 pkgr/__init__.py(빈 파일) · pkgr/util42r.py · pkgr/tool42r.py 가 있다.
e42_rel/ 에서  ①  python3 pkgr/tool42r.py   ②  python3 -m pkgr.tool42r
```

```python
# util42r.py
NAME = "util42r"
```

```python
# tool42r.py
import sys

print("tool42r : __name__ =", __name__, "· __package__ =", repr(__package__), file=sys.stderr)
from . import util42r
print("tool42r : util42r.NAME =", util42r.NAME, file=sys.stderr)
```

### 6. ★★ `__init__.py` 가 없는 두 디렉토리 (예측)

```text
e42_ns/
  nsa/space42/alpha42.py      (__init__.py 없음)
  nsb/space42/beta42.py       (__init__.py 없음)
  reg42/__init__.py
  reg42/leaf42.py
  nsmain.py                   e42_ns/ 에서 python3 -m nsmain
```

```python
# alpha42.py
NAME = "alpha42 (nsa 쪽)"
```

```python
# beta42.py
NAME = "beta42 (nsb 쪽)"
```

```python
# __init__.py
print("reg42/__init__.py 몸통 실행")
```

```python
# leaf42.py
print("reg42/leaf42.py 몸통 실행")
```

```python
# nsmain.py
import os
import sys

sys.path[1:1] = ["nsa", "nsb"]

import space42.alpha42
import space42.beta42

print("[1] __init__.py 없는 디렉토리 둘")
print("  space42.alpha42.NAME :", space42.alpha42.NAME)
print("  space42.beta42.NAME  :", space42.beta42.NAME)
print("  space42.__file__     :", getattr(space42, "__file__", "속성 없음"))
print("  __spec__.origin      :", space42.__spec__.origin)
print("  type(__path__)       :", type(space42.__path__).__name__)
print("  __path__ 의 자리들     :", [os.path.relpath(p) for p in space42.__path__])

print("[2] __init__.py 가 있는 패키지의 하위 모듈")
import reg42.leaf42
print("  reg42.__file__       :", os.path.relpath(reg42.__file__))
print("  type(__path__)       :", type(reg42.__path__).__name__)
```

### 7. ★★★ `import X` 와 `from X import n` 이 가르는 것 (왜)

* 2번 격자의 진입점 `import ca` 표에서 **「맨 위 import ca · 함수에서 씀」 행과 「맨 위 from ca import TAG」 행의 결과**를 **반쯤 찬 모듈**이라는 말로 설명하라.
* 진입점을 `import cb` 로 바꾼 아래 표의 결과를 **위 표와 견주어** 설명하라.

### 8. ★★ 같은 순환을 세 언어에 (경계)

* Go · Python · JS(ESM) · JS(CommonJS) 가 순환에서 「아직 없는 이름」을 만났을 때 — **각각 무엇을 내고, 언제 알게 되나**?
* 그중 **가장 조용한 것**은 무엇이고, 무엇이 그것을 겨우 알려 주나?

### 9. 층 가르기 (경계)

* 「몸통 실행 전에 `sys.modules` 에 넣는다」·「`(most likely due to a circular import)` 꼬리」·「이름 공간 패키지의 `__path__` 타입 이름이 `_NamespacePath`」 —
  각각 **언어 보장 · CPython 구현** 중 어디인가?
* ★ 4번에서 **`-m` 과 스크립트 실행**이 `sys.path[0]` 에 넣는 것은 각각 무엇인가 — 그것이 ②의 예외 종류를 어떻게 정했나?

### 10. 이웃 주제와의 경계 (연결)

* ★ [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 「모듈 전역 스코프」와 1번에서 `ob` 가 찍은 **「그 oa 에 든 이름」 줄의 값**은 어떻게 이어지나?
* ★ [Go 01번](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md)이 순환 import 를 「이 주제에서 유일하게 안전한 실수」라 부른 이유를, 2번 격자의 **24칸**과 견주어 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
