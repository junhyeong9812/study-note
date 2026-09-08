# PR #36933 — Close class resource `InputStream` in `ThrowawayClassLoader`

## 0. 정향

이 문서는 Spring Framework 기여 PR #36933을 처음부터 재구성하기 위한 해설이다. 다루는 코드는 GraalVM 네이티브 이미지 빌드에만 쓰이는 내부 클래스로더 `ThrowawayClassLoader`이며, 바뀐 줄은 단 하나다. 그러나 그 한 줄이 왜 필요한지는 이 클래스가 무엇을 위해 존재하는지를 알아야 보인다. 그래서 배경과 구조부터 시작해 문제, 수정, 검증 순으로 따라간다.

기준 소스는 이 저장소의 `upstream/main`이며, 수정 전 코드는 커밋 `03d80feed0f`의 부모에서 읽었다.

## 1. 배경 — 이 클래스는 무엇을 하는 물건인가

`ThrowawayClassLoader`는 클래스의 static 초기화 부작용을 본체 이미지에 남기지 않고 그 클래스를 한 번 읽어보기 위한 일회용 클래스로더다. 이름 그대로 쓰고 버리는 용도이며, 패키지는 `org.springframework.aot.nativex.feature`, 가시성은 패키지 프라이빗이다. 공개 API가 아니므로 사용자가 직접 호출할 일은 없다.

유일한 소비자는 같은 패키지의 `PreComputeFieldFeature`다. 이것은 GraalVM의 `Feature` 구현으로, 네이티브 이미지 빌드 도중 특정 `static final boolean` 필드의 값을 미리 계산해 이미지에 박아 넣는다. 대상은 아래 패턴에 걸리는 필드들이다.

```java
private static final Pattern[] patterns = {
		Pattern.compile(Pattern.quote("org.springframework.core.NativeDetector#inNativeImage")),
		Pattern.compile(Pattern.quote("org.springframework.cglib.core.AbstractClassGenerator#inNativeImage")),
		Pattern.compile(Pattern.quote("org.springframework.aot.AotDetector#inNativeImage")),
		Pattern.compile(Pattern.quote("org.springframework.") + ".*#.*Present"),
		Pattern.compile(Pattern.quote("org.springframework.") + ".*#.*PRESENT"),
		Pattern.compile(Pattern.quote("reactor.core.") + ".*#.*Available"),
		Pattern.compile(Pattern.quote("org.apache.commons.logging.LogAdapter") + "#.*Present")
};
```

여기서 딜레마가 생긴다. 필드 값을 읽으려면 그 클래스의 static 초기화가 실행되어야 한다. 그런데 빌드 클래스로더로 초기화해 버리면 그 클래스는 "빌드 시점에 초기화된 클래스"로 이미지에 고정되고, 런타임에 다시 초기화될 기회를 잃는다. 이는 GraalVM에서 build-time initialization 문제로 알려진 함정이다.

해법이 일회용 클래스로더다. 같은 클래스의 별도 복제본을 격리된 로더에서 정의하고, 그 복제본의 static 초기화 결과만 읽어 온 뒤 로더째 버린다. `PreComputeFieldFeature`의 호출 경로가 정확히 그 모습이다.

```java
private Object provideFieldValue(Field field)
		throws ClassNotFoundException, NoSuchFieldException, IllegalAccessException {

	Class<?> throwawayClass = this.throwawayClassLoader.loadClass(field.getDeclaringClass().getName());
	Field throwawayField = throwawayClass.getDeclaredField(field.getName());
	throwawayField.setAccessible(true);
	return throwawayField.get(null);
}
```

여기서 알아 둘 개념이 세 가지다. 첫째는 부모 위임 모델이다. 자바 클래스로더는 요청받은 클래스를 스스로 정의하기 전에 부모에게 먼저 물어보고, 부모가 이미 로드했다면 그 클래스를 그대로 돌려준다. 둘째는 `defineClass`로, 바이트 배열을 받아 이 로더 소유의 새 `Class` 객체를 만드는 연산이다. 셋째는 `loadClass` 계약으로, 클래스를 찾지 못하면 `null`을 반환하는 것이 아니라 `ClassNotFoundException`을 던져야 한다는 규약이다. 참고로 `findClass`는 위임이 실패한 뒤 하위 클래스가 직접 클래스를 찾도록 마련된 확장 지점이지만, 이 클래스는 `findClass` 대신 `loadClass(String, boolean)` 자체를 재정의하는 길을 택했다.

