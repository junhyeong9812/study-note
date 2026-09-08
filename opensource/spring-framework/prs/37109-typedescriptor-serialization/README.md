# PR #37109 — Restore serialization support for TypeDescriptor

## 0. 정향

이 PR은 `TypeDescriptor`가 3.0부터 선언해 온 `Serializable` 계약이 6.2.x 어느 시점부터 깨져 있던 회귀를 고친다. `Field`·`MethodParameter`·`Property`로 만든 디스크립터를 직렬화하면 `NotSerializableException`이 터졌고, 원인은 성능 개선 커밋 `1a573d6e3c7`(gh-33948)이 도입한 **직렬화 가능한 람다**가 그 리플렉션 객체들을 그대로 캡처했기 때문이다. 수정은 그 람다 필드를 `transient`로 바꾸고, `writeObject()`/`readObject()` 한 쌍으로 애너테이션만 스트림에 실어 보내는 방식이다. 2026-08-04에 제출되어 아직 리뷰 대기 상태다.

직렬화 기초 개념(왜 람다가 캡처를 실어 나르나, transient·hook·serialVersionUID)은
[직렬화 학습 시리즈](../../concepts/serialization-series/00-learning-index.md) 00~11편이
이 PR을 사례 연구(09편)로 삼아 다룬다.

## 1. 배경 — TypeDescriptor는 무엇이고 왜 Serializable인가

`TypeDescriptor`는 변환의 출발점과 도착점을 **맥락까지 포함해** 서술하는 값 객체다. Javadoc의 한 줄 요약이 "Contextual descriptor about a type to convert from or to"인데, 여기서 방점은 *contextual*에 찍힌다. `Class<?>` 하나로는 `List<String>`과 `List<Integer>`를 구별할 수 없고, 그 필드에 `@DateTimeFormat`이 붙어 있는지도 알 수 없다. `TypeDescriptor`는 그 셋을 한 객체에 담는다.

```java
private final Class<?> type;

private final ResolvableType resolvableType;

private final AnnotatedElementSupplier annotatedElementSupplier;

private volatile @Nullable AnnotatedElementAdapter annotatedElement;
```

`type`은 원시 타입, `resolvableType`은 제네릭 정보, 나머지 둘이 애너테이션 담당이다. 생성자는 넷이고, 앞의 셋은 각각 `MethodParameter`·`Field`·`Property`라는 리플렉션 객체를 받아 거기서 세 조각을 뽑아낸다. 네 번째 `(ResolvableType, Class, Annotation[])` 생성자는 리플렉션 출처 없이 재료를 직접 받으며, `valueOf(Class)`·`narrow(Object)` 같은 파생 경로가 이 생성자를 쓴다.

이 클래스가 `Serializable`인 이유는 스스로 직렬화될 일이 있어서라기보다, **다른 직렬화 가능한 객체에 실려 다니기 때문**이다. 가장 직접적인 사례가 변환 예외 두 개다.

```java
public class ConversionFailedException extends ConversionException {

	private final @Nullable TypeDescriptor sourceType;

	private final TypeDescriptor targetType;

	private final @Nullable Object value;
```

`ConversionFailedException`과 `ConverterNotFoundException`은 `Throwable`을 상속하므로 자동으로 직렬화 가능하고, 두 필드 모두 `transient`가 아니다. 즉 원격 호출이나 세션 복제 경계를 넘는 예외 안에 `TypeDescriptor`가 통째로 실린다. 예외를 직렬화하려면 그 안의 디스크립터도 직렬화되어야 한다.

여기서 미리 짚어 둘 점이 있다. 제네릭 정보를 담은 `ResolvableType`도 원래는 직렬화 불가능한 `java.lang.reflect.Type`을 품는데, Spring은 이 문제를 이미 오래전에 풀어 두었다. `SerializableTypeWrapper`가 `Type`을 직렬화 가능한 프록시로 감싸고, 그 뒤에 있는 `FieldTypeProvider`는 `Field`를 `transient`로 두고 이름과 선언 클래스만 저장한 뒤 역직렬화 시점에 다시 찾아온다.

