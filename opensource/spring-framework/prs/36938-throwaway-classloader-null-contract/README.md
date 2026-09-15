# PR #36938 — Throw `ClassNotFoundException` for missing class resource in `ThrowawayClassLoader`

## 0. 정향

이 문서는 GraalVM native image 빌드 전용 클래스로더인 `ThrowawayClassLoader`가 `loadClass`에서 `null`을 반환하던 계약 위반을 바로잡은 기여를 다룬다.\
변경 자체는 catch 블록 4줄이지만, 그 4줄이 왜 필요한지는 이 로더가 왜 존재하고 어떤 3단 로딩을 하는지 알아야 보인다.\
그래서 배경, 수정 전 동작, 문제, 수정, 검증 순서로 읽는다.\
대상 코드는 `spring-core/src/main/java/org/springframework/aot/nativex/feature/ThrowawayClassLoader.java` 하나이며, 소비자는 같은 패키지의 `PreComputeFieldFeature` 하나뿐이다.

> **GraalVM native image** — 자바 프로그램을 JVM 없이 바로 실행되는 네이티브 실행 파일로 미리 컴파일하는 빌드 방식.\
> 예: 빌드 시점에 도달 가능한 클래스를 모두 분석해 이미지에 넣어 두므로, 런타임에 클래스를 새로 찾아 로드하는 일이 없다.

## 1. 배경 — `ThrowawayClassLoader`는 무엇인가

`ThrowawayClassLoader`는 GraalVM native image 빌드 시점에 클래스를 "build-time initialization을 유발하지 않고" 읽기 위한 일회용 클래스로더다.\
패키지 전용(package-private) 클래스이고 `@since 6.0`, 원저자는 Phillip Webb이다.\
이름 그대로 한 번 쓰고 버리는 로더이며, 애플리케이션 런타임에는 등장하지 않는다.

> **패키지 전용(package-private)** — 접근 제어자를 붙이지 않아 같은 패키지 안에서만 보이는 가시성.\
> 예: `ThrowawayClassLoader`는 `org.springframework.aot.nativex.feature` 밖에서는 이름조차 참조할 수 없다.

존재 이유는 static 초기화의 부작용 회피다.\
native image 빌드에서 어떤 클래스를 정상 경로로 로드하면 그 클래스의 `static` 초기화가 빌드 시점에 실행되고, 그 결과가 이미지 힙에 그대로 굳어버린다.\
특정 `static final boolean` 필드의 값만 훔쳐보고 싶은데 부작용까지 이미지에 새겨지면 곤란하다.\
그래서 별도 로더로 클래스 바이트를 다시 `defineClass`해 원본 클래스와 분리된 사본을 만든다.

> **build-time initialization** — 클래스의 `static` 초기화 블록을 런타임이 아니라 네이티브 이미지 빌드 시점에 실행해 그 결과를 이미지에 굳혀 넣는 것.\
> 예: 빌드 중에 열린 파일 핸들이나 계산된 시각이 실행 파일에 그대로 박혀 나가는 식의 부작용이 생긴다.

> **`defineClass`** — 클래스의 바이트 배열을 받아 그 로더가 소유하는 `Class` 객체를 직접 만들어 내는 `ClassLoader`의 메서드.\
> 예: 같은 이름 `org.springframework.core.NativeDetector`라도 정의한 로더가 다르면 JVM은 서로 다른 클래스로 취급한다.

핵심 트릭은 생성자에 있다.\
부모를 인자로 받은 `parent`가 아니라 `parent.getParent()`로 설정하고, `parent`는 리소스 공급자로만 보관한다.

```java
private final ClassLoader resourceLoader;


ThrowawayClassLoader(ClassLoader parent) {
	super(parent.getParent());
	this.resourceLoader = parent;
}
```

이렇게 하면 위임 체인에서 애플리케이션 클래스로더(=`parent`)가 빠진다.\
애플리케이션 클래스는 위임으로 풀리지 않으므로 반드시 리소스 폴백을 거쳐 이 로더가 직접 정의하게 되고, 원본 클래스로더가 이미 초기화한 사본과 섞이지 않는다.\
반면 JDK 부트스트랩 클래스는 조부모 체인으로 그대로 풀린다.

> **위임 체인 / 부모 위임(parent delegation)** — 클래스로더가 자기가 찾기 전에 먼저 부모에게 물어보는 자바의 기본 규칙.\
> 예: `java.lang.Object`는 어느 로더에 요청해도 부모를 타고 올라가 부트스트랩 로더 하나에서만 나온다.

