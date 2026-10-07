# language/21-language-choice-tradeoffs — "틀렸을 때 어떻게 틀리는가"로 언어 고르기 — 정리 (힌트)

## 해결하는 문제

언어를 "벤치마크 순위"로 고르면, 정작 운영에서 비싼 실패를 놓친다.

```text
  같은 버그: 정수 넘침, 배열 밖 접근, 무시한 에러
  ┌ 컴파일 거부       → 배포 전에 멈춘다
  ├ 즉시 예외·panic    → 그 자리에서 멈추고 로그가 남는다        (시끄러운 실패)
  ├ 정의된 틀린 값     → 에러 없이 틀린 숫자로 계속 돈다         (조용한 실패)
  └ 미정의 동작        → 틀린 값 + 남의 메모리까지 번질 수 있다   (조용한 실패, 최악)
```

- *조용한 실패(silent failure)*: 에러 없이 틀린 값을 남기는 실패. 정합성이 중요한 시스템(원장·정산·재고)에서는 크래시보다 비싸다. 크래시는 알림이 오지만, 조용한 오답은 대사(reconciliation)나 고객 민원으로 늦게 발견된다.
- 원고 [languages/README.md](../../../languages/README.md) 축 ①의 한 문장: 언어는 "얼마나 빠른가"가 아니라 "틀렸을 때 어떻게 틀리는가", "그 도메인의 지식이 어디에 쌓여 있는가", "5년 뒤 누가 고치는가"로 갈린다. 성능은 넷째 축이 아니라 이 셋 안에 흩어져 있다.

쉬운 예: 체중계 세 대.
- A는 고장 나면 "Err"를 띄운다.
- B는 고장 나면 항상 0kg을 띄운다.
- C는 고장 나면 옆 사람 몸무게를 띄울 때도 있다.

똑같은 구조다.\
A = 예외를 던지는 언어·연산, B = 정의된 엉뚱한 값을 내는 언어·연산, C = 미정의 동작이 있는 언어다. 매일 재는 데 쓰려면 "가장 정확한 체중계"보다 "고장 났을 때 Err를 띄우는 체중계"가 낫다.

실무 예:
- Java `int`로 누적 금액을 계산하다 21억을 넘자 잔액이 음수가 됐다. 예외는 없었다.
- 프런트엔드(JS)가 서버의 64비트 주문 ID를 `Number`로 받아 끝자리가 바뀌었고, 다른 주문을 갱신했다.
- Go 코드에서 `n, _ := strconv.Atoi(s)`로 에러를 버려 잘못된 입력이 0으로 저장됐다.

## 동작·원리

### 1. 같은 버그를 다섯 언어에 넣어 본다

- 문서의 "안전하다"보다 실제 출력이 판단 근거가 된다. 흔한 버그 다섯 가지를 같은 모양으로 각 언어에 넣었다.

### 실험 1: 실패 모양 비교 (`e21/Fail.java`·`fail.go`·`fail.py`·`fail.js`·`fail.c`)

환경: `eclipse-temurin:21-jdk`(21.0.12), `golang:1.23-alpine`(go1.23.12), `python:3.12-slim`(3.12.14), `node:22-alpine`(v22.23.2), 호스트 gcc 13.3.0 `-O0`. `--cpus=2`, `--network none`.

