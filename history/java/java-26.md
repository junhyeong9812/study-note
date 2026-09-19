# Java 26 (2026.03) — non-LTS

> 원본: `~/project/java-history/java/java-26.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/메서드 이름·자바 코드블록 4개·「릴리스 정보」의 JEP 목록·「참고 출처」는 원문 그대로다.\
> ASCII 도식 1개는 원문 mermaid 도식 1개를 글자로 옮긴 것이고, 새로 그린 도식은 없다.\
> 「한눈에」의 지름길 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「이 편의 기능은 지금 어디쯤인가」 표의 「그 앞」 칸은 같은 시리즈의 다른 편(`java-21.md`~`java-25.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.\
> 「head-of-line blocking」 풀이 한 줄은 이 저장소의 다른 주제(`history/network/02-프로토콜-스택.md`)에 이미 있는 것을 그대로 가져왔다 — 이 편 원문은 이름만 들고 풀지 않는다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 25 LTS 직후의 첫 정규(비-LTS) 릴리스. HTTP/3 클라이언트와 모든 GC에 적용되는 AOT 객체 캐싱을 정식화하고, "final은 진짜 final"로 가는 무결성 준비 단계를 시작했다. 구조적 동시성·원시 타입 패턴·지연 상수는 다음 LTS를 향해 프리뷰를 한 단계씩 더 진전시켰다.

이 편에서 정식이 된 것 하나를 비유로 읽으면 **새로 난 지름길이 열려 있으면 그리로 가고, 막혀 있으면 원래 큰길로 되돌아가는 내비게이션**이다.\
**HTTP/3 지원도 똑같은 구조다** — 원문 자신이 도식 앞에 이렇게 적는다: "요청에만 HTTP/3을 지정하면 QUIC 연결을 시도하고, 실패하면 기존 TCP 기반 HTTP/2(또는 1.1)로 자연스럽게 내려간다."

본문 흐름에 쓰는 비유는 이 지름길 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 새로 난 지름길 | 원문 도식 라벨로 "HTTP/3 over QUIC" — 원문 표현으로 "TCP가 아니라 **QUIC(UDP 기반)** 위에서 동작" |
| 그 길이 열려 있는지 확인 | 원문 도식 라벨로 "QUIC(UDP) 연결 가능?" |
| 원래 큰길로 되돌아감 | 원문 도식 라벨로 "폴백: HTTP/2 over TCP" |
| 내비게이션이 기본으로 잡아 두는 길 | 원문 표현으로 "기본 협상 버전은 여전히 HTTP/2이며, HTTP/3은 명시적으로 선택한다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **HTTP/3이 기본으로 켜지는 것이 아니다.** 원문이 그 절에 직접 적어 둔 그대로다 — "기본 협상 버전은 여전히 HTTP/2이며, HTTP/3은 명시적으로 선택한다."
- **`final`이 지금까지 손댈 수 없는 것이었다는 뜻이 아니다.** 바로 그 반대라서 이 JEP가 나왔다. 원문이 적은 조건이 "deep reflection으로 `final` 필드를 변경(mutate)하려 하면"이고, 이 편에서 그 자리에 붙는 것은 금지가 아니라 **런타임 경고**다.
- **이 편에서 정식이 된 것과 프리뷰로 한 차수 올라간 것은 다르다.** 원문 JEP 목록이 그 수를 먼저 밝힌다 — "총 10개 — 정식 5 / 프리뷰·인큐베이터 5".

### 이 편의 기능은 지금 어디쯤인가

가운데 칸은 이 편 원문이 적은 것이고, 왼쪽 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 그 앞 | 이 편(26)에서의 상태 |
|---|---|---|
| HTTP/3 for the HTTP Client API (JEP 517) | — (이 편이 처음) | **정식** |
| Ahead-of-Time Object Caching with Any GC (JEP 516) | `java-24.md` JEP 483(AOT 클래스 로딩·링킹) · `java-25.md` JEP 514·515 | **정식** |
| Prepare to Make Final Mean Final (JEP 500) | — (이 편이 처음) | **정식**(다만 원문 표현으로 "준비 단계") |
| Remove the Applet API (JEP 504) | `java-17.md` JEP 398(제거 예정으로 표시) | **정식**(완전 제거) |
| G1 GC 처리량 개선 (JEP 522) | — | **정식** |
| Lazy Constants (JEP 526) | `java-25.md`에 "Stable Values"라는 이름으로 1차 프리뷰(JEP 502) | 2차 프리뷰 — **아직 정식이 아니다** |
| PEM Encodings of Cryptographic Objects (JEP 524) | `java-25.md` 1차 프리뷰(JEP 470) | 2차 프리뷰 — **아직 정식이 아니다** |
| Structured Concurrency (JEP 525) | `java-19.md` 인큐베이터(JEP 428) → `java-21.md` 1차 프리뷰(JEP 453) → 22·23·24·25에서 2·3·4·5차 | 6차 프리뷰 — **이 시리즈가 끝날 때까지 정식이 아니다** |
| Primitive Types in Patterns, instanceof, and switch (JEP 530) | `java-23.md` 1차 프리뷰(JEP 455) → `java-24.md` 2차 → `java-25.md` 3차 | 4차 프리뷰 — **이 시리즈가 끝날 때까지 정식이 아니다** |
| Vector API (JEP 529) | `java-16.md`의 1차 인큐베이터부터 이어진 줄기 | 11차 인큐베이터 — **이 시리즈가 끝날 때까지 정식이 아니다** |

