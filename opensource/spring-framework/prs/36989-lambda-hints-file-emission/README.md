# PR #36989 — Write native configuration file when only lambda hints are present

## 0. 정향

이 PR은 `NativeConfigurationWriter.hasAnyHint()`에 한 줄을 추가해, lambda 힌트만 등록된 `RuntimeHints`에서도 `reachability-metadata.json`이 생성되도록 고친다. 고치기 전에는 직렬화기가 lambda 힌트를 출력할 준비를 이미 마쳤는데도, 파일을 만들지 말지 결정하는 앞단 조건이 lambda 힌트를 세지 않아 파일 자체가 만들어지지 않았다. 결과는 조용한 메타데이터 유실이었고, JVM 테스트로는 드러나지 않고 네이티브 이미지 런타임에서만 표면화된다. 업스트림에 커밋 `d1470bbb259`로 반영되었으며, `main`과 `7.0.x` 양쪽에 들어 있다.

## 1. 배경 — RuntimeHints와 네이티브 설정 직렬화

GraalVM `native-image`는 닫힌 세계 가정 위에서 동작한다. 빌드 시점에 도달 가능하다고 판단되지 않은 클래스와 멤버는 이미지에서 제거되므로, 리플렉션·프록시·리소스처럼 정적 분석이 볼 수 없는 접근은 별도 메타데이터로 알려야 한다. Spring은 이 메타데이터를 자바 객체 모델로 모으는 API를 `org.springframework.aot.hint` 패키지에 두었고, 그 최상위가 `RuntimeHints`다. 그 아래로 `reflection()`, `proxies()`, `resources()`, `jni()`, `serialization()` 같은 하위 힌트 묶음이 갈라진다.

`ReflectionHints`는 두 종류의 상태를 나란히 들고 있다. 하나는 타입별 리플렉션 힌트이고, 다른 하나는 lambda 힌트다. 실코드에서 이 둘은 서로 다른 필드로 분리되어 있다.

```java
public class ReflectionHints {

	private final Map<TypeReference, TypeHint.Builder> types = new HashMap<>();

	private final Set<LambdaHint> lambdaHints = new LinkedHashSet<>();

	/**
	 * Return the types that require reflection.
	 * @return the type hints
	 */
	public Stream<TypeHint> typeHints() {
		return this.types.values().stream().map(TypeHint.Builder::build);
	}


	/**
	 * Return the lambda hints.
	 * @return a stream of {@link LambdaHint}
	 * @since 7.0.6
	 */
	public Stream<LambdaHint> lambdaHints() {
		return this.lambdaHints.stream();
	}
```

lambda 힌트가 왜 따로 필요한지가 이 PR의 배경이다. 자바 lambda는 컴파일 시점에 이름 있는 클래스가 아니라 `invokedynamic` 호출 지점으로 남고, 실제 클래스는 런타임에 `LambdaMetafactory`가 만들어 낸다. 네이티브 이미지는 그 생성 과정을 빌드 시점으로 당겨와야 하므로, "어느 클래스의 어느 메서드 안에서 어떤 함수형 인터페이스를 구현하는 lambda가 만들어지는가"를 별도 형식으로 기술한다. `LambdaHint`가 담는 정보가 정확히 그 세 가지다 — `declaringClass`, `declaringMethod`, `interfaces`. 이 지원은 gh-36339(커밋 `3bc55c77ec8`)에서 7.0.6에 추가되었다.

등록 API는 `ReflectionHints.registerLambda(...)`이고, 빌더 소비자를 받아 `LambdaHint`를 만들어 집합에 넣는다.

```java
	public ReflectionHints registerLambda(TypeReference declaringClass, Consumer<LambdaHint.Builder> lambdaHint) {
		LambdaHint.Builder builder = LambdaHint.of(declaringClass);
		lambdaHint.accept(builder);
		this.lambdaHints.add(builder.build());
		return this;
	}
```

모아 둔 힌트를 JSON으로 바꾸는 쪽은 `org.springframework.aot.nativex` 패키지다. 파이프라인은 세 단계로 나뉜다. `RuntimeHintsWriter`가 문서 최상위 골격(`reflection`, `jni`, `resources` 키)을 만들고, `ReflectionHintsAttributes`가 각 힌트를 맵 속성으로 펼치며, `BasicJsonWriter`가 실제 문자열을 찍는다. `ReflectionHintsAttributes`는 처음부터 lambda 힌트를 알고 있었다. 타입 힌트 스트림 뒤에 lambda 힌트 스트림을 정렬해 이어 붙인다.