부모 위임을 어떻게 비껴가는지가 이 클래스의 핵심 트릭이며, 생성자에 압축되어 있다.

```java
ThrowawayClassLoader(ClassLoader parent) {
	super(parent.getParent());
	this.resourceLoader = parent;
}
```

넘겨받은 로더를 부모로 삼지 않고 그 로더의 부모, 즉 조부모를 부모로 삼는다. 그리고 넘겨받은 로더는 `resourceLoader` 필드에 따로 보관한다. 결과적으로 애플리케이션 클래스는 위임으로 해결되지 않고, 대신 `resourceLoader`에서 바이트만 얻어 이 로더가 직접 정의하게 된다. 부모 체인을 한 칸 건너뛰는 이 배치가 격리를 만든다.

## 2. 수정 전 동작 방식

수정 전 흐름은 "먼저 위임, 실패하면 리소스에서 직접 정의"라는 2단 구조였다. 진입점은 재정의된 `loadClass`다.

```java
@Override
protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
	synchronized (getClassLoadingLock(name)) {
		Class<?> loaded = findLoadedClass(name);
		if (loaded != null) {
			return loaded;
		}
		try {
			return super.loadClass(name, true);
		}
		catch (ClassNotFoundException ex) {
			return loadClassFromResource(name);
		}
	}
}
```

순서대로 읽으면 이렇다. 이름별 락을 잡고, 이미 이 로더가 정의한 클래스가 있으면 그대로 돌려준다. 없으면 `super.loadClass`로 조부모 체인에 위임한다. 이 체인에는 애플리케이션 클래스패스가 없으므로 대상 클래스는 대개 여기서 실패한다. 그 실패가 곧 2단계 신호가 되어 `loadClassFromResource`로 넘어간다.

실제로 클래스를 만들어 내는 곳은 그 두 번째 단계다.

```java
private Class<?> loadClassFromResource(String name) throws ClassNotFoundException, ClassFormatError {
	String resourceName = name.replace('.', '/') + ".class";
	InputStream inputStream = this.resourceLoader.getResourceAsStream(resourceName);
	if (inputStream == null) {
		return null;
	}
	try {
		ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
		inputStream.transferTo(outputStream);
		byte[] bytes = outputStream.toByteArray();
		return defineClass(name, bytes, 0, bytes.length);

	}
	catch (IOException ex) {
		throw new ClassNotFoundException("Cannot load resource for class [" + name + "]", ex);
	}
}
```

클래스 이름을 리소스 경로로 바꾸고, 보관해 둔 `resourceLoader`에게 스트림을 요청한다. 스트림이 `null`이면 그런 리소스가 없다는 뜻이므로 `null`을 반환한다. 스트림이 있으면 전부 읽어 바이트 배열로 만들고 `defineClass`로 이 로더 소유의 클래스를 정의한다. 읽는 도중 `IOException`이 나면 `ClassNotFoundException`으로 감싸 던진다.

이 코드는 기능적으로는 의도대로 동작한다. 그러나 열린 스트림이 어디에서도 닫히지 않는다는 점만은 다르다.

## 3. 무엇이 문제였나

문제는 단순하다. `getResourceAsStream`이 연 `InputStream`이 어떤 경로에서도 `close()`되지 않는다. `try` 블록에는 `finally`도 없고 try-with-resources도 아니다. 성공 경로에서는 `defineClass`의 결과를 곧장 반환하며 빠져나가고, 실패 경로에서는 `ClassNotFoundException`을 던지며 빠져나간다. 두 경우 모두 스트림은 열린 채 남는다.

왜 실질 피해인가를 보려면 이 메서드가 몇 번 불리는지 세어 봐야 한다. `PreComputeFieldFeature`는 `registerSubtypeReachabilityHandler(this::iterateFields, Object.class)`로 등록되므로, 도달 가능한 모든 타입에 대해 콜백을 받는다. 그중 패턴에 걸리는 `static final boolean` 필드마다 `provideFieldValue`가 호출되고, 그때마다 `loadClass`가 위임 실패를 거쳐 리소스 경로로 내려간다. 즉 이미지 빌드 한 번에 이 경로가 반복해서 실행된다.

누수되는 것은 자바 객체가 아니라 그 아래의 OS 자원이다. 클래스패스가 jar이면 스트림은 열린 zip 엔트리와 네이티브 inflater 버퍼를 붙들고, 디렉터리면 파일 디스크립터를 붙든다. 이것들은 가비지 컬렉터가 해당 스트림 객체를 수거할 때까지, 그리고 정리 로직이 있는 경우에 한해서만 반환된다. 언제 수거될지는 보장되지 않으므로, 피해는 "항상 터지는 버그"가 아니라 "빌드 규모가 커질수록 확률이 오르는 비결정적 고갈"의 형태로 나타난다.

