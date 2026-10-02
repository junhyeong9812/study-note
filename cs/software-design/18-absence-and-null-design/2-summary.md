# software-design/18-absence-and-null-design — "없음"의 설계: null·빈 컬렉션·Optional·Null Object·예외 — 정리 (힌트)

## 해결하는 문제

"값이 없다"는 흔한 상황이다. 회원의 쿠폰 목록이 비었다, 별명을 안 정했다, 그 id의 주문이 없다. 이것을 `null` 하나로 표현하면 **호출처마다 기억해서 검사해야** 하고, 한 곳만 잊어도 NPE가 난다.

```text
 getCoupons(userId) ── null ──┬─> 호출처 1  if (cs != null) ...   OK
                              ├─> 호출처 2  if (cs != null) ...   OK
                              ├─> ...
                              ├─> 호출처 7  cs.size()             NPE  ← 하나만 잊어도
                              └─> 호출처 11 if (cs != null) ...   OK
 getCoupons(userId) ── List.of() ─> 11곳 모두 검사 없이 OK (빈 목록을 도는 루프는 0번 돈다)
```

- *NPE(NullPointerException)*: null 참조로 필드를 읽거나 메서드를 부를 때 JVM이 던지는 예외.
- Tony Hoare는 1965년 ALGOL W에 null 참조를 넣은 것을 "my billion-dollar mistake"라고 불렀다. QCon London 2009 발표다(InfoQ 영상 페이지 날짜 표기 2009-08-25). 발표 요약문에 "simply because it was so easy to implement"라는 말이 인용돼 있다.

쉬운 예: 우편함이 비었을 때 "우편함 없음"과 "편지 0통"은 다르다. 편지가 0통이면 그냥 열어 보고 닫으면 된다. 우편함 자체가 없다고 하면 받는 사람마다 "우편함이 있나?"부터 확인해야 한다.\
똑같은 구조다.\
실무 예: 쿠폰 목록 API가 쿠폰이 없을 때 `null`을 돌려줬다. 호출처 11곳 중 10곳은 검사했지만 새로 만든 정산 배치 한 곳이 검사를 빠뜨려 새벽에 NPE로 멈췄다. 또 할인율 입력란을 비운 상품이 `int` 필드 때문에 "0% 할인"으로 저장돼, "할인 미정"과 "할인 없음"을 구분할 수 없게 됐다.

기초: 에러를 정의로 없애는 시각은 [15](../15-error-handling-design/2-summary.md), Special Case 패턴의 출처와 "실패를 숨기는 경우"는 [16](../16-error-strategy-exceptions-vs-results/2-summary.md)에 있다.

## 동작·원리

### 1. "없음"을 표현하는 다섯 방법

```text
 방법              시그니처에 드러나나   호출자가 할 일             어울리는 자리
 ─────────────────────────────────────────────────────────────────────────────────────────────
 null              아니오               기억해서 검사               경계 밖(외부 API·DB 컬럼) — 들여오면 바로 바꾼다
 빈 컬렉션/배열     (타입이 컬렉션)       없음 — 그냥 돈다            "여러 개일 수 있는" 결과는 이것
 Optional<T>       예                   map/orElse/orElseThrow      "0개 또는 1개" 반환값
 Null Object       아니오(일부러)        없음 — 기본 동작이 정해짐    없음일 때 할 일이 정해진 경우(할인 없음 = 원가)
 예외              (unchecked면 아니오) 잡거나 전파                 없으면 호출 계약 위반인 경우(id로 꼭 있어야 할 주문)
```

- Bloch 『Effective Java』 3판 Item 54 "Return empty collections or arrays, not nulls", Item 55 "Return optionals judiciously"(Pearson 목차로 제목 확인, 본문 미열람).
- JDK 21 `Optional` API 문서: "Optional is primarily intended for use as a method return type where there is a clear need to represent "no result," and where using null is likely to cause errors." 그리고 "A variable whose type is Optional should never itself be null".

### 실험 A: 호출처 11곳 중 1곳이 검사를 잊으면

```java
static List<Coupon> couponsNull(long userId)  { return userId == 7 ? null      : List.of(new Coupon("WELCOME", 10)); }
static List<Coupon> couponsEmpty(long userId) { return userId == 7 ? List.of() : List.of(new Coupon("WELCOME", 10)); }
// 호출처 11곳: #7만 검사 없이 cs.size()
```

