# PR #37109 — 테스트 해설 (테스트 하나하나)

> PR #37109 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

`TypeDescriptorTests`에 테스트 일곱 건과 공용 헬퍼 하나가 추가됐다. 결론부터 말하면
**red 5건, 항상 green인 가드 2건**이다. red 다섯은 네 생성자 중 직렬화가 깨져 있던 세
경로와 그 파생 상황을 재현하고, 가드 둘은 원래 멀쩡하던 경로가 `transient` 변경으로
망가지지 않았음을 고정한다. 앞 네 건이 "네 생성자를 하나씩 밟는다"는 한 축을 이루고,
뒤 세 건이 각각 `EMPTY` 정체성, 파생 디스크립터, 지연 조회 타이밍이라는 다른 축을
맡는다. red/green 판별은 실행 결과가 아니라 diff 논리 — 수정 전 `annotatedElementSupplier`가
`transient`가 아니어서 캡처한 리플렉션 객체가 스트림에 실렸다는 사실 — 에서 유도했다.

## 0. 헬퍼가 먼저인 이유

일곱 테스트를 읽기 전에 공용 헬퍼를 봐야 한다. 이 헬퍼의 한 가지 선택이 일곱 건 전부의
의미를 결정하기 때문이다.

```java
/**
 * Serialize the supplied {@link TypeDescriptor} without resolving its
 * annotations first, and assert that the deserialized copy is equal to it.
 */
private static TypeDescriptor serializeAndDeserialize(TypeDescriptor typeDescriptor) throws Exception {
	ByteArrayOutputStream out = new ByteArrayOutputStream();
	try (ObjectOutputStream outputStream = new ObjectOutputStream(out)) {
		outputStream.writeObject(typeDescriptor);
	}
	try (ObjectInputStream inputStream = new ObjectInputStream(new ByteArrayInputStream(out.toByteArray()))) {
		TypeDescriptor readObject = (TypeDescriptor) inputStream.readObject();
		assertThat(readObject).isEqualTo(typeDescriptor);
		return readObject;
	}
}
```

핵심은 Javadoc이 밝히는 "without resolving its annotations first"다. 헬퍼는 넘겨받은
디스크립터에 `getAnnotations()`를 먼저 부르지 않고 곧바로 스트림에 쓴다. 그래서 각
테스트가 왕복 후 애너테이션을 확인할 때, 그 애너테이션이 살아 있다는 사실 자체가
`writeObject()`가 쓰기 직전에 조회를 강제했다는 증거가 된다. 헬퍼가 미리 조회했다면
이 축은 관찰 불가능해지고, 일곱 테스트 전부가 훅 하나를 통과시키는 무의미한 왕복이 된다.

`ByteArrayOutputStream`/`ByteArrayInputStream` 쌍은 파일이나 네트워크 없이 직렬화
경계를 메모리 안에서 흉내 낸다. 실제로 이 경계가 등장하는 곳은 세션 복제나 원격 호출이며,
`ConversionFailedException`처럼 `TypeDescriptor`를 non-transient 필드로 들고 있는
예외가 그 경계를 넘을 때다.

헬퍼 안의 `assertThat(readObject).isEqualTo(typeDescriptor)`도 단순 형식이 아니다.
`TypeDescriptor.equals()`는 타입과 제네릭뿐 아니라 `annotationsMatch()`로 애너테이션
배열까지 비교하므로, 왕복이 애너테이션을 잃으면 각 테스트의 개별 단언에 닿기도 전에
여기서 먼저 걸린다. 즉 헬퍼 자체가 모든 테스트에 공통 단언 하나를 얹는다.

## 1. Field 생성자 — red

첫 테스트는 `Field`로 만든 디스크립터의 왕복과 애너테이션 보존을 함께 본다.

```java
@Test  // gh-33948
void serializableWithFieldAnnotations() throws Exception {
	Field field = getClass().getField("fieldAnnotated");
	TypeDescriptor readObject = serializeAndDeserialize(new TypeDescriptor(field));
	assertThat(readObject.getAnnotations()).containsExactly(field.getAnnotations());
	assertThat(readObject.hasAnnotation(FieldAnnotation.class)).isTrue();
}
```

