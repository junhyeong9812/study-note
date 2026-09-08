# PR #36972 — 테스트 해설 (테스트 하나하나)

> PR #36972 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `FileNativeConfigurationWriterTests`의 한 건이고, 그 한 건은
red 테스트가 아니라 **플랫폼 조건부 가드**다. 기본 charset이 이미 UTF-8인 환경
(CI와 대부분의 리눅스 개발 머신)에서는 수정 전에도 통과하고, 기본 charset이 UTF-8이
아닌 환경에서만 수정 전에 실패한다. 이 성격을 흐리지 않고 그대로 드러내는 것이 이
문서의 목적이다.

## 1. resourceConfigWithNonAsciiPatternIsWrittenAsUtf8 — 조건부 가드

추가된 유일한 테스트는 비ASCII 리소스 패턴을 등록한 뒤 기록된 파일의 바이트열을 직접 검사한다.

```java
@Test
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

- **주장**: 비ASCII 문자를 담은 리소스 패턴을 힌트로 등록하고 설정 파일을 쓰면,
  **디스크에 실제로 기록된 바이트열**이 그 문자의 UTF-8 인코딩을 포함한다. 문자열
  수준이 아니라 바이트 수준의 주장이라는 점이 이 테스트의 전부다.

- **fix 전 결과와 이유 — 환경에 따라 갈린다**: 이 판별은 diff 논리만으로 결정되지
  않고 실행 환경의 기본 charset에 의존한다. 두 갈래를 나눠서 보면 이렇다.

  - 기본 charset이 UTF-8인 JVM(CI 포함): `new FileWriter(file)`이 우연히 UTF-8로
    인코딩하므로 수정 전에도 green이다. 이 환경에서 이 테스트는 red를 거치지 않는다.
  - 기본 charset이 UTF-8이 아닌 JVM(예: JDK 18 이전 Windows의 windows-1252):
    `é`가 단일 바이트 `0xE9`로 기록되는데 단언이 찾는 UTF-8 시퀀스는 `0xC3 0xA9`
    두 바이트이므로 `containsSequence`가 실패한다. 즉 red다.

  두 갈래 모두 `FileWriter(File)`이 플랫폼 기본 charset을 쓰고 `BasicJsonWriter`가
  비ASCII를 이스케이프 없이 통과시킨다는 사실에서 곧바로 도출되므로, "환경에 따라
  갈린다"는 결론 자체는 근거가 충분하다. 불확실한 것은 어느 갈래가 발동하느냐뿐이다.

- **fix 후**: `new FileWriter(file, StandardCharsets.UTF_8)`이 환경과 무관하게 UTF-8로
  인코딩하므로 두 갈래 모두 green이다. 즉 이 테스트가 고정하는 것은 "쓰기 인코딩이
  플랫폼 기본값에 의존하지 않는다"는 계약이다.

- **역할**: 수정 자체의 정당성은 이 테스트가 아니라 `FileWriter(File, Charset)`의
  계약에서 나온다. 이 테스트가 맡는 역할은 두 가지로, 비UTF-8 플랫폼에서 실제로
  회귀를 잡는 것과, UTF-8 환경에서도 "이 파일은 UTF-8로 쓴다"는 의도를 코드로
  문서화하는 것이다. 회귀 테스트가 실패 재현에서 시작한다는 원칙에서 보면 약한
  테스트이고, PR 본문도 그 한계를 스스로 밝혔다.

## 2. 바이트로 읽는 이유 — 헬퍼를 쓰지 않은 선택

같은 테스트 클래스의 다른 테스트들은 전부 `assertEquals(String)` 헬퍼를 통과한다.

```java
private static void assertEquals(String expectedString) throws Exception {
	Path jsonFile = tempDir.resolve("META-INF").resolve("native-image").resolve("reachability-metadata.json");
	String content = Files.readString(jsonFile);
	JSONAssert.assertEquals(expectedString, content, JSONCompareMode.NON_EXTENSIBLE);
}
```

이 테스트만 헬퍼를 쓰지 않고 `Files.readAllBytes`로 원시 바이트를 직접 읽는데, 이는
취향이 아니라 검증 대상 때문이다. `Files.readString(Path)`는 **UTF-8로 디코딩**한다.
따라서 헬퍼를 탔다면 쓸 때의 인코딩과 읽을 때의 디코딩이 서로를 상쇄하거나, 어긋난
경우 디코딩 단계의 예외나 대체 문자로 원인이 흐려진다. 어느 쪽이든 "쓸 때 UTF-8이었는가"라는
질문에는 답하지 못한다. 바이트 비교는 읽기 쪽 디코딩을 아예 개입시키지 않아 그
모호함을 제거한다.

`containsSequence`를 쓴 것도 같은 맥락이다. 파일 전체는 JSON 구조와 경로 문자열이
섞여 있으므로 전체 바이트 일치를 요구할 이유가 없고, 문제의 문자가 어떤 바이트열로
들어갔는지만 확인하면 충분하다.

## fixture

이 테스트에는 mock이 없고, 대체물은 임시 디렉터리 하나뿐이다.

```java
@TempDir
static Path tempDir;
```

`@TempDir`는 실제 파일시스템에 임시 디렉터리를 만들어 준다. 즉 파일 쓰기 자체는
가짜가 아니라 실물이며, 그래야 "디스크에 어떤 바이트가 남았는가"를 물을 수 있다.
`static`이므로 이 디렉터리는 테스트 메서드별이 아니라 클래스 전체에서 공유되지만,
이 테스트는 자기가 방금 쓴 파일을 읽고 `FileWriter`가 append 없이 파일을 덮어쓰므로
다른 테스트가 남긴 내용에 영향받지 않는다.

`"com/example/café/**"`라는 리소스 패턴이 흉내 내는 것은 비ASCII 문자를 포함한 실제
리소스 경로나 번들 이름이다. 실제 상황에서 그런 이름은 프로젝트의 디렉터리 구조나
i18n 번들 명명에서 자연스럽게 생기는데, 그것을 재현하려고 실제 리소스 파일을 만들 필요는
없다. `registerPattern`은 문자열을 힌트로 기록할 뿐 실재 여부를 확인하지 않으므로,
문자열 하나가 그 상황 전체를 대신한다. `é`를 고른 것도 의도적인데, ASCII 범위 밖이면서
Latin-1 계열 코드페이지에는 단일 바이트로 존재하는 문자라 UTF-8과의 바이트 차이가
가장 선명하기 때문이다.

## 실측·역할 요약

머지된 업스트림 코드에서 이 테스트에는 `// gh-36972` 주석이 붙었다. 로컬과 CI처럼
기본 charset이 UTF-8인 환경에서는 수정 전후 모두 green이므로, 이 PR에는 "수정 전
빨간불을 실측했다"는 형태의 증거가 존재하지 않는다. 이 점을 감추지 않고 PR 본문에
먼저 밝힌 것이 리뷰를 빠르게 만든 요인이었다.

역할을 한 줄로 정리하면, 이 한 건은 결함을 재현하는 테스트가 아니라 **의도를 고정하는
가드**다. 누군가 미래에 `FileWriter(file, StandardCharsets.UTF_8)`을 다시
`FileWriter(file)`로 되돌리면, UTF-8 기본 환경에서는 여전히 침묵하지만 비UTF-8
환경에서는 즉시 빨간불이 된다.
