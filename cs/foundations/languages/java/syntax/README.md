# Java — 문법·API 주제 목록

> 1단계 리스트업이다. 3파일(질문·서머리·정답)이 있는 주제는 **주제 이름에 폴더 링크**가 걸려 있다.
> **진행 — 5 / 60** (2026-09-21 파일럿: [01](01-primitives-and-wrappers/) · [06](06-initialization-order/) · [27](27-equals-hashcode-contract/) · [44](44-stream-creation/) · [45](45-intermediate-operations/)). 나머지는 아직 없다.
> 기준 소스: [Java Language Specification SE 21](https://docs.oracle.com/javase/specs/jls/se21/html/index.html) · [Java SE 21 API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/index.html) · [JEP 색인](https://openjdk.org/jeps/0) (JDK [21](https://openjdk.org/projects/jdk/21/) · [24](https://openjdk.org/projects/jdk/24/) · [25](https://openjdk.org/projects/jdk/25/) 릴리스 페이지로 기능의 확정 버전 확인)
> 실행 검증: **가능**. 이 머신에 sdkman JDK 17.0.13 · 21.0.5 · 25.0.1(Temurin)과 `javac`가 있다. 시스템 기본 `java`는 1.8이므로 **JDK 경로를 명시해 실행**한다(`~/.sdkman/candidates/java/21.0.5-tem/bin/`). 21에서 돌린 것·25에서만 도는 것을 나눠 적는다.
> 기준일 2026-09-20.

## 이 언어에서 무엇을 자르는 축

JLS 자신의 목차는 **타입(4장) → 클래스·인터페이스(8·9장) → 문장·패턴(14장) → 식(15장) → 스레드와 락(17장)** 순으로, "무엇을 선언하는가"와 "무엇이 실행되는가"를 갈라 놓는다. 이 목록은 그 골격은 따르되, 학습 순서에 맞춰 **선언 → 타입 시스템 → 제어·패턴 → 예외 → 함수형** 으로 다시 세운다.

표준 API 쪽은 `java.base` 모듈의 패키지 경계를 그대로 쓰지 않았다. `java.util` 하나에 컬렉션·스트림·시간·동시성이 섞여 있어 패키지가 학습 단위가 되지 못하기 때문이다. 대신 **"한 번에 인출할 수 있는 기능 하나"** 를 단위로 잘랐다 — 스트림은 생성·중간 연산·최종 연산·수집·병렬로 다섯 갈래가 되고, 컬렉션은 계층 지도·List/Set·Map·순서 보장·순회로 다섯 갈래가 된다.

버전은 **21 LTS를 기준선**으로 잡고, 21 이후에 확정된 것(Gatherers 24, 모듈 import·유연한 생성자 본문 25)은 주제 이름에 버전을 달았다. JVM 내부(GC·JIT·클래스로더·메모리 모델)는 이 목록에서 다루지 않는다 — [`../언어-특성/README.md`](../언어-특성/README.md)의 영역이다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | [기본형과 래퍼 — 값 의미론·오토박싱·`Integer` 캐시](01-primitives-and-wrappers/) | 문법 | `==` 가 언제 참조를 비교하고 언제 값을 비교하는지 예측할 수 있다 | — | [`../../../data-representation/`](../../../data-representation/) | A |
| 02 | 수치 연산 — 이항 승격·정수 오버플로·`Math.*Exact` | 문법 | `int` 곱셈이 조용히 음수가 되는 자리를 예측하고 방어 선택을 판단할 수 있다 | 01 | [`../../../data-representation/`](../../../data-representation/) | A |
| 03 | 변수와 대입 — 전부 값 전달·`final`·effectively final | 문법 | 메서드에 객체를 넘겼을 때 무엇이 바뀌고 무엇이 안 바뀌는지 설명할 수 있다 | 01 | [`../../../variables-and-memory/`](../../../variables-and-memory/) | A |
| 04 | `var` 지역 변수 타입 추론 (10+) | 문법 | `var` 가 추론하는 타입과 쓸 수 없는 자리를 판단할 수 있다 | 03 | [`../../../../../history/java/java-10.md`](../../../../../history/java/java-10.md) | B |
| 05 | 배열 — 생성·기본값·공변성·`Arrays` 유틸 | 문법 | 배열 공변성이 런타임 `ArrayStoreException` 으로 나오는 경로를 예측할 수 있다 | 01 | [`../../../../data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) | A |
| 06 | [클래스 멤버와 초기화 순서 — static/인스턴스 초기화 블록](06-initialization-order/) | 문법 | 필드·초기화 블록·생성자가 어느 순서로 도는지 설명할 수 있다 | — | — | A |
| 07 | 생성자 — `this()`/`super()`·(25) 유연한 생성자 본문 | 문법 | `super()` 앞에서 무엇을 할 수 있는지 21과 25로 나눠 판단할 수 있다 | 06 | [`../../../../../history/java/java-25.md`](../../../../../history/java/java-25.md) | A |
| 08 | 메서드 선언 — 오버로딩 해소·가변 인자 | 문법 | 오버로딩 후보 중 어느 것이 뽑히는지 박싱·가변 인자까지 넣어 예측할 수 있다 | — | — | A |
| 09 | 상속과 오버라이딩 — 동적 디스패치·공변 반환·필드 숨김 | 문법 | 메서드는 재정의되고 필드는 숨겨지는 차이를 예측할 수 있다 | 08 | [`../../../oop-basics/`](../../../oop-basics/) | A |
| 10 | 접근 제어자 — package-private·`protected` 의 실제 경계 | 문법 | 네 단계가 각각 어디까지 열리는지 다른 패키지의 하위 클래스까지 넣어 판단할 수 있다 | — | — | A |
| 11 | 인터페이스 — `default`/`static`/`private` 메서드와 충돌 해소 (8+) | 문법 | 같은 시그니처의 default 메서드 둘을 상속했을 때 무엇이 필요한지 설명할 수 있다 | 09 | [`../../../../../history/java/java-8.md`](../../../../../history/java/java-8.md) | A |
| 12 | 중첩 클래스 — static nested·inner·지역·익명 | 문법 | inner 클래스가 바깥 인스턴스를 붙잡는 비용과 누수 경로를 설명할 수 있다 | 09 | — | B |
| 13 | `enum` 클래스 — 상수별 본문·`EnumSet`/`EnumMap` | 문법 | enum 을 분기 대신 다형성으로 쓰는 자리와 `EnumMap` 이 빠른 이유를 판단할 수 있다 | 06 | — | A |
| 14 | `record` (16+) — 컴팩트 생성자·불변 계약·못 하는 것 | 문법 | record 로 바꿔도 되는 클래스와 안 되는 클래스를 판단할 수 있다 | 06 | [`../../../../../history/java/java-16.md`](../../../../../history/java/java-16.md) | A |
| 15 | `sealed` (17+) — `permits`·허용 계층의 조건 | 문법 | 하위 타입을 늘렸을 때 어디가 컴파일 에러로 터지는지 예측할 수 있다 | 11, 14 | [`../../../../../history/java/java-17.md`](../../../../../history/java/java-17.md) | A |
| 16 | 애너테이션 — 선언·`@Retention`·`@Target`·메타 애너테이션 | 문법 | 런타임에 읽히는 애너테이션과 컴파일에서 사라지는 애너테이션을 구분·판단할 수 있다 | — | — | B |
| 17 | 제네릭 선언 — 타입 파라미터·바운드·제네릭 메서드 | 문법 | 타입 파라미터를 클래스에 둘지 메서드에 둘지 판단할 수 있다 | 09 | — | A |
| 18 | 와일드카드와 PECS — `? extends`/`? super` | 문법 | 어느 쪽 와일드카드가 읽기·쓰기를 막는지 예측할 수 있다 | 17 | — | A |
| 19 | 타입 소거 — 런타임에 없는 것·제네릭 배열 금지·브리지 메서드 | 문법 | 제네릭 때문에 못 쓰는 문법(`new T[]`·`instanceof List<String>`)의 이유를 설명할 수 있다 | 17 | [`../../../../../history/java/java-5.md`](../../../../../history/java/java-5.md) | B |
| 20 | 제어문 — 향상된 `for`·레이블 `break`/`continue` | 문법 | 중첩 루프를 레이블로 빠져나오는 형태와 그 대안을 판단할 수 있다 | — | — | A |
| 21 | `switch` 문과 `switch` 식 (14+) — 화살표·`yield`·fallthrough | 문법 | 문과 식의 완결성 요구 차이를 설명하고 fallthrough 버그를 예측할 수 있다 | 20 | [`../../../../../history/java/java-14.md`](../../../../../history/java/java-14.md) | A |
| 22 | `instanceof` 타입 패턴 (16+) | 문법 | 패턴 변수의 스코프가 어디까지인지 `&&`/`!` 조합에서 예측할 수 있다 | 09 | [`../../../../../history/java/java-16.md`](../../../../../history/java/java-16.md) | A |
| 23 | `switch` 패턴 매칭 (21) — 완결성·`null`·`when` 가드 | 문법 | sealed 타입 분기에서 `default` 를 안 쓰는 것이 왜 이득인지 판단할 수 있다 | 15, 21, 22 | [`../../../../../history/java/java-21.md`](../../../../../history/java/java-21.md) | A |
| 24 | `record` 패턴 (21) — 중첩 해체 | 문법 | 중첩 record 를 한 줄로 분해하는 형태와 그 한계를 설명할 수 있다 | 14, 23 | [`../../../../../history/java/java-21.md`](../../../../../history/java/java-21.md) | B |
| 25 | 예외 — checked/unchecked·전파·다중 `catch`·재던지기 | 문법 | 어떤 예외를 검사 예외로 둘지, 삼키면 무엇이 사라지는지 판단할 수 있다 | — | [`../../../../ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) | A |
| 26 | `try`-with-resources — `AutoCloseable`·suppressed·`finally` 순서 | 문법 | 본문과 `close()` 가 함께 던질 때 어느 예외가 남는지 예측할 수 있다 | 25 | — | A |
| 27 | [`equals`/`hashCode`/`toString` 계약](27-equals-hashcode-contract/) | 문법 | 계약을 깬 객체가 `HashMap` 에서 어떻게 사라지는지 예측할 수 있다 | 09 | [`../../../../data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | A |
| 28 | `Comparable`/`Comparator` — 전순서 계약과 위반의 결과 | 문법 | 비일관 비교자가 정렬에서 예외로 터지는 조건을 설명할 수 있다 | 27 | [`../../../../algorithm/01-elementary-sort/`](../../../../algorithm/01-elementary-sort/) | A |
| 29 | 람다 — 문법·변수 캡처·`this` 의 의미 (8+) | 문법 | 람다의 `this` 가 익명 클래스와 왜 다른지 설명할 수 있다 | 11 | [`../../../../../history/java/java-8.md`](../../../../../history/java/java-8.md) | A |
| 30 | 메서드 참조 네 형태 | 문법 | 어떤 람다가 어떤 메서드 참조로 바뀌는지, 안 바뀌는 경우를 판단할 수 있다 | 29 | — | B |
| 31 | 함수형 인터페이스 — `java.util.function` 지도·`@FunctionalInterface` | 문법 | 필요한 시그니처에 맞는 표준 인터페이스를 고르고 없으면 직접 만들 수 있다 | 29 | — | A |
| 32 | 텍스트 블록 (15+) | 문법 | 들여쓰기 제거 규칙과 개행 처리를 예측할 수 있다 | — | [`../../../../../history/java/java-15.md`](../../../../../history/java/java-15.md) | C |
| 33 | `synchronized`·`volatile` — 문법과 그 보장이 끝나는 자리 | 문법 | 어느 모니터로 짝을 맞춰야 보장이 성립하는지 판단할 수 있다 | — | [`../언어-특성/README.md`](../언어-특성/README.md) §9 | B |
| 34 | `import`·static import·(25) 모듈 import 선언 | 문법 | 이름 충돌이 언제 컴파일 에러가 되는지 설명할 수 있다 | — | [`../../../../../history/java/java-9.md`](../../../../../history/java/java-9.md) · [`java-25.md`](../../../../../history/java/java-25.md) | C |
| 35 | `String` — 불변성·상수 풀·자주 쓰는 메서드 | 표준 API | 같은 리터럴이 같은 객체인지, `new String` 이 무엇을 바꾸는지 예측할 수 있다 | 01 | — | A |
| 36 | `StringBuilder` 와 문자열 연결이 컴파일되는 모습 | 표준 API | 루프 안 `+=` 가 왜 느린지 바이트코드 수준으로 설명할 수 있다 | 35 | — | A |
| 37 | 정규식 — `Pattern`/`Matcher`·`String` 의 정규식 메서드 | 표준 API | `matches`/`find`/`split` 이 각각 무엇을 요구하는지 판단할 수 있다 | 35 | [`../../../../algorithm/25-string-matching/`](../../../../algorithm/25-string-matching/) | B |
| 38 | `Optional` — 생성·소비·안티패턴 | 표준 API | 필드·파라미터에 `Optional` 을 두면 안 되는 이유를 설명할 수 있다 | 25 | — | A |
| 39 | 컬렉션 프레임워크 지도 — 인터페이스 계층과 구현체 선택 | 표준 API | 요구(순서·중복·정렬·동시성)에서 구현체를 역으로 고를 수 있다 | 17 | [`../../../../data-structure/`](../../../../data-structure/) | A |
| 40 | `List`·`Set` API 와 불변 팩토리 — `List.of`·`copyOf`·`unmodifiable*` | 표준 API | "불변"과 "수정 불가 뷰"의 차이를 예측할 수 있다 | 39 | [`../../../../data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) | A |
| 41 | `Map` API — `merge`/`compute*`/`getOrDefault`/`putIfAbsent` | 표준 API | 카운팅·누적 코드를 한 호출로 줄이고 `null` 값의 의미를 판단할 수 있다 | 39 | [`../../../../data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | A |
| 42 | `SequencedCollection` (21) — 순서 있는 컬렉션의 공통 API | 표준 API | `getFirst`/`reversed` 가 어느 타입에 생겼고 무엇을 통일했는지 설명할 수 있다 | 39 | [`../../../../../history/java/java-21.md`](../../../../../history/java/java-21.md) | B |
| 43 | `Iterator`·`ListIterator`·fail-fast 와 `ConcurrentModificationException` | 표준 API | 순회 중 삭제가 언제 터지고 어떻게 안전하게 하는지 예측할 수 있다 | 39 | — | A |
| 44 | [`Stream` 생성 — 소스별·기본형 스트림](44-stream-creation/) | 표준 API | 컬렉션·배열·`Stream.iterate`·`IntStream` 중 무엇을 쓸지 판단할 수 있다 | 31, 39 | [`../../../../../history/java/java-8.md`](../../../../../history/java/java-8.md) | A |
| 45 | [중간 연산 — `map`/`filter`/`flatMap`/`mapMulti`](45-intermediate-operations/) | 표준 API | `map` 과 `flatMap` 이 갈리는 자리를 타입으로 판단할 수 있다 | 44 | — | A |
| 46 | 최종 연산과 지연 평가·단락 평가 | 표준 API | 최종 연산이 없으면 아무 일도 안 일어나는 이유와 실행 순서를 설명할 수 있다 | 45 | — | A |
| 47 | `Collectors` — 기본 수집기와 `toMap` 의 함정 | 표준 API | 키 충돌·`null` 값에서 `toMap` 이 터지는 조건을 예측할 수 있다 | 46 | — | A |
| 48 | `Collectors` 그룹핑·분할·다운스트림 | 표준 API | 2단 그룹핑과 집계를 다운스트림 조합으로 조립할 수 있다 | 47 | — | A |
| 49 | 병렬 스트림 — 값이 나오는 조건 | 표준 API | 병렬이 손해인 경우(분할 불가·작은 데이터·공유 상태)를 판단할 수 있다 | 46 | [`../언어-특성/README.md`](../언어-특성/README.md) | B |
| 50 | `Stream` Gatherers (24) — 커스텀 중간 연산 | 표준 API | 기존 중간 연산으로 안 되는 것(윈도·스캔)을 어떻게 메우는지 설명할 수 있다 | 46 | [`../../../../../history/java/java-24.md`](../../../../../history/java/java-24.md) | C |
| 51 | `java.time` — `Instant`·`LocalDate`/`LocalDateTime`·`ZonedDateTime` | 표준 API | "언제"를 표현할 때 어느 타입이 맞는지 시간대 유무로 판단할 수 있다 | — | [`../../../../ops-patterns/17-timeseries/`](../../../../ops-patterns/17-timeseries/) | A |
| 52 | `Duration`·`Period`·`DateTimeFormatter` | 표준 API | 기계 시간 간격과 달력 간격이 갈리는 지점을 예측할 수 있다 | 51 | — | B |
| 53 | `BigDecimal` — 스케일·반올림·`equals` vs `compareTo` | 표준 API | 금액 계산에서 `double` 이 틀리는 자리와 `equals` 함정을 설명할 수 있다 | 02 | [`../../../data-representation/`](../../../data-representation/) | A |
| 54 | `java.util.concurrent` — `ExecutorService`·`Future`·`CompletableFuture` | 표준 API | 스레드를 직접 만들지 않고 작업을 제출·조합·종료하는 형태를 설계할 수 있다 | 25, 31 | [`../../../process-thread/`](../../../process-thread/) | A |
| 55 | 원자 변수와 동시 컬렉션 — `Atomic*`·`ConcurrentHashMap` | 표준 API | 락 없이 안전한 갱신이 가능한 조건과 복합 연산의 위험을 판단할 수 있다 | 33, 41 | [`../언어-특성/README.md`](../언어-특성/README.md) §9 | B |
| 56 | 가상 스레드 (21) — 쓰는 법과 막히는 자리 | 표준 API | 어떤 블로킹이 캐리어를 붙잡는지(고정) 예측할 수 있다 | 54 | [`../../../../../history/java/java-21.md`](../../../../../history/java/java-21.md) · [`../../../process-thread/`](../../../process-thread/) | B |
| 57 | `Files`·`Path` — NIO.2 파일 API | 표준 API | 파일을 줄 단위로 읽고 안전하게 쓰는 형태를 고를 수 있다 | 26, 44 | [`../../../../data-structure/33-filesystem/`](../../../../data-structure/33-filesystem/) | B |
| 58 | 리플렉션 — `Class`·`getDeclared*`·접근 제어 우회의 경계 | 표준 API | 프레임워크가 어떻게 필드를 채우는지, 무엇이 막히는지 설명할 수 있다 | 16, 19 | [`../언어-특성/README.md`](../언어-특성/README.md) §3 | C |
| 59 | 불변 객체 만들기 — 방어적 복사·`record` 와의 조합 | 관용구 | "불변으로 만들었다"가 깨지는 경로(컬렉션 필드·배열 필드)를 찾아낼 수 있다 | 14, 40 | — | A |
| 60 | `null` 다루기 — `Objects.requireNonNull`·`Optional` 의 경계 | 관용구 | 어디서 막고 어디서 통과시킬지 계층별로 판단할 수 있다 | 38 | — | A |

**60주제** (문법 34 · 표준 API 24 · 관용구 2 / 우선 A 42 · B 14 · C 4)

- **분류** — `문법` / `표준 API` / `관용구` 중 하나
- **무엇을 인출하게 되나** — 한 줄. 「~를 안다」가 아니라 **「~를 설명·예측·판단할 수 있다」**
- **선행** — 먼저 봐야 하는 주제 번호(없으면 `—`). 모든 선행은 자기보다 작은 번호라 순환이 없다
- **기존 주제** — `cs/**` 나 `history/**` 에 이미 있으면 그 경로
- **우선** — `A`(핵심·먼저) / `B`(중요) / `C`(나중에)

## 기존 주제와 겹치는 것

| 겹치는 주제 | 기존에 있는 것 | 새 주제를 어떻게 좁혔나 |
|---|---|---|
| 05 배열 · 40 `List`/`Set` | [`data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) — 동적 배열이라는 **자료구조**(증폭·상환 분석) | 자료구조 설명은 안 한다. **Java 배열의 언어 규칙**(공변성·기본값·`Arrays` 유틸)과 **`List` 구현체를 고르는 판단**만 |
| 39 컬렉션 지도 · 41 `Map` | [`data-structure/`](../../../../data-structure/) 35편 — 해시맵·트리·힙·트라이의 내부 | 내부 구조는 거기. 여기는 **`java.util` 이 그것들을 어떤 인터페이스로 노출하고 어느 구현체를 언제 고르는가** |
| 27 `equals`/`hashCode` | [`data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) — 해시 충돌·버킷 | 해시 원리는 거기. 여기는 **계약 문서(javadoc)가 요구하는 다섯 조항과 위반 시 관측되는 증상** |
| 28 `Comparator` | [`algorithm/01-elementary-sort/`](../../../../algorithm/01-elementary-sort/) — 정렬 알고리즘 | 알고리즘은 거기. 여기는 **비교자 계약과 `TimSort` 가 계약 위반을 감지해 던지는 예외** |
| 14 `record` · 15 `sealed` · 22~24 패턴 · 42 `SequencedCollection` · 56 가상 스레드 · 50 Gatherers · 04 `var` · 32 텍스트 블록 · 07 유연한 생성자 본문 · 34 모듈 import | [`history/java/`](../../../../../history/java/) 28편 — **언제·왜 들어왔나**(JEP 번호·설계 논쟁) | 역사는 링크만. 여기는 **어떻게 쓰고 무엇을 못 하나** — 예: record 의 역사는 java-16, 이 목록의 record 는 "컴팩트 생성자에서 뭘 할 수 있고 상속은 왜 안 되나" |
| 29 람다 · 31 함수형 인터페이스 · 11 default 메서드 · 44~49 스트림 | [`history/java/java-8.md`](../../../../../history/java/java-8.md) — Java 8 이 무엇을 바꿨나 | 도입 맥락은 거기. 여기는 **연산 하나하나의 계약과 실패 모드**(`toMap` 키 충돌·병렬의 조건) |
| 33 `synchronized`/`volatile` · 55 원자 변수 | [`../언어-특성/README.md`](../언어-특성/README.md) §9 — happens-before **모델** | 메모리 모델 자체는 거기. 여기는 **키워드의 문법과 "같은 모니터로 짝을 맞춘다"는 사용 규칙** |
| 49 병렬 스트림 · 56 가상 스레드 | [`../언어-특성/README.md`](../언어-특성/README.md) §4~8(JIT·GC) · [`foundations/process-thread/`](../../../process-thread/) | 런타임 내부와 OS 스레드 개념은 거기. 여기는 **API 호출 형태와 안 되는 경우** |
| 01~02 기본형·수치 · 53 `BigDecimal` | [`foundations/data-representation/`](../../../data-representation/) — 2의 보수·IEEE 754 | 표현 방식은 거기. 여기는 **Java 가 그 위에 얹은 규칙**(이항 승격·`Integer` 캐시·`BigDecimal` 스케일) |
| 25 예외 | [`ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) — 실패 모드 분류 | 운영 관점 분류는 거기. 여기는 **언어의 검사 예외 규칙과 전파 문법** |
| 09 상속 | [`foundations/oop-basics/`](../../../oop-basics/) — OOP 개념 | 개념은 거기. 여기는 **Java 의 디스패치 규칙**(필드는 숨고 메서드는 재정의되는 비대칭) |

## 뺀 것과 이유

**있는데 뺀 것**이다. 없어서 안 넣은 것이 아니다.

| 뺀 것 | 이유 |
|---|---|
| 모듈 시스템(JPMS) 전체 — `module-info.java`·서비스 바인딩 | 한 언어 주제라기보다 **빌드·배포 구조** 쪽이다. 문법 표면(34 모듈 import 선언)만 남겼다 |
| `Serializable` 직렬화 | 사실상 유지보수 모드이고 OpenJDK 스스로 대체를 예고한 영역이다. 새로 배워 쓸 기능이 아니라 **읽을 줄만 알면 되는 레거시** |
| FFM API(`java.lang.foreign`)·Vector API·Class-File API(24) | 일반 애플리케이션 코드에서 만나지 않는다. Vector API 는 아직 인큐베이터(25에서 10차) |
| 문자열 템플릿(JEP 430) | 21에서 프리뷰였다가 **23에서 철회**됐다. 지금 배울 문법이 아니다 |
| 구조적 동시성(JEP 505)·스코프 값 밖의 프리뷰들·Valhalla value class | 25 기준으로도 프리뷰다. 확정 문법만 다룬다(스코프 값은 25에서 확정됐으나 가상 스레드 주제에서 언급만) |
| GC 튜닝 플래그·JIT 컴파일 단계·클래스로더 위임 | [`../언어-특성/README.md`](../언어-특성/README.md) 의 영역. 문법·API 가 아니다 |
| JDBC·HTTP 클라이언트·`javax.crypto` 등 도메인 API | 표준 라이브러리이긴 하나 **그 도메인을 배우는 것**이지 Java 를 배우는 것이 아니다 |
| 빌더·정적 팩토리 등 GoF 패턴 | [`cs/engineering/design-patterns-gof/`](../../../../engineering/design-patterns-gof/) 에 있다. 관용구 칸은 **언어가 강제하는 것**(불변·`null`)만 남겼다 |
| 애너테이션 프로세싱(APT)·Lombok | 언어 밖 도구 층이다. 애너테이션 **선언**(16)까지만 |

## 버전 기준

**Java 21 (LTS, 2023-09)** 을 기준선으로 한다. 17과 25의 차이는 아래처럼 갈린다.

| 주제 | 확정 버전 | 17 기준이면 | 25 기준이면 |
|---|---|---|---|
| 04 `var` | 10 | 동일 | 동일 |
| 32 텍스트 블록 | 15 | 동일 | 동일 |
| 14 `record` | 16 | 동일 | 동일 |
| 22 `instanceof` 타입 패턴 | 16 | 동일 | 동일 |
| 15 `sealed` | 17 | 동일 | 동일 |
| 21 `switch` 식 | 14 | 동일 | 동일 |
| 23 `switch` 패턴 매칭 | **21** (JEP 441) | 17에는 **없다**(프리뷰) | 동일 + 원시 타입 패턴은 25에서도 프리뷰(JEP 507) |
| 24 `record` 패턴 | **21** (JEP 440) | 17에는 없다 | 동일 |
| 42 `SequencedCollection` | **21** (JEP 431) | 17에는 없다 | 동일 |
| 56 가상 스레드 | **21** (JEP 444) | 17에는 없다 | 25에서 고정(pinning) 문제가 24 JEP 491로 완화됨 — 동작이 달라진다 |
| 50 Stream Gatherers | **24** (JEP 485) | 없다 | 있다. 21 기준 학습에서는 "21에 없는 것"으로 표시 |
| 07 유연한 생성자 본문 | **25** (JEP 513) | 없다 | 있다 — `super()` 앞 문장 허용 |
| 34 모듈 import 선언 | **25** (JEP 511) | 없다 | 있다 |

**버전에 갈리는 주제 = 8개**(23·24·42·56·50·07·34 + 실행 시 동작이 갈리는 33/55의 `synchronized` 고정 동작).
21에 없는 것(50·07·34)은 **주제로는 남기되 "25 전용"을 이름에 달고 우선순위를 낮췄다**(C 또는 B).
실행 검증은 기본을 21.0.5로 하고, 25 전용 주제만 25.0.1로 돌린 뒤 **어느 JDK 에서 돌렸는지 3파일에 적는다**.
