# PR #36919 — 테스트 해설 (테스트 하나하나)

> PR #36919 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 한 건뿐이며 성격은 red다. 이 문서는 그 한 건을 해설하고, 이
PR이 새로 만들지 않은 대신 기존에 이미 존재하던 어떤 테스트가 가드 역할을 하고 있는지를
함께 정리한다. 테스트가 하나라는 사실 자체가 이 수정의 성격 — 진단 문자열 한 줄의
렌더링 규칙 통일 — 을 그대로 반영한다.

## 1. 파라미터 타입 이름 렌더링 — red

이 한 건은 ClassFile 리더로 읽은 메서드의 `toString()`에서 괄호 안 두 칸만 겨눈다.

```java
@Test
void toStringRendersParameterTypeNames() throws Exception {
	ClassFileMetadataReaderFactory factory = new ClassFileMetadataReaderFactory(new DefaultResourceLoader());
	MetadataReader reader = factory.getMetadataReader(WithMethod.class.getName());
	MethodMetadata method = reader.getAnnotationMetadata().getDeclaredMethods().stream()
			.filter(candidate -> candidate.getMethodName().equals("sample"))
			.findFirst()
			.orElseThrow();
	// primitive and array parameter types must keep their canonical names,
	// not be prefixed with "." (".int", ".String[]")
	assertThat(method.toString()).endsWith(".sample(int,java.lang.String[])");
}
```

- **주장**: ClassFile 기반 `MethodMetadata`의 `toString()`이 원시 타입 파라미터와 참조
  배열 파라미터를 정규 이름으로 렌더링한다. 구체적으로 `int`는 `int`로,
  `String[]`은 `java.lang.String[]`로 나와야 한다.
- **fix 전 결과와 이유**: red다. 판별은 diff 한 줄로 확정된다. 수정 전 파라미터 매핑은
  `desc -> desc.packageName() + "." + desc.displayName()`이었고, `ClassDesc.packageName()`은
  원시 타입과 배열 타입에 대해 빈 문자열을 반환한다. 그래서 `int`는 `.int`가 되고
  `String[]`은 `.String[]`이 된다. 후자는 점이 하나 붙는 데 그치지 않고 패키지가
  통째로 사라진다는 점에서 더 나쁘다. 결과 문자열은
  `...WithMethod.sample(.int,.String[])`이 되어 `endsWith` 단언이 어긋난다. 예외가 아니라
  문자열 불일치로 실패하는 형태의 red다.
- **fix 후**: 매핑이 `ClassFileAnnotationMetadata::resolveTypeName`으로 바뀐다. 이 헬퍼는
  원시 타입이면 `displayName()`만 쓰고, 배열이면 `componentType()`으로 원소 타입까지
  벗겨 낸 뒤 그 패키지를 붙이므로 두 칸 모두 정규 이름이 된다.
- **단언을 `endsWith`로 고른 이유**: 이 PR의 관심사는 괄호 안뿐이기 때문이다. 앞쪽의
  접근 제어자와 반환 타입, 선언 클래스 이름은 gh-36577이 이미 고쳤고 공유 테스트가
  검증한다. `isEqualTo`로 전체 문자열을 고정하면 관심 밖의 이유로 깨질 수 있으므로,
  검증 표면을 파라미터 슬롯으로 좁힌 선택이다.
- **주석의 역할**: 단언 바로 위 두 줄 주석이 기대값이 아니라 **깨진 값**(`.int`,
  `.String[]`)을 명시한다. 문자열 단언은 무엇이 틀렸었는지가 보이지 않으므로, 실패 형태를
  코드에 남겨 두는 편이 나중에 이 테스트를 읽는 사람에게 유용하다.

## 2. 픽스처

픽스처는 메서드 하나짜리 중첩 클래스이며, 파라미터 두 개가 각각 결함의 한 갈래를 대표한다.

```java
@SuppressWarnings("unused")
static class WithMethod {

	public void sample(int number, String[] values) {
	}
}
```

이 픽스처가 흉내 내는 것은 사용자 코드의 평범한 메서드 하나다. 목이나 스텁은 없고,
컴파일되면서 생기는 진짜 `.class` 파일이 곧 테스트 입력이다. `ClassFileMetadataReaderFactory`와
`DefaultResourceLoader`도 스텁이 아니라 프로덕션에서 컴포넌트 스캐닝이 쓰는 조합
그대로이며, 이 테스트는 "클래스를 로딩하지 않고 바이트코드만 읽어 메서드 메타데이터를
얻는" 경로를 시뮬레이션하는 것이 아니라 그대로 실행한다.