호출 경로는 짧고 단일하다.\
`META-INF/native-image/org.springframework/spring-core/native-image.properties`가 `--features=org.springframework.aot.nativex.feature.PreComputeFieldFeature`로 feature를 등록하고, 그 `PreComputeFieldFeature`가 필드 하나로 로더를 붙든다.

```java
private final ThrowawayClassLoader throwawayClassLoader = new ThrowawayClassLoader(getClass().getClassLoader());
```

> **Feature(GraalVM Feature SPI)** — native image 빌드 도구가 빌드 단계마다 불러 주는 확장 지점 인터페이스.\
> 예: `--features=...PreComputeFieldFeature`로 등록하면 분석 단계 전에 `beforeAnalysis`가 호출된다.

`PreComputeFieldFeature`는 `NativeDetector#inNativeImage`나 `...Present` 같은 패턴에 매칭되는 `static final boolean` 필드를 찾아, 빌드 시점에 값을 미리 계산해 상수로 박아 넣는다.\
값을 읽는 지점이 바로 이 로더의 유일한 소비 지점이다.

```java
private Object provideFieldValue(Field field)
		throws ClassNotFoundException, NoSuchFieldException, IllegalAccessException {

	Class<?> throwawayClass = this.throwawayClassLoader.loadClass(field.getDeclaringClass().getName());
	Field throwawayField = throwawayClass.getDeclaredField(field.getName());
	throwawayField.setAccessible(true);
	return throwawayField.get(null);
}
```

여기서 알아야 할 개념이 `ClassLoader.loadClass`의 계약이다.\
`java.lang.ClassLoader`의 문서는 이 메서드가 요청한 클래스의 non-null `Class` 객체를 반환하거나, 찾지 못하면 `ClassNotFoundException`을 던진다고 규정한다.\
"찾지 못함"을 `null`로 표현하는 선택지는 계약에 없다.\
그래서 위 코드처럼 모든 호출자는 반환값을 즉시 역참조한다.

> **`loadClass` 반환 계약** — "non-null `Class`를 돌려주거나 `ClassNotFoundException`을 던진다" 둘 중 하나만 허용하는 약속.\
> 예: 호출자는 `loadClass(...).getDeclaredField(...)`처럼 널 검사 없이 바로 이어 쓰는 것이 정상이다.

이 구분은 단순한 형식 논쟁이 아니다.\
`ClassNotFoundException`은 "무엇을 못 찾았는지"를 클래스명과 cause로 실어 나르는 도메인 예외이고, `NullPointerException`은 "누군가 계약을 어겼다"는 사후 증상일 뿐 어떤 클래스가 문제였는지 알려주지 않는다.\
계약 위반의 실질 비용은 대부분 이 진단 정보의 소실로 나타난다.

> **cause(원인 예외)** — 예외 안에 중첩해 담는 "이 예외를 유발한 더 아래층의 예외".\
> 예: `ClassNotFoundException`의 cause에 JDK 로더가 붙인 상세가 들어 있으면 어느 층에서 끊겼는지 추적할 수 있다.

## 2. 수정 전 동작 방식

수정 전 `loadClass`는 3단 로딩이었다.\
아래는 커밋 `03d80feed0f` 시점, 즉 이 PR 직전의 실코드다.

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

한 번의 `loadClass` 요청이 이 안에서 어떻게 갈라지는지를 세로로 펴면 다음과 같다.\
왼쪽은 단계, 오른쪽은 그 단계가 정하는 것이다.

```text
 PreComputeFieldFeature#provideFieldValue        무엇을 정하나
   |
   | loadClass("org.springframework.core.NativeDetector")
   v
 [1] findLoadedClass(name)                       이 로더가 이미 정의했나
   |
   +-- non-null --> return loaded                그대로 반환하고 끝
   |
   v  null
 [2] super.loadClass(name, true)                 조부모 체인이 풀어 주나
   |
   +-- 성공 -----> return Class                  JDK/부트스트랩 클래스는 여기서 끝
   |
   v  ClassNotFoundException ex                  앱 클래스의 정상 흐름 신호
 [3] loadClassFromResource(name)                 .class 바이트를 구할 수 있나
   |
   +-- getResourceAsStream != null
   |     --> defineClass(...) --> return Class   사본 탄생. 이 로더의 존재 이유
   |
   +-- getResourceAsStream == null
   |     --> return null                         "리소스 없음" 내부 신호
   |                                             수정 전: 이 null 이 그대로 밖으로
   |
   +-- transferTo 중 IOException
         --> throw ClassNotFoundException        "Cannot load resource for class [...]"
```

