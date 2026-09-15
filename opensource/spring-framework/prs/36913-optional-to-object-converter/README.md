# PR #36913 — Fix OptionalToObjectConverter applicability check

## 0. 정향

이 문서는 `spring-core` 변환 시스템의 `OptionalToObjectConverter#matches()` 수정 PR을 처음부터 이해하기 위한 해설이다.\
`canConvert`가 왜 값 없이 동작하는지, 제네릭 와일드카드가 판별에 어떻게 흘러드는지가 핵심이라, 층 개념 문서 `../../concepts/compile-runtime-layers/compile-runtime-layers.md`를 먼저 읽으면 좋다.\
다 읽으면 "왜 `Optional<Integer> -> LocalDate`가 true로 과대보고됐는가"와 "와일드카드 테스트가 왜 따로 필요한가"를 설명할 수 있어야 한다.

## 1. 배경 — 변환 시스템에서 이 컨버터의 자리

Spring의 타입 변환은 `ConversionService`라는 단일 진입점 뒤에 수많은 컨버터가 등록된 구조다.\
각 컨버터는 "나는 어떤 타입쌍을 다룬다"를 선언하고, 엔진이 소스·대상 `TypeDescriptor`(선언 메타데이터 카드)에 맞는 컨버터를 고른다.

> **ConversionService** — Spring의 타입 변환 단일 진입점 인터페이스. 등록된 컨버터 표를 대신 뒤져 준다.\
> 예: `DefaultConversionService`가 기본 컨버터들을 전부 등록한 구현체다.

> **TypeDescriptor** — "이 자리의 타입은 무엇인가"를 담은 선언 메타데이터 카드. 클래스만이 아니라 제네릭 인자·애노테이션까지 들고 다닌다.\
> 예: 필드 `Optional<? extends Number> boundedWildcardOptional` 선언에서 만든 카드는 상한 `Number`를 기억하고 있다.

여기서 두 질문이 분리된다.\
`canConvert`는 "갈 수 있는 컨버터가 등록돼 있나"(값 없이, 카드만), `convert`는 "실제 값을 바꿔라"(값 등장)다.

`OptionalToObjectConverter`는 `Optional<X>`를 벗겨 `X`(또는 그 변환 결과)로 만드는 컨버터다.\
조건부 컨버터(`ConditionalGenericConverter`)라서 `matches()`로 "이 타입쌍에 내가 적용되는가"를 스스로 판별한다 — 이 판별이 이번 PR의 무대다.

> **ConditionalGenericConverter** — 등록만으로 무조건 선택되지 않고, `matches()`로 자기 적용 여부를 스스로 답하는 컨버터.\
> 예: `OptionalToObjectConverter`는 `(Optional, Object)` 쌍에 등록돼 있지만, 실제 선택 여부는 `matches()`가 정한다.

## 2. 수정 전 동작 방식 — 원소 타입을 못 보는 판별

수정 전 `matches()`는 한 줄이었다.

```java
return ConversionUtils.canConvertElements(sourceType.getElementTypeDescriptor(), targetType, this.conversionService);
```

`canConvertElements`는 원소 타입이 null이면 "maybe"로 true를 돌려준다.\
그런데 `TypeDescriptor#getElementTypeDescriptor()`는 컬렉션·배열·스트림용이라 Optional에는 원소를 주지 못하고 항상 null이었다.\
결과적으로 이 판별은 **원소가 무엇이든 항상 true** — 판별이 아니라 통과였다.

> **getElementTypeDescriptor()** — 배열 컴포넌트 타입 또는 Collection 원소 타입을 카드로 돌려주고, 아니면 null을 주는 메서드.\
> 예: `List<String>` 카드에는 `String` 카드를 주지만, `Optional<Integer>` 카드에는 null을 준다.

호출이 어디서 갈리는지를 세로로 따라가면 이렇다.

```text
canConvert(Optional<Integer> 카드, LocalDate 카드)  질의 — 값 없이 카드만
        |
        v
matches(sourceType, targetType)                     이 컨버터가 선택될지 스스로 판별
        |
        v
sourceType.getElementTypeDescriptor()               컬렉션/배열/스트림용 -> Optional 은 대상 밖
        |
        v
원소 카드 = null                                    여기서 원소 타입 정보가 사라진다
        |
        v
canConvertElements(null, LocalDate 카드, cs)        원소가 null 이면 "maybe"
        |
        v
return true                                         입력과 무관하게 항상 이 값
```

