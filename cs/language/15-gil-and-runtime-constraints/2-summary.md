# language/15-gil-and-runtime-constraints — GIL 같은 런타임 제약: 스레드를 늘려도 병렬이 안 되는 이유 — 정리 (힌트)

## 해결하는 문제

CPython 3.12에서 순수 파이썬 계산을 스레드 4개로 나눴다. 시간이 거의 그대로다(실험 1).

```text
  기대                         실제 (CPython 3.12, 순수 파이썬 계산)
  T1 ████                      T1 ██    ██    ██
  T2 ████                      T2   ██    ██    ██
  T3 ████   (동시에)            T3     ██    ██
  T4 ████                      T4       ██    ██      (한 번에 하나씩)
```

- 원인은 언어 문법이 아니라 **런타임(인터프리터 구현)의 제약**이다.
  - *GIL(global interpreter lock)*: CPython 인터프리터가 "한 번에 한 스레드만 파이썬 바이트코드를 실행하게" 하는 장치(Python 용어집).
  - *런타임 제약*: 언어 명세가 아니라 특정 구현이 거는 실행 조건. 같은 Python이라도 Jython·IronPython에는 GIL이 없다(PEP 703 "Jython and IronPython" 절 — 대신 CPython 확장을 지원하지 않는다. 원고 §12는 "자바나 아이언파이썬"으로 적는다).

쉬운 예: 회의실에 마이크가 하나뿐이다.
- 발언자(스레드)가 여럿이어도 마이크를 쥔 사람만 말한다.
- 누가 자료를 찾으러 나가면(I/O) 마이크를 내려놓는다. 그동안 다른 사람이 말한다.

똑같은 구조다.\
그래서 **기다림이 많은 일**은 스레드로 빨라지고, **말(계산)만 하는 일**은 안 빨라진다.

실무 예:
- Flask·Django 워커에서 이미지 리사이즈·PDF 생성을 스레드 풀에 넘겼는데 처리량이 그대로다.
- 그래서 파이썬 웹 서버는 흔히 프로세스 워커를 여러 개 띄운다(프로세스마다 GIL이 따로 있다).
- Node도 JS 코드는 이벤트 루프 스레드 하나에서만 돈다. CPU 작업을 병렬로 돌리려면 `worker_threads`(실험 4)나 별도 프로세스(`cluster`·`child_process`)가 필요하다.

기초(GIL 정의, CPU/I/O 바운드 구분, 경쟁 조건과 Lock)는 원고 [foundations/process-thread §9~12](../../foundations/process-thread/README.md)에 있다. 이 노트는 **왜 그런 제약이 있고, 어디서 풀리고, 운영에서 어떻게 보이나**를 채운다.

## 동작·원리

### 1. GIL 한 바퀴 — 언제 놓나

```text
  시간 ──────────────────────────────────────────────────────────────▶
  T1  [바이트코드 실행 ...........][놓음]           [대기 ...........][획득 ...
  T2  [GIL 대기 ── 5ms 지나면 "놓아 달라" 요청]─[획득][바이트코드 ......][놓음]
  T3  [time.sleep / socket.recv → 기다리는 동안 GIL 놓음 ─────────────────────]
  T4  [hashlib.sha256(64MB) → C 코드가 GIL 놓고 계산 ── 다른 코어에서 동시에 ──]
```

- **I/O를 기다릴 때 놓는다.** 용어집: "the GIL is always released when doing I/O".
- **C 확장이 계산 중 놓을 수 있다.** 용어집: 압축·해싱 같은 무거운 작업에서 GIL을 놓도록 설계된 표준·서드파티 확장 모듈이 있다.
- **바이트코드끼리는 전환 간격마다 넘긴다.** `sys.getswitchinterval()`은 3.12에서 0.005(초)였다(실험 1 출력).
  - Python 3.12 `sys.setswitchinterval` 문서: 이 값은 타임슬라이스의 "이상적인 길이"다. 실제로는 더 길 수 있고, 다음에 누가 실행될지는 OS가 정한다. 인터프리터에는 자기 스케줄러가 없다.
  - 참고: 원고 §9의 "각 스레드 실행 시간인 타임 슬라이스는 0.005초이다"는 "목표 간격"으로 읽어야 한다. 실제 간격은 위 문서처럼 더 길 수 있다.