파라미터 두 개의 선정은 임의가 아니다. `int`는 `packageName()`이 비는 원시 타입 사례,
`String[]`은 `packageName()`이 비면서 동시에 패키지가 있어야 정답이 되는 배열 사례다.
즉 수정 전 코드에서 깨지던 두 종류를 각각 한 칸씩 배치했다. 반대로 `String` 같은 일반
참조 타입은 일부러 넣지 않았는데, 그 타입은 수정 전 표현식으로도 우연히 맞는 값이
나오므로 이 테스트에서는 판별력이 없기 때문이다.

`@SuppressWarnings("unused")`는 `sample`이 어디에서도 호출되지 않기 때문에 붙는다.
이 메서드는 실행 대상이 아니라 **디스크립터를 만들어 내기 위한 선언**이므로 본문이 비어
있는 것이 정상이다.

`WithMethod`가 테스트 클래스의 중첩 클래스라는 점은 단언 형태와 맞물린다. 선언 클래스
이름이 `...ClassFileMethodMetadataToStringTests$WithMethod`처럼 길어지므로,
`endsWith(".sample(...)")`로 그 앞부분을 검증 대상에서 빼는 편이 읽기 쉽다.

## 3. 배치 — 이 PR이 만들지 않은 가드

이 PR에는 별도의 가드 테스트가 없다. 대신 가드 역할은 이미 존재하던 공유 테스트
`AbstractMethodMetadataTests.verifyToString()`이 맡는다. 그 테스트는 참조 타입 파라미터
두 개짜리 메서드의 전체 문자열을 등호로 고정하고 있다.

```java
assertThat(getTagged(WithMethodWithTwoArguments.class).toString())
		.isEqualTo("public java.lang.String " + WithMethodWithTwoArguments.class.getName() + ".test(java.lang.String,java.lang.Integer)");
```

이 단언은 수정 전에도 통과했다. `java.lang.String`과 `java.lang.Integer`는
`packageName()`이 비지 않으므로 옛 표현식으로도 정답이 나왔기 때문이다. 그리고 수정
후에도 통과해야 한다. `resolveTypeName`이 같은 값을 내야 하기 때문이다. 즉 이것이
양성 가드다. 이 PR이 헬퍼로 교체하면서 패키지 있는 참조 타입의 렌더링을 바꿔 버렸다면
바로 여기서 잡힌다.

동시에 이 공유 테스트가 이번 결함을 놓친 이유도 같은 자리에서 드러난다. 이 파일은
"원시/배열"과 "반환/파라미터"라는 두 축을 갖고 있었지만 실제로는 대각선만 채웠다.
원시 배열은 반환 타입 축에만 있고(`WithPrimitiveArrayMethod`의 `test()`는 인자가 없다),
파라미터 축에는 참조 타입만 있었다. 곱집합의 빈 칸이 정확히 이 PR이 겨냥한 칸이다.

배치에 대해 남는 물음도 하나 기록해 둔다. 이 테스트는 `src/test/java24`에 ClassFile
전용으로 놓였는데, 선행 gh-36577의 최종 커밋은 반대 방향으로 움직여 ClassFile 전용
테스트 파일을 지우고 검증을 `AbstractMethodMetadataTests`로 옮겼다. 이 픽스처를
`verifyToString()`에 파라미터 케이스로 추가했다면 ASM과 ClassFile 두 구현의 정렬까지
한 벌의 단언으로 고정됐을 것이다.

## 4. 머지 후 polish — 이 테스트가 어디로 갔나

위 1~3절은 **제출 시점**의 테스트를 해설한 것이고, 머지 커밋 `ad83d5ebd9e`에도 그대로
들어갔다. 그런데 같은 날 Brian Clozel의 `6316c06a977`("Polishing contribution")이
`ClassFileMethodMetadataToStringTests.java` 55줄을 삭제하고, 같은 검증을 공유 추상
스위트 `AbstractMethodMetadataTests`에 15줄로 다시 넣었다. 현재 upstream에 남아 있는
형태는 이쪽이다.