```java
static class FieldTypeProvider implements TypeProvider {

	private final String fieldName;

	private final Class<?> declaringClass;

	private transient Field field;

	...

	private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
		inputStream.defaultReadObject();
		try {
			this.field = this.declaringClass.getDeclaredField(this.fieldName);
		}
		catch (Throwable ex) {
			throw new IllegalStateException("Could not find original class structure", ex);
		}
	}
}
```

이 패턴 — 리플렉션 객체는 `transient`로 빼고, 재구성 가능한 재료만 스트림에 싣고, `readObject()`에서 복원한다 — 이 이번 PR이 따르는 선례다. 즉 `TypeDescriptor`의 세 필드 중 둘은 이미 직렬화를 감당할 준비가 되어 있었고, 문제는 남은 하나에서 생겼다.

## 2. 수정 전 동작 방식 — 성능 개선이 남긴 캡처

회귀의 출발점은 gh-33948, "Expression performance regression due to missing annotation types on context classes"라는 성능 이슈다. 보고자의 관찰은 이렇다. SpEL 표현식이 애너테이션 없는 클래스(예: Guava 컬렉션)를 다룰 때, `TypeDescriptor`가 매번 애너테이션을 조회하려 들고 그 과정에서 클래스패스 탐색이 일어난다. 단일 스레드에서 약 2배 느려지고, `ClassLoader.loadClass`의 동기화 때문에 동시성이 올라가면 더 나빠진다.

Juergen Hoeller의 해법은 애너테이션 조회를 **필요할 때까지 미루는** 것이었다(`1a573d6e3c7`, 2025-02-07). 생성자에서 즉시 `AnnotatedElementAdapter`를 만들던 코드가 람다로 바뀌었다.

```java
-	private final AnnotatedElementAdapter annotatedElement;
+	private final AnnotatedElementSupplier annotatedElementSupplier;
+
+	@Nullable
+	private volatile AnnotatedElementAdapter annotatedElement;
```

```java
	public TypeDescriptor(Field field) {
		this.resolvableType = ResolvableType.forField(field);
		this.type = this.resolvableType.resolve(field.getType());
		this.annotatedElementSupplier = () -> AnnotatedElementAdapter.from(field.getAnnotations());
	}
```

조회는 접근자 안쪽의 지연 캐시로 옮겨 갔고, 이 부분은 지금도 그대로다.

```java
private AnnotatedElementAdapter getAnnotatedElement() {
	AnnotatedElementAdapter annotatedElement = this.annotatedElement;
	if (annotatedElement == null) {
		annotatedElement = this.annotatedElementSupplier.get();
		this.annotatedElement = annotatedElement;
	}
	return annotatedElement;
}
```

성능 목표만 보면 깔끔한 변경이다. 문제는 필드가 직렬화 가능해야 한다는 제약을 만족시키려고 도입한 전용 인터페이스에 있다.

```java
private interface AnnotatedElementSupplier extends Supplier<AnnotatedElementAdapter>, Serializable {
}
```

`Serializable`을 상속한 함수형 인터페이스의 람다는 자바가 `SerializedLambda`로 직렬화한다. 그런데 `SerializedLambda`는 람다가 **캡처한 값을 전부 함께** 스트림에 쓴다. 여기서 각 생성자의 람다가 캡처하는 값은 정확히 그 디스크립터가 만들어진 리플렉션 객체 자신이다.

| 생성자 | 람다가 캡처하는 값 | 직렬화 가능 |
| --- | --- | --- |
| `TypeDescriptor(Field)` | `java.lang.reflect.Field` | 아니오 |
| `TypeDescriptor(MethodParameter)` | `MethodParameter` | 아니오 |
| `TypeDescriptor(Property)` | `Property` | 아니오 |
| `TypeDescriptor(ResolvableType, Class, Annotation[])` | `Annotation[]` | 예 |

앞의 셋은 지연 조회를 위해 리플렉션 객체를 붙잡아 둘 수밖에 없고, 바로 그것이 직렬화를 막는다. 필드를 인터페이스로 감싸 `Serializable`을 붙인 것은 타입 수준의 선언일 뿐, 캡처된 내용물의 직렬화 가능성까지 보장하지 못한다. 인터페이스가 `Serializable`을 상속한 순간 컴파일러는 통과시키고, 실패는 런타임으로 미뤄진다.