(실험 A, JDK 21.0.12 eclipse-temurin `--cpus=2`, `scratchpad/sd/15/e18/Absence.java`, 2026-10-01)

```text
== 1. null 반환 목록, 호출처 11곳 중 1곳 누락
    호출처 #7: Cannot invoke "java.util.List.size()" because "<local5>" is null
  null 반환: NPE 1건
  빈 목록 반환: NPE 0건
```

- 반환 쪽 한 곳을 바꾸면 호출처 11곳의 검사 의무가 사라진다. 검사 코드 10곳도 지울 수 있다.

### 2. Optional — 반환값 전용 상자

```text
 findCoupon(code) ──> Optional ──┬─ .map(Coupon::percent).orElse(0)        기본값
                                 ├─ .orElseThrow(() -> new X("문맥"))       없음 = 계약 위반
                                 └─ .get()                                 검사 없이 꺼냄 → NoSuchElementException
```

(실험 B, 같은 환경)

```text
== 2. Optional.get() 무조건 호출
  java.util.NoSuchElementException: No value present
  orElseThrow(문맥): 쿠폰 없음 code=X
  orElse(기본값): 0%
```

- `get()`을 검사 없이 부르면 NPE가 `NoSuchElementException: No value present`로 **이름만 바뀐다**. 메시지에 어떤 값이 없었는지도 없다.
- `orElseThrow(공급자)`는 문맥을 담은 예외를, `orElse`는 기본값을 준다. "없음"일 때 할 일을 호출자가 명시하게 된다.
- Optional을 **필드·인자**에 쓰면 손해가 크다.
  - 필드: `Optional`은 `Serializable`이 아니다(실험 D). 객체마다 상자 하나가 더 생긴다.
  - 인자: 호출자가 `Optional.empty()`·`Optional.of(x)`로 감싸야 하고, 인자 자체가 `null`로 올 수도 있다. 오버로드나 기본값 있는 두 메서드가 보통 더 단순하다(관례 — JDK 문서의 "반환 타입용" 의도에서 나온 권고).

### 3. Null Object — 없음일 때의 기본 동작을 객체로

```text
          «interface» Discount
          apply(price) / describe()
             ▲                 ▲
     Percent(p)            NoDiscount (싱글턴)
     price*(100-p)/100     price 그대로, "할인 없음"
```

(실험 C, 같은 환경)

```text
== 3. Null Object
  WELCOME -> 10%, 10000원 -> 9000
  NONE -> 할인 없음, 10000원 -> 10000
```

- `byCode.getOrDefault(code, NoDiscount.INSTANCE)` 한 곳에서 없음을 처리하고, 호출자는 분기 없이 `apply`를 부른다.
- 『Refactoring』 2판 "Introduce Special Case"(별칭 Introduce Null Object), PoEAA "Special Case"가 이 모양이다.
- 경계: 호출자가 "없었다는 사실"을 알아야 하는 경우(쿠폰 코드를 잘못 입력해 사용자에게 알려야 함)에는 Null Object가 그 사실을 숨긴다. 그때는 Optional이나 결과 타입이 맞다.

### 4. "없음"과 "0"·"빈 문자열"은 다르다

(실험 4·5, 같은 환경 — 번호는 출력의 머리 번호)

```text
== 4. Map.get의 null은 두 가지 뜻
  get(A)=null, get(B)=null, containsKey(A)=true, containsKey(B)=false
  Map.of(값 null) -> NPE
== 5. 미입력과 0
  int 필드: 0 (미입력인지 0%인지 구분 불가)
  Integer 필드: null (미입력 = null)
```

- `HashMap.get`의 `null`은 "키가 없음"과 "값이 null"을 구분하지 못한다. JDK 21 `Map.of` 같은 불변 맵은 null 키·값을 아예 거부한다(API 문서 "They disallow null keys and values", 실험에서 NPE).
- 원시 타입 `int` 필드는 기본값 0이라 "미입력"을 표현할 수 없다. "할인 미정"과 "할인 0%"가 업무에서 다르다면 타입으로 구분해야 한다.
  - 선택지: `Integer`(null = 미입력 — 다시 null 문제), `OptionalInt`, 또는 상태를 드러내는 타입(`sealed DiscountPolicy permits Undecided, Rate`). 마지막이 가장 명시적이다([24 types-as-invariants](../24-types-as-invariants/2-summary.md)).

### 5. null 경계 정하기