구체적인 증상은 세 가지 방향이다. 디스크립터 한도가 낮은 CI 컨테이너에서는 빌드 후반부에 `Too many open files`가 나올 수 있다. 윈도우에서는 열린 핸들이 jar 파일을 잠가 후속 단계의 삭제나 교체를 막는다. 그리고 inflater 버퍼가 쌓이면 빌드 프로세스의 메모리 사용이 필요 이상으로 늘어난다.

`IOException` 경로는 더 나쁘다. 스트림이 이미 이상 상태일 때 그대로 버려지므로, 하필 자원이 부족한 상황에서 자원 반환이 가장 확실하게 누락된다. 정리하면 이 결함은 기능을 깨뜨리지 않는 대신, 실패 지점을 코드에서 멀리 떨어뜨려 놓는 종류의 결함이다.

## 4. 수정 해설

수정은 기존 `inputStream` 변수를 try-with-resources의 자원으로 채택하는 것 하나다. 프로덕션 코드 변경은 다음 한 줄이다.

```java
-		try {
+		try (inputStream) {
```

이 형태는 자바 9에서 도입된 문법으로, 이미 선언된 변수가 final이거나 실질적으로 final이면 괄호 안에 이름만 적어 자원으로 쓸 수 있다. 여기서 `inputStream`은 한 번 대입된 뒤 재대입되지 않으므로 조건을 만족한다.

왜 스트림 획득 자체를 `try (InputStream in = ...)`로 감싸지 않았는지가 설계상의 요점이다. 그렇게 바꾸면 `null` 검사 후 조기 반환하는 구조를 함께 손봐야 하고, 변경 범위가 넓어진다. 기존 변수를 자원으로 채택하면 `null` 검사와 조기 반환은 그대로 두면서 닫기만 추가된다. 최소 변경으로 불변식 하나를 더한 셈이다.

동작 보존도 함께 보자. 자원 선언이 추가되어도 `try` 블록 본문, `catch (IOException)` 절, 반환 값, 던지는 예외의 종류는 그대로다. 성공 경로에서는 `defineClass`의 결과를 반환하기 직전에 스트림이 닫히고, `defineClass`가 `ClassFormatError`를 던져도 스트림은 닫힌 뒤 에러가 전파된다.

한 가지 미묘한 이점이 더 있다. try-with-resources에서 자원의 `close()`는 같은 `try` 문의 `catch` 절보다 먼저 실행된다. 따라서 닫는 도중 발생한 `IOException` 역시 아래의 `catch (IOException ex)`에 잡혀 `ClassNotFoundException`으로 변환된다. 본문과 `close()`가 동시에 실패하면 후자는 suppressed 예외로 첨부되어 원인 정보가 사라지지 않는다.

수정 후 메서드의 최종 형태는 다음과 같다.

```java
private Class<?> loadClassFromResource(String name) throws ClassNotFoundException, ClassFormatError {
	String resourceName = name.replace('.', '/') + ".class";
	InputStream inputStream = this.resourceLoader.getResourceAsStream(resourceName);
	if (inputStream == null) {
		return null;
	}
	try (inputStream) {
		ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
		inputStream.transferTo(outputStream);
		byte[] bytes = outputStream.toByteArray();
		return defineClass(name, bytes, 0, bytes.length);
	}
	catch (IOException ex) {
		throw new ClassNotFoundException("Cannot load resource for class [" + name + "]", ex);
	}
}
```

## 5. 검증

이 클래스에는 테스트가 아예 없었으므로 PR은 `ThrowawayClassLoaderTests`를 새로 만들었다. 테스트 하나가 두 가지를 동시에 고정한다. 하나는 새 불변식인 "스트림이 닫힌다"이고, 다른 하나는 기존 동작인 "클래스가 정상 로드된다"이다.

닫힘을 관찰하는 장치는 `FilterInputStream`을 상속한 작은 데코레이터다. 자원 누수는 눈에 보이지 않으므로 관찰 가능한 신호로 바꾸는 것이 첫 과제다.

```java
private static final class TrackingInputStream extends FilterInputStream {

	private final AtomicBoolean closed;

	TrackingInputStream(InputStream in, AtomicBoolean closed) {
		super(in);
		this.closed = closed;
	}

	@Override
	public void close() throws IOException {
		this.closed.set(true);
		super.close();
	}
}
```

