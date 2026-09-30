# Java SE 9 (2017년 9월)

> 원본: `~/project/java-history/java/java-9.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR/JEP 번호·클래스/패키지/도구 이름·코드블록 10개(java 7 · bash 2 · jshell 세션 1)·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개는 원문의 mermaid 그림을 글자로 옮긴 것이고, 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 교차 주 1개는 원문에 없는 보충이다.\
> 원문에 없는 도식은 새로 그리지 않았다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Project Jigsaw 모듈 시스템으로 플랫폼을 모듈화하고, 6개월 정기 릴리스 시대 직전에 등장한 마지막 "구(舊)모델" 메이저 릴리스.

이 편을 하나의 비유로 읽으면 **벽 없이 책상만 늘어놓던 사무실에, 방을 나누고 방마다 "누가 들어와도 되는 문"과 "이 방이 쓰는 다른 방"을 문패로 적어 붙인 일**이다.\
그전에는 아무 책상이나 가서 서랍을 열 수 있었다.\
**Java 9의 모듈도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 그 상태를 이렇게 적는다: "public이지만 내부용인 API(`sun.misc.Unsafe` 등)에 외부 코드가 자유롭게 접근하면서 강한 캡슐화가 불가능했다".

본문 흐름에 쓰는 비유는 이 사무실 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 벽 없이 책상만 늘어놓은 사무실 | 원문 표현으로 "거대한 모놀리식 `rt.jar` 하나로 묶여 있어" · "classpath hell" |
| 벽으로 나눈 방 하나 | 모듈 — 원문 표현으로 "이름이 있고 자기 자신을 기술하는(self-describing) 코드와 데이터의 묶음" |
| 방문 앞에 붙인 문패 | `module-info.java` — 원문 표현으로 "모듈 디스크립터" |
| 문패에 적는 "누가 들어와도 되는 문" | `exports` — 원문 표현으로 "이 패키지만 외부에 공개 (강한 캡슐화)" |
| 문패에 적는 "이 방이 쓰는 다른 방" | `requires` — 원문 표현으로 "다른 모듈에 대한 의존" |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **9가 나왔다고 모두가 모듈을 쓰게 된 것은 아니다.**\
  아래 「Java 플랫폼 모듈 시스템」 절과 「영향과 의의」가 이 기능의 비용으로 적는 문장이 그 근거다.\
  원문이 실무 패턴으로 든 것은 "모듈 마이그레이션 부담 때문에 Java 8에 머무르거나, Java 9\~10을 건너뛰고 곧바로 LTS인 Java 11로 이동하는" 쪽이다.
- **이 편의 HTTP 클라이언트는 아직 정식이 아니다.**\
  원문이 절 제목에 "(인큐베이터, JEP 110)"이라 적고, 본문에서 "이후 Java 11(JEP 321)에서 `java.net.http`로 정식 표준화되었다"고 적는다.
- **"마지막 구(舊)모델 릴리스"는 Java 9가 새 모델의 첫 버전이라는 뜻이 아니다.**\
  원문이 「시대적 배경」에서 적는 그대로다 — "Java 9는 옛 모델의 마지막 메이저 릴리스가 되었고, 6개월 뒤 Java 10(2018년 3월)이 새 모델의 첫 릴리스로 나왔다".

## 릴리스 정보
- 정식 출시일: 2017년 9월 21일
- 개발 주체: Oracle (OpenJDK / JCP)
- 플랫폼 명세: JSR 379 (Java SE 9 Platform)
- 코드네임: 별도 마케팅 코드네임 없음 (대표 프로젝트명은 "Project Jigsaw")
- LTS 여부: 비(非)LTS. 단기 지원(단기 피처 릴리스) 성격

> **LTS(Long-Term Support) / 비LTS** — 한 버전을 오래 지원해 주기로 정해 둔 것 / 그렇지 않은 것.\
> 예: 원문은 Java 9를 비LTS로 적고, 「영향과 의의」에서 그 결과를 "짧은 지원 기간을 가진 채 빠르게 Java 10·11로 대체되었다"고 적는다.

## 시대적 배경

*(「한눈에」의 사무실 비유가 가리키는 자리다.)*

Java 9의 중심 주제는 **모듈화**다. 모듈 시스템은 원래 Java 7(2011)에 포함될 예정이었으나 Java 8을 거쳐 Java 9까지 미뤄졌다. JDK 자체가 거대한 모놀리식 `rt.jar` 하나로 묶여 있어, 작은 애플리케이션조차 전체 런타임을 끌고 다녀야 했고, public이지만 내부용인 API(`sun.misc.Unsafe` 등)에 외부 코드가 자유롭게 접근하면서 강한 캡슐화가 불가능했다. "classpath hell"(클래스패스 지옥)이라 불리는 암묵적 의존성과 JAR 충돌 문제도 오래된 골칫거리였다.

모듈 시스템(JSR 376)은 진통을 겪었다. 2017년 4\~5월의 1차 Public Review 투표가 하위 호환성·벤더 종속 우려 등으로 부결되었고, 수정된 명세가 6월 재투표를 통과한 뒤, 8월 29일\~9월 11일 최종 승인 투표를 거쳐 9월 21일 출시되었다.

또한 Java 9는 **릴리스 모델 전환의 분수령**이다. GA(9월 21일)를 앞둔 2017년 9월 6일, Oracle(Mark Reinhold)은 거대 릴리스를 수년에 한 번 내던 방식을 버리고 **6개월마다 정기 피처 릴리스**를 내며 3년마다 LTS를 지정하는 새 모델로의 전환을 발표했다. 이에 따라 Java 9는 옛 모델의 마지막 메이저 릴리스가 되었고, 6개월 뒤 Java 10(2018년 3월)이 새 모델의 첫 릴리스로 나왔다.

> **모놀리식(monolithic)** — 여러 조각으로 나뉘지 않고 통째로 하나인 상태.\
> 예: 원문이 이 말로 부른 것이 JDK의 `rt.jar` 하나이고, 그 결과로 든 것이 "작은 애플리케이션조차 전체 런타임을 끌고 다녀야 했고"다.

> **강한 캡슐화(strong encapsulation)** — 안쪽에서만 쓰라고 만든 것에 바깥이 손대지 못하게 막는 것.\
> 예: 원문이 이것이 불가능했던 이유로 든 것이 "public이지만 내부용인 API(`sun.misc.Unsafe` 등)에 외부 코드가 자유롭게 접근"한 일이다.

> **classpath hell(클래스패스 지옥)** — 원문이 이 이름으로 부른 오래된 골칫거리. 원문이 함께 든 내용이 "암묵적 의존성과 JAR 충돌 문제"다.\
> 예: 원문은 이 이름과 그 두 문제만 들고, 구체적인 충돌 사례는 적지 않는다.

> **릴리스 케이던스(release cadence)** — 새 버전을 내는 주기.\
> 예: 원문이 적은 전환 내용이 "6개월마다 정기 피처 릴리스를 내며 3년마다 LTS를 지정하는" 것이고, 발표일이 2017년 9월 6일이다.

## 주요 추가 기능

### Java 플랫폼 모듈 시스템 (Project Jigsaw / JSR 376, JEP 261 등)

- 모듈(module)은 이름이 있고 자기 자신을 기술하는(self-describing) 코드와 데이터의 묶음이다. 패키지 단위의 가시성을 넘어 모듈 단위의 강한 캡슐화와 명시적 의존성을 제공한다.
- 관련 JEP: **JEP 261 모듈 시스템**, JEP 200 모듈러 JDK, JEP 201 모듈러 소스 코드, JEP 220 모듈러 런타임 이미지, JEP 260 내부 API 캡슐화.
- 모듈은 루트에 `module-info.java`(모듈 디스크립터)를 둔다. `requires`(의존), `exports`(공개 패키지), `opens`(리플렉션 허용), `provides ... with`(서비스 제공), `uses`(서비스 소비)로 관계를 선언한다.

원문이 이 기능의 비용으로 적은 문장은 「영향과 의의」의 "다만 강한 캡슐화로 인해 리플렉션에 의존하던 다수의 라이브러리·프레임워크가 깨졌고, 애플리케이션 레벨에서의 모듈 도입은 기대만큼 빠르게 확산되지 않았다"이다.

> **모듈 디스크립터(`module-info.java`)** — 그 모듈이 무엇에 기대고 무엇을 내주는지 적어 두는 파일. 원문 표현으로 모듈 "루트에" 둔다.\
> 예: 아래 코드블록 전체가 하나의 모듈 디스크립터이고, 그 이름이 `com.example.app`이다.

> **리플렉션(reflection)** — 실행 중에 클래스·필드·메서드를 이름으로 들여다보고 다루는 기능.\
> 예: 원문이 `opens`에 단 주석이 "리플렉션 접근 허용 (예: 직렬화/프레임워크)"이다 — 강한 캡슐화가 그 리플렉션에 무엇을 했는지는 바로 위 문단과 「영향과 의의」에 있다.

> **서비스(service) — `uses` / `provides ... with`** — 어떤 일을 해 줄 구현을 이름으로만 요구하는 쪽 / 실제 구현을 내놓는 쪽. 원문 주석 그대로 "서비스 소비" / "서비스 구현 제공"이다.\
> 예: 아래 코드에서 요구하는 것이 `com.example.spi.PaymentProvider`이고, 그것을 실제로 제공하는 구현이 `com.example.app.KakaoPayProvider`다.

```java
// module-info.java — 모듈 디스크립터
module com.example.app {
    requires java.sql;                 // 다른 모듈에 대한 의존
    requires transitive com.example.api; // 추이 의존 (이 모듈을 쓰는 쪽도 자동 의존)

