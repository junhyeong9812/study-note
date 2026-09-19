# Java 25 (2025.09) — LTS

> 원본: `~/project/java-history/java/java-25.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·수치·자바 코드블록 5개와 셸 코드블록 1개·「릴리스 정보」의 JEP 목록·「참고 출처」는 원문 그대로다.\
> ASCII 도식 2개는 원문 mermaid 도식 2개를 글자로 옮긴 것이고, 새로 그린 도식은 없다.\
> 「한눈에」의 손목 밴드 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「이 편의 기능은 지금 어디쯤인가」 표의 「그 앞」·「그 뒤」 칸은 같은 시리즈의 다른 편(`java-21.md`~`java-24.md`·`java-26.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 21에 이은 차세대 LTS. 스코프드 값·모듈 임포트 선언·유연한 생성자 본문·컴팩트 소스 파일과 인스턴스 main을 정식화하고, 컴팩트 객체 헤더·세대별 Shenandoah를 안정화한 집대성 릴리스.

이 편에서 정식이 된 것 하나를 비유로 읽으면 **행사장 입구에서 손목 밴드를 받아 차고 들어가면, 안에서 어느 부스에 가든 그 밴드가 그대로 통하는 일**이다.\
밴드는 행사장 안에서만 쓸모가 있고, 안에서 고쳐 쓸 수도 없다.\
**Scoped Values도 똑같은 구조다** — 원문 자신이 그 절에서 이렇게 적는다: "값은 명시된 동적 범위(`run`/`call`) 안에서만 유효하며 불변이다."

본문 흐름에 쓰는 비유는 이 손목 밴드 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 행사장(입장부터 퇴장까지) | 동적 범위 — 원문 표현으로 "명시된 동적 범위(`run`/`call`)" |
| 입구에서 밴드를 채우는 일 | 바인딩 — 원문 도식 라벨로 "ScopedValue.where(USER, user)" |
| 손목 밴드 | 그 범위에 매인 값 — 원문 도식 라벨로 "불변 값 user" |
| 안쪽의 부스들 | 원문 표현으로 "동적 범위 안의 호출 트리 하위" |
| 밴드를 고쳐 쓸 수 없는 점 | 원문 표현으로 "불변이다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **LTS라고 해서 모든 것이 정식인 것은 아니다.** 원문이 「영향과 의의」에서 못 박은 그대로다 — "다만 구조적 동시성·원시 타입 패턴·Vector API·String Templates(보류) 등은 여전히 미완으로 남아, 다음 LTS(예정상 Java 29)로 숙제를 넘긴다."
- **이 편에서 처음 만들어진 기능은 많지 않다.** 원문이 「시대적 배경」에서 적은 성격이 "여러 프로젝트의 결실을 안정화해 모은다"이고, 원문이 정식 기능 대부분에 이전 편의 경로를 함께 적어 둔다.

### 이 편의 기능은 지금 어디쯤인가

