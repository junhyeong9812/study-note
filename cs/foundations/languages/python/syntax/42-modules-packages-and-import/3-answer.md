# python/syntax/42-modules-packages-and-import — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 대비로 `go1.27.1`·node `v18.19.1`. 지어낸 출력은 없다.
> 파일이 여럿인 실험은 **실험 디렉토리를 새로 복사해 `cd` 하고** 배너의 명령으로 던졌다. 절대 경로가 박힌 블록은 배너의 `sed` 가 `.` 로 바꿨다.

## 정답

### 1. `oa` 시작 → `ob` 전체 → `oa` 나머지 — `ob` 가 본 `oa` 는 빈 모듈이고 같은 객체다

**출력**

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

```text
===== cd e42_order && python3 -m omain =====
oa : 몸통 시작
ob : 몸통 시작
ob : 'oa' in sys.modules = True
ob : 그 oa 에 든 이름 = []
ob : import oa 가 준 것 is sys.modules['oa'] = True
oa : import ob 다음 줄
oa : 몸통 끝
omain : oa 에 든 이름 = ['TAG', 'f', 'ob']
omain : f>g>A
(exit 0)
```

**왜 그런가**

* ★★★ `oa : 몸통 시작` 다음에 곧바로 **`ob` 의 줄 넷**이 온다 — `import ob` 줄에서 **`ob` 로 뛰어가** 그 몸통을 끝까지 돈다.
* ★★★ `ob` 가 본 `oa` — **`'oa' in sys.modules` 가 `True`**, 그런데 **든 이름은 `[]`**. 몸통 실행 **전에** 대장에 넣었기 때문이다.
* ★★ **`import oa` 가 준 것 `is sys.modules['oa']` 가 `True`**, 그리고 **`oa : 몸통 시작` 은 한 번뿐** — 다시 실행하지 않고 **반쯤 찬 그 객체**를 줬다.
* ★ `ob` 는 `oa.TAG` 를 **함수 `g` 안에서만** 읽으므로 안 깨졌고, `omain` 이 부를 때는 다 차 있다 → `f>g>A`.

### 2. `깨진 칸 7 / 24` — 진입점 `ca` 에서 넷, `cb` 에서 셋

**출력**

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

```text
===== python3 - <e42_grid.py =====
--- 들어가는 문 : import ca ---
cb 쪽 \ ca 쪽                    | 맨 위 import cb          | 맨 위 from cb import g   | 함수 안 import cb
맨 위 import ca · 함수에서 씀         | f>g>A                  | f>g>A                  | f>g>A
맨 위 import ca · 맨 위에서 씀        | AttributeError         | AttributeError         | f>g>A
맨 위 from ca import TAG         | ImportError            | ImportError            | f>g>A
함수 안 import ca                 | f>g>A                  | f>g>A                  | f>g>A
--- 들어가는 문 : import cb ---
cb 쪽 \ ca 쪽                    | 맨 위 import cb          | 맨 위 from cb import g   | 함수 안 import cb
맨 위 import ca · 함수에서 씀         | f>g>A                  | ImportError            | f>g>A
맨 위 import ca · 맨 위에서 씀        | f>g>A                  | ImportError            | f>g>A
맨 위 from ca import TAG         | f>g>A                  | ImportError            | f>g>A
함수 안 import ca                 | f>g>A                  | f>g>A                  | f>g>A
--- 예외 문구 ---
AttributeError: partially initialized module 'ca' has no attribute 'TAG' (most likely due to a circular import)
ImportError: cannot import name 'TAG' from partially initialized module 'ca' (most likely due to a circular import) (./ca.py)
ImportError: cannot import name 'g' from partially initialized module 'cb' (most likely due to a circular import) (./cb.py)
깨진 칸 7 / 24
(exit 0)
```

**왜 그런가**

* ★★★ **진입점 `import ca`** — `ca` 가 먼저 시작해 반쯤 찬 쪽이 된다. `cb` 가 **몸통 실행 중에 `ca` 에서 이름을 꺼내는** 두 행이 깨진다 —
  `from ca import TAG` 는 **`ImportError`**, 맨 위의 `ca.TAG` 는 **`AttributeError`**. `ca` 쪽이 **함수 안 import** 인 열은 `ca` 몸통이 끝난 뒤에 `cb` 를 부르므로 **통과**.
