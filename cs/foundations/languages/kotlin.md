# foundations/languages — Kotlin: 같은 JVM 위에서 기본값을 어디서 뒤집었나 (정리)

> 이 노트는 Kotlin을 "무엇을 컴파일러가 거부하게 만들었는가"라는 한 축으로 정리하고, 그 방어선이 **끝나는 경계**에서 어떤 비용이 나는지까지 본다.\
> 원고 출처: `jun-bank/docs/study/tech/languages/kotlin.md` (따라 친 학습 노트) · 이관일 2026-09-16.\
> 본문 절들은 **원고**를 고쳐 쓴 것이다(문체·순서·인용·실측 유지). 프로젝트 고유명(특정 은행 시스템·내부 규약 코드·공통 라이브러리 이름)은 일반형으로 바꿨다.\
> **실측 표(컬렉션 런타임 클래스)는 원고 저자가 직접 확인한 값**이다(`kotlin-stdlib` 2.4.10 · Temurin JDK 21.0.5). 이관본은 복사만 한다.\
> 「한눈에」·「전체 흐름」 그림은 **Claude가 새로 그린 것**이고, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다.

Kotlin FAQ가 먼저 내세우는 것은 분량이다 — "대략 40%의 코드 줄 수 감소"([Kotlin FAQ](https://kotlinlang.org/docs/faq.html)). 그런데 줄 수는 언어를 고르는 이유가 되기 어렵다. 이 노트가 따라가는 축은 다른 것이다 — **무엇을 컴파일러가 거부하게 만들었는가.** null, 상태 분기 누락, 금액과 날짜의 혼동, 컬렉션의 가변성 — Java에서 전부 "규율로 지키는 것"을, Kotlin은 그중 일부를 "타입으로 지켜지는 것"으로 옮겼다. **옮긴 만큼 얻고, 옮기지 못한 경계에서 정확히 비용이 발생한다.** 그 경계가 이 노트의 절반이다.

---

## 한눈에 — 쉽게 말하면

Kotlin은 **문에 자동 잠금을 단 방**이다. *(Claude 보강 — 원고에 없는 비유)*

```text
Java (규율로 잠근다)                    Kotlin (문 하나가 자동으로 잠긴다)
+---------------------------+          +---------------------------+
| "나가면 문 잠그기" 규칙     |          | 그 문은 나가면 저절로 잠긴다  |
| 지키는 사람에 달렸다        |          | (non-null · when 완결성)   |
+---------------------------+          +---------------------------+
  → 한 명이라도 안 잠그면 뚫림          → 그 문 하나는 확실히 잠긴다
                                       → 그런데 옆문·뒷문은 여전히 규율
```

**언어도 똑같은 구조다.** 각 기능은 **특정한 경계 하나에서** 코드를 거부한다 — non-null 타입은 그 시그니처를 지나는 대입에서, `when` 완결성은 sealed 타입을 분기하는 자리에서. 그리고 각각은 그 경계 **바깥에서 정확히 무력하다.**

쉽게 말하면, Kotlin은 규칙을 대신 지켜 주지 않는다. **어느 규칙이 언어로 지켜질 수 있고 어느 규칙이 그럴 수 없는지를 분명하게 만들어 준다.**

---

## 이 문서가 답하려는 질문

개념 정리다. 각 기능을 두 질문으로 본다.

```text
① 무엇을 컴파일러가 거부하게 만들었나?  (그 경계에서 얻는 것)
② 그 거부는 어디서 끝나는가?           (그 경계 바깥의 비용)
```

인용은 Kotlin 2.x 공식 문서와 KEEP(설계 제안서), 대조가 필요한 곳에서는 OpenJDK JEP를 쓴다.

---

## 전체 흐름 — 두 결정이 낳은 방어선과 청구서

*(Claude 보강 — 원고 도입부의 논지를 세로로)*

```text
두 창립 결정
   │
   ├─ 실용주의: 기존 Java 자산을 버리지 않는다
   └─ JVM에 얹힘: 런타임을 새로 만들지 않는다
   │
   ▼
얻은 것 (타입 방어선 — 컴파일 시점)
   null 타입화 · when 완결성 · value class · 읽기전용 컬렉션
   │
   ▼
청구서 (같은 뿌리)
   상호운용 마찰(플랫폼 타입·@JvmStatic·final by default)
   stdlib 런타임 의존 · 컴파일 시간
```

---

## 0. 왜 생겼나 · 무엇을 지향하나

> 출처: 원고 도입부

Kotlin은 언어 연구가 아니라 IntelliJ를 비롯한 수백만 줄의 Java를 가진 회사(JetBrains)에서 나왔다(2010 시작). 초기 구성원이 적은 동기의 핵심은 두 제약이다 — 하나는 상호운용("점진적으로 도입될 것이고 기존 코드베이스와 매끄럽게 상호운용해야 한다"), 다른 하나는 컴파일 속도("our code base takes long enough to compile with javac, and we cannot afford making it any slower")([Why JetBrains needs Kotlin](https://blog.jetbrains.com/kotlin/2011/08/why-jetbrains-needs-kotlin/)). 이 두 번째 제약이 언어의 성격을 크게 갈랐다 — 표현력을 끝까지 민 JVM 언어(Scala)를 두고도 그리로 가지 않은 이유가 여기 있다. **[불확실]** "Scala를 느린 컴파일 때문에 버렸다"는 서사의 1차 출처는 위 글에서 확인하지 못했다; 확실한 것은 컴파일 속도가 물러설 수 없는 요구였다는 사실이다.

1.0 발표 글이 자기규정을 한 단어로 못박는다 — "**pragmatism** … Kotlin is not so much about invention or research"([Kotlin 1.0 Released](https://blog.jetbrains.com/kotlin/2016/02/kotlin-1-0-released-pragmatic-language-for-jvm-and-android/)). 공식 FAQ가 지향 넷을 든다 — 간결·안전(non-null 타입)·100% Java 상호운용·도구 지원. 이 넷을 묶는 단어가 실용주의다.

**세 개의 대조 — 지향이 곧 장단점의 출처다.**

- **Java와의 관계** — 같은 JVM 바이트코드로 내려가 표준 라이브러리를 공유한다(그래서 100% 상호운용). Kotlin이 더한 것은 런타임이 아니라 **타입 시스템의 방어선**이다. 이점 대부분이 컴파일 시점에 있고, 그래서 §9의 상호운용 마찰은 "Java 위에 얹힌다"는 선택의 청구서다.
- **Scala와의 관계** — 둘 다 "Java 개선"에서 출발했지만, Scala가 표현력을 끝까지 밀었다면 Kotlin은 컴파일 속도와 학습 표면을 지키는 쪽을 택했다.
- **null을 타입에 두는 언어들** — Kotlin 고유가 아니다. Swift의 `Optional`, Rust의 `Option<T>`이 같은 사고를 공유한다. Kotlin의 특수성은 발상이 아니라 그것을 **Java와 100% 섞으면서** 하려 한 데 있고, §2의 플랫폼 타입이라는 구멍이 정확히 그 야심의 이음매다.

---

## 1. 공식 목록이 스스로 말하는 축

> 출처: 원고 §1

Kotlin 문서의 "Kotlin에서 해소된 Java의 문제"는 일곱 줄인데, 여섯이 **타입 시스템을 손본 것**이고 하나(검사 예외)는 반대로 타입 시스템이 하던 일을 **뺀** 것이다([Comparison to Java](https://kotlinlang.org/docs/comparison-to-java.html)). "간결하다"는 이 목록에 없다. 반대 방향("Java에 있고 Kotlin에 없는 것")과 나란히 놓으면 성격이 드러난다 — Kotlin은 Java를 확장한 것이 아니라 **몇 개의 기본값을 반대로 정하고, 그 반대편에 있던 것을 버린** 언어다.

---

## 2. null이 타입에 있다는 것 — 그리고 그 타입이 끝나는 자리

> 출처: 원고 §2

공식 정의는 짧다 — non-null 변수를 선언하면 "the compiler enforces that these variables cannot hold a `null` value, preventing an NPE"([Null safety](https://kotlinlang.org/docs/null-safety.html)). Java에도 `@Nullable`은 있다. 차이는 검사기의 유무가 아니라 **기본값이 어느 쪽인가**다 — Java는 nullable이 기본이고 판정은 선택적 도구가 하며, Kotlin에서 `String`과 `String?`는 서로 다른 타입이다. **규칙을 지키는 주체가 도구에서 언어로 옮겨 갔다.**

`!!`는 그 규칙을 코드에서 명시적으로 취소하는 장치다. 구판 문서가 의도를 가장 잘 드러낸다 — *"if you want an NPE, you can have it, but you have to ask for it explicitly and it won't appear out of the blue"*(현행 문서에서는 삭제된 표현). NPE는 "언제든 터질 수 있는 것"이 아니라 **누군가 명시적으로 요청해야 나오는 것**으로 재정의됐다. 한 팀의 규약이 `!!`를 아예 금지한 이유가 여기 있다 — 요청 창구가 열려 있는 한 "타입이 보장한다"는 문장이 코드 어디서든 취소될 수 있다.

**경계 — 플랫폼 타입.** 타입 시스템의 보장이 끝나는 자리는 Java 쪽 경계다. Java 선언의 타입은 Kotlin에서 **플랫폼 타입**으로 취급되고, 소스에 적을 수 없으며(non-denotable) 오류 메시지에서만 `T!`로 표시된다. 중요한 것은 컴파일러가 무엇을 **하지 않는가**다 — "Kotlin does not issue nullability errors at compile time, but the call may fail at runtime." 즉 플랫폼 타입은 **검사가 유예된 구간**이고, 검사는 개발자가 타입을 적는 순간 일어난다([Java interop](https://kotlinlang.org/docs/java-interop.html)). 실무 규칙 — 플랫폼 타입(전문·파일 파싱·JDBC 경계)은 **경계에서 즉시 검증**해 non-null 도메인 타입으로 바꾼다. 그대로 안쪽으로 흘리면 NPE가 파싱 코드가 아니라 도메인 로직 한가운데서 터진다.

이 경로는 최근 강해졌다 — JSpecify에 대해 **Kotlin 2.1.0부터 nullability 위반이 경고가 아니라 오류**다([What's new in Kotlin 2.1.0](https://kotlinlang.org/docs/whatsnew21.html)). Java 라이브러리가 JSpecify를 채택했다면 이 구멍은 그 라이브러리 표면에서 거의 사라진다.

**한계 — "타입에 있다"가 "자동으로 지켜진다"는 뜻은 아니다.** 공식 문서가 Kotlin에서 NPE가 나는 경로를 열거한다 — 명시적 `throw`, `!!`, 초기화 중 새는 `this`, 그리고 Java 상호운용(예: Java 코드가 `MutableList<String>`에 `null`을 넣는 것). **타입 시스템이 주는 것은 "한 경계에서의 거부"이고, 그 경계를 어디에 그을지는 여전히 설계가 정한다.**

---

## 3. sealed class와 when 완결성 — 상태를 늘리면 컴파일이 깨진다

> 출처: 원고 §3

`sealed`는 서브클래스 집합을 컴파일 시점에 닫는 선언이다 — "All direct subclasses of a sealed class are known at compile time"([Sealed classes](https://kotlinlang.org/docs/sealed-classes.html)). 집합이 닫히면 `when`이 모든 경우를 덮었는지 판정할 수 있고 `else`가 필요 없어진다. 강제는 두 단계로 올라갔다 — 1.6 경고 → 1.7 오류, 그것도 값을 버리는 **문(statement)에서도** 분기 누락이 오류가 된다([Compatibility guide for Kotlin 1.7](https://kotlinlang.org/docs/compatibility-guide-17.html)). 상태 전이 코드는 대개 값을 반환하지 않는 문이므로, 이 승격이 없었다면 이 절의 이야기가 성립하지 않는다.

이 항목이 직결되는 이유는 상태 머신의 크기다. 어떤 결제 승인 애그리게이트는 상태 8종에 전이 16건, 그리고 **금지 전이가 따로 22건** 있다. 그런 도메인의 핵심은 대개 금지 전이다 — 허용 전이는 구현하면서 자연히 드러나지만, 금지는 명시하지 않으면 아무도 막지 않는다. 상태를 sealed 계층(또는 enum)으로 표현하면, 상태가 하나 늘 때 **그 상태를 분기하는 모든 자리가 동시에 컴파일 오류가 된다.** 이것이 "문서의 전이표"와 "실제 코드"를 잇는, 사람 리뷰가 아닌 유일한 자동 장치다.

**이 장치가 하지 않는 세 가지.**

- **완결성 검사는 상태의 집합만 본다.** "`AUTHORIZED`에서 `capture`가 허용되는가" 같은 조건은 사람이 적은 것이며 컴파일러 시야 밖이다. sealed가 막는 것은 "새 상태를 아무도 다루지 않는 것"까지다.
- **`else`를 한 번 적으면 그 자리에서 검사가 영구히 꺼진다.** 새 상태는 오류 대신 조용히 `else`로 흘러든다. Java 명세도 같은 논거를 더 강한 문장으로 적는다 — "**A match-all clause risks sweeping exhaustiveness errors under the rug**"([JEP 441](https://openjdk.org/jeps/441)). 두 언어가 독립적으로 같은 결론에 도달했다는 사실이, 이것이 문법 취향이 아니라 유지보수 문제라는 근거다.
- **subject가 sealed·enum·Boolean이 아니면 애초에 검사 대상이 아니다.** 상태를 문자열이나 코드 값으로 들고 다니면 같은 코드가 아무 경고 없이 통과한다.

**Java 17+ sealed와의 실질 차이** — Kotlin은 허용 서브클래스 목록(`permits`)을 요구하지 않고([KEEP-226](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0226-sealed-interface-freedom.md)), `non-sealed` 탈출구가 없으며, 런타임 안전망(`MatchException`)이 Java에만 있다. 두 언어의 봉인 계층은 섞을 수 없다. 다만 Kotlin 2.2.20/2.3.0의 **데이터 흐름 기반 완결성 검사**가 앞선 조건·조기 반환까지 추적해 불필요한 `else`를 지울 수 있게 해 둘째 함정을 줄인다.

---

## 4. 값을 값으로 — data class와 value class

> 출처: 원고 §4

값 타입은 두 도구로 만들어진다 — `Money` 같은 다필드 값은 `data class`, `BusinessDate` 같은 단일 래퍼는 `@JvmInline value class`.

```kotlin
public data class Money(val minorUnits: Long, val currency: Currency) : Comparable<Money>

@JvmInline
public value class BusinessDate(val value: LocalDate) : Comparable<BusinessDate>
```

**data class — 동등성을 컴파일러가 쓴다.** 컴파일러가 주 생성자 프로퍼티에서 `equals()`/`hashCode()`·`toString()`·`componentN()`·`copy()`를 파생한다([Data classes](https://kotlinlang.org/docs/data-classes.html)). 값 타입에서 이것이 중요한 이유는 편의가 아니라 **정확성**이다 — `Money(1000, KRW) == Money(1000, KRW)`가 참이어야 금액을 맵 키나 단언에 쓸 수 있고, 손으로 쓰면 필드가 늘 때 조용히 어긋난다. 함정이 셋 — ① 클래스 바디 프로퍼티는 생성 코드에서 빠진다(동등성이 조용히 바뀔 수 있다), ② `copy()`는 **얕은 복사**라 `MutableList`를 든 data class는 원본과 사본이 리스트를 공유한다(§5와 같은 함정), ③ private 생성자로 불변식을 지켜도 생성된 `copy()`가 public이라 뚫린다(2.0.20부터 경고, 아직 오류 아님 — `@ConsistentCopyVisibility`로 켠다).

**value class — 타입만 얻고 래퍼는 안 만든다.** 어떤 시스템에는 영업일(원장 귀속)과 달력일(한도의 "하루")이 둘 다 쓰이고, 둘이 같은 `LocalDate`를 쓰면 **컴파일러가 혼동을 잡아주지 않는다**. 감싸는 것 자체가 목적이지만 감싸는 비용(힙 할당)이 문제인데, value class는 런타임에 대개 감싼 값 그 자체로 표현돼 이 비용을 없앤다. "대개"가 정확한 표현이다 — "**inline classes are boxed whenever they are used as another type**"([Inline value classes](https://kotlinlang.org/docs/inline-classes.html)). 제네릭 인자·인터페이스·**nullable**(`Foo?`)로 쓰는 순간 힙 할당이 되살아난다. **"무비용 래퍼"는 조건부 문장이다.** 그리고 언박싱되면 함수 이름에 해시가 붙어 Java에서 잘 안 보이는데, 설계 문서는 이것이 부작용이 아니라 **의도**라 적는다 — 불변식을 Java 우회로 뚫지 못하게 만든 대가로 Java 상호운용을 끊은 것이다([KEEP-0104](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0104-inline-classes.md)).

**Java record와의 자리** — record는 필드가 `final`("immutable by default")이라 이 지점에서 data class보다 엄격하지만, **record에는 `copy()`가 없다**([JEP 395](https://openjdk.org/jeps/395)). `@JvmRecord`로 진짜 record를 만들 수도 있으나 "기존 클래스에 나중에 붙이면 바이너리 호환이 깨진다" — 버전으로 배포되는 공통 라이브러리에서는 이 한 줄이 결정적이다. Kotlin이 `@JvmInline`을 굳이 요구하는 이유는 JVM에 진짜 값 타입(Project Valhalla, [JEP 401](https://openjdk.org/jeps/401))이 오기를 기다릴 수 없어서였고, 그 Valhalla가 JDK 28 preview라 JVM 21에서는 "프로퍼티 하나" 제약이 한동안 유효하다.

---

## 5. 가변성을 이름에 적는다 — val/var와 읽기 전용 컬렉션

> 출처: 원고 §5

`val`이 보장하는 범위는 정확히 한정된다 — **참조가 고정될 뿐 객체 내부는 고정되지 않는다.** "Write operations with a mutable collection are still possible even if it is assigned to a `val`"([Collections overview](https://kotlinlang.org/docs/collections-overview.html)).

컬렉션 쪽 설계는 읽기 전용/가변 인터페이스 분리다. Java에서는 `Arrays.asList()`도 `Collections.unmodifiableList()`도 타입이 전부 `List`라 "**타입만 봐서는 가변인지 알 수 없고**" 실패가 런타임 예외다. Kotlin에서는 `listOf(...)`에 `add`를 부르면 컴파일 오류다([Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html)) — **실패 시점이 런타임에서 컴파일로 옮겨 온 것.**

**읽기 전용은 불변이 아니다 — 그리고 공식 문서가 이 말을 흐린다.** `List`는 **뷰**다 — 입문 문서는 "you can **create a read-only view of a mutable list**"라고 숨기지 않는데, 코딩 컨벤션은 같은 인터페이스를 "**immutable** collection interfaces"라 부른다([Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)). 뷰는 원본과 같은 객체이므로 원본 참조를 든 쪽은 여전히 고칠 수 있다. **함정의 절반은 용어에 있다.**

**실측(원고 저자 직접 확인, `kotlin-stdlib` 2.4.10 · JDK 21).**

| Kotlin에서 만든 것 | 런타임 클래스 | Java에서 `add()` | Java에서 `set()` |
|---|---|---|---|
| `listOf()` | `kotlin.collections.EmptyList` | 예외 | 예외 |
| `listOf("a")` | `Collections$SingletonList` | 예외 | 예외 |
| `listOf("a","b")` | `Arrays$ArrayList` | 예외 | **성공** |
| `mutableListOf(...)`를 `List`로 노출 | `java.util.ArrayList` | **성공** | **성공** |
| (대조) Java `List.of("a","b")` | `ImmutableCollections$List12` | 예외 | 예외 |

두 줄이 중요하다 — **`listOf()`는 `List.of()`가 아니다**(원소가 둘 이상이면 `Arrays.asList`로 내려가 `set`이 통과), **`List` 타입은 런타임 보증이 아니다**(애그리게이트가 자기 `MutableList`를 `List`로 내주면 런타임 클래스는 그냥 `ArrayList`). 애그리게이트 불변식이 "객체 안에서만 성립"하려면 밖에서 고쳐질 수 없어야 하는데, **타입 시스템이 주는 것은 그 절반뿐이다.** 나머지 절반은 방어 복사·영속 컬렉션 + 변경 감지 테스트가 막는다. 진짜 불변 컬렉션(`kotlinx.collections.immutable`)은 stdlib가 아니고 안정성 등급이 **Alpha**("breaking changes are expected")라, "영속 컬렉션 쓰면 된다"에는 이 비용이 함께 적혀야 한다.

---

## 6. 코루틴 — 스레드가 아니라 컴파일러 변환이다

> 출처: 원고 §6

`suspend`는 문법 설탕이 아니라 **JVM 시그니처를 바꾸는 컴파일 변환**이다 — CPS(Continuation-Passing-Style)로 구현되어 모든 suspend 함수에 `Continuation` 파라미터가 암묵적으로 붙는다([KEEP-0164](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0164-coroutines.md)). 본문은 상태 기계로 컴파일되고, **지역 변수는 스택이 아니라 익명 클래스의 필드로 승격**된다. "가볍다"의 실체는 "**중단된 코루틴만 스레드를 놓는다**" — 실행 중일 때는 언제나 진짜 스레드 위에 있다.

**구조적 동시성 — 이 모델의 진짜 값.** 가장 크게 갈리는 것은 성능이 아니라 **생명주기 관리**다 — "coroutines form a tree hierarchy … A parent coroutine waits for its children … if the parent … fails or gets canceled, all its child coroutines are recursively canceled too"([Coroutines basics](https://kotlinlang.org/docs/coroutines-basics.html)). 새 코루틴은 `CoroutineScope` 안에서만 시작하므로 "던져 놓고 잊는" 작업이 구조적으로 안 생긴다. 예외 전파도 강하다 — 형제까지 함께 죽는 것이 기본이고, 벗어나려면 `try/catch`가 아니라 `SupervisorJob`으로 **구조 자체를 바꿔야** 한다.

**한계 — 취소는 보장이 아니라 규약이다.** "coroutine cancellation is cooperative" — 중단점을 지나지 않는 계산 루프는 취소해도 계속 돈다([Cancellation](https://kotlinlang.org/docs/coroutines-cancellation.html)). 관측성 비용도 실재한다 — 비동기 스택 트레이스는 사후 재봉합해야 하고 "losing referential transparency"의 대가가 붙으며, 디버거에서 변수가 "was optimized out"으로 사라지고 회피 옵션 `-Xdebug`는 "Never use this flag in production"이라 못박혀 있다.

**가상 스레드와의 대비 — 같은 문제, 반대 해법.** Java 21 가상 스레드는 같은 문제(스레드 희소성)를 정반대로 푼다 — 목표가 "**simple thread-per-request style**로 스케일"이고 "basic concurrency model을 바꾸지 않는다"이며, 블로킹 I/O를 런타임이 흡수한다([JEP 444](https://openjdk.org/jeps/444)). Kotlin은 언어에 최소만 넣고 나머지를 라이브러리(`kotlinx.coroutines`)에 남겼고, 가상 스레드는 JDK 런타임에 들어가 코드는 그대로다.

**블로킹 스택이 쓰지 않는 이유** — Spring MVC도 `suspend` 컨트롤러를 지원하므로 "블로킹이라 못 쓴다"는 근거는 성립하지 않는다. 실제 이유는 이익-비용이다 — JDBC는 코루틴이 흡수하지 못해 결국 진짜 스레드를 점유하고 `Dispatchers.IO`(64스레드 상한)로 격리되므로 "코루틴 → `withContext(IO)` → 스레드 풀"이라는 우회 계층이 늘 뿐이고, 비용(ThreadLocal 기반 MDC·trace 유실, 스택 트레이스·디버깅 비용, 의존성 추가)은 실재한다. 처리량 요구가 스레드 병목으로 실측될 때 JVM 21에서 먼저 검토할 것은 코드 변경이 없는 **가상 스레드**이고, 코루틴이 나은 자리는 **구조적 동시성과 취소가 요구 자체인 경우**다.

---

## 7. 확장 함수와 수신자 람다 — DSL이 되는 이유, 그리고 정적 디스패치라는 천장

> 출처: 원고 §7

확장 함수에서 중요한 것은 무엇을 하지 않는가다 — "extensions don't modify the classes … You make new functions callable … using the same syntax"([Extensions](https://kotlinlang.org/docs/extensions.html)). 클래스를 열지 않고 그 타입의 어휘를 바깥에서 늘리는 것이 값이다(`LocalDate`·`String`에 도메인의 말을 붙이는 자리). 대가는 디스패치에 있다 — 확장은 **정적 디스패치**라 다형적이지 않고, 변수의 **선언 타입**이 무엇을 부를지 정한다. 멤버와 이름이 겹치면 확장이 진다.

**수신자 람다 — DSL이 성립하는 지점.** DSL을 만드는 것은 확장 함수가 아니라 **수신자 있는 함수 타입**이다 — `init: HTML.() -> Unit`은 "이 블록 안에서 `this`는 `HTML`이다"를 선언해 부를 수 있는 이름을 타입으로 제한한다. 오타가 런타임이 아니라 컴파일에서 걸린다. `@DslMarker`가 중첩 수신자 혼선을 막는다.

**테스트가 읽히는 이유가 라이브러리가 아니라 언어 기본 기능이다** — 단언 DSL 라이브러리 없이도 첫 테스트가 읽히는 것은 백틱 함수 이름, data class, 연산자 오버로딩 덕이고, 셋 다 의존성을 늘리지 않는다. **읽히는 테스트를 위해 DSL 라이브러리가 필요하다는 통념은 최소한 이 규모에서는 성립하지 않았다.**

---

## 8. 검사 예외 폐지 — 무엇을 얻고 무엇을 떠넘겼나

> 출처: 원고 §8

"Kotlin does not have checked exceptions"가 앞서 본 두 목록에 **동시에** 실려 있다 — "해소된 문제"에도, "Kotlin에 없는 것"에도. 공식 문서가 이것을 개선이자 상실로 함께 적는 사실 자체가 논쟁 상태를 보여 준다.

찬성 근거는 한 줄이다 — 검사 예외가 지우는 것은 아무것도 안 하는 `catch` 블록과, 람다·고차 함수와의 충돌이다(함수 타입에 예외 목록을 실을 방법이 없다). 반대 손실도 분명하다 — 검사 예외는 **실패 경로를 시그니처에 적게 만드는 유일한 언어 장치**였고, 사라지면 "이 함수가 어떤 이유로 실패하는가"는 문서와 규율의 문제가 된다. 상호운용에서 즉시 형태를 드러낸다 — Kotlin 함수는 기본적으로 `throws`를 선언하지 않아 Java 호출자가 그 예외를 잡으려 하면 컴파일되지 않는다(`@Throws`로 되돌린다). 빈자리는 언어가 아니라 설계로 메운다 — 오류 코드 대장을 유일 창구로 두고 판정 순서를 고정하는 식이다. `kotlin.Result`·`runCatching`도 같은 자리를 노리지만 **컴파일러가 강제하지 않는 관용구**라 예외와 다르지 않다.

---

## 9. Java 상호운용의 실제

> 출처: 원고 §9

"100% interoperable"은 사실이지만 **무마찰이라는 뜻은 아니다.** 마찰은 한 형태로 반복된다 — Kotlin에 없는 개념(static 멤버, 필드, 오버로드, 검사 예외, open 클래스)을 Java 쪽이 요구할 때 어노테이션이나 플러그인으로 되돌린다. 가장 자주 부딪히는 것이 `static`이다 — companion object 멤버는 기본적으로 인스턴스 메서드이고 `@JvmStatic`으로 static을 생성한다. 나머지도 하나씩 있다 — `@JvmField`, `@JvmOverloads`, `@file:JvmName`, 앞 절의 `@Throws`.

**실측된 마찰의 전형** — JUnit5 `@MethodSource`가 **정적** 팩토리를 요구하는데 Kotlin에 `static`이 없다. 확인 결과 세 형태 전부 성립이었다.

| 형태 | 구성 | 쓰기 좋은 자리 |
|---|---|---|
| A | `@MethodSource` + `companion object` + `@JvmStatic` | 케이스가 타입 있는 data class여야 할 때 |
| B | `@CsvSource` | 스칼라만으로 표가 되는 자리(문자열 리터럴이라 타입 오타는 실행 시에 걸림) |
| C | `@TestInstance(PER_CLASS)` + 비정적 `@MethodSource` | 케이스가 픽스처를 참조할 때(`@JvmStatic`도 companion도 없다) |

판정은 "실행기를 바꿔야 할 이유가 아니라 형태를 고르는 문제였다." 상호운용 마찰의 전형이 이렇다 — 막히지 않지만 **한 번은 알아야 하고**, 모르면 "Kotlin에서는 이 도구가 안 된다"는 잘못된 결론에 도달한다.

**어노테이션으로 안 되는 것 — final by default.** Kotlin은 클래스·멤버가 `final`이 기본이라 Spring AOP처럼 `open`을 요구하는 프레임워크와 충돌한다 — 해법은 `kotlin-spring` 컴파일러 플러그인이 `@Component`·`@Transactional` 등이 붙은 클래스를 자동으로 여는 것이다([All-open plugin](https://kotlinlang.org/docs/all-open-plugin.html)). **언어 기본값과 프레임워크 전제가 충돌하는 자리**이고, 여는 범위가 어노테이션 목록으로 정해지므로 목록 밖 조합은 그 자리에서 막힌다. 반대 방향(Java를 Kotlin에서 호출)의 마찰은 훨씬 얕다(SAM 변환 자동·게터가 프로퍼티로) — 남는 문제는 §2의 플랫폼 타입 하나다.

---

## 10. 비용 — 컴파일 시간·바이너리·학습

> 출처: 원고 §10

- **컴파일 시간.** "Kotlin이 javac보다 느리다"는 인식은 널리 있지만 **JetBrains 발표의 Kotlin 대 Java 비교 수치는 확인하지 못했다.** 공식 수치는 컴파일러 세대 간 비교다 — "K2 compiler brings up to 94% compilation speed gains"(Anki-Android clean build 57.7초 → 29.7초)([K2 migration guide](https://kotlinlang.org/docs/k2-compiler-migration-guide.html)). 주의 둘 — 이것은 **K1 대비**이지 Java 대비가 아니고, clean(29.7초)과 incremental(0.122초)은 자릿수부터 다르다. 증분 컴파일이 기본으로 켜져 있으나 ABI가 바뀌면 파급이 커진다.
- **어노테이션 처리는 별도 항목이다.** kapt는 "expensive, significantly increases build time"이고 KSP가 대안이다 — **Java 어노테이션 프로세서에 의존하는 스택을 그대로 들고 오면 Kotlin의 빌드 비용이 가장 나빠진다.**
- **바이너리 크기.** `kotlin-stdlib`를 런타임 의존으로 갖는다. 서버 배포에서 문제가 된 **공식 수치는 확인하지 못했다**(Android 메서드 수 논의가 주 출처라 전제가 다르다). 비용으로 세우되 값은 비워 두는 것이 정직하다.
- **학습 비용.** "Kotlin에 있고 Java에 없는 것"에 21개 항목이 있다 — 이것이 학습 표면이고, 팀이 하는 일은 그중 **부분집합을 고르고 나머지를 안 쓰기로 합의하는 것**이다. 언어 기능이 많다는 것의 비용은 "배울 게 많다"가 아니라 **"팀마다 다른 Kotlin을 쓰게 된다"**이고, 그 비용은 규약과 린트로만 줄어든다.

---

## 11. 정리 — 컴파일러가 막는 것과 우리가 막아야 하는 것

> 출처: 원고 §11

돌아본 기능들은 하나의 공통 형태를 갖는다 — **각각은 특정한 경계 하나에서 코드를 거부한다**(non-null은 대입에서, `when` 완결성은 sealed 분기에서, value class는 그 타입을 요구하는 API에서, 읽기 전용 컬렉션은 수신자가 변경 메서드를 부르는 지점에서). 그리고 각각은 그 경계 **바깥에서 정확히 무력하다.**

그래서 실전에서는 규칙마다 주 강제 수단이 갈린다 — 불변 우선은 린트+변경 감지 테스트가, null 안전은 정적 검사+경계 테스트가, 값 타입 의무는 정적 스캔이 막는다. 컴파일이 **단독** 강제 수단인 것은 모듈 경계뿐이다(별도 빌드 모듈로 빼서 다른 컨텍스트 참조를 컴파일 단계에서 끊는 것 — 타입이 아니라 **모듈 그래프**가 하는 일).

이것을 "Kotlin이 기대만 못하다"로 읽으면 틀린 독해다. 저 배치에 도달할 수 있었던 것 자체가 언어 덕분이다 — 무엇이 컴파일에 걸리고 무엇이 안 걸리는지를 **한 줄로 판정할 수 있었기 때문에** 나머지를 린트·테스트·리뷰로 정확히 배분할 수 있었다. Java에서 같은 표를 만들면 대부분 칸이 "리뷰"가 된다. 그래서 실질은 이렇게 요약된다 — Kotlin은 규칙을 대신 지켜 주지 않는다. **어느 규칙이 언어로 지켜질 수 있고 어느 규칙이 그럴 수 없는지를 분명하게 만들어 준다.**

---

## 핵심 문장

- **Kotlin의 축은 간결이 아니라 "무엇을 컴파일러가 거부하게 만들었는가"다.**
- **각 기능은 특정한 경계 하나에서 코드를 거부하고, 그 경계 바깥에서 정확히 무력하다.**
- **null 안전의 차이는 검사기 유무가 아니라 기본값이 어느 쪽인가다** — 규칙을 지키는 주체가 도구에서 언어로 옮겨 갔다.
- **`else`를 한 번 적으면 완결성 검사가 그 자리에서 영구히 꺼진다** — "match-all이 오류를 양탄자 밑으로 쓸어 넣는다".
- **읽기 전용 컬렉션 타입은 런타임 보증이 아니다** — 타입 시스템이 주는 것은 절반뿐이다.
- **"무비용 래퍼(value class)"는 조건부 문장이다** — nullable·제네릭·인터페이스로 쓰면 박싱이 되살아난다.
- **코루틴과 가상 스레드는 같은 문제(스레드 희소성)의 반대 해법이다.**

---

## 관련 자료

- 같은 컬렉션: [`java-jvm.md`](java-jvm.md)(Kotlin이 얹히는 런타임 — 코루틴 대 가상 스레드의 대비) · [`c-cpp-csharp.md`](c-cpp-csharp.md)(C#도 값 타입·record가 있는 관리 런타임) · [`go.md`](go.md)(sealed·null 안전이 없어 상태 분기를 컴파일러가 못 잡는 대조군).
- 자매 개념 노트: [`../../engineering/clean-code/`](../../engineering/clean-code/)(불변식·캡슐화가 왜 값 타입·읽기전용 컬렉션과 이어지는지).
- 공식 문서: [Comparison to Java](https://kotlinlang.org/docs/comparison-to-java.html) · [Null safety](https://kotlinlang.org/docs/null-safety.html) · [Sealed classes](https://kotlinlang.org/docs/sealed-classes.html) · [Inline value classes](https://kotlinlang.org/docs/inline-classes.html).
- 설계 제안(KEEP): [KEEP-0164 Coroutines](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0164-coroutines.md) · [KEEP-0104 Inline classes](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0104-inline-classes.md) · [KEEP-226 Sealed freedom](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0226-sealed-interface-freedom.md).

---

## 용어 풀이

- **null 안전(Null Safety)** — `String`과 `String?`를 다른 타입으로 두어 nullable 값이 non-null 자리에 들어가는 것을 컴파일러가 막는 것.
- **플랫폼 타입(Platform Type)** — Java에서 온 값의 타입. 소스에 적을 수 없고(`T!`로만 표시), nullability 검사가 유예된 구간이다.
- **sealed class** — 서브클래스 집합을 컴파일 시점에 닫는 선언. `when`이 모든 경우를 덮었는지 판정하게 해 준다.
- **완결성 검사(Exhaustiveness Check)** — `when`이 sealed/enum/Boolean의 모든 경우를 덮었는지 컴파일러가 확인하는 것. `else`를 적으면 꺼진다.
- **data class** — `equals`/`hashCode`/`copy` 등을 컴파일러가 파생해 주는 클래스. `copy()`는 얕은 복사다.
- **value class(inline class, `@JvmInline`)** — 단일 값을 감싸 타입만 얻고 런타임 래퍼(힙 할당)는 대개 없애는 것. 다른 타입으로 쓰이면 박싱된다.
- **읽기 전용 뷰(Read-only View)** — 가변 컬렉션을 `List` 타입으로 노출한 것. 원본 참조로는 여전히 변경 가능하므로 불변이 아니다.
- **코루틴(Coroutine)** — `suspend`가 만드는 컴파일 변환(CPS + 상태 기계). 중단된 동안만 스레드를 놓는다.
- **구조적 동시성(Structured Concurrency)** — 부모-자식 코루틴이 생명주기를 공유해 부모 취소 시 자식이 재귀적으로 취소되는 모델.
- **확장 함수(Extension Function)** — 클래스를 열지 않고 그 타입에 함수를 붙이는 것. 정적 디스패치라 다형적이지 않다.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **"불법 상태를 표현 불가능하게(make illegal states unrepresentable)".** sealed + when 완결성, value class, non-null이 함께 겨냥하는 설계 격언이다. Kotlin이 Go와 갈리는 지점([`go.md`](go.md) §8)이 정확히 이 도구의 유무이고, 값 타입·불변식은 [`../../engineering/clean-code/`](../../engineering/clean-code/)의 캡슐화·단정적(Assertive)과 이어진다.
- **왜 `!!`가 위험 신호인가.** `!!`는 타입 방어선을 코드 한 줄로 취소하는 유일한 창구라, 코드베이스에서 `!!` 개수가 곧 "타입이 보장한다는 문장이 취소된 지점 수"다. 그래서 많은 팀이 린트로 개수를 0에 묶는다.
- **Project Valhalla가 왜 value class에 걸리나.** JVM에 진짜 값 타입이 오면(JEP 401) 다필드 value class도 힙 할당 없이 표현되지만, 그전까지 Kotlin의 `@JvmInline`은 "프로퍼티 하나"로 제한된다 — 언어가 런타임에 얹혀 있어서 런타임이 못 주는 것은 언어도 못 주는 전형이다.
- **CPS 변환이 스택 트레이스를 흐리는 이유.** 코루틴은 콜스택을 힙의 `Continuation` 체인으로 옮기므로, 예외가 났을 때 "어디서 왔나"의 물리적 콜스택이 존재하지 않는다. 그래서 디버깅 지원이 별도 기능(사후 재봉합)으로 필요하고, 이것이 가상 스레드(콜스택을 그대로 두는 쪽)와의 실무적 차이다.
