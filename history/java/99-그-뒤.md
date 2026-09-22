# Java — 그 뒤 (2026-09 기준)

> 이 문서는 **재서술이 아니라 새로 쓴 것**이다.\
> 앞의 jdk-1.0 ~ java-26 편은 `~/project/java-history/java/` 원본을 정본으로 두고 옮긴 것이지만, 이 편은 원본이 없다.\
> 그래서 「원문과 같은가」 대신 「**출처가 있는가**」로 검증한다 — 출처 없는 문장은 쓰지 않았다.
>
> **원본이 멈춘 자리**: `java-26.md` — Java 26 (2026-03-17 정식 출시)까지. 원본 repo 의 마지막 커밋은 2026-06-22.\
> **이 문서의 기준일**: 2026-09-20.

---

## 원본이 멈춘 자리

원본의 마지막 편은 **`java-26.md`** — Java 26(2026년 3월 17일 정식 출시, non-LTS)이다.\
그 편이 정리한 26의 JEP 10개는 정식 5개(500·504·516·517·522)와 프리뷰·인큐베이터 5개(524·525·526·529·530)였다.

그리고 원본은 끝을 이렇게 맺는다 — **"구조적 동시성·원시 타입 패턴·지연 상수는 아직 프리뷰로 남아, Loom·Amber·Valhalla 의 완성은 다음 LTS 의 숙제로 이어진다."**

**그 숙제의 다음 한 걸음이 이 문서가 다루는 전부다.**

---

## 그 뒤 무슨 일이 있었나

### Java 27 이 정식 출시됐다 — 2026년 9월 15일

**이 문서 기준일(2026-09-20)의 닷새 전이다.**\
OpenJDK 의 JDK 27 프로젝트 페이지가 배포 일정을 그대로 적고 있다.

| 일정 | 날짜 |
|---|---|
| Rampdown Phase One (main line 에서 분기) | 2026-06-04 |
| Rampdown Phase Two | 2026-07-16 |
| Release Candidate Phase | 2026-08-06 |
| Release Candidate Build | 2026-08-20 |
| **General Availability** | **2026-09-15** |

Java 26 이 2026-03-17 이었으니, 6개월 케이던스가 그대로 지켜졌다.

근거를 두 겹으로 둔다 — ⓐ JDK 27 프로젝트 페이지의 일정표에 GA 가 `2026/09/15` 로 적혀 있고, ⓑ 아래에서 하나씩 열어 본 27의 JEP 들이 모두 **Status `Closed / Delivered` · Release `27`** 로 표시돼 있다.

⚠️ **Java 27 은 LTS 가 아니다.**\
원본 26편이 적은 대로 다음 LTS 는 **Java 29 예정**이고, 이 문서가 확인한 범위에서 그 계획이 바뀌었다는 1차 발표는 없다.

### JDK 27 의 JEP 9개 — 정식 4 / 프리뷰·인큐베이터 5

JDK 27 프로젝트 페이지가 나열한 목록 전부다.\
괄호 안 표기는 **출처 표현 그대로**다.

| JEP | 제목 (원문) | 성격 |
|---|---|---|
| 523 | Make G1 the Default Garbage Collector in All Environments | 정식 |
| 527 | Post-Quantum Hybrid Key Exchange for TLS 1.3 | 정식 |
| 534 | Compact Object Headers by Default | 정식 |
| 536 | JFR In-Process Data Redaction | 정식 |
| 531 | Lazy Constants (**Third Preview**) | 3차 프리뷰 |
| 532 | Primitive Types in Patterns, instanceof, and switch (**Fifth Preview**) | 5차 프리뷰 |
| 533 | Structured Concurrency (**Seventh Preview**) | 7차 프리뷰 |
| 537 | Vector API (**Twelfth Incubator**) | 12차 인큐베이터 |
| 538 | PEM Encodings of Cryptographic Objects (**Third Preview**) | 3차 프리뷰 |