    exports com.example.app.service;   // 이 패키지만 외부에 공개 (강한 캡슐화)
    opens com.example.app.model;       // 리플렉션 접근 허용 (예: 직렬화/프레임워크)

    uses com.example.spi.PaymentProvider;                 // 서비스 소비
    provides com.example.spi.PaymentProvider
        with com.example.app.KakaoPayProvider;            // 서비스 구현 제공
}
```

위 코드에서 원문이 주석으로 이름 붙인 키워드는 여섯이다 — `requires`("다른 모듈에 대한 의존"), `requires transitive`("추이 의존 (이 모듈을 쓰는 쪽도 자동 의존)"), `exports`("이 패키지만 외부에 공개 (강한 캡슐화)"), `opens`("리플렉션 접근 허용"), `uses`("서비스 소비"), `provides ... with`("서비스 구현 제공").

```bash
# 모듈 경로로 컴파일/실행
javac -d out --module-source-path src $(find src -name "*.java")
java --module-path out --module com.example.app/com.example.app.Main
```

`requires`(의존)와 `exports`(공개 패키지) 선언으로 모듈 간 의존성 그래프가 형성된다. 아래는 예시 앱 모듈의 의존 구조다.

```text
[상자와 그 안의 글자]
  com.app          exports: com.app.web
  com.service      exports: com.service.api
  java.base        (모든 모듈 암묵 의존)
  java.sql         exports: java.sql