- **주장**: `Field`로 만든 디스크립터는 직렬화 왕복이 가능하고, 왕복 후에도 필드
  애너테이션이 원본과 같아야 한다.
- **fixture가 흉내 내는 것**: `fieldAnnotated`는 `@FieldAnnotation`이 붙은
  `List<String>` 필드다. 애너테이션이 붙은 도메인 필드를 변환 경계에 넘기는 평범한
  상황이며, `@DateTimeFormat` 같은 실제 애너테이션의 자리에 해당한다.
- **fix 전 결과와 이유**: red다. `TypeDescriptor(Field)` 생성자의 람다는
  `() -> AnnotatedElementAdapter.from(field.getAnnotations())` 형태로 `Field` 자체를
  캡처한다. `AnnotatedElementSupplier`가 `Serializable`을 상속하므로 이 람다는
  `SerializedLambda`로 직렬화되는데, `SerializedLambda`는 캡처한 값을 전부 함께 쓴다.
  `java.lang.reflect.Field`는 직렬화 불가라 `writeObject` 단계에서
  `NotSerializableException: java.lang.reflect.Field`가 터진다. 단언에 닿기도 전에
  예외로 실패한다.
- **fix 후**: 공급자 필드가 `transient`라 스트림에 실리지 않고, `writeObject()`가
  강제한 조회로 채워진 `annotatedElement`만 건너간다.
- **두 단언이 다른 것을 보는 이유**: 첫째는 애너테이션 배열의 내용 보존을,
  둘째 `hasAnnotation(...)`은 왕복 후에도 조회 API가 정상 동작하는지를 본다.
  `hasAnnotation`은 어댑터의 빠른 경로를 타므로, 5번이 직접 겨냥하는 `EMPTY` 정체성
  문제의 간접 관찰점이기도 하다.

## 2. MethodParameter 생성자 — red

둘째 테스트는 같은 축을 `MethodParameter` 생성자에 대고 다시 세운다.

```java
@Test  // gh-33948
void serializableWithMethodParameterAnnotations() throws Exception {
	MethodParameter methodParameter = new MethodParameter(
			getClass().getMethod("testAnnotatedMethod", String.class), 0);
	TypeDescriptor readObject = serializeAndDeserialize(new TypeDescriptor(methodParameter));
	assertThat(readObject.getAnnotations()).containsExactly(methodParameter.getParameterAnnotations());
	assertThat(readObject.hasAnnotation(ParameterAnnotation.class)).isTrue();
}
```

- **주장**: `MethodParameter`로 만든 디스크립터도 왕복 가능하고, 파라미터 애너테이션이
  보존된다.
- **fixture가 흉내 내는 것**: `testAnnotatedMethod(@ParameterAnnotation(123) String parameter)`의
  0번 파라미터다. 컨트롤러 메서드 파라미터나 setter 인자처럼 애너테이션을 단 메서드
  파라미터를 변환 대상으로 서술하는 경우에 해당한다. `@ParameterAnnotation(123)`처럼
  값을 가진 애너테이션이라 왕복 후 값까지 같아야 `containsExactly`가 성립한다.
- **fix 전 결과와 이유**: red다. 이 생성자의 람다가 캡처하는 것은 `MethodParameter`이고,
  이 클래스는 `Serializable`이 아니다. 1번과 같은 지점에서
  `NotSerializableException`으로 실패한다.
- **1번과 별도인 이유**: 캡처 대상이 다르므로 실패도 별개다. 세 생성자 중 하나만 고치는
  부분 수정을 각각 잡아낸다.

## 3. Property 생성자 — red

셋째 테스트는 읽기·쓰기 메서드를 묶은 `Property` 생성자를 같은 방식으로 덮는다.

```java
@Test  // gh-33948
void serializableWithPropertyAnnotations() throws Exception {
	Property property = new Property(getClass(), getClass().getMethod("getProperty"),
			getClass().getMethod("setProperty", Map.class));
	TypeDescriptor readObject = serializeAndDeserialize(new TypeDescriptor(property));
	assertThat(readObject.getAnnotations()).containsExactly(property.getAnnotations());
	assertThat(readObject.hasAnnotation(MethodAnnotation1.class)).isTrue();
}
```

