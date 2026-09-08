# PR #36972 — Write native configuration files as UTF-8

## 0. 정향

이 PR은 Spring AOT가 GraalVM 네이티브 이미지용 설정 파일을 디스크에 쓸 때 인코딩을 UTF-8로 못 박은 한 줄짜리 수정이다. 바뀐 것은 `FileNativeConfigurationWriter.writeTo`의 `new FileWriter(file)` 한 곳뿐이고, 나머지는 그 계약을 고정하는 테스트다. 변경 자체는 작지만 이해하려면 "네이티브 설정 파일이 무엇이고 누가 읽는가"와 "플랫폼 기본 인코딩이 왜 함정인가"를 먼저 알아야 한다. 이 문서는 그 맥락부터 따라간다.

## 1. 배경 — 네이티브 설정 파일과 플랫폼 기본 인코딩

GraalVM native-image는 애플리케이션을 정적 분석해 미리 컴파일하기 때문에, 리플렉션·동적 프록시·리소스 로딩처럼 정적으로 추적되지 않는 동작을 미리 알려줘야 한다. 그 통로가 `META-INF/native-image/` 아래에 놓이는 JSON 설정 파일이고, 최신 GraalVM에서는 `reachability-metadata.json` 하나로 통합되었다. Spring은 빌드 타임 AOT 처리 과정에서 `RuntimeHints`를 수집한 뒤 이 파일로 직렬화한다. 즉 파일의 생산자는 Spring 빌드 플러그인이고, 소비자는 GraalVM native-image 컴파일러다.

직렬화를 담당하는 클래스가 `spring-core`의 `org.springframework.aot.nativex.NativeConfigurationWriter` 계층이다. 추상 클래스가 "무엇을 쓸지"를 정하고, 파일 출력이라는 "어디에 쓸지"는 하위 클래스 `FileNativeConfigurationWriter`가 맡는다.

```java
public void write(RuntimeHints hints) {
	if (hasAnyHint(hints)) {
		writeTo("reachability-metadata.json",
				writer -> new RuntimeHintsWriter().write(writer, hints));
	}
}
```

여기서 문제의 씨앗은 Java의 오래된 기본값 하나다. `FileWriter`를 charset 없이 생성하면 JVM의 플랫폼 기본 charset으로 인코딩한다. JDK 18의 JEP 400이 `file.encoding` 기본값을 UTF-8로 바꾸기 전까지, 그리고 지금도 `-Dfile.encoding`으로 명시 지정된 환경에서는 이 기본값이 UTF-8이 아닐 수 있다. 한국어 Windows JVM의 MS949, 서유럽권의 windows-1252가 대표적이다. 반면 GraalVM은 이 JSON 파일을 UTF-8로 읽는다. 생산자의 인코딩이 환경에 따라 흔들리고 소비자의 인코딩은 고정이라면, 둘이 어긋나는 환경이 반드시 존재한다.

## 2. 수정 전 동작 방식

수정 전 `writeTo`는 파일을 만들고 `FileWriter`로 감싼 뒤 JSON 작성을 위임하는 단순한 구조였다.

```java
@Override
protected void writeTo(String fileName, Consumer<BasicJsonWriter> writer) {
	try {
		File file = createIfNecessary(fileName);
		try (FileWriter out = new FileWriter(file)) {
			writer.accept(createJsonWriter(out));
		}
	}
	catch (IOException ex) {
		throw new IllegalStateException("Failed to write native configuration for " + fileName, ex);
	}
}
```

파이프라인을 끝까지 따라가면 인코딩 결정권이 어디 있는지가 분명해진다. `createJsonWriter`는 `BasicJsonWriter`를 만들고, 그 안의 `IndentingWriter`는 들여쓰기만 얹은 뒤 `char[]`를 그대로 하위 `Writer`에 넘긴다. 즉 문자에서 바이트로 바뀌는 지점은 오직 `FileWriter` 한 곳이다.

결정적인 것은 `BasicJsonWriter.escape`가 비ASCII 문자를 이스케이프하지 않는다는 점이다.