[화살표 여섯 — 라벨은 모두 requires]
  com.app      --requires-->  com.service
  com.app      --requires-->  java.sql
  com.service  --requires-->  java.sql
  com.app      --requires-->  java.base
  com.service  --requires-->  java.base
  java.sql     --requires-->  java.base
```

- 이 그림은 원문의 mermaid 그림을 글자로 옮긴 것이다 — 화살표 여섯으로 원문의 화살표 수와 같고, 방향과 라벨(`requires`)도 원문과 같다.
- 위쪽 네 줄은 원문이 상자 안에 줄바꿈으로 적어 둔 글자를 두 칸으로 나눈 것이고, 상자를 선언한 순서도 원문과 같다.
- 아래쪽 여섯 줄이 원문의 화살표이며, 적은 순서도 원문이 적은 순서 그대로다.

`com.app`은 `com.service`와 `java.sql`을 명시적으로 `requires`하고, 각 모듈은 `exports`한 패키지만 외부에 노출한다. `java.base`는 모든 모듈이 자동으로 의존하는 기반 모듈이다.

### jlink — 모듈 기반 커스텀 런타임 이미지 (JEP 282)

- 애플리케이션이 실제로 쓰는 모듈만 골라 최소 크기의 전용 JRE 이미지를 만드는 링커 도구. 모듈 시스템이 있어서 가능해진 기능으로, 컨테이너·임베디드 배포에 유용하다.

> **런타임 이미지(runtime image)** — 그 프로그램을 돌리는 데 필요한 자바 실행 환경을 한 덩어리로 묶어 낸 것.\
> 예: 아래 명령이 만들어 내는 `myapp-runtime` 폴더가 그것이고, 원문은 여기에 "애플리케이션이 실제로 쓰는 모듈만" 담긴다고 적는다.

```bash
jlink --module-path $JAVA_HOME/jmods:out \
      --add-modules com.example.app \
      --output myapp-runtime