```text
 바깥(null이 올 수 있음)                       경계                         안쪽(non-null 가정)
 HTTP JSON 필드 · DB nullable 컬럼 ──> [파싱·매핑에서 한 번 결정] ──> 도메인 객체: 필드 non-null
 외부 라이브러리 반환값                    null → 기본값 / Optional /       없음은 타입(Optional·sealed)으로
                                         Null Object / 거절(400)
```

- 경계에서 한 번 정하고 안쪽은 null을 들이지 않는다. 생성자에서 `Objects.requireNonNull`로 fail-fast([15](../15-error-handling-design/2-summary.md) 「fail-fast」 절).
- 도구로 강제할 수 있다. JSpecify는 도구 중립 null 표기(`@Nullable`·`@NullMarked` 등)를 정의하고 1.0.0을 냈다(jspecify.dev). 정적 분석기가 이 표기로 경계 위반을 찾는다 — 도구별 지원 범위는 각 도구 문서에서 확인 [?].

### 실험 E: NPE 메시지는 무엇을 알려 주나 (JEP 358)

(실험 E, JDK 21.0.12 — 같은 코드를 컴파일 옵션만 바꿔 실행)

```text
[javac 기본]
  Cannot invoke "String.length()" because "<local5>" is null
[javac -g]
  Cannot invoke "String.length()" because "n" is null
[-XX:-ShowCodeDetailsInExceptionMessages]
  null
```

- JEP 358(Helpful NullPointerExceptions, JDK 14)이 "무엇이 null이었나"를 메시지에 넣는다. JDK 15부터 기본으로 켜졌다(JDK 15 릴리스 노트, JDK-8233014).
- 지역 변수 이름은 지역 변수 표가 있을 때만 나온다(JEP 358: 없으면 `<local i>`). javac는 `-g` 없이는 지역 변수 표를 넣지 않아 `<local5>`가 됐다.
- 이 메시지는 원인 추적을 돕지만 **null을 없애 주지는 않는다**. 그리고 응답 본문에 새면 코드 단서가 노출된다([17](../17-error-messages-and-log-level-policy/2-summary.md)).

### 실험 D: Optional 필드와 직렬화

(실험 D, 같은 환경 — 출력 머리 번호 6)

```text
== 6. Optional 필드 직렬화
  java.io.NotSerializableException: java.util.Optional
```

- `Serializable` 클래스에 `Optional` 필드를 두면 Java 직렬화가 실패한다. 세션 복제·일부 캐시가 Java 직렬화를 쓰면 이 지점에서 깨진다.

## 쓰이는 자료구조·알고리즘

- **Null Object(빈 구현)** — 인터페이스의 "아무것도 안 하는" 구현을 싱글턴으로 하나 둔다(`enum NoDiscount { INSTANCE }`). 맵 조회의 기본값(`getOrDefault`)과 함께 쓰면 분기가 한 곳에 모인다.
- **Option/Maybe 타입** — "0개 또는 1개"를 담는 상자. `map`·`flatMap`으로 상자 안의 값에 함수를 적용하고, 없으면 그대로 없음. 결과 타입([16](../16-error-strategy-exceptions-vs-results/2-summary.md))에서 실패 정보를 뺀 모양이다.
- **빈 컬렉션 = 덧셈의 0** — 빈 목록은 루프·스트림·합계에서 "아무 영향 없음"으로 작동한다. 그래서 호출자 분기가 필요 없다. `List.of()`는 불변 빈 리스트를 돌려준다(OpenJDK 21 소스는 공유 인스턴스 `ImmutableCollections.EMPTY_LIST`를 돌려준다 — 같은 객체라는 것은 API 문서가 보장하는 계약은 아니다).
- **해시 맵의 null 의미 중첩** — `get`이 "키 없음"과 "값 null"을 같은 `null`로 돌려준다. `containsKey`·`getOrDefault`·null 금지 맵으로 구분한다. 해시 맵 구조는 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 반환 타입 고르기

1. 여러 개일 수 있나? → **빈 컬렉션**(`List.of()`). null 반환 금지.
2. 0개 또는 1개이고, 호출자마다 없음일 때 할 일이 다르다? → **`Optional<T>`** 반환.
3. 없음일 때 할 일이 하나로 정해져 있다? → **Null Object / Special Case**.
4. 없으면 호출 계약 위반이다(방금 만든 주문 id로 조회)? → **예외**(`OrderNotFound`). 또는 `Optional`을 돌려주고 호출자가 `orElseThrow(문맥)`.
5. 업무상 "미정"과 "0"이 다르다? → 상태를 드러내는 **타입**.