- **주장**: `Property`로 만든 디스크립터도 왕복 가능하고, 읽기·쓰기 메서드에서 모은
  애너테이션이 보존된다.
- **fixture가 흉내 내는 것**: `@MethodAnnotation1`이 붙은 `getProperty()`와
  `@MethodAnnotation2`가 붙은 `setProperty(Map)` 한 쌍이다. `Property`는 이 둘을 묶어
  하나의 논리 프로퍼티로 보고 애너테이션을 합치므로, 왕복이 그 병합 결과까지 옮기는지를
  본다. 단언이 `MethodAnnotation1`을 고른 것은 읽기 메서드 쪽 애너테이션이 살아남는지를
  대표로 확인하는 것이다.
- **fix 전 결과와 이유**: red다. `Property` 역시 `Serializable`이 아니어서 캡처가
  직렬화를 막는다.

## 4. Annotation 배열 생성자 — 항상 green (양성 가드)

넷째 테스트는 네 생성자 중 유일하게 멀쩡하던 경로를 덮어, 수정이 그 경로를 깨뜨리지 않았음을 고정한다.

```java
@Test  // gh-33948
void serializableWithAnnotationArray() throws Exception {
	Annotation[] annotations = getClass().getField("fieldAnnotated").getAnnotations();
	TypeDescriptor readObject = serializeAndDeserialize(
			new TypeDescriptor(ResolvableType.forClass(String.class), String.class, annotations));
	assertThat(readObject.getAnnotations()).containsExactly(annotations);
	assertThat(readObject.hasAnnotation(FieldAnnotation.class)).isTrue();
}
```

- **주장**: `(ResolvableType, Class, Annotation[])` 생성자로 만든 디스크립터도 왕복
  후 애너테이션을 유지한다.
- **fix 전 green인 이유**: 이 생성자의 람다가 캡처하는 것은 `Annotation[]`뿐이고,
  JDK의 애너테이션 프록시는 직렬화 가능하다. 네 생성자 중 유일하게 수정 전에도 멀쩡히
  직렬화되던 경로이므로 이 테스트는 fix 전에도 통과한다.
- **존재 이유는 fix 후에 있다**: 공급자 필드를 `transient`로 바꾸는 변경은 이 경로의
  동작 방식도 함께 바꾼다. 예전에는 람다가 애너테이션을 실어 날랐지만, 이제는
  `writeObject()`가 강제한 조회 결과인 `annotatedElement`가 실어 나른다. 같은 결과가
  나오는지를 확인하는 것이 이 테스트의 일이다. 즉 "고치면서 멀쩡하던 경로를 안
  깨뜨렸다"의 직접 보증이며, ../37153/guard-tests.md의 용어로 양성 가드다.
- **기존 `serializable()` 테스트와의 관계**: 기존 테스트는 `TypeDescriptor.forObject("")`로
  같은 생성자를 밟되 애너테이션 배열이 `null`인 경우만 본다. 이 테스트는 배열이 실제로
  비어 있지 않은 경우를 더해, 같은 생성자의 두 갈래를 모두 덮는다.

## 5. 애너테이션 없는 필드와 EMPTY 정체성 — red

다섯째 테스트는 애너테이션이 하나도 없는 필드를 왕복시켜 `EMPTY` 싱글턴 정체성이 복원되는지를 본다.

```java
@Test  // gh-33948
void serializableWithoutAnnotations() throws Exception {
	TypeDescriptor readObject = serializeAndDeserialize(new TypeDescriptor(getClass().getField("fieldScalar")));
	assertThat(readObject.getAnnotations()).isEmpty();
	// An empty AnnotatedElementAdapter is a shared instance which returns its annotation
	// array as is, whereas any other adapter hands out a defensive copy on every call.
	assertThat(readObject.getAnnotations()).isSameAs(readObject.getAnnotations());
}
```

