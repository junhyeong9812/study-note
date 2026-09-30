# Python — 그 뒤 (2026-09 기준)

> 이 문서는 재서술이 아니라 **새로 쓴 것**이다.\
> `history/python/` 의 다른 편은 모두 원본 repo(`~/project/python-history/`)를 정본으로 두고 옮긴 것이지만, 이 편만 원본이 없다.\
> 그래서 원문 대조 자리를 **출처 접지**가 대신한다 — 본문의 사실 주장은 전부 아래 「출처」 절의 항목으로 되돌아간다.\
> 기준일은 **2026-09-20** 이다.\
> 그 뒤의 일은 담기지 않았다.

## 원본이 멈춘 자리

원본 repo 는 여섯 편인데, **편마다 멈춘 자리가 다르다.**\
그래서 한 사건으로 잘라 말할 수 없고, 범위를 여기 밝혀 둔다.

| 원본 | 마지막으로 다룬 것 | 원문의 표현 |
|------|-------------------|-------------|
| `03-현대-Python.md` | **Python 3.13 (2024년 10월)** | 문서 제목부터 "현대 Python (3.5 \~ 3.13)" 이고, 마지막 절이 "## Python 3.13 (2024년 10월)" 이다 |
| `06-핵심-개념-진화.md` | 3.13 의 free-threading·JIT — 둘 다 **실험적** | "free-threading과 JIT 모두 **실험적(experimental)** — 기본 빌드에는 꺼져 있고, 별도 빌드/옵션으로 활성화한다" |
| `04-패키징-생태계.md` | **PEP 751**(`pylock.toml`) 승인과 **pip 25.1**(2025-04) | "Brett Cannon의 **PEP 751**이 2025년 3월 승인되며 … pip은 25.1(2025-04)에 실험적 `pip lock`을 추가했고" |
| `05-데이터-ML-생태계.md` | LLM 시대의 Python — 연도를 못 박지 않는다 | — |

그래서 이 문서의 범위는 이렇다.

- **언어 릴리스**는 **Python 3.13(2024-10) 다음**부터.
- **패키징**은 **2025년 4월 다음**부터.
- 기준일은 **2026-09-20**.

원문이 앞을 내다본 문장도 하나 있다.\
`06-핵심-개념-진화.md` 가 PEP 703 의 단계적 도입을 적으면서 **"Python 3.14: PEP 779에 따라 '지원되는(supported)' 상태로 승격"** 이라고 썼다.\
「원문이 「예정」이라 한 것은 어떻게 됐나」 절이 그 자리를 받는다.

## 그 뒤 무슨 일이 있었나

### 1. Python 3.14 — 2025년 10월 7일

원본이 3.13(2024-10)에서 멈춘 뒤 나온 첫 정식 릴리스다.\
연 1회·10월이라는 주기가 그대로 지켜졌다.

공식 「What's New In Python 3.14」가 표제로 드는 PEP 들이다.\
**PEP 779**(free-threading)도 같은 표제 목록에 있지만, 분량이 커서 아래 2절에서 따로 다룬다.