```java
default -> {
	if (c <= 0x1F) {
		yield String.format("\\u%04x", c);
	}
	else {
		yield (char) c;
	}
}
```

제어 문자(0x1F 이하)만 `\uXXXX`로 바꾸고, `é`나 한글 같은 문자는 원문 그대로 통과시킨다. JSON 스펙상 유효한 선택이지만, 그 결과 최종 파일의 바이트 표현은 전적으로 `FileWriter`의 charset이 결정하게 된다. 만약 `escape`가 모든 비ASCII를 `\uXXXX`로 바꿨다면 출력이 순수 ASCII가 되어 charset이 무엇이든 결과가 같았을 것이다. 두 설계 선택이 맞물려야 버그가 성립한다.

## 3. 무엇이 문제였나

깨짐이 일어나려면 조건 두 개가 동시에 만족해야 한다. 첫째, JVM 기본 charset이 UTF-8이 아닐 것. 둘째, hint 내용에 비ASCII 문자가 들어 있을 것. 후자는 리소스 패턴 경로나 리소스 번들 이름에 비ASCII가 섞이는 경우다.

구체적으로 재현하면 이렇다. 기본 charset이 windows-1252인 JVM에서 `hints.resources().registerPattern("com/example/café/**")`를 등록하고 AOT 처리를 돌린다고 하자. `é`(U+00E9)는 `BasicJsonWriter`를 그대로 통과해 `FileWriter`에 도달하고, windows-1252로 인코딩되어 단일 바이트 `0xE9`로 디스크에 기록된다. UTF-8이라면 `0xC3 0xA9` 두 바이트여야 한다. 이후 GraalVM이 이 파일을 UTF-8로 읽으면 `0xE9`는 유효한 UTF-8 선두 바이트 뒤에 따라와야 할 연속 바이트가 없는 상태라 디코딩에 실패하거나 대체 문자로 바뀐다. 결과는 해당 리소스 패턴이 잘못 해석되어 리소스가 네이티브 이미지에 포함되지 않는 것이고, 실패는 빌드가 아니라 런타임의 리소스 누락으로 드러난다.

기본 charset이 MS949인 환경에서 한글 경로를 쓰면 바이트 수준의 결과만 다를 뿐 구조는 같다. 어느 경우든 증상이 원인에서 멀리 떨어져 나타나는, 추적이 까다로운 종류의 문제다.

다만 발동 조건이 좁다는 점은 PR 본문에서도 명시했다. JDK 18 이상에서는 기본값이 UTF-8이고, 비ASCII 경로를 쓰는 프로젝트도 흔하지 않다. 그래서 이 변경은 자주 터지는 버그의 수정이라기보다 계약을 명시화하는 hardening에 가깝다.

## 4. 수정 해설

수정은 charset을 명시하는 것 하나다.

```java
try (FileWriter out = new FileWriter(file, StandardCharsets.UTF_8)) {
	writer.accept(createJsonWriter(out));
}
```

이 선택의 근거는 세 가지다. 첫째, 소비자인 GraalVM이 UTF-8을 기대하므로 생산자가 UTF-8을 보장하는 것이 계약상 옳다. 둘째, 출력물의 인코딩이 실행 환경에 따라 달라지는 것 자체가 결함이다. 빌드 산출물은 어느 머신에서 만들든 동일해야 한다. 셋째, `aot.generate` 패키지가 이미 `StandardCharsets.UTF_8`을 명시적으로 쓰고 있어(`InMemoryGeneratedFiles`, `AppendableConsumerInputStreamSource`) 모듈 내 일관성에도 맞는다.

대안으로 `BasicJsonWriter.escape`가 비ASCII를 전부 `\uXXXX`로 이스케이프하게 만드는 방법도 있다. 그러면 출력이 ASCII만 남아 charset과 무관해진다. 하지만 이는 JSON 출력 형식 자체를 바꾸는 넓은 변경이고 기존 테스트의 기대 문자열에도 영향을 준다. 인코딩 문제는 인코딩을 결정하는 지점에서 고치는 것이 근본 원인에 가장 가깝다. 실제 머지된 것도 이 한 줄이다.