## 3. 무엇이 문제였나 — 재현

실제로 무엇이 터지는지는 열 줄이면 확인된다. 아래는 수정 전 `spring-core` 클래스에 대고 돌린 결과다.

```java
Field field = Repro.class.getField("fieldAnnotated");
TypeDescriptor td = new TypeDescriptor(field);
new ObjectOutputStream(new ByteArrayOutputStream()).writeObject(td);
// java.io.NotSerializableException: java.lang.reflect.Field
```

주목할 점 두 가지가 있다. 첫째, 이 실패는 **애너테이션을 이미 조회한 뒤에도** 똑같이 일어난다. `annotatedElement` 캐시가 채워져도 `annotatedElementSupplier` 필드는 `transient`가 아니고 비워지지도 않으므로, 여전히 스트림에 쓰인다. 위 재현 코드에서 `getAnnotations()`를 먼저 호출해도 결과는 같다. 둘째, 애너테이션이 하나도 없는 필드에서도 똑같이 실패한다. 터지는 것은 애너테이션이 아니라 람다가 붙잡은 `Field` 자체이기 때문이다.

기존 테스트가 이를 놓친 이유도 분명하다.

```java
@Test
void serializable() throws Exception {
	TypeDescriptor typeDescriptor = TypeDescriptor.forObject("");
	...
}
```

`forObject("")`는 `valueOf(String.class)`를 거쳐 `new TypeDescriptor(ResolvableType.forClass(type), null, null)`로 간다. 즉 네 생성자 중 유일하게 멀쩡한 경로, 그것도 애너테이션 배열이 `null`인 경우만 밟는다. 재현 실행에서도 이 경로만 수정 전후 모두 성공했다.

정리하면 수정 전 동작은 다음과 같다. 같은 재현 프로그램을 수정 전/후 클래스에 각각 돌린 결과다.

| 경로 | 수정 전 | 수정 후 |
| --- | --- | --- |
| `forObject("")` | 성공 | 성공 |
| `new TypeDescriptor(Field)` (애너테이션 있음) | `NotSerializableException: java.lang.reflect.Field` | 성공, 애너테이션 보존 |
| `new TypeDescriptor(Field)` (애너테이션 없음) | `NotSerializableException: java.lang.reflect.Field` | 성공 |
| `getElementTypeDescriptor()` | `NotSerializableException: TypeVariableImpl` | 변화 없음 (별건) |

마지막 줄은 이 PR의 범위 밖이다. 그 실패는 애너테이션 공급자가 아니라 디스크립터가 들고 있는 `ResolvableType` 쪽에서 나오며, 수정 전후가 동일하다.

## 4. 수정 해설 — transient로 빼고 어댑터만 실어 보낸다

수정의 핵심 판단은 "람다를 직렬화하려 애쓰지 말고, 애초에 스트림에 싣지 말자"는 것이다. 캡처된 리플렉션 객체가 문제라면, 그 객체를 붙잡은 필드를 스트림에서 빼면 된다. 대신 애너테이션 자체는 이미 직렬화 가능한 `AnnotatedElementAdapter`가 실어 나른다.

```java
-	private final AnnotatedElementSupplier annotatedElementSupplier;
+	private transient AnnotatedElementSupplier annotatedElementSupplier;
```

`transient`를 붙이면 필드에서 `final`이 빠져야 한다. 역직렬화 후 다시 채워 넣어야 하기 때문이다. 그리고 직렬화 훅 두 개가 추가된다.

```java
private void writeObject(ObjectOutputStream outputStream) throws IOException {
	// Resolve the annotations up front since the supplier is transient: it captures
	// the Field/MethodParameter/Property this descriptor has been created from.
	getAnnotatedElement();
	outputStream.defaultWriteObject();
}

private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
	inputStream.defaultReadObject();
	AnnotatedElementAdapter annotatedElement = AnnotatedElementAdapter.from(
			this.annotatedElement != null ? this.annotatedElement.getAnnotations() : null);
	this.annotatedElement = annotatedElement;
	this.annotatedElementSupplier = () -> annotatedElement;
}
```