| PEP | 내용 |
|-----|------|
| **PEP 649 · 749** | 애노테이션의 **지연 평가**. 애노테이션을 즉시 평가하지 않고 annotate 함수에 담아 두었다가 필요할 때 평가한다. 들여다보는 도구로 `annotationlib` 모듈이 새로 들어왔다(VALUE·FORWARDREF·STRING 형식) |
| **PEP 750** | **템플릿 문자열(t-string)**. f-string 의 `f` 대신 `t` 접두사를 쓰면, 합쳐진 문자열이 아니라 정적 부분과 보간 부분을 담은 `Template` 객체가 나온다 |
| **PEP 734** | 표준 라이브러리의 **다중 인터프리터** — `concurrent.interpreters` 모듈 |
| **PEP 758** | `as` 절이 없을 때 `except`·`except*` 의 예외 타입 나열에 괄호를 요구하지 않음 |
| **PEP 765** | `finally` 블록을 `return`·`break`·`continue` 로 빠져나가면 컴파일러가 `SyntaxWarning` 을 낸다 |
| **PEP 768** | 외부 디버거를 안전하게 붙이는 인터페이스 — `sys.remote_exec()` |
| **PEP 784** | **Zstandard 압축** — `compression.zstd` 모듈, 그리고 `lzma`·`bz2`·`gzip`·`zlib` 을 묶은 `compression` 패키지 |
| **PEP 776** | Emscripten 을 tier 3 공식 지원 플랫폼으로 |
| **PEP 741** | Python Configuration C API |
| **PEP 761** | 공식 릴리스의 **PGP 서명 중단**. 표제 문장이 "PGP signatures have been discontinued for official releases" 다 — 언어·라이브러리가 아니라 **배포 쪽** 항목이다 |

그 밖에 REPL 의 구문 강조, `python -m asyncio ps PID` / `pstree PID` 같은 asyncio 내부 관찰 명령, 오류 메시지 개선이 들어갔다.

### 2. free-threading — 「실험적」에서 「공식 지원」으로. **기본값은 아니다**

이 문서에서 가장 조심해서 읽어야 할 자리다.

원본은 3.13 의 free-threading 을 **실험적(experimental)** 이라 적었다.\
3.14 에서 그 상태가 올라갔다 — 「What's New In Python 3.14」가 표제 항목으로 이렇게 적는다.

> "**PEP 779**: Free-threaded Python is officially supported"

**그런데 「공식 지원」이 「기본값」이 아니다.**\
PEP 779 본문이 단계를 셋으로 나누어 직접 말한다.

> "Phase II would make the free-threaded build **officially supported but still optional**, and **phase III would make the free-threaded build the default**."

3.14 가 들어간 것은 **Phase II** 다.\
Phase III(기본값)는 아직 오지 않았다.\
즉 **free-threaded 빌드는 여전히 별도 빌드이고, 일반 빌드에는 GIL 이 그대로 있다.**

3.14 에서 실제로 달라진 것:

- PEP 703 의 구현이 완결돼, 임시 우회책들이 영구적 해법으로 교체됐다.
- free-threaded 모드에서도 **특화 적응형 인터프리터(specializing adaptive interpreter)** 가 켜진다.
- 단일 스레드 코드의 성능 손해가 **대략 5\~10%** 로 줄었다.
  원본은 3.13 시점의 수치를 **"약 10\~15% 느리다"** 로 적었으니, 그 폭이 좁혀진 것이다.

> **오해하기 쉬운 자리** — 「Python 3.14 부터 GIL 이 없어졌다」는 틀렸다.\
> 출처가 말하는 것은 **GIL 없는 빌드가 실험 딱지를 떼고 공식 지원 대상이 됐다**는 것이고, **선택 사항(optional)** 임을 같은 문장에서 명시한다.\
> 기본 빌드를 바꾸는 단계는 PEP 779 가 Phase III 라 부르는 별도의 단계다.

### 3. JIT 은 여전히 experimental — 그리고 3.14 의 성능 수치는 JIT 의 것이 아니다

여기도 상태 표현을 그대로 옮긴다.\
「What's New In Python 3.14」의 표제 문장은 이렇다.

> "Windows and macOS binary releases now support the **experimental** just-in-time compiler"

**「실험적」이라는 단어가 그대로 남아 있다.**\
달라진 것은 **공식 바이너리 배포본에서 그 실험 기능을 켤 수 있게 됐다**는 점이다.

그리고 3.14 문서에 실린 「3\~5% 빨라졌다」는 수치는 **JIT 의 것이 아니라 별개 항목의 것**이다.\
문서는 「A new type of interpreter」라는 절을 따로 두고 **tail-call 인터프리터**를 설명한다.

