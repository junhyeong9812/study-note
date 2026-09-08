# PR #36913 — 테스트 해설 (테스트 하나하나)

> PR #36913 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 `DefaultConversionServiceTests`의 중첩 클래스 `OptionalConversionTests`에 5건을
추가했다. 판별 기준은 수정 전 `matches()`가 **입력과 무관하게 항상 true**였다는 사실이다.

```java
return ConversionUtils.canConvertElements(sourceType.getElementTypeDescriptor(), targetType, this.conversionService);
```

`getElementTypeDescriptor()`가 Optional에는 항상 null을 주고, `canConvertElements`는 null
원소 타입을 "maybe"로 보아 true를 돌려준다. 따라서 **true를 기대하는 단언은 fix 전에도
전부 통과하고, false를 기대하는 단언만 red가 된다.** 5건 중 red 2건, 가드 3건이다.

## 1. raw Optional 관대 계약 — 항상 green (양성 가드)

첫 테스트는 제네릭 정보가 아예 없는 raw `Optional`이 새 판별식에서도 막히지 않는지를
고정한다.

```java
@Test  // raw Optional: no element type information, so the converter remains permissive
void canConvertRawOptionalRemainsPermissive() {
	assertThat(conversionService.canConvert(rawOptionalType, TypeDescriptor.valueOf(LocalDate.class))).isTrue();
}
```

- **주장**: 제네릭 정보가 아예 없는 raw `Optional`은 변환기가 없는 대상(`LocalDate`)에
  대해서도 `canConvert`가 true다.
- **fix 전 green인 이유**: 수정 전에는 모든 입력이 true였으므로 당연히 통과한다.
- **존재 이유는 fix 후**: 새 판별식이 "모르면 막지 않는다"는 관대 규칙을 지키는지
  고정한다. `resolve() == null` 가드가 지워지거나 `elementType`이 null일 때 false를
  돌려주는 방향으로 잘못 조여지면 이 테스트가 먼저 깨진다. 과잉 필터링 방지의 첫 축이다.
- **대상 타입 선택의 의미**: 굳이 `LocalDate`를 쓴 이유는 `DefaultConversionService`에
  `Object -> LocalDate` 변환기가 없기 때문이다. `String`처럼 fallback이 있는 대상을 골랐다면
  관대 여부와 무관하게 true가 나와 아무것도 구별하지 못한다.

## 2. Optional<?> 관대 계약 — 항상 green (양성 가드)

두 번째 테스트는 같은 관대 규칙을 상한 없는 와일드카드 경로에서 확인한다.

```java
@Test  // Optional<?>: the Object upper bound resolves to null, so the converter remains permissive
void canConvertOptionalWithUnboundedWildcardRemainsPermissive() throws Exception {
	TypeDescriptor unboundedWildcardOptionalType = optionalTypeFor("unboundedWildcardOptional");
	assertThat(conversionService.canConvert(unboundedWildcardOptionalType, TypeDescriptor.valueOf(LocalDate.class))).isTrue();
}
```

- **주장**: 상한이 없는 와일드카드 `Optional<?>`도 관대하게 true다.
- **fix 전 green인 이유**: 1번과 같다.
- **존재 이유는 fix 후**: raw와 와일드카드는 **해석 경로가 다르다**. raw는 제네릭 자체가
  없고, `Optional<?>`는 제네릭은 있지만 `ResolvableType.resolveBounds`가 상한 `Object`를
  "정보 없음"으로 판정해 null로 떨어뜨린다. 결과값이 같아도 도달 경로가 다르므로 각각
  고정해야 한다는 것이 리뷰어(sbrannen)가 와일드카드 커버를 콕 집어 요청한 이유다.

## 3. 미해석 타입 변수 관대 계약 — 항상 green (양성 가드)

세 번째 테스트는 관대 계약의 마지막 경로인 미해석 타입 변수를 맡는다.

```java
@Test  // Optional<T> with an unresolved type variable also remains permissive
void canConvertOptionalWithUnresolvedTypeVariableRemainsPermissive() throws Exception {
	TypeDescriptor typeVariableOptionalType =
			new TypeDescriptor(TypeVariableHolder.class.getDeclaredField("typeVariableOptional"));
	assertThat(conversionService.canConvert(typeVariableOptionalType, TypeDescriptor.valueOf(LocalDate.class))).isTrue();
}
```

- **주장**: 타입 변수 `T`가 실인자로 채워지지 않은 `Optional<T>`도 관대하게 true다.
- **fix 전 green인 이유**: 1·2번과 같다.
- **fixture가 흉내 내는 것**: `TypeVariableHolder<T>`는 제네릭 클래스의 필드가 **바인딩
  없이** 관측되는 상황을 만든다. 실제로는 제네릭 컨테이너 타입의 프로퍼티를 상위 타입
  정보 없이 내성(introspection)할 때 이런 미해석 `T`가 흘러든다.
