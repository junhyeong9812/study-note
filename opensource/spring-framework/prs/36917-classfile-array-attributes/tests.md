# PR #36917 — 테스트 해설 (테스트 하나하나)

> PR #36917 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 `spring-core/src/test/java24/`에 테스트 클래스 하나를 새로 만들고 그 안에 두 건을
넣었다. 한 건은 결함을 재현하는 red이고, 다른 한 건은 결함이 눈에 띄지 않던 이유를
고정하는 가드다. 이 문서는 그 둘을 각각 해설하고, 마지막에 이 PR이 거절된 사실과
테스트의 관계를 정리한다.

## 1. 비어 있지 않은 원시 배열 어트리뷰트 — red

첫 테스트는 여덟 가지 원시 배열 어트리뷰트를 한 메서드 안에서 차례로 읽어 선언 타입과의 일치를 확인한다.

```java
@Test
void parsesNonEmptyPrimitiveArrayAttributes() throws Exception {
	MergedAnnotation<?> annotation = readAnnotation(WithArrays.class);
	assertThat(annotation.getValue("byteValue")).contains(new byte[] { 1 });
	assertThat(annotation.getValue("shortValue")).contains(new short[] { 2 });
	assertThat(annotation.getValue("intValue")).contains(new int[] { 3 });
	assertThat(annotation.getValue("longValue")).contains(new long[] { 4 });
	assertThat(annotation.getValue("booleanValue")).contains(new boolean[] { true });
	assertThat(annotation.getValue("charValue")).contains(new char[] { 'c' });
	assertThat(annotation.getValue("doubleValue")).contains(new double[] { 5.0 });
	assertThat(annotation.getValue("floatValue")).contains(new float[] { 6.0f });
}
```

- **주장**: 여덟 가지 원시 배열 어트리뷰트를 ClassFile 리더로 읽으면 전부 **선언된
  원시 배열 타입 그대로** 값이 나온다. 즉 `byte[] byteValue()`는 `byte[]`로 나와야 하고
  `Byte[]`로 나오면 안 된다.
- **fix 전 결과와 이유**: red다. 판별 근거는 diff의 프로덕션 쪽이다. 수정 전
  `parseArrayValue()`는 `OfInt`/`OfLong`/`OfDouble` 세 분기만 갖고 나머지를 `default`로
  떨어뜨렸고, 그 분기는 `toArray(...)`를 `Object[]`로 캐스팅하므로 결과가 반드시 참조 배열이
  된다. 그러면 `MergedAnnotation.getValue(...)`가 값을 꺼낼 때
  `TypeMappedAnnotation`의 `adaptForAttribute()` 마지막 관문
  (`if (!attributeType.isInstance(value))`)에 걸려 `IllegalStateException`이 던져진다.
  단언이 어긋나서 실패하는 것이 아니라 **첫 `byteValue` 줄에서 예외로 중단**되는 형태의
  red다. PR 본문도 같은 예외 문구를 인용하며 "현재 코드에서 실패하고 수정 후 통과한다"고
  적고 있다.
- **여덟 줄 중 어디가 red인가**: 여덟 줄이 모두 red는 아니다. `intValue`, `longValue`,
  `doubleValue`는 수정 전에도 원시 배열로 나왔으므로 그 세 줄만 따로 떼면 가드다. 같은
  메서드 안에 red 다섯 줄과 가드 세 줄이 섞여 있는 배치이며, 그 섞임 자체가 "일부 원시
  타입만 특별 취급되고 나머지는 빠졌다"는 비대칭을 한 화면에 보여 주는 장치다. 다만
  단언이 순차 실행이므로 첫 red 줄에서 멈춘다.
- **fix 후**: `OfByte`/`OfShort`/`OfChar`/`OfBoolean`/`OfFloat` 다섯 `case`가 각각 원시
  배열을 직접 채워 반환하므로 여덟 줄이 모두 통과한다.
- **형식 디테일**: 단언에 `contains(...)`를 쓴 것은 `MergedAnnotation.getValue(String)`의
  반환 타입이 `Optional<Object>`이기 때문이다. AssertJ의 `OptionalAssert.contains`는 값
  비교에 배열을 인지하는 표준 비교 전략을 쓰므로, 원시 배열끼리의 내용 비교가 성립한다.

## 2. 빈 원시 배열 어트리뷰트 — 항상 green (가드)