> "It uses tail calls between small C functions that implement individual Python opcodes, rather than one large C `case` statement. … Preliminary benchmarks suggest a geometric mean of **3-5% faster** on the standard `pyperformance` benchmark suite, **depending on platform and architecture**. **The baseline is Python 3.14 built with Clang 19, without this new interpreter.**"

조건을 그대로 옮기면 이렇다.

- 잰 대상: 표준 `pyperformance` 벤치마크 스위트의 **기하평균**
- 비교 기준선: **같은 3.14 를 Clang 19 로 빌드하되 이 인터프리터를 뺀 것**
- 전제: **Clang 19 이상**, **x86-64 · AArch64** 에서만 동작. GCC 지원은 "a future release of GCC is expected to support this as well" 로 적힌 예정
- 상태: **"This feature is opt-in for now"** — 기본이 아니다.\
  문서는 PGO(프로파일 기반 최적화)를 함께 켤 것을 강력히 권한다("the only configuration that has been tested and validated")

문서는 이름 때문에 생기는 오해까지 직접 막아 둔다.

> "This is not to be confused with tail call optimization of Python functions, which is currently not implemented in CPython."

> **오해하기 쉬운 자리 둘** —\
> ① 「Python 3.14 의 JIT 덕분에 3\~5% 빨라졌다」는 출처가 하는 말이 아니다.\
> 그 수치는 **tail-call 인터프리터** 절의 것이고, JIT 은 같은 문서에서 여전히 **experimental** 로 불린다.\
> ② 「tail-call 인터프리터」는 **Python 함수의 꼬리 호출 최적화가 아니다.**\
> 문서가 "currently not implemented in CPython" 이라 못 박는다.\
> 바뀐 것은 인터프리터 내부의 C 함수 호출 방식이다.

### 4. 패키징 — `pylock.toml` 이 「만드는 쪽」에서 「읽는 쪽」으로 넘어갔다

원본은 PEP 751 이 승인되고(**2025년 3월** — PEP 페이지의 Resolution 은 **2025-03-31**, Status 는 **Final**), pip 25.1(2025-04)이 실험적 `pip lock` 을 더한 데까지 적었다.\
**즉 그때까지는 「락파일을 만드는」 쪽만 있었다.**\
그 뒤 pip 변경 이력에서 확인되는 것은 이렇다.

| pip 버전 | 날짜 | 변경 이력이 적는 것 |
|----------|------|---------------------|
| 25.1 | 2025-04-26 | "Add a new, *experimental*, `pip lock` command, implementing **PEP 751**" — **원본이 다룬 지점** |
| 25.2 | 2025-07-30 | Python 3.14 지원 선언, 다운로드 자동 재개를 기본으로 |
| 25.3 | 2025-10-24 | 레거시 `setup.py develop` 방식 제거, `--global-option`·`--build-option` 제거 |
| 26.0 | 2026-01-30 | **PEP 723** 인라인 스크립트 메타데이터(`--requirements-from-script`), `--all-releases`·`--only-final`·`--uploaded-prior-to` |
| **26.1** | **2026-04-26** | **"Add experimental support to read requirements from standardized `pylock.toml` files (`-r pylock.toml`)"** |
| 26.2 | 2026-07-29 | `pylock.toml` 의 `upload-time` 필드 지원, `--use-feature=venv-isolation`(실험) |
| 26.2.1 | 2026-08-04 | virtualenv 의 keyring 공급자 수정 |

**읽는 쪽도 여전히 experimental 이다.**\
변경 이력의 문장에 `experimental` 이 그대로 붙어 있다.\
그러니 「이제 파이썬에 표준 락파일이 자리잡았다」로 읽으면 안 된다 — 표준은 Final 이지만, pip 쪽 **구현**은 만드는 쪽·읽는 쪽 모두 실험 단계로 적혀 있다.