### 2. 왜 GIL이 있나 — 참조 카운트

```text
  obj ── ob_refcnt = 2          (이미 참조 2개)
   T1: x = obj   → refcnt 읽기(2) → +1 → 3 쓰기 ─┐
   T2: y = obj   → refcnt 읽기(2) → +1 → 3 쓰기 ─┴─ 실제 참조는 4개인데 값은 3 (갱신 하나 유실)
   나중에 참조 3개가 사라지면 refcnt = 0 → 해제 → 남은 1개는 해제된 메모리를 가리킨다(use-after-free)
```

- CPython은 모든 객체에 참조 카운트를 두고, 새 참조를 만들거나 버릴 때 늘리고 줄인다(빌린 참조는 그대로이고, 3.12부터 immortal 객체는 카운트가 안 바뀐다 — C API 문서 "Reference Counting")(참조 카운트 일반은 [language/09](../09-memory-management-models/2-summary.md)).
- 이 증감이 원자적이 아니면 위처럼 갱신이 사라진다. 모든 증감을 원자 연산으로 바꾸면 단일 스레드도 느려진다.
- 용어집의 설명: 인터프리터 전체를 잠그면 객체 모델(`dict` 같은 내장 타입 포함)이 동시 접근에 "암묵적으로 안전"해져 구현이 단순해진다. 대가는 멀티프로세서 병렬성의 상당 부분이다.

### 3. GIL은 **내 코드**의 원자성을 보장하지 않는다

```text
  g += 1  의 바이트코드 (3.12)        GIL 전환이 끼어들 수 있는 곳(3.12 구현)
  LOAD_GLOBAL g                      JUMP_BACKWARD(루프 끝), CALL 계열 명령 뒤 등
  LOAD_CONST 1                       → "읽기 ~ 쓰기" 사이에 CALL이 없으면 우연히 안 끼어든다
  BINARY_OP +=                       → 사이에 함수 호출을 넣으면 끼어든다
  STORE_GLOBAL g
```

- CPython 3.12 소스 `Python/bytecodes.c`에서 전환 요청 검사(`CHECK_EVAL_BREAKER()`)는 `JUMP_BACKWARD`와 `CALL` 계열 명령에 있다. 함수 진입의 `RESUME`도 eval breaker를 직접 확인한다.
- 실험 2: 원고 §10의 `g += 1`(스레드 50개 × 10만 번)은 3.12에서 3회 모두 정확히 5,000,000이었다. 읽기와 쓰기 사이에 `abs(0)` 호출 하나를 넣자 1,797,065~2,884,197로 깨졌다(사실 점검 재실행 6회: 2,941,076~3,734,654 — 값은 실행마다 다르다).
- 결론: "결과가 맞게 나온다"는 **구현 세부의 우연**이다. 언어 차원의 보장이 아니다. 공유 상태는 `threading.Lock`으로 보호한다.
  - 참고: 원고 §10은 `g += 1` 코드가 "매번 다른 값이 나온다"고 적는다. 3.12 이 환경에서는 재현되지 않았다. 그래도 같은 절의 결론(락이 필요하다)은 그대로 맞다. free-threading 문서도 내장 타입의 내부 락보다 `threading.Lock`을 쓰라고 권한다.

### 4. GIL을 없애려면 — PEP 703과 3.13 free-threading 빌드

```text
  기본 빌드(3.12·3.13·3.14)          free-threaded 빌드(3.13+, --disable-gil)
  GIL 1개 → 바이트코드 1개씩           GIL 없음 → 스레드가 코어마다 동시에
  (GIL은 인터프리터마다 하나)
  refcount 증감 = 평범한 연산          biased reference counting: 만든 스레드는 싸게, 남은 원자 연산
                                     immortal 객체(상수 등 — 3.12부터 기본 빌드에도 있음): 카운트를 아예 안 바꿈
  pymalloc                           mimalloc(스레드 안전 할당기)
```