**정식으로 들어온 것 4개 중 하나도 26의 프리뷰 목록에서 올라온 게 아니다.**\
26에서 프리뷰·인큐베이터였던 다섯은 **다섯 다 그대로 프리뷰·인큐베이터로 한 차수씩만 올라갔다.**\
(아래 절에서 하나씩 본다.)

### 정식 ① 포스트 양자 하이브리드 키 교환 (JEP 527)

> **하이브리드 키 교환 (hybrid key exchange)** — 양자 내성 알고리즘과 기존 알고리즘을 **함께** 써서 키를 교환하는 방식.\
> 예 — JEP 527 요약 표현: "combining a quantum-resistant algorithm with a traditional algorithm".

JEP 527 은 TLS 1.3 용 하이브리드 키 교환 세 가지를 넣었다 — **X25519MLKEM768 · SecP256r1MLKEM768 · SecP384r1MLKEM1024**.\
ML-KEM(양자 내성)과 기존 ECDHE 를 결합한 것이다.\
**기본 선호 방식이 X25519MLKEM768 로 바뀌며**, `javax.net.ssl` API 를 쓰는 애플리케이션은 코드를 고칠 필요가 없다.

⚠️ 적용 범위는 좁게 못박혀 있다.\
JEP 의 Non-Goals 표현 그대로 — "It is not a goal to implement hybrid key exchange for any API other than `javax.net.ssl`, nor for any version of TLS other than 1.3."\
즉 **TLS 1.3 · `javax.net.ssl` 밖은 대상이 아니다.**


### 정식 ② 압축 객체 헤더가 기본값 (JEP 534)

> **압축 객체 헤더 (compact object headers)** — HotSpot JVM 이 객체마다 붙이는 머리말(헤더)을 줄인 레이아웃.\
> 예 — JEP 534 요약 표현: "reduce object headers from 96 bits down to 64 bits on 64-bit architectures".

JDK 27 부터 이게 **기본 레이아웃**이 된다.\
전에는 명령줄 플래그로 직접 켜야 했다.\
JEP 가 적은 효과는 셋이다 — "reducing heap size, improving deployment density, and increasing data locality".

끄는 방법도 JEP 에 적혀 있다 — `java -XX:-UseCompactObjectHeaders ...`.

### 정식 ③ G1 이 모든 환경의 기본 GC (JEP 523)

JDK 9 의 JEP 248 이래 G1 은 **서버 환경에서만** 기본이었다.\
자원이 빠듯한 환경 — JEP 표현으로 CPU 가 하나이거나 물리 메모리가 1792MB 미만인 시스템 — 에서는 JVM 이 **Serial** 컬렉터를 골랐다.

JEP 523 은 그 특례를 없앤다.\
Goals 표현 그대로:\
"When no garbage collector is specified on the command line: The HotSpot JVM will always select G1."

같은 Goals 가 조건도 함께 적는다 — 전에 Serial 이 선택되던 상황에서 처리량·지연·메모리 사용량·시작 시간이 "should not degrade significantly"(크게 나빠지지 않아야 한다).

⚠️ 원본 26편은 JEP 522 로 **G1 의 처리량이 개선**된 것을 다뤘다.\
27의 JEP 523 은 성능이 아니라 **기본값 선택 규칙**을 바꾼 것이다 — 다른 이야기다.

### 정식 ④ JFR 인프로세스 데이터 마스킹 (JEP 536)

JDK Flight Recorder 가 기록하는 것 중 **명령줄 인자·환경 변수와 시스템 속성의 초기값**을 가린다.\
핵심은 가리는 *시점*이다 — JEP 요약 표현으로 "Redact this data before it leaves the process, so that sensitive information does not leak".\
즉 기록 파일이 프로세스를 떠나기 **전에** 가린다.

---

## 정식이 안 된 채 남아 있던 것들은 어떻게 됐나

원본 26편이 프리뷰·인큐베이터로 남겨둔 다섯 개를 **하나씩** 따라간다.\
「정식이 됐다」로 읽히면 안 되므로 **차수와 상태를 출처 표현 그대로** 적는다.