둘째 테스트는 원소가 없는 경우를 따로 떼어, 이 결함이 눈에 띄지 않던 이유를 코드로 남긴다.

```java
@Test
void parsesEmptyPrimitiveArrayAttributes() throws Exception {
	MergedAnnotation<?> annotation = readAnnotation(WithEmptyArrays.class);
	assertThat(annotation.getValue("byteValue")).contains(new byte[] {});
	assertThat(annotation.getValue("floatValue")).contains(new float[] {});
}
```

- **주장**: 원소가 하나도 없는 원시 배열 어트리뷰트도 선언 타입의 빈 배열로 나온다.
- **fix 전 green인 이유**: 수정 전 `parseArrayValue()`는 맨 앞에
  `if (arrayValue.values().isEmpty()) return new Object[0];`라는 조기 반환을 갖고 있었고,
  `TypeMappedAnnotation`이 그 `Object[0]`을 가로채
  `if (attributeType.isArray() && isEmptyObjectArray(value)) return emptyArray(...)`로
  선언 타입의 빈 배열로 바꿔 준다. 즉 값이 하나라도 있어야 결함 경로에 진입한다.
- **fix 후에도 같은 경로**: 이 PR의 다섯 `case`는 조기 반환 뒤에 놓이므로 빈 배열은 새
  분기를 아예 타지 않는다. 이 테스트는 수정 전후로 **한 글자도 다르지 않은 경로**를
  지나며, 그래서 순수한 가드다.
- **역할**: 두 가지다. 하나는 새 분기가 빈 배열 처리를 건드리지 않았다는 보존 증명이고,
  다른 하나는 문서적 역할 — "빈 배열만 시험하면 이 결함은 보이지 않는다"는 함정을 테스트
  코드로 못 박는다. 이 함정을 모른 채 재현을 시도하면 결함이 없다고 오판하기 쉽다.
- **범위 한정**: 여덟 타입 전부가 아니라 `byteValue`와 `floatValue` 두 개만 확인한다.
  빈 경우는 타입별 분기를 타지 않고 공통 조기 반환 하나로 처리되므로, 대표 두 개로
  경로 커버리지가 채워진다는 판단이다.

## 3. 픽스처와 헬퍼

두 테스트가 공유하는 진입 헬퍼는 프로덕션 파이프라인을 그대로 조립해 어노테이션 하나를 꺼내 온다.

```java
private static MergedAnnotation<?> readAnnotation(Class<?> type) throws Exception {
	ClassFileMetadataReaderFactory factory = new ClassFileMetadataReaderFactory(new DefaultResourceLoader());
	MetadataReader reader = factory.getMetadataReader(type.getName());
	return reader.getAnnotationMetadata().getAnnotations().get(ArrayTypesAnnotation.class);
}
```

이 테스트에는 Mockito 목이 하나도 없다. 흉내 내는 대상을 목이 아니라 **실제 파이프라인
전체**로 대신하기 때문이다. `ClassFileMetadataReaderFactory`와 `DefaultResourceLoader`는
프로덕션에서 컴포넌트 스캐닝이 쓰는 바로 그 조합이고, 입력은 테스트 소스가 컴파일되며
생긴 진짜 `.class` 파일이다. 즉 "클래스를 로딩하지 않고 바이트코드만 읽어 어노테이션
메타데이터를 뽑는" 상황을 시뮬레이션하는 것이 아니라 그대로 실행한다.

```java
@ArrayTypesAnnotation(byteValue = 1, shortValue = 2, intValue = 3, longValue = 4,
		booleanValue = true, charValue = 'c', doubleValue = 5.0, floatValue = 6.0f)
static class WithArrays {
}

@ArrayTypesAnnotation(byteValue = {}, shortValue = {}, intValue = {}, longValue = {},
		booleanValue = {}, charValue = {}, doubleValue = {}, floatValue = {})
static class WithEmptyArrays {
}

@Retention(RetentionPolicy.RUNTIME)
@interface ArrayTypesAnnotation {

	byte[] byteValue();

	short[] shortValue();

	int[] intValue();

	long[] longValue();

	boolean[] booleanValue();

	char[] charValue();

	double[] doubleValue();

	float[] floatValue();
}
```