원소 카드가 null로 고정되므로, 마지막 분기는 늘 같은 갈래만 탄다.

## 3. 무엇이 문제였나 — canConvert와 convert의 어긋남

`Optional<Integer>`를 `LocalDate`로 바꿀 수 있느냐고 물으면, 정답은 "없다"다 (`Integer -> LocalDate` 컨버터가 등록돼 있지 않다).\
그런데 수정 전에는 `canConvert`가 true를 돌려주고, 정작 `convert`를 실행하면 변환기를 못 찾아 실패했다.\
"할 수 있다고 답해 놓고 시키면 못 하는" 계약 불일치다.\
`canConvert`로 분기하는 호출자(바인딩, 조건부 로직)는 이 과대보고 때문에 잘못된 경로를 탄다.

> **과대보고(over-reporting)** — 실제로는 불가능한데 질의에 "가능"이라고 답하는 것. 호출자가 그 답을 믿고 분기하면 엉뚱한 경로를 탄다.\
> 예: `canConvert(Optional<Integer>, LocalDate)`가 true를 돌려주고 `convert()`는 실패한 것.

## 4. 수정 해설 — 원소 타입을 직접 꺼내되, 모르면 관대하게

수정은 원소 타입을 `ResolvableType`으로 직접 꺼낸다.

```java
ResolvableType elementType = sourceType.getResolvableType().getGeneric();
if (elementType.resolve() == null) {
    // Unknown Optional element type (raw Optional, wildcard, or unresolved
    // type variable): remain permissive.
    return true;
}
TypeDescriptor sourceElementType = new TypeDescriptor(elementType, null, null);
return ConversionUtils.canConvertElements(sourceElementType, targetType, this.conversionService);
```

> **ResolvableType** — 자바 제네릭 타입을 다룰 수 있게 감싼 Spring의 타입 표현. 제네릭 인자를 꺼내고 실제 `Class`로 해석하는 일을 맡는다.\
> 예: `Optional<Integer>`의 `getGeneric()`은 `Integer`를 가리키는 `ResolvableType`을 준다.

두 갈래다.\
원소 타입이 **해석되면**(`Optional<Integer>`의 Integer, `Optional<? extends Number>`의 상한 Number) 그 타입 기준으로 "원소 -> 대상 변환기가 있는가"를 판별한다.\
**해석 안 되면**(raw `Optional`, `Optional<?>`, 미해석 `Optional<T>`) 막을 근거가 없으므로 관대하게 true를 유지한다 — 모른다고 거부하면 정당한 변환까지 막기 때문이다.

> **raw 타입(raw type)** — 제네릭 인자를 적지 않은 타입. 선언에 인자가 없으니 원소 타입 정보도 없다.\
> 예: `Optional<Integer>`가 아니라 그냥 `Optional`로 쓴 경우.

> **와일드카드 상한(upper bound)** — `? extends X`에서 `X` 자리. 그 자리에 올 수 있는 타입의 천장을 말한다.\
> 예: `Optional<? extends Number>`의 상한은 `Number`이고, `Optional<?>`의 상한은 `Object`다.

와일드카드의 갈림은 `ResolvableType.resolveBounds`가 만든다.\
상한이 `Object`면 정보 없음으로 보고 null(-> 관대), `Number`처럼 구체적이면 그 타입을 돌려준다(-> 실제 판별 기준).\
이 판별 전체가 값 없이, 선언 메타데이터만으로 이루어진다.

같은 입력에 대해 수정 전후 답이 어떻게 갈리는지 나란히 두면 이렇다.

```text
수정 전 matches()                           수정 후 matches()
+--------------------------------------+    +--------------------------------------+
| Optional<Integer>   -> LocalDate : T |    | Optional<Integer>   -> LocalDate : F |
| Optional<? ext Num> -> LocalDate : T |    | Optional<? ext Num> -> LocalDate : F |
| Optional<? ext Num> -> String    : T |    | Optional<? ext Num> -> String    : T |
| raw Optional        -> LocalDate : T |    | raw Optional        -> LocalDate : T |
| Optional<?>         -> LocalDate : T |    | Optional<?>         -> LocalDate : T |
| Optional<T> 미해석  -> LocalDate : T |    | Optional<T> 미해석  -> LocalDate : T |
+--------------------------------------+    +--------------------------------------+
  원소 카드가 늘 null -> 전부 true          원소가 해석되면 판별, 모르면 관대 유지
```