```

### jshell — Java REPL (JEP 222)

- 자바 최초의 공식 Read-Eval-Print Loop. 클래스/`main` 메서드 없이 표현식·문장을 한 줄씩 즉시 실행하고 결과를 확인할 수 있어 학습·프로토타이핑·API 탐색에 적합하다.

> **REPL(Read-Eval-Print Loop)** — 한 줄 읽고(Read), 계산하고(Eval), 결과를 찍고(Print), 다시 받는(Loop) 대화형 실행기.\
> 예: 아래 세션에서 `int x = 10`을 적자 바로 `x ==> 10`이 찍히는 것이 그 한 바퀴다.

```text
$ jshell
jshell> int x = 10
x ==> 10
jshell> IntStream.rangeClosed(1, 5).sum()
$2 ==> 15
jshell> String greet(String n) { return "Hi " + n; }
|  created method greet(String)
jshell> greet("Java")
$4 ==> "Hi Java"
```

위 세션은 원문이 그대로 실은 것이다. 원문 문장의 "클래스/`main` 메서드 없이"가 여기서 확인되는 부분이 `String greet(String n) { ... }`로, 클래스를 만들지 않고 메서드를 바로 정의해 다음 줄에서 부른다.

### 컬렉션 팩토리 메서드 (JEP 269)

- `List`, `Set`, `Map`에 간결한 불변 컬렉션 생성용 정적 팩토리 메서드 `of(...)` 추가. 반환된 컬렉션은 변경 불가(immutable)다.

> **팩토리 메서드(factory method)** — `new` 대신 불러 쓰는, 객체를 만들어 돌려주는 메서드.\
> 예: 아래 "After" 코드의 `List.of("a", "b", "c")`·`Set.of(...)`·`Map.of(...)`가 그것이다.

> **변경 불가(immutable) 컬렉션** — 만들어진 뒤로는 넣지도 빼지도 못하는 컬렉션.\
> 예: 원문이 아래 코드 마지막 줄 주석에 적어 둔 그대로다 — "모두 불변: list.add(...) 호출 시 UnsupportedOperationException".

```java
// Before (Java 8): 장황한 불변 컬렉션 생성
List<String> list = Collections.unmodifiableList(
        Arrays.asList("a", "b", "c"));
Map<String, Integer> map = new HashMap<>();
map.put("a", 1);
map.put("b", 2);
map = Collections.unmodifiableMap(map);
```

```java
// After (Java 9): 팩토리 메서드 한 줄
List<String> list = List.of("a", "b", "c");
Set<String> set   = Set.of("x", "y", "z");
Map<String, Integer> map = Map.of("a", 1, "b", 2);
Map<String, Integer> big = Map.ofEntries(
        Map.entry("a", 1),
        Map.entry("b", 2));
// 모두 불변: list.add(...) 호출 시 UnsupportedOperationException
```

두 블록을 맞대어 보면, 위 블록의 `Collections.unmodifiableList(Arrays.asList("a", "b", "c"))` 두 줄이 아래 블록의 `List.of("a", "b", "c")` 한 줄이 되고, `new HashMap<>()` + `put` 두 번 + `Collections.unmodifiableMap(map)` 네 줄이 `Map.of("a", 1, "b", 2)` 한 줄이 된다.\
원문이 두 블록 첫 줄 주석에 붙인 이름이 각각 "장황한 불변 컬렉션 생성"과 "팩토리 메서드 한 줄"이다.

### private 인터페이스 메서드 (Milling Project Coin, JEP 213)

- Java 8에서 도입된 `default`/`static` 인터페이스 메서드 간의 공통 로직을 캡슐화하기 위해, 인터페이스에 `private` 및 `private static` 메서드를 허용.
- JEP 213은 그 외에도 try-with-resources의 effectively-final 변수 사용 허용, 다이아몬드 연산자의 익명 클래스 적용, private 메서드에 `@SafeVarargs` 허용, 식별자 `_`(단독 언더스코어) 금지 등 작은 개선을 포함한다.

```java
interface Logger {
    default void logInfo(String msg)  { log("INFO", msg); }
    default void logError(String msg) { log("ERROR", msg); }