| 기능 | Java 26 | Java 27 (2026-09-15) | 그 다음 — JDK 28 쪽 움직임 |
|---|---|---|---|
| 구조적 동시성 | JEP 525 · **6차 프리뷰** | JEP 533 · **7차 프리뷰** | JEP 543 — **정식화 제안, 상태는 Candidate** |
| 원시 타입 패턴 | JEP 530 · **4차 프리뷰** | JEP 532 · **5차 프리뷰** | 확인된 후속 JEP 없음 |
| Vector API | JEP 529 · **11차 인큐베이터** | JEP 537 · **12차 인큐베이터** | 확인된 후속 JEP 없음 |
| PEM Encodings | JEP 524 · **2차 프리뷰** | JEP 538 · **3차 프리뷰** | JEP 542 — **정식(preview 표기 없음), Release 28** |
| Lazy Constants | JEP 526 · **2차 프리뷰** | JEP 531 · **3차 프리뷰** | 색인 `Draft JEPs` 절에 초안 **Lazy Constants (Fourth Preview)** — JEP 번호 미부여, 상태 `Draft` |

**다섯 다 Java 27 에서도 정식이 되지 않았다.**\
한 차수씩 올라갔을 뿐이다.

### 구조적 동시성 — 7차 프리뷰, 그리고 처음으로 「정식화 제안」이 나왔다

JEP 533(7차 프리뷰)에서 API 가 또 손질됐다.\
JEP 가 적은 변경은 이렇다.

- `StructuredTaskScope` 와 `Joiner` 에 **세 번째 타입 파라미터 `R_X`** 가 생겼다 — `join()` 이 던질 수 있는 예외의 타입이다.
- `StructuredTaskScope` 에 **새 정적 `open` 메서드** 가 추가됐다(기본 join 정책 + `UnaryOperator` 로 설정을 만든다).
- `Joiner` 팩토리 메서드들이 결과가 예외일 때 `join()` 이 **`ExecutionException` 을 던지도록** 바뀌었다.
- `Joiner` 의 팩토리 메서드 **`awaitAll()` 이 제거**됐다.
- `Joiner` 의 **`onTimeout()` 이 `timeout()` 으로 대체**됐다 — 타임아웃으로 스코프가 취소되면 결과를 내거나 예외를 던진다.

⚠️ 원본 26편은 6차 프리뷰의 메서드명 정돈(`anySuccessfulResultOrThrow()` → `anySuccessfulOrThrow()` 등)을 적었다.\
**7차에서 또 바뀌었다** — 구조적 동시성은 차수마다 API 가 계속 움직이는 상태다.

그리고 **처음으로 정식화 제안이 나왔다.**

> **JEP 543: Structured Concurrency** — 제목에 프리뷰 표기가 없다.\
> 본문 표현: "We here propose to finalize Structured Concurrency in JDK 28, without further change."

⚠️ **아직 확정이 아니다.**\
JEP 543 의 **Status 는 `Candidate`** 이고, JDK 28 프로젝트 페이지의 대상 JEP 목록(2026-08-27 갱신분)에는 **아직 올라 있지 않다.**\
"JDK 28 에서 정식이 된다"고 읽으면 안 된다 — **그렇게 하자는 제안이 올라왔다**가 정확하다.

JEP 543 은 이 기능의 이력도 한자리에 적어 뒀다 — JEP 428(JDK 19)·437(JDK 20) 인큐베이터 → JEP 453(JDK 21) 프리뷰 → 462(22)·480(23)·499(24)·505(25)·525(26)·533(27) 재프리뷰.

### PEM Encodings — 다섯 중 정식화 JEP 이 `Completed` 인 것은 이것뿐이다

**JEP 542: PEM Encodings of Cryptographic Objects** — **제목에 프리뷰 표기가 없고**, Status 는 `Completed`, Release 는 **28** 이다.\
JEP 본문 표현: "We here propose to finalize the API without further change."

JEP 542 가 정리한 프리뷰 이력 — JEP 470(JDK 25) 1차 → JEP 524(JDK 26) 2차 → JEP 538(JDK 27) 3차 → 정식.

⚠️ 그래도 **아직 쓸 수 있는 게 아니다.**\
JDK 28 은 2026-09-20 현재 출시되지 않았다.

