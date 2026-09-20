# C# — 문법·API 주제 목록

> 1단계 리스트업이다. 아래 주제들의 3파일(질문·서머리·정답)은 **아직 없다**.
> 기준 소스: [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)
> 실행 검증: **불가** — 이 머신에 **`dotnet`·`mono`·`csc` 가 모두 없다**(2026-09-20 확인). 3파일의 코드 예시는 **「실행 검증 안 됨」으로 명시**하고 공식 문서로만 접지한다. 필요하면 .NET SDK 설치를 **제안**한다(임의 설치하지 않는다).
> 기준일 2026-09-20.

언어 선택의 축(“C# 은 기술이 아니라 생태계에서 갈린다 · 실행 모형이 JVM 과 동형이다”)은 [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md)에 있다.
이 목록은 그 논증이 아니라 **“그래서 어떻게 쓰나”**다 — 저기서 *`struct`·`ref struct` 가 JVM 에 없는 값 타입이라는 사실*을 읽었다면, 여기서는 *`struct` 를 언제 고르고 박싱을 어디서 잃는가*를 인출한다.

**C·C++ 와는 독립이다.** C# 은 관리 런타임 언어라 포인터·수동 해제·미정의 동작 축이 없다. 그래서 C 목록을 선행으로 걸지 않는다.
대신 **Java 와 대비가 값을 내는 자리**를 `↔Java` 로 표시했다 — 같은 진영(IL/바이트코드 → JIT → 추적 GC)인데 **기본값이 다른 곳**이 인출의 핵심이기 때문이다. Java 쪽 목록은 [`../../java/syntax/`](../../java/syntax/) 에 따로 있다(경로 참조만 한다).

## 이 언어에서 무엇을 자르는 축

```text
① 타입 체계      값 타입 vs 참조 타입 · 널 허용 · 제네릭 — "이 변수에 무엇이 들어 있나"
② 데이터 모델링   속성 · record · 패턴 매칭 — "데이터를 어떤 모양으로 선언하나"
③ 함수와 시퀀스   델리게이트 · 람다 · IEnumerable · yield · LINQ — 한 뿌리다
④ 자원과 실패     IDisposable · 예외 · 비동기 — "끝날 때 무엇이 보장되나"
⑤ 성능 도구       ref · Span<T> · struct — "GC 를 피해야 할 때 무엇을 쓰나"
```

③이 다른 언어 목록보다 두꺼운 것이 C# 의 특징이다. 델리게이트 → 람다 → 확장 메서드 → `IEnumerable` → `yield` → LINQ 가 **서로 다른 기능이 아니라 한 줄기**라서, 따로 외우면 안 되고 순서대로 쌓아야 인출된다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | 값 타입과 참조 타입 | 문법 | 변수에 값이 직접 들어가는지 참조가 들어가는지 그림으로 구분하고, 대입·인자 전달 후 원본이 바뀌는지 예측할 수 있다 `↔Java`(Java 에는 사용자 정의 값 타입이 없다) | — | [`variables-and-memory/`](../../../variables-and-memory/) — 값/참조 개념은 거기, 여기는 **C# 타입 체계의 이분** | A |
| 02 | `struct` 대 `class` 고르기 | 문법 | 크기·불변성·복사 비용을 기준으로 둘을 고르고, `readonly struct`(C# 7.2)·`record struct`(C# 10)가 무엇을 바꾸는지 설명할 수 있다 `↔Java` | 01 | [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md) — 값 타입이 JVM 대비 20년 앞섰다는 **논증**은 거기, 여기는 **선택 기준** | A |
| 03 | 박싱과 언박싱 | 문법 | 값 타입이 `object`·인터페이스로 올라갈 때 힙 할당이 생기는 자리를 짚고, 제네릭이 그것을 어떻게 없애는지 설명할 수 있다 `↔Java`(Java 의 오토박싱과 대비) | 01 | — | A |
| 04 | 변수 선언·`var`·타겟 타입 `new` | 문법 | `var` 가 동적 타입이 아님을 설명하고, `var`/명시 타입/타겟 타입 `new`(C# 9) 중 무엇을 쓸지 가독성 기준으로 고를 수 있다 | 01 | — | B |
| 05 | 기본 숫자 타입·`checked`/`unchecked`·`decimal` | 문법 | 정수 오버플로가 기본적으로 조용히 감싸는 것과 `checked` 가 예외를 던지는 것을 구분하고, 돈 계산에 `decimal` 을 고르는 근거를 댈 수 있다 | 01 | [`data-representation/`](../../../data-representation/) — 부동소수점 표현은 거기, 여기는 **C# 타입 선택** | A |
| 06 | 널 허용 참조 타입(C# 8) | 문법 | `string?` 과 `string` 의 차이가 **컴파일러 분석**이지 런타임 타입이 아님을 설명하고, 경고를 끄는 `!` 를 언제 쓸지 판단할 수 있다 `↔Java`(Optional·애너테이션과 대비) | 01 | — | A |
| 07 | 널 관련 연산자 `?.`·`??`·`??=` | 문법 | 널 조건 연산자의 단락 평가 결과 타입을 예측하고, 널 병합 대입·널 조건 대입(C# 14)을 쓸 수 있다 | 06 | — | A |
| 08 | 널 허용 값 타입 `Nullable<T>` | 문법 | `int?` 가 구조체이고 `HasValue`/`Value` 로 동작하는 것과, 참조 타입의 `?` 와 의미가 다른 것을 구분할 수 있다 | 01, 06 | — | B |
| 09 | 배열과 인덱스·범위 연산자(C# 8) | 문법 | `^1`·`1..^1` 로 끝 기준 인덱싱과 슬라이싱을 쓰고, 그것이 어떤 메서드 호출로 풀리는지 설명할 수 있다 | 01 | [`data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) — 배열 구조는 거기, 여기는 **C# 문법** | B |
| 10 | 컬렉션 선택 — `List`·`Dictionary`·`HashSet`·`Queue`/`Stack` | 표준 라이브러리 | 접근 패턴별로 컬렉션을 고르고, `Dictionary` 키에 필요한 것(`GetHashCode`/`Equals`)을 말할 수 있다 | 03 | [`data-structure/01`](../../../../data-structure/01-dynamic-array/)·[`03`](../../../../data-structure/03-stack/)·[`04`](../../../../data-structure/04-queue-deque/)·[`05`](../../../../data-structure/05-hashmap/) — 원리는 거기, 여기는 **BCL 선택 기준** | A |
| 11 | 컬렉션 초기화와 컬렉션 식(C# 12) | 문법 | 객체·컬렉션 초기화 구문과 `[1, 2, ..other]` 스프레드를 쓰고, 어떤 타입이 이것을 받을 수 있는지 안다 | 10 | — | B |
| 12 | 클래스·필드·생성자·`this`/`base` | 문법 | 생성자 연쇄와 초기화 순서를 설명하고, 기본 생성자(primary constructor, C# 12)가 무엇을 줄이는지 판단할 수 있다 | 01 | [`oop-basics/`](../../../oop-basics/) — 클래스 개념은 거기, 여기는 **C# 문법** | A |
| 13 | 속성(property)과 `init`·`required`·`field` | 문법 | 자동 구현 속성·계산 속성·`init`(C# 9)·`required`(C# 11)·`field` 키워드(C# 14)를 고르고, 속성이 메서드로 컴파일되는 결과를 설명할 수 있다 `↔Java`(getter/setter 관례와 대비) | 12 | [`oop-basics/`](../../../oop-basics/) §12 — 파이썬 property 는 거기, 여기는 **C# 의 1급 문법** | A |
| 14 | 인덱서 | 문법 | `this[int i]` 로 인덱싱 가능한 타입을 만들고, 언제 인덱서 대신 메서드가 나은지 판단할 수 있다 | 13 | — | C |
| 15 | 접근 한정자와 어셈블리 경계 | 문법 | `public`/`internal`/`protected`/`private protected` 를 어셈블리 기준으로 구분해 쓸 수 있다 `↔Java`(package-private·모듈과 대비) | 12 | — | B |
| 16 | 상속·`virtual`/`override`/`abstract`/`sealed`/`new` | 문법 | C# 이 **기본 비가상**임을 설명하고, `new` 로 숨기는 것과 `override` 로 재정의하는 것의 호출 결과 차이를 예측할 수 있다 `↔Java`(Java 는 기본 가상) | 12 | [`oop-basics/`](../../../oop-basics/) §14~18 — 상속·다형성 개념은 거기, 여기는 **C# 기본값** | A |
| 17 | 인터페이스·기본 구현 멤버·명시적 구현 | 문법 | 인터페이스를 설계하고, 기본 구현 멤버(C# 8)와 명시적 구현이 각각 무엇을 푸는지 말할 수 있다 `↔Java`(default 메서드와 대비) | 16 | — | A |
| 18 | `record` 와 값 동등성·`with` | 문법 | `record`(C# 9)·`record struct`(C# 10)가 자동 생성하는 것(동등성·`ToString`·해체)을 말하고, `with` 식의 비파괴 변경을 쓸 수 있다 `↔Java`(Java record 는 `with` 가 없다) | 13 | — | A |
| 19 | 동등성 규칙 — `Equals`/`GetHashCode`/`==` | 문법 | 참조 동등·값 동등·연산자 오버로드가 어긋날 때 생기는 버그를 설명하고, 셋을 일관되게 구현할 수 있다 | 18 | [`data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) — 해시 원리는 거기, 여기는 **계약 준수** | A |
| 20 | `enum` 과 `[Flags]` | 문법 | 열거형이 정수 위의 얇은 껍데기임을 설명하고, 비트 플래그 열거형과 `Enum` API 를 쓸 수 있다 | 05 | — | B |
| 21 | 패턴 매칭 — 타입·속성·관계·목록 패턴 | 문법 | `is` 패턴으로 타입 검사와 캐스트를 한 번에 하고, 속성·관계(C# 9)·목록 패턴(C# 11)을 조합해 조건을 선언적으로 쓸 수 있다 | 16 | — | A |
| 22 | `switch` 식과 `switch` 문 | 문법 | `switch` 식(C# 8)의 완전성 검사와 `switch` 문의 fallthrough 금지를 설명하고, 어느 쪽을 쓸지 고를 수 있다 | 21 | — | A |
| 23 | 튜플과 해체(deconstruction) | 문법 | 값 튜플로 여러 값을 반환·해체하고, 언제 `record`/클래스로 올려야 하는지 판단할 수 있다 | 18 | — | B |
| 24 | 제네릭과 타입 매개변수 | 문법 | 제네릭 타입·메서드를 정의하고, **C# 제네릭이 런타임까지 타입을 유지한다**는 점이 무엇을 가능하게 하는지 설명할 수 있다 `↔Java`(타입 소거와 대비 — 이 목록에서 Java 대비가 가장 크게 갈리는 자리) | 03 | — | A |
| 25 | 제네릭 제약 `where` 와 `default(T)` | 문법 | `class`/`struct`/`new()`/인터페이스 제약을 고르고, `default(T)` 가 타입마다 다른 값이 되는 것을 설명할 수 있다 | 24 | — | A |
| 26 | 공변·반변 (`out`/`in`) | 문법 | `IEnumerable<out T>` 가 왜 안전하고 `IList<T>` 는 왜 불변인지 설명하고, 인터페이스 설계에 적용할 수 있다 `↔Java`(와일드카드와 대비) | 24 | — | B |
| 27 | 델리게이트와 `Func`/`Action` | 문법 | 델리게이트가 **타입**임을 설명하고, 메서드 그룹 변환·멀티캐스트를 쓸 수 있다 `↔Java`(함수형 인터페이스와 대비) | 24 | — | A |
| 28 | 람다식과 클로저 캡처 | 문법 | 람다가 캡처한 변수의 수명이 늘어나는 것을 설명하고, 반복 변수 캡처 함정과 `static` 람다(C# 9)를 판단할 수 있다 | 27 | [`variables-and-memory/`](../../../variables-and-memory/) §9 — 람다 개념은 거기, 여기는 **캡처 의미론** | A |
| 29 | 이벤트와 `event` | 문법 | `event` 가 델리게이트 필드에 무엇을 제한하는지 말하고, 구독 해제 누락이 만드는 누수를 설명할 수 있다 | 27 | — | B |
| 30 | 확장 메서드와 확장 멤버(C# 14) | 문법 | 확장 메서드가 정적 메서드의 문법 설탕임을 설명하고, C# 14 의 확장 멤버가 넓힌 범위를 말할 수 있다 `↔Java`(대응물이 없다) | 27 | — | A |
| 31 | `IEnumerable<T>` 와 `foreach` | 표준 라이브러리 | `foreach` 가 어떤 패턴으로 풀리는지 설명하고, `IEnumerable`/`IEnumerator`/컬렉션의 역할을 구분할 수 있다 | 10, 24 | — | A |
| 32 | `yield return` 반복자와 지연 실행 | 문법 | `yield` 메서드가 상태 기계로 컴파일되는 결과를 설명하고, 호출 시점이 아니라 열거 시점에 실행되는 것을 예측할 수 있다 `↔Java`(Java 에는 없다 — Stream 으로 우회) | 31 | — | A |
| 33 | LINQ 메서드 구문과 지연 실행 | 표준 라이브러리 | `Where`/`Select`/`OrderBy` 를 잇고, 지연 실행과 `ToList`/`Count` 같은 즉시 실행의 경계를 판단할 수 있다 `↔Java`(Stream 과 대비) | 30, 32 | — | A |
| 34 | LINQ 쿼리 구문 | 문법 | 쿼리 구문이 메서드 구문으로 번역되는 규칙을 설명하고, 어느 쪽이 읽기 쉬운 자리를 고를 수 있다 | 33 | — | B |
| 35 | LINQ 그룹·조인·집계 | 표준 라이브러리 | `GroupBy`·`Join`·`Aggregate` 로 집계를 쓰고, 결과가 왜 여러 번 열거될 수 있는지 설명할 수 있다 | 33 | — | B |
| 36 | `IQueryable` 과 식 트리 맛보기 | 표준 라이브러리 | `IEnumerable` 과 `IQueryable` 의 갈림(메모리 실행 vs 번역)을 설명하고, ORM 에서 어느 지점에 실제 쿼리가 나가는지 판단할 수 있다 | 35 | — | C |
| 37 | `IDisposable` 과 `using` | 문법 | 결정적 해제가 GC 와 별개임을 설명하고, `using` 선언(C# 8)·`IAsyncDisposable`·Dispose 패턴을 쓸 수 있다 `↔Java`(try-with-resources 와 대비) | 12 | [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md) — GC 논증은 거기, 여기는 **결정적 해제 문법** | A |
| 38 | 예외 — `try`/`catch`/`finally`·필터 `when` | 문법 | 예외 필터가 스택을 되감기 전에 평가된다는 점을 설명하고, `throw;` 와 `throw ex;` 의 차이를 말할 수 있다 `↔Java`(**검사 예외가 없다**) | 37 | — | A |
| 39 | 예외 설계 — 무엇을 던지고 어디서 잡나 | 관용구 | 예외 타입 선택·예외를 흐름 제어로 쓰지 않는 기준·`TryParse` 류 패턴과의 경계를 정할 수 있다 | 38 | [`ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) — 실패 모드 분류는 거기, 여기는 **C# 예외 설계** | A |
| 40 | `async`/`await` 와 `Task` | 문법 | `await` 가 메서드를 어디서 끊고 이어 붙이는지 설명하고, `Task`/`Task<T>` 의 상태와 예외 전달을 말할 수 있다 `↔Java`(CompletableFuture·가상 스레드와 대비) | 38 | — | A |
| 41 | 비동기 함정 — `async void`·`.Result`·`ConfigureAwait` | 관용구 | 데드락이 생기는 경로를 그림으로 설명하고, 라이브러리 코드에서 `ConfigureAwait(false)` 를 쓰는 근거를 댈 수 있다 | 40 | — | A |
| 42 | `ValueTask`·`IAsyncEnumerable`·`await foreach` | 표준 라이브러리 | `ValueTask` 가 할당을 줄이는 대신 갖는 제약을 말하고, 비동기 스트림(C# 8)을 쓸 수 있다 | 32, 40 | — | B |
| 43 | `CancellationToken` 관용구 | 관용구 | 취소 토큰을 호출 사슬로 전달하고, 협조적 취소가 “강제 중단”이 아님을 설명할 수 있다 | 40 | [`ops-patterns/deadline-propagation/`](../../../../ops-patterns/deadline-propagation/) — 데드라인 전파 패턴은 거기, 여기는 **C# API 사용** | B |
| 44 | `ref`/`out`/`in` 매개변수 | 문법 | 세 한정자의 방향과 대입 의무를 구분하고, `out` 변수 선언(C# 7)·`in` 의 복사 회피를 쓸 수 있다 | 01 | — | B |
| 45 | `ref` 지역·`ref` 반환·`ref struct` | 문법 | 참조를 값처럼 들고 다닐 때의 수명 제약을 설명하고, `ref struct` 가 힙으로 탈출할 수 없다는 규칙의 귀결을 말할 수 있다 | 44 | — | B |
| 46 | `Span<T>`·`Memory<T>`·`stackalloc` | 표준 라이브러리 | 할당 없이 부분 배열·문자열을 다루고, `Span<T>` 를 필드·async 메서드에 둘 수 없는 이유를 설명할 수 있다 `↔Java`(대응물이 미리보기 단계) | 45 | — | B |
| 47 | 문자열 — 불변성·보간·`StringBuilder` | 표준 라이브러리 | 보간 문자열이 무엇으로 컴파일되는지 설명하고, 반복 연결에서 `StringBuilder` 를 고르는 기준을 댈 수 있다 | 01 | — | A |
| 48 | 문자열 서식·`ToString`·문화권 | 표준 라이브러리 | 숫자·날짜 서식 지정자를 쓰고, `CultureInfo` 때문에 파싱·출력이 환경마다 달라지는 자리를 짚을 수 있다 | 47 | — | B |
| 49 | 연산자 오버로딩과 변환 연산자 | 문법 | `operator`·`implicit`/`explicit` 변환을 정의하고, 암묵 변환을 언제 금지할지 판단할 수 있다 `↔Java`(Java 에는 없다) | 19 | [`oop-basics/`](../../../oop-basics/) §19~20 — 개념은 거기, 여기는 **C# 규칙** | C |
| 50 | 정적 멤버·정적 클래스·`static using` | 문법 | 정적 생성자의 실행 시점을 설명하고, 정적 상태가 테스트·동시성에서 만드는 문제를 판단할 수 있다 | 12 | — | B |
| 51 | 네임스페이스·파일 범위 선언·`global using` | 문법 | 파일 범위 네임스페이스(C# 10)·`global using`·`using` 별칭을 쓰고, 이름 충돌을 해소할 수 있다 | — | — | B |
| 52 | 최상위 문과 진입점 | 문법 | 최상위 문(C# 9)이 무엇으로 생성되는지 설명하고, `Main` 시그니처 선택지(`async Task<int>` 등)를 말할 수 있다 | 40 | — | C |
| 53 | 특성(attribute) 정의와 사용 | 문법 | 특성이 메타데이터로 박혀 런타임에 읽히는 구조를 설명하고, 커스텀 특성을 정의·소비할 수 있다 | 24 | — | B |
| 54 | 리플렉션 맛보기 | 표준 라이브러리 | `Type`·`GetMethod`·`Activator` 로 타입을 런타임에 다루고, 그 비용과 **Native AOT 에서 막히는 지점**을 판단할 수 있다 `↔Java` | 53 | [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md) — AOT 제약 **논증**은 거기, 여기는 **리플렉션 API 사용** | B |
| 55 | 파일·스트림 입출력 기본 | 표준 라이브러리 | `File`·`Stream`·`StreamReader` 로 읽고 쓰며, 동기/비동기 API 와 `using` 을 함께 쓸 수 있다 | 37, 40 | — | B |
| 56 | 불변성 도구 정리 | 관용구 | `readonly`·`init`·`record`·`ImmutableArray` 를 놓고 “어디까지 불변으로 만들 것인가”를 층별로 고를 수 있다 | 13, 18 | — | B |

**주제 수 56** — 문법 41 · 표준 라이브러리 11 · 관용구 4 / 우선 A 29 · B 23 · C 4.

`↔Java` 는 **Java 와 대비할 때 값이 나는 자리**다. Java 쪽 목록은 [`../../java/syntax/`](../../java/syntax/) 에 있다(다른 워커가 작성 중 — 이 문서는 경로만 가리킨다).
가장 크게 갈리는 셋: **24 제네릭**(런타임 유지 vs 타입 소거) · **02 값 타입**(`struct` vs JEP 401 미리보기) · **38 예외**(검사 예외 없음).

## 기존 주제와 겹치는 것

| 여기 주제 | 기존 주제 | 어떻게 좁혔나 |
|---|---|---|
| 01 값/참조 타입, 28 클로저 | [`foundations/variables-and-memory/`](../../../variables-and-memory/) | 값/참조·얕은 복사·람다 개념은 **파이썬으로 설명한 것**이다. 여기는 **C# 의 이분(값 타입이 언어에 있다)과 캡처 의미론** |
| 05 숫자 타입 | [`foundations/data-representation/`](../../../data-representation/) | 2진·부동소수점 표현은 거기. 여기는 **`decimal`·`checked` 등 C# 타입 선택** |
| 10 컬렉션 | [`data-structure/01`](../../../../data-structure/01-dynamic-array/)·[`03`](../../../../data-structure/03-stack/)·[`04`](../../../../data-structure/04-queue-deque/)·[`05`](../../../../data-structure/05-hashmap/) | 자료구조 원리·복잡도는 거기. 여기는 **BCL 타입 선택과 키 요구사항(`GetHashCode`/`Equals`)** |
| 12·13·16·17·49 OOP | [`foundations/oop-basics/`](../../../oop-basics/) | 캡슐화·상속·다형성·property·연산자 오버로딩 **개념**은 거기(파이썬). 여기는 **C# 이 기본값을 어디서 뒤집었나** — 기본 비가상, property 가 1급 문법, 명시적 인터페이스 구현 |
| 19 동등성 | [`data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | 해시 테이블 원리는 거기. 여기는 **`Equals`/`GetHashCode` 계약을 어겼을 때 딕셔너리가 조용히 틀리는 자리** |
| 39 예외 설계 | [`ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) | 실패 모드 분류(조용한 실패 등)는 거기. 여기는 **C# 에서 어떤 예외를 던지고 어디서 잡나** |
| 43 취소 토큰 | [`ops-patterns/deadline-propagation/`](../../../../ops-patterns/deadline-propagation/) | 데드라인 전파 패턴은 거기. 여기는 **`CancellationToken` API 관용구** |
| 02·37·54 값 타입·GC·AOT | [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md) | *값 타입이 JVM 보다 20년 앞섰다 · AOT 의 대가가 문서에 박혀 있다*는 **논증**은 그 노트. 여기는 **`struct` 를 언제 고르나 · `Dispose` 를 어떻게 구현하나 · 리플렉션을 어떻게 쓰나** |

## 뺀 것과 이유

- **런타임 내부(CLR·GC 세대·JIT 계층·Native AOT 의 원리)** — [`../../c-cpp-csharp.md`](../../c-cpp-csharp.md) 와 [`foundations/memory-management/`](../../../memory-management/) 의 축이다. 이 목록은 **언어와 BCL** 만 본다.
- **`unsafe`·포인터·`fixed`·P/Invoke** — C# 의 기본 축(관리 런타임)을 벗어나고, 포인터 문법은 [`../../c/syntax/`](../../c/syntax/README.md) 와 겹친다. 상호운용이 필요해지면 2단계에서 별도 묶음으로 붙인다.
- **동시성(`lock`·`Interlocked`·`Parallel`·`Channel`)** — 비동기(40~43)와 축이 달라 독립 묶음이 맞다. 개념은 [`foundations/process-thread/`](../../../process-thread/) 에 있다.
- **프레임워크(ASP.NET Core·EF Core·DI 컨테이너)** — 언어가 아니라 플랫폼이다. 36(`IQueryable`)만 “언어 쪽 접점”으로 남겼다.
- **소스 생성기·Roslyn 분석기 작성** — 53·54의 한 단계 위 도구 축이다. 필요해지면 자매 주제로 붙인다.
- **`dynamic`·COM 상호운용** — 현대 C# 코드에서 인출 빈도가 낮다.

## 버전 기준

**C# 14 / .NET 10(2025-11 출시) 기준**으로 쓰고, **각 기능이 어느 버전부터인지 주제 안에 반드시 적는다.**
주의할 것이 하나 있다 — **ECMA-334 7판(2023-12)은 C# 7 까지만 규범적으로 덮는다.** 그 이후 기능(C# 8~14)의 1차 기준은 **Microsoft Learn 언어 레퍼런스와 `dotnet/csharplang` 의 기능 명세**다. 3파일에서는 이 둘을 구분해 인용한다.

| 표기 | 해당 주제 |
|---|---|
| **C# 6부터** | 47 문자열 보간 · 38 예외 필터 `when` |
| **C# 7 계열부터** | 21 패턴 매칭 시작 · 23 튜플·해체 · 44 `out` 변수 선언·`in` · 45 `ref` 지역/반환 · 02 `readonly struct`·`ref struct`(7.2) |
| **C# 8부터** | 06 널 허용 참조 타입 · 09 인덱스·범위 · 17 기본 인터페이스 멤버 · 22 `switch` 식 · 37 `using` 선언 · 42 비동기 스트림 |
| **C# 9부터** | 18 `record` · 13 `init` · 21 관계·논리 패턴 · 04 타겟 타입 `new` · 52 최상위 문 · 28 `static` 람다 |
| **C# 10부터** | 18 `record struct` · 51 파일 범위 네임스페이스·`global using` · 47 보간 문자열 핸들러 |
| **C# 11부터** | 13 `required` 멤버 · 21 목록 패턴 · 47 원시 문자열 리터럴·UTF-8 리터럴 · 25 `static abstract` 인터페이스 멤버(제네릭 수학) |
| **C# 12부터** | 11 컬렉션 식 · 12 기본 생성자 · 51 모든 타입 별칭 |
| **C# 13부터** | 10 `params` 컬렉션 · 45 `ref struct` 의 인터페이스 구현·제네릭 인자 허용 |
| **C# 14부터** | 30 확장 멤버 · 13 `field` 키워드 · 07 널 조건 대입 · 46 `Span<T>` 암묵 변환 확대 |

**이 머신에서는 컴파일해 확인할 수 없다.** 3파일을 쓸 때 각 예시에 「실행 검증 안 됨 — 기준 소스로만 접지」를 명시하고, 버전 표기는 위 공식 버전 이력 문서로 대조한다.