`WithArrays`와 `WithEmptyArrays`가 흉내 내는 실제 상황은 "사용자 코드의 어노테이션 붙은
클래스"다. 스캐너가 만나는 것은 이런 클래스의 클래스 파일이고, 어노테이션 어트리뷰트는
클래스 파일의 `RuntimeVisibleAnnotationsAttribute`에 기록된다. 값을 하나짜리 배열
축약 문법(`byteValue = 1`)으로 쓴 것은 원소가 반드시 하나 이상이어야 결함 경로에
진입하기 때문이며, 각 타입에 서로 다른 값(1, 2, 3, ...)을 준 것은 어트리뷰트가 뒤섞여
읽히는 실수를 함께 잡기 위한 배치다.

`@Retention(RetentionPolicy.RUNTIME)`이 필수인 이유는 이 리더가 읽는 대상이
`RuntimeVisibleAnnotationsAttribute`이기 때문이다. `CLASS` 보존 정책이면 어노테이션이
`RuntimeInvisible` 쪽에 기록되어 조회 자체가 비게 된다.

## 4. 거절 사유와 테스트의 관계

이 PR은 `status: declined` 라벨로 닫혔지만, 테스트가 "의도된 동작을 깨뜨리려 했기 때문"이
아니다. 닫힌 이유는 중복이다. 메인테이너 bclozel이 남긴 유일한 코멘트는 같은 결함이
커밋 7de2b24에서 이미 해결되었다는 안내였다.

테스트의 주장 자체는 옳았다. 근거는 같은 계약의 다른 구현이다. ASM 기반 리더는 동일한
어노테이션을 진짜 원시 배열로 돌려주므로, 두 리더가 `AnnotationMetadata`라는 하나의
계약을 구현하는 이상 둘 중 하나는 반드시 틀린 것이다. 이 테스트가 고정하는 명제는
"ClassFile 리더도 ASM 리더와 같은 값을 낸다"이며, 클래스 Javadoc이 그 의도를 명시한다.

```java
/**
 * Tests for primitive array attribute parsing by the {@code java.lang.classfile}
 * based {@link ClassFileAnnotationDelegate}. Mirrors the ASM-based
 * {@code MergedAnnotationMetadataVisitorTests} expectations.
 */
```

실제로 이 두 테스트는 메인테이너의 수정에 대고 돌려도 통과한다. 그쪽 수정은
`resolveArrayElementType()`이 `byte.class` 같은 원시 클래스 리터럴을 돌려주게 만들어
`Array.newInstance(byte.class, n)`이 진짜 `byte[]`를 만들도록 바꿨기 때문이다. 즉 이
테스트는 폐기된 주장이 아니라 다른 패치로 충족된 주장이다.

거절과 직결된 문제는 주장이 아니라 **배치**였다. 문제를 "구현 간 불일치"로 진단해
놓고 테스트는 JDK 24 전용 소스셋에 새 클래스로 한쪽 구현에만 붙였다. 메인테이너는 대신
`AbstractAnnotationMetadataTests`의 `ComplexAttributes`에 `bytes`, `floats`, `shorts`,
`chars`, `booleans` 어트리뷰트를 추가했고, 그 추상 클래스를 리플렉션·ASM·ClassFile 세
구현이 함께 상속하므로 한 곳의 수정으로 세 구현이 동시에 같은 계약으로 검증된다.
불일치를 근거로 삼았다면 테스트도 불일치를 잴 수 있는 자리에 놓았어야 했다는 것이
이 PR 테스트가 남긴 교훈이다.

## 실측과 역할 요약

이 PR의 테스트에서 확인된 사실과 확인되지 않은 사실을 나눠 적는다.

- 실측 기록: PR 본문에 "현재 코드에서 위 `IllegalStateException`으로 실패하고 수정 후
  통과한다"는 한 문장이 있다. 그 이상의 수치(총 테스트 수, 실패 건수)는 PR 본문과
  diff에 남아 있지 않으므로 판별 근거 부족으로 남긴다.
- 역할 분담: 1번이 결함 재현과 수정 인과를 담당하고, 2번이 보존 증명과 함정 문서화를
  담당한다. 두 건 모두 JDK 24 이상에서만 컴파일·실행되는 `java24Test` 태스크에 속한다.
- 없는 것: 과확장을 막는 음성 가드가 없다. 예컨대 `String[]`이나 `Class[]` 같은 참조
  배열이 여전히 참조 배열로 나오는지를 확인하는 단언이 이 클래스에는 없고, 그 보증은
  전적으로 기존 회귀 스위트에 맡겨져 있다.