### Vector API — 왜 12차까지 인큐베이터인가

JEP 537 은 이유를 직접 적는다.

> "The Vector API will incubate until necessary features of Project Valhalla become available as preview features. At that time, we will adapt the Vector API and its implementation to use them and then promote the Vector API from incubation to preview."

즉 **Valhalla 의 필요한 기능이 프리뷰로 제공될 때까지** 인큐베이터에 머문다는 것이고, 그때 가서야 인큐베이터 → **프리뷰**로 올라간다(정식이 아니다).

27의 12차에는 **API 변경이 없었다** — "we here propose to re-incubate the Vector API in JDK 27 without API change".\
바뀐 것은 ARM·RISC-V 벡터 수학 intrinsic 에 쓰이는 번들 **SLEEF 라이브러리가 3.6.1 → 3.9.0** 으로 올라간 것뿐이다.

⚠️ 한편 Valhalla 쪽에서 **JEP 401: Value Objects (Preview)** 가 JDK 28 대상으로 올라와 있다(아래 참조).\
그리고 **JEP 537 은 JEP 401 을 지목한다** — Description 절의 「Run-time compilation」 과 Future Work 절, 두 곳에서 링크까지 달아 가리킨다.

> "We expect ultimately to declare vector classes as value classes, as proposed by Project Valhalla (JEP 401)."

**다만 어느 릴리스에서 프리뷰로 올릴지는 적지 않았다.**\
위에 인용한 대로 537 은 "until necessary features of Project Valhalla become available as preview features" 라고만 하고, JDK 28 이든 어느 번호든 지목하지 않는다.\
그래서 이 문서는 두 사실을 이어 "다음엔 Vector API 가 프리뷰가 된다"고 쓰지 않는다 — **방향은 537 에 있지만 시점은 출처에 없다.**

### 원시 타입 패턴 — 5차, 변경 없음

JEP 532 의 표현 그대로 — "We here propose to preview it for a fifth time, without change."\
26의 4차(JEP 530)에서 정확성(exactness) 정의를 다듬고 `switch` 의 dominance 검사를 조인 것이 마지막 변경이었다.

### Lazy Constants — 3차, API 가 정리됐다

JEP 531 이 적은 2차(JEP 526) 대비 변경 둘.

- 저수준 메서드 `isInitialized`·`orElse` **제거** — JEP 표현으로 "could be used in ways not consistent with the design goals of the API".
- **`Set.ofLazy(...)` 팩토리 메서드 추가** — 이로써 `List`·`Set`·`Map` 세 기본 컬렉션에 모두 lazy 판이 생겼다.

JEP 색인의 `Draft JEPs` 절에는 **Lazy Constants (Fourth Preview)** 초안이 올라 있다(이슈 8389764, 상태 `Draft`).\
**JEP 번호가 아직 붙지 않았고 대상 릴리스 표기도 없다** — 「4차 프리뷰가 확정됐다」로 읽으면 안 된다.

### String Templates — 여전히 철회 상태, 후속 JEP 을 확인하지 못했다

원본은 String Templates 가 JDK 23 에서 빠진 것을 다뤘다.\
OpenJDK JEP 색인에서 2026-09-20 현재 확인되는 것은 셋뿐이다.

| JEP | 제목 | 상태 |
|---|---|---|
| 430 | String Templates (Preview) | `Closed / Delivered` · Release 21 |
| 459 | String Templates (Second Preview) | `Closed / Delivered` · Release 22 |
| 465 | String Templates (Third Preview) | **`Closed / Withdrawn`** · Release 칸 비어 있음 |

**대체·후속 JEP 은 확인하지 못했다.**\
JEP 색인 전문에서 `String Template` 은 위 세 행에서만 나오고 `interpolation` 은 0회다 — 문자열 보간·템플릿 관련 새 항목이 없다.\
설계 논의가 메일링 리스트에서 계속되고 있는지는 이 조사 범위에서 판단하지 않는다.

---

## 아직 안 끝난 것

