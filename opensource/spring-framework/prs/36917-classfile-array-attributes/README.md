# PR #36917 — Parse byte/short/char/boolean/float array attributes

## 0. 정향

이 PR은 머지되지 않았다. 2026-06-13에 열렸고 2026-08-05에 `status: declined` 라벨과 함께 닫혔다. 리뷰는 한 건도 달리지 않았고, 닫힌 이유는 "이미 다른 커밋에서 해결되었다"였다. 즉 진단이 틀려서 거절된 것이 아니라, 같은 결함이 다른 경로로 먼저 고쳐졌고 그 수정이 이 패치보다 근본적이었기 때문에 밀려난 사례다. 이 문서의 가치는 그 차이 — 증상을 지운 패치와 구조를 지운 패치의 차이 — 를 정확히 보는 데 있다.

## 1. 배경 — `ClassFileAnnotationDelegate`는 무엇을 하나

Spring은 클래스를 로딩하지 않고 바이트코드만 읽어 어노테이션 메타데이터를 뽑는다. 컴포넌트 스캔이나 조건부 설정 평가처럼, 아직 로딩하면 안 되는 클래스의 어노테이션을 미리 봐야 하는 상황이 많기 때문이다. 이 역할을 하는 것이 `MetadataReader` 계열이다.

JDK 24부터 Spring 7은 두 가지 구현을 갖는다. JDK 24 미만에서는 기존 ASM 기반 리더가, JDK 24 이상에서는 JDK 표준 `java.lang.classfile` API 기반 리더가 선택된다. 선택 주체는 `MetadataReaderFactoryDelegate`이고, JDK 24 전용 소스셋(`spring-core/src/main/java24/`)에 놓인 `ClassFileAnnotationDelegate`가 후자의 어노테이션 파싱을 담당한다.

이 클래스가 다루는 대상은 `RuntimeVisibleAnnotationsAttribute`, 즉 클래스 파일에 기록된 런타임 가시 어노테이션이다. 어노테이션 어트리뷰트 값은 `AnnotationValue`라는 sealed 계층으로 표현된다. 하위 타입은 `OfByte`, `OfShort`, `OfChar`, `OfInt`, `OfLong`, `OfFloat`, `OfDouble`, `OfBoolean`, `OfString`, `OfClass`, `OfEnum`, `OfAnnotation`, `OfArray`로 고정되어 있다.

배열 어트리뷰트는 `OfArray`로 오고, 그 안에 원소 `AnnotationValue`들이 들어 있다. 문제는 여기서 시작한다. 자바 어노테이션의 `byte[] value()` 같은 선언은 실제 원시 타입 배열을 요구하는데, 파서가 원소를 어떤 배열로 담아 돌려주느냐가 곧 계약이 된다.

## 2. 제안했던 변경

당시 `parseArrayValue()`는 원시 배열을 세 종류만 특별 취급했다. PR의 diff 컨텍스트에 남아 있는 원본은 다음과 같은 모양이었다.

```java
private static Object parseArrayValue(String className, @Nullable ClassLoader classLoader, AnnotationValue.OfArray arrayValue) {
	if (arrayValue.values().isEmpty()) {
		return new Object[0];
	}
	Stream<AnnotationValue> stream = arrayValue.values().stream();
	switch (arrayValue.values().getFirst()) {
		case AnnotationValue.OfInt _ -> {
			return stream.map(AnnotationValue.OfInt.class::cast).mapToInt(AnnotationValue.OfInt::intValue).toArray();
		}
		case AnnotationValue.OfDouble _ -> {
			return stream.map(AnnotationValue.OfDouble.class::cast).mapToDouble(AnnotationValue.OfDouble::doubleValue).toArray();
		}
		case AnnotationValue.OfLong _ -> {
			return stream.map(AnnotationValue.OfLong.class::cast).mapToLong(AnnotationValue.OfLong::longValue).toArray();
		}
		default -> {
			Class<?> arrayElementType = resolveArrayElementType(arrayValue.values(), classLoader);
			return stream
					.map(rawValue -> readAnnotationValue(className, rawValue, classLoader))
					.toArray(length -> (Object[]) Array.newInstance(arrayElementType, length));
		}
	}
}
```

`int`, `double`, `long`만 `mapToInt`/`mapToDouble`/`mapToLong`로 원시 배열이 되고, 나머지는 `default` 분기로 떨어진다. 그 분기는 `toArray(...)`를 `Object[]`로 캐스팅해 쓰므로 결과는 언제나 참조 타입 배열이다. 원소 타입을 정하는 `resolveArrayElementType()`도 당시에는 `OfConstant constantValue -> constantValue.resolvedValue().getClass()`를 반환했다. `byte` 상수의 `resolvedValue()`는 박싱된 `Byte`이므로 반환 타입은 `Byte.class`가 되고, 최종 결과는 `byte[]`가 아니라 `Byte[]`가 된다.