    // private 메서드: default 메서드들의 공통 로직 캡슐화 (외부 비공개)
    private void log(String level, String msg) {
        System.out.println("[" + level + "] " + msg);
    }
}
```

위 코드에서 원문 문장의 "`default`/`static` 인터페이스 메서드 간의 공통 로직"에 해당하는 것이 `logInfo`와 `logError`가 똑같이 부르는 `log(...)`이고, 그 `log`에 원문이 단 주석이 "private 메서드: default 메서드들의 공통 로직 캡슐화 (외부 비공개)"다.

### HTTP/2 클라이언트 (인큐베이터, JEP 110)

- `HttpURLConnection`의 낡은 한계를 대체하는 새 HTTP 클라이언트. HTTP/2와 WebSocket을 지원하며 동기/비동기 요청을 제공한다.
- Java 9에서는 **인큐베이터 모듈**(모듈명 `jdk.incubator.httpclient`, 패키지 `jdk.incubator.http`)로 시범 도입되었고, 이후 Java 11(JEP 321)에서 `java.net.http`로 정식 표준화되었다.
- 정식화 과정에서 패키지뿐 아니라 API 이름도 바뀌었다. 아래 인큐베이터 코드의 `HttpResponse.BodyHandler.asString()`은 Java 11에서 `HttpResponse.BodyHandlers.ofString()`에 해당한다.

**언제 정식이 됐나** — 원문이 둘째 불릿에 적은 그대로다. 이 편에서는 인큐베이터 모듈이고, 정식 표준화는 Java 11(JEP 321)에서 `java.net.http`로 이뤄졌다.

> **인큐베이터 모듈(incubator module)** — 정식 API가 되기 전에 시험 삼아 따로 내놓는 모듈. 이름부터 정식과 다르다.\
> 예: 원문이 적은 이 시점의 이름이 모듈 `jdk.incubator.httpclient`, 패키지 `jdk.incubator.http`이고, 정식화된 뒤의 이름은 `java.net.http`다.

```java
// Java 9 인큐베이터 API (이후 java.net.http로 표준화됨)
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder()
        .uri(URI.create("https://example.com"))
        .GET()
        .build();
HttpResponse<String> res =
        client.send(req, HttpResponse.BodyHandler.asString());
System.out.println(res.statusCode());
```

### 프로세스 API 개선 (JEP 102)

- 운영체제 프로세스를 다루는 API 강화. `ProcessHandle`로 PID 조회, 자식/후손 프로세스 열거, 생존 여부 확인, 종료 시 콜백 등을 지원.

> **프로세스(process)와 PID** — 운영체제가 돌리고 있는 프로그램 하나와, 그것에 붙은 번호.\
> 예: 아래 코드의 `current.pid()`가 지금 이 자바 프로그램 자신의 번호를 가져온다.

```java
ProcessHandle current = ProcessHandle.current();
System.out.println("PID: " + current.pid());
current.info().command().ifPresent(System.out::println);
ProcessHandle.allProcesses()
        .filter(p -> p.info().command().isPresent())
        .forEach(p -> System.out.println(p.pid()));
```

위 코드에서 원문 목록의 "PID 조회"에 해당하는 것이 `current.pid()`다. 나머지 셋(자식/후손 프로세스 열거, 생존 여부 확인, 종료 시 콜백)은 목록에만 있고 이 코드에는 나오지 않는다.

### G1을 기본 가비지 컬렉터로 (JEP 248)

- 32비트/64비트 서버 구성에서 **G1(Garbage-First) GC를 기본 GC로** 채택. 기존 기본값이던 Parallel GC를 대체하여, 큰 힙에서도 예측 가능한 짧은 정지 시간(low-pause)을 우선하는 방향으로 전환했다.

> **기본 GC(default garbage collector)** — 따로 지정하지 않으면 JVM이 쓰는 가비지 컬렉터.\
> 예: 원문에 따르면 서버 구성에서 이 자리를 이 버전 전까지 Parallel GC가 차지했고, 이 버전부터 G1이 차지한다.

> **정지 시간(pause)** — GC가 일하는 동안 애플리케이션이 멈춰 있는 시간.\
> 예: 원문이 이 전환의 방향으로 적은 말이 "큰 힙에서도 예측 가능한 짧은 정지 시간(low-pause)을 우선하는"이다.

> **재서술자 주:** G1이 어디서 왔는지는 이 편 밖이다. 같은 시리즈 `java-7.md`가 G1 도입을 적으면서 "Java 7 GA에서는 experimental 상태였고, 정식 지원은 7u4부터"라고 적는다.

### Stream / Optional API 개선

- **Stream**: `takeWhile`, `dropWhile`(조건 기반 자르기), 3인자 `iterate(seed, hasNext, next)`(종료 조건을 받는 오버로드), `ofNullable`(null이면 빈 스트림) 추가.
- **Optional**: `ifPresentOrElse`(값 유무에 따라 분기), `or`(빈 경우 대체 Optional), `stream`(Optional → Stream 변환) 추가.

```java
Stream.iterate(1, n -> n <= 100, n -> n * 2)  // 종료 조건 포함 iterate
      .forEach(System.out::println);

