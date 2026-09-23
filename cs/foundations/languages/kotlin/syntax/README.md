# Kotlin — 문법·API 주제 목록

> 진행 — **5 / 58**(01 · 02 · 03 · 04 · 05). 「주제」 칸의 링크가 각 주제의 3파일 폴더다.
> 기준 소스: [kotlinlang.org 언어 레퍼런스](https://kotlinlang.org/docs/home.html) · [kotlin-stdlib API](https://kotlinlang.org/api/core/kotlin-stdlib/) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)(기능이 Stable 이 된 버전 확인) · [릴리스 목록](https://kotlinlang.org/docs/releases.html)
> 실행 검증: **가능**(2026-09-23 에 `sdk install kotlin` 으로 갖췄다). **kotlinc 2.4.20 · JRE 21.0.5.**
> ★★ **이 갈래의 근거는 `javap` 다** — Kotlin 은 JVM 바이트코드로 컴파일되므로 「무엇으로 컴파일되나」를 지어낼 수 없다.
> `?` 없는 파라미터에 컴파일러가 **`Intrinsics.checkNotNullParameter` 를 심는다**는 것이 그렇게 드러났다 —
> null 안전은 타입 시스템만이 아니라 **런타임 코드**다.
> ⚠️ **`kotlinc` 의 기본 `-jvm-target` 은 1.8 이다**(JRE 21 에서도 `major version: 52`).
> 그래서 문자열 템플릿이 **`invokedynamic` 이 아니라 `StringBuilder`** 로 나온다 — **플래그를 밝히지 않은 바이트코드 주장은 반쪽이다.**
> 기준일 2026-09-20. 최신 안정 버전 **Kotlin 2.4.20**(2026-09-07, 언어 릴리스는 2.4.0 / 2026-06-03).

## 이 언어에서 무엇을 자르는 축

Kotlin 공식 레퍼런스는 **타입 → 클래스·객체 → 함수·람다 → null 안전 → 컬렉션 → 코루틴** 순의 평평한 페이지 묶음이다. 이 목록은 그 페이지 경계를 그대로 쓰지 않고, **「Java 의 기본값을 어디서 뒤집었나」** 를 뼈대로 다시 세웠다 — 그래야 JVM 을 이미 아는 사람에게 인출할 것이 생긴다.

축은 넷이다. ① **기본값이 뒤집힌 것** — null 불가가 기본, `final` 이 기본, 읽기 전용 컬렉션이 기본, 검사 예외 없음. ② **Java 에 없는 선언** — `data`/`sealed`/`value`/`object`/위임/확장/context parameter. ③ **식(expression)이 늘어난 것** — `if`·`when`·`try` 가 값을 낸다. ④ **표준 라이브러리가 흡수한 것** — 컬렉션 연산·`Sequence`·scope function·`Result`·`Duration`·코루틴.

코루틴은 `suspend` 라는 **언어 기능**과 `kotlinx.coroutines` 라는 **stdlib 밖 라이브러리**로 나뉜다. 둘 다 넣되 어느 쪽 출처인지 3파일에 표기한다. 멀티플랫폼·Native·JS/Wasm 은 뺐다(아래 「뺀 것」).

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | [`val`/`var` 와 기본 타입 — 암묵 수치 변환이 없다](01-val-var-and-basic-types/) | 문법 | `Int` 를 `Long` 에 그냥 못 넣는 이유와 `val` 이 막는 것·못 막는 것을 설명할 수 있다 | — | [`../언어-특성/README.md`](../언어-특성/README.md) §5 | A |
| 02 | [문자열 템플릿·raw string·멀티달러 보간 (2.2+)](02-string-templates-and-raw-strings/) | 문법 | `$` 를 문자로 넣어야 할 때 어느 형태를 쓸지 판단할 수 있다 | 01 | — | A |
| 03 | [null 안전 타입 — `?`·`?.`·`?:`·`!!`](03-null-safe-types/) | 문법 | 타입 시스템이 막아 주는 경계와 `!!` 가 그 경계를 버리는 지점을 설명할 수 있다 | 01 | [`../언어-특성/README.md`](../언어-특성/README.md) §2 | A |
| 04 | [스마트 캐스트와 그것이 깨지는 자리](04-smart-casts/) | 문법 | `var` 프로퍼티·다른 모듈 프로퍼티에서 스마트 캐스트가 안 되는 이유를 예측할 수 있다 | 03 | — | A |
| 05 | [플랫폼 타입 — Java 경계에서 null 보증이 끝나는 곳](05-platform-types/) | 문법 | Java 라이브러리에서 온 값이 왜 런타임에야 터지는지, 무엇으로 막는지 판단할 수 있다 | 03 | [`../언어-특성/README.md`](../언어-특성/README.md) §2·§9 | A |
| 06 | [`when` 식 — 주체 있는/없는 형태·guard 조건 (2.2+)](06-when-expression/) | 문법 | `when` 이 식일 때 완결성이 요구되는 조건을 설명할 수 있다 | 01 | — | A |
| 07 | [반복문·`range`·progression·비지역 `break`/`continue` (2.2+)](07-loops-ranges-and-labels/) | 문법 | `until`/`..<`/`downTo`/`step` 이 만드는 범위를 예측하고 인라인 람다 안에서 루프를 빠져나올 수 있다 | 01 | — | A |
| 08 | [함수 선언 — 기본 인자·이름 붙인 인자·단일식 함수](08-function-declaration-default-and-named-args/) | 문법 | 기본 인자가 오버로딩을 어떻게 대체하고 Java 에서 볼 때 무엇이 사라지는지 판단할 수 있다 | 01 | — | A |
| 09 | [가변 인자·spread 연산자·로컬 함수](09-varargs-spread-local-and-infix-functions/) | 문법 | `vararg` 에 배열을 넘길 때 `*` 가 필요한 이유를 설명할 수 있다 | 08 | — | B |
| 10 | 람다와 고차 함수 — `it`·마지막 인자 람다·클로저 | 문법 | 람다가 바깥 `var` 를 고쳐 쓸 수 있는 것이 Java 와 어떻게 다른지 설명할 수 있다 | 08 | — | A |
| 11 | 인라인 함수 — `noinline`/`crossinline`·비지역 반환 | 문법 | 인라인이 없앤 비용과 그 대가로 생기는 제약을 판단할 수 있다 | 10 | — | A |
| 12 | `reified` 타입 파라미터 — 소거를 뚫는 방법 | 문법 | 왜 `inline` 없이는 `reified` 가 불가능한지 소거로 설명할 수 있다 | 11 | — | B |
| 13 | 확장 함수·확장 프로퍼티 — 정적 디스패치라는 천장 | 문법 | 확장 함수가 오버라이드되지 않는 이유와 멤버와 충돌할 때 누가 이기는지 예측할 수 있다 | 08 | [`../언어-특성/README.md`](../언어-특성/README.md) §7 | A |
| 14 | scope function 5종 — `let`/`run`/`with`/`apply`/`also` | 문법 | 수신자 형태(`this`/`it`)와 반환값(수신자/람다 결과)으로 다섯을 구분해 고를 수 있다 | 10, 13 | — | A |
| 15 | 클래스 선언 — 주 생성자·부 생성자·`init` 블록 순서 | 문법 | 프로퍼티 초기화와 `init` 이 어느 순서로 도는지 예측할 수 있다 | 01 | — | A |
| 16 | 프로퍼티 — backing field·커스텀 접근자·`lateinit`·`const` | 문법 | `field` 키워드가 필요한 자리와 `lateinit` 이 쓸 수 없는 타입을 판단할 수 있다 | 15 | — | A |
| 17 | 위임 프로퍼티 — `by lazy`·`observable`·`Map` 위임 | 문법 | `by` 가 어떤 연산자 규약(`getValue`/`setValue`)으로 풀리는지 설명할 수 있다 | 16 | — | B |
| 18 | 가시성 수식어 — `internal` 이 Java 에 없는 이유 | 문법 | 모듈 경계가 무엇으로 정의되고 Java 에서 보면 어떻게 보이는지 설명할 수 있다 | 15 | — | B |
| 19 | 상속 — `open`/`final` 기본값 뒤집기·`override` 강제 | 문법 | 상속을 열려면 무엇을 명시해야 하는지, 그 기본값이 막는 실패를 설명할 수 있다 | 15 | [`../언어-특성/README.md`](../언어-특성/README.md) §11 | A |
| 20 | 인터페이스 — 기본 구현·프로퍼티 선언·충돌 해소(`super<T>`) | 문법 | 같은 시그니처를 둘에서 상속했을 때 요구되는 형태를 쓸 수 있다 | 19 | — | A |
| 21 | 클래스 위임 (`by`) — 상속 대신 합성 | 문법 | 위임이 오버라이드한 메서드를 위임 대상이 못 보는 함정을 예측할 수 있다 | 20 | — | B |
| 22 | `data class` — 무엇이 생성되고 무엇이 안 되나 | 문법 | `copy`/`equals`/`componentN` 이 **주 생성자 프로퍼티만** 본다는 결과를 예측할 수 있다 | 15 | [`../언어-특성/README.md`](../언어-특성/README.md) §4 | A |
| 23 | `sealed class`/`sealed interface` 와 `when` 완결성 | 문법 | 하위 타입을 늘렸을 때 컴파일이 깨지는 자리와 깨지지 **않는** 자리를 판단할 수 있다 | 06, 20, 22 | [`../언어-특성/README.md`](../언어-특성/README.md) §3 | A |
| 24 | `enum class` 와 `sealed` 선택 기준 | 문법 | 상태에 데이터가 붙는 순간 enum 이 부족해지는 지점을 판단할 수 있다 | 23 | — | A |
| 25 | `object` 선언·`companion object`·`object` 식 | 문법 | Kotlin 에 `static` 이 없는데 정적 멤버가 어떻게 만들어지는지 설명할 수 있다 | 15 | — | A |
| 26 | `value class`(인라인 클래스) — 언제 박싱되나 | 문법 | 래핑 비용이 사라지는 경우와 다시 살아나는 경우(제네릭·nullable·인터페이스)를 예측할 수 있다 | 22 | [`../언어-특성/README.md`](../언어-특성/README.md) §4 | A |
| 27 | 중첩 클래스와 `inner` — 기본값이 뒤집힌 또 한 곳 | 문법 | `inner` 를 안 붙이면 바깥 인스턴스를 못 잡는 이유와 그 기본값의 값어치를 설명할 수 있다 | 15 | — | B |
| 28 | 제네릭 — 선언 지점 변성 `in`/`out`·star projection·`where` | 문법 | Java 와일드카드를 선언 지점으로 옮기면 무엇이 줄어드는지 설명할 수 있다 | 20 | — | A |
| 29 | 타입 별칭·중첩 타입 별칭 (2.2+) | 문법 | 별칭이 새 타입을 만들지 **않는다**는 결과(타입 안전성 없음)를 예측할 수 있다 | 26 | — | C |
| 30 | 구조 분해 선언 — `componentN` 과 그 한계 | 문법 | 위치 기반 분해가 왜 위험한지(필드 순서 변경) 판단할 수 있다 | 22 | — | B |
| 31 | 연산자 오버로딩·중위 함수·`invoke` 규약 | 문법 | 어떤 함수 이름이 어떤 기호로 풀리는지, 언제 쓰면 안 되는지 판단할 수 있다 | 13 | — | B |
| 32 | 동등성 — `==`/`===`·`equals` 규약·`data class` 와의 관계 | 문법 | Kotlin `==` 가 Java `equals` 인 것과 `null` 안전 처리까지 설명할 수 있다 | 22 | [`../../../../data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | A |
| 33 | 타입 검사·캐스트 — `is`/`as`/`as?` | 문법 | 실패 시 예외인 캐스트와 `null` 인 캐스트를 상황에 맞게 고를 수 있다 | 04 | — | A |
| 34 | 예외 — 검사 예외 없음·`Nothing` 타입·`try` 가 식이라는 것 | 문법 | 검사 예외 폐지가 무엇을 규율로 떠넘겼는지, `Nothing` 이 타입 추론에서 하는 일을 설명할 수 있다 | 06 | [`../언어-특성/README.md`](../언어-특성/README.md) §8 | A |
| 35 | 애너테이션과 use-site target (`@field:`·`@get:`·`@param:`) | 문법 | 애너테이션이 필드·게터·파라미터 중 어디에 붙는지 예측할 수 있다(프레임워크 오동작의 단골) | 16 | — | B |
| 36 | 함수 타입·`fun interface`·SAM 변환 | 문법 | Java 인터페이스에 람다를 넘길 때와 Kotlin 인터페이스일 때가 왜 다른지 판단할 수 있다 | 10 | — | A |
| 37 | 리시버 지정 람다와 type-safe builder (DSL) | 문법 | `A.() -> Unit` 이 무엇을 바꾸는지, 중첩 DSL 에서 수신자가 헷갈리는 이유를 설명할 수 있다 | 14, 36 | — | B |
| 38 | context parameters — 2.2 실험 → **2.4.0 Stable** | 문법 | 암묵 인자를 타입으로 넘기는 형태와 예전 context receivers 와의 차이를 설명할 수 있다 | 37 | — | C |
| 39 | Java 상호운용 애너테이션 — `@JvmStatic`/`@JvmOverloads`/`@JvmName`/`@JvmField`/`@Throws` | 문법 | Java 에서 쓸 API 를 낼 때 무엇을 붙여야 하는지 판단할 수 있다 | 25, 34 | [`../언어-특성/README.md`](../언어-특성/README.md) §9 · [`../../../../../history/spring/kotlin-and-spring.md`](../../../../../history/spring/kotlin-and-spring.md) | B |
| 40 | 컬렉션 — 읽기 전용 인터페이스와 실제 런타임 타입 | 표준 API | `List` 가 불변이 **아니라** 읽기 전용 뷰라는 것과 그 구멍을 예측할 수 있다 | 01 | [`../언어-특성/README.md`](../언어-특성/README.md) §5 · [`../../../../data-structure/`](../../../../data-structure/) | A |
| 41 | 컬렉션 생성 — `listOf`/`mutableListOf`/`buildList`/`toList` | 표준 API | 만드는 시점에 가변성을 정하는 형태를 고르고 복사가 일어나는 자리를 판단할 수 있다 | 40 | — | A |
| 42 | 변환 연산 — `map`/`flatMap`/`associate`/`zip` | 표준 API | 컬렉션을 다른 모양으로 바꾸는 연산을 타입으로 골라낼 수 있다 | 41 | — | A |
| 43 | 필터·검색 — `filter`/`find`/`first`/`any`/`all`/`none` | 표준 API | 빈 컬렉션에서 각각이 무엇을 반환하거나 던지는지 예측할 수 있다 | 41 | — | A |
| 44 | 집계·그룹핑 — `groupBy`/`partition`/`fold`/`reduce`/`sumOf` | 표준 API | `fold` 와 `reduce` 가 빈 입력에서 갈리는 지점을 설명할 수 있다 | 42 | — | A |
| 45 | 정렬·부분 연산 — `sortedBy`/`take`/`drop`/`chunked`/`windowed` | 표준 API | `sort*` 가 제자리인지 새 리스트인지 이름으로 구분해 고를 수 있다 | 41 | [`../../../../algorithm/09-sliding-window/`](../../../../algorithm/09-sliding-window/) | A |
| 46 | `Map` 조작 — `getOrPut`/`getOrElse`/`mapValues`/`filterKeys` | 표준 API | `null` 값과 "키 없음"이 겹칠 때 어느 함수가 맞는지 판단할 수 있다 | 41 | [`../../../../data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | A |
| 47 | `Sequence` — 지연 평가, 언제 `List` 보다 싼가 | 표준 API | 중간 컬렉션이 몇 개 생기는지 세고 `Sequence` 전환이 손해인 경우를 판단할 수 있다 | 42 | — | A |
| 48 | 문자열 API — `split`/`trim*`/`pad*`/`Regex` | 표준 API | Java `String` API 와 갈리는 지점(확장 함수로 들어온 것들)을 설명할 수 있다 | 02 | [`../../../../algorithm/25-string-matching/`](../../../../algorithm/25-string-matching/) | B |
| 49 | `Result` 와 `runCatching` — 예외를 값으로 | 표준 API | 왜 `Result` 를 반환 타입으로 두는 것이 제한되는지 설명할 수 있다 | 34 | — | B |
| 50 | `kotlin.time` — `Duration`·시간 측정 | 표준 API | 단위가 타입에 들어간 `Duration` 이 막는 실수를 설명할 수 있다 | 01 | — | C |
| 51 | 계약 함수 — `require`/`check`/`error`/`TODO` | 표준 API | 어느 것이 어떤 예외를 던지고 어디에 써야 하는지(인자 검증 vs 상태 검증) 판단할 수 있다 | 34 | — | A |
| 52 | 코루틴 기초 — `suspend`·`CoroutineScope`·`launch`/`async`/`await` | 표준 API | `suspend` 가 스레드가 아니라 컴파일러 변환이라는 것과 호출 규칙을 설명할 수 있다 | 10, 34 | [`../언어-특성/README.md`](../언어-특성/README.md) §6 · [`../../../process-thread/`](../../../process-thread/) | A |
| 53 | 구조적 동시성 — `Job`·취소 전파·예외 전파·`supervisorScope` | 표준 API | 자식 하나가 실패했을 때 형제와 부모가 어떻게 되는지 예측할 수 있다 | 52 | [`../../../../ops-patterns/19-graceful-shutdown/`](../../../../ops-patterns/19-graceful-shutdown/) | A |
| 54 | `CoroutineContext` 와 디스패처·`withContext` | 표준 API | 블로킹 호출을 어느 디스패처로 옮겨야 하는지 판단할 수 있다 | 52 | — | A |
| 55 | `Flow` — 콜드 스트림·연산자·`collect` | 표준 API | `Flow` 가 왜 collect 전에는 아무 일도 안 하는지, 스트림과 무엇이 다른지 설명할 수 있다 | 53 | — | B |
| 56 | `Channel`·`Mutex` — 공유 가변 상태 다루기 | 표준 API | 코루틴에서 `synchronized` 를 쓰면 안 되는 이유를 설명할 수 있다 | 54 | [`../언어-특성/README.md`](../언어-특성/README.md) §6 | B |
| 57 | Java 코드를 Kotlin 답게 — 식으로서의 `if`/`when`·엘비스 조기 반환 | 관용구 | 같은 로직을 Java 스타일로 쓴 것과 Kotlin 관용구로 쓴 것의 차이를 판단할 수 있다 | 06, 34 | [`../언어-특성/README.md`](../언어-특성/README.md) | A |
| 58 | null 처리 관용구 — `?.let`·`requireNotNull`·엘비스 + `return` | 관용구 | 어디서 막고 어디서 통과시킬지 계층별로 판단할 수 있다 | 03, 51 | — | A |

**58주제** (문법 39 · 표준 API 17 · 관용구 2 / 우선 A 40 · B 15 · C 3)

- **분류** — `문법` / `표준 API` / `관용구` 중 하나
- **무엇을 인출하게 되나** — 한 줄. 「~를 안다」가 아니라 **「~를 설명·예측·판단할 수 있다」**
- **선행** — 먼저 봐야 하는 주제 번호(없으면 `—`). 모든 선행은 자기보다 작은 번호라 순환이 없다
- **기존 주제** — `cs/**` 나 `history/**` 에 이미 있으면 그 경로
- **우선** — `A`(핵심·먼저) / `B`(중요) / `C`(나중에)

## Java 와 짝으로 볼 때 값이 나오는 주제

이 목록의 절반은 **혼자 읽으면 절반만 보인다.** Java 쪽 주제 번호는 [`../../java/syntax/README.md`](../../java/syntax/README.md) 기준이다.

| Kotlin | Java 대응 | 대비가 내는 값 |
|---|---|---|
| 03 null 안전 타입 · 05 플랫폼 타입 | 60 `null` 다루기·38 `Optional` | Java 는 **런타임 객체**(`Optional`)로, Kotlin 은 **타입**으로 푼다. 그래서 Kotlin 은 경계(Java 상호운용)에서 정확히 뚫린다 |
| 19 `open`/`final` 기본값 | 09 상속과 오버라이딩 | 같은 JVM 디스패치 위에서 **기본값만 뒤집었다** — 무엇이 줄고 무엇이 불편해지는지 |
| 22 `data class` · 26 `value class` | 14 `record` | 둘 다 "값을 값으로". record 는 **불변을 강제**하고 data class 는 **`var` 를 허용한다** — 방어선의 위치가 다르다 |
| 23 `sealed` + `when` 완결성 | 15 `sealed` · 23 `switch` 패턴 매칭 | Java 는 21에서야 같은 자리에 도착했다. **Kotlin 이 먼저 한 것을 Java 가 어떻게 따라왔나** |
| 40 읽기 전용 컬렉션 | 40 `List.of`·불변 팩토리 | "읽기 전용 **뷰**"(Kotlin)와 "진짜 불변 **객체**"(Java)의 차이 — 런타임 클래스를 보면 갈린다 |
| 34 검사 예외 없음 | 25 checked/unchecked 예외 | Kotlin 이 **없앤 것**이 Java 에서 무엇을 하고 있었는지 |
| 13 확장 함수 | 11 `default` 메서드 | 둘 다 "남의 타입에 메서드 추가". 하나는 **정적 디스패치**, 하나는 **가상 디스패치** |
| 14 scope function | 59~60 관용구 | Java 에 대응이 **없다**. 그래서 Kotlin 코드가 Java 개발자에게 낯설어지는 첫 지점 |
| 47 `Sequence` | 44~46 `Stream` | 같은 지연 평가를 **다른 타입 체계**로 — Kotlin 은 컬렉션 연산이 기본 즉시 평가라 전환이 명시적이다 |
| 52~56 코루틴 | 54 `ExecutorService` · 56 가상 스레드 | **같은 문제(블로킹을 싸게)를 언어 변환으로 푼 쪽과 런타임으로 푼 쪽.** 21 가상 스레드가 나온 뒤 이 대비가 가장 값이 크다 |
| 28 선언 지점 변성 | 18 와일드카드 PECS | 같은 변성을 **쓰는 쪽**(Java)과 **선언하는 쪽**(Kotlin)에서 적는다 |
| 01 암묵 변환 없음 | 02 이항 수치 승격 | Java 가 자동으로 해 주는 것을 Kotlin 은 거부한다 — 어느 쪽이 어떤 버그를 막나 |

## 기존 주제와 겹치는 것

| 겹치는 주제 | 기존에 있는 것 | 새 주제를 어떻게 좁혔나 |
|---|---|---|
| 03 null 안전 · 05 플랫폼 타입 | [`../언어-특성/README.md`](../언어-특성/README.md) §2 — **"컴파일러가 무엇을 거부하게 만들었나"와 그 방어선이 끝나는 경계** | 그 노트는 *왜 이 언어를 고르나*를 답한다. 여기는 **문법 자체** — `?.`·`?:`·`!!` 의 정확한 의미, 스마트 캐스트가 안 되는 조건 |
| 23 `sealed`+`when` | [`../언어-특성/README.md`](../언어-특성/README.md) §3 | 거기는 "상태를 늘리면 컴파일이 깨진다"는 **설계 논지**. 여기는 **어떤 조건에서 완결성이 요구되고 어떤 조건에서 조용히 통과하는가** |
| 22 `data class` · 26 `value class` | [`../언어-특성/README.md`](../언어-특성/README.md) §4 | 거기는 "값을 값으로"라는 논지와 실측. 여기는 **생성되는 멤버 목록과 박싱이 살아나는 구체 조건** |
| 40 읽기 전용 컬렉션 | [`../언어-특성/README.md`](../언어-특성/README.md) §5 — 런타임 클래스 실측표 | 실측표는 거기(재측정 안 한다). 여기는 **연산 API 를 고르는 법** |
| 52~56 코루틴 | [`../언어-특성/README.md`](../언어-특성/README.md) §6 — "스레드가 아니라 컴파일러 변환" | 변환 원리는 거기. 여기는 **`launch`/`async`/`withContext`/`Flow` 를 실제로 조립하는 규칙과 취소·예외 전파** |
| 13 확장 함수 | [`../언어-특성/README.md`](../언어-특성/README.md) §7 — 정적 디스패치 천장 | 천장의 의미는 거기. 여기는 **선언 문법·해소 순서·멤버와 충돌할 때의 규칙** |
| 34 예외 | [`../언어-특성/README.md`](../언어-특성/README.md) §8 — 검사 예외 폐지가 무엇을 떠넘겼나 | 논지는 거기. 여기는 **`Nothing` 타입과 `try` 가 식이라는 문법** |
| 39 Java 상호운용 | [`../언어-특성/README.md`](../언어-특성/README.md) §9 · [`history/spring/kotlin-and-spring.md`](../../../../../history/spring/kotlin-and-spring.md) | 상호운용의 **실제 비용**과 Spring 맥락은 거기. 여기는 **애너테이션 하나하나가 바이트코드에서 무엇을 바꾸나** |
| 40~47 컬렉션·`Sequence` | [`cs/data-structure/`](../../../../data-structure/) 35편 | 자료구조 내부는 거기. 여기는 **stdlib 가 노출하는 연산의 계약**(빈 컬렉션에서의 동작·복사 여부) |
| 32 동등성 · 46 `Map` | [`cs/data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) | 해시 원리는 거기. 여기는 **`==`/`===` 의 의미와 `data class` 가 만든 `equals` 의 범위** |
| 53 구조적 동시성 | [`cs/ops-patterns/19-graceful-shutdown/`](../../../../ops-patterns/19-graceful-shutdown/) | 운영 패턴은 거기. 여기는 **`Job` 트리에서 취소·예외가 전파되는 규칙** |
| 52 코루틴 기초 | [`cs/foundations/process-thread/`](../../../process-thread/) | 스레드·프로세스 개념은 거기. 여기는 **`suspend` 함수 호출 규칙** |
| 45 `windowed`/`chunked` · 48 `Regex` | [`cs/algorithm/09-sliding-window/`](../../../../algorithm/09-sliding-window/) · [`25-string-matching/`](../../../../algorithm/25-string-matching/) | 알고리즘은 거기. 여기는 **stdlib 가 그 패턴을 이미 함수로 갖고 있다는 것과 그 경계 동작** |

> Kotlin 은 `history/` 에 언어 역사 갈래가 **없다**(Java·JS·Python·Rust·Spring 만 있다). 그래서 Java 목록과 달리 "버전 도입 역사는 저기" 하고 넘길 곳이 없어, **버전 표기를 주제 이름과 아래 버전표에 직접 단다.**

## 뺀 것과 이유

**있는데 뺀 것**이다.

| 뺀 것 | 이유 |
|---|---|
| Kotlin Multiplatform·Native·JS·Wasm — `expect`/`actual`, C/ObjC interop, `dynamic` 타입 | 문서 분량으로는 Kotlin 문서의 절반 가까이지만 **JVM 위에서 쓰는 문법이 아니다**. `dynamic` 은 JS 타깃에서만 존재한다 |
| `kotlinx.serialization`·Ktor·Compose·Exposed | stdlib 가 아니라 **별도 라이브러리**다. ③기준소스가 "표준 라이브러리 API"로 한정돼 있다 |
| 컴파일러 플러그인 — kapt·KSP·all-open·no-arg·Lombok 연동 | 빌드 도구 층. Spring 과 쓸 때 필요하지만 **언어 문법이 아니다** |
| `kotlin-reflect` 전체 API | 별도 아티팩트이고 JVM 전용이다. 35(애너테이션 use-site target)에서 **프레임워크가 그걸 읽는다**까지만 언급 |
| 실험 기능 — collection literals(2.4)·name-based destructuring(2.3.20)·unused return value checker(2.3)·context-sensitive resolution(2.2) | 아직 Experimental 이다. 지금 외우면 바뀐다. 2.4.0에서 Stable 이 된 **context parameters 만** 38로 넣었다 |
| context receivers(옛 형태) | **context parameters 로 대체**되며 빠졌다. 옛 문법을 배울 이유가 없다 |
| Gradle Kotlin DSL·빌드 설정·코딩 컨벤션 문서 | 도구·스타일 층 |
| Lincheck·Power-assert·Dokka | 테스트·문서화 도구 |
| `kotlin.io`(파일 I/O) | JVM 에서는 대부분 `java.nio` 로 내려간다. Java 목록 57이 같은 것을 다룬다 — **중복을 피해 뺐다** |
| `kotlin.math`·`kotlin.random` | Java `Math`/`Random` 의 얇은 래퍼다. 별도 인출 가치가 낮다 |

## 버전 기준

**Kotlin 2.4.20**(2026-09-07 · 언어 릴리스 2.4.0, 2026-06-03)을 기준으로 한다.
Kotlin 은 Java 와 달리 LTS 개념이 없고 **6개월 언어 릴리스 + 중간 툴링 릴리스** 구조라, "이 기능이 Stable 이 된 버전"을 [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)로 확인해 적는다.

| 주제 | 도입/Stable 버전 | 그 이전 버전이면 |
|---|---|---|
| 02 멀티달러 보간(`$$"..."`) | Stable **2.2.0** | 2.1 이하에서는 `${'$'}` 관용구를 써야 한다 |
| 06 `when` guard 조건(`if` 가드) | Stable **2.2.0** | 2.1 이하에는 없다 — 중첩 `when` 으로 풀어야 한다 |
| 07 비지역 `break`/`continue` | Stable **2.2.0** | 2.1 이하에서는 인라인 람다 안에서 루프를 빠져나올 수 없다 |
| 29 중첩(비캡처) 타입 별칭 | Stable **2.3.0**(2.2.0 도입) | 2.1 이하에서는 최상위 별칭만 |
| 23 `when` 완결성 — 데이터 흐름 기반 검사 | Stable **2.3.0**(2.2.20 도입) | 이전에는 완결로 인정되지 않던 형태가 있다 |
| 38 context parameters | 2.2.0 실험 → Stable **2.4.0** | 그 이전은 context receivers(폐기) 또는 명시 인자 |
| 16 explicit backing fields | 2.3.0 도입 → Stable **2.4.0** | 이전에는 private 백킹 프로퍼티 + public 게터 관용구 |
| 50 `kotlin.time.Instant` | Stable **2.3.0**(2.1.0 도입) | 이전에는 `java.time.Instant` 직접 사용 |
| (참고) K2 컴파일러 | **2.0.0** 기본 | 1.9 이하는 구 프런트엔드 — 스마트 캐스트·추론 동작이 일부 다르다 |
| 26 `value class` | Stable **1.5**(inline class → value class 개명) | 1.4 이하는 `inline class`, 실험 |
| 23 `sealed interface` | Stable **1.5** | 1.4 이하는 `sealed class` 만 |
| 24 data object | **1.9** | 이전에는 `object` 에 `toString` 수동 구현 |

**버전에 갈리는 주제 = 9개**(02·06·07·16·23·24·26·29·38 · K2 영향은 04 스마트 캐스트에도 걸린다).
나머지 주제는 **2.0(K2) 이후 어느 버전에서도 같다.**
3파일에는 **「kotlinc 2.4.20 · JRE 21.0.5 · `-jvm-target` 을 밝힌 실측」** 을 명시한다.
★ **못 잰 것도 적는다** — 예: `-language-version 1.9` 는 2.4.20 이 거부하므로 **K1 과의 비교는 이 환경에서 불가능**하다.