uv 쪽은 기준일 현재도 **1.0 이 아니다.**\
GitHub 릴리스 목록의 최신은 **0.12.17(2026-09-18)** 이고, 그 앞도 0.12.x 가 며칠 간격으로 이어진다.\
원본이 uv 를 "Python의 Cargo를 지향"한다고 소개한 도구인데, **버전 번호로 보면 아직 0.x 를 벗어나지 않았다.**

### 5. Python 3.15 — 기준일 현재 **아직 정식이 아니다**

PEP 790(Python 3.15 Release Schedule, Status: Active)이 적은 일정이다.

| 단계 | 날짜 |
|------|------|
| 알파 1 | 2025-10-14 |
| 알파 8 | 2026-04-07 |
| **베타 1**(기능 동결) | 2026-05-07 |
| 베타 4 | 2026-07-18 |
| **RC 1** | 2026-08-04 |
| **RC 2** | 2026-09-01 |
| **정식(final)** | **2026-10-01 예정** |

**기준일(2026-09-20)은 RC 2 와 정식 사이**다.\
파이썬 개발자 가이드의 버전 표도 3.15 를 **`prerelease`** 로 적고, 정식일을 이탤릭(예정)으로 둔다 — 3.13 은 `bugfix`, 3.14 도 `bugfix` 다.

3.15 의 「What's New」 초안이 표제로 드는 것(**아직 확정된 정식 릴리스의 내용이 아니다**):

| PEP | 내용 |
|-----|------|
| **PEP 810** | **명시적 지연 임포트** — `lazy import json` 처럼 써서 시작 시간을 줄인다 |
| **PEP 814** | `frozendict` 내장 타입 |
| **PEP 661** | `sentinel` 내장 타입 |
| **PEP 799** | 프로파일링 전용 패키지(`profiling.tracing`·`profiling.sampling`)와 고빈도 표본 프로파일러 **Tachyon** |
| **PEP 831** | 프레임 포인터를 기본 활성화 |
| **PEP 798** | 컴프리헨션 안에서의 언패킹 — `[*L for L in lists]` |
| **PEP 686** | **UTF-8 을 기본 인코딩으로** |
| **PEP 829** | 패키지 시작 설정 파일 |
| **PEP 728 · 747 · 800** | 타입 쪽 — 타입 지정 extra items 를 갖는 `TypedDict`, `TypeForm`, 타입 시스템의 disjoint bases |
| **PEP 803 · 820 · 793** | **free-threaded 빌드용 Stable ABI**(`abi3t`) 등 C API |
| **PEP 782 · 788** | `PyBytesWriter` C API, C API 의 finalization 보호 |

같은 문서가 JIT 에 대해 "The JIT compiler has been significantly upgraded" 라 적고, **공식 Windows 64비트 바이너리가 tail-call 인터프리터를 쓰게 된다**고 적는다.\
3.14 에서 opt-in 이던 tail-call 인터프리터가 한 배포 채널의 기본으로 들어가는 셈이다 — **다만 이것은 아직 정식 릴리스가 아닌 문서의 서술이다.**

## 원문이 「예정」이라 한 것은 어떻게 됐나

원본에서 앞을 내다본 문장을 모아 대조하면 이렇다.