JDK 28 프로젝트 페이지(2026-08-27 갱신)에 **대상으로 올라 있는** JEP 목록이다.\
**JDK 28 은 출시되지 않았고**, 이 페이지에서 GA 날짜를 확인하지 못했다.

| JEP | 제목 (원문) | 성격 |
|---|---|---|
| 401 | Value Objects (**Preview**) | 프리뷰 — Project **Valhalla** |
| 535 | Shenandoah GC: Generational Mode by Default | 기본값 변경 |
| 539 | Strict Field Initialization in the JVM (**Preview**) | 프리뷰 |
| 540 | Simple JSON API (**Incubator**) | 인큐베이터 |
| 541 | Deprecate the macOS/x64 Port for Removal | 제거 예고 |
| 542 | PEM Encodings of Cryptographic Objects | 정식 |

**JEP 401 (Value Objects)** 가 눈에 띈다 — 원본이 "Valhalla 의 완성은 다음 LTS 의 숙제"라고 남긴 그 프로젝트다.

> **값 객체 (value object)** — 불변이고 **객체 식별자(identity)가 없는** 객체. 필드 값만으로 구별된다.\
> 예 — JEP 401 요약 표현: "Value objects ... are distinguished solely by the values of their fields, and can be represented by Java Virtual Machines in ways that improve performance."

JEP 401 의 Goals 가 밝힌 범위 — `==` 를 포함한 모든 연산이 식별자가 아닌 **필드 값**으로 구별하도록 개발자가 **선택(opt in)** 하게 하고, `Integer`·`LocalDate` 같은 기존 불변 클래스를 이 모델로 **호환 이행**시킨다.\
그리고 **Goals 가 명시한 제약 하나** — "The Java language should continue to operate on just two kinds of data: primitives and object references."\
(이 문장은 Non-Goals 가 아니라 **Goals 절 안**에 있다.\
Non-Goals 절은 따로 있고 내용이 다르다.)

⚠️ **프리뷰다.**\
Status 는 `Integrated`, Release 는 28 — **출시된 기능이 아니다.**

아직 대상으로 확정되지 않은 채 떠 있는 것 둘.

| JEP | 제목 | 상태 | 비고 |
|---|---|---|---|
| 543 | Structured Concurrency | **Candidate** | 본문이 JDK 28 정식화를 **제안** |
| 544 | Ahead-of-Time Code Compilation | **Proposed to Target** (Release 28) | Project **Leyden** |

JEP 544 의 목표 문장 — "Improve startup and warmup time by making optimized native code for an application instantly available when the HotSpot Java Virtual Machine starts."\
원본 26편이 다룬 **JEP 516**(모든 GC 에서의 AOT 객체 **캐싱**)과의 관계는 조심해서 적어야 한다.\
JEP 544 본문에 "JEP 516" 이라는 문자열은 **한 번도 나오지 않는다.**\
대신 Goals 의 한 항목 "Continue to support the Serial, Parallel, G1, and ZGC garbage collectors" 에 걸린 **링크가 JEP 516 을 향한다** — 「516 이 넓힌 GC 범위를 그대로 지원하겠다」는 뜻이고, 544 가 `Relates to` 로 적은 것은 JEP 483·JEP 515 다.\
⚠️ 따라서 **「캐싱의 다음 걸음이 코드 컴파일」이라는 연결은 이 문서의 추론이다** — JEP 544 가 그렇게 적은 곳은 없다.

⚠️ `Candidate` 와 `Proposed to Target` 은 **대상 확정이 아니다.**\
빠질 수 있다.

### LTS

원본이 적은 대로 **다음 LTS 는 Java 29 예정**이다.\
Java 27 이 LTS 로 지정됐다거나 LTS 주기가 바뀌었다는 1차 발표는 **확인하지 못했다.**

---

## 용어 풀이

이 문서에서 처음 나온 용어만 모았다(정의는 각각 첫 등장 자리에 있다).