```java
		return Stream.concat(
				allTypeHints.entrySet().stream().sorted(Map.Entry.comparingByKey()).map(Map.Entry::getValue),
				hints.reflection().lambdaHints().sorted(LAMBDA_HINT_COMPARATOR).map(this::toAttributes)).toList();
```

각 lambda 힌트는 `type` 아래 `lambda` 객체로 감싸여 나간다.

```java
	private Map<String, Object> toAttributes(LambdaHint hint) {
		Map<String, Object> attributes = new LinkedHashMap<>();
		Map<String, Object> lambdaAttributes = new LinkedHashMap<>();
		lambdaAttributes.put("declaringClass", hint.getDeclaringClass());
		LambdaHint.DeclaringMethod declaringMethod = hint.getDeclaringMethod();
		if (declaringMethod != null) {
			Map<String, Object> methodAttributes = new LinkedHashMap<>();
			methodAttributes.put("name", declaringMethod.name());
			methodAttributes.put("parameterTypes", declaringMethod.parameterTypes());
			lambdaAttributes.put("declaringMethod", methodAttributes);
		}
		lambdaAttributes.put("interfaces", hint.getInterfaces());

		attributes.put("lambda", lambdaAttributes);
		return Map.of("type", attributes);
	}
```

마지막으로 이 JSON을 어디에 쓸지를 정하는 계층이 `NativeConfigurationWriter`(추상)와 그 구현 `FileNativeConfigurationWriter`(파일시스템)다. 파일 구현은 `META-INF/native-image/` 아래에, groupId·artifactId가 주어지면 그 하위 네임스페이스에 파일을 만든다. 실제 호출자는 `AbstractAotProcessor.writeHints(RuntimeHints)`이며, AOT 처리 결과물의 리소스 출력 디렉터리에 이 작성기를 붙인다.

## 2. 수정 전 동작 방식 — 파일 생성 여부를 결정하는 게이트

핵심은 `NativeConfigurationWriter.write(RuntimeHints)`가 무조건 파일을 쓰지 않는다는 점이다. 힌트가 하나도 없는 애플리케이션에까지 빈 JSON을 흩뿌리지 않으려고, 앞단에 게이트를 하나 두었다.

```java
	public void write(RuntimeHints hints) {
		if (hasAnyHint(hints)) {
			writeTo("reachability-metadata.json",
					writer -> new RuntimeHintsWriter().write(writer, hints));
		}
	}
```

게이트의 판정자는 `hasAnyHint()`이고, 수정 전에는 다음과 같이 하위 힌트 묶음을 하나씩 훑으며 `findAny().isPresent()`로 존재 여부만 확인했다.

```java
	private boolean hasAnyHint(RuntimeHints hints) {
		return (hints.proxies().jdkProxyHints().findAny().isPresent() ||
				hints.reflection().typeHints().findAny().isPresent() ||
				hints.resources().resourcePatternHints().findAny().isPresent() ||
				hints.resources().resourceBundleHints().findAny().isPresent() ||
				hints.jni().typeHints().findAny().isPresent() ||
				hasAnyDeprecatedHint(hints));
	}
```

여기서 구조적 사실 하나가 드러난다. 이 메서드는 "힌트가 있는가"를 힌트 모델에게 묻지 않고, 알고 있는 종류를 손으로 나열해 묻는다. 다시 말해 게이트는 힌트 종류의 열거를 통째로 복제한 코드이며, 새 힌트 종류가 생길 때마다 함께 갱신되어야만 정확성이 유지된다. `RuntimeHints`에는 "비어 있는가"를 스스로 답하는 메서드가 없으므로, 이 복제는 컴파일러가 지켜 주지 않는다.

## 3. 무엇이 문제였나 — lambda 힌트만 있을 때 파일이 조용히 빠진다

`ReflectionHints.lambdaHints()`가 위 목록에 없다. 그래서 lambda 힌트만 등록한 `RuntimeHints`는 게이트에서 "힌트 없음"으로 판정된다. 재현은 세 줄이면 충분하다.

```java
		FileNativeConfigurationWriter generator = new FileNativeConfigurationWriter(tempDir);
		RuntimeHints hints = new RuntimeHints();
		hints.reflection().registerLambda(Integer.class, builder -> builder
				.withDeclaringMethod("getCell", Integer.class, Integer.class)
				.withInterfaces(Supplier.class));
		generator.write(hints);
```

`write()`는 예외를 던지지 않고, 경고도 남기지 않고, 그냥 아무것도 하지 않는다. `hasAnyHint()`가 `false`이므로 `writeTo(...)`에 도달하지 않고, `reachability-metadata.json`은 생성되지 않는다. 실행은 정상 종료하고 빌드는 초록색이다.