- 기본 빌드의 GIL은 **인터프리터 하나**에 하나다. 3.12부터 C API(`Py_NewInterpreterFromConfig`)로 자기 GIL을 가진 서브인터프리터를 만들면 한 프로세스 안에서도 병렬로 돌 수 있다(C API 문서 "A Per-Interpreter GIL"). 이 노트의 실험은 보통의 단일 인터프리터다.
- PEP 703 "Making the Global Interpreter Lock Optional in CPython": 상태 Final, Python-Version 3.13.
- 켜는 법(용어집·free-threading HOWTO): `--disable-gil`로 빌드한 인터프리터를 `-X gil=0` 또는 `PYTHON_GIL=0`으로 실행한다.
  - 확인: `sys._is_gil_enabled()`, `sysconfig.get_config_var("Py_GIL_DISABLED")`.
  - free-threading 지원 표시가 없는 C 확장을 import하면 GIL이 **자동으로 다시 켜지고** 경고가 나온다(HOWTO).
- 비용
  - PEP 703 표(pyperformance 1.0.6): 단일 스레드 오버헤드 6%(Skylake)·5%(Zen 3), 다중 스레드 8%·7%.
  - HOWTO(3.14판): 평균 오버헤드 약 1%(macOS aarch64)~8%(x86-64 Linux). 메모리 사용도 대개 늘어난다.
- 이 호스트에는 free-threaded 빌드 이미지가 없어 직접 재지 않았다. 실험은 기본 3.12 빌드만이다.

### 5. 다른 런타임의 "GIL 같은" 제약

| 런타임 | 제약 | 병렬 계산을 하려면 |
|---|---|---|
| CPython(기본 빌드) | 한 인터프리터 안에서 한 번에 한 스레드만 바이트코드 실행 | `multiprocessing`·프로세스 워커, GIL을 놓는 C 확장, free-threaded 빌드 |
| Node.js(V8) | JS 코드는 이벤트 루프 스레드 하나에서 실행 | `worker_threads`(메모리는 `ArrayBuffer` 전달·`SharedArrayBuffer`로만 공유), `cluster`·프로세스 |
| Java(HotSpot) | GIL 없음. 스레드가 코어마다 동시에 실행 | 그대로 병렬. 대신 데이터 레이스는 언어 메모리 모델로 직접 다룬다([language/13](../13-language-memory-model/2-summary.md)) |

- Node 문서: Worker는 "CPU 집약적 JavaScript 작업"에 유용하고 I/O 집약 작업에는 별 도움이 안 된다. `child_process`·`cluster`와 달리 메모리를 공유할 수 있다(`ArrayBuffer` 이전, `SharedArrayBuffer` 공유).
- Python `multiprocessing` 문서: 스레드 대신 하위 프로세스를 써서 GIL을 "비켜 간다(side-stepping)". 대가는 프로세스 기동·데이터 직렬화(pickle)·메모리 복제다.

### 실험 1: CPU·C 확장·I/O — 스레드 vs 프로세스 (CPython 3.12)

```python
def cpu(n=3_000_000):          # 순수 파이썬 바이트코드
    s = 0
    for i in range(n): s += i * i
    return s
BUF = b"x" * (64 * 1024 * 1024)
def hash_big(_=None): return hashlib.sha256(BUF).hexdigest()   # C 코드가 GIL을 놓는 일
def io(_=None): time.sleep(0.2)                                  # 기다리는 일
# 각각 4개(또는 10개)를 차례로 / ThreadPoolExecutor / ProcessPoolExecutor 로 돌린다
```

환경: `python:3.12-slim`(3.12.14), `--cpus=2 --cpuset-cpus=2,4`(서로 다른 물리 코어 2개), 3회.