`FileWriter(File, Charset)`는 JDK 11에서 추가된 생성자라 Spring Framework 7.x의 baseline에서는 문제없이 쓸 수 있다.

## 5. 검증 — 테스트가 무엇을 고정하나

추가된 테스트는 비ASCII 문자가 UTF-8 바이트열로 기록되는지를 바이트 수준에서 확인한다.

```java
@Test  // gh-36972
void resourceConfigWithNonAsciiPatternIsWrittenAsUtf8() throws IOException {
	FileNativeConfigurationWriter generator = new FileNativeConfigurationWriter(tempDir);
	RuntimeHints hints = new RuntimeHints();
	hints.resources().registerPattern("com/example/café/**");
	generator.write(hints);
	Path jsonFile = tempDir.resolve("META-INF").resolve("native-image").resolve("reachability-metadata.json");
	byte[] content = Files.readAllBytes(jsonFile);
	assertThat(content).containsSequence("café".getBytes(StandardCharsets.UTF_8));
}
```

핵심은 `Files.readAllBytes`로 원시 바이트를 읽는다는 점이다. 같은 파일의 다른 테스트들이 쓰는 헬퍼는 `Files.readString(jsonFile)`으로 문자열을 읽고 `JSONAssert`로 비교하는데, `Files.readString(Path)`는 UTF-8로 디코딩한다. 즉 문자열 레벨 비교로는 "쓸 때 UTF-8이었는가"를 직접 확인할 수 없고, 인코딩 왕복이 우연히 상쇄되거나 디코딩 예외로 원인이 흐려질 수 있다. 바이트 비교는 그 모호함을 없앤다.

이 테스트의 한계도 정직하게 짚어둘 만하다. 기본 charset이 이미 UTF-8인 CI 환경에서는 수정 전 코드로도 통과한다. 회귀 테스트가 실패 재현으로 시작한다는 원칙에서 보면 약한 테스트다. 그럼에도 값어치가 있는 이유는 두 가지다. 비UTF-8 플랫폼에서는 실제로 회귀를 잡아주고, UTF-8 환경에서도 "이 파일은 UTF-8로 쓴다"는 의도를 코드로 문서화한다. 수정의 정당성 자체는 CI에서 비UTF-8 기본값을 재현하는 것이 아니라 `FileWriter(File, Charset)`의 계약에서 나온다.

## 6. 상태와 교훈

PR은 2026년 6월 27일 Sam Brannen이 "Good catch"와 함께 리뷰했고 `7.0.x`와 `main` 양쪽에 머지되었다. GitHub UI상 PR 상태는 `CLOSED`이고 `mergedAt`은 비어 있는데, 이는 Spring 팀이 PR 브랜치를 병합하는 대신 커밋을 각 브랜치에 cherry-pick하는 관행 때문이다. 실제 커밋은 `872b1addeb1`이며, 머지 과정에서 유지보수자가 테스트에 `// gh-36972` 주석을 덧붙였다.

교훈 하나. 인코딩·로케일·타임존처럼 "플랫폼 기본값"에 의존하는 API는 그 자체가 잠재적 결함이다. 개발 환경에서는 기본값이 우연히 맞아떨어져 조용히 지나가고, 다른 환경에서 원인과 동떨어진 증상으로 터진다. 파일을 읽거나 쓰는 코드에서는 charset을 항상 명시하는 편이 낫다.

교훈 둘. 좁은 조건에서만 발동하는 문제를 제안할 때는 조건의 좁음을 먼저 밝히는 편이 리뷰를 빠르게 한다. 이 PR은 본문에서 발동 조건과 테스트의 한계를 스스로 드러냈고, 그 덕에 유지보수자가 "이게 진짜 문제인가"를 재조사할 필요가 없었다. 결함의 크기를 부풀리지 않는 것이 오히려 신뢰를 만든다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