가운데 칸은 이 편 원문이 적은 것이고, 양옆 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 그 앞 | 이 편(25)에서의 상태 | 그 뒤 |
|---|---|---|---|
| Scoped Values (JEP 506) | `java-20.md` 인큐베이터(JEP 429) → `java-21.md` 1차 프리뷰(JEP 446) → 22·23·24에서 2·3·4차 | **정식** | — |
| Module Import Declarations (JEP 511) | `java-23.md` 1차 프리뷰(JEP 476) · `java-24.md` 2차(JEP 494) | **정식** | — |
| Compact Source Files and Instance Main Methods (JEP 512) | `java-21.md` 1차 프리뷰(JEP 445, 당시 이름 "미명명 클래스와 인스턴스 main 메서드") → 22·23·24에서 이름을 바꿔 가며 2·3·4차 | **정식** | — |
| Flexible Constructor Bodies (JEP 513) | `java-22.md` 1차 프리뷰(JEP 447, 당시 이름 "Statements before super(...)") · `java-23.md` 2차 · `java-24.md` 3차 | **정식** | — |
| Key Derivation Function API (JEP 510) | `java-24.md` 1차 프리뷰(JEP 478) | **정식** | — |
| Compact Object Headers (JEP 519) | `java-24.md` 실험적(JEP 450) | **정식** | — |
| Generational Shenandoah (JEP 521) | `java-24.md` 실험적(JEP 404) | **정식** | — |
| Remove the 32-bit x86 Port (JEP 503) | `java-21.md` JEP 449(폐기 예고) → `java-24.md` JEP 479(윈도우 제거)·JEP 501(폐기 예고) | **정식**(완전 제거) | — |
| Stable Values (JEP 502) | — (이 편이 1차) | 프리뷰 | `java-26.md`에서 "Lazy Constants"로 개명해 2차 프리뷰(JEP 526) — **아직 정식이 아니다** |
| PEM Encodings of Cryptographic Objects (JEP 470) | — (이 편이 1차) | 프리뷰 | `java-26.md` 2차 프리뷰(JEP 524) — **아직 정식이 아니다** |
| Structured Concurrency (JEP 505) | `java-19.md` 인큐베이터(JEP 428)부터 이어진 줄기 | 5차 프리뷰 | `java-26.md` 6차 프리뷰(JEP 525) — **아직 정식이 아니다** |
| Primitive Types in Patterns, instanceof, and switch (JEP 507) | `java-23.md` 1차 프리뷰(JEP 455) · `java-24.md` 2차(JEP 488) | 3차 프리뷰 | `java-26.md` 4차 프리뷰(JEP 530) — **아직 정식이 아니다** |
| Vector API (JEP 508) | `java-16.md`의 1차 인큐베이터부터 이어진 줄기 | 10차 인큐베이터 | `java-26.md` 11차 인큐베이터(JEP 529) — **아직 정식이 아니다** |
| JFR CPU-Time Profiling (JEP 509) | — | **실험적**(리눅스) | — |

Scoped Values 행의 「그 앞」 칸만 이 편 원문과 어긋나 보인다 — 이 편 원문 본문은 그 경로를 "22~24의 여러 프리뷰"로 적어 `java-21.md`의 1차 프리뷰(JEP 446)를 빼고 세지만, 위 칸은 그 편들의 원문에 대고 1차부터 채웠다.

## 릴리스 정보
- 정식 출시일: 2025년 9월 16일
- LTS 여부: **예** (장기 지원 / Oracle 기준 최소 8년 지원). 직전 LTS는 Java 21(2023.09)
- 포함 JEP 목록 (총 18개):
  - JEP 470: PEM Encodings of Cryptographic Objects (프리뷰)
  - JEP 502: Stable Values (프리뷰)
  - JEP 503: Remove the 32-bit x86 Port (정식)
  - JEP 505: Structured Concurrency (5차 프리뷰)
  - JEP 506: Scoped Values (정식)
  - JEP 507: Primitive Types in Patterns, instanceof, and switch (3차 프리뷰)
  - JEP 508: Vector API (10차 인큐베이터)
  - JEP 509: JFR CPU-Time Profiling (실험적)
  - JEP 510: Key Derivation Function API (정식)
  - JEP 511: Module Import Declarations (정식)
  - JEP 512: Compact Source Files and Instance Main Methods (정식)
  - JEP 513: Flexible Constructor Bodies (정식)
  - JEP 514: Ahead-of-Time Command-Line Ergonomics (정식)
  - JEP 515: Ahead-of-Time Method Profiling (정식)
  - JEP 518: JFR Cooperative Sampling (정식)
  - JEP 519: Compact Object Headers (정식)
  - JEP 520: JFR Method Timing & Tracing (정식)
  - JEP 521: Generational Shenandoah (정식)

> **LTS(장기 지원)** — 오래 보안 패치를 받는 버전. 원문이 이 편에 붙인 기간이 "Oracle 기준 최소 8년 지원"이고, 직전 LTS로 든 것이 Java 21(2023.09)이다.\
> 예: 같은 시리즈 `java-21.md`도 21·17·25를 "함께 장기 지원 라인"으로 묶어 적는다 — 두 편이 같은 지정을 서로 확인해 준다.