## 릴리스 정보
- 정식 출시일: 2026년 3월 17일
- LTS 여부: **아니오** (non-LTS, 6개월 지원). 직전 LTS는 Java 25(2025.09), 다음 LTS는 예정상 Java 29
- 클래스 파일 포맷 버전: 70
- 포함 JEP 목록 (총 10개 — 정식 5 / 프리뷰·인큐베이터 5):
  - JEP 500: Prepare to Make Final Mean Final (정식)
  - JEP 504: Remove the Applet API (정식)
  - JEP 516: Ahead-of-Time Object Caching with Any GC (정식)
  - JEP 517: HTTP/3 for the HTTP Client API (정식)
  - JEP 522: G1 GC 처리량 개선 — 동기화 비용 축소 (정식)
  - JEP 524: PEM Encodings of Cryptographic Objects (2차 프리뷰)
  - JEP 525: Structured Concurrency (6차 프리뷰)
  - JEP 526: Lazy Constants (2차 프리뷰)
  - JEP 529: Vector API (11차 인큐베이터)
  - JEP 530: Primitive Types in Patterns, instanceof, and switch (4차 프리뷰)

> **비-LTS(non-LTS)** — 다음 릴리스가 나오면 지원이 끝나는 버전. 원문이 이 편에 붙인 기간이 "6개월 지원"이다.\
> 예: 원문은 이 편의 앞뒤를 함께 적어 둔다 — "직전 LTS는 Java 25(2025.09), 다음 LTS는 예정상 Java 29"다.

## 시대적 배경

Java 26은 Java 25 LTS가 차세대 기능들을 정식화해 모은 직후, 6개월 케이던스의 정규 비-LTS 릴리스로 도착했다.\
LTS가 "결실을 안정화해 모으는" 릴리스라면, 그 다음 비-LTS는 "다음 LTS(Java 29)를 향해 프리뷰를 한 단계씩 더 다듬고, 준비된 기능은 바로 정식화하는" 성격이 강하다.\
실제로 26에서는 신규 기능인 HTTP/3과 G1 개선이 곧장 정식으로 들어왔고, **Project Leyden**의 AOT 객체 캐싱이 모든 GC로 확장되어 정식화된 반면, **Project Loom**(구조적 동시성)·**Project Amber**(원시 타입 패턴)·지연 상수·PEM·Vector API는 프리뷰/인큐베이터 단계를 한 차수씩 더 올렸다.\
또한 오래 사장돼 있던 **Applet API가 완전히 제거**되고, 향후 "final은 진짜 final"을 강제하기 위한 **무결성(integrity by default)** 준비가 시작됐다.

> **6개월 케이던스** — 매년 3월과 9월에 한 번씩 릴리스를 내보내는 주기. 같은 시리즈 `README.md`가 적는 표현이 "매년 3월/9월 릴리스"다.\
> 예: 이 편의 출시일이 2026년 3월 17일이고, 직전 LTS인 Java 25의 출시일이 2025년 9월 16일이다.

## 주요 추가 기능

### HTTP/3 for the HTTP Client API (JEP 517, 정식)
- `java.net.http.HttpClient`가 HTTP/3을 지원한다. HTTP/3은 TCP가 아니라 **QUIC(UDP 기반)** 위에서 동작해 연결 수립 지연과 head-of-line blocking을 줄인다. 기본 협상 버전은 여전히 HTTP/2이며, HTTP/3은 명시적으로 선택한다.

> **QUIC** — HTTP/3이 올라타는 아래층. 원문 표현으로 "TCP가 아니라 **QUIC(UDP 기반)** 위에서 동작"한다.\
> 예: 원문이 이 교체로 줄어든다고 든 둘이 "연결 수립 지연"과 "head-of-line blocking"이다.