- **역할**: 관대 계약 세 형제(raw, 와일드카드, 타입 변수)의 마지막 조각. 셋을 함께 두면
  "원소 타입을 모르는 모든 경로"가 하나의 규칙 아래 있음을 명시한다.

## 4. 상한 와일드카드 판별 — red

네 번째 테스트부터 실제 판별이 시작된다. 상한이 구체적인 와일드카드에서 `canConvert`와
`convert`가 같은 답을 내는지 네 단언으로 확인한다.

```java
@Test  // Optional<? extends Number>: applicability is decided against the Number upper bound
void canConvertOptionalWithBoundedWildcardReflectsUpperBound() throws Exception {
	TypeDescriptor boundedWildcardOptionalType = optionalTypeFor("boundedWildcardOptional");
	TypeDescriptor localDateType = TypeDescriptor.valueOf(LocalDate.class);

	assertThat(conversionService.canConvert(boundedWildcardOptionalType, TypeDescriptor.valueOf(String.class))).isTrue();
	assertThat(conversionService.convert(Optional.of(42), boundedWildcardOptionalType,
			TypeDescriptor.valueOf(String.class))).isEqualTo("42");
	assertThat(conversionService.canConvert(boundedWildcardOptionalType, localDateType)).isFalse();
	assertThatExceptionOfType(ConverterNotFoundException.class)
			.isThrownBy(() -> conversionService.convert(Optional.of(42), boundedWildcardOptionalType, localDateType));
}
```

- **주장**: 상한이 구체적인 `Optional<? extends Number>`는 그 상한 `Number`를 기준으로
  판별된다. `Number -> String`은 가능하므로 true이자 실제 변환도 성공하고,
  `Number -> LocalDate`는 불가능하므로 false이자 실제 변환도 `ConverterNotFoundException`이다.
- **fix 전**: 셋째 단언에서 red다. 수정 전 `matches()`는 항상 true였으므로
  `canConvert(..., LocalDate)`가 true를 돌려주고 `isFalse()` 단언이 실패한다. 앞의 두
  단언은 fix 전에도 통과한다. 마지막 예외 단언은 **fix 전에는 red다** (2026-08-27 실측
  정정 — 이전 판본은 "예외 타입이 같다"고 적었으나 틀렸다). 수정 전에는 컨버터가 선택된
  뒤 **내부 위임에서** 변환기를 못 찾아 `ConverterNotFoundException`이 나고, 그것을
  `ConversionUtils.invokeConverter`의 `catch (Throwable)`(L46-48)이
  `ConversionFailedException`으로 감싸 바깥에 던진다. 수정 후에는 애초에 선택되는
  컨버터가 없어 `ConverterNotFoundException`이 그대로 나온다. 두 예외는
  `ConversionException`을 각각 상속한 형제라 `assertThatExceptionOfType(
  ConverterNotFoundException.class)`는 수정 전 실패한다 — 셋째 줄과 함께 판별력을
  갖는다. 실측 근거는 analysis.md §3.
- **판별력에 관한 주의**: `-> String` 방향의 긍정 단언은 상한 해석이 깨져도 통과한다.
  `ObjectToStringConverter` fallback이 어떤 타입이든 String으로 보내 주기 때문이다.
  README에 기록된 테스트 설계 교훈이 이것이다 — **통과가 쉬운 방향의 긍정 단언은 회귀
  가드가 되기 어렵고, 실질 판별은 부정 단언이 담당한다.** 그럼에도 `-> String` 두 줄을
  남긴 이유는 판별이 아니라 무회귀 확인이다. 새 판별식이 정당한 변환까지 막지 않음을
  end-to-end로 보인다.
- **fixture가 흉내 내는 것**: 와일드카드 타입은 자바 코드로 직접 인스턴스화할 수 없다.
  `Optional<? extends Number>`라는 타입 자체를 만들 방법이 없으므로, 필드로 **선언해
  두고** `new TypeDescriptor(Field)`로 그 선언 메타데이터를 읽어 온다. 이것이 실제
  프레임워크가 하는 일과 정확히 같다 — 변환은 값이 아니라 선언에서 타입을 얻는다.

## 5. 구체 원소 타입 판별 — red

다섯 번째 테스트가 이 PR의 본체 주장을 담는다. 원소 타입이 확정된 `Optional<Integer>`에서
과대보고가 사라졌는지를 본다.