### 2. 코드 (Java 21)

```java
// 반환: 빈 컬렉션
List<Coupon> coupons(long userId) {
    return couponRepo.findByUser(userId);              // 결과 없으면 List.of()를 돌려주는 계약
}

// 반환: Optional — 호출자가 없음 처리를 고른다
Optional<Member> findByEmail(Email email) { ... }
Member m = members.findByEmail(email)
        .orElseThrow(() -> new MemberNotFound("email=" + email.masked()));

// 경계: 외부 JSON의 nullable 필드를 도메인 타입으로 한 번 바꾼다
record ProductRequest(String name, Integer discountRate) {}       // 바깥: null 가능
sealed interface DiscountPolicy permits Undecided, Rate {}
record Undecided() implements DiscountPolicy {}
record Rate(int percent) implements DiscountPolicy {
    Rate { if (percent < 0 || percent > 100) throw new IllegalArgumentException("percent=" + percent); }
}
static DiscountPolicy toPolicy(Integer raw) {
    return raw == null ? new Undecided() : new Rate(raw);         // 안쪽: null 없음
}
```

### 3. 진단

```bash
# 컬렉션·배열을 null로 돌려주는 메서드 후보
grep -rnE 'return null;' --include=*.java src/main/ | head
grep -rnB8 'return null;' --include=*.java src/main/ | grep -E '(List|Set|Map|Collection|\[\])<?.*\('

# Optional을 필드나 인자로 쓰는 곳
grep -rnE 'private .*Optional<|\(.*Optional<[^>]+> [a-z]' --include=*.java src/main/

# 검사 없는 Optional.get()
grep -rnE '\.get\(\)' --include=*.java src/main/ | grep -i optional
```

- 운영: NPE 스택 트레이스의 맨 위 프레임별 건수를 센다. 같은 메서드가 반복되면 그 메서드의 입력 경계가 null을 들이고 있다.

## 장애 시나리오와 대처

### 1. 목록 조회가 null을 반환 → 11곳 중 1곳 체크 누락으로 NPE (⚠ 커리큘럼)

- 현상: 새로 추가된 호출처(배치·리포트)에서만 간헐적 NPE.
- 보이는 형태: `Cannot invoke "java.util.List.size()" because "<local5>" is null`(실험 A). 특정 사용자(쿠폰 0개)에서만 난다.
- 원인: "없음"을 null로 돌려줘 검사 의무가 호출처마다 퍼졌다.
- 대처: 빈 컬렉션 반환으로 바꾼다(Item 54). 호출처의 null 검사는 그 뒤 지운다. 반환 계약을 문서·타입 표기(JSpecify 등)로 고정한다.

### 2. `Optional.get()` 무조건 호출 → NPE가 이름만 바뀜 (⚠ 커리큘럼)

- 현상: Optional을 도입했는데 장애 건수가 그대로다.
- 보이는 형태: `java.util.NoSuchElementException: No value present`(실험 B). 무엇이 없었는지 메시지에 없다.
- 원인: Optional을 null 검사 없는 null처럼 썼다.
- 대처: `get()` 대신 `orElseThrow(() -> new X(문맥))`·`orElse`·`map`. 정적 분석·리뷰로 검사 없는 `get()`을 막는다.

### 3. "없음"과 "0"을 구분 못 해 미입력 할인율이 0%로 저장 (⚠ 커리큘럼)

- 현상: 할인율을 "나중에 정하기로" 비워 둔 상품이 "할인 없음"으로 판매됐다. 정산·마케팅 리포트에서 미정 상품을 셀 수 없다.
- 보이는 형태: DB 컬럼 값 0. 화면·로그에 에러 없음(실험 5: `int` 필드 기본값 0).
- 원인: 원시 `int`는 "없음"을 표현할 수 없다. 기본값 0이 업무 의미("할인 0%")와 겹쳤다.
- 대처: 미정을 타입으로(`Undecided`/`Rate`), DB는 nullable 컬럼 또는 상태 컬럼. 이미 0으로 저장된 행은 생성 이력 등으로 미정 여부를 따로 판별해야 한다(되돌리기 어렵다).

### 4. Optional 필드 → 직렬화 실패