## 시대적 배경

Java 21 이후 2년간(22·23·24) 프리뷰·인큐베이터·실험 단계를 거쳐 온 기능들이 마침내 정식 안착하는 LTS 릴리스다.\
기업·프레임워크가 실제로 장기간 채택할 기준 버전이므로, "여러 프로젝트의 결실을 안정화해 모은다"는 성격이 강하다.\
**Project Loom**의 스코프드 값(정식)과 구조적 동시성(여전히 프리뷰), **Project Amber**의 모듈 임포트·유연한 생성자 본문·컴팩트 소스 파일(모두 정식), **Project Leyden**의 AOT 메서드 프로파일링·명령행 인체공학(정식), **Project Valhalla**로 가는 길목의 컴팩트 객체 헤더(정식) 등이 한자리에 모였다.\
또한 32비트 x86 포트가 완전히 제거되며 한 시대를 마감했다.

이 문단이 이 편의 성격을 한 줄로 보여 준다 — 같은 Project Loom 안에서도 스코프드 값은 정식이고 구조적 동시성은 프리뷰다. **갈래 이름이 아니라 기능 하나하나가 각자의 단계를 갖는다.**

> **Project Valhalla** — 원문이 컴팩트 객체 헤더를 "가는 길목"으로 부르는 갈래의 이름.\
> 예: 원문은 같은 시리즈에서 이 갈래를 한 번 더 언급한다 — Vector API가 10차 인큐베이터에 머무는 사유로 든 것이 "Valhalla 의존성"이다.

## 주요 추가 기능

### Scoped Values (JEP 506, 정식)
- 스레드(특히 가상 스레드) 간 불변 데이터를 `ThreadLocal`보다 안전하고 효율적으로 공유한다. 22~24의 여러 프리뷰를 거쳐 LTS에서 정식화되었다. 값은 명시된 동적 범위(`run`/`call`) 안에서만 유효하며 불변이다.

> **동적 범위(dynamic scope)** — 코드에 적힌 괄호 범위가 아니라, 실행이 그 안에 머무는 동안이라는 범위. 원문 표현으로 "명시된 동적 범위(`run`/`call`)"다.\
> 예: 아래 코드에서 `run(...)`이 부른 `handleRequest()`와 그 아래 호출 전부가 도는 동안이 그 범위이고, 원문이 그 자리에 단 주석이 "이 범위 안에서만 CURRENT_USER.get() 가능"이다.

```java
final static ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

ScopedValue.where(CURRENT_USER, user).run(() -> {
    handleRequest();          // 이 범위 안에서만 CURRENT_USER.get() 가능
});
```

아래 흐름도는 Scoped Value의 전파를 보여준다. `where(...).run(...)`으로 바인딩한 불변 값이 동적 범위 안의 호출 트리 하위로 자동 전파되어, `ThreadLocal`처럼 명시적으로 인자를 넘기지 않고도 하위 메서드에서 `get()`으로 읽을 수 있다. (Java 25에서 Scoped Values는 정식 기능이다.)

```text
ScopedValue.where(USER, user)
   │
   v
run(() -> handleRequest())
   │
   v
handleRequest()   ····USER.get()····┐
   │                                │
   v                                │
service()         ····USER.get()····┼──>  불변 값 user
   │                                │
   v                                │
repository()      ····USER.get()····┘
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 세로로 내려가는 실선 화살표 넷과 오른쪽으로 나가는 점선 셋으로, 원문의 화살표 일곱과 수·방향이 같다.
- 칸 이름(`ScopedValue.where(USER, user)`·`run(() -> handleRequest())`·`handleRequest()`·`service()`·`repository()`·`불변 값 user`)과 점선에 붙은 `USER.get()`은 전부 원문의 라벨 그대로다.
- 점선 셋이 닿는 곳은 **같은 칸 하나**다 — 원문도 세 점선을 `불변 값 user` 한 칸에 잇는다. 값이 셋 생기는 것이 아니라 하나를 셋이 읽는 것이다.

### Module Import Declarations (JEP 511, 정식)
- 모듈이 export하는 모든 패키지를 한 줄로 임포트한다. 23 프리뷰 → 24 2차 프리뷰 → 25 정식.

```java
import module java.base;
import module java.sql;