두 번째 과제는 리소스 대체 경로를 확실히 타게 만드는 것이다. 위임이 성공해 버리면 `loadClassFromResource`는 아예 호출되지 않으므로, 테스트는 부모 체인을 직접 조립해 위임이 실패하도록 강제한다.

```java
// The grandparent resolves bootstrap classes only, so super.loadClass(...)
// fails for the probe class and ThrowawayClassLoader falls back to loading it
// from the resource stream provided below.
ClassLoader resourceLoader = new ClassLoader(new ClassLoader(null) {}) {
	@Override
	public InputStream getResourceAsStream(String name) {
		return new TrackingInputStream(new ByteArrayInputStream(classBytes), closed);
	}
};

ThrowawayClassLoader classLoader = new ThrowawayClassLoader(resourceLoader);
Class<?> loaded = classLoader.loadClass(className);

assertThat(loaded.getName()).isEqualTo(className);
assertThat(closed).as("InputStream closed").isTrue();
```

여기서 `new ClassLoader(null) {}`가 조부모다. 부모가 `null`이므로 부트스트랩 클래스만 해석하며, 테스트용 `Probe` 클래스는 찾지 못한다. `ThrowawayClassLoader`는 생성자에서 조부모를 자기 부모로 삼으므로 `super.loadClass`가 실패하고, 곧바로 대체 경로로 내려가 위에서 심어 둔 `TrackingInputStream`을 받는다.

바이트는 진짜여야 한다. `defineClass`가 성공해야 "기존 동작 보존"까지 확인할 수 있기 때문에, 테스트는 `Probe`의 실제 클래스 파일을 읽어 넣는다.

```java
private static byte[] classBytesOf(String className) throws IOException {
	String resourceName = className.replace('.', '/') + ".class";
	try (InputStream in = ThrowawayClassLoaderTests.class.getClassLoader().getResourceAsStream(resourceName)) {
		assertThat(in).as("class bytes for %s", className).isNotNull();
		return in.readAllBytes();
	}
}
```

두 assertion의 역할은 서로 다르다. `loaded.getName()` 검사는 수정이 로딩 로직을 건드리지 않았음을 고정한다. `closed` 검사는 이번에 추가된 불변식을 고정하며, 수정 전 코드에서는 반드시 실패한다. 즉 이 테스트는 결함을 실제로 재현하는 회귀 테스트다.

참고로 현재 `upstream/main`의 같은 파일에는 테스트가 하나 더 있다. `loadClassThrowsClassNotFoundExceptionWhenClassResourceIsMissing`은 후속 PR #36938에서 추가된 것으로, 이 PR의 범위는 아니다.

## 6. 상태와 교훈

상태부터 정리하면 이 PR은 병합되었다. GitHub 상의 상태는 `CLOSED`이고 `mergedAt`은 비어 있지만, 메인테이너 `sbrannen`이 "This has been merged into `main`."이라고 남겼고, 실제로 `upstream/main`에는 커밋 `03d80feed0f`("Close class resource InputStream in ThrowawayClassLoader", `Closes gh-36933`)로 반영되어 있다. Spring 프로젝트는 기여 커밋을 직접 적용한 뒤 PR을 닫는 방식을 쓰므로 이 조합이 곧 병합을 뜻한다. 코드 리뷰 코멘트는 없었고, 수정 요구도 없었다.

첫 번째 교훈은 자원 수명은 성공 경로가 아니라 예외 경로에서 판정하라는 것이다. 이 코드가 잘못된 이유는 `close()`를 잊어서라기보다, 반환과 예외라는 두 출구를 가진 블록에 출구별 정리가 없었기 때문이다. try-with-resources는 새 변수를 선언할 때만 쓰는 문법이 아니며, 이미 있는 실질적 final 변수를 자원으로 채택하면 구조를 거의 건드리지 않고 모든 출구를 덮을 수 있다.

두 번째 교훈은 테스트하기 어려워 보이는 대상도 의존성 배치를 조작하면 특정 분기를 결정론적으로 강제할 수 있다는 것이다. 클래스로더는 전역 상태처럼 느껴지지만, 여기서는 부모를 `null`로 둔 로더 하나와 `getResourceAsStream` 재정의만으로 대체 경로를 확실히 태웠다. 그리고 이렇게 한 클래스를 끝까지 읽는 과정에서 인접 결함이 드러났고, 그것이 후속 PR #36938로 이어졌다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