* ★★★ **진입점 `import cb`** — 이번엔 `cb` 가 반쯤 찬 쪽이다. `ca` 의 **`from cb import g`** 열만 깨진다(`cannot import name 'g' from partially initialized module 'cb'`).
* ★★ **「함수 안 import」 는 행이든 열이든 24칸 중 한 칸도 안 깨졌다.**
* ★ 예외 문구 셋 모두 **`(most likely due to a circular import)`** — 인터프리터가 **반쯤 찬 모듈**임을 알고 붙이는 힌트다.

### 3. `pb` 에서 `ImportError` — `pa`·`pb` 둘 다 대장에서 빠지고, 두 번째 시도는 처음부터 다시 돌아 또 깨진다

**출력**

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

```text
===== cd e42_fail && python3 -m pmain =====
pa : 몸통 시작
pb : 몸통 시작
pmain 1 : ImportError: cannot import name 'TAG' from partially initialized module 'pa' (most likely due to a circular import) (./pa.py)
pmain 1 : 'pa' in sys.modules = False · 'pb' = False
pa : 몸통 시작
pb : 몸통 시작
pmain 2 : ImportError: cannot import name 'TAG' from partially initialized module 'pa' (most likely due to a circular import) (./pa.py)
pmain 2 : 'pa' in sys.modules = False · 'pb' = False
(exit 0)
```

**왜 그런가**

* ★★★ `pb` 의 `from pa import TAG` 시점에 `pa` 는 `import pb` 줄에서 멈춰 있어 **`TAG` 가 없다** → `ImportError`. `pb : from pa import TAG 다음 줄` 은 **안 찍혔다.**
* ★★ 예외가 `pb` 몸통을 뚫고 `pa` 몸통도 뚫었으니 **둘 다 실패한 모듈**이다 — 레퍼런스대로 **둘 다 `sys.modules` 에서 빠졌다**(`False`·`False`).
* ★★ 그래서 **두 번째 시도(`pmain 2`)에서 `pa : 몸통 시작` 이 다시 찍혔다** — 대장에 없으니 **처음부터 다시** 실행하고, **같은 자리에서 또** 깨진다.

### 4. ① 몸통이 두 번 · `check` 가 `False` · 두 모듈은 다른 객체 / ② `ModuleNotFoundError: No module named 'pkgm'`

**출력**

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

```text
===== cd e42_twice && python3 -m pkgm.mainmod =====
mainmod 몸통 실행 : __name__ = __main__
mainmod 몸통 실행 : __name__ = pkgm.mainmod
usemod.check(Token()) = False
sys.modules['__main__'] is sys.modules['pkgm.mainmod'] = False
(exit 0)
```

```text
===== cd e42_twice && python3 pkgm/mainmod.py 2>&1 | sed "s#$PWD#.#g" =====
mainmod 몸통 실행 : __name__ = __main__
Traceback (most recent call last):
  File "./pkgm/mainmod.py", line 11, in <module>
    import pkgm.usemod
ModuleNotFoundError: No module named 'pkgm'
(exit 1)
```

**왜 그런가**

* ★★★ ① — `-m` 으로 돌린 `mainmod` 는 대장에 **`__main__`** 으로 적힌다. `usemod` 의 `from pkgm.mainmod import Token` 은 **`pkgm.mainmod`** 라는 이름을 찾는데 **없으니 새로 실행**한다 —
  몸통이 **두 번**(`__main__` · `pkgm.mainmod`), **`Token` 클래스가 둘.** `tok` 은 첫째 `Token` 의 인스턴스이고 `check` 는 둘째 `Token` 으로 검사하니 **`False`**.
* ★★ ② — 스크립트로 돌리면 `sys.path[0]` 이 **`pkgm/`** 이라 그 **바깥의 `pkgm` 패키지가 안 보인다.** 몸통은 한 번 돌고 `import pkgm.usemod` 에서 죽는다.
* ★ 두 블록 모두 `print` 를 **`sys.stderr`** 로 찍었다 — ②가 트레이스백으로 끝나므로 같은 흐름이어야 순서가 고정된다.

### 5. ① `__package__ = None` → `attempted relative import with no known parent package` / ② `__package__ = 'pkgr'` → 된다

**출력**

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

```text
===== cd e42_rel && python3 pkgr/tool42r.py 2>&1 | sed "s#$PWD#.#g" =====
tool42r : __name__ = __main__ · __package__ = None
Traceback (most recent call last):
  File "./pkgr/tool42r.py", line 4, in <module>
    from . import util42r
ImportError: attempted relative import with no known parent package
(exit 1)
```

