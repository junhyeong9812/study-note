# PR #36933 — 테스트 해설 (테스트 하나하나)

> PR #36933 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 테스트가 아예 없던 `ThrowawayClassLoader`에 테스트 클래스를 새로 만들고 그 안에
테스트 메서드 하나를 넣었다. 메서드는 하나지만 단언은 둘이고, 둘의 성격이 다르다. 하나는
수정 전에 반드시 실패하는 red이고 다른 하나는 수정 전후로 통과해야 하는 가드다. 이
문서는 그 한 메서드를 단언 단위로 쪼개 해설하고, 관찰 불가능한 자원 누수를 관찰 가능한
신호로 바꾸는 픽스처 두 개를 따로 다룬다.

## 1. 리소스 폴백 경로의 스트림 닫힘 — red + 가드 한 세트

이 한 메서드가 폴백 경로를 강제로 태운 뒤 클래스 정의 성공과 스트림 닫힘을 차례로 단언한다.

```java
@Test
void loadingClassFromResourceClosesInputStream() throws Exception {
	String className = Probe.class.getName();
	byte[] classBytes = classBytesOf(className);
	AtomicBoolean closed = new AtomicBoolean();

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
}
```

- **주장 (단언 1, `loaded.getName()`)**: 리소스 폴백 경로가 클래스를 정상적으로 정의해
  돌려준다. 즉 이 수정이 로딩 로직을 건드리지 않았다.
- **주장 (단언 2, `closed`)**: 그 과정에서 열린 `InputStream`이 닫혔다.
- **fix 전 결과와 이유**: 단언 2에서 red다. 판별은 diff의 프로덕션 한 줄로 확정된다.
  수정 전 `loadClassFromResource`는 `try { ... }`였고 `finally`도 try-with-resources도
  없었다. 성공 경로는 `defineClass`의 결과를 곧장 반환하며 빠져나가고, 실패 경로는
  `ClassNotFoundException`을 던지며 빠져나간다. 두 출구 어디에도 `close()`가 없으므로
  `TrackingInputStream.close()`는 호출되지 않고 `closed`는 `false`로 남는다.
- **fix 전 단언 1은 green**: 수정 전에도 `defineClass`는 성공했다. 이 단언은 처음부터
  끝까지 통과하는 양성 가드이며, 존재 이유는 수정 **후**에 있다. try-with-resources를
  도입하면서 반환 값이나 예외 종류가 달라지지 않았음을 고정한다.
- **단언 순서가 의미를 만든다**: 로딩 성공을 먼저 확인하고 닫힘을 나중에 확인한다.
  순서가 반대라면, 스트림이 닫히긴 했지만 클래스 정의는 실패한 상태도 통과해 버릴 수
  있다. 실패 메시지의 정보량 관점에서도 이 순서가 낫다. 클래스 로딩부터 깨졌다면
  단언 1이 먼저 알려 준다.
- **fix 후**: `try (inputStream)`이 성공 경로에서는 `defineClass`의 결과를 반환하기
  직전에 스트림을 닫고, `ClassFormatError`가 나도 닫은 뒤 에러를 전파한다. 두 단언이
  모두 통과한다.
- **`as("InputStream closed")`의 역할**: `AtomicBoolean`에 대한 `isTrue()` 실패 메시지는
  기본적으로 "expected true but was false"에 그친다. 설명을 붙여 두면 실패 로그만 보고도
  무엇이 안 닫혔는지 읽힌다.

## 2. `TrackingInputStream` — 보이지 않는 누수를 신호로 바꾸는 장치

첫 픽스처는 `close()` 호출 하나만 가로채 플래그로 기록하는 얇은 데코레이터다.

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

- **흉내 내는 실제 대상**: 프로덕션에서 `getResourceAsStream`이 돌려주는 스트림은
  클래스패스가 jar이면 열린 zip 엔트리와 네이티브 inflater 버퍼를, 디렉터리이면 파일
  디스크립터를 붙들고 있는 물건이다. 그 OS 자원의 반환 여부는 테스트에서 직접 관측할 수
  없다. 이 데코레이터가 하는 일은 관측 불가능한 자원 반환을 관측 가능한 boolean 플래그
  하나로 번역하는 것이다.
- **`FilterInputStream`을 고른 이유**: `InputStream`의 모든 읽기 메서드를 직접 구현하지
  않고 위임하기 위해서다. 재정의는 `close()` 하나뿐이고, `transferTo`가 쓰는 읽기 경로는
  안쪽 `ByteArrayInputStream`이 그대로 처리한다. 즉 이 픽스처는 동작을 바꾸지 않고
  한 지점만 계측한다.
- **`super.close()`를 반드시 부르는 이유**: 플래그만 세우고 실제 닫기를 생략하면
  데코레이터가 프로덕션 스트림의 계약을 왜곡한다. 이 테스트에서는 안쪽이
  `ByteArrayInputStream`이라 실질 효과가 없지만, 데코레이터가 지켜야 할 규약을 지키는
  형태로 두는 편이 옳다.
- **`AtomicBoolean`인 이유**: 값을 람다와 익명 클래스 바깥에서 읽어야 하므로 지역
  변수를 직접 쓸 수 없다. 가변 홀더가 필요하고, `AtomicBoolean`이 그 역할을 하는 가장
  짧은 표준 타입이다. 동시성 요구가 있어서가 아니다.

## 3. 이중 익명 클래스로더 — 폴백 경로를 결정론적으로 강제하는 장치