```text
  3.12.14 switchinterval = 0.005 gil_enabled = n/a
                               1회     2회     3회
  cpu  serial x4              2.12s   1.92s   2.05s
  cpu  threads(4)             2.00s   2.11s   2.61s     ← 직렬과 같다
  cpu  processes(4)           1.07s   1.04s   1.30s     ← 코어 2개만큼 약 2배
  sha256 64MB serial x4       0.52s   0.54s   0.58s
  sha256 64MB threads(4)      0.27s   0.34s   0.33s     ← 스레드인데 빨라진다(GIL을 놓는 C 코드)
  sleep 0.2 serial x10        2.00s   2.00s   2.00s
  sleep 0.2 threads(10)       0.20s   0.21s   0.20s     ← 기다리는 동안 GIL을 놓는다
```

- `gil_enabled = n/a`: 3.12.14에는 `sys._is_gil_enabled()`가 없었다(free-threading HOWTO가 "새" 함수로 소개한다).
- 처음에 `--cpuset-cpus=2,3`으로 돌렸을 때는 `processes(4)`도 2.08·2.11초로 빨라지지 않았다. `lscpu`에서 CPU 2·3은 같은 물리 코어(CORE 1)의 하이퍼스레드다. 측정 코어는 물리 코어 단위로 고른다.
- `--cpuset` 없이 `--cpus=2`만 준 3회에서는 `processes(4)` 1.24~1.40초, `sha256 threads(4)` 0.20~0.24초였다. 쿼터만으로는 어느 논리 CPU에 놓일지 정해지지 않아 값이 흔들린다(해석).

### 실험 2: GIL 아래의 경쟁 조건 (CPython 3.12)

```python
def plain():                  # 원고 §10의 코드
    global g
    for _ in range(100_000): g += 1
def with_call():              # 읽기와 쓰기 사이에 함수 호출 하나
    global g
    for _ in range(100_000):
        x = g; abs(0); g = x + 1
# 각각 스레드 50개, 3회. 기대값 5,000,000
```

```text
  plain     trial0: 5,000,000   trial1: 5,000,000   trial2: 5,000,000
  with_call trial0: 2,884,197   trial1: 1,797,065   trial2: 2,667,112

  사실 점검 재실행 2묶음(각 3회): plain 6회 모두 5,000,000, with_call 2,941,076 ~ 3,734,654
```

### 실험 3: 원고 §9 측정의 재현 (CPython 3.12)

원고 §9는 "순수 파이썬 CPU 연산"을 스레드 4개로 돌려 `멀티스레드: 62.182초 / 싱글스레드: 0.643초`라고 적는다. 같은 코드(요소 1,000개 × 100회 연산)를 3회 돌렸다.

```text
  멀티스레드 0.035s / 0.037s / 0.038s     (사실 점검 재실행 0.029 / 0.028 / 0.031s)
  싱글스레드 0.030s / 0.030s / 0.032s     (사실 점검 재실행 0.026 / 0.027 / 0.028s)
```

- 이 환경에서 멀티스레드는 싱글스레드보다 약 5~25% 느렸다(6회의 실행별 비율). "안 쓰느니만 못하다"는 방향은 맞다.
- 원고의 약 100배 차이와 60초대 절대값은 재현되지 않았다. 원고의 측정 환경·코드 차이를 확인할 수 없어 원인은 모른다.

### 실험 4: 다른 런타임 — Node의 CPU 작업 (node 22)

```js
function cpu(n = 300_000_000) { let s = 0; for (let i = 0; i < n; i++) s = (s + i * i) % 1_000_003; return s; }
// 메인 스레드에서 cpu() 두 번 vs worker_threads 2개가 각각 cpu() 한 번
```

환경: `node:22-alpine`(v22.23.2), `--cpus=2 --cpuset-cpus=2,4`, 3회.