```java
	@Test
	void toStringMethodShowsPrimitives() {
		assertThat(getTagged(WithMethodParameters.class).toString())
				.isEqualTo("public java.lang.String org.springframework.core.type.AbstractMethodMetadataTests$WithMethodParameters.test(java.lang.String[],int)");
	}
```

```java
	public static class WithMethodParameters {

		@Tag
		public String test(String[] names, int age) {
			return "";
		}

	}
```

세 가지가 바뀌었고, 각각 다른 것을 얻는다.

- **위치**: `src/test/java24`의 ClassFile 전용 파일에서 `src/test/java`의 공유 파일로 옮겼다. 이 추상 클래스를
  상속하는 구현은 `StandardMethodMetadataTests`(리플렉션)와
  `DefaultMethodMetadataTests`(JDK 24 미만 ASM / 24 이상 ClassFile) 둘이고,
  `java24Test` 태스크는 공유 테스트 소스셋을 멀티 릴리스 JAR와 함께 다시 돌린다
  (`MultiReleaseExtension.createTestTask`가 `sharedTestSourceSet.getOutput()`을
  `testClassesDirs`에 더하고 `jar` 산출물을 클래스패스 맨 앞에 놓는다). 결과적으로
  단언 한 줄이 세 구현을 잰다.
- **픽스처**: `public void sample(int number, String[] values)`가
  `@Tag public String test(String[] names, int age)`로 바뀌었다. `@Tag`가 붙은 이유는 이 스위트의
  `getTagged(...)` 헬퍼가 그 애노테이션으로 대상 메서드를 고르기 때문이고, 반환 타입이
  `void`에서 `String`으로 바뀐 것은 단언이 이제 반환 타입 슬롯까지 포함한 전체
  문자열이기 때문이다. 파라미터 두 칸의 성격은 그대로다 — `String[]`이 배열 사례,
  `int`가 원시 사례이고, 순서만 뒤집혔다.
- **단언**: `endsWith(".sample(int,java.lang.String[])")`가 전체 문자열 `isEqualTo`로
  강해졌다. §1에서 `endsWith`를 고른 근거는 "관심 밖의 이유로 깨지지
  않게 검증 표면을 좁힌다"였는데, 공유 스위트에서는 그 판단이 뒤집힌다. 여기서 기대
  문자열은 `StandardMethodMetadata.toString()`이 위임하는 JDK
  `java.lang.reflect.Method#toString()`의 출력 그 자체이므로, 전체를 등호로 고정하는
  것이 곧 "바이트코드 리더 둘이 JDK 리플렉션과 같은 값을 낸다"는 계약의 표현이 된다.
  좁힌 표면은 그 계약을 표현할 수 없다.

즉 §3 끝에 "배치에 대해 남는 물음"으로 적어 둔 것이 그대로 실현됐다. 우리가 지적까지
해 놓고 제출에 반영하지 않은 한 걸음을 메인테이너가 걸었다는 점이 이 폴리시에서 가장
값진 기록이다.

## 실측과 역할 요약

이 PR의 테스트 한 건에 대해 확인된 사실과 남은 조건을 모아 둔다.

- 실측 기록: PR 본문에 회귀 테스트를 `src/test/java24`에 추가했다는 서술은 있으나
  실행 결과 수치는 남아 있지 않다. 총 테스트 수나 실패 건수는 판별 근거 부족으로 남긴다.
- red 1건, 이 PR이 추가한 가드 0건. 보존 증명은 기존 공유 테스트
  `AbstractMethodMetadataTests.verifyToString()`이 맡는다.
- 실행 조건(제출 시점): `java24Test` 태스크에서만 컴파일·실행된다. `spring-core.gradle`의
  `multiRelease { releaseVersions 21, 24 }` 선언이 이 소스셋을 등록하므로, JDK 24 미만
  환경에서는 이 테스트가 아예 존재하지 않는다. **머지 후 폴리시로 이 조건이 사라졌다**
  — §4대로 검증이 공유 스위트로 옮겨져 이제 `test`와 `java24Test` 양쪽에서 돈다.
- 검증 표면: 이 PR이 바꾼 것은 사람이 읽는 진단 문자열뿐이며, 이 문자열을 읽어 분기하는
  메타데이터 로직은 없다. 그래서 테스트도 `toString()` 한 곳만 겨눈다.