- **주장**: 애너테이션이 하나도 없는 필드도 왕복 가능하고, 왕복 후의 어댑터가
  **공유 `EMPTY` 인스턴스여야** 한다.
- **fixture가 흉내 내는 것**: `fieldScalar`는 애너테이션이 없는 `Integer` 필드다.
  실무에서 압도적으로 흔한 경우이며, gh-33948이 성능 문제로 지목했던 "애너테이션 없는
  클래스"의 최소형이기도 하다.
- **fix 전 결과와 이유**: red다. 애너테이션이 하나도 없어도 실패한다 — 터지는 것은
  애너테이션이 아니라 람다가 붙잡은 `Field` 자체이기 때문이다. 이 사실이 결함의 성격을
  가장 선명하게 보여 준다.
- **둘째 단언이 정체성을 잡아내는 원리**: 어댑터의 `getAnnotations()`는
  `(isEmpty() ? this.annotations : this.annotations.clone())`을 반환하고, `isEmpty()`는
  값 비교가 아니라 `this == EMPTY` 동일성 비교다. 그러므로 두 번 호출해 **같은 배열
  인스턴스**가 나온다는 것은 곧 그 어댑터가 `EMPTY`라는 뜻이다. 방어 복사 여부라는
  관찰 가능한 부작용으로 내부 동일성을 간접 측정한 셈이다.
- **왜 이 단언이 필요한가**: `AnnotatedElementAdapter`에는 `readResolve()`가 없어서,
  역직렬화된 빈 어댑터는 `EMPTY`와 다른 인스턴스가 된다. 그대로 두면 `hasAnnotation()`과
  `getAnnotation()`의 빠른 경로가 왕복 이후 사라진다. `readObject()`가 복원된 어댑터를
  `AnnotatedElementAdapter.from(...)`에 한 번 더 통과시키는 이유가 그것이고, 그 재호출을
  빼면 이 테스트만 깨진다. red 다섯 중 fix의 특정 한 줄을 단독으로 겨냥하는 유일한
  테스트다.

## 6. 파생 디스크립터 — 항상 green (양성 가드)

여섯째 테스트는 Map 값 타입으로 파생시킨 디스크립터가 왕복 후에도 원본의 애너테이션 맥락을 유지하는지를 본다.

```java
@Test  // gh-33948
void serializableWithDerivedTypeDescriptor() throws Exception {
	Field field = getClass().getField("mapPreserveContext");
	TypeDescriptor valueTypeDescriptor = new TypeDescriptor(field).getMapValueTypeDescriptor();
	TypeDescriptor readObject = serializeAndDeserialize(valueTypeDescriptor);
	assertThat(readObject.getAnnotations()).containsExactly(field.getAnnotations());
}
```

- **주장**: Map 값 타입처럼 원본에서 파생된 디스크립터도 왕복 후 원본의 애너테이션
  맥락을 유지한다.
- **fixture가 흉내 내는 것**: `mapPreserveContext`는 `@FieldAnnotation`이 붙은
  `Map<List<Integer>, List<Integer>>` 필드다. 컬렉션 요소나 Map 값으로 한 단계 들어가도
  바깥 필드의 애너테이션이 따라간다는 것이 `TypeDescriptor`의 "맥락 보존" 계약이고,
  이 필드 이름 자체가 그 계약을 가리킨다.
- **fix 전 green으로 판단하는 근거**: `getMapValueTypeDescriptor()`는
  `getRelatedIfResolvable(...)`을 거쳐 `new TypeDescriptor(type, null, getAnnotations())`,
  곧 4번과 같은 3-인자 생성자를 부른다. 파생 시점에 애너테이션이 이미 배열로 풀려
  있으므로 파생 디스크립터의 람다는 `Annotation[]`만 캡처하고 `Field`를 붙잡지 않는다.
  따라서 이 PR이 고친 축(리플렉션 객체 캡처)에서는 수정 전에도 통과한다.
- **판별의 한계**: 이 왕복은 애너테이션 축 외에 디스크립터가 들고 있는 `ResolvableType`의
  직렬화 가능성에도 의존한다. `List<Integer>`처럼 구체 파라미터화 타입이라 문제가 없을
  것으로 읽히지만, 그 축까지 diff만으로 단정하기는 어렵다. "이 PR이 고친 축에서는
  green"으로 읽는 것이 정확하다.