| 버그 | Java 21 | Go 1.23 | Python 3.12 | node 22 | C(gcc 13 -O0) |
|---|---|---|---|---|---|
| 32비트 최댓값 + 1 | `-2147483648` (조용히 감김) | `-2147483648` (감김) | `2147483648` (넘침 없음) | `(2147483647+1)\|0` → `-2147483648` | UB — [language 20](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 같은 넘침, 검사 연산 | `Math.addExact` → `ArithmeticException: integer overflow` | 상수식이면 **컴파일 오류**(`overflows`) | — | `Number.MAX_SAFE_INTEGER + 2` → `9007199254740992`(정밀도 손실, 조용) | `__builtin_add_overflow` |
| 길이 3 배열의 [5] | `ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3` | `panic: runtime error: index out of range [5] with length 3`, 종료 코드 2 | `IndexError('list index out of range')` | `undefined` (조용) | UB — 이 빌드에서는 실행마다 다른 정수(예: `159879248`·`-432788448`)가 조용히 찍혔다(보장 없음) |
| 숫자 파싱 실패 `"12a"` | `NumberFormatException` — `catch {}`로 삼켜도 컴파일 통과 | `n, _ := Atoi` → `0` (조용). `err`를 받고 안 쓰면 **컴파일 오류** `declared and not used: err` | `ValueError` — `except: pass`로 삼킬 수 있음 | `Number("12a")` → `NaN`, `parseInt("12a")` → `12` (조용) | `atoi("12a")` → `12` (조용) |
| 처리 안 한 비동기 실패 | ([language 16](../16-concurrency-design-patterns/2-summary.md) 실험 4: 조용) | — | — | `Promise.reject` 미처리 → **프로세스 종료**, exit 1 | — |
| `0.1 + 0.2` | `0.30000000000000004` | 변수면 같음, 상수식은 `0.3` | 같음 | 같음 | — |

- 같은 "버그"가 언어마다 다른 등급의 실패가 됐다. 한 언어 안에서도 **연산·관례마다** 등급이 다르다(Java `+` vs `Math.addExact`, JS `Number()` vs `parseInt()`).
- 명세 근거
  - Java: JLS §15.18.2 — 정수 덧셈이 넘치면 결과는 2의 보수 하위 비트, 부호가 수학적 합과 다르다.
  - Go: 명세 "Integer overflow" — 부호 있는 넘침도 정의된 값, panic이 아니다. "Run-time panics" — 범위 밖 인덱스는 런타임 panic.
  - Python: 표준 타입 문서 — "Integers have unlimited precision."
  - JS: MDN `Number.MAX_SAFE_INTEGER` = 2^53 − 1 = `9007199254740991`. 그보다 큰 정수는 정확히 표현된다는 보장이 없다.
  - node: Node.js 22 CLI 문서 `--unhandled-rejections` — v15.0.0부터 기본 모드가 `throw`(처리 안 한 거부를 잡히지 않은 예외로 올림). 그 전에는 경고였다.
  - Rust(이 호스트에 없음, 문서로): The Rust Book 3.2 — 배열 범위 밖 인덱스는 **런타임 panic**, 정수 넘침은 디버그 빌드에서 panic·`--release`에서 2의 보수 감김(Rust Reference는 release 동작을 "panic 또는 감김, 구현 재량"으로 둔다).

### 2. 안전을 어느 통화로 사는가 — 축은 둘이다

```text
                     메모리 안전              데이터 레이스 없음
  C / C++           개발자 규율 (UB)         개발자 규율 (UB)
  Java·Kotlin(JVM)  런타임(GC·경계 검사)     ✗ — 경쟁 결과는 명세가 제한하지만 값이 어긋날 수 있다
  Go                런타임(GC·경계 검사)     ✗ — 여러 워드짜리 값의 경쟁은 메모리 손상까지 갈 수 있다
  Rust              컴파일러(소유권·차용)    컴파일러(Send·Sync)
                    (safe Rust 한정 — `unsafe` 블록의 정확성은 개발자 몫)
                    ↑ 실행 자원으로 지불      ↑ 사람의 시간(학습·설계·빌드)으로 지불
```

- 원고 [languages/rust/언어-특성](../../../languages/rust/언어-특성/README.md) §9의 정리: "안전한가"를 한 축으로 보면 틀린다. GC는 첫째 축만 준다. 세 진영의 차이는 같은 안전을 **운영 사고(C++)·실행 자원(Go·JVM)·사람의 시간(Rust)** 중 어느 통화로 내느냐다. 어느 쪽도 데드락과 논리적 순서 버그는 막지 못한다.
- 런타임 탐지기의 비용(원 출처 확인)
  - Clang ASan 문서: 일반적 감속 약 2배.
  - Go race detector 문서: 메모리 5~10배, 실행 시간 2~20배까지 늘 수 있다. 실행된 경로의 레이스만 찾는다.
- 참고: 원고 [languages/README.md](../../../languages/README.md) 비교표와 rust 원고 §9의 "Go·JVM — 데이터 레이스는 정의되나 값이 어긋남"은 Go에 대해 너무 약하다. Go 메모리 모델은 기계어 한 워드보다 큰 값(인터페이스·맵·슬라이스·문자열)의 경쟁이 "단일 쓰기에 대응하지 않는 값"을 낼 수 있고, 그것이 "임의의 메모리 손상"으로 이어질 수 있다고 적는다(<https://go.dev/ref/mem>).
- 참고: 원고 [languages/README.md](../../../languages/README.md) 비교표의 Rust "경계 위반의 결과 = 컴파일 거부"는 일반적으로 틀리다. The Rust Book 3.2 "Invalid Array Element Access"는 사용자 입력 인덱스가 범위를 넘으면 "런타임 오류"로 panic하는 예를 보이고, "컴파일러가 사용자가 넣을 값을 알 수 없으므로 이 검사는 런타임에 일어나야 한다"고 적는다. 컴파일에서 막히는 것은 소유권·차용·수명(시간 축)이고, 경계(공간 축)는 런타임 panic이다.

### 3. 실행 모형과 기동 — 층이 요구하는 조건

```text
  네이티브 (C·Go·Rust)            : 실행 파일 하나, 런타임 초기화가 작다     → 짧게 뜨는 프로세스·작은 데몬
  바이트코드 + JIT (JVM·.NET)     : 로드·검증·워밍업 후 최고 성능           → 오래 사는 서버
  인터프리터 (CPython 3.12)       : 시작은 중간, 생태계·개발 속도 (JIT는 3.13부터 실험적 빌드 옵션)
  인터프리터 + JIT (V8)           : 시작은 중간, 생태계·개발 속도
```

- 원고 [languages/java/언어-특성](../../../languages/java/언어-특성/README.md)의 한 문장: JVM은 "결정을 실행 시점까지 미룬다"(바이트코드·클래스로더·JIT·GC). 그 판단 비용을 상각할 만큼 **오래 사는가**가 JVM이 값을 내는 조건이다. 계층 컴파일·워밍업은 [language 01](../01-compile-interpret-jit/2-summary.md)·[23](../23-jit-tiered-compilation-and-warmup/2-summary.md), AOT는 [24](../24-aot-native-image-and-startup/2-summary.md).

### 실험 2: hello world 기동 시간 (`e21/hello`)

컨테이너 안에서 프로세스 시작~종료 벽시계(ms), 7회 × 2라운드를 집필·점검에서 한 번씩(합 28회), `--cpus=2`. 같은 컨테이너의 `true`를 기준선으로 같이 쟀다(`date` 호출 비용 포함). C·Go·Python은 `python:3.12-slim`, node는 `node:22-bookworm-slim`(alpine의 busybox `date`는 나노초를 주지 않아 0으로 찍혔다), Java는 `eclipse-temurin:21-jdk`. 호스트는 다른 작업이 돌던 24코어 기계라 범위는 이 호스트·이 부하에 한정된다.

```text
  기준선 true               : 1~4ms (Debian 계열 이미지), 8~15ms (temurin 이미지)
  C   (gcc -O2 -static)     : 3~4
  Go  (go build, 정적)       : 4~6
  Python 3.12 (-I)          : 35~55
  node 22                   : 50~91 (집필 첫 회 190)
  Java 21 (javac 후 java -cp): 59~105     (temurin 이미지 기준선 8~15 포함)
  Java 21 -Xshare:off        : 123~198    (클래스 데이터 공유 끔)
```

- 수십 배 차이가 난다. 호출마다 새로 뜨는 CLI·짧은 배치·스케일 0에서 시작하는 함수에서는 이것이 지연 그 자체다.
- 오래 사는 서버에서는 같은 수치가 거의 무의미하다(한 번 뜨면 몇 주를 돈다). **같은 수치가 층에 따라 결정적이기도, 무의미하기도 하다**(원고 Go 언어-특성 「핵심 문장」).
- `-Xshare:off`가 2배 가까이 느렸다(중앙값 기준 약 1.7~1.8배). CDS가 덜어 주는 클래스 로딩 비용이 이 환경의 기동에서 작지 않다는 해석과 맞는다(기동 시간 중 클래스 로딩 비율 자체는 재지 않았다). 콜드 스타트 대처는 [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md).

### 4. 표현력 — "불법 상태를 표현 불가능하게"

- Kotlin(원고 kotlin 언어-특성 §2·§3): `String`과 `String?`가 다른 타입이라 null 검사를 컴파일러가 강제한다. `sealed` + `else` 없이 상태를 열거한 `when`은 상태를 추가하면 처리 안 한 분기가 컴파일 오류가 된다(Kotlin 1.7+ — `when` 문은 1.6까지 경고, 식으로 쓴 `when`은 원래 오류. `else`가 있으면 조용히 그리로 간다). 단 Java 상호운용의 **플랫폼 타입**에서는 검사가 유예된다.
- Go(원고 go 언어-특성 §8): 합 타입·열거형·불변 한정자가 없다. Go FAQ는 합 타입을 "인터페이스와 혼란스럽게 겹쳐" 넣지 않았다고 적는다. 그래서 상태 분기 누락을 `default: panic`·린터가 막아야 한다.
- 타입으로 불변식을 세우는 설계는 [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md), 에러 모델은 [language 08](../08-error-handling-models/2-summary.md).

### 5. 같은 진영 안에서는 생태계가 가른다

- 원고 [languages/c-cpp-csharp.md](../../../languages/c-cpp-csharp.md): C#/.NET은 실행 모형(중간 언어 → JIT, 세대별 이동 GC)이 JVM과 사실상 같다. 기술로 갈리지 않으면 결정은 **그 도메인에 쌓인 코드·사람·문서**로 넘어간다. 생태계는 낯섦을 줄여 위험(stakes)을 낮추는 요인이지, 기술 판단을 생략해도 되는 근거는 아니다.
- C가 커널·임베디드에 남는 이유는 "빠르다"가 아니라 "의지할 런타임이 아래에 없다"이다(같은 원고). 배제 사유는 "나쁘다"가 아니라 "요구가 겹치지 않는다"이다.

### 6. 층별 배치 — 결론은 한 시스템 안에서도 층마다 다르다

```text
  질문: 이 층의 실패 모드를 무엇이 가장 싸게 막는가?
  돈의 불변식을 타입으로 세우는 층     → null 안전·sealed·값 타입 (예: Kotlin/JVM)
  입력 받고 호스트를 다루는 작은 데몬   → 단일 바이너리·밀리초 기동 (예: Go)
  런타임을 못 얹거나 정지가 곧 위반     → 소유권으로 두 축을 컴파일에 (예: Rust)
  I/O 대기가 지배하는 릴레이·배치       → 언어 바꿔도 병목이 그대로 (DB·외부 API)
```

- 원고 rust 언어-특성 §10: 대기가 비용인 워크로드에서는 실행 속도를 몇 배 올려도 총 지연이 거의 그대로다. 언어 교체의 재판정 신호는 **측정된** CPU·GC 정지 병목이다.

## 쓰이는 자료구조·알고리즘

- **합 타입(태그 유니언) + 완결성 검사** — `sealed`/`enum` 분기를 컴파일러가 빠짐없이 확인한다. 상태 누락을 컴파일 오류로 바꾸는 장치다. [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md)
- **경계 = 포인터 + 길이** — 안전한 언어의 배열·슬라이스는 길이를 들고 다니며 접근마다 범위를 확인한다. 컴파일러가 안전을 증명하면 비교 명령은 지운다(경계 검사 제거 — Go `test/checkbce.go`)([language 20](../20-undefined-behavior-and-memory-safety/2-summary.md)).
- **임의 정밀도 정수** — Python `int`처럼 자릿수 배열로 수를 표현해 넘침이 없다. 대신 연산이 상수 시간이 아니다. 고정 소수점 금액은 `BigDecimal`·정수 최소 단위(원·센트).
- **결정 표(평가 행렬)** — 후보 언어 × 실패 등급·층 조건·생태계 칸을 채워 비교한다. 칸은 "벤치마크"가 아니라 실험 1 같은 실측으로 채운다.

## 적용 — 풀어나가는 법

1. **도메인의 최악 실패를 먼저 적는다.** 정합성 시스템이면 "조용한 오답", 실시간 시스템이면 "정지", 보안 경계면 "메모리 누출".
2. **후보 언어마다 실험 1의 표를 채운다.** 정수 넘침·경계·파싱·에러 무시·비동기 실패·부동소수가 각각 어느 등급인지. 문서가 아니라 실행으로 확인한다.
3. **층 조건을 대 본다.** 기동(실험 2)·상주 메모리·배포 형태(단일 바이너리·컨테이너)·런타임 유무.
4. **생태계·팀을 본다.** 그 도메인의 라이브러리·운영 도구·사람이 어디에 있나. 5년 뒤 누가 고치나.
5. **고른 언어의 조용한 경로를 관례·도구로 막는다.**

```java
// Java — 금액은 넘침 검사 연산 또는 BigDecimal
total = Math.addExact(total, amount);                    // long total — 넘치면 ArithmeticException
BigDecimal fee = price.multiply(rate).setScale(0, RoundingMode.HALF_EVEN);
```

```ts
// TS/JS — 64비트 ID는 문자열이나 BigInt로, 숫자 파싱은 실패를 검사
const id: string = row.order_id;                         // JSON에서 문자열로 받는다
if (!/^-?\d+$/.test(input)) throw new Error(`invalid integer: ${input}`); // Number("")·Number("  ")는 0이 된다
const n = Number(input);
if (!Number.isSafeInteger(n)) throw new Error(`invalid integer: ${input}`);
```

   - Go: 에러 무시를 CI에서 막는다(원고 go 언어-특성 §6: 반환 에러를 무시해도 컴파일러는 막지 않고, `errcheck` 린터를 걸어야 강제된다).
   - C/C++: [language 20](../20-undefined-behavior-and-memory-safety/2-summary.md)의 새니타이저 빌드를 CI에.
   - 어느 언어든: 비동기 실패를 사슬 끝에서 받는다([language 16](../16-concurrency-design-patterns/2-summary.md)).

## 장애 시나리오와 대처

### 1. 조용히 감기는 정수 → 잔액·재고가 음수

- **현상**: 큰 거래·누적에서 잔액이 갑자기 음수나 엉뚱한 값이 된다. 에러 로그는 없다.
- **보이는 형태**: 값이 2^31(약 21억) 또는 2^63 근처에서 부호가 뒤집힌다. 실험 1의 Java·Go `MAX+1 = -2147483648`.
- **원인**: Java·Go의 정수 넘침은 명세상 정의된 감김이다. 예외가 아니다.
- **대처**: 금액·수량에 `Math.addExact`류(넘치면 예외)나 `long`·`BigDecimal`. 상한 불변식을 DB 제약으로도 건다. Go는 연산 전 범위 검사.

### 2. JS가 64비트 ID의 정밀도를 잃는다

- **현상**: 프런트엔드가 보낸 ID로 조회하면 다른 레코드가 나오거나 404.
- **보이는 형태**: 서버 로그의 ID와 클라이언트의 ID가 끝자리만 다르다. 실험 1에서 `MAX_SAFE_INTEGER + 2`가 `9007199254740992`로 나왔다(정확한 값은 …993).
- **원인**: JS `Number`는 2^53 − 1을 넘는 정수를 정확히 담는다는 보장이 없다. `JSON.parse`도 숫자를 `Number`로 만든다.
- **대처**: 큰 ID는 JSON에서 문자열로 주고받는다. 계산이 필요하면 `BigInt`.

### 3. 에러를 버리는 관례 → 실패가 성공으로 기록된다

- **현상**: 잘못된 입력이 0·빈 값으로 저장된다. 사용자에게는 "저장됨".
- **보이는 형태**: 데이터에 0·기본값이 비정상적으로 많다. 로그에 실패가 없다. 실험 1의 Go `n, _ := Atoi("12a")` → 0, Java `catch {}`, Python `except: pass`, C `atoi("12a")` → 12.
- **원인**: 언어가 에러 무시를 허용하고(Go `_`, 빈 `catch`), 팀 관례가 그것을 막지 않았다. 반대로 Go는 받은 `err`를 안 쓰면 컴파일을 거부하므로 "받고 잊기"는 막는다 — 막히는 것은 "아예 `_`로 버리기"가 아니다.
- **대처**: 린터(Go `errcheck`, 빈 catch 금지 규칙)를 CI 차단 조건으로. 파싱은 실패를 반환·예외로 받는 API만 쓴다(`parseInt`·`atoi` 대신 `Number`+형식·범위 검사, `strtol`+`errno`(범위)+`endptr`(숫자가 있었나·끝까지 읽었나) — `strtol("12a")`는 `errno` 0으로 12를 준다).

### 4. 메모리 비안전 언어의 조용한 오염

- **현상**: 재현 안 되는 값 오염, 다른 요청 데이터 섞임.
- **보이는 형태**: 실험 1의 C `arr[5]`가 오류 없이 값을 냈다. 사고 사례는 [language 20](../20-undefined-behavior-and-memory-safety/2-summary.md)·[27](../27-pl-incidents/2-summary.md)(Cloudbleed·Heartbleed).
- **원인**: C·C++의 경계·수명 위반은 미정의 동작이라 언어가 막지 않는다.
- **대처**: 새 코드는 메모리 안전 언어로(CISA 2023 로드맵), 기존 코드는 새니타이저·퍼징·경계 API.

### 5. 층에 맞지 않는 실행 모형 → 기동·메모리 비용

- **현상**: 호출마다 뜨는 CLI·서버리스 함수가 느리고, 작은 데몬 수십 개의 메모리 합이 크다.
- **보이는 형태**: 실험 2에서 같은 hello world가 Go 4~6ms, Java 59~105ms. 함수 콜드 스타트 p99가 길다.
- **원인**: JVM은 오래 살아서 판단 비용을 상각하는 모형인데, 짧은 프로세스에서는 상각할 시간이 없다.
- **대처**: 그 층만 네이티브 언어나 AOT([language 24](../24-aot-native-image-and-startup/2-summary.md))로. 코어 서비스까지 바꿀 이유는 아니다 — 층마다 답이 다르다.

## 핵심 문장

- 언어는 벤치마크 순위가 아니라 "틀렸을 때 어떻게 틀리는가", 지식이 어디에 쌓였나, 누가 고치나로 고른다.
- 같은 버그가 언어·연산마다 컴파일 거부·즉시 예외·조용한 틀린 값·미정의 동작 중 다른 등급이 되며, 정합성 시스템에서는 조용한 등급이 가장 비싸다.
- GC 언어는 메모리 안전만 주고 데이터 레이스 없음은 주지 않으며, Go에서는 여러 워드짜리 값의 경쟁이 메모리 손상까지 갈 수 있다.
- 안전의 비용은 사라지지 않고 운영 사고·실행 자원·사람의 시간 중 어디로 옮겨질 뿐이다.
- 기동 시간 같은 수치는 짧게 뜨는 층에서는 결정적이고 오래 사는 층에서는 무의미하므로, 한 시스템 안에서도 층마다 다른 언어가 맞을 수 있다.
- 어떤 언어를 고르든 그 언어의 조용한 경로(감기는 정수·정밀도 손실·무시한 에러)를 관례와 린터로 막아야 한다.

## 관련 주제·근거

- 선행
  - [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md)
  - [10-garbage-collection](../10-garbage-collection/2-summary.md), [08-error-handling-models](../08-error-handling-models/2-summary.md), [13-language-memory-model](../13-language-memory-model/2-summary.md), [01](../01-compile-interpret-jit/2-summary.md)·[23](../23-jit-tiered-compilation-and-warmup/2-summary.md)·[24](../24-aot-native-image-and-startup/2-summary.md)(실행 모형·워밍업·AOT)
- 원고(병합 대상)
  - [languages/README.md](../../../languages/README.md) 축 ① — 비교표 세 개, 관통 문장
  - [languages/c-cpp-csharp.md](../../../languages/c-cpp-csharp.md) — 두 진영, C의 실패 계급, RAII, C#≈JVM
  - [languages/go/언어-특성](../../../languages/go/언어-특성/README.md) · [languages/java/언어-특성](../../../languages/java/언어-특성/README.md) · [languages/kotlin/언어-특성](../../../languages/kotlin/언어-특성/README.md) · [languages/rust/언어-특성](../../../languages/rust/언어-특성/README.md)
- 후속·연결
  - [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) · [software-design/16-error-strategy-exceptions-vs-results](../../software-design/16-error-strategy-exceptions-vs-results/2-summary.md)
  - [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md) — 조용한 실패 계열 · [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md)
- 명세·문서
  - JLS SE21 §15.18.2(정수 덧셈 넘침) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html> · Java API `Math.addExact`
  - Go 명세 "Integer overflow"·"Run-time panics" <https://go.dev/ref/spec> · The Go Memory Model(여러 워드 값의 경쟁 → 임의 메모리 손상) <https://go.dev/ref/mem> · Data Race Detector(메모리 5~10배·실행 2~20배) <https://go.dev/doc/articles/race_detector> · Go FAQ(합 타입 없음)
  - Python 3 표준 타입 — "Integers have unlimited precision" <https://docs.python.org/3/library/stdtypes.html>
  - MDN `Number.MAX_SAFE_INTEGER` <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER> · Node.js 22 CLI `--unhandled-rejections`(v15.0.0 기본 `throw`) <https://nodejs.org/docs/latest-v22.x/api/cli.html>
  - The Rust Programming Language 3.2 "Data Types" — Integer Overflow(디버그 panic·release 감김), Invalid Array Element Access(런타임 panic) <https://doc.rust-lang.org/book/ch03-02-data-types.html>
  - Clang AddressSanitizer("Typical slowdown … 2x") · CISA 외 "The Case for Memory Safe Roadmaps"(2023-12)
- 실험(로컬 컨테이너 `--cpus=2`·`--network none` + 호스트 gcc 13.3.0)
  - `e21/Fail.java`·`fail.go`·`unused.go`·`constov.go`·`fail.py`·`fail.js`·`fail.c` — 넘침·검사 연산·범위 밖 인덱스·파싱 실패·에러 무시·처리 안 한 거부·부동소수
  - `e21/hello` — C·Go·Python·node·Java(CDS 기본/끔) 기동 7회 × 2라운드(집필·점검 각 1벌), 이미지별 `true` 기준선