둘째 픽스처는 로더를 두 겹으로 쌓아 위임이 반드시 실패하도록 만든다.

```java
ClassLoader resourceLoader = new ClassLoader(new ClassLoader(null) {}) {
	@Override
	public InputStream getResourceAsStream(String name) {
		return new TrackingInputStream(new ByteArrayInputStream(classBytes), closed);
	}
};
```

- **문제**: `loadClassFromResource`는 `super.loadClass`가 실패해야만 호출된다. 위임이
  성공해 버리면 검증하려는 코드에 도달조차 하지 못한다.
- **해법의 근거는 생성자다**. `ThrowawayClassLoader(ClassLoader parent)`는
  `super(parent.getParent())`로 **조부모**를 자기 부모로 삼고, 넘겨받은 `parent`는
  `resourceLoader` 필드에 따로 보관한다. 그러므로 테스트는 로더를 두 겹 쌓는다.
  바깥 익명 로더가 `resourceLoader`가 되고, 그 부모인 `new ClassLoader(null) {}`이
  `ThrowawayClassLoader`의 실제 부모가 된다.
- **`new ClassLoader(null) {}`의 의미**: 부모가 `null`인 로더는 부트스트랩 클래스만
  해석한다. 테스트용 `Probe`는 애플리케이션 클래스패스에 있으므로 여기서 반드시 실패하고,
  그 `ClassNotFoundException`이 곧 폴백 진입 신호가 된다. 확률적으로가 아니라 구조적으로
  실패하므로 이 테스트는 결정론적이다.
- **흉내 내는 실제 배치**: 프로덕션에서는 `PreComputeFieldFeature`가
  `new ThrowawayClassLoader(getClass().getClassLoader())`로 로더를 만든다. 그때 넘어가는
  애플리케이션 클래스로더가 여기서는 바깥 익명 로더이고, 그것이 jar나 디렉터리에서
  `.class` 바이트를 공급하는 역할을 대신한다. 즉 이 두 겹 구조는 인위적 트릭이 아니라
  프로덕션 배치를 최소 형태로 옮겨 놓은 것이다.
- **`getResourceAsStream`만 재정의한 이유**: `ThrowawayClassLoader`가 `resourceLoader`에서
  쓰는 API가 그것 하나뿐이다. 접점이 하나이므로 재정의도 하나면 된다.

## 4. 픽스처와 헬퍼

나머지 둘은 정의 대상 클래스와 그 실제 바이트를 읽어 오는 헬퍼다.

```java
static class Probe {
}
```

```java
private static byte[] classBytesOf(String className) throws IOException {
	String resourceName = className.replace('.', '/') + ".class";
	try (InputStream in = ThrowawayClassLoaderTests.class.getClassLoader().getResourceAsStream(resourceName)) {
		assertThat(in).as("class bytes for %s", className).isNotNull();
		return in.readAllBytes();
	}
}
```

- **`Probe`**: 본문이 빈 정적 중첩 클래스다. 이 로더가 실제로 정의해 볼 대상이며, 필드도
  메서드도 없어야 하는 이유는 이 테스트가 검증하는 것이 클래스의 내용이 아니라 정의
  성공 여부뿐이기 때문이다. 프로덕션에서 이 자리에 오는 것은
  `org.springframework.core.NativeDetector` 같은 실제 클래스다.
- **바이트가 진짜여야 하는 이유**: 임의의 바이트 배열을 넣으면 `defineClass`가
  `ClassFormatError`로 실패하고, 그러면 "닫힘"은 확인해도 "정상 로딩 보존"은 확인할 수
  없다. 그래서 헬퍼가 테스트 클래스로더에서 `Probe`의 실제 클래스 파일을 읽어 온다.
- **헬퍼 안의 `isNotNull()` 단언**: 이것은 검증이 아니라 안전장치다. 클래스 파일을 못
  읽었을 때 `NullPointerException` 대신 "class bytes for ..."라는 문장으로 실패하게
  만들어, 픽스처 준비 실패와 대상 코드의 결함을 구별할 수 있게 한다.
- **헬퍼 자신이 try-with-resources를 쓴다**: 검증 대상이 스트림 닫기이므로, 테스트 코드
  자신이 같은 결함을 저지르지 않도록 하는 형식상의 일관성이기도 하다.

## 실측과 역할 요약

이 PR의 테스트 한 건과 픽스처 셋에 대해 확인된 사실을 모아 둔다.

- 실측 기록: PR 본문은 회귀 테스트가 "추적 가능한 `InputStream`을 리소스 폴백 경로로
  흘려보내 닫힘을 검증한다"고만 적었고, 실행 결과 수치는 남기지 않았다. 총 테스트 수나
  실패 건수는 판별 근거 부족으로 남긴다.
- 테스트 메서드 1건. 그 안에서 단언 단위로 보면 red 1개(`closed`)와 양성 가드
  1개(`loaded.getName()`)의 한 세트다.
- 픽스처 3종의 역할이 각각 다르다. `TrackingInputStream`은 관측 불가능한 자원 반환을
  관측 가능하게 만들고, 이중 익명 클래스로더는 검증 대상 분기를 결정론적으로 강제하며,
  `Probe`와 `classBytesOf`는 성공 경로가 끝까지 도달하도록 진짜 입력을 공급한다.
- 이 파일은 이후 PR #36938이 테스트를 하나 더 얹는 토대가 된다. 그 시점부터 이
  테스트는 성공 경로를 지키는 가드 역할까지 겸하게 된다.