```java
@Test
void canConvertOptionalToObjectReflectsContainedElementType() {
	TypeDescriptor integerOptionalType =
			new TypeDescriptor(ResolvableType.forClassWithGenerics(Optional.class, Integer.class), null, null);
	TypeDescriptor localDateType = TypeDescriptor.valueOf(LocalDate.class);

	// Integer -> String is convertible
	assertThat(conversionService.canConvert(integerOptionalType, TypeDescriptor.valueOf(String.class))).isTrue();

	// Integer -> LocalDate is not convertible, so canConvert must not over-report...
	assertThat(conversionService.canConvert(integerOptionalType, localDateType)).isFalse();
	// ...and must stay consistent with convert(): no converter is selected
	assertThatExceptionOfType(ConverterNotFoundException.class)
			.isThrownBy(() -> conversionService.convert(Optional.of(42), integerOptionalType, localDateType));

	// An Optional with an unknown element type remains permissive
	assertThat(conversionService.canConvert(rawOptionalType, localDateType)).isTrue();
}
```

- **주장**: 이 PR의 본체 주장이다. `Optional<Integer>`처럼 원소 타입이 확정된 경우
  `canConvert`는 그 원소 타입 기준으로 답해야 하며, `convert`와 일관돼야 한다.
- **fix 전**: 둘째 단언(`isFalse()`)에서 red다. PR 본문이 든 재현 예시가 그대로
  테스트가 된 것이다.
- **한 테스트에 네 단언을 모은 이유**: 이 건은 "계약 불일치"라는 하나의 이야기를
  순서대로 서술한다. 갈 수 있는 방향은 true, 갈 수 없는 방향은 false, 그리고 그 false가
  `convert`의 실제 실패와 짝을 이룬다는 것 — `canConvert`가 예언이고 `convert`가 실행인데
  둘이 어긋나 있었다는 문제 정의를 단언 배치로 재현한다. 마지막 줄의 raw 확인은 1번
  테스트와 중복이지만, "조이면서 관대함을 잃지 않았다"를 같은 시야 안에서 보이려는
  배치다.
- **`ResolvableType.forClassWithGenerics`를 쓰는 이유**: 4번과 달리 구체 타입 인자는
  코드로 직접 조립할 수 있으므로 필드 선언 없이 만든다. 즉 이 파일의 두 fixture 방식
  (필드 선언 읽기 / 코드 조립)은 만들 수 있는 타입인지 아닌지에 따라 갈린다.

## fixture

새로 추가된 fixture는 필드 둘, 중첩 클래스 하나, 헬퍼 하나다.

```java
@SuppressWarnings("unused")
private Optional<?> unboundedWildcardOptional;

@SuppressWarnings("unused")
private Optional<? extends Number> boundedWildcardOptional;

private static TypeDescriptor optionalTypeFor(String fieldName) throws Exception {
	return new TypeDescriptor(OptionalConversionTests.class.getDeclaredField(fieldName));
}

@SuppressWarnings("unused")
private static class TypeVariableHolder<T> {

	Optional<T> typeVariableOptional;
}
```

세 fixture 모두 **값이 아니라 선언을 제공하려고** 존재한다. 필드에는 아무 값도 대입하지
않고(그래서 `@SuppressWarnings("unused")`), 읽는 것은 오직 `Field` 객체가 들고 있는
제네릭 선언 정보다. 이것이 이 PR의 검증 대상과 정확히 맞물린다 —
`matches()`는 값 없이 선언 메타데이터만으로 판별하는 함수이므로, 테스트도 값 없이
선언만으로 입력을 구성해야 실제 판별 경로를 밟는다.

기존 fixture인 `conversionService`(테스트 클래스 필드의 `new DefaultConversionService()`)와
`rawOptionalType` 상수는 그대로 재사용한다. `DefaultConversionService`를 쓴다는 것은 실제
등록 표를 그대로 쓴다는 뜻이라, "`Integer -> LocalDate` 변환기가 없다"는 전제가 mock이
아니라 실제 기본 설정에서 나온다. 이 PR은 mock을 전혀 쓰지 않는데, 흉내 낼 협력자가
없기 때문이다 — 판별에 필요한 것은 실제 컨버터 레지스트리의 내용 그 자체다.

## 실측·역할 요약

fix 전 기준으로 정리하면 다음과 같다.

| 분류 | 건수 | 해당 테스트 |
|---|---|---|
| red | 2 | 4(셋째 단언), 5(둘째 단언) |
| 양성 가드 | 3 | 1, 2, 3 |

역할은 두 갈래다. red 2건이 "`canConvert`가 과대보고했다"는 결함을 각각 구체 타입과
상한 와일드카드 경로에서 재현하고, 가드 3건이 "원소 타입을 모르는 입력은 여전히 통과한다"는
관대 계약을 고정해 과잉 필터링 회귀를 막는다. README가 기록한 대로 관대 가드는 **동작
중립**이다 — 가드가 없어도 미상 원소는 `Object`로 떨어져 어차피 true가 되므로, 이 3건의
가치는 동작 보증보다 의도의 명시와 경로별 커버리지에 있다.