> **head-of-line blocking** — 줄의 맨 앞이 막히면 뒤가 전부 대기하는 현상. 이 편 원문은 이름만 들 뿐 풀지 않아, 이 한 줄은 이 저장소의 다른 주제 `history/network/02-프로토콜-스택.md`에서 그대로 가져왔다.\
> 예: 원문이 이 이름을 한 번 더 쓰는 자리가 도식 라벨의 "HOL blocking 완화"다.

```java
// 클라이언트 레벨에서 HTTP/3 선택
HttpClient client = HttpClient.newBuilder()
        .version(HttpClient.Version.HTTP_3)
        .build();

// 요청 레벨에서만 지정 — 실패 시 HTTP/2·1.1로 폴백 가능
HttpRequest request = HttpRequest.newBuilder()
        .version(HttpClient.Version.HTTP_3)
        .uri(URI.create("https://example.com"))
        .GET()
        .build();
```

원문이 위 코드를 두 토막으로 나누고 각 토막에 이름을 붙여 두었다 — "클라이언트 레벨에서 HTTP/3 선택"과 "요청 레벨에서만 지정 — 실패 시 HTTP/2·1.1로 폴백 가능"이다. 아래 도식이 그리는 것은 둘째 토막 쪽이다.

아래 흐름도는 HTTP/3 요청의 협상·폴백 경로를 보여준다. 요청에만 HTTP/3을 지정하면 QUIC 연결을 시도하고, 실패하면 기존 TCP 기반 HTTP/2(또는 1.1)로 자연스럽게 내려간다.

```text
HttpRequest (version=HTTP_3)
   │
   v
{ QUIC(UDP) 연결 가능? }
   ├─ 예 ──────>  HTTP/3 over QUIC
   │              (낮은 지연 · HOL blocking 완화)
   └─ 아니오 ──>  폴백: HTTP/2 over TCP
                      │
                      v
                  { HTTP/2 협상 가능? }
                      ├─ 아니오 ──>  HTTP/1.1
                      └─ 예 ──────>  HTTP/2
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 화살표 여섯으로 원문의 화살표 수와 같고, 방향도 위에서 아래로 원문과 같다.
- 중괄호로 감싼 두 칸은 원문이 마름모(판정)로 그린 칸이고, 칸 이름과 갈림길 라벨(`예`·`아니오`)은 전부 원문의 것이다. `(낮은 지연 · HOL blocking 완화)`는 원문이 같은 칸 안에서 줄을 바꿔 적은 글자다.
- 둘째 판정의 두 갈래를 `아니오` → `예` 순으로 적은 것도 원문의 차례 그대로다.

### Ahead-of-Time Object Caching with Any GC (JEP 516, 정식)
- Project Leyden의 AOT 캐시가 특정 GC(이전엔 비-세대형 전제)에 묶이지 않고 **모든 GC(ZGC 포함)에서 동작**하도록 객체 캐싱을 일반화했다. 캐시된 힙 객체를 GC 중립적인 포맷으로 순차 로딩해, 시작·워밍업 시간을 단축한다. Java 25의 AOT 작업(JEP 514·515)을 GC 선택과 무관하게 쓸 수 있게 넓힌 후속이다.

**이 줄기의 앞** — 위 불릿이 후속으로 잇는 Java 25의 JEP 514·515보다 앞에, 같은 시리즈 `java-24.md`의 JEP 483(AOT 클래스 로딩·링킹)이 이 줄기의 첫머리로 있다.

> **GC 중립적인 포맷** — 어느 가비지 컬렉터를 쓰든 그대로 읽히는 형태. 원문 표현 그대로이고, 그래서 "모든 GC(ZGC 포함)에서 동작"이 가능해진다.\
> 예: 원문이 이전 상태로 괄호에 적어 둔 것이 "이전엔 비-세대형 전제"다.

### Prepare to Make Final Mean Final (JEP 500, 정식)
- deep reflection으로 `final` 필드를 변경(mutate)하려 하면 **런타임 경고**를 발생시킨다. 향후 릴리스에서는 기본적으로 예외를 던질 예정으로, "integrity by default"(무결성 기본화)를 향한 준비 단계다. 직렬화 프레임워크·테스트 도구 등이 final 필드를 우회 수정하던 관행을 점진적으로 막는다.

> **deep reflection** — 평소라면 닿을 수 없는 자리까지 실행 중에 파고들어 읽고 쓰는 것. 원문이 이 편의 대상으로 든 동작이 그것으로 "`final` 필드를 변경(mutate)"하는 일이다.\
> 예: 원문이 그렇게 해 오던 쪽으로 든 것이 "직렬화 프레임워크·테스트 도구 등"이다.

이 편에서 붙는 것은 경고까지다. 원문이 다음 단계로 적은 것은 "향후 릴리스에서는 기본적으로 예외를 던질 예정"이므로, **이 편의 `final`은 아직 막히지 않았다.**

### Lazy Constants (JEP 526, 2차 프리뷰)
- Java 25의 **Stable Values(JEP 502, 1차 프리뷰)**가 `Lazy Constants`로 개명·진전했다. `final`의 불변성과 지연 초기화의 유연성을 결합한 "단 한 번만 설정되는" 컨테이너로, 내부적으로 JVM의 `@Stable` 의미론에 저장돼 JIT가 상수처럼 최적화한다.

```java
// 지연 초기화 싱글턴 (Holder 패턴 대체)
static final LazyConstant<ExpensiveObject> INSTANCE = LazyConstant.of(ExpensiveObject::new);

