# Java 11 (2018년 9월) — LTS

> 원본: `~/project/java-history/java/java-11.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/패키지/메서드 이름·코드블록 4개(java 3 · bash 1)·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개는 원문의 mermaid 시퀀스 그림을 글자로 옮긴 것이고, 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 교차 주 1개는 원문에 없는 보충이다.\
> 원문에 없는 도식은 새로 그리지 않았다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 새 릴리스 모델에서 나온 첫 번째 LTS. 표준 HTTP 클라이언트, 단일 파일 실행, Oracle JDK 라이선스 변화로 자바 생태계의 분기점이 된 버전.

이 편을 하나의 비유로 읽으면 **6개월마다 뜨는 열차 가운데, "이 열차는 몇 년 동안 정비를 계속 받는다"고 표시해 둔 열차를 정한 일**이다.\
매번 갈아타야 한다면 회사가 따라가기 어려우니, 몇 대에 한 번은 오래 타도 되는 열차를 지정한 것이다.\
**Java 11의 LTS도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "모든 릴리스가 다음 릴리스까지만(6개월) 지원되면 기업이 따라가기 어렵기 때문에".

본문 흐름에 쓰는 비유는 이 열차 하나뿐이다("편"은 이 문서 한 편을 가리키는 말로만 쓴다) — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 6개월마다 뜨는 보통 열차 | 원문 표현으로 "다음 릴리스까지만(6개월) 지원되면" |
| 오래 타도 되는 지정 열차 | LTS — 원문 표현으로 "수년간 보안 패치를 제공하기로" |
| 그 지정을 붙이는 간격 | 원문 표현으로 "3년마다 한 번씩(이후 2년으로 단축)" |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **"첫 LTS"에 원문이 붙인 한정은 "6개월 케이던스 도입 이후"다.**\
  원문이 「릴리스 정보」에 적은 그대로다 — "**예 (Long-Term Support)** — 6개월 케이던스 도입 이후 첫 LTS".\
  오래 쓰인 것과 LTS로 지정된 것은 이 시리즈에서 따로 적힌다 — `java-8.md`는 Java 8을 「현대적 LTS 모델(Java 11부터 시작) 이전 버전이지만 … 사실상 가장 오래 살아남은 "장기 지원" 버전으로 취급됨」이라 적고, `java-7.md`는 그 시대를 "해당 시대엔 LTS 개념 없음"이라 적는다.
- **Java 11에서 유료가 된 것은 "자바"가 아니라 Oracle의 자사 빌드다.**\
  원문이 「시대적 배경」에서 적는 그대로다 — "이 버전부터 Oracle은 자사 빌드(Oracle JDK)를 상용 OTN … 라이선스로 배포해 운영/상업적 사용에 유료 구독을 요구했고, 무료로 쓰려면 OpenJDK 기반 빌드(Adoptium/Temurin, Amazon Corretto, Azul Zulu, Red Hat 등)를 선택하는 흐름이 자리 잡았다".
- **`var`를 람다 파라미터에 쓰는 것은 타입을 적는 것과 다르지 않다.**\
  원문이 적는 그대로다 — "단독으로는 타입을 명시하는 것과 차이가 없지만, 모든 파라미터에 어노테이션(`@NonNull` 등)이나 수식어를 일관되게 붙일 수 있다는 장점이 있다".

## 릴리스 정보
- 정식 출시일: 2018년 9월 25일
- 개발 주체: Oracle (OpenJDK)
- LTS 여부: **예 (Long-Term Support)** — 6개월 케이던스 도입 이후 첫 LTS
- 포함 JEP 수: 17개

> **LTS(Long-Term Support)** — 그 버전을 수년간 보안 패치를 계속 받도록 지정해 두는 것.\
> 예: 원문이 그 목적으로 든 것이 "모든 릴리스가 다음 릴리스까지만(6개월) 지원되면 기업이 따라가기 어렵기 때문"이고, 지정 간격이 "3년마다 한 번씩(이후 2년으로 단축)"이다.

## 시대적 배경

*(「한눈에」의 열차 비유가 가리키는 자리다.)*

Java 10이 6개월 릴리스 케이던스를 증명했다면, Java 11은 그 모델 위에서 **장기 지원(LTS)** 개념을 정립했다. 모든 릴리스가 다음 릴리스까지만(6개월) 지원되면 기업이 따라가기 어렵기 때문에, Oracle은 3년마다 한 번씩(이후 2년으로 단축) LTS 릴리스를 지정해 수년간 보안 패치를 제공하기로 했다. Java 11이 그 첫 LTS로, Java 8을 잇는 사실상의 "기업 표준" 버전이 되었다.

또한 Java 11은 **라이선스 측면의 전환점**이기도 하다. 이 버전부터 Oracle은 자사 빌드(Oracle JDK)를 상용 OTN(Oracle Technology Network) 라이선스로 배포해 운영/상업적 사용에 유료 구독을 요구했고, 무료로 쓰려면 OpenJDK 기반 빌드(Adoptium/Temurin, Amazon Corretto, Azul Zulu, Red Hat 등)를 선택하는 흐름이 자리 잡았다.

> **배포판(build/distribution)** — 같은 OpenJDK 소스에서 여러 회사가 각자 만들어 내놓는 JDK 꾸러미.\
> 예: 원문이 무료로 쓸 수 있는 쪽으로 든 것이 Adoptium/Temurin, Amazon Corretto, Azul Zulu, Red Hat이고, 유료 구독이 필요해진 쪽이 Oracle 자사 빌드다.

## 주요 추가 기능

### 표준 HTTP 클라이언트 (JEP 321)
- 상태: **정식 기능(standard)** — Java 9/10에서 incubator였던 `jdk.incubator.http`가 표준 `java.net.http` 패키지로 승격.
- HTTP/1.1과 HTTP/2, WebSocket을 지원하며 동기/비동기(CompletableFuture) 호출이 모두 가능하다. 오래된 `HttpURLConnection`을 대체한다.

**언제 정식이 됐나** — 원문이 첫 불릿에 적은 그대로다. Java 9/10에서는 incubator였고, 이 버전에서 표준 `java.net.http` 패키지로 승격했다.

> **incubator(인큐베이터)** — 정식 API가 되기 전에 시험 삼아 따로 내놓아 둔 상태. 이름부터 정식과 다르다.\
> 예: 원문이 적은 승격 전 이름이 `jdk.incubator.http`이고, 승격 후 이름이 `java.net.http`다.

> **동기(synchronous) / 비동기(asynchronous) 호출** — 결과가 올 때까지 그 자리에서 기다리는 호출 / 기다리지 않고 돌아와 나중에 결과를 받는 호출.\
> 예: 아래 코드에서 원문이 "동기 호출"이라 적은 것이 `client.send(...)`이고, "비동기 호출"이라 적은 것이 `client.sendAsync(...)`다.

```java
import java.net.http.*;
import java.net.URI;

HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/data"))
        .GET()
        .build();

// 동기 호출
HttpResponse<String> response =
        client.send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.statusCode());
System.out.println(response.body());

// 비동기 호출
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
      .thenApply(HttpResponse::body)
      .thenAccept(System.out::println);
```

> **재서술자 주:** 같은 시리즈 `java-9.md`의 인큐베이터 시절 코드는 같은 자리에 `HttpResponse.BodyHandler.asString()`을 쓰는데, 이 편은 `HttpResponse.BodyHandlers.ofString()`이다. 정식화하며 이름이 바뀐 것으로 보이나, 두 편 모두 이름 변경을 직접 적지는 않는다.

아래 시퀀스 다이어그램은 동기 `send()`와 비동기 `sendAsync()`의 차이를 보여준다. 동기 호출은 응답이 올 때까지 호출 스레드가 블로킹되지만, 비동기 호출은 즉시 `CompletableFuture`를 반환하고 논블로킹 I/O 완료 후 콜백(`thenApply`)이 실행된다. 이때 `thenApply` 콜백은 원래 호출 스레드가 아니라 완료를 수행한 스레드에서 실행될 수 있다(호출 스레드 실행을 보장하려면 `thenApplyAsync(fn, executor)`를 쓴다).

```text
[동기 send() — 응답까지 블로킹]
호출 스레드            -->  HttpClient             send(request)
HttpClient             -->  서버                   HTTP 요청
서버                   -->  HttpClient             HTTP 응답
HttpClient             -->  호출 스레드            HttpResponse 반환 (이때까지 대기)