1단계는 `findLoadedClass(name)`이다.\
이 로더가 이미 정의한 클래스면 그대로 돌려준다.\
같은 로더가 같은 이름을 두 번 `defineClass`하면 `LinkageError`가 나므로 이 캐시 조회는 필수다.\
`getClassLoadingLock(name)`으로 이름별 락을 잡고, 클래스 최상단의 `registerAsParallelCapable()`이 병렬 로딩을 활성화한다.

> **`LinkageError`** — 같은 로더가 같은 이름의 클래스를 두 번 정의하는 등 클래스 연결 단계에서 규칙이 깨졌을 때 나는 `Error`.\
> 예: `findLoadedClass` 검사를 빼면 같은 이름을 다시 `defineClass`하는 순간 이 에러가 난다.

2단계는 `super.loadClass(name, true)`, 즉 표준 부모 위임이다.\
앞서 본 대로 부모는 조부모로 치환돼 있으므로 여기서 풀리는 것은 사실상 부트스트랩/플랫폼 클래스다.\
애플리케이션 클래스는 여기서 `ClassNotFoundException`으로 실패하는 것이 정상 흐름이다.

3단계는 그 `ClassNotFoundException`을 잡아 실행하는 리소스 폴백이다.\
클래스명을 `.class` 리소스 경로로 바꿔 `resourceLoader`에서 바이트를 읽고 직접 정의한다.

> **`getResourceAsStream`** — 클래스패스에서 주어진 경로의 파일을 열어 `InputStream`으로 돌려주고, 없으면 `null`을 돌려주는 메서드.\
> 예: `"org/springframework/core/NativeDetector.class"`를 넘기면 그 클래스 파일의 바이트 스트림이 나온다.

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

즉 정상 시나리오는 2단계가 실패하고 3단계가 성공하는 흐름이다.\
`PreComputeFieldFeature`가 다루는 `org.springframework.core.NativeDetector` 같은 클래스는 클래스패스에 `.class` 파일이 실재하므로 3단계가 바이트를 얻어 `defineClass`로 사본을 만든다.\
이 경로가 이 로더의 존재 이유 그 자체다.

문제는 3단계마저 실패하는 경우의 표현이다.\
`getResourceAsStream`이 `null`을 주면 `loadClassFromResource`는 `null`을 반환하고, catch 블록은 그 `null`을 그대로 `loadClass`의 반환값으로 흘려보낸다.

## 3. 무엇이 문제였나

`loadClass`가 `null`을 반환할 수 있었고, 이는 `ClassLoader` 계약 위반이다.\
재현 조건은 두 가지가 동시에 성립할 때다.\
첫째, 대상 클래스가 위임 체인(부트스트랩/플랫폼)에서 풀리지 않는다.\
둘째, 그 클래스의 `.class` 리소스를 `resourceLoader`가 제공하지 못한다.\
대표적으로 런타임에 생성된 클래스, 즉 CGLIB 프록시나 JDK 프록시, 또는 `defineClass`로만 존재하고 파일 실체가 없는 클래스가 declaring class인 경우다.

> **런타임 생성 클래스(CGLIB 프록시 · JDK 동적 프록시)** — 실행 중에 바이트코드를 만들어 `defineClass`로 등록한, 디스크에 `.class` 파일이 없는 클래스.\
> 예: `@Transactional` 빈을 감싸는 CGLIB 프록시는 클래스패스를 뒤져도 대응하는 파일을 찾을 수 없다.

> **declaring class(선언 클래스)** — 어떤 필드가 실제로 선언되어 있는 클래스.\
> 예: `provideFieldValue`는 `field.getDeclaringClass().getName()`으로 그 이름을 얻어 로더에 넘긴다.

이때 소비자에서 벌어지는 일은 다음과 같다.\
`provideFieldValue`가 `loadClass`로 `null`을 받고, 바로 다음 줄에서 `throwawayClass.getDeclaredField(field.getName())`를 호출하며 `NullPointerException`이 터진다.\
즉 계약 위반이 호출자 쪽 NPE로 옮겨 붙는 전형적 패턴이다.

