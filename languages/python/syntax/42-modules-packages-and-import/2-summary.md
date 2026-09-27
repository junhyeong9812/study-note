# python/syntax/42-modules-packages-and-import — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [언어 레퍼런스 — The import system(3.12)](https://docs.python.org/3.12/reference/import.html) —
>   *"The module will exist in `sys.modules` before the loader executes the module code. This is crucial because the module code may (directly or indirectly) import itself"* ·
>   *"If loading fails, the failing module – and only the failing module – gets removed from `sys.modules`"* ·
>   정규 패키지의 *"`__init__.py` file is implicitly executed"* · 이름 공간 패키지 절(*"a composite of various portions"*, `__path__` 가 *"custom iterable type"*)
> - [튜토리얼 — Modules(3.12)](https://docs.python.org/3.12/tutorial/modules.html) — *"They are executed only the first time the module name is encountered in an import statement"* ·
>   *"Since the name of the main module is always `"__main__"`, modules intended for use as the main module of a Python application must always use absolute imports."*
> - 대비용 Go 명세 문장은 이 문서가 열지 않았다 — [Go 01번](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md)이 인용한 것을 가리킨다.
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 하나(이 주제는 3.11 과 갈리는 자리를 찾지 않았다). 대비로 **`go1.27.1`**·**node `v18.19.1`** 을 한 번씩 던졌다.\
> ★★ **파일이 여럿인 실험은 실험마다 디렉토리를 새로 복사하고 `cd` 해서** `python3 -m …` 로 던졌다(배너의 `cd <실험> && …`).
> 트레이스백에 **그 디렉토리의 절대 경로가 박히는 블록 셋**은 경로를 `.` 로 바꿨고, 배너에 그 `sed` 를 적었다 — **배너대로 던지면 같은 글자가 나온다.**\
> ★ 파일 이름은 **실험마다 다르게** 지었다(`oa.py`·`pa.py`·`ca.py` …) — 같은 이름이 둘이면 소스 대조가 판정 불가가 된다.\
> ★ 격자 하나(동작 2)는 파일을 **스크립트가 임시 디렉토리에 써 가며** 24번 던진다 — 그 스크립트의 전문이 곧 소스다.\
> **버전** — 명시적 상대 import(`from . import x`)는 **2.5**(PEP 328), 이름 공간 패키지는 **3.3**(PEP 420).
> 순환 import 예외 문구의 꼬리 `(most likely due to a circular import)` 는 **이 판(3.12.3)에서 본 문구**다 — 몇 판부터인지는 적지 않는다.\
> ★ **구현 대 언어 보장 한 줄** — **「실행 전에 `sys.modules` 에 넣는다 · 실패한 모듈만 뺀다 · 몸통은 처음 import 때 한 번」** 이 레퍼런스의 보장이고,
> **예외 문구**(`partially initialized module …`)는 CPython 의 것이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ 실험 디렉토리의 **절대 경로** — 배너의 `sed` 로 `.` 가 된다 | ★★ 격자의 칸 · 마지막 줄 **「깨진 칸 N / M」** |
> | ★ node 경고의 **PID**(`(node:NNN)`) — 재대조에서 정규화 규칙 하나로 뺐다 | 로그 줄의 **순서** |
> | 판이 오르면 예외 **문구** | 예외 **종류** · `(exit N)` · `go build` 의 `import cycle not allowed` 경로 줄 |
>
> **선행** — 목록의 선행 칸은 비어 있다. 가장 가까운 이웃은 [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md)(★ **모듈 전역 스코프** —
> 이 주제에서 그 전역은 **모듈 객체의 속성**으로 보이고, 반쯤 실행된 모듈은 **반쯤 찬 전역**이다).

## 한눈에 — 쉽게 말하면

**`import` 는 「도서관 대출 대장」이다.** 책(모듈)을 처음 빌리러 오면 사서가 **대장에 이름부터 적고**(`sys.modules`) 그다음 **책을 인쇄한다**(몸통 실행).
두 번째부터는 **대장을 보고 그 책을 그대로** 내준다 — 다시 인쇄하지 않는다.

* 순환 import 는 **인쇄 중인 책을 빌리러 오는 것**이다 — 대장에는 이름이 있으니 **반쯤 인쇄된 책**을 내준다.
* 그 책의 **아직 인쇄 안 된 쪽**을 펴 보면 터진다 — `from a import X`·맨 위에서 `a.X` 를 읽는 것.
* 대장의 이름표가 다르면 **같은 책을 두 번 인쇄한다** — `__main__` 과 `pkg.mod` 가 그것이다.

```text
   import oa                         sys.modules (대출 대장)
     |                               +--------------------------+
     +-- 1. 대장에 'oa' 를 먼저 적는다 -->| 'oa' : 빈 모듈 객체         |  <-- 몸통 실행 전
     +-- 2. oa 의 몸통을 위에서부터 실행          |                          |
     |      import ob  -------------->| 'ob' : 빈 모듈 객체         |
     |        ob 의 몸통 실행                  |                          |
     |          import oa  --> 대장에 있다 -> ★ 반쯤 찬 oa 를 그대로 받는다 (다시 실행 안 함)
     |          from oa import TAG --> ★ TAG 는 아직 없다 -> ImportError
     |        ob 끝                            |                          |
     +-- oa 의 나머지 실행 (TAG = "A")          | 'oa' : TAG, f 가 찬다      |
                                         +--------------------------+
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 대출 대장 | `sys.modules`(이름 → 모듈 객체) | `'oa' in sys.modules` |
| ★ **대장에 먼저 적고** 인쇄한다 | 몸통 실행 **전에** 모듈 객체를 넣는다 | 순환 중에 `sys.modules['oa']` 가 **빈 모듈** |
| 인쇄 | 모듈 몸통의 실행(한 번) | 몸통의 `print` 가 한 번 찍힌다 |
| 반쯤 인쇄된 책 | 부분 초기화 모듈(partially initialized) | 예외 문구에 그대로 나온다 |
| 인쇄 실패한 책은 대장에서 지운다 | 실패한 모듈은 `sys.modules` 에서 빠진다 | 실패 뒤 `'pa' in sys.modules` 가 `False` |
| ★ 이름표가 다른 같은 책 | `__main__` 과 `pkg.mainmod` | 몸통이 **두 번** 찍힌다 |
| 여러 서가에 흩어진 한 시리즈 | 이름 공간 패키지 | `__path__` 에 자리가 **둘** |
| 인쇄 전에 대출 자체를 거부하는 도서관 | Go 컴파일러 | `import cycle not allowed` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**모델 파일 둘이 서로를 `from … import` 했더니 `ImportError` 가 나는데, 진입점을 바꾸면 안 난다**」와
「**`python pkg/mod.py` 로 돌리면 `attempted relative import` 로 죽는데 `python -m pkg.mod` 는 된다**」가 그것이다.\
앞엣것은 **반쯤 인쇄된 책의 빈 쪽을 편 것**이고, 뒤엣것은 **대장에 적힌 이름이 `__main__` 이라 어느 시리즈인지 모르는 것**이다.

> **모듈(module)** — `.py` 파일 하나를 실행해 만든 **객체**. 그 파일의 전역 이름들이 모듈의 속성이 된다.\
> 예: `import oa` 뒤 `oa.f` 는 `oa.py` 에서 정의한 `f`.

> **패키지(package)** — 하위 모듈을 담는 모듈. `__path__` 속성이 있다. `__init__.py` 가 있으면 **정규**, 없으면 **이름 공간** 패키지.\
> 예: `pkgr/__init__.py` 가 있으면 `pkgr` 는 정규 패키지.

> **`sys.modules`** — 이미 import 한 모듈의 **캐시 dict**. `import` 는 **여기부터** 본다.\
> 예: 두 번째 `import oa` 는 파일을 다시 읽지 않고 `sys.modules['oa']` 를 준다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 순환 import 격자 창이다.** 두 모듈의 가져오는 방식 **3 × 4** 를 **진입점 2** 곳에서 던져 **24칸**을 채우고 **깨진 칸을 스크립트가 센다.**
그리고 ② **실행 순서 로그**가 그 격자의 **왜**를 그림으로 보여 준다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **순환 import 격자**(24칸) | **어느 조합·어느 진입점에서** 깨지나 | 왜 깨지나 |
| ② ★★★ **실행 순서 로그**(몸통마다 `print`) | 몸통이 **언제 · 몇 번** 실행되나, 그 순간 모듈에 **무엇이 들어 있나** | — |
| ③ ★★ **`sys.modules` 조회** | 순환 중·실패 뒤에 **대장에 무엇이 있나** | — |
| ④ ★★ **`__name__`·`__package__`·`__path__`** | 모듈이 **자기를 누구라고 아나** | — |
| ⑤ ★ **교차 언어 창** — `go build` · node | 같은 순환을 **다른 언어는 어디서 막나** | 그 언어의 런타임 세부 |
| ★ **부적용인 창** — 속도 · import 비용 | — | 「지연 import 가 빠르다」를 **한 번도 재지 않았다** |

★★ **②가 이 주제의 네 번째 창이다.** 격자(①)는 「**깨졌다 / 통과했다**」 만 말한다.
몸통마다 한 줄을 찍으면 **import 가 파일 안의 어느 줄에서 다른 파일로 뛰어갔다 돌아오는지**가 출력 순서로 드러나고,
**반쯤 찬 모듈의 속성 목록**을 그 순간에 찍으면 **「왜 `from … import` 만 깨지나」** 가 한 줄로 보인다.

## 이 주제가 답하려는 질문

1. ★★★ **순환 import 는 언제 깨지나** — 가져오는 방식(맨 위 `import` · `from … import` · 함수 안)과 **진입점**에 따라 어느 칸이 깨지나.
2. ★★ **`import` 는 무엇을 하나** — `sys.modules` 에 **먼저 넣고** 몸통을 **한 번** 실행한다. 그래서 `__main__` 으로 돌린 모듈은 **두 번** 실행될 수 있다.
3. **패키지와 상대 import** — `__init__.py` 의 역할, 스크립트로 돌리면 상대 import 가 깨지는 이유, `__init__.py` 없는 이름 공간 패키지.

★ 첫째가 이 주제의 인출 목표다.
**「반쯤 찬 모듈을 받는다」는 한 문장으로 격자 24칸의 깨짐을 전부 예측할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 실행 순서 — 반쯤 찬 모듈이 대장에 들어간다

**언제 쓰나** — 순환 import 를 처음 만났을 때. 「왜 `import` 는 되는데 `from` 은 안 되지」가 막힐 때.

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

```text
   시간 ▼            oa.py                      ob.py                       sys.modules['oa'] 에 든 이름
   ─────────────────────────────────────────────────────────────────────────────────────────────
   ①  oa 몸통 시작    print                                                    []   (대장에 먼저 들어갔다)
   ②                 import ob  ──────────▶   ob 몸통 시작
   ③                                           'oa' in sys.modules -> True     []
   ④                                           import oa  -> 대장의 oa 를 받는다   []   ★ 같은 객체 (is -> True)
   ⑤                                           def g  (oa.TAG 는 아직 안 읽는다)
   ⑥                 ◀────────── ob 끝
   ⑦  import ob 다음 줄 · def f · TAG = "A"                                     ['TAG', 'f', 'ob']
   ⑧  omain 이 oa.f() -> ob.g() -> oa.TAG       ★ 이때는 다 찼다 -> f>g>A
```

그림 해설.

* ★★★ **③** — `ob` 몸통이 돌기 시작했을 때 **`'oa' in sys.modules` 가 이미 `True`** 다. 그런데 **그 `oa` 에 든 이름은 `[]`** — 몸통이 `import ob` 줄에서 멈춰 있으니 아래 줄의 `f`·`TAG` 가 **아직 없다.**
  ★ 레퍼런스 — *"The module will exist in `sys.modules` before the loader executes the module code."*
* ★★★ **④** — `ob` 안의 `import oa` 는 **`oa` 를 다시 실행하지 않고** 대장의 그 **빈 객체**를 준다(`is` 가 `True`). **`oa 몸통 시작` 이 한 번만 찍힌 것**이 그 증거다.
  ★ 대장에 먼저 넣는 이유를 레퍼런스가 적는다 — 넣지 않으면 **무한히 서로를 실행**한다(*"prevents unbounded recursion"*).
* ★★ **⑤** — `ob` 는 `oa.TAG` 를 **함수 `g` 안에서만** 읽는다. 모듈 객체를 받아 두고 **속성은 부를 때 찾으니** 지금 비어 있어도 괜찮다.
* ★★ **⑦·⑧** — `oa` 가 끝까지 돌면 **같은 객체가 채워진다.** `omain` 이 `f()` 를 부르는 시점엔 `ob.g()` 가 `oa.TAG` 를 찾을 수 있다 → `f>g>A`.

**비용** — 순환 import 는 **「언제 무엇을 읽느냐」에 결과가 달리는** 코드를 만든다. 파일 안의 **줄 순서**가 곧 초기화 순서다.

### 2. ★★★ 순환 import 격자 — 방식 3 × 4 × 진입점 2

**언제 쓰나** — 「어떻게 import 해야 순환이 안 깨지나」를 **규칙으로** 외우고 싶을 때.

```text
   ca.py (가져오는 방식 셋)                   cb.py (가져오는 방식 넷)
   ┌──────────────────────────┐            ┌─────────────────────────────────┐
   │ import cb                │            │ import ca        · 함수 g 안에서 ca.TAG │
   │ from cb import g         │   <--->    │ import ca        · 맨 위에서 ca.TAG     │
   │ (함수 f 안에서) import cb  │            │ from ca import TAG                  │
   │ ...                      │            │ (함수 g 안에서) import ca             │
   │ TAG = 'A'   <-- 맨 끝      │            └─────────────────────────────────┘
   └──────────────────────────┘
   진입점  import ca  /  import cb     그 뒤 import ca; print(ca.f())
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

그림 해설.

* ★★★ **마지막 줄 — `깨진 칸 7 / 24`.**
* ★★★ **진입점 `import ca`(위 표)** — 먼저 시작한 `ca` 가 **반쯤 찬 채** `cb` 를 부른다. 그래서 **`cb` 가 `ca` 에서 무엇을 곧바로 꺼내는 행**만 깨진다 —
  **`from ca import TAG`**(`ImportError`) · **맨 위에서 `ca.TAG`**(`AttributeError`). 각각 **`ca` 쪽 앞 두 열**에서 깨지고 **함수 안 import 열은 전부 통과**(`ca` 가 `cb` 를 부르는 순간이 `ca` 가 다 찬 뒤이므로).
* ★★★ **진입점 `import cb`(아래 표)** — 이번엔 `cb` 가 반쯤 찬 쪽이다. 그래서 깨지는 것은 **`ca` 쪽의 `from cb import g` 열**이다(`ImportError: cannot import name 'g' from partially initialized module 'cb'`).
  ★ **같은 두 파일인데 진입점만 바꿔서 깨지는 칸이 옮겨 갔다** — `cb` 의 맨 위 `ca.TAG`·`from ca import TAG` 행은 여기서는 **통과**한다.
* ★★ **「함수 안 import」 행·열은 24칸 중 한 칸도 안 깨졌다** — 몸통 실행 중에 **상대 모듈을 건드리지 않으니** 반쯤 찬 모듈을 볼 일이 없다.
* ★★ **「맨 위 `import` · 함수에서 씀」 행도 진입점 `ca` 에서는 한 칸도 안 깨졌다** — 모듈 **객체**만 받아 두고 속성은 **부를 때** 찾는다(동작 1 의 ⑤).
* ★ **예외 문구 셋** — 둘은 `ImportError`, 하나는 `AttributeError` 인데 **셋 다 `(most likely due to a circular import)`** 를 단다. 인터프리터가 **반쯤 찬 모듈**임을 알고 힌트를 붙인다.

```text
   깨지는 조건 한 줄 — 「몸통이 실행되는 동안, 아직 몸통이 안 끝난 모듈에서 이름을 꺼낸다」

                             몸통 실행 중에 꺼내나?      반쯤 찬 쪽이 그 이름을 이미 만들었나?
   from X import name        ★ 꺼낸다                  아니면 ImportError
   맨 위에서 X.name           ★ 꺼낸다                  아니면 AttributeError
   맨 위 import X (함수에서 씀)  안 꺼낸다 (객체만 받는다)    상관없다
   함수 안 import X            몸통 실행 중에는 import 도 안 한다   상관없다
```

**비용** — 「함수 안 import」 는 격자에서 **가장 안전**했지만, **import 오류가 부를 때까지 미뤄지고** 함수를 부를 때마다 `sys.modules` 를 본다(이 비용은 **재지 않았다**).
구조로 푸는 길 — **둘이 함께 쓰는 것을 제3의 모듈로 뺀다.**

### 3. ★★ 실패하면 — 실패한 모듈은 대장에서 빠진다

**언제 쓰나** — `try: import …` 로 순환 실패를 받아 넘긴 뒤 **다시 import 하면 어떻게 되나**가 막힐 때.

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

* ★★★ `pb` 의 `from pa import TAG` 가 **`ImportError`** — `pb : from pa import TAG 다음 줄` 은 **안 찍혔다.**
* ★★ 받은 뒤 **`'pa'`·`'pb'` 둘 다 `sys.modules` 에 없다(`False`)** — 둘 다 **실패한 모듈**이라 대장에서 빠졌다(`pb` 가 먼저 실패하고, 그 예외가 `pa` 의 몸통을 뚫고 나가 `pa` 도 실패).
  ★ 레퍼런스 — *"If loading fails, the failing module – and only the failing module – gets removed from `sys.modules`."*
* ★★ **두 번째 시도(`pmain 2`)에서 두 몸통이 다시 찍혔다** — 대장에서 빠졌으니 **처음부터 다시** 실행하고, **같은 자리에서 또** 깨진다. 순환 실패는 `try` 로 받아도 **고쳐지지 않는다.**
* ★ 예외 문구 끝의 `(./pa.py)` 는 **파일 경로**다 — 원래는 절대 경로이고, `pmain.py` 가 `os.getcwd()` 를 `.` 로 바꿔 찍었다(소스에 그 줄이 있다).

### 4. ★★★ `__main__` 은 이름표가 다르다 — 같은 파일이 두 번 실행된다

**언제 쓰나** — 「`if __name__ == "__main__":` 아래에서 자기 패키지의 다른 모듈을 import 했더니 **클래스 검사가 이상하다**」가 막힐 때.

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

(`pkgm/__init__.py` 는 **빈 파일**이다 — 블록으로 싣지 않았다.)

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

```text
   python3 -m pkgm.mainmod

   sys.modules
   '__main__'      ─▶ mainmod.py 를 실행한 모듈 ①   Token ①       tok = Token ①()
   'pkgm.mainmod'  ─▶ mainmod.py 를 실행한 모듈 ②   Token ②   ◀── usemod 가 from pkgm.mainmod import Token
                        ★ 같은 파일, 다른 이름표, 두 번 실행
   usemod.check(tok) = isinstance(Token①의 인스턴스, Token②)  ->  False
```

그림 해설.

* ★★★ **첫 블록** — `mainmod 몸통 실행` 이 **두 번** 찍혔다. 한 번은 `__name__ = __main__`, 한 번은 **`pkgm.mainmod`**.
  `usemod` 가 `from pkgm.mainmod import Token` 을 했는데 대장에는 **`__main__` 이라는 이름표만** 있고 `pkgm.mainmod` 는 **없으니 새로 실행한다.**
  ★ 그래서 **`Token` 클래스가 둘** 생겼고 `isinstance(tok, Token)` 이 **`False`** 다. 마지막 줄의 `is` 도 **`False`** — **모듈이 두 벌**이다.
* ★★ **둘째 블록** — `python3 pkgm/mainmod.py` 로 돌리면 **아예 `ModuleNotFoundError: No module named 'pkgm'`** 이다.
  스크립트로 돌리면 `sys.path[0]` 이 **스크립트가 있는 디렉토리(`pkgm/`)** 라서 그 **바깥의 `pkgm` 패키지가 안 보인다.** `-m` 은 **현재 디렉토리**를 넣는다.
* ★ 몸통의 `print` 는 전부 **`sys.stderr`** 로 찍었다 — 둘째 블록이 트레이스백(stderr)으로 끝나므로 **같은 흐름**이어야 순서가 고정된다(규칙 18).

**비용** — **진입점으로 쓸 모듈에는 다른 모듈이 import 할 것(클래스·전역 상태)을 두지 않는다.** 두 벌이 생기면 `isinstance`·전역 캐시·싱글턴이 **조용히 갈린다.**

### 5. ★★ 상대 import — 스크립트로 돌리면 부모가 없다

**언제 쓰나** — `ImportError: attempted relative import with no known parent package` 를 만났을 때.

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

```text
   python3 pkgr/tool42r.py          __name__ = '__main__'   __package__ = None     from . -> 기준이 없다 -> ImportError
   python3 -m pkgr.tool42r          __name__ = '__main__'   __package__ = 'pkgr'   from . -> pkgr       -> 된다
                                    ★ 둘 다 __main__ 이다. 가르는 것은 __package__ 다
```

* ★★★ **스크립트 실행은 `__package__ = None`** — 상대 import 의 `.` 이 **어느 패키지 기준인지** 모른다 → `ImportError: attempted relative import with no known parent package`.
* ★★★ **`-m` 실행은 `__name__` 이 똑같이 `__main__` 인데 `__package__ = 'pkgr'`** 다 — 그래서 된다. **상대 import 의 기준은 `__name__` 이 아니라 `__package__`** 다.
  ★ 튜토리얼은 더 보수적으로 적는다 — *"modules intended for use as the main module … must always use absolute imports."*
* ★ 트레이스백의 `File "./pkgr/tool42r.py"` 는 원래 절대 경로다 — 배너의 `sed` 가 `.` 로 바꿨다.
* ★ 이 트레이스백에는 **소스 줄이 있다** — `<stdin>` 이 아니라 **실제 파일**로 던졌기 때문이다. 캐럿 줄은 **없다**(이 판의 표시 — 이유는 재지 않았다).

### 6. ★★ `__init__.py` 가 있는 패키지와 없는 패키지

**언제 쓰나** — 「`__init__.py` 를 꼭 만들어야 하나」가 막힐 때.

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

```text
   nsa/space42/alpha42.py        ★ __init__.py 없음        import space42.alpha42 ─┐
   nsb/space42/beta42.py         ★ __init__.py 없음        import space42.beta42  ─┴─▶ space42 하나로 합쳐진다
                                                                                    __path__ = [nsa/space42, nsb/space42]
   reg42/__init__.py             있음                      import reg42.leaf42  ──▶ ① __init__.py 몸통  ② leaf42.py 몸통
```

그림 해설.

* ★★★ **`[1]`** — **서로 다른 두 디렉토리**의 `space42/` 가 **한 패키지 `space42`** 가 됐다. `alpha42` 는 `nsa` 쪽, `beta42` 는 `nsb` 쪽에서 왔다.
  `__path__` 가 **자리 둘**(`['nsa/space42', 'nsb/space42']`)이고 타입은 리스트가 아니라 **`_NamespacePath`** 다.
  ★ **`__file__` 과 `__spec__.origin` 이 `None`** — 실행할 `__init__.py` 가 **없으니** 가리킬 파일도 없다.
* ★★★ **`[2]`** — `import reg42.leaf42` 한 줄에 **`reg42/__init__.py` 몸통이 먼저**, 그다음 `leaf42.py` 몸통이 찍혔다. **하위 모듈을 부르면 부모 패키지의 `__init__.py` 가 먼저 돈다.**
  정규 패키지의 `__path__` 는 **`list`**.
* ★ **`[2]` 의 두 줄이 `[2]` 제목 바로 뒤에 찍힌 이유** — `import reg42.leaf42` 를 **그 `print` 다음 줄**에 두었기 때문이다. **import 가 곧 실행**이라는 것을 출력 순서가 보인다.

**비용** — 이름 공간 패키지는 **`__init__.py` 한 파일이 없어서** 된다. 그래서 **오타로 빠뜨린 `__init__.py`** 도 에러 없이 이름 공간 패키지가 되고, `__init__.py` 에 넣어 둔 초기화가 **조용히 안 돈다.**

### 7. ★★★ Go 는 빌드가 거부하고, JS 는 두 모양으로 깨진다

**언제 쓰나** — 「다른 언어는 순환 import 를 어떻게 다루나」를 견줄 때.

```text
// go.mod
module ex42

go 1.22
```

```go
// g42main.go
package main

import (
	"fmt"

	"ex42/one"
)

func main() { fmt.Println(one.F()) }
```

```go
// g42one.go
package one

import "ex42/two"

const Tag = "A"

func F() string { return "f>" + two.G() }
```

```go
// g42two.go
package two

import "ex42/one"

func G() string { return "g>" + one.Tag }
```

```text
===== cd e42_go && go build -o /dev/null . =====
package ex42
	imports ex42/one from g42main.go
	imports ex42/two from g42one.go
	imports ex42/one from g42two.go: import cycle not allowed
(exit 1)
```

* ★★★ **Go 는 실행 전에 거부한다** — `import cycle not allowed`, 그리고 **경로를 한 줄씩** 따라간다(`ex42` → `ex42/one` → `ex42/two` → 다시 `ex42/one`). `(exit 1)` — **바이너리 자체가 안 생긴다.**
  ★ 명세의 이유(초기화 순환이 **있을 수 없게** 만든다)는 [Go 01번](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md)이 인용했다 — **파이썬의 격자 24칸 같은 「어떻게 import 했나」의 차이가 Go 에는 원리상 없다.**

```js
// esa42.mjs
import { g } from "./esb42.mjs";
export const TAG = "A";
export function f() { return "f>" + g(); }
```

```js
// esb42.mjs
import { TAG } from "./esa42.mjs";
export const SEEN = TAG;
export function g() { return "g>" + SEEN; }
```

```js
// esmain42.mjs
import("./esa42.mjs").then(
  (m) => console.log("ESM :", m.f()),
  (e) => console.log("ESM :", e.name + ":", e.message),
);
```

```text
===== cd e42_node && node esmain42.mjs =====
ESM : ReferenceError: Cannot access 'TAG' before initialization
(exit 0)
```

```js
// cja42.cjs
const b = require("./cjb42.cjs");
exports.TAG = "A";
exports.f = () => "f>" + b.g();
```

```js
// cjb42.cjs
const a = require("./cja42.cjs");
const SEEN = a.TAG;
exports.g = () => "g>" + SEEN;
```

```js
// cjmain42.cjs
const a = require("./cja42.cjs");
console.error("CJS :", a.f());
```

```text
===== cd e42_node && node cjmain42.cjs =====
CJS : f>g>undefined
(node:4132475) Warning: Accessing non-existent property 'TAG' of module exports inside circular dependency
(Use `node --trace-warnings ...` to show where the warning was created)
(exit 0)
```

* ★★★ **ESM** — `esb42` 가 맨 위에서 `TAG` 를 읽자 **`ReferenceError: Cannot access 'TAG' before initialization`** — **TDZ**(선언 전 접근 금지 구간)다. 이름은 **있는데 아직 초기화 전**이라 막는다.
* ★★★ **CommonJS** — `cjb42` 가 받은 `a` 는 **반쯤 찬 `exports` 객체**라 `a.TAG` 가 **`undefined`** 다. **에러가 아니라 조용히 `undefined`** 가 흘러 `f>g>undefined` 가 됐고, node 가 **경고만** 한 줄 냈다.

```text
                     순환에서 반쯤 찬 상대를 만나면           「아직 없는 이름」을 읽으면            언제 알게 되나
   Go                ★ 만날 수 없다 — 빌드가 거부              —                                빌드 때 (exit 1)
   Python            반쯤 찬 모듈 객체를 받는다                ImportError / AttributeError       실행 중, 그 줄에서
   JS ESM            바인딩은 있지만 초기화 전                  ReferenceError (TDZ)              실행 중, 그 줄에서
   JS CommonJS       반쯤 찬 exports 객체를 받는다             ★ undefined (경고만)               ★ 값이 틀린 채 계속 간다
```

* ★★ **파이썬은 CommonJS 와 같은 모양**(반쯤 찬 객체를 준다)인데 **없는 이름을 읽으면 `undefined` 대신 예외**를 낸다 — 그리고 예외 문구에 **순환이라는 힌트**까지 붙인다.
* ★ JS 쪽 모듈 주제는 JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**(ESM 모듈)이고 아직 폴더가 없다. TDZ 자체는 JS 갈래의 [05번](../../../js/syntax/05-var-let-const-and-tdz/2-summary.md)이 정본이다.

## 문법 — 형태와 규칙

**형태**

```text
import pkg.mod                  # 절대 import. 이름 pkg 가 묶인다 (pkg.mod 로 쓴다)
import pkg.mod as m             # 이름 m 에 pkg.mod 를 묶는다
from pkg import mod, name       # 꺼내기 — ★ 그 순간 pkg 에 그 이름이 있어야 한다
from . import sibling           # 상대 import — 기준은 __package__
from ..up import thing          # 두 단계 위

if __name__ == "__main__":      # 진입점으로 실행됐을 때만
    main()

python3 -m pkg.mod              # __name__ = '__main__', __package__ = 'pkg', sys.path[0] = 현재 디렉토리
python3 pkg/mod.py              # __name__ = '__main__', __package__ = None,  sys.path[0] = pkg/
```

규칙 열.

1. ★★★ **import 는 `sys.modules` 를 먼저 본다** — 있으면 **몸통을 다시 실행하지 않고** 그 객체를 준다.
2. ★★★ **몸통 실행 전에 `sys.modules` 에 넣는다** — 그래서 순환 중에는 **반쯤 찬 모듈**을 받는다.
3. ★★★ **순환이 깨지는 것은 「몸통 실행 중에 상대에게서 이름을 꺼낼 때」** — `from X import n` · 맨 위의 `X.n`(동작 2 — 7 / 24).
4. ★★ **깨지는 칸은 진입점에 달렸다** — 먼저 시작한 쪽이 반쯤 찬 쪽이다.
5. ★★ **실패한 모듈은 `sys.modules` 에서 빠진다.**
6. ★★ **`__main__` 과 `pkg.mod` 는 다른 이름표**다 — 진입 모듈을 다시 import 하면 **두 번 실행**, 클래스가 둘.
7. ★★ **상대 import 의 기준은 `__package__`** — 스크립트 실행은 `None` 이라 깨진다.
8. ★ **`__init__.py` 가 없으면 이름 공간 패키지** — 여러 디렉토리가 합쳐지고 `__file__` 이 `None`.
9. ★ **하위 모듈을 import 하면 부모의 `__init__.py` 가 먼저** 돈다.

## 어디서 틀리나

### (1) ★★★ 「순환 import 는 무조건 에러다」

**아니다** — 격자 24칸 중 **17칸이 통과**했다(동작 2). 깨지는 것은 **몸통 실행 중에 이름을 꺼내는 칸**뿐이다.

### (2) ★★★ 「테스트에서는 되는데 운영에서 깨진다」

**진입점이 다르면 깨지는 칸이 옮겨 간다**(동작 2 의 위·아래 표). 테스트가 `import cb` 부터, 운영이 `import ca` 부터면 **같은 코드가 다르게** 돈다.

### (3) ★★★ `from X import name` 을 `import X` 와 같은 것으로 안다

**꺼내는 시점이 다르다** — `from` 은 **그 줄에서** 이름을 꺼내고, `import X` 는 **객체만** 받는다(동작 1 의 ④·⑤).

### (4) ★★ 진입 모듈에 클래스를 두고 다른 모듈이 그것을 import 한다

**모듈이 두 벌** 생겨 `isinstance` 가 **`False`**(동작 4).

### (5) ★★ `python pkg/mod.py` 로 패키지 안의 모듈을 돌린다

**상대 import 가 `ImportError`**, 절대 import 도 `pkg` 가 **안 보일 수** 있다(동작 4·5). **`python -m pkg.mod`** 로 돌린다.

### (6) ★★ 순환 실패를 `try` 로 받고 계속 쓴다

**실패한 모듈은 대장에서 빠진다**(동작 3) — 다음 `import` 는 **처음부터 다시** 실행한다.

### (7) ★ `__init__.py` 를 빠뜨렸는데 에러가 안 나서 모른다

**이름 공간 패키지가 된다**(동작 6) — 에러 없이 `__init__.py` 의 초기화만 **조용히 빠진다.**

### (8) ★ 「파이썬도 Go 처럼 순환을 막아 준다」

**빌드 단계가 없다** — 실행 중 **그 줄에서** 드러난다(동작 7).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·튜토리얼이 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 예외 문구 · 힌트 꼬리 | 실행 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 출력 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 몸통 실행 **전에** `sys.modules` 에 넣는다 | 레퍼런스 — import system |
| 실패한 모듈은 **그것만** `sys.modules` 에서 빠진다 | 레퍼런스 — import system |
| 몸통은 **처음 import 때 한 번** 실행된다 | 튜토리얼 — Modules |
| 정규 패키지를 import 하면 **`__init__.py` 가 실행**된다 | 레퍼런스 — Regular packages |
| 이름 공간 패키지는 여러 **portion** 의 합성이고 `__path__` 는 **리스트가 아닌 반복 가능 객체** | 레퍼런스 — Namespace packages |
| 진입 모듈의 이름은 늘 **`"__main__"`** — 그래서 상대 import 를 쓰지 말라 | 튜토리얼 — Intra-package references |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ 순환일 때 예외 문구에 **`partially initialized module`** 과 **`(most likely due to a circular import)`** 가 붙는다 | 실행(동작 2 · 3) |
| 같은 상황이 `from` 이면 **`ImportError`**, 속성 접근이면 **`AttributeError`** | 실행(동작 2) — 종류는 문법이 정하고 문구는 구현이다 |
| 이름 공간 패키지의 `__path__` 타입 이름 **`_NamespacePath`** | 실행(동작 6) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「순환 import 를 하면 `ImportError` 가 난다」\
  ○ **몸통 실행 중에 이름을 꺼낼 때만**, 그리고 **진입점에 따라** 깨지는 칸이 다르다(7 / 24).
* ✗ 「`if __name__ == "__main__":` 이 있으면 그 파일은 한 번만 실행된다」\
  ○ **다른 모듈이 그 파일을 import 하면 한 번 더** 실행된다(동작 4).
* ✗ 「`__init__.py` 가 없으면 패키지가 아니다」\
  ○ 3.3 부터 **이름 공간 패키지**다(동작 6).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 두 모듈이 서로의 함수를 **부를 때만** 쓴다 | 맨 위 `import X`(모듈째) | 객체만 받으니 격자에서 **진입점 `ca` 쪽 한 행이 전부 통과** |
| 서로의 **상수·클래스를 맨 위에서** 쓴다 | ★ 공통 부분을 **제3의 모듈**로 | `from` 과 맨 위 접근은 격자에서 깨진다 |
| 급한 순환 끊기 | 함수 안 import | 격자에서 **한 칸도 안 깨졌다** — 대신 import 오류가 부를 때로 미뤄진다 |
| 패키지 안의 모듈을 실행 | `python -m pkg.mod` | `__package__` 가 서고 `sys.path[0]` 이 현재 디렉토리 |
| 진입점 파일 | 얇게 — **`main()` 을 부르기만** | 두 벌이 생겨도 잃을 것이 없게 |
| 패키지를 만든다 | `__init__.py` 를 둔다 | 이름 공간 패키지는 **여러 배포판이 한 이름을 나눠 쓸 때** 쓴다 |

## 핵심 문장

1. **import 는 대장(`sys.modules`)에 먼저 적고 몸통을 한 번 실행한다** — 그래서 순환 중에는 **반쯤 찬 모듈**을 받는다.
2. **순환은 「몸통 실행 중에 상대에게서 이름을 꺼낼 때」만 깨진다** — `from X import n` 과 맨 위의 `X.n`. 격자 **7 / 24**.
3. **깨지는 칸은 진입점에 달렸다** — 같은 두 파일이 `import ca` 와 `import cb` 에서 다른 칸이 깨졌다.
4. **`__main__` 은 다른 이름표다** — 진입 모듈을 다시 import 하면 두 번 실행되고 클래스가 둘이 된다.
5. **Go 는 빌드가 거부하고, 파이썬은 그 줄에서 예외를, CommonJS 는 조용히 `undefined` 를** 낸다.

## 관련 자료

* 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — ★ **경계**: 이름이 **어느 스코프에서 풀리나**는 그쪽,
  여기는 **모듈 전역(= 모듈 객체의 속성)이 언제 채워지나**부터. 반쯤 찬 모듈의 `vars()` 가 `[]` 인 것(동작 1 의 ③)이 그 이음매다.
* 이어지는 곳: [목록의 **51번 주제**](../51-asyncio-coroutine-basics/)(`asyncio` 기초) — `if __name__ == "__main__": asyncio.run(main())` 의 관용이 여기의 동작 4 위에 선다.
* 대비: [Go 01번 — 패키지·import·main·init](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md) — ★ **경계**: Go 의 순환 금지와 명세 인용은 그쪽이 정본. 여기서는 **같은 모양의 순환을 한 번 더 던져** 에러 전문만 얻었다.
* 대비: JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**(ESM 모듈) · [05번 — TDZ](../../../js/syntax/05-var-let-const-and-tdz/2-summary.md) —
  ★ **경계**: ESM 의 라이브 바인딩·호이스팅은 JS 42번의 몫이다. 여기서는 **순환 한 모양**만 node 18 로 던졌다.
* 공식 문서: [The import system](https://docs.python.org/3.12/reference/import.html) · [Modules 튜토리얼](https://docs.python.org/3.12/tutorial/modules.html) ·
  [`__main__`](https://docs.python.org/3.12/library/__main__.html) · [PEP 420](https://peps.python.org/pep-0420/) · [PEP 328](https://peps.python.org/pep-0328/)

## 용어 풀이

* **모듈(module)**: `.py` 파일을 실행해 만든 객체. 파일의 전역 이름이 모듈의 속성이 된다.
* **`sys.modules`**: 모듈 이름 → 모듈 객체의 **캐시 dict**. import 가 가장 먼저 본다.
* **몸통(module body)**: 모듈 파일의 최상위 코드. **처음 import 될 때 한 번** 실행된다.
* **부분 초기화 모듈(partially initialized module)**: 몸통이 **아직 끝나지 않은** 채 `sys.modules` 에 있는 모듈.\
  예: 순환 중에 `ob` 가 받은 `oa` — 이름 목록이 `[]`.
* **순환 import(circular import)**: A 가 B 를, B 가 A 를 import 하는 것.
* **진입점(entry point)**: 가장 먼저 실행되는 모듈. 파이썬에서는 이름이 **`__main__`** 이 된다.
* **`__package__`**: 상대 import 의 **기준 패키지 이름**. 스크립트로 실행하면 `None`.
* **절대 / 상대 import**: `import pkg.mod` 처럼 **최상위부터** 적는 것 / `from . import x` 처럼 **자기 패키지 기준**으로 적는 것.
* **정규 패키지(regular package)**: `__init__.py` 가 있는 디렉토리. import 하면 그 파일이 실행된다.
* **이름 공간 패키지(namespace package)**(3.3+, PEP 420): `__init__.py` 없는 디렉토리. **여러 자리(portion)** 가 한 패키지로 합쳐진다.
* **TDZ(temporal dead zone)**: JS 에서 `let`·`const`·`import` 바인딩이 **선언은 됐지만 초기화 전**이라 읽으면 `ReferenceError` 가 나는 구간.

## 더 들어가면

* ★ **`importlib.reload`** — 레퍼런스가 *"This contrasts with reloading where even the failing module is left in `sys.modules`"* 라고 적는다. 동작 3 의 반대편인데 **이 문서는 재지 않았다.**
* ★ **`__getattr__` 모듈 함수(PEP 562)** — 반쯤 찬 모듈에서 없는 이름을 읽을 때 **끼어들 자리**가 있다. 순환을 푸는 도구로는 권하지 않는다(이 문서는 재지 않았다).
* ★ **`python -m` 과 `sys.path[0]`** — 3.11 의 **`-P`/`PYTHONSAFEPATH`** 가 그 자리를 비운다. 동작 4 의 둘째 블록이 그 옵션으로 어떻게 바뀌는지는 **재지 않았다.**