- **역할**: 파생 경로가 원본 경로와 다른 생성자를 탄다는 사실을 계약으로 못박는다.
  1~3번이 리플렉션 출처 생성자를 덮고 4·6번이 배열 생성자를 두 가지 만들어짐 경로
  (직접 생성, 파생)로 덮어, 네 생성자가 실제로 만들어지는 방식 전부가 왕복 검사를 받는다.

## 7. 지연 조회와 직렬화의 타이밍 — red

마지막 테스트는 조회 횟수를 세는 수동 spy로, 조회가 생성 시점이 아니라 직렬화 시점에만 일어남을 고정한다.

```java
@Test  // gh-33948
void serializationResolvesAnnotationsThatHaveNotBeenResolvedYet() throws Exception {
	AtomicInteger resolutionCount = new AtomicInteger();
	MethodParameter methodParameter =
			new MethodParameter(getClass().getMethod("testAnnotatedMethod", String.class), 0) {
				@Override
				public Annotation[] getParameterAnnotations() {
					resolutionCount.incrementAndGet();
					return super.getParameterAnnotations();
				}
			};

	TypeDescriptor typeDescriptor = new TypeDescriptor(methodParameter);
	assertThat(resolutionCount).hasValue(0);

	TypeDescriptor readObject = serializeAndDeserialize(typeDescriptor);
	assertThat(resolutionCount).hasValue(1);
	assertThat(readObject.getAnnotations()).containsExactly(methodParameter.getParameterAnnotations());
}
```

- **주장**: 생성 직후에는 애너테이션 조회가 **한 번도** 일어나지 않고, 직렬화 시점에
  **정확히 한 번** 일어난다.
- **spy가 흉내 내는 것**: `MethodParameter`를 익명 서브클래스로 감싸
  `getParameterAnnotations()` 호출 횟수를 센다. Mockito 없이 오버라이드 한 줄로 만든
  수동 spy이며, 세는 대상은 gh-33948이 비용으로 지목했던 바로 그 조회다. 실제 상황에서
  이 조회는 애너테이션 타입 로딩과 클래스패스 탐색을 유발하고, `ClassLoader.loadClass`의
  동기화 때문에 동시성 아래에서 더 나빠진다. 카운터 하나가 그 비용의 발생 여부를
  관찰 가능한 정수로 바꾼다.
- **fix 전 결과와 이유**: red다. 첫 단언 `hasValue(0)`은 fix 전에도 통과한다 —
  지연 조회 자체는 gh-33948이 이미 넣어 둔 동작이기 때문이다. 실패는 그 다음
  `serializeAndDeserialize` 호출에서 일어난다. 익명 서브클래스 인스턴스 역시
  직렬화 불가이므로 `NotSerializableException`으로 터지고, `hasValue(1)`에 닿지 못한다.
- **두 단언이 반드시 함께여야 하는 이유**: `hasValue(0)`만 있으면 "지연 조회는
  살아 있으나 직렬화가 애너테이션을 잃는" 상태를 통과시키고, `hasValue(1)`만 있으면
  "직렬화는 되지만 생성 시점에 이미 조회해 버려 성능 개선이 되돌아간" 상태를
  통과시킨다. 둘이 함께 있어야 **고치면서 gh-33948의 성능 개선을 되돌리지 않았다**는
  명제가 성립한다.
- **세 번째 단언**: 왕복 후에도 값이 원본과 같은지를 확인해, 강제된 조회가 실제로
  스트림에 실렸는지까지 본다.
- **역할**: 이 PR에서 가장 미묘한 성질을 유일하게 관찰 가능한 형태로 만든 테스트다.
  `writeObject()` 안의 `getAnnotatedElement()` 한 줄이 없어도 1~6번 중 일부는 red로
  잡히지만, "조회가 정확히 직렬화 시점에만 일어난다"는 타이밍 계약은 이 테스트만
  고정한다.

## fixture