void main() {
    var list = List.of(1, 2, 3);     // java.util.* 자동 가용
}
```

### Compact Source Files and Instance Main Methods (JEP 512, 정식)
- 초보자 친화 진입점이 정식화되었다(여러 차례 프리뷰를 거쳐 명칭이 "Compact Source Files"로 확정). 클래스 선언과 `String[] args` 없이 인스턴스 `main` 메서드만으로 프로그램을 작성할 수 있고, 콘솔 입출력 헬퍼(`java.lang.IO`)를 제공한다.

원문이 괄호에 적은 "여러 차례 프리뷰"의 실물은 같은 시리즈에서 확인된다 — `java-21.md`의 JEP 445("미명명 클래스와 인스턴스 main 메서드"), `java-22.md`의 JEP 463·`java-23.md`의 JEP 477("Implicitly Declared Classes and Instance Main Methods"), `java-24.md`의 JEP 495("Simple Source Files and Instance Main Methods")다. **이름이 넷이다(세 번 바뀌었다 — 22·23은 같은 이름이다).**

```java
// 클래스/메서드 시그니처 보일러플레이트 없이 실행 가능
void main() {
    IO.println("Hello, Java 25!");
}
```

### Flexible Constructor Bodies (JEP 513, 정식)
- 명시적 생성자 호출(`super(...)`/`this(...)`) 이전에 인자 검증·필드 준비 등의 문장을 둘 수 있다. JDK 22의 JEP 447에서 출발해 LTS에서 정식화되었다.

```java
class Measurement {
    final double value;
    Measurement(double value) { this.value = value; }
}

class Temperature extends Measurement {
    Temperature(double celsius) {
        if (celsius < -273.15)                    // 명시적 super(...) 호출 전 검증
            throw new IllegalArgumentException("절대영도 미만");
        super(celsius);                           // 검증 뒤에 오는 명시적 부모 생성자 호출
    }
}
```

위 코드에서 원문이 말한 "이전에"가 눈에 보인다 — `super(celsius);`보다 위에 `if (celsius < -273.15)` 검증이 놓여 있고, 원문이 두 줄에 붙인 주석이 "명시적 super(...) 호출 전 검증"과 "검증 뒤에 오는 명시적 부모 생성자 호출"이다.

### Key Derivation Function API (JEP 510, 정식)
- HKDF 등 키 유도 함수(KDF)를 위한 표준 API가 정식화되었다(24 프리뷰 → 25 정식). 포스트양자 암호 등 현대 프로토콜에 필요한 키 파생을 표준화한다.

> **키 유도 함수(KDF)** — 이미 가진 비밀에서 실제로 쓸 키를 뽑아내는 함수. 원문 표현으로 "키 파생"이고, 원문이 예로 든 이름이 HKDF다.\
> 예: 아래 코드의 `KDF.getInstance("HKDF-SHA256")`이 그 HKDF이고, 마지막 줄 `hkdf.deriveKey("AES", params)`가 뽑아내는 자리다.

```java
KDF hkdf = KDF.getInstance("HKDF-SHA256");
AlgorithmParameterSpec params = HKDFParameterSpec.ofExtract()
        .addIKM(secretKey).addSalt(salt).thenExpand(info, 32);