[비동기 sendAsync() — 논블로킹]
호출 스레드            -->  HttpClient             sendAsync(request)
HttpClient             -->  호출 스레드            CompletableFuture 즉시 반환
HttpClient             -->  논블로킹 I/O (셀렉터)  요청 등록 (스레드 점유 안 함)
논블로킹 I/O (셀렉터)  -->  서버                   HTTP 요청
서버                   -->  논블로킹 I/O (셀렉터)  HTTP 응답 도착
논블로킹 I/O (셀렉터)  -->  HttpClient             완료 통지
HttpClient             -->  HttpClient             CompletableFuture 완료
HttpClient             -->  완료 스레드(콜백)      thenApply 콜백 실행 (원래 호출 스레드 아님)
```

- 이 그림은 원문의 mermaid 시퀀스 그림을 글자로 옮긴 것이다 — 화살표 열둘로 원문의 메시지 수와 같고, 순서와 방향도 원문과 같다.
- 왼쪽·가운데의 이름은 원문이 participant로 선언한 이름 그대로이고, 오른쪽에 적은 말은 원문이 그 화살표에 붙인 메시지 글자 그대로다.
- 대괄호 두 줄은 원문이 `Note over`로 적어 둔 글자 그대로다. 원문은 실선과 점선 두 종류를 쓰지만, 여기서는 화살표 모양을 하나로 통일했다(방향과 라벨은 그대로다).
- 바로 위 문단이 이 그림을 읽는 법이다 — 특히 "즉시 `CompletableFuture`를 반환하고"가 비동기 묶음의 둘째 줄에 해당하고, "원래 호출 스레드가 아니라 완료를 수행한 스레드에서 실행될 수 있다"가 마지막 줄에 해당한다.

> **블로킹(blocking) / 논블로킹(non-blocking)** — 결과가 올 때까지 그 스레드가 붙들려 있는 것 / 붙들지 않고 다른 일을 하게 두는 것.\
> 예: 원문이 위 그림의 동기 묶음 마지막 화살표에 붙인 라벨이 "HttpResponse 반환 (이때까지 대기)"이고, 비동기 묶음의 셋째 화살표에 붙인 라벨이 "요청 등록 (스레드 점유 안 함)"이다.

> **`CompletableFuture`** — 아직 결과가 없지만 나중에 채워질 자리. 그 뒤에 할 일을 미리 이어 붙여 둘 수 있다.\
> 예: 위 코드에서 `sendAsync(...)`가 그것을 돌려주고, 이어 붙인 할 일이 `.thenApply(HttpResponse::body)`와 `.thenAccept(System.out::println)`다.

### 람다 파라미터에 대한 지역변수 문법 (JEP 323)
- 상태: 정식 기능
- Java 10의 `var`를 **람다 파라미터**에도 쓸 수 있게 했다. 단독으로는 타입을 명시하는 것과 차이가 없지만, 모든 파라미터에 어노테이션(`@NonNull` 등)이나 수식어를 일관되게 붙일 수 있다는 장점이 있다. 단, 일부 파라미터만 `var`로 쓰거나 명시적 타입과 섞을 수 없다(모두 `var`이거나 모두 명시이거나).

```java
// 모든 파라미터에 어노테이션 적용 가능
BiFunction<Integer, Integer, Integer> add =
        (@NonNull var x, @NonNull var y) -> x + y;