여기서 정직해야 할 부분은 피해의 크기다.\
이 NPE는 빌드를 깨뜨리지 않는다.\
`iterateFields`가 광범위한 `catch (Throwable)`로 감싸고 있어서, 예외가 나면 그 필드는 빌드 시점 상수화를 포기하고 런타임 평가로 폴백한다.

```java
catch (Throwable ex) {
	if (verbose) {
		System.out.println("Field " + fieldIdentifier + " will be evaluated at runtime " +
				"due to this error during build time evaluation: " + ex);
	}
}
```

> **광범위 안전망(`catch (Throwable)`)** — 어떤 예외·에러든 가리지 않고 삼켜 상위로 올라가지 못하게 막는 catch.\
> 예: 필드 하나의 상수화가 실패해도 빌드 전체는 초록으로 남고, 그 필드만 런타임 평가로 넘어간다.

그래서 실질 피해는 크래시가 아니라 두 가지다.\
하나는 계약 위반 자체 — 이 클래스는 `ClassLoader`의 하위 타입이므로 상위 타입이 약속한 것을 지켜야 하고, 지금은 지키지 않는다.\
다른 하나는 진단 품질이다.

`-Dspring.native.precompute.log=verbose`로 빌드 로그를 켰을 때 개발자가 보는 문장은 "이 필드는 `NullPointerException` 때문에 런타임 평가로 넘어갑니다"가 된다.\
이 메시지로는 어떤 클래스가 왜 안 잡혔는지 알 수 없고, 오히려 Spring 코드에 널 버그가 있다는 잘못된 인상을 준다.\
반면 `ClassNotFoundException`이 올라오면 메시지에 클래스명이 있어 "이 클래스는 `.class` 리소스가 없다"는 사실이 바로 읽힌다.

> **verbose 로그** — `-Dspring.native.precompute.log=verbose`를 줬을 때만 켜지는, 필드별 상수화 성공·실패 출력.\
> 예: 이 플래그가 꺼져 있으면 실패한 필드가 있어도 빌드 로그에 아무 흔적도 남지 않는다.

같은 입력을 놓고 수정 전후가 무엇이 달라지는지를 나란히 보면 이렇다.

```text
 같은 입력: .class 리소스가 없는 클래스 (CGLIB 프록시 등)

 수정 전                                  수정 후
 +------------------------------------+    +------------------------------------+
 | loadClass -> null 반환             |    | loadClass -> 원본 CNFE 재전파      |
 | getDeclaredField 에서 NPE          |    | 클래스명 + cause 보존              |
 | catch(Throwable) 가 삼킴           |    | catch(Throwable) 가 삼킴           |
 | 런타임 평가로 폴백                 |    | 런타임 평가로 폴백                 |
 | 로그: NullPointerException         |    | 로그: CNFE: 클래스명               |
 +------------------------------------+    +------------------------------------+
```

빌드 결과는 양쪽 모두 "런타임 평가로 폴백, 빌드 성공"으로 같고, 달라지는 것은 로그가 원인을 지목하느냐뿐이다.

정리하면 이것은 크래시 수정이 아니라 계약 정합성과 진단 가능성 수정이다.\
PR 본문에서도 이 점을 "Note on impact" 섹션으로 먼저 밝혔다.\
영향 범위를 부풀리지 않고 정확히 서술하는 편이 리뷰어의 판단을 빠르게 만든다.

## 4. 수정 해설

수정은 catch 블록 하나다.\
`loadClassFromResource`의 결과를 변수로 받아 `null`이면 원래 예외를 재전파한다.

```java
catch (ClassNotFoundException ex) {
	Class<?> loadedFromResource = loadClassFromResource(name);
	if (loadedFromResource == null) {
		throw ex;
	}
	return loadedFromResource;
}
```

설계 선택은 세 가지였고, 각각 이유가 있다.

첫째, 새 예외를 만들지 않고 원래 `ex`를 다시 던진다.\
2단계에서 발생한 `ClassNotFoundException`은 위임 실패의 가장 정확한 정보(클래스명과 JDK 로더가 붙인 cause)를 이미 담고 있다.\
3단계 실패는 "정의할 클래스 바이트도 없었다"는 확인일 뿐 새로운 정보를 추가하지 않는다.\
그러므로 정보량이 많은 원본을 보존하는 편이 낫다.