```text
  main thread x2    26.80s / 26.02s / 25.34s     (사실 점검 재실행 24.82s)
  worker_threads 2  13.51s / 13.27s / 13.31s     (사실 점검 재실행 12.77s)
```

- JS 코드는 이벤트 루프 스레드 하나에서만 돈다. 계산 두 개를 병렬로 하려면 실행 환경(워커)을 따로 띄워야 한다.

## 쓰이는 자료구조·알고리즘

- **전역 상호 배제 락 1개** — 커널 뮤텍스·조건 변수 위에 만든 "인터프리터 전체의 락". 전환 요청은 플래그(eval breaker)로 알린다. 락 구현 일반은 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md), 조건 변수는 [os/17](../../os/17-condition-variables-and-monitors/2-summary.md).
- **참조 카운트** — GIL이 지키는 대상. 순환 참조는 따로 순환 GC가 잡는다([language/09](../09-memory-management-models/2-summary.md)).
- **biased reference counting** — 객체 헤더에 "주인 스레드 ID, 주인용 로컬 카운트, 공유 카운트" 세 정보를 둔다(PEP 703). 주인 스레드는 원자 연산 없이 로컬 카운트만 바꾼다.
- **프로세스 풀 + 작업 큐** — `ProcessPoolExecutor`는 작업을 큐로 보내고 결과를 pickle로 돌려받는다. 블로킹 큐 + 워커 구조는 [language/16](../16-concurrency-design-patterns/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원인 가르기

```text
  스레드를 늘렸는데 처리량이 그대로, CPU는 코어 1개만 100%  → GIL(CPU 위주 파이썬 코드)
  스레드를 늘렸는데 처리량이 늘었다                          → I/O 대기이거나 GIL을 놓는 C 코드
  프로세스로 바꿨더니 빨라졌지만 메모리가 N배               → 프로세스마다 인터프리터·데이터 복제
```

```bash
# 코어별 사용률: 1개만 100%면 GIL 의심
top -H -p <pid>                  # 스레드별 CPU
py-spy dump --pid <pid>          # (설치돼 있다면) 스레드별 현재 파이썬 스택 — 이 노트 실험에서는 쓰지 않음
python -X importtime app.py      # 시작이 느릴 때 import 시간(GIL과 별개 증상)
```

### 2. 고르는 순서 (CPython 기본 빌드)

1. **I/O 위주** → 스레드 또는 `asyncio`. 지금 구조 그대로 효과가 있다(실험 1의 sleep).
2. **계산이 라이브러리(NumPy·hashlib·zlib) 안에서 일어난다** → 그 라이브러리가 GIL을 놓는지 확인하고 스레드로 시도한다.
3. **순수 파이썬 계산** → `ProcessPoolExecutor`. 넘기는 데이터를 작게(pickle 비용), 워커 수는 물리 코어 수 근처.
4. **그래도 부족** → 계산 핵심을 C/Rust 확장·벡터화로, 또는 free-threaded 빌드 검토(확장 호환성 확인 필수).

```python
# 3번: 웹 요청 처리 중 무거운 계산을 프로세스 풀로
from concurrent.futures import ProcessPoolExecutor
pool = ProcessPoolExecutor(max_workers=2)        # 예시 값: 물리 코어 수 근처
def handle(req):
    fut = pool.submit(resize, req.image_bytes)   # 인자·결과는 pickle로 오간다
    return fut.result(timeout=5)
```

### 3. Java와 비교할 때

- Java 21(HotSpot)에는 GIL이 없다. 같은 계산을 스레드 4개로 나누면 코어 수만큼 빨라질 수 있다.
- 대신 GIL이 덮어 주던 문제가 그대로 드러난다. `HashMap`을 락 없이 공유하면 유실·손상이 난다([data-structure/29](../../data-structure/29-concurrent-data-structures/2-summary.md)). 가시성 규칙은 [language/13](../13-language-memory-model/2-summary.md).

## 장애 시나리오와 대처

### 1. CPU 바운드 멀티스레드가 안 빨라짐 (⚠)

- **현상**: 배치 처리를 스레드 8개로 나눴는데 시간이 그대로거나 더 느리다.
- **보이는 형태**: `top`에서 프로세스 CPU 약 100%(코어 1개분), 코어가 8개여도. 스레드 수를 바꿔도 처리 시간 변화 없음(실험 1: threads(4) 2.00~2.61s vs serial 1.92~2.12s).
- **원인**: CPython 기본 빌드는 한 번에 한 스레드만 바이트코드를 실행한다.
- **대처**: `ProcessPoolExecutor`(실험 1: 1.04~1.30s), 계산을 GIL을 놓는 확장으로 옮기기, 또는 free-threaded 빌드 검토.

### 2. "GIL이 있으니 안전하다"고 믿은 카운터가 틀린다

- **현상**: 테스트에서는 맞던 집계가 운영에서 조금씩 모자란다. 코드를 조금 고친(로그 한 줄 추가) 뒤부터 틀리기 시작했다.
- **원인**: GIL은 바이트코드 경계에서 스레드를 바꿀 뿐, 내 읽기-수정-쓰기를 묶어 주지 않는다. 그 사이에 전환 지점(함수 호출 등)이 생기면 갱신이 사라진다. 바이트코드 하나도 원자 단위가 아니다 — `+=`가 사용자 정의 `__iadd__` 같은 파이썬 코드를 부르면 그 안에서도 전환된다(실험 2: `abs(0)` 하나로 5,000,000 → 약 180만~370만, 실행마다 다름).
- **대처**: 공유 상태는 `threading.Lock`, 또는 `queue.Queue`로 소유권을 한 스레드에 모은다. free-threaded 빌드로 옮길 계획이 있으면 더더욱 그렇다.

### 3. 프로세스로 바꿨더니 메모리 N배·느린 시작

- **현상**: `multiprocessing`으로 CPU 문제는 풀렸는데 컨테이너 메모리가 워커 수만큼 늘어 OOMKilled.
- **원인**: 프로세스마다 인터프리터와 모듈·데이터를 따로 가진다. 큰 객체를 인자로 넘기면 pickle로 복사된다.
- **대처**: 워커 수를 물리 코어·메모리 한도에 맞춘다. 큰 읽기 전용 데이터는 `multiprocessing.shared_memory`나 파일 매핑으로 공유한다. 컨테이너 메모리 한도는 [os/13](../../os/13-oom-and-memory-limits/2-summary.md).

### 4. free-threaded 빌드에서 GIL이 다시 켜져 있다

- **현상**: 3.13t로 바꿨는데 스레드 확장이 여전히 안 된다.
- **보이는 형태**: 시작 시 경고, `sys._is_gil_enabled()`가 `True`.
- **원인**: free-threading 지원 표시가 없는 C 확장을 import하면 GIL이 자동으로 켜진다(HOWTO).
- **대처**: 확장의 free-threaded 휠 지원 여부를 확인한다. 강제로 끄려면 `PYTHON_GIL=0`/`-X gil=0`이지만, 지원 안 된 확장의 스레드 안전성은 보장되지 않는다(해석).

### 5. Node API 서버에서 CPU 작업이 모든 요청을 막는다

- **현상**: 보고서 생성 API가 돌 때 다른 API가 같이 멈춘다.
- **원인**: JS는 이벤트 루프 스레드 하나에서 돈다. Python GIL과 증상이 같은 런타임 제약이다([14번](../14-concurrency-models/2-summary.md) 실험 3).
- **대처**: `worker_threads`(실험 4: 2개로 약 2배), 별도 서비스·큐로 분리.

## 핵심 문장

- GIL은 언어가 아니라 CPython 구현의 제약이다. 한 번에 한 스레드만 바이트코드를 실행한다.
- GIL은 I/O 대기와, 놓도록 만든 C 확장의 계산 중에는 풀린다. 그래서 I/O·라이브러리 계산은 스레드로 빨라지고 순수 파이썬 계산은 안 빨라진다.
- GIL이 있는 이유는 참조 카운트를 포함한 객체 모델을 단순하게 지키기 위해서다. 대가는 멀티코어 병렬성이다.
- GIL은 내 코드의 읽기-수정-쓰기를 원자적으로 만들지 않는다. 우연히 맞는 결과는 구현 세부다.
- PEP 703의 free-threaded 빌드(3.13+)는 GIL 없이 돌지만 단일 스레드 오버헤드가 있고, 지원 안 된 C 확장이 GIL을 다시 켤 수 있다.

## 관련 주제·근거

- 선행
  - [14-concurrency-models](../14-concurrency-models/2-summary.md) — 스레드·이벤트 루프·가상 스레드
  - 원고 [foundations/process-thread](../../foundations/process-thread/README.md) §9 GIL 실험, §10 경쟁 조건, §11 Lock, §12 GIL
- 후속·연결
  - [09-memory-management-models](../09-memory-management-models/2-summary.md)(참조 카운트) · [13-language-memory-model](../13-language-memory-model/2-summary.md) · [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md)
  - [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) · [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) · [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) · [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)
  - [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- 근거
  - Python 용어집 "global interpreter lock" <https://docs.python.org/3/glossary.html#term-global-interpreter-lock>
  - Python 3.12 C API "A Per-Interpreter GIL" <https://docs.python.org/3.12/c-api/init.html> · "Reference Counting"(3.12 immortal 객체) <https://docs.python.org/3.12/c-api/refcounting.html> · 참조 소유권·빌린 참조 <https://docs.python.org/3.12/c-api/intro.html> · 데이터 모델 `__iadd__` <https://docs.python.org/3.12/reference/datamodel.html>
  - Python 3.12 `sys.setswitchinterval` <https://docs.python.org/3.12/library/sys.html> · `multiprocessing`(GIL을 비켜 가는 프로세스 기반) <https://docs.python.org/3.12/library/multiprocessing.html>
  - PEP 703 "Making the Global Interpreter Lock Optional in CPython" — Final, 3.13, biased reference counting·immortalization·mimalloc, 오버헤드 표 <https://peps.python.org/pep-0703/>
  - Python HOWTO "Python support for free threading"(3.14판) — `-X gil`·`PYTHON_GIL`, `sys._is_gil_enabled()`, 확장 import 시 GIL 재활성, 오버헤드 1~8% <https://docs.python.org/3/howto/free-threading-python.html>
  - CPython 3.12 소스 `Python/bytecodes.c` — `JUMP_BACKWARD`·`CALL` 계열의 `CHECK_EVAL_BREAKER()` <https://github.com/python/cpython/blob/3.12/Python/bytecodes.c>
  - Node.js 22 `worker_threads` <https://nodejs.org/docs/latest-v22.x/api/worker_threads.html>
- 실험 목록(i7-13700HX 호스트, 일회용 컨테이너 `--network none`)
  - 실험 1: `python:3.12-slim`(3.12.14), `--cpus=2 --cpuset-cpus=2,4` 3회(+ 사실 점검 재실행 2회: 직렬 1.91~2.15s, 스레드 2.17~2.19s, 프로세스 1.08~1.26s, sha256 스레드 0.28s — 위 표와 같은 경향) — CPU·sha256·sleep × 직렬/스레드/프로세스. 비교로 `--cpuset-cpus=2,3`(같은 물리 코어) 2회, `--cpus=2`만 3회
  - 실험 2: 같은 이미지, `--cpus=2` — `g += 1` vs 사이에 `abs(0)`, 스레드 50 × 10만, 3회(+ 점검 재실행 6회)
  - 실험 3: 같은 이미지 — 원고 §9 코드 그대로 3회(+ 점검 재실행 3회)
  - 실험 4: `node:22-alpine`(v22.23.2), `--cpus=2 --cpuset-cpus=2,4` — 메인 스레드 vs `worker_threads` 2개, 3회(+ 점검 재실행 1회)