```text
===== cd e42_rel && python3 -m pkgr.tool42r =====
tool42r : __name__ = __main__ · __package__ = 'pkgr'
tool42r : util42r.NAME = util42r
(exit 0)
```

**왜 그런가**

* ★★★ **둘 다 `__name__` 이 `__main__`** 이다. 가르는 것은 **`__package__`** — 스크립트 실행은 `None`, `-m` 은 `'pkgr'`.
  상대 import 의 `.` 은 **`__package__` 기준**으로 풀리므로 ①은 기준이 없다.
* ★ ①의 `File "./pkgr/tool42r.py"` 는 원래 절대 경로다 — 배너의 `sed` 가 `.` 로 바꿨다.

### 6. 두 디렉토리가 한 패키지로 · `__file__` 이 `None` · `__path__` 가 둘 · `__init__.py` 가 하위 모듈보다 먼저

**출력**

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

```text
===== cd e42_ns && python3 -m nsmain =====
[1] __init__.py 없는 디렉토리 둘
  space42.alpha42.NAME : alpha42 (nsa 쪽)
  space42.beta42.NAME  : beta42 (nsb 쪽)
  space42.__file__     : None
  __spec__.origin      : None
  type(__path__)       : _NamespacePath
  __path__ 의 자리들     : ['nsa/space42', 'nsb/space42']
[2] __init__.py 가 있는 패키지의 하위 모듈
reg42/__init__.py 몸통 실행
reg42/leaf42.py 몸통 실행
  reg42.__file__       : reg42/__init__.py
  type(__path__)       : list
(exit 0)
```

**왜 그런가**

* ★★★ `nsa/space42` 와 `nsb/space42` 가 **한 이름 공간 패키지 `space42`** 로 합쳐졌다 — `__path__` 에 **자리 둘**, 타입은 **`_NamespacePath`**.
* ★★ **`__file__`·`__spec__.origin` 이 `None`** — 실행할 `__init__.py` 가 없다.
* ★★ `import reg42.leaf42` 한 줄에 **`reg42/__init__.py` 몸통 → `leaf42.py` 몸통** 순서. 정규 패키지의 `__path__` 는 `list`.
* ★ 그 두 줄이 `[2]` 제목 **바로 뒤**에 찍힌 것은 import 줄이 **그 `print` 다음**에 있기 때문이다 — import 가 곧 실행이다.

### 7. 모듈 **객체**만 받아 두면 속성은 부를 때 찾는다 — `from` 은 **그 줄에서** 꺼낸다 · 먼저 시작한 쪽이 반쯤 찬 쪽이다

**왜 그런가**

* ★★★ 진입점 `import ca` 에서 `cb` 가 실행될 때 `ca` 는 **`import cb` 줄에서 멈춘 반쯤 찬 모듈**이다(1번의 `[]`).
  **`import ca`** 는 그 **객체를 이름에 묶기만** 하고, `ca.TAG` 는 **`g()` 를 부를 때** 찾는다 — 그때는 다 찼다. 그래서 통과.
  **`from ca import TAG`** 는 **그 줄에서 `TAG` 를 꺼낸다** — 반쯤 찬 `ca` 에 `TAG` 가 없으니 `ImportError`.
* ★★ **반쯤 찬 쪽은 「먼저 시작한 쪽」** 이다. 진입점을 `import cb` 로 바꾸면 `cb` 가 반쯤 찬 쪽이 되고, 이번엔 **`ca` 가 `cb` 에서 꺼내는 칸**(`from cb import g`)이 깨진다.
  ★ **같은 코드의 깨짐이 「누가 먼저 import 되나」에 달렸다** — 테스트와 운영의 진입점이 다르면 한쪽에서만 터진다.

### 8. Go 빌드 거부 · Python 그 줄에서 예외 · ESM `ReferenceError`(TDZ) · CommonJS 조용히 `undefined` — 경고 한 줄

**왜 그런가**