- 현상: 세션 복제나 Java 직렬화 캐시를 켜자 특정 객체에서 저장이 실패한다.
- 보이는 형태: `java.io.NotSerializableException: java.util.Optional`(실험 D).
- 원인: Optional은 반환 타입용으로 설계됐고 `Serializable`이 아니다.
- 대처: 필드는 nullable 참조 + Optional을 돌려주는 getter, 또는 상태 타입.

### 5. Map.get의 null을 "없음"으로 오해

- 현상: 설정 맵에 "값을 일부러 비워 둔" 키가 기본값으로 덮인다(또는 그 반대).
- 보이는 형태: `get(A)=null, get(B)=null`인데 `containsKey(A)=true`(실험 4).
- 원인: `HashMap`이 null 값을 허용해 두 의미가 섞였다.
- 대처: null 값을 맵에 넣지 않는다(불변 맵 `Map.of`는 거부한다). 의미가 필요하면 값 타입에 상태를 둔다.

## 핵심 문장

- "없음"을 null로 표현하면 검사 의무가 호출처마다 퍼진다. 실험에서 11곳 중 1곳만 잊어도 NPE가 났고, 빈 목록으로 바꾸자 0건이었다.
- 여러 개일 수 있는 결과는 빈 컬렉션, 0개 또는 1개인 반환값은 Optional, 없음일 때 할 일이 정해져 있으면 Null Object다.
- JDK 문서에 따르면 Optional은 반환 타입용이다. 필드에 두면 직렬화가 깨지고, `get()`을 검사 없이 부르면 NPE가 `NoSuchElementException`으로 이름만 바뀐다.
- "없음"과 "0"이 업무에서 다르면 원시 타입으로는 표현할 수 없다. 상태를 타입으로 드러낸다.
- null은 경계에서 한 번 정리하고 안쪽은 non-null로 둔다. helpful NPE 메시지는 추적을 도울 뿐 null을 없애지는 않는다.

## 관련 주제·근거

- 선행
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) — fail-fast, 에러를 정의로 없애기
  - [16-error-strategy-exceptions-vs-results](../16-error-strategy-exceptions-vs-results/2-summary.md) — 결과 타입, Special Case
  - language/08 error-handling-models — 미작성([language README](../../language/README.md))
- 후속·연결
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) — 값 객체가 생성 시점에 null을 거절한다
  - [24 types-as-invariants](../24-types-as-invariants/2-summary.md), [29 refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md)(Introduce Null Object)
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 글·문서
  - Tony Hoare, "Null References: The Billion Dollar Mistake", QCon London 2009, InfoQ 페이지 날짜 2009-08-25 <https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/>
  - Joshua Bloch, 『Effective Java』 3판 Item 54·55 — Pearson 목차로 제목 확인, 본문 미열람(Item 55 예제 코드는 저자 GitHub `effectivejava/chapter8/item55/Max.java`에서 확인) <https://github.com/jbloch/effective-java-3e-source-code>
  - Martin Fowler, 『Refactoring』 2판 "Introduce Special Case" <https://refactoring.com/catalog/introduceSpecialCase.html> · PoEAA "Special Case" <https://martinfowler.com/eaaCatalog/specialCase.html>
  - JDK 21 API 문서 `java.util.Optional`(반환 타입용, value-based), `java.util.Map`("disallow null keys and values") <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html>
  - JEP 358 "Helpful NullPointerExceptions"(JDK 14, `<local i>` 규칙) <https://openjdk.org/jeps/358> · JDK 15 릴리스 노트(기본 켜짐) <https://www.oracle.com/java/technologies/javase/15-relnote-issues.html>
  - JSpecify 1.0.0 <https://jspecify.dev/docs/start-here/>
- 실험 목록 (코드: scratchpad `sd/15/e18/Absence.java`, JDK 21.0.12 eclipse-temurin `--cpus=2`, `java Absence.java`)
  - A null 반환 vs 빈 목록, 호출처 11곳 중 1곳 누락 — NPE 1 vs 0
  - B `Optional.get()`·`orElseThrow`·`orElse`
  - C Null Object 할인
  - 4·5 `Map.get` null 의미 중첩, `Map.of` null 거부, `int` 기본값 0 vs `Integer` null
  - D Optional 필드 직렬화 실패
  - E helpful NPE 메시지 — javac 기본 / `-g` / `-XX:-ShowCodeDetailsInExceptionMessages`