Stream.of(1, 2, 3, 4, 5)
      .takeWhile(n -> n < 4)   // [1, 2, 3]
      .forEach(System.out::println);

Optional.ofNullable(user)
        .ifPresentOrElse(
            u -> System.out.println(u.getName()),
            () -> System.out.println("no user"));
```

위 코드에서 원문이 주석으로 결과를 적어 둔 것은 `takeWhile(n -> n < 4)` 한 줄로, 그 결과가 `[1, 2, 3]`이다.\
`ifPresentOrElse`의 두 인자가 원문 목록의 "값 유무에 따라 분기"에 해당하는데, 값이 있을 때가 `u -> System.out.println(u.getName())`이고 없을 때가 `() -> System.out.println("no user")`다.

## 그 외 변경 / API 추가
- **JEP 266 — More Concurrency Updates**: Reactive Streams 표준을 구현한 `java.util.concurrent.Flow`(Publisher/Subscriber/Processor) API 도입, `CompletableFuture` 보강(`completeOnTimeout`, `orTimeout` 등).
- **JEP 193 — Variable Handles (VarHandles)**: `sun.misc.Unsafe` 대체를 위한 안전한 저수준 메모리/필드 원자 연산 API.
- **JEP 238 — Multi-Release JAR Files**: 하나의 JAR에 자바 버전별 클래스를 함께 담아 런타임 버전에 맞는 구현을 선택.
- **JEP 254 — Compact Strings**: `String` 내부 저장을 `char[]`(UTF-16)에서 `byte[]` + 인코딩 플래그(Latin-1/UTF-16)로 변경하여 Latin-1 문자열의 메모리 사용량을 절감.
- **JEP 295 — Ahead-of-Time Compilation**: `jaotc`를 통한 실험적 AOT 컴파일.
- **JEP 158/271 — Unified JVM/GC Logging**: 로그 출력을 단일 프레임워크(`-Xlog`)로 통합.
- **JEP 277 — Enhanced Deprecation**: `@Deprecated`에 `since`, `forRemoval` 속성 추가.
- **JEP 213 부수**: `@SafeVarargs`를 private 메서드에도 적용 등.
- **JEP 222 외 도구**: `jdeps` 강화, `jlink`, `jmod` 등 모듈 관련 도구군 추가.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 불릿은 원문 두 문단을 나눠 적은 것이다.)*

- Java 9의 가장 큰 유산은 두 가지다.
- 첫째, **모듈 시스템**은 플랫폼을 모듈화하여 보안(내부 API 캡슐화)·확장성·배포 최적화(jlink)의 토대를 놓았다.
- 다만 강한 캡슐화로 인해 리플렉션에 의존하던 다수의 라이브러리·프레임워크가 깨졌고, 애플리케이션 레벨에서의 모듈 도입은 기대만큼 빠르게 확산되지 않았다. 그럼에도 JDK 자체의 모듈화와 내부 API 차단은 이후 자바의 보안·진화 전략의 핵심이 되었다.
- 둘째, Java 9는 **릴리스 케이던스 전환의 경계선**이다. 이 버전을 끝으로 자바는 6개월 정기 릴리스 + LTS 모델로 이행했고, 그 결과 Java 9는 비LTS로 짧은 지원 기간을 가진 채 빠르게 Java 10·11로 대체되었다.
- 실무에서는 많은 조직이 모듈 마이그레이션 부담 때문에 Java 8에 머무르거나, Java 9\~10을 건너뛰고 곧바로 LTS인 Java 11로 이동하는 패턴을 보였다.
- 한편 jshell(REPL)과 컬렉션 팩토리 메서드처럼 일상 개발 경험을 직접 개선한 기능들은 버전과 무관하게 빠르게 자리 잡았다.

## 용어 풀이

- **LTS(Long-Term Support) / 비LTS** — 한 버전을 오래 지원해 주기로 정해 둔 것 / 그렇지 않은 것. 원문은 Java 9를 비LTS, "단기 지원(단기 피처 릴리스) 성격"으로 적는다.
- **릴리스 케이던스(release cadence)** — 새 버전을 내는 주기. 이 시점의 전환 내용이 "6개월마다 정기 피처 릴리스"와 "3년마다 LTS 지정"이다.
- **모놀리식(monolithic)** — 여러 조각으로 나뉘지 않고 통째로 하나인 상태. 원문이 이 말로 부른 것이 JDK의 `rt.jar`다.
- **강한 캡슐화(strong encapsulation)** — 안쪽에서만 쓰라고 만든 것에 바깥이 손대지 못하게 막는 것. 모듈 시스템이 제공하는 것이 "모듈 단위의" 이것이다.
- **classpath hell(클래스패스 지옥)** — 원문이 이 이름으로 부른 골칫거리. 원문이 함께 든 내용이 "암묵적 의존성과 JAR 충돌 문제"다.
- **모듈(module)** — 원문 표현으로 "이름이 있고 자기 자신을 기술하는(self-describing) 코드와 데이터의 묶음".
- **모듈 디스크립터(`module-info.java`)** — 모듈 루트에 두고 의존·공개 관계를 선언하는 파일.
- **`requires` / `exports` / `opens`** — 다른 모듈에 대한 의존 / 이 패키지만 외부에 공개 / 리플렉션 접근 허용. 셋 다 원문의 코드 주석 표현 그대로다.
- **`requires transitive`** — 원문 주석 표현으로 "추이 의존 (이 모듈을 쓰는 쪽도 자동 의존)".
- **`uses` / `provides ... with`** — 서비스 소비 / 서비스 구현 제공. 원문의 코드 주석 표현 그대로다.
- **리플렉션(reflection)** — 실행 중에 클래스·필드·메서드를 이름으로 들여다보고 다루는 기능. 원문이 `opens`의 쓰임으로 든 예가 직렬화·프레임워크다.
- **런타임 이미지(runtime image)** — 프로그램을 돌릴 자바 실행 환경을 한 덩어리로 묶어 낸 것. `jlink`가 "최소 크기의 전용 JRE 이미지"로 만들어 준다.
- **REPL(Read-Eval-Print Loop)** — 한 줄 읽고 계산하고 찍고 다시 받는 대화형 실행기. 원문은 `jshell`을 "자바 최초의 공식" REPL로 적는다.
- **팩토리 메서드(factory method)** — `new` 대신 불러 쓰는, 객체를 만들어 돌려주는 메서드. 이 편에서 추가된 것이 `of(...)`다.
- **변경 불가(immutable) 컬렉션** — 만들어진 뒤로는 넣지도 빼지도 못하는 컬렉션. 원문 주석대로 `add`를 부르면 `UnsupportedOperationException`이 난다.
- **인큐베이터 모듈(incubator module)** — 정식 API가 되기 전에 시험 삼아 따로 내놓는 모듈. 이 편의 HTTP 클라이언트가 그 상태다.
- **프로세스(process) / PID** — 운영체제가 돌리는 프로그램 하나 / 그것에 붙은 번호.
- **기본 GC(default garbage collector)** — 따로 지정하지 않으면 JVM이 쓰는 가비지 컬렉터. 원문은 서버 구성에서 이 버전부터 Parallel GC 대신 G1이 그 자리를 맡는다고 적는다.
- **정지 시간(pause)** — GC가 일하는 동안 애플리케이션이 멈춰 있는 시간. 원문 표현으로 G1은 "예측 가능한 짧은 정지 시간(low-pause)을 우선"한다.

## 참고 출처
- [Java SE 9 released today (InfoQ, 2017-09-21)](https://www.infoq.com/news/2017/09/Java-9-release-sept-21/)
- [Java Platform Module System (Wikipedia)](https://en.wikipedia.org/wiki/Java_Platform_Module_System)
- [Java version history (Wikipedia)](https://en.wikipedia.org/wiki/Java_version_history)
- [Java 9 Modules (DigitalOcean)](https://www.digitalocean.com/community/tutorials/java-9-modules)
- [The road to Java 9: The current status (InfoWorld)](https://www.infoworld.com/article/2253040/the-road-to-java-9-the-current-status.html)
- [Java 9 Features with Examples (GeeksforGeeks)](https://www.geeksforgeeks.org/java/java-9-features-with-examples/)