문제의 성격은 "직렬화가 틀렸다"가 아니라 "직렬화가 아예 호출되지 않는다"에 가깝다. 아래 표는 lambda 힌트를 다루는 두 계층의 준비 상태가 어긋나 있었음을 값으로만 비교한 것이다.

| 계층 | lambda 힌트 인지 | 수정 전 결과 |
|------|------------------|--------------|
| `ReflectionHintsAttributes.reflectionHints()` | 인지함(`lambdaHints()` 스트림 연결) | lambda JSON 생성 가능 |
| `NativeConfigurationWriter.hasAnyHint()` | 인지하지 않음 | 파일 미생성 |

직렬화기 쪽이 이미 정상임은 `RuntimeHintsWriterTests`의 `oneLambda` 테스트가 증명한다. 그 테스트는 `RuntimeHintsWriter`를 직접 호출해 lambda JSON을 검증하므로 게이트를 통과하지 않는다. 게이트를 지나는 경로는 `FileNativeConfigurationWriter`를 쓰는 테스트뿐인데, 수정 전 그 테스트 클래스에는 lambda 케이스가 없었다. 두 테스트 사이의 틈이 정확히 이 버그가 숨어 있던 자리다.

파장은 여기서 끝나지 않는다. 실전에서 `RuntimeHints`가 lambda 힌트만 담는 경우는 라이브러리나 모듈 단위 AOT 처리에서 충분히 발생하며, 이때 산출물에 메타데이터 파일이 통째로 빠진다. JVM에서는 lambda가 평소대로 동작하니 아무 증상이 없고, 네이티브 이미지로 빌드한 뒤 해당 lambda 경로를 밟을 때에야 런타임 실패로 나타난다. 즉 결함의 발견 지점이 발생 지점에서 멀다.

원인은 기능 추가의 불완전한 확장이다. gh-36339은 `LambdaHint`, `ReflectionHints`, `ReflectionHintsAttributes`, `RuntimeHints` javadoc과 테스트를 건드렸지만 `NativeConfigurationWriter`는 건드리지 않았다. 등록 경로와 직렬화 경로는 확장되었는데 게이트만 옛 목록에 머문 것이다. sbrannen도 리뷰에서 "7.0.6에서 lambda 힌트 지원이 추가될 때 유입된 버그"라고 확인했다.

## 4. 수정 해설 — 게이트를 힌트 모델과 다시 맞춘다

수정은 `hasAnyHint()`에 lambda 힌트 검사를 한 줄 추가하는 것이다.

```java
	private boolean hasAnyHint(RuntimeHints hints) {
		return (hints.proxies().jdkProxyHints().findAny().isPresent() ||
				hints.reflection().typeHints().findAny().isPresent() ||
				hints.reflection().lambdaHints().findAny().isPresent() ||
				hints.resources().resourcePatternHints().findAny().isPresent() ||
				hints.resources().resourceBundleHints().findAny().isPresent() ||
				hints.jni().typeHints().findAny().isPresent() ||
				hasAnyDeprecatedHint(hints));
	}
```

위치를 `typeHints()` 바로 다음으로 잡은 데에는 이유가 있다. 두 검사는 같은 `hints.reflection()` 묶음에서 나오므로 나란히 두는 편이 목록을 읽을 때 종류별로 묶여 보인다. 단락 평가 순서상 성능 차이는 없고, `findAny()`는 요소 하나만 확인하고 끝난다.

게이트 자체를 없애고 항상 파일을 쓰는 선택지도 있지만 택하지 않았다. 힌트가 전혀 없을 때 파일을 만들지 않는 것은 기존 계약이고, `emptyConfig` 테스트가 그것을 명시적으로 고정하고 있기 때문이다.

```java
	@Test
	void emptyConfig() {
		Path empty = tempDir.resolve("empty");
		FileNativeConfigurationWriter generator = new FileNativeConfigurationWriter(empty);
		generator.write(new RuntimeHints());
		assertThat(empty.toFile().listFiles()).isNull();
	}
```

더 근본적인 대안은 `RuntimeHints`에 "비어 있는가"를 스스로 답하는 API를 추가해 게이트의 목록 복제를 없애는 것이다. 그러나 그것은 public API 확장이며 버그 수정의 범위를 넘는다. 기여 PR로서는 결함을 최소 diff로 닫고, 구조 개선은 메인테이너의 판단에 남기는 편이 채택 가능성이 높다. 실제로 이 PR은 프로덕션 코드 1줄과 테스트 29줄로 병합되었다.

## 5. 검증 — 테스트가 무엇을 고정하나

추가된 테스트는 `FileNativeConfigurationWriterTests.lambdaConfig()`다. lambda 힌트 하나만 등록하고 `write()`를 호출한 뒤, 생성된 파일 내용을 기대 JSON과 비교한다.