> **재전파(rethrow)** — 잡아 둔 예외 객체를 가공하지 않고 그대로 다시 던지는 것.\
> 예: `throw ex;`는 새 스택트레이스를 만들지 않고 2단계 실패의 원본 정보를 그대로 위로 올려보낸다.

둘째, 수정 위치를 `loadClassFromResource`가 아니라 호출자인 catch 블록으로 잡았다.\
`loadClassFromResource`가 직접 예외를 던지게 바꿀 수도 있었지만, 그러면 원래 `ex`에 접근할 수 없어 정보가 빈약한 새 예외를 만들어야 한다.\
지금 형태에서 `null`은 "리소스 없음"을 뜻하는 내부 신호로 남고, 그 신호는 유일한 호출자가 즉시 `ClassNotFoundException`으로 번역해 외부로 새지 않는다.

셋째, 정상 경로의 동작은 한 글자도 바뀌지 않는다.\
`findLoadedClass` 히트, 위임 성공, 리소스 폴백 성공 세 경로 모두 이전과 같은 값을 반환한다.\
달라지는 것은 오직 "세 경로가 전부 실패했을 때 무엇을 내보내는가"뿐이다.\
다섯 가지 상황의 반환값을 수정 전후로 나란히 놓으면 그 사실이 한눈에 보인다.

| 상황 | 수정 전 `loadClass` 결과 | 수정 후 `loadClass` 결과 |
| --- | --- | --- |
| 이미 정의된 클래스 | `Class` 객체 | `Class` 객체 |
| 위임으로 해결 | `Class` 객체 | `Class` 객체 |
| 리소스 폴백으로 해결 | `Class` 객체 | `Class` 객체 |
| 리소스 읽기 중 `IOException` | `ClassNotFoundException` | `ClassNotFoundException` |
| 위임 실패 + 리소스 없음 | `null` | `ClassNotFoundException` (원본 재전파) |

표에서 값이 달라지는 행은 마지막 하나뿐이며, 그것이 이 PR의 전부다.

호출자 입장의 결과도 확인해 둘 만하다.\
`provideFieldValue`의 시그니처에는 이미 `throws ClassNotFoundException`이 선언되어 있고, `iterateFields`의 `catch (Throwable)`이 NPE든 CNFE든 똑같이 잡는다.\
따라서 빌드 동작(런타임 평가로 폴백)은 그대로이고, 로그 문장만 의미 있는 것으로 바뀐다.\
기존 동작 보존이 이 수정의 안전성 근거다.

## 5. 검증

테스트는 `spring-core/src/test/java/org/springframework/aot/nativex/feature/ThrowawayClassLoaderTests.java`에 한 개를 추가했다.\
이 테스트 클래스 자체가 인접 기여 #36933에서 새로 만들어진 것이라, 이번 PR은 거기에 메서드를 덧붙였다.

```java
@Test  // gh-36938
void loadClassThrowsClassNotFoundExceptionWhenClassResourceIsMissing() {
	// The grandparent resolves bootstrap classes only, so super.loadClass(...) fails,
	// and the resource loader provides no class bytes. The fallback must then honor the
	// ClassLoader.loadClass contract by reporting the failure instead of returning null.
	ClassLoader resourceLoader = new ClassLoader(new ClassLoader(null) {}) {
		@Override
		public InputStream getResourceAsStream(String name) {
			return null;
		}
	};
	ThrowawayClassLoader classLoader = new ThrowawayClassLoader(resourceLoader);

	String name = "com.example.MissingClass";
	assertThatExceptionOfType(ClassNotFoundException.class)
			.isThrownBy(() -> classLoader.loadClass(name))
			.withMessageContaining(name);
}
```

이 테스트의 어려운 부분은 결함 조건을 인위적으로 만드는 일이다.\
생성자가 `parent.getParent()`를 부모로 쓰므로, 이중 익명 클래스로 로더를 두 겹 쌓았다.\
바깥 로더가 `resourceLoader`가 되고, 그 부모인 `new ClassLoader(null) {}`이 `ThrowawayClassLoader`의 실제 부모가 된다.\
부모가 `null`인 로더는 부트스트랩 위임만 하므로 `com.example.MissingClass`는 2단계에서 반드시 실패한다.\
그리고 `getResourceAsStream`이 항상 `null`을 반환하도록 오버라이드해 3단계도 실패시킨다.