SecretKey derived = hkdf.deriveKey("AES", params);
```

### Compact Object Headers (JEP 519, 정식)
- 객체 헤더를 (보통) 12바이트에서 8바이트로 줄여 힙 메모리 사용량을 절감한다. 24의 실험적 기능에서 LTS에서 제품(정식) 기능으로 승격되었다. 수백만 객체를 다루는 애플리케이션에서 메모리·캐시 효율이 향상된다.

> **객체 헤더** — 객체 하나하나에 딸려 있는, 값이 아닌 관리용 앞머리. 개수가 많을수록 그 앞머리의 크기가 통째로 곱해진다.\
> 예: 원문이 적은 수치가 "(보통) 12바이트에서 8바이트로"이고, 효과가 크게 나는 자리로 든 것이 "수백만 객체를 다루는 애플리케이션"이다.

```bash
java -XX:+UseCompactObjectHeaders -jar app.jar
```

### Generational Shenandoah (JEP 521, 정식)
- Shenandoah GC의 세대별 모드가 정식화되었다(24 실험적 → 25 정식). 짧게 사는 객체가 많은 워크로드에서 처리량과 지연을 개선한다.

## 그 외 변경
- **Ahead-of-Time Method Profiling (JEP 515)** / **Ahead-of-Time Command-Line Ergonomics (JEP 514)**: Project Leyden 후속. 메서드 프로파일을 미리 수집해 워밍업을 단축하고, AOT 캐시 사용을 위한 명령행 옵션을 단순화한다.
- **JFR 강화**: CPU-Time Profiling(JEP 509, 실험적, 리눅스), Cooperative Sampling(JEP 518), Method Timing & Tracing(JEP 520)으로 Flight Recorder의 프로파일링·진단 능력을 확장한다.
- **Stable Values (JEP 502, 프리뷰)**: `final`의 불변성과 지연 초기화의 유연성을 결합한 "안정값" API의 첫 프리뷰. 한 번만 설정되며 JIT가 상수처럼 최적화할 수 있다.
- **PEM Encodings of Cryptographic Objects (JEP 470, 프리뷰)**: 키·인증서 등 암호 객체를 PEM 텍스트로 인코딩/디코딩하는 표준 API의 첫 프리뷰.
- **Structured Concurrency (JEP 505, 5차 프리뷰)**: 아직 정식화되지 않고 API를 다듬는 5차 프리뷰로 유지된다.

> **워밍업(warm-up)** — 갓 띄운 JVM이 아직 최적화되지 않아 느린 구간. 원문은 AOT 메서드 프로파일링의 효과를 "메서드 프로파일을 미리 수집해 워밍업을 단축"이라 적는다.\
> 예: 이 갈래의 앞 단계가 같은 시리즈 `java-24.md`의 JEP 483(AOT 클래스 로딩·링킹)이고, 그 편이 거기에 붙인 이름이 "Project Leyden의 첫 정식 산출물"이다.

> **지연 초기화(lazy initialization)** — 만들어 두지 않고 있다가 처음 필요해질 때 만드는 것. 원문은 Stable Values를 "`final`의 불변성과 지연 초기화의 유연성을 결합한" 것으로 적는다.\
> 예: 원문이 그 성질로 든 것이 "한 번만 설정되며 JIT가 상수처럼 최적화할 수 있다"이다.

아래 흐름도는 구조적 동시성의 작업 트리를 보여준다. `StructuredTaskScope`(부모)가 여러 subtask를 `fork`하고 `join`으로 모두 기다린 뒤 결과를 취합한다. 부모 스코프가 닫히면 자식 작업도 함께 정리되어, 부모-자식 생명주기가 하나로 묶인다. (Java 25 시점에 구조적 동시성은 프리뷰, Scoped Values는 정식이다.)

```text
              StructuredTaskScope (부모)
                │ fork        │ fork        │ fork
                v             v             v
        subtask:          subtask:       subtask:
        findUser()        fetchOrder()   fetchPrefs()
                │ 완료        │ 완료        │ 완료
                └──────┬──────┴─────────────┘
                       v
             join() — 모든 자식 대기
                       │
                       v
        결과 취합 / 실패 시 전체 취소
                       │
                       v
        scope.close() — 자식 생명주기 종료
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 화살표 여덟(fork 셋 · 완료 셋 · 그 뒤 둘)으로 원문의 화살표 수와 같고, 방향도 위에서 아래로 원문과 같다.
- 칸 이름과 화살표에 붙은 `fork`·`완료`는 전부 원문의 라벨 그대로다. 바로 위 문단이 이 그림을 읽는 법이고, 그 문단도 원문의 것이다.
- 세 subtask의 `완료` 화살표가 **같은 칸 하나**(`join() — 모든 자식 대기`)로 모인다 — 원문도 셋을 그 한 칸에 잇는다.