이 PR은 새 fixture를 만들지 않았다. 일곱 테스트가 쓰는 필드·메서드·애너테이션은 전부
`TypeDescriptorTests`가 이미 갖고 있던 "test introspection용" 자산이다.

```java
public Integer fieldScalar;

@FieldAnnotation
public List<String> fieldAnnotated;

@FieldAnnotation
public Map<List<Integer>, List<Integer>> mapPreserveContext;

@MethodAnnotation1
public Map<List<Integer>, List<Long>> getProperty() {
	return property;
}

@MethodAnnotation2
public void setProperty(Map<List<Integer>, List<Long>> property) {
	this.property = property;
}

public void testAnnotatedMethod(@ParameterAnnotation(123) String parameter) {
}
```

애너테이션 세 종류는 모두 `RUNTIME` 유지 정책이라 리플렉션으로 읽힌다. `@FieldAnnotation`은
필드 전용, `@ParameterAnnotation`은 파라미터 전용에 `int value()`를 갖고,
`@MethodAnnotation1`/`@MethodAnnotation2`는 메서드용이다. 새로 추가된 임포트는
`java.util.concurrent.atomic.AtomicInteger` 하나이며, 7번의 조회 카운터에만 쓰인다.

기존 자산을 그대로 쓴 것은 우연이 아니라 이 PR의 성격을 반영한다. 이 회귀가 놓쳐진
이유는 픽스처가 부족해서가 아니라 **기존 테스트가 네 생성자 중 하나만 밟았기**
때문이다. 필요한 재료는 이미 파일 안에 다 있었고, 빠져 있던 것은 그 재료를 나머지
세 경로에 대고 왕복시키는 테스트였다.

## 분류와 역할 요약

일곱 테스트를 fix 전 결과와 고정 대상으로 정리하면 다음과 같다. 판별 근거는 diff
논리이며 실행으로 측정한 값이 아니다.

| 테스트 | 생성자 경로 | fix 전 | 고정하는 것 |
|---|---|---|---|
| `serializableWithFieldAnnotations` | `Field` | red | Field 캡처 제거 |
| `serializableWithMethodParameterAnnotations` | `MethodParameter` | red | MethodParameter 캡처 제거 |
| `serializableWithPropertyAnnotations` | `Property` | red | Property 캡처 제거 |
| `serializableWithAnnotationArray` | `(ResolvableType, Class, Annotation[])` | green | 멀쩡하던 경로 보존 |
| `serializableWithoutAnnotations` | `Field` | red | `EMPTY` 정체성 복원 |
| `serializableWithDerivedTypeDescriptor` | 파생 -> 3-인자 | green | 파생 경로 맥락 보존 |
| `serializationResolvesAnnotationsThatHaveNotBeenResolvedYet` | `MethodParameter` | red | 지연 조회 타이밍 |

배치를 읽는 두 가지 방식이 있다. 하나는 **생성자 축**으로, 앞 네 건이 네 생성자를
하나씩 밟아 "한 경로만 밟는 테스트는 계약이 아니라 그 경로를 지킬 뿐"이라는 이 회귀의
근본 원인을 정면으로 메운다. 다른 하나는 **fix의 구성 요소 축**으로, 세 훅
(`transient` 선언, `writeObject()`의 강제 조회, `readObject()`의 `from(...)` 재호출)이
각각 어느 테스트에 걸려 있는지를 본다. `transient`는 red 다섯 전부가, 강제 조회는
1~3·5·7번의 애너테이션 단언과 7번의 카운터가, `from(...)` 재호출은 5번의 `isSameAs`
단언이 지킨다.

가드가 두 건뿐인 것은 이 결함이 "되던 것이 안 되던" 회귀라서다. 깨져 있던 경로에는
보존할 동작이 없고, 보존해야 할 것은 멀쩡하던 배열 생성자 경로와 gh-33948이 얻은
지연 조회 성능뿐이다. 전자는 4·6번이, 후자는 7번의 첫 단언이 맡는다. 7번이 red이면서도
그 안에 보존 축 단언을 품고 있다는 점은, red/가드가 파일 안의 배타적 분류가 아니라
단언 단위의 성질임을 보여 준다.