> **부트스트랩 로더** — JVM이 자체적으로 가진 최상위 클래스로더로, `java.*` 같은 코어 클래스만 푼다.\
> 예: 부모가 `null`인 `ClassLoader`는 부모 자리에 이 부트스트랩 로더가 놓인 것과 같다.

고정하는 것은 두 가지다.\
`assertThatExceptionOfType(ClassNotFoundException.class)`는 "`null` 반환이 아니라 예외"라는 계약을 고정한다.\
수정 전 코드에서는 예외가 나지 않고 `null`이 조용히 반환되므로 이 단언이 실패한다.\
뒤이은 `.withMessageContaining(name)`은 sbrannen이 폴리시 커밋에서 추가한 부분으로, 예외 메시지에 클래스명이 들어 있음 — 즉 재전파된 것이 정보 없는 빈 예외가 아니라 진단 가능한 원본임 — 을 고정한다.

같은 파일의 기존 테스트 `loadingClassFromResourceClosesInputStream`은 성공 경로를 지킨다.\
실제 `Probe` 클래스의 바이트를 공급해 3단계가 `defineClass`까지 도달함을 확인하므로, 이번 변경이 정상 로딩을 망가뜨리지 않았다는 회귀 방어선 역할을 한다.\
두 테스트가 폴백의 성공과 실패 양쪽을 각각 하나씩 붙잡는 구조다.

로컬 검증은 `./gradlew :spring-core:test`와 `checkstyleMain`/`checkstyleTest`로 수행했다.

## 6. 상태와 교훈

PR은 main에 반영됐다.\
GitHub 상태는 `CLOSED`이고 `mergedAt`은 비어 있는데, 이는 Spring 팀이 merge 버튼 대신 커밋을 직접 적용하고 `Closes gh-36938`로 닫기 때문이다.\
실제 반영 커밋은 `233e7b91f9b5aa9fc2be92fa1adc3ed1e4180cdb`(기여자 커밋)이며, 곧이어 sbrannen이 `7b31e0c2dcd9f6d0b142d58f111b6f960409555e`("Polish contribution")로 테스트에 `// gh-36938` 주석과 `withMessageContaining` 단언을 보탰다.\
과정에서 "Please rebase on `main` and force push"라는 요청이 한 번 있었고, 리베이스 후 약 한 시간 만에 반영됐다.

> **리베이스(rebase) · force push** — 내 커밋을 최신 `main` 위로 다시 얹어 히스토리를 직선으로 만들고, 그 결과를 원격 브랜치에 덮어쓰는 것.\
> 예: 리뷰어가 머지 커밋 없는 깔끔한 diff를 보려고 요청하는 정리 작업이다.

첫 번째 교훈은 인접 변경을 분리해 내는 판단이다.\
이 결함은 #36933(같은 메서드의 `InputStream` 누수 수정) 작업 중에 발견됐다.\
이미 7.1.0-M1 마일스톤으로 트리아지된 PR에 새 관심사를 얹는 대신, 별도 PR로 떼어내고 본문에 그 경위와 독립성을 명시했다.\
두 변경은 `loadClassFromResource`라는 같은 메서드를 건드리지만 서로 다른 줄이라 충돌하지 않았고, 실제로 리베이스 시 충돌은 테스트 파일에서만 났으며 양쪽 테스트를 모두 남기는 것으로 해결됐다.\
리뷰어가 한 번에 하나의 판단만 하게 만드는 것이 통과 확률을 높인다.

> **트리아지(triage)** — 들어온 이슈·PR을 분류해 어느 릴리스 마일스톤에 넣을지 정하는 메인테이너의 작업.\
> 예: #36933은 이미 7.1.0-M1 마일스톤이 붙어 있었으므로, 거기에 새 관심사를 얹으면 그 분류를 다시 흔들게 된다.

두 번째 교훈은 영향 범위를 정직하게 축소해 쓰는 편이 유리하다는 점이다.\
이 NPE는 상위 `catch (Throwable)`에 삼켜져 빌드를 깨지 않으므로 "크래시 수정"이 아니다.\
그 사실을 감추고 심각도를 부풀렸다면 리뷰어가 코드를 읽는 순간 신뢰를 잃었을 것이다.\
대신 "계약 정합성과 verbose 로그의 진단 품질"이라는 실제 이득을 명시하고, 트리거 조건이 좁다는 것까지 적었다.\
작은 계약 수정일수록 왜 지금 고칠 가치가 있는지를 설명하는 문장이 코드보다 중요하다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