| 용어 | 한 줄 |
|---|---|
| **하이브리드 키 교환** | 양자 내성 알고리즘과 기존 알고리즘을 함께 써서 키를 교환하는 방식 (JEP 527, 정식) |
| **압축 객체 헤더** | 64비트 아키텍처에서 객체 헤더를 96비트 → 64비트로 줄인 레이아웃 (JEP 534, 27부터 기본값) |
| **값 객체 (value object)** | 불변이고 객체 식별자가 없어 필드 값만으로 구별되는 객체 (JEP 401, JDK 28 프리뷰 대상) |

JEP 상태 표기도 정리해 둔다 — 이 문서가 옮긴 표기들이다.\
**JEP 1(JEP Process)이 정의한 것만 정의로 적고**, 그 문서에 정의가 없는 표기는 「정의를 찾지 못했다」로 둔다.

| 표기 | 근거 |
|---|---|
| `Candidate` | JEP 1 정의 — "Accepted for inclusion in the Roadmap by the OpenJDK Lead" |
| `Completed` | JEP 1 정의 — "Finished and delivered" |
| `Withdrawn` | JEP 1 정의 — "Withdrawn by the author; may be re-drafted later" |
| `Closed / Delivered` · `Integrated` · `Proposed to Target` | 각 JEP 페이지 **Status 필드**에 그대로 표시된 값이다. **JEP 1 에 정의가 없어 이 문서는 뜻을 적지 않는다.** |

⚠️ 그래서 이 문서는 상태 표기를 **해석하지 않고 그대로 옮긴다.**\
다만 **색인의 절 제목을 상태로 읽지 않도록** 한 가지를 못박아 둔다.

JEP 색인(JEP 0)은 전체를 일곱 절로 나눈다 — `Process` · `Informational` · `In-flight` · `Submitted` · `Draft` · `Delivered Feature and Infrastructure` · `Withdrawn`.\
**`In-flight JEPs` 는 절 제목이지 상태값이 아니다**(JEP 1 에 그런 상태 정의도 없다).\
예컨대 JEP 542 는 개별 JEP 페이지에서 `Completed` 이고, 색인에서도 `In-flight JEPs` 절 **안의 상태 칸이 `Com`(Completed)·Release 칸이 `28`** 이다 — 두 표기는 엇갈리지 않는다.\
그러니 `In-flight` 절에 있다는 이유로 "출시됐다"로 읽으면 안 된다.\
**JDK 28 은 아직 나오지 않았다.**

---

## 출처

**1차 출처** — openjdk.org 의 JEP 문서·JDK 프로젝트 페이지

| # | 제목 | URL |
|---|---|---|
| J1 | JDK 27 프로젝트 페이지 (JEP 목록·일정, GA 2026/09/15) | https://openjdk.org/projects/jdk/27/ |
| J2 | JDK 28 프로젝트 페이지 (대상 JEP 목록, 2026-08-27 갱신) | https://openjdk.org/projects/jdk/28/ |
| J3 | JEP 0: JEP Index (절 구성·상태 칸 확인 — String Templates 430/459/465, JEP 539~544, `Draft` 절의 Lazy Constants 초안) | https://openjdk.org/jeps/0 |
| J3b | JEP 1: JEP Process (상태 표기 정의 — Candidate·Completed·Withdrawn) | https://openjdk.org/jeps/1 |
| J4 | JEP 523: Make G1 the Default Garbage Collector in All Environments | https://openjdk.org/jeps/523 |
| J5 | JEP 527: Post-Quantum Hybrid Key Exchange for TLS 1.3 | https://openjdk.org/jeps/527 |
| J6 | JEP 531: Lazy Constants (Third Preview) | https://openjdk.org/jeps/531 |
| J7 | JEP 532: Primitive Types in Patterns, instanceof, and switch (Fifth Preview) | https://openjdk.org/jeps/532 |
| J8 | JEP 533: Structured Concurrency (Seventh Preview) | https://openjdk.org/jeps/533 |
| J9 | JEP 534: Compact Object Headers by Default | https://openjdk.org/jeps/534 |
| J10 | JEP 536: JFR In-Process Data Redaction | https://openjdk.org/jeps/536 |
| J11 | JEP 537: Vector API (Twelfth Incubator) | https://openjdk.org/jeps/537 |
| J12 | JEP 542: PEM Encodings of Cryptographic Objects | https://openjdk.org/jeps/542 |
| J13 | JEP 543: Structured Concurrency (정식화 제안, Candidate) | https://openjdk.org/jeps/543 |
| J14 | JEP 544: Ahead-of-Time Code Compilation (Proposed to Target, 28) | https://openjdk.org/jeps/544 |
| J15 | JEP 401: Value Objects (Preview) | https://openjdk.org/jeps/401 |
| J16 | JEP 465: String Templates (Third Preview) — Status 필드 `Closed / Withdrawn` 확인 | https://openjdk.org/jeps/465 |

