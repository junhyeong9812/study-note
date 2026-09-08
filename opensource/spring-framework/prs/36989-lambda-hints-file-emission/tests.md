# PR #36989 — 테스트 해설 (테스트 하나하나)

> PR #36989 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `FileNativeConfigurationWriterTests.lambdaConfig()` 한 건이고,
그 한 건은 수정 전에 실패하는 red 테스트다. 실패 모드가 단언 불일치가 아니라 **파일
부재**라는 점이 이 테스트의 특징이다. 결함의 본질이 "파일이 조용히 안 생긴다"였으므로
재현과 실패 모드가 정확히 일치한다. 가드 역할은 새로 추가되지 않았고, 게이트의 반대편
경계는 기존 `emptyConfig()`가 계속 지킨다.

## 1. lambdaConfig — red

추가된 유일한 테스트는 lambda 힌트 하나만 등록한 뒤 파일이 생성되고 그 내용이 기대 JSON과 일치하는지를 확인한다.

```java
@Test
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

- **주장**: lambda 힌트 **하나만** 들어 있는 `RuntimeHints`로도 `reachability-metadata.json`이
  생성되고, 그 내용이 기대 JSON과 정확히 일치한다. 다른 종류의 힌트를 하나도 등록하지
  않는 것이 이 테스트 설계의 핵심이다. 힌트를 하나라도 더 넣으면
  `hasAnyHint`가 그쪽 조건으로 true가 되어 결함이 가려진다.

- **fix 전 결과와 이유**: red다. `write(RuntimeHints)`는 `hasAnyHint(hints)`가 true일
  때만 `writeTo(...)`를 부르는데, 수정 전 `hasAnyHint`는 jdkProxy·reflection typeHints·
  resourcePattern·resourceBundle·jni·deprecated만 확인하고 `reflection().lambdaHints()`를
  빠뜨렸다. 이 테스트는 그중 어느 항목에도 해당하지 않는 힌트만 등록하므로
  `hasAnyHint`가 false를 반환하고, `writeTo`가 호출되지 않아 파일이 만들어지지 않는다.
  그 다음 단계에서 헬퍼가 파일을 읽으려다 실패한다.

- **fix 후**: `hints.reflection().lambdaHints().findAny().isPresent()` 한 줄이 조건에
  더해져 파일이 생성되고, `RuntimeHintsWriter`는 원래부터 lambda 힌트를 직렬화할 줄
  알았으므로 내용도 기대와 일치한다. 이 "직렬화기는 이미 할 줄 알았는데 게이트가 막고
  있었다"는 구조가 결함의 성격을 그대로 보여준다.

## 2. 실패가 파일 부재로 나타나는 이유 — assertEquals 헬퍼

이 테스트가 결함을 실제로 재현한다는 근거는 단언 문자열이 아니라 헬퍼에 있다.

```java
private static void assertEquals(String expectedString) throws Exception {
	Path jsonFile = tempDir.resolve("META-INF").resolve("native-image").resolve("reachability-metadata.json");
	String content = Files.readString(jsonFile);
	JSONAssert.assertEquals(expectedString, content, JSONCompareMode.NON_EXTENSIBLE);
}
```

헬퍼는 비교하기 **전에** 파일을 읽는다. 따라서 수정이 없으면 JSON 비교에 도달하기도
전에 `Files.readString`이 터진다. 이 테스트가 1차로 고정하는 것은 JSON 형식이 아니라
"파일이 생성되는가"이고, 형식은 2차다.

다만 정확한 실패 예외는 실행 맥락에 따라 갈리므로 단정하지 않는 편이 정확하다. 임시
디렉터리가 클래스 단위로 공유되기 때문이다.

```java
@TempDir
static Path tempDir;
```

`static`이므로 이 디렉터리는 테스트 메서드마다 새로 만들어지지 않고 클래스 전체에서
한 번 만들어진다. 그래서 `lambdaConfig`를 단독으로 돌리거나 클래스 안에서 파일을 쓰는
첫 테스트로 돌리면 파일이 아예 없어 `NoSuchFileException`이 나고, 앞선 다른 테스트가
이미 같은 경로에 파일을 남긴 뒤라면 그 낡은 내용이 읽혀 `JSONAssert` 불일치로 실패한다.
어느 쪽이든 red라는 결론은 같지만, 예외 종류까지 하나로 단정하려면 실행 순서를 근거로
확보해야 한다. PR 본문이 말하는 `NoSuchFileException`은 단독 실행 기준의 관측이다.

## 3. NON_EXTENSIBLE이 추가로 고정하는 것

헬퍼가 쓰는 `JSONCompareMode.NON_EXTENSIBLE`은 "기대에 없는 필드가 실제 JSON에 있으면
실패"를 뜻한다. 느슨한 모드였다면 lambda 힌트 외에 예상치 못한 항목이 함께 직렬화되어도
통과했을 것이다. 즉 이 테스트가 고정하는 계약은 세 겹이다. 첫째, lambda 힌트만 있어도
파일이 나온다. 둘째, 그 내용이 `type.lambda` 구조로 `declaringClass`·`declaringMethod`·
`interfaces`를 담는다. 셋째, 그 밖의 것은 들어가지 않는다.

## 4. 게이트의 반대편은 기존 테스트가 지킨다

이 PR은 가드 테스트를 새로 추가하지 않았다. `hasAnyHint`에 조건을 하나 더한 수정이므로
위험 방향은 "게이트가 너무 열려서 빈 힌트에도 파일을 만드는가"인데, 그것은 같은 파일에
이미 있던 테스트가 계속 막는다.

```java
@Test
void emptyConfig() {
	Path empty = tempDir.resolve("empty");
	FileNativeConfigurationWriter generator = new FileNativeConfigurationWriter(empty);
	generator.write(new RuntimeHints());
	assertThat(empty.toFile().listFiles()).isNull();
}
```

- **역할**: 힌트가 하나도 없으면 파일도 디렉터리도 만들지 않는다는 음성 경계.
  `lambdaHints()` 조건이 추가돼도 빈 `RuntimeHints`에서는 여전히 false이므로 수정
  전후 모두 green이며, 두 테스트가 게이트의 양쪽 경계를 함께 붙잡는 배치가 된다.
- 이 테스트가 별도 하위 디렉터리 `empty`를 쓰는 것도 앞서 말한 static `@TempDir`
  공유 때문이다. 공유 디렉터리를 그대로 봤다면 다른 테스트가 남긴 파일에 걸려
  `listFiles()`가 null이 아니게 된다.

## fixture

이 테스트의 fixture는 lambda 힌트 하나이고, 그것은 실물이 아니라 **기술자(descriptor)**다.

```java
hints.reflection().registerLambda(Integer.class, builder -> builder
		.withDeclaringMethod("getCell", Integer.class, Integer.class)
		.withInterfaces(Supplier.class));