ExpensiveObject get() {
    return INSTANCE.get();   // 최초 접근 시 1회 초기화, 이후 상수처럼 취급
}
```
프리뷰 기능이므로 `--enable-preview`가 필요하다.

> **지연 초기화(lazy initialization)** — 만들어 두지 않고 있다가 처음 필요해질 때 만드는 것. 원문이 코드 주석에 적은 그대로 "최초 접근 시 1회 초기화, 이후 상수처럼 취급"이다.\
> 예: 위 코드에서 `LazyConstant.of(ExpensiveObject::new)`는 만드는 법만 건네 둔 것이고, 실제로 만들어지는 시점은 `INSTANCE.get()`이 처음 불릴 때다.

### Primitive Types in Patterns, instanceof, and switch (JEP 530, 4차 프리뷰)
- 원시 타입을 패턴 매칭·`instanceof`·`switch`에서 쓸 수 있다. 핵심 개념은 **exactness(정확 변환)** — 손실 없는 변환일 때만 바인딩되어 컴파일 타임 안전성을 준다. Java 25에서 3차 프리뷰(JEP 507)였던 것이 26에서 4차 프리뷰로 진전했다.

> **exactness(정확 변환)** — 원문이 이 기능의 "핵심 개념"으로 든 것. 원문 표현으로 "손실 없는 변환일 때만 바인딩"된다.\
> 예: 원문이 아래 코드 주석에 적은 조건이 "손실 없이 byte 범위에 들어갈 때만 바인딩"이다.

```java
// 손실 없이 byte 범위에 들어갈 때만 바인딩
if (x instanceof byte b) {
    handleByte(b);
}