```

위 코드에서 원문이 말한 "모두 `var`이거나 모두 명시이거나"가 확인되는 부분이 `(@NonNull var x, @NonNull var y)`로, 두 파라미터가 모두 `var`다.\
원문이 주석에 적은 이 문법의 쓸모가 "모든 파라미터에 어노테이션 적용 가능"이다.

### 단일 파일 소스 코드 실행 (JEP 330)
- 상태: 정식 기능
- 컴파일(`javac`) 없이 단일 `.java` 파일을 `java` 런처로 바로 실행할 수 있다. 학습·스크립팅·프로토타이핑에 유용하다.

> **런처(launcher)** — 자바 프로그램을 띄우는 실행 명령. 여기서는 `java`가 그것이다.\
> 예: 아래 명령에서 `java Hello.java`처럼 `.java` 파일을 바로 주는 것이 이 버전에서 가능해진 일이고, 원문이 주석에 적은 말이 "이제 컴파일 단계 없이 바로 실행 가능"이다.

```bash
# 이제 컴파일 단계 없이 바로 실행 가능
java Hello.java
```

### 새로운 String / Files 메서드 (API)
- 상태: 정식 기능
- `String`에 `strip()`, `stripLeading()`, `stripTrailing()`(유니코드 인지 공백 제거), `isBlank()`, `lines()`(스트림으로 줄 분리), `repeat(int)` 추가.
- `Files.readString(Path)`, `Files.writeString(Path, CharSequence)` 추가로 파일 ↔ 문자열 변환이 한 줄로 가능.

```java
"  hello  ".strip();          // "hello" (trim보다 유니코드 공백을 더 정확히 처리)
"   ".isBlank();              // true
"=".repeat(20);              // "===================="
"a\nb\nc".lines().count();    // 3

