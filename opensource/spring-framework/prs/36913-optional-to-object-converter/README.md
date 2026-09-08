# PR #36913 — Fix OptionalToObjectConverter applicability check

## 0. 정향

이 문서는 `spring-core` 변환 시스템의 `OptionalToObjectConverter#matches()` 수정
PR을 처음부터 이해하기 위한 해설이다. `canConvert`가 왜 값 없이 동작하는지, 제네릭
와일드카드가 판별에 어떻게 흘러드는지가 핵심이라, 층 개념 문서
`../../concepts/compile-runtime-layers/compile-runtime-layers.md`를 먼저 읽으면 좋다. 다 읽으면 "왜
`Optional<Integer> -> LocalDate`가 true로 과대보고됐는가"와 "와일드카드 테스트가 왜
따로 필요한가"를 설명할 수 있어야 한다.

## 1. 배경 — 변환 시스템에서 이 컨버터의 자리

Spring의 타입 변환은 `ConversionService`라는 단일 진입점 뒤에 수많은 컨버터가
등록된 구조다. 각 컨버터는 "나는 어떤 타입쌍을 다룬다"를 선언하고, 엔진이 소스·대상
`TypeDescriptor`(선언 메타데이터 카드)에 맞는 컨버터를 고른다. 여기서 두 질문이
분리된다: `canConvert`는 "갈 수 있는 컨버터가 등록돼 있나"(값 없이, 카드만),
`convert`는 "실제 값을 바꿔라"(값 등장).

`OptionalToObjectConverter`는 `Optional<X>`를 벗겨 `X`(또는 그 변환 결과)로 만드는
컨버터다. 조건부 컨버터(`ConditionalGenericConverter`)라서 `matches()`로 "이
타입쌍에 내가 적용되는가"를 스스로 판별한다 — 이 판별이 이번 PR의 무대다.

## 2. 수정 전 동작 방식 — 원소 타입을 못 보는 판별

수정 전 `matches()`는 한 줄이었다:

```java
return ConversionUtils.canConvertElements(sourceType.getElementTypeDescriptor(), targetType, this.conversionService);
```

`canConvertElements`는 원소 타입이 null이면 "maybe"로 true를 돌려준다. 그런데
`TypeDescriptor#getElementTypeDescriptor()`는 컬렉션·배열·스트림용이라 Optional에는
원소를 주지 못하고 항상 null이었다. 결과적으로 이 판별은 **원소가 무엇이든 항상
true** — 판별이 아니라 통과였다.

## 3. 무엇이 문제였나 — canConvert와 convert의 어긋남

`Optional<Integer>`를 `LocalDate`로 바꿀 수 있느냐고 물으면, 정답은 "없다"다
(`Integer -> LocalDate` 컨버터가 등록돼 있지 않다). 그런데 수정 전에는 `canConvert`가
true를 돌려주고, 정작 `convert`를 실행하면 변환기를 못 찾아 실패했다. "할 수
있다고 답해 놓고 시키면 못 하는" 계약 불일치다. `canConvert`로 분기하는 호출자
(바인딩, 조건부 로직)는 이 과대보고 때문에 잘못된 경로를 탄다.

## 4. 수정 해설 — 원소 타입을 직접 꺼내되, 모르면 관대하게

수정은 원소 타입을 `ResolvableType`으로 직접 꺼낸다:

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

두 갈래다. 원소 타입이 **해석되면**(`Optional<Integer>`의 Integer, `Optional<?
extends Number>`의 상한 Number) 그 타입 기준으로 "원소 -> 대상 변환기가 있는가"를
판별한다. **해석 안 되면**(raw `Optional`, `Optional<?>`, 미해석 `Optional<T>`)
막을 근거가 없으므로 관대하게 true를 유지한다 — 모른다고 거부하면 정당한 변환까지
막기 때문이다.

와일드카드의 갈림은 `ResolvableType.resolveBounds`가 만든다: 상한이 `Object`면
정보 없음으로 보고 null(-> 관대), `Number`처럼 구체적이면 그 타입을 돌려준다(-> 실제
판별 기준). 이 판별 전체가 값 없이, 선언 메타데이터만으로 이루어진다.

리뷰 과정에서 확인된 사실 하나를 기록해 둔다: 해석 실패 가드(`resolve() == null ->
true`)는 **동작 중립**이다. 가드가 없어도 미상 원소는 `Object`로 떨어지고,
`canConvertElements`의 assignable-폴백(`Object`는 무엇이든 담을 수 있다 -> maybe)이
어차피 true를 낸다. 가드의 가치는 동작 변경이 아니라 의도의 문서화와 불필요한
객체 생성 회피다.

## 5. 검증 — 테스트가 각각 고정하는 것

리뷰어(sbrannen)가 요청한 것은 raw에 더해 `Optional<?>`와 `Optional<? extends
Number>` 커버였고, 리뷰 반영 후 테스트는 다음을 고정한다. 와일드카드 타입은 코드로
직접 못 만들어 테스트 픽스처 필드의 선언에서 `TypeDescriptor(Field)`로 얻는다.

관대 계약 세 형제: raw `Optional`, `Optional<?>`, 미해석 `Optional<T>` 모두
변환기 없는 대상(`LocalDate`)에도 true — "모르면 막지 않는다"를 고정한다.

상한 판별: `Optional<? extends Number>`는 `-> String` true(그리고
`convert(Optional.of(42)) == "42"`까지 end-to-end), `-> LocalDate` false +
`convert()`도 `ConverterNotFoundException` — canConvert와 convert의 일관성 회복이
이 PR의 본질임을 그대로 보여준다.

여기서 테스트 설계 교훈이 하나 나왔다. `-> String` 방향의 긍정 단언은 fallback
(`ObjectToString`) 때문에 상한 해석이 깨져도 통과한다 — **판별력은 부정 단언
(`-> LocalDate` false)이 담당한다.** 통과가 쉬운 방향의 긍정 단언은 회귀 가드가
되기 어렵다는 일반 원칙의 실례다.

## 6. 상태와 교훈

2026-08-15 기준 리뷰 반영(테스트 4건 추가, 최신 main rebase) 후 재리뷰 대기 중이다.

교훈 둘. 첫째, `canConvert`류의 "가능성 질의"는 실제 실행과 계약이 어긋나기 쉽다 —
질의와 실행을 같은 근거(여기서는 원소 타입)로 판단하게 맞추는 것이 수정의 본질이다.
둘째, 제네릭 판별 코드는 구체 타입·raw·와일드카드·타입 변수가 **서로 다른 해석
경로**를 타므로, 같은 결과를 내는 케이스라도 경로별 테스트가 필요하다 — 리뷰어가
와일드카드를 콕 집어 요청한 이유다.

---

연관 ko-docs (모듈 지도): `spring-core/02-타입-변환-conversion.md`