```java
	@Test  // gh-36989
	void lambdaConfig() throws Exception {
		FileNativeConfigurationWriter generator = new FileNativeConfigurationWriter(tempDir);
		RuntimeHints hints = new RuntimeHints();
		hints.reflection().registerLambda(Integer.class, builder -> builder
				.withDeclaringMethod("getCell", Integer.class, Integer.class)
				.withInterfaces(Supplier.class));
		generator.write(hints);
		assertEquals("""
				{
					"reflection": [
						{
							"type": {
								"lambda": {
									"declaringClass": "java.lang.Integer",
									"declaringMethod": {
										"name": "getCell",
										"parameterTypes": [ "java.lang.Integer", "java.lang.Integer" ]
									},
									"interfaces": [ "java.util.function.Supplier" ]
								}
							}
						}
					]
				}
				""");
	}
```

이 테스트가 결함을 실제로 재현한다는 근거는 헬퍼에 있다. `assertEquals(String)`는 기대 문자열을 비교하기 전에 파일을 먼저 읽는다.

```java
	private static void assertEquals(String expectedString) throws Exception {
		Path jsonFile = tempDir.resolve("META-INF").resolve("native-image").resolve("reachability-metadata.json");
		String content = Files.readString(jsonFile);
		JSONAssert.assertEquals(expectedString, content, JSONCompareMode.NON_EXTENSIBLE);
	}
```

수정이 없으면 파일이 존재하지 않으므로 `Files.readString`이 `NoSuchFileException`을 던지며 실패한다. 즉 이 테스트는 JSON 형식이 아니라 "파일이 생성되는가"를 1차로 고정하고, 형식은 2차로 고정한다. 버그의 본질이 미생성이었으므로 실패 모드와 재현이 정확히 일치한다.

현재 코드 기준으로 `./gradlew :spring-core:test --tests "*FileNativeConfigurationWriterTests*"`를 실행하면 9개 테스트가 모두 통과한다.

고정되는 계약은 세 겹이다. 첫째, lambda 힌트만 있어도 `reachability-metadata.json`이 나온다. 둘째, 그 내용은 `type.lambda` 구조로 `declaringClass`·`declaringMethod`·`interfaces`를 담는다. 셋째, `JSONCompareMode.NON_EXTENSIBLE` 덕분에 기대하지 않은 추가 필드가 끼어들면 실패한다. 반대 방향은 기존 `emptyConfig`가 계속 지킨다 — 힌트가 하나도 없으면 여전히 파일을 만들지 않는다. 두 테스트가 게이트의 양쪽 경계를 함께 붙잡는 셈이다.

## 6. 상태와 교훈

PR은 채택되었다. 업스트림에는 GitHub의 merge 버튼이 아니라 메인테이너가 직접 적용하는 방식으로 들어갔고, 그래서 PR 페이지 상태는 `CLOSED`로 보이지만 실제 커밋은 `d1470bbb259` "Register native configuration file when only lambda hints are present"로 남아 있다. 커밋 author는 기여자 본인이며 메시지에 `Closes gh-36989`가 붙어 있고, `upstream/main`과 `upstream/7.0.x` 양쪽에 포함되어 있다. 리뷰에서 sbrannen은 "Good catch"와 함께 7.0.6의 lambda 힌트 지원에서 유입된 버그라고 확인했다.

첫 번째 교훈은 결함을 찾는 위치에 관한 것이다. 이 버그는 데이터를 만드는 코드에도, 데이터를 형식화하는 코드에도 없었다. 둘 사이에서 "일을 할지 말지"를 정하는 조건절에 있었다. 새 종류를 다루는 기능을 추가할 때는 그 종류를 소비하는 코드뿐 아니라, 종류 목록을 손으로 열거하는 모든 지점을 함께 찾아야 한다. 이런 열거는 컴파일러가 누락을 잡아 주지 않으므로 `findAny().isPresent()` 같은 존재 검사 목록은 확장 지점의 상습 사각지대다.

두 번째 교훈은 테스트 층위의 틈에 관한 것이다. `RuntimeHintsWriterTests`는 직렬화기를 단위로 검증했고 `FileNativeConfigurationWriterTests`는 파일 생성을 통합적으로 검증했는데, lambda라는 신규 개념은 앞쪽에만 추가되었다. 하위 계층에 새 케이스를 넣을 때 상위 계층에도 같은 케이스가 필요한지 되묻는 습관이, 조용한 유실을 가장 싸게 잡는 방법이다. 특히 이번처럼 실패가 JVM에서는 보이지 않고 네이티브 런타임에서만 드러나는 경우, 자동화된 검증이 없으면 발견이 사용자에게 미뤄진다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