```

`Integer`에는 `getCell`이라는 메서드가 없다. 그런데도 등록이 성공하는 이유는
`LambdaHint.Builder.withDeclaringMethod`가 이름과 파라미터 타입을 `TypeReference`로
바꿔 담기만 하고 실제 메서드를 리플렉션으로 찾지 않기 때문이다.

```java
public Builder withDeclaringMethod(String name, List<TypeReference> parameterTypes) {
	this.declaringMethod = new DeclaringMethod(name, parameterTypes);
	return this;
}
```

이 fixture가 흉내 내는 실제 상황은 "애플리케이션 어딘가의 메서드 본문 안에서 만들어진
람다가 어떤 함수형 인터페이스를 구현하고 있고, GraalVM이 네이티브 이미지에서 그 람다를
복원하려면 선언 클래스·선언 메서드·구현 인터페이스 세 정보가 필요하다"는 장면이다.
그 세 정보를 얻으려고 진짜 람다를 만들고 그 합성 클래스를 뒤질 필요는 없고, 세 값을
직접 적어 넣으면 충분하다. 검증 대상이 람다 탐지가 아니라 힌트가 파일까지 흘러가는
경로이기 때문이다.

이 값들은 임의로 지어낸 것도 아니다. 같은 패키지의 `RuntimeHintsWriterTests.oneLambda()`가
쓰던 fixture와 등록 코드·기대 JSON이 동일하다. 하위 계층(직렬화기 단위 테스트)에서
이미 검증된 케이스를 상위 계층(파일 생성 통합 테스트)에 그대로 옮겨 온 것인데, 이
PR이 드러낸 결함이 정확히 "그 케이스가 하위 계층에만 있었다"는 층위의 틈이었으므로
같은 fixture를 재사용하는 것이 진단과 대칭을 이룬다.

## 실측·역할 요약

머지된 업스트림 코드에서 이 테스트에는 `// gh-36989` 주석이 붙었다. 현재 코드 기준으로
`FileNativeConfigurationWriterTests` 전체가 통과한다.

역할을 한 줄로 정리하면, `lambdaConfig`는 "게이트가 새 힌트 종류를 알고 있는가"를
파일 존재로 묻는 red 테스트이고, `emptyConfig`는 "게이트가 아무 힌트도 없을 때는 닫혀
있는가"를 묻는 기존 음성 경계다. 결함이 데이터를 만드는 코드에도 형식화하는 코드에도
없고 둘 사이의 조건절에 있었으므로, 테스트도 그 조건절의 양쪽을 겨눈다.