제안한 패치는 빠진 다섯 타입에 대해 `case`를 추가하는 것이었다. `Stream`에는 `mapToByte`류가 없으므로 각 분기가 직접 배열을 채웠다. `OfByte` 분기는 다음과 같았고, `OfShort`/`OfChar`/`OfBoolean`/`OfFloat`도 같은 형태를 반복했다.

```java
case AnnotationValue.OfByte _ -> {
	List<AnnotationValue> values = arrayValue.values();
	byte[] result = new byte[values.size()];
	for (int i = 0; i < result.length; i++) {
		result[i] = ((AnnotationValue.OfByte) values.get(i)).byteValue();
	}
	return result;
}
```

테스트는 `spring-core/src/test/java24/`에 새 클래스 `ClassFileAnnotationDelegatePrimitiveArrayTests`를 만들어 붙였다. 여덟 가지 원시 배열 어트리뷰트를 가진 어노테이션을 선언하고, `ClassFileMetadataReaderFactory`로 읽어 값이 원시 배열로 나오는지 확인하는 방식이었다.

## 3. 왜 문제라고 판단했었나

박싱된 배열은 소비 지점에서 곧바로 예외가 된다. `MergedAnnotation`으로 값을 꺼내면 `TypeMappedAnnotation`이 선언된 어트리뷰트 타입과 실제 값을 맞춰 보는데, 이 검사는 `adaptForAttribute()`의 마지막 관문에서 실패한다. 현재 upstream 코드에도 같은 문장이 그대로 있다.

```java
if (!attributeType.isInstance(value)) {
	throw new IllegalStateException("Attribute '" + attribute.getName() +
			"' in annotation " + ClassUtils.getCanonicalName(getType()) + " should be compatible with " +
			ClassUtils.getCanonicalName(attributeType) + " but a " + ClassUtils.getCanonicalName(value.getClass()) +
			" value was returned");
}
```

`byte[].class.isInstance(new Byte[]{...})`는 거짓이므로 예외가 던져진다. 배열 공변성은 참조 타입 사이에서만 성립하고 원시 배열과는 무관하기 때문이다.

판단의 결정적 근거는 ASM 리더였다. 같은 어노테이션을 ASM 경로로 읽으면 진짜 원시 배열이 나온다. 두 리더는 같은 `AnnotationMetadata` 계약을 구현하므로, 둘의 결과가 다르면 한쪽이 틀린 것이다. 나중 것이 JDK 24 전용 신규 구현이었으니 틀린 쪽은 명백했다. 즉 "의도된 동작"으로 볼 여지가 없는, 구현 간 불일치였다.

한 가지 함정도 함께 확인했다. 빈 배열은 예외가 나지 않는다. `parseArrayValue()`가 `new Object[0]`을 돌려주고, `TypeMappedAnnotation`이 그 앞에서 가로채기 때문이다.

```java
if (attributeType.isArray() && isEmptyObjectArray(value)) {
	return emptyArray(attributeType.componentType());
}
```

빈 배열만 시험해 보면 아무 문제가 없어 보인다. 결함을 재현하려면 반드시 원소가 하나 이상 있어야 한다.

## 4. 왜 거절되었나

거절 사유는 기술적 반박이 아니라 중복이었다. 메인테이너 Brian Clozel(`bclozel`, MEMBER)이 남긴 유일한 코멘트는 다음 한 줄이다.

> Thanks @junhyeong9812 , this has been addressed in 7de2b24d81c02681c8e8cb764de0690726eb1a8c already.

시간선을 보면 사정이 분명해진다. PR은 2026-06-13에 열렸고 39일간 리뷰가 없었다. 그 사이 2026-07-22 07:57(UTC)에 외부 사용자 `gsruisch`가 이슈 gh-37083을 열었다. Spring Boot 4 마이그레이션 중 `MetadataReader`로 `byte[]` 어트리뷰트를 읽다가 실패한다는 회귀 보고였고, 스택트레이스는 PR 본문에 적었던 것과 같은 `IllegalStateException`이었다. 08:49(UTC)에 커밋 7de2b24가 만들어졌고 08:55에 이슈가 닫혔다. 신고에서 수정까지 한 시간이 채 걸리지 않았다. 이 PR이 닫힌 것은 그로부터 2주 뒤다.

정리하면 거절의 성격은 세 가지 중 어느 것도 아니다. 의도된 동작이라 반려된 것이 아니고, 범위를 벗어나 반려된 것도 아니며, 구현이 틀렸다고 지적받은 것도 아니다. 결함은 실재했고 메인테이너가 직접 고쳤다. 다만 그 수정이 이 PR을 대체했다.

그리고 대체한 쪽이 더 나았다. 메인테이너의 커밋은 특수 분기를 더 추가하는 대신 `parseArrayValue()`를 통째로 지웠다.