`writeObject()`는 **지연 조회를 보존하기 위해** 존재한다. 공급자가 스트림에서 빠졌으므로, 애너테이션은 `annotatedElement` 캐시에 담겨야만 건너간다. 그런데 그 캐시는 누군가 애너테이션을 물어봤을 때만 채워진다. 한 번도 물어보지 않은 디스크립터를 그냥 쓰면 `null` 어댑터가 나가고 애너테이션이 조용히 사라진다. 따라서 쓰기 직전에 딱 한 번 조회를 강제한다. 이 시점 선택 덕분에 gh-33948이 얻은 성능 이득은 **직렬화하지 않는 모든 경로에서 그대로 유지된다**. 애너테이션 조회가 늘어나는 것은 실제로 직렬화하는 순간뿐이다.

`readObject()`는 **`EMPTY` 싱글톤 정체성을 되살리기 위해** 존재한다. 복원된 어댑터를 그냥 쓰지 않고 `AnnotatedElementAdapter.from(...)`에 한 번 더 통과시키는 이유가 여기 있다. 어댑터의 빈 판정은 값 비교가 아니라 동일성 비교다.

```java
public boolean isEmpty() {
	return (this == EMPTY);
}
```

`AnnotatedElementAdapter`에는 `readResolve()`가 없으므로, 역직렬화된 빈 어댑터는 `EMPTY`와 다른 인스턴스가 된다. 그대로 두면 `hasAnnotation()`과 `getAnnotation()`의 빠른 경로가 왕복 이후 사라진다. `from(...)`을 다시 태우면 빈 배열이 `EMPTY`로 접혀 들어가 정체성이 복구된다. 마지막으로 공급자 필드에는 복원된 어댑터를 그대로 돌려주는 람다를 넣는다. 이제 이 람다는 리플렉션 객체를 캡처하지 않는다.

한편 이 변경에는 감출 수 없는 대가가 하나 있다. `serialVersionUID` 계산이 달라진다. 재현 프로그램으로 실측한 값은 수정 전 `-4882614078662365050`(직렬화 필드 4개), 수정 후 `1724818276882560505`(3개)다. 즉 이전 버전이 쓴 스트림은 `InvalidClassException`으로 거부된다.

PR은 이전 UID를 고정하는 선택지를 검토한 뒤 의도적으로 채택하지 않았고, 그 근거를 본문에 적어 두었다. UID를 맞춰 두면 옛 스트림의 공급자 필드는 읽혀서 버려지고, 옛 코드는 조회를 강제하지 않았으므로 `annotatedElement`는 `null`인 채로 들어온다. 결과는 **애너테이션의 조용한 소실**이다. `TypeDescriptor`는 `serialVersionUID`를 선언한 적이 없고 `@SuppressWarnings("serial")`이 붙어 있으니 버전 간 스트림 호환은 애초에 계약이 아니었다. 그렇다면 조용히 값을 잃는 것보다 시끄럽게 실패하는 쪽이 낫다. 게다가 `Field`·`MethodParameter`·`Property` 기반 디스크립터가 담긴 옛 스트림은 **존재할 수가 없다** — 그것을 쓰는 일이 바로 지금 실패하는 동작이기 때문이다.

또 하나 밝혀 둘 행동 변화가 있다. 애너테이션 조회가 직렬화 시점에 일어나므로, 애너테이션 클래스가 클래스패스에 없으면 `writeObject()`에서 `TypeNotPresentException`이 올라온다. 이전에는 같은 상황이 `NotSerializableException`으로 나타났다. 둘 다 실패이고, 전자가 원인 정보를 더 많이 담는다.

## 5. 검증 — 테스트가 무엇을 고정하나

테스트 일곱 개가 추가되었고, 각각이 고정하는 대상이 다르다. 앞의 네 개는 **네 생성자를 전부 덮는다**. `serializableWithFieldAnnotations`·`serializableWithMethodParameterAnnotations`·`serializableWithPropertyAnnotations`·`serializableWithAnnotationArray`가 그것이며, 기존 테스트가 한 경로만 밟아 회귀를 놓쳤던 구멍을 정면으로 메운다. 각 테스트는 왕복 후 `getAnnotations()`가 원본과 같은지, 그리고 `hasAnnotation()`이 참인지를 함께 본다. 후자가 중요한 이유는 `isEmpty()` 빠른 경로가 살아 있는지를 간접적으로 확인하기 때문이다.