- **Primitive Types in Patterns, instanceof, and switch (JEP 507, 3차 프리뷰)**: 원시 타입 패턴 매칭은 LTS에서도 여전히 프리뷰(3차)다.
- **Vector API (JEP 508, 10차 인큐베이터)**: Valhalla 의존성으로 인해 LTS에서도 여전히 인큐베이터(10차)에 머문다.
- **Remove the 32-bit x86 Port (JEP 503, 정식)**: 32비트 x86 포트와 관련 빌드를 완전히 제거.

32비트 x86의 마지막 장면이다 — 같은 시리즈 `java-21.md`의 JEP 449가 윈도우 쪽 폐기를 예고했고, `java-24.md`의 JEP 479가 윈도우 포트를 제거하면서 JEP 501로 나머지를 폐기 예고했으며, 여기서 전부 사라진다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 문장은 원문의 것이다.)*

Java 25는 Java 21 이후 2년간 축적된 차세대 기능들을 정식화해 모은 LTS로, 기업의 차기 표준 채택 기준점이 된다.\
스코프드 값·유연한 생성자 본문·모듈 임포트의 정식화는 Loom·Amber 시대의 언어/라이브러리 모델을 굳혔고, 컴팩트 객체 헤더와 세대별 Shenandoah, AOT 프로파일링은 메모리·시작 성능을 LTS 수준으로 안정화했다.\
다만 구조적 동시성·원시 타입 패턴·Vector API·String Templates(보류) 등은 여전히 미완으로 남아, 다음 LTS(예정상 Java 29)로 숙제를 넘긴다.

## 용어 풀이

- **LTS(장기 지원)** — 오래 보안 패치를 받는 버전. 이 편에 붙은 기간이 "Oracle 기준 최소 8년 지원"이고, 직전 LTS는 Java 21(2023.09)이다.
- **동적 범위(dynamic scope)** — 실행이 그 안에 머무는 동안이라는 범위. 원문 표현으로 "명시된 동적 범위(`run`/`call`)"이고, 그 안에서만 값이 유효하다.
- **Project Valhalla** — 원문이 컴팩트 객체 헤더를 "가는 길목"으로 부르는 갈래의 이름. Vector API가 인큐베이터에 머무는 사유로도 "Valhalla 의존성"이 적힌다.
- **키 유도 함수(KDF)** — 이미 가진 비밀에서 실제로 쓸 키를 뽑아내는 함수. 원문 표현으로 "키 파생"이고, 원문이 든 이름이 HKDF다.
- **객체 헤더** — 객체 하나하나에 딸려 있는, 값이 아닌 관리용 앞머리. 원문이 적은 수치가 "(보통) 12바이트에서 8바이트로"다.
- **워밍업(warm-up)** — 갓 띄운 JVM이 아직 최적화되지 않아 느린 구간. 원문은 AOT 메서드 프로파일링이 이것을 "단축"한다고 적는다.
- **지연 초기화(lazy initialization)** — 만들어 두지 않고 있다가 처음 필요해질 때 만드는 것. 이 편의 Stable Values는 그것을 `final`의 불변성과 결합한 첫 프리뷰다.

## 참고 출처
- [JDK 25 - OpenJDK 프로젝트 페이지](https://openjdk.org/projects/jdk/25/)
- [Oracle Releases Java 25](https://www.oracle.com/news/announcement/oracle-releases-java-25-2025-09-16/)
- [The Arrival of Java 25 - Oracle Java Blog](https://blogs.oracle.com/java/the-arrival-of-java-25)
- [New Features in Java 25 - Baeldung](https://www.baeldung.com/java-25-features)
- [JDK 25 and JDK 26: What We Know So Far - InfoQ](https://www.infoq.com/news/2025/08/java-25-so-far/)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