```java
private static Object parseArrayValue(String className, @Nullable ClassLoader classLoader, AnnotationValue.OfArray arrayValue) {
	List<AnnotationValue> values = arrayValue.values();
	Class<?> arrayElementType = (values.isEmpty() ? Object.class : resolveArrayElementType(values, classLoader));
	Object array = Array.newInstance(arrayElementType, values.size());
	for (int i = 0; i < values.size(); i++) {
		Array.set(array, i, readAnnotationValue(className, values.get(i), classLoader));
	}
	return array;
}
```

핵심은 타입별 분기를 `resolveArrayElementType()` 한 곳으로 몰고, 그 메서드를 sealed 계층에 대해 빠짐없이 열거한 것이다.

```java
private static Class<?> resolveArrayElementType(List<AnnotationValue> values, @Nullable ClassLoader classLoader) {
	return switch (values.getFirst()) {
		case AnnotationValue.OfByte _ -> byte.class;
		case AnnotationValue.OfChar _ -> char.class;
		case AnnotationValue.OfDouble _ -> double.class;
		case AnnotationValue.OfFloat _ -> float.class;
		case AnnotationValue.OfInt _ -> int.class;
		case AnnotationValue.OfLong _ -> long.class;
		case AnnotationValue.OfShort _ -> short.class;
		case AnnotationValue.OfBoolean _ -> boolean.class;
		case AnnotationValue.OfString _ -> String.class;
		case AnnotationValue.OfAnnotation _ -> MergedAnnotation.class;
		case AnnotationValue.OfClass _ -> String.class;
		case AnnotationValue.OfEnum enumValue -> loadEnumClass(enumValue, classLoader);
		case AnnotationValue.OfArray _ -> Object.class;
	};
}
```

`default` 분기가 사라진 것이 결정적이다. `AnnotationValue`가 sealed이므로 컴파일러가 열거의 완전성을 강제한다. JDK가 새 하위 타입을 추가하면 컴파일이 깨지고, 같은 종류의 누락이 조용히 재발할 수 없다. 커밋 메시지도 이 점을 이유로 든다. "Because the `AnnotationValue` hierarchy is sealed, we can now ma[k]e sure that the implementation is exhaustive."

반환 타입 표현도 바뀌었다. 이제 `byte.class` 같은 원시 클래스 리터럴을 돌려주므로 `Array.newInstance(byte.class, n)`이 진짜 `byte[]`를 만들고, `Array.set`이 박싱된 값을 언박싱해 채워 넣는다. `readAnnotationValue()`는 여전히 박싱된 `Object`를 돌려주지만 배열에 담기는 순간 원시로 풀린다.

같은 어트리뷰트를 두 코드가 각각 어떤 배열로 돌려주는지 비교하면 차이가 한눈에 보인다.

| 어트리뷰트 선언 | 거절 당시 원본 | 제안했던 패치 | 현재 upstream |
|---|---|---|---|
| `int[]` | `int[]` | `int[]` | `int[]` |
| `long[]`, `double[]` | 원시 배열 | 원시 배열 | 원시 배열 |
| `byte[]`, `short[]`, `char[]` | `Byte[]`, `Short[]`, `Character[]` | 원시 배열 | 원시 배열 |
| `boolean[]`, `float[]` | `Boolean[]`, `Float[]` | 원시 배열 | 원시 배열 |
| 빈 배열 전체 | `Object[0]` | `Object[0]` | 선언 타입의 빈 배열 |

마지막 행이 제안 패치가 손대지 않은 부분이다. 원본의 `if (values.isEmpty()) return new Object[0];` 조기 반환을 그대로 두었기 때문에, 빈 배열은 여전히 `TypeMappedAnnotation`의 보정에 의존했다. 현재 코드는 빈 경우에도 `Object.class`로 길이 0 배열을 만들지만 조기 반환이라는 별도 경로 자체를 없앴다.

## 5. 되돌아보기

세 가지를 사전에 확인했어야 했다.

첫째, 이슈를 먼저 열었어야 했다. 이 PR은 연결된 이슈가 없었고 본문에도 `Closes gh-` 참조가 없다. Spring 팀의 트리아지는 이슈 기준으로 돌아간다. gh-37083은 열린 지 한 시간 만에 고쳐졌지만, 같은 내용을 담은 이 PR은 39일 동안 라벨조차 붙지 않았다. 재현 코드를 담은 이슈를 먼저 열고 거기에 PR을 연결했다면, 최소한 같은 큐에 들어갔을 것이다.

둘째, 테스트를 새 클래스가 아니라 기존 공용 테스트에 넣었어야 했다. 이 제안은 `src/test/java24/`에 JDK 24 전용 테스트 클래스를 새로 만들었다. 메인테이너는 대신 `AbstractAnnotationMetadataTests`의 `ComplexAttributes`에 `bytes`, `floats`, `shorts`, `chars`, `booleans` 어트리뷰트를 추가했다.