다섯 번째는 `EMPTY` 정체성을 직접 겨냥한다.

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

이 단언이 성립하는 근거는 어댑터의 접근자에 있다. `getAnnotations()`는 `(isEmpty() ? this.annotations : this.annotations.clone())`을 반환하므로, 두 번 호출해 같은 배열이 나온다는 것은 곧 `isEmpty()`가 참이라는 뜻이다. `readObject()`의 `from(...)` 재호출이 빠지면 이 테스트만 깨진다.

여섯 번째 `serializableWithDerivedTypeDescriptor`는 `getMapValueTypeDescriptor()`로 파생시킨 디스크립터를 왕복시킨다. 파생 디스크립터는 원본의 애너테이션을 물려받으므로, 파생 경로에서도 맥락이 유지되는지를 고정한다.

일곱 번째는 이 수정의 가장 미묘한 성질, 즉 **지연 조회와 직렬화의 타이밍**을 고정한다.

```java
TypeDescriptor typeDescriptor = new TypeDescriptor(methodParameter);
assertThat(resolutionCount).hasValue(0);

TypeDescriptor readObject = serializeAndDeserialize(typeDescriptor);
assertThat(resolutionCount).hasValue(1);
```

`MethodParameter`를 익명 서브클래스로 감싸 `getParameterAnnotations()` 호출 횟수를 센다. 생성 직후는 0이어야 하고(gh-33948의 지연 조회가 살아 있다는 뜻), 직렬화 후에는 정확히 1이어야 한다(`writeObject()`가 조회를 강제했다는 뜻). 두 단언이 함께 있어야 "고치면서 성능 개선을 되돌리지 않았다"가 증명된다.

공통 헬퍼는 왕복과 동등성 확인을 묶는다.

```java
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

`isEqualTo`가 여기 들어간 것이 은근히 중요하다. `TypeDescriptor.equals()`는 타입·제네릭뿐 아니라 `annotationsMatch()`로 애너테이션 배열까지 비교하므로, 왕복이 애너테이션을 잃으면 이 단언에서 먼저 걸린다.

## 6. 상태와 교훈

PR은 2026-08-04에 `fix/typedescriptor-serialization` 브랜치로 제출되어 현재 OPEN, 리뷰어 배정 전이다. 코멘트도 리뷰도 아직 없다. 참고로 커밋 메시지 기준으로는 `f92313cc3e1`이 이 작업의 커밋이다.

교훈은 둘이다. 첫째, **`Serializable`을 상속한 함수형 인터페이스는 직렬화 가능성을 보장하지 않는다.** 그것은 "이 람다를 스트림에 쓰겠다"는 선언일 뿐이고, 실제 성패는 람다가 무엇을 캡처했느냐가 결정한다. 컴파일러는 캡처 내용을 검사하지 않으므로 실패는 전부 런타임으로 미뤄진다. 지연 조회를 위해 람다를 도입할 때 캡처 대상이 리플렉션 객체나 컨텍스트 객체라면, 그 필드는 대개 `transient`여야 하고 재구성 경로가 따로 필요하다. `SerializableTypeWrapper.FieldTypeProvider`가 같은 클래스 계열 안에서 이미 그 답을 보여 주고 있었다.

둘째, **한 경로만 밟는 테스트는 계약이 아니라 그 경로를 지킬 뿐이다.** 기존 `serializable()` 테스트는 이름만 보면 직렬화 계약 전체를 지키는 것 같지만, 실제로는 네 생성자 중 문제가 없는 하나만 통과시켰다. 팩토리 메서드나 생성자가 여러 갈래인 클래스에서 횡단 계약(직렬화·동등성·불변성 같은)을 테스트할 때는, 갈래마다 한 번씩 밟아야 계약이 실제로 고정된다. 이번 회귀가 6.2.1에서 6.2.13 사이에 들어와 릴리스를 여럿 건너 살아남은 것도 그 때문이다.

---

연관 ko-docs (모듈 지도): `spring-core/02-타입-변환-conversion.md` `spring-core/04-타입-리플렉션과-제네릭.md`