아는 것은 판별하고 모르는 것만 통과시키도록, 바뀐 줄은 위 세 줄뿐이다.

리뷰 과정에서 확인된 사실 하나를 기록해 둔다.\
해석 실패 가드(`resolve() == null -> true`)는 **동작 중립**이다.\
가드가 없어도 미상 원소는 `Object`로 떨어지고, `canConvertElements`의 assignable-폴백(`Object`는 무엇이든 담을 수 있다 -> maybe)이 어차피 true를 낸다.\
가드의 가치는 동작 변경이 아니라 의도의 문서화와 불필요한 객체 생성 회피다.

> **폴백(fallback)** — 앞의 판정이 결론을 못 내렸을 때 뒤에서 받아 주는 대비 경로.\
> 예: 원소가 `Object`로 떨어졌을 때 "무엇이든 담을 수 있다"고 보고 true를 내는 assignable 검사.

## 5. 검증 — 테스트가 각각 고정하는 것

리뷰어(sbrannen)가 요청한 것은 raw에 더해 `Optional<?>`와 `Optional<? extends Number>` 커버였고, 리뷰 반영 후 테스트는 다음을 고정한다.\
와일드카드 타입은 코드로 직접 못 만들어 테스트 픽스처 필드의 선언에서 `TypeDescriptor(Field)`로 얻는다.

> **테스트 픽스처(fixture)** — 테스트가 입력으로 쓰려고 미리 마련해 둔 고정 재료.\
> 예: 값은 대입하지 않고 선언만 해 둔 필드 `private Optional<? extends Number> boundedWildcardOptional;`.

관대 계약 세 형제: raw `Optional`, `Optional<?>`, 미해석 `Optional<T>` 모두 변환기 없는 대상(`LocalDate`)에도 true — "모르면 막지 않는다"를 고정한다.

상한 판별: `Optional<? extends Number>`는 `-> String` true(그리고 `convert(Optional.of(42)) == "42"`까지 end-to-end), `-> LocalDate` false + `convert()`도 `ConverterNotFoundException` — canConvert와 convert의 일관성 회복이 이 PR의 본질임을 그대로 보여준다.

> **end-to-end** — 중간 단계만 보지 않고 입력에서 최종 결과까지 실제로 관통해 확인하는 것.\
> 예: `canConvert`가 true인지만 보지 않고 `convert(Optional.of(42))`가 실제로 `"42"`를 내는지까지 단언한 것.

여기서 테스트 설계 교훈이 하나 나왔다.\
`-> String` 방향의 긍정 단언은 fallback(`ObjectToString`) 때문에 상한 해석이 깨져도 통과한다 — **판별력은 부정 단언(`-> LocalDate` false)이 담당한다.**\
통과가 쉬운 방향의 긍정 단언은 회귀 가드가 되기 어렵다는 일반 원칙의 실례다.

> **회귀 가드(regression guard)** — 한 번 고친 결함이 되돌아오면 반드시 실패하도록 세워 두는 테스트.\
> 예: 관대 계약 3건은 새 판별식이 지나치게 조여지면 먼저 깨지도록 놓인 가드다.

## 6. 상태와 교훈

2026-08-15 기준 리뷰 반영(테스트 4건 추가, 최신 main rebase) 후 재리뷰 대기 중이다.

교훈 둘.\
첫째, `canConvert`류의 "가능성 질의"는 실제 실행과 계약이 어긋나기 쉽다 — 질의와 실행을 같은 근거(여기서는 원소 타입)로 판단하게 맞추는 것이 수정의 본질이다.\
둘째, 제네릭 판별 코드는 구체 타입·raw·와일드카드·타입 변수가 **서로 다른 해석 경로**를 타므로, 같은 결과를 내는 케이스라도 경로별 테스트가 필요하다 — 리뷰어가 와일드카드를 콕 집어 요청한 이유다.

---

연관 ko-docs (모듈 지도): `spring-core/02-타입-변환-conversion.md`