```java
@ComplexAttributes(names = {"first", "second"}, count = {TestEnum.ONE, TestEnum.TWO},
		types = {TestEnum.class}, subAnnotation = @SubAnnotation(name="spring"), bytes = {1, 2},
		floats = {1.0f, 2.0f}, shorts = {1, 2}, chars = {'a', 'b'}, booleans = {true, false})
```

이 추상 클래스는 `StandardAnnotationMetadataTests`(리플렉션), `SimpleAnnotationMetadataTests`(ASM), `DefaultAnnotationMetadataTests`가 함께 상속한다. 그리고 `DefaultAnnotationMetadataTests`는 `MetadataReaderFactory.create(...)`를 쓰므로 JDK 24 이상에서 ClassFile 리더를 태운다. 즉 한 곳에 어트리뷰트를 추가하는 것만으로 세 구현이 동시에 같은 계약으로 검증된다. 문제를 "구현 간 불일치"로 진단해 놓고 정작 테스트는 한쪽 구현에만 붙인 것이 모순이었다.

셋째, 결함의 형태를 보고 수정의 형태를 정했어야 했다. 다섯 타입이 한꺼번에 빠졌다는 사실 자체가 "타입을 손으로 열거하는 구조"가 원인이라는 신호였다. 그 신호를 읽었다면 `case`를 다섯 개 더 붙이는 대신 열거를 강제 가능한 형태로 바꾸는 방향을 택했을 것이다. 게다가 `AnnotationValue`가 sealed이고 `readAnnotationValue()`가 이미 `default` 없는 exhaustive switch를 쓰고 있었으므로, 재료는 코드 안에 다 있었다.

## 6. 교훈 — "의도 vs 버그" 판별

이 사례에서 판별 자체는 맞았다. 메인테이너가 같은 결함을 직접 고쳤으니 사후적으로 증명되었다. 무엇이 그 판단을 옳게 만들었는지 짚어 두면 다음에도 쓸 수 있다.

가장 강한 근거는 같은 계약의 다른 구현이었다. ASM 리더와 ClassFile 리더는 같은 `AnnotationMetadata` 인터페이스를 만족해야 한다. 둘의 결과가 다르면 설계자의 의도를 추측할 필요가 없다. 계약이 하나뿐이므로 둘 중 하나는 반드시 틀렸다. 두 번째 근거는 하위 타입의 비대칭이었다. `int`, `long`, `double`만 특별 취급하고 `byte`, `short`, `char`, `boolean`, `float`을 빼는 설계 의도는 존재할 수 없다. 규칙이 일부 원소에만 적용되면 그것은 정책이 아니라 누락이다.

반대로 의도를 의심해야 하는 신호도 있다. 동작이 문서화되어 있거나, 그 동작을 못 박은 테스트가 있거나, 주석이 이유를 설명하고 있으면 바꾸기 전에 물어야 한다. 이 사례에는 그런 것이 하나도 없었다.

그러나 판별을 통과한 것과 PR이 채택되는 것은 다른 문제다. 실제로 갈린 지점은 두 가지였다.

하나는 가시성이다. 결함이 진짜여도 큐에 보이지 않으면 존재하지 않는 것과 같다. 사용자가 실제 마이그레이션 중 막힌 사연과 재현 코드를 이슈로 올리자 한 시간 만에 고쳐졌다. 재현 코드와 영향받는 실사용 시나리오는 패치 자체만큼 값이 나간다.

다른 하나는 수정의 층위다. 결함이 한 값에서 났다고 해서 수정이 한 값짜리여야 하는 것은 아니다. 같은 종류의 누락이 여러 개 동시에 발견되면 그것은 개별 버그가 아니라 구조의 증상이다. 이때 옳은 질문은 "빠진 것을 다 채웠나"가 아니라 "다음에 또 빠지는 것을 컴파일러가 막을 수 있나"다. sealed 계층에서 `default`를 지우는 선택이 정확히 그 질문에 대한 답이었고, 채워 넣는 패치와 지우는 패치의 차이가 이 PR의 결말이었다.

같은 "의도 vs 버그" 판별이 반대로 결말난 사례는 [#36912](../36912-aot-reserve-method-names/README.md)다. 그쪽은 결함이 한 줄에 국소적이라 판별이 그대로 채택으로 이어졌고, 메인테이너가 "You were right on the intent"라는 코멘트와 함께 머지했다. 두 문서를 나란히 읽으면 판별의 정확성과 수정 층위의 적절성이 서로 다른 관문이라는 점이 분명해진다.

---

연관 ko-docs (모듈 지도): `spring-core/05-어노테이션-메타데이터와-asm.md`