| 원문의 문장 | 어떻게 됐나 | 근거 |
|-------------|-------------|------|
| `06` — "**Python 3.14**: PEP 779에 따라 '지원되는(supported)' 상태로 승격" | **그대로 됐다.** 3.14 의 What's New 가 표제로 "PEP 779: Free-threaded Python is officially supported" 를 단다 | docs.python.org 3.14 What's New |
| `06` — "**기본값 전환**: 향후 수년간 보류 — 기존 빌드는 여전히 GIL이 기본" | **여전히 그렇다.** PEP 779 가 기본값 전환을 **Phase III** 로 따로 두고, 3.14 가 들어간 Phase II 는 "officially supported but **still optional**" 이라 적는다 | PEP 779 |
| `06` — free-threaded 빌드는 단일 스레드에서 "약 **10\~15%** 느리다" | 3.14 에서 **"roughly 5-10%"** 로 적힌다. 폭이 좁혀졌다 | docs.python.org 3.14 What's New |
| `03` — 3.13 의 JIT 성능 향상은 "미미하다(modest)" … "앞으로 몇 개 버전에 걸쳐 키워 갈 인프라의 첫 삽" | 3.14 에서도 JIT 은 **experimental** 그대로이고, 달라진 것은 Windows·macOS 바이너리 배포본이 그 실험 기능을 지원하게 된 것이다. 3.15 의 What's New **초안**은 "The JIT compiler has been significantly upgraded" 라 적지만 **3.15 는 아직 정식이 아니다** | docs.python.org 3.14 / 3.15 What's New |
| `04` — PEP 751 은 락파일 "**표준화 시도**" | 표준 자체는 **Final**(Resolution 2025-03-31). pip 은 26.1(2026-04-26)에서 **읽는 쪽**(`-r pylock.toml`)까지 붙였는데, **양쪽 다 changelog 에 `experimental` 로 적혀 있다** | PEP 751 · pip changelog |

## 아직 안 끝난 것

기준일(2026-09-20) 현재 **정식이 아니거나 기본이 아닌** 것들이다.\
정식·기본으로 읽지 말 것.

- **Python 3.15** — 정식이 아니다.\
  **RC 2(2026-09-01)** 까지 나왔고 정식은 **2026-10-01 예정**이다.\
  개발자 가이드가 3.15 를 `prerelease` 로 분류한다.\
  위에 옮긴 3.15 의 기능 목록은 **What's New 초안**의 것이다.
- **free-threading 의 기본값화** — 오지 않았다.\
  PEP 779 의 **Phase III** 이고, 3.14 가 들어간 것은 Phase II(공식 지원·여전히 선택)다.
- **JIT** — 3.14 에서 여전히 **experimental** 이다.
- **tail-call 인터프리터** — 3.14 에서 **opt-in** 이고 **Clang 19 이상 · x86-64/AArch64** 에서만 동작한다.\
  GCC 지원은 "a future release of GCC is expected to support this as well" 로 적힌 예정이다.
- **pip 의 `pylock.toml`** — 만드는 쪽(`pip lock`, 25.1)도 읽는 쪽(`-r pylock.toml`, 26.1)도 changelog 표현이 **experimental** 이다.
- **uv 1.0** — 오지 않았다.\
  최신은 **0.12.17(2026-09-18)** 이다.

### 확인하지 못한 것

- **PEP 751 을 각 도구가 어디까지 받아들였는지의 전수.**\
  pip 쪽은 변경 이력으로 확인했으나, poetry·PDM·uv 의 대응 범위는 검색 결과(2차 출처)에만 있었고 각 프로젝트의 1차 문서로 확인하지 못했다.\
  uv 에 대해서는 **버전 번호와 날짜만** 1차(GitHub 릴리스 목록)로 확인해 적었다.
- **데이터·ML 생태계(원본 `05`)의 그 뒤.**\
  원본이 그 편에서 연도를 못 박지 않아 「멈춘 자리」를 정할 수 없었고, 주요 라이브러리의 릴리스를 1차 출처로 추적하지 못했다.\
  이 문서는 그 갈래를 다루지 않는다.
- **3.14·3.15 의 성능 비교 수치 일반.**\
  위에 옮긴 두 수치(free-threaded 의 5\~10% 손해, tail-call 의 3\~5% 개선) 외에는, 1차 출처가 잰 조건이 함께 적힌 값을 찾지 못해 쓰지 않았다.

## 용어 풀이

새로 나온 것만 적는다.

> **Phase II / Phase III (PEP 779)** — free-threaded 빌드를 단계적으로 들이는 구간 이름이다.\
> Phase II 는 「공식 지원하되 여전히 선택」, Phase III 는 「기본값」이다.\
> 예: Python 3.14 는 Phase II 에 들어갔고, Phase III 는 기준일 현재 오지 않았다.