switch (number) {
    case int i    -> handleInt(i);
    case double d -> handleDouble(d);
    default       -> { }
}
```
프리뷰 기능이므로 `--enable-preview`가 필요하다.

이 기능이 프리뷰를 시작한 편은 `java-23.md`(JEP 455)다. 23·24·25·26 네 편을 프리뷰로 지나왔고, **이 시리즈가 끝나는 이 편까지도 정식이 아니다.**

### Structured Concurrency (JEP 525, 6차 프리뷰)
- 구조적 동시성 API가 6차 프리뷰로 계속 다듬어졌다. 이번 차수에서는 `Joiner`에 타임아웃을 거는 방식과 결과 취합 메서드명이 정돈됐다(예: `anySuccessfulResultOrThrow()` → `anySuccessfulOrThrow()`, `allSuccessfulOrThrow()`는 결과 리스트 반환).

```java
Response handle() throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {
        var user  = scope.fork(() -> findUser());
        var order = scope.fork(() -> fetchOrder());
        scope.join();                 // 자식 모두 대기 (실패 시 함께 취소)
        return new Response(user.get(), order.get());
    }
}
```
프리뷰 기능이므로 `--enable-preview`가 필요하다. (Java 21에서 정식화된 가상 스레드와 달리, 구조적 동시성은 여전히 미정식 상태로 남아 있다.)

원문이 괄호로 달아 둔 그 대비가 이 시리즈 전체의 요약에 가깝다 — 같은 Project Loom에서 출발했어도 가상 스레드는 `java-21.md`에서 정식이 됐고, 구조적 동시성은 `java-19.md`의 인큐베이터부터 여기까지 여덟 편을 지나오며 아직 프리뷰다.

## 그 외 변경
- **Remove the Applet API (JEP 504, 정식)**: 브라우저 플러그인 시대의 유물인 `java.applet` API를 완전히 제거했다. 한 시대를 마감하는 정리 작업이다.
- **G1 GC 처리량 개선 (JEP 522, 정식)**: G1 가비지 컬렉터의 내부 동기화 비용을 줄여 처리량을 높였다. 애플리케이션 코드 변경 없이 기본 GC의 성능이 개선된다.
- **PEM Encodings of Cryptographic Objects (JEP 524, 2차 프리뷰)**: 키·인증서 등 암호 객체를 PEM 텍스트로 인코딩/디코딩하는 API가 25의 1차 프리뷰(JEP 470)에 이어 2차 프리뷰로 진전했다.
- **Vector API (JEP 529, 11차 인큐베이터)**: SIMD 벡터 연산 API는 Valhalla 의존성으로 인해 여전히 인큐베이터(11차)에 머문다.

Applet의 마지막 장면이다 — 같은 시리즈 `jdk-1.0.md`가 「애플릿(Applet)」 절을 따로 두고 다루었고, `java-17.md`의 JEP 398이 `java.applet.Applet`을 "제거 예정으로 표시"했으며, 여기서 사라진다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 줄은 원문의 것이다.)*

Java 26은 LTS 사이를 잇는 전형적인 비-LTS 릴리스다. 당장 프로덕션 표준으로 채택되기보다, Java 25 LTS 위에서 차기 LTS(Java 29)로 가는 기능들을 검증·정식화하는 자리에 가깝다.\
그럼에도 **HTTP/3 클라이언트**와 **모든 GC에 적용되는 AOT 객체 캐싱**처럼 바로 쓸 수 있는 정식 기능이 들어왔고, **"final은 진짜 final"** 무결성 준비와 **Applet API 제거**는 플랫폼의 장기 방향(안전한 기본값·레거시 정리)을 분명히 보여준다.\
구조적 동시성·원시 타입 패턴·지연 상수는 아직 프리뷰로 남아, Loom·Amber·Valhalla의 완성은 다음 LTS의 숙제로 이어진다.

## 용어 풀이

- **비-LTS(non-LTS)** — 다음 릴리스가 나오면 지원이 끝나는 버전. 이 편에 붙은 기간이 "6개월 지원"이고, 직전 LTS는 Java 25(2025.09)다.
- **6개월 케이던스** — 매년 3월과 9월에 한 번씩 릴리스를 내보내는 주기. 같은 시리즈 `README.md`의 표현이 "매년 3월/9월 릴리스"다.
- **QUIC** — HTTP/3이 올라타는 아래층. 원문 표현으로 "TCP가 아니라 **QUIC(UDP 기반)** 위에서 동작"한다.
- **head-of-line blocking** — 줄의 맨 앞이 막히면 뒤가 전부 대기하는 현상. 이 편 원문은 이름만 들고, 이 풀이는 `history/network/02-프로토콜-스택.md`에서 가져왔다.
- **GC 중립적인 포맷** — 어느 가비지 컬렉터를 쓰든 그대로 읽히는 형태. 원문 표현 그대로이고, 그래서 "모든 GC(ZGC 포함)에서 동작"이 된다.
- **deep reflection** — 평소라면 닿을 수 없는 자리까지 실행 중에 파고들어 읽고 쓰는 것. 이 편의 대상은 그것으로 "`final` 필드를 변경(mutate)"하는 일이고, 이 편에서 붙는 것은 런타임 경고까지다.
- **지연 초기화(lazy initialization)** — 만들어 두지 않고 있다가 처음 필요해질 때 만드는 것. 원문 주석 표현으로 "최초 접근 시 1회 초기화, 이후 상수처럼 취급"이다.
- **exactness(정확 변환)** — 원문이 원시 타입 패턴의 "핵심 개념"으로 든 것. 원문 표현으로 "손실 없는 변환일 때만 바인딩"된다.

## 참고 출처
- [JDK 26 - OpenJDK 프로젝트 페이지](https://openjdk.org/projects/jdk/26/)
- [JDK 26 - jdk.java.net](https://jdk.java.net/26/)
- [The Arrival of Java 26 - Oracle Java Blog](https://blogs.oracle.com/java/the-arrival-of-java-26)
- [Java 26 Delivers... - InfoQ](https://www.infoq.com/news/2026/03/java26-released/)
- [JEP 517: HTTP/3 for the HTTP Client API](https://openjdk.org/jeps/517)
- [JEP 526: Lazy Constants](https://openjdk.org/jeps/526)
- [JEP 525: Structured Concurrency (Sixth Preview)](https://openjdk.org/jeps/525)
- [JEP 530: Primitive Types in Patterns, instanceof, and switch (Fourth Preview)](https://openjdk.org/jeps/530)
- [JEP 500: Prepare to Make Final Mean Final](https://openjdk.org/jeps/500)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