* ★★★ **Go** — `import cycle not allowed`, `(exit 1)`. **실행 전에** 안다. 격자 같은 것이 원리상 없다.
* ★★ **Python** — 반쯤 찬 모듈을 주고, 없는 이름을 꺼내면 **`ImportError`/`AttributeError`**(순환 힌트 꼬리까지). **실행 중, 그 줄에서** 안다.
* ★★ **JS ESM** — 바인딩은 있지만 초기화 전이라 **`ReferenceError: Cannot access 'TAG' before initialization`**. 실행 중에 안다.
* ★★★ **가장 조용한 것은 CommonJS** — 반쯤 찬 `exports` 에서 `a.TAG` 가 **`undefined`** 로 흘러 **`f>g>undefined`** 라는 **틀린 값으로 계속** 돈다.
  알려 주는 것은 node 의 **경고 한 줄**(`Accessing non-existent property 'TAG' of module exports inside circular dependency`) 뿐이다 — 그 줄의 `(node:NNN)` PID 는 실행마다 바뀐다.

### 9. 보장 · 구현 · 구현 — `-m` 은 현재 디렉토리, 스크립트는 스크립트의 디렉토리

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 몸통 실행 **전에** `sys.modules` 에 넣는다 | **언어 보장** | 레퍼런스 — *"The module will exist in `sys.modules` before the loader executes the module code."* |
| `(most likely due to a circular import)` 꼬리 | **CPython 구현** | 실행 — 문구는 레퍼런스에 없다 |
| `__path__` 타입 이름 `_NamespacePath` | **CPython 구현** | 실행 — 레퍼런스는 「리스트가 아닌 반복 가능 객체」까지만 말한다 |

* ★★ `-m` 은 `sys.path[0]` 에 **현재 디렉토리**를, 스크립트 실행은 **스크립트가 있는 디렉토리(`pkgm/`)** 를 넣는다.
  그래서 ①은 `pkgm` 이 보여 `usemod` 까지 가서 **두 벌**이 됐고, ②는 `pkgm` 이 **안 보여** `ModuleNotFoundError` 였다.

### 10. 모듈 전역 = 그 모듈 객체의 속성 — 몸통이 멈춘 줄까지만 찬다 · Go 는 「어떻게 import 했나」로 결과가 안 갈린다

**왜 그런가**

* ★★ [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 **모듈 전역 스코프**에 들어가는 이름은 **몸통의 대입·`def`·`import` 가 실행될 때** 생긴다.
  1번에서 `oa` 몸통이 **`import ob` 줄에서 멈춰 있으니** 그 아래의 `def f`·`TAG = "A"` 가 아직 안 돌았고, 그래서 모듈 객체의 속성 목록(`vars`)이 **`[]`** 다.
* ★★★ [Go 01번](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md)의 「유일하게 안전한 실수」 — 순환이 **컴파일 에러**라 조용히 지나가지 않는다.
  파이썬은 같은 순환이 **24칸 중 17칸에서 조용히 통과**하고 나머지 7칸만 **실행 중에** 깨진다 — 그리고 **어느 7칸인지가 진입점에 따라 바뀐다.** Go 에는 그런 칸 자체가 없다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 실행 순서 로그 | `cd e42_order && python3 -m omain` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | 빈 모듈 · 같은 객체 |
| 순환 격자 | `python3 - <e42_grid.py`(임시 디렉토리에 파일을 써 가며 24번) | 3 | **깨진 칸 7 / 24** |
| 실패 뒤의 대장 | `cd e42_fail && python3 -m pmain` | 3 | 둘 다 빠진다 |
| `__main__` 두 번 | `cd e42_twice && python3 -m pkgm.mainmod` · `python3 pkgm/mainmod.py` | 3씩 | 두 번 실행 · `False` / `ModuleNotFoundError` |
| 상대 import | `cd e42_rel && python3 pkgr/tool42r.py` · `python3 -m pkgr.tool42r` | 3씩 | `__package__` 가 가른다 |
| 이름 공간 패키지 | `cd e42_ns && python3 -m nsmain` | 3 | 자리 둘 · `__file__` 이 `None` |
| Go | `cd e42_go && go build -o /dev/null .` | 3 | `import cycle not allowed` |
| node | `cd e42_node && node esmain42.mjs` · `node cjmain42.cjs` | 3씩 | `ReferenceError` / `undefined` + 경고 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| 예외 **문구**와 순환 힌트 꼬리 | 구현이다 |
| `_NamespacePath` | 구현이다 |

★ **안 흔들리는 칸** — 격자 칸 · **「7 / 24」** · 로그 줄의 순서 · 예외 종류 · `(exit N)`.
★ **흔들리는 칸** — node 경고의 `(node:NNN)` PID(재대조에서 정규화 규칙 하나로 뺐다) · 실험 디렉토리의 절대 경로(배너의 `sed`).