import java.nio.file.*;
String content = Files.readString(Path.of("data.txt"));
Files.writeString(Path.of("out.txt"), "Hello, Java 11");
```

앞 네 줄에 붙은 주석은 전부 원문이 단 것으로, 각 줄이 내놓는 결과값이다(첫 줄에는 `trim`과의 대비가 덧붙어 있다).\
원문이 `strip()`에 붙인 주석 "trim보다 유니코드 공백을 더 정확히 처리"가 불릿의 "유니코드 인지 공백 제거"와 같은 이야기다.

> **유니코드 인지(Unicode-aware) 공백 제거** — 스페이스·탭뿐 아니라 유니코드가 공백으로 정한 문자까지 알아보고 떼어 내는 것.\
> 예: 원문이 `strip()` 주석에 적은 대비가 "trim보다 유니코드 공백을 더 정확히 처리"다(`trim`이 무엇을 떼는지는 원문에 없다).

## 그 외 변경 / API 추가
- **JEP 318 — Epsilon GC(실험적)**: 메모리를 할당만 하고 회수하지 않는 "No-Op" GC. 성능 테스트, 매우 단명하는 작업, GC 오버헤드 측정용.
- **JEP 333 — ZGC(실험적)**: 대용량 힙에서도 일시정지를 10ms 이하로 유지하는 것을 목표로 하는 확장 가능 저지연 GC(이 시점에는 Linux/x64 실험적).
- **JEP 328 — Flight Recorder(JFR)**: 과거 상용 기능이던 저오버헤드 프로파일링/진단 도구를 오픈소스화해 OpenJDK에 포함.
- **JEP 331 — 저오버헤드 힙 프로파일링**.
- **JEP 320 — Java EE 및 CORBA 모듈 제거**: `java.xml.ws`(JAX-WS), `java.xml.bind`(JAXB), `java.activation`, `java.corba` 등 제거. JavaFX도 JDK에서 분리되어 별도 오픈소스(OpenJFX)로 제공.
- **JEP 332 — TLS 1.3** 지원.
- **JEP 181 — Nest 기반 접근 제어**: 중첩 클래스 간 private 멤버 접근을 컴파일러의 합성 브리지 메서드 없이 JVM 레벨에서 처리.
- **JEP 309 — 동적 클래스 파일 상수(`CONSTANT_Dynamic`)**, **JEP 324 — Curve25519/Curve448 키 교환**, **JEP 329 — ChaCha20/Poly1305 암호 알고리즘**, **JEP 327 — 유니코드 10**.
- **JEP 335 — Nashorn 자바스크립트 엔진 deprecate**, **JEP 336 — Pack200 도구/API deprecate**.

> **실험적(experimental)** — 들어는 있지만 아직 정식으로 지원한다고 보증하지 않는 상태.\
> 예: 원문이 이 상태로 적은 것이 이 버전의 Epsilon GC와 ZGC이고, ZGC에는 "이 시점에는 Linux/x64 실험적"이라는 단서를 더 붙인다.

> **deprecate(사용 중단 예고)** — 아직 동작하지만 앞으로 없앨 예정이니 쓰지 말라고 표시해 두는 것.\
> 예: 원문이 이 버전에서 그렇게 된 것으로 든 둘이 Nashorn 자바스크립트 엔진(JEP 335)과 Pack200 도구/API(JEP 336)다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 불릿은 원문 두 문단을 나눠 적은 것이다.)*

- Java 11은 **Java 8 이후 가장 중요한 LTS**로 평가받으며, 많은 기업이 8에서 곧바로 11로 이주했다(중간 9·10은 단기 릴리스라 건너뛴 경우가 많다).
- 표준 HTTP 클라이언트는 외부 라이브러리(Apache HttpClient, OkHttp) 없이도 현대적 HTTP 통신을 가능하게 했고, 모듈 시스템과 함께 자바를 더 모듈화된 플랫폼으로 만들었다.
- 동시에 Java EE/CORBA/JavaFX 제거와 Nashorn deprecate(제거 예고, 실제 제거는 Java 15의 JEP 372)는 "레거시 청산"의 신호였다.
- 가장 큰 파장은 **라이선스 변화**였다. Oracle JDK가 운영 환경에서 유료가 되면서, 생태계는 OpenJDK 기반 무료 배포판(Eclipse Temurin/Adoptium, Amazon Corretto, Azul Zulu, Microsoft Build of OpenJDK 등)으로 다변화되었다.
- 오늘날 "어떤 JDK 배포판을 쓸 것인가"라는 질문이 보편화된 출발점이 바로 Java 11이다.

## 용어 풀이

- **LTS(Long-Term Support)** — 그 버전을 수년간 보안 패치를 계속 받도록 지정해 두는 것. 원문은 Java 11을 "6개월 케이던스 도입 이후 첫 LTS"로 적는다.
- **배포판(build/distribution)** — 같은 OpenJDK 소스에서 여러 회사가 각자 만들어 내놓는 JDK 꾸러미. 원문이 든 무료 쪽이 Adoptium/Temurin·Amazon Corretto·Azul Zulu·Red Hat이다.
- **OTN(Oracle Technology Network) 라이선스** — 원문이 Oracle 자사 빌드의 배포 조건으로 든 상용 라이선스. 운영/상업적 사용에 유료 구독을 요구했다.
- **incubator(인큐베이터)** — 정식 API가 되기 전에 시험 삼아 따로 내놓아 둔 상태. 승격 전 이름이 `jdk.incubator.http`였다.
- **동기 / 비동기 호출** — 결과가 올 때까지 그 자리에서 기다리는 호출 / 기다리지 않고 돌아와 나중에 결과를 받는 호출. 원문이 코드 주석으로 나눠 적은 둘이다.
- **블로킹 / 논블로킹** — 결과가 올 때까지 스레드가 붙들려 있는 것 / 붙들지 않는 것. 원문 라벨로 "이때까지 대기" / "스레드 점유 안 함"이다.
- **`CompletableFuture`** — 아직 결과가 없지만 나중에 채워질 자리. 그 뒤에 할 일을 이어 붙일 수 있다.
- **런처(launcher)** — 자바 프로그램을 띄우는 실행 명령. 이 버전부터 `.java` 파일을 바로 줄 수 있다.
- **유니코드 인지(Unicode-aware) 공백 제거** — 유니코드가 공백으로 정한 문자까지 알아보고 떼어 내는 것. 원문 표현으로 `strip()`이 "trim보다 유니코드 공백을 더 정확히 처리"한다.
- **실험적(experimental)** — 들어는 있으나 아직 정식 지원을 보증하지 않는 상태. 이 버전에서 Epsilon GC와 ZGC가 그 상태다.
- **deprecate(사용 중단 예고)** — 아직 동작하지만 앞으로 없앨 예정이라 표시해 두는 것. 원문은 Nashorn의 실제 제거를 "Java 15의 JEP 372"로 적는다.

## 참고 출처
- [JDK 11 — OpenJDK Project](https://openjdk.org/projects/jdk/11/)
- [JEP 321: HTTP Client (Standard)](https://openjdk.org/jeps/321)
- [Introducing Java SE 11 — Oracle Blog](https://blogs.oracle.com/java-platform-group/introducing-java-se-11)
- [JDK 11 Release Notes — Oracle](https://www.oracle.com/java/technologies/javase/11-relnote-issues.html)
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [90 New Features and APIs in JDK 11 — Azul](https://www.azul.com/blog/90-new-features-and-apis-in-jdk-11/)