> **tail-call 인터프리터** — 각 파이썬 opcode 를 구현한 작은 C 함수들 사이를 꼬리 호출로 옮겨 다니게 만든 인터프리터다.\
> 기존에는 커다란 C `case` 문 하나였다.\
> 예: 3.14 문서가 "It uses tail calls between small C functions that implement individual Python opcodes, rather than one large C `case` statement" 라 적는다.\
> **파이썬 함수의 꼬리 호출 최적화와는 다른 것**이라고 같은 문서가 덧붙인다.

> **t-string (템플릿 문자열, PEP 750)** — `f` 대신 `t` 접두사를 붙인 문자열 리터럴이다.\
> 합쳐진 문자열 대신 정적 부분과 보간 부분을 나눠 담은 `Template` 객체가 나온다.\
> 예: f-string 은 곧바로 문자열이 되지만, t-string 은 합치기 **전**의 조각을 손에 쥐어 준다.

> **지연 임포트 (lazy import, PEP 810)** — 임포트 문을 만난 자리에서 바로 모듈을 불러오지 않고, 실제로 쓰일 때 불러오는 것이다.\
> 예: 3.15 의 What's New 초안이 `lazy import json` 이라는 표기를 든다.\
> **3.15 는 아직 정식이 아니다.**

> **`pylock.toml` (PEP 751)** — 어떤 패키지를 어떤 버전으로 설치할지 못 박아 둔 **표준 락파일** 형식이다.\
> 도구마다 달랐던 `poetry.lock`·`uv.lock` 등을 한 형식으로 모으려는 것이다.\
> 예: pip 은 25.1 에서 이 파일을 **만드는** 쪽을, 26.1 에서 **읽는** 쪽을 실험적으로 붙였다.

## 출처

**1차 출처** — python.org 의 What's New 문서, peps.python.org 의 PEP 원문, 파이썬 개발자 가이드, pip 의 변경 이력, uv 저장소의 릴리스 목록.

| 제목 | 발행일·상태 | URL |
|------|-------------|-----|
| What's New In Python 3.14 | 3.14 정식 **2025-10-07** | https://docs.python.org/3/whatsnew/3.14.html |
| What's New In Python 3.15 (**초안** — 3.15 는 미출시) | 정식 **2026-10-01 예정** | https://docs.python.org/3.15/whatsnew/3.15.html |
| PEP 779 – Criteria for supported status for free-threaded Python | Status: **Final** | https://peps.python.org/pep-0779/ |
| PEP 790 – Python 3.15 Release Schedule | Status: **Active** | https://peps.python.org/pep-0790/ |
| PEP 751 – A file format to record Python dependencies for installation reproducibility | Status: **Final**, Resolution **2025-03-31** | https://peps.python.org/pep-0751/ |
| Status of Python versions (Python Developer's Guide) | 수시 갱신 | https://devguide.python.org/versions/ |
| pip — Release Notes (changelog) | 수시 갱신 | https://pip.pypa.io/en/stable/news/ |
| Releases · astral-sh/uv (GitHub) | 최신 **0.12.17 — 2026-09-18** | https://github.com/astral-sh/uv/releases |

**2차 출처** — 이 문서는 본문 사실에 2차 출처를 쓰지 않았다.\
검색 과정에서 본 2차 출처(패키징 도구 대응 현황을 정리한 블로그·포럼 글 등)는 1차로 가는 길잡이로만 썼고, 1차로 확인되지 않은 항목(poetry·PDM 의 PEP 751 대응 범위 등)은 「확인하지 못한 것」으로 남겼다.

**원본 repo 인용** — 「원본이 멈춘 자리」와 「원문이 「예정」이라 한 것」 절이 인용한 문장의 출처는 `~/project/python-history/` 의 `03-현대-Python.md` · `04-패키징-생태계.md` · `06-핵심-개념-진화.md` 다.\
읽기만 했고 고치지 않았다.