**2차 출처** — 길잡이로만 썼고, 본문 사실은 전부 위 1차에서 확인했다.\
이 문서 본문에는 2차 출처에만 근거한 문장이 **없다.**

**부정 주장의 근거 — 어느 페이지를 열어 무엇을 찾았는지**

「없다」·「지목하지 않는다」는 마지막 사건이 아니라 **색인**으로 뒷받침한다.\
이 문서의 부정은 전부 아래에서 왔다.

| 부정 주장 | 연 곳 | 찾은 방법과 결과 |
|---|---|---|
| JDK 28 의 GA 날짜를 확인하지 못했다 | J2 (2026/8/27 14:17 UTC 갱신) | 페이지에 일정표(Rampdown·GA) 자체가 없다. 실린 것은 "JEPs targeted to JDK 28, so far" 목록뿐이고, "JEPs proposed to target JDK 28" 표는 비어 있다 |
| JEP 543 이 JDK 28 대상 목록에 없다 | J2 | 목록은 401·535·539·540·541·542 여섯 개다 — 543·544 는 없다 |
| String Templates 의 대체·후속 JEP 이 없다 | J3 (JEP 색인 전문) | `String Template` 은 430·459·465 세 행에서만, `interpolation` 은 **0회** 나온다 |
| 원시 타입 패턴·Vector API 의 후속 JEP 이 없다 | J3 | `In-flight`·`Submitted`·`Draft` 세 절에서 해당 제목을 찾지 못했다(두 기능의 행은 전부 `Delivered` 절에 있다) |
| JEP 537 이 프리뷰 승격 **시점**을 적지 않았다 | J11 (JEP 537 원문) | 원문에서 `401` 과 `Valhalla` 를 전수로 찾아 두 자리(Description·Future Work)를 확인했다. 두 곳 모두 릴리스 번호를 적지 않는다 |
| JEP 544 가 JEP 516 을 「다음 걸음」이라 적지 않았다 | J14 (JEP 544 원문) | 본문에 "JEP 516" 문자열 **0회**. `jeps/516` 링크는 Goals 의 GC 지원 항목 한 곳뿐이고, `Relates to` 는 JEP 483·515 다 |
| Java 27 의 LTS 지정이 바뀌지 않았다 | J1 (JDK 27 프로젝트 페이지) | 페이지 전문에 `LTS`·`long-term` 이 **0회** — LTS 지정은 이 페이지가 싣는 정보가 아니다. **벤더(Oracle 등)의 지원 정책 문서는 이 조사에서 열지 않았다** |

⚠️ 위 확인은 **요약이 아니라 원문 HTML 을 받아 문자열을 직접 찾는 방식**으로 했다.\
요약만 믿으면 「544 가 516 을 참조한다」·「색인의 542 는 In-flight 다」 같은 오독이 그대로 들어온다.

**열지 않은 문서**

- JEP 538(PEM 3차 프리뷰)·JEP 535·539·540·541 의 개별 JEP 문서는 열지 않았다 — 제목·차수는 J1·J2 프로젝트 페이지의 목록 표기를 따랐다.
- Oracle 등 벤더의 Java 지원 로드맵 문서는 열지 않았다(위 표 마지막 행).

**참고 — 원본 repo**: `~/project/java-history/java/` (마지막 편 `java-26.md`, 마지막 커밋 2026-06-22). 읽기만 했다.
