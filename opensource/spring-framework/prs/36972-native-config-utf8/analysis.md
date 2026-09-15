# PR #36972 분석 — 네이티브 설정 파일의 인코딩이 플랫폼 기본값에 맡겨진 문제

> 기준 상태. **수정 전** = `872b1addeb1^`, **수정 커밋** = `872b1addeb1`, **메인테이너 폴리시** = `78dcdab3fc8`, **현재** = `upstream/main`(`7daf1013aa8`).\
> 파일:줄 인용마다 어느 상태 기준인지 밝힌다.\
> 이 문서의 자리: README(서사)·structure(5층 스택 구조도)·tests(테스트 해설)와 겹치지 않게, **"문자가 바이트가 되는 단 한 지점"에 이르는 호출 사슬의 이름표**와 **바이트 수준의 단계 추적**을 고정한다.

## 0. 결론

`FileNativeConfigurationWriter.writeTo`가 `new FileWriter(file)`를 써서 GraalVM 네이티브 이미지 설정 파일(`reachability-metadata.json`)을 **JVM 플랫폼 기본 charset**으로 기록했다.\
소비자인 GraalVM은 이 파일을 UTF-8로 읽는다.\
그래서 기본 charset이 UTF-8이 아닌 JVM(JDK 18의 JEP 400 이전 윈도우, 또는 `-Dfile.encoding`이 명시 지정된 환경)에서 비ASCII 문자가 든 리소스 패턴·번들 이름을 등록하면 디스크 바이트가 어긋난다.

> **플랫폼 기본 charset(platform default charset)** — 프로그램이 인코딩을 명시하지 않았을 때 JVM이 대신 골라 주는 문자-바이트 변환 규칙.\
> 예: 같은 코드가 리눅스에서는 UTF-8로, JEP 400 이전 한국어 Windows에서는 MS949로 파일을 쓰게 된다.

수정은 `new FileWriter(file, StandardCharsets.UTF_8)` 한 줄로 charset을 명시해 인코딩을 실행 환경에서 떼어 낸 것이다.

상태: 머지됨(7.0.x + main).\
커밋 `872b1addeb1`("Write native configuration files as UTF-8", `Closes gh-36972`) + 메인테이너 폴리시 `78dcdab3fc8`.\
성격은 자주 터지는 버그의 수정이 아니라, 발동 조건이 좁은 **hardening 겸 계약 명시화**다 — PR 본문도 그렇게 프레이밍했다.

> **hardening(경화)** — 지금 당장 터지지는 않지만 조건이 맞으면 터질 수 있는 여지를 미리 닫아 두는 수정.\
> 예: 여기서는 "환경이 UTF-8이면 우연히 맞는" 상태를 "환경과 무관하게 맞는" 상태로 바꾼 것이 그 여지 닫기다.

## 1. 무대

결함이 사는 자리는 AOT 산출물을 디스크에 쓰는 단 한 클래스다.\
모듈부터 소비자까지 여섯 항목으로 고정한다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 패키지 | `org.springframework.aot.nativex` |
| 결함 클래스 | `FileNativeConfigurationWriter` (**public**, `@since 6.0`) |
| 결함 메서드 | `writeTo(String, Consumer<BasicJsonWriter>)` (protected, `NativeConfigurationWriter`의 추상 메서드 구현) |
| 산출물 | `META-INF/native-image/[groupId/artifactId/]reachability-metadata.json` |
| 소비자 | GraalVM `native-image` 컴파일러 (스프링 런타임은 이 파일을 되읽지 않는다) |

이 클래스는 앞의 두 PR과 달리 **공개 API**다.\
공개 진입 API는 상위 추상 클래스의 `NativeConfigurationWriter.write(RuntimeHints)`(`:39`)이다.\
실제로 부르는 곳은 저장소 안에 하나 확인된다 — `AbstractAotProcessor.writeHints(RuntimeHints)`(`spring-context/src/main/java/org/springframework/context/aot/AbstractAotProcessor.java:124-128`)가 Gradle/Maven AOT 플러그인이 구동하는 빌드 타임 처리 끝에서 이 writer를 만들어 호출한다.\
즉 "누가 언제 부르나"의 답은 **빌드 타임 AOT 처리 1회**다.

> **AOT(ahead-of-time)** — 애플리케이션을 실행하기 전 빌드 시점에 빈 정의·메타데이터를 미리 확정해 두는 Spring의 처리 방식.\
> 예: 이 결함 경로는 런타임에 반복해 도는 코드가 아니라 빌드 한 번에 한 번만 지나간다.

## 2. 전체 메서드 그래프

현재(`upstream/main`) 줄번호이며, 수정 전 형태가 필요한 곳은 표시했다.\
화살표 옆 괄호는 그 구간을 흐르는 **데이터의 타입**이다 — 이 그래프의 요점이 타입 전환 지점이기 때문이다.

```text
 빌드 타임 (Gradle/Maven AOT 플러그인)
   |
   v
 AbstractAotProcessor.writeHints(hints)          AbstractAotProcessor.java:124
   |  new FileNativeConfigurationWriter(resourceOutput, groupId, artifactId)  :125-126
   |  writer.write(hints)                                                     :127
   v
 NativeConfigurationWriter.write(hints)          NativeConfigurationWriter.java:39
   |  if (hasAnyHint(hints)) { ... }        <-- 출력 여부 게이트 (#36989의 무대)  :40, :46
   |  writeTo("reachability-metadata.json",
   |          writer -> new RuntimeHintsWriter().write(writer, hints))         :41-42
   v                                                                (RuntimeHints 객체)
 FileNativeConfigurationWriter.writeTo(fileName, writer)   FileNativeConfigurationWriter.java:60
   |  File file = createIfNecessary(fileName)                                  :62
   |     |  basePath/META-INF/native-image[/groupId/artifactId]                :73-76
   |     |  outputDirectory.toFile().mkdirs(); file.createNewFile()            :77-79
   |  try (FileWriter out = new FileWriter(file, StandardCharsets.UTF_8)) {    :63   [!] 수정 지점
   |         수정 전:  new FileWriter(file)                       (872b1addeb1^ :62)
   |      writer.accept(createJsonWriter(out))                                 :64
   |         createJsonWriter(out) = new BasicJsonWriter(out)                  :83-85
   |  }
   |  catch (IOException ex) { throw new IllegalStateException(...); }         :67-69
   v                                                                (Writer 한 개)
 RuntimeHintsWriter.write(jsonWriter, hints)            RuntimeHintsWriter.java:37
   |  document = LinkedHashMap
   |    "comment"    <- SpringVersion.getVersion()                             :39-41
   |    "reflection" <- new ReflectionHintsAttributes().reflection(hints)      :43-46
   |    "jni"        <- new ReflectionHintsAttributes().jni(hints)             :47-50
   |    "resources"  <- new ResourceHintsAttributes().resources(hints.resources()) :51-54
   |       ResourceHintsAttributes.toAttributes(ResourcePatternHint)
   |         attributes.put("glob", hint.getPattern())   <-- 패턴 문자열이 그대로 값 ResourceHintsAttributes.java:74
   |  writer.writeObject(document)                                             :56
   v                                                                (Map -> String)
 BasicJsonWriter.writeObject / writeArray / writeAttribute / writeValue  BasicJsonWriter.java:66,77,121,127
   |  value instanceof CharSequence -> this.writer.print(quote(escape(string)))  :137-139
   |     escape(CharSequence)                                                    :153
   |        '"' '\' '/' '\b' '\f' '\n' '\r' '\t' -> 이스케이프                    :157-164
   |        default: c <= 0x1F ? String.format("\\u%04x", c) : (char) c          :165-172
   |                                              ^^^^^^^^^ [!] 비ASCII는 raw 통과
   v                                                                (String -> char[])
 BasicJsonWriter.IndentingWriter.write(char[], offset, length)                   :262
   |  들여쓰기(currentIndent)를 얹고                                              :264-267
   |  this.out.write(chars, offset, length)     <-- out = 위에서 꽂은 FileWriter   :268
   v                                                                (char[] -> byte[])
 java.io.FileWriter          [!] 문자에서 바이트로 바뀌는 유일한 지점
   |  수정 전: 플랫폼 기본 charset (환경 의존)
   |  수정 후: StandardCharsets.UTF_8 (환경 무관)
   v
 디스크: reachability-metadata.json  ->  GraalVM native-image가 UTF-8로 읽음
```

이 그래프에서 읽어야 할 사실은 두 가지다.\
첫째, `String`에서 `char[]`를 거쳐 `byte[]`가 되는 사슬에서 **인코딩 결정권을 가진 객체는 `FileWriter` 하나뿐**이다.\
`BasicJsonWriter`는 `String`만 다루고 `IndentingWriter`는 `char[]`를 그대로 위임한다.\
둘째, 그 하나뿐인 결정권자에게 아무도 charset을 알려 주지 않으면 결정은 **JVM 기본값**, 즉 실행 환경에 넘어간다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 지점은 "Writer가 세 겹(FileWriter / IndentingWriter / BasicJsonWriter)"이라는 것과, "charset이라는 단어가 나오지 않는 코드 대부분이 사실은 charset에 의존하고 있다"는 것이다.

세 겹이 어떻게 포개져 있고 누가 charset을 아는지를 먼저 그림으로 고정한다.

```text
 +--------------------------------------------------+
 | BasicJsonWriter            :34                   |
 |   다루는 것: String  (quote / escape 로 조립)     |
 |   charset 을 아는가:  모른다                      |
 |   +----------------------------------------------+
 |   | IndentingWriter        :179                  |
 |   |   다루는 것: char[]  (들여쓰기만 앞에 붙임)    |
 |   |   charset 을 아는가:  모른다                   |
 |   |   +------------------------------------------+
 |   |   | FileWriter                               |
 |   |   |   다루는 것: char[] -> byte[]             |
 |   |   |   charset 을 아는가:  여기서만 안다        |
 |   |   |     수정 전: 아무도 안 알려 줌 -> JVM 기본값|
 |   |   |     수정 후: StandardCharsets.UTF_8       |
 |   |   +------------------------------------------+
 |   +----------------------------------------------+
 +--------------------------------------------------+
            |
            v
      디스크 byte[]
```

아래 표는 각 이름이 어떤 타입 층에 서 있는지를 함께 적었다.

| 이름표 | 무엇인가 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `AbstractAotProcessor.writeHints(hints)` | 빌드 타임 AOT 처리의 마지막 단계 (`AbstractAotProcessor.java:124`) | `RuntimeHints` -> 없음(부작용: 파일) | Gradle/Maven AOT 플러그인 | 결함 경로의 실질적 진입점. 빌드 1회에 1번 |
| `NativeConfigurationWriter.write(hints)` | 공개 진입 API (`:39`) | `RuntimeHints` -> 없음 | `writeHints` | 파일명을 정하고 게이트를 거쳐 `writeTo` 호출 |
| `hasAnyHint(hints)` (`:46`) | 힌트가 하나라도 있는지 판정하는 출력 게이트 | `RuntimeHints` -> boolean | `write` | **이 PR과 무관**(그쪽은 #36989의 무대). 다만 이 게이트를 통과해야 결함 경로에 도달한다 |
| `writeTo(fileName, writer)` (`FileNativeConfigurationWriter.java:60`) | "어디에 어떻게 쓸지"의 구현 | 파일명 + JSON 작성 콜백 -> 없음 | `write` | **결함이 사는 메서드** |
| `fileName` (파라미터) | `"reachability-metadata.json"` 문자열 | -> 파일명 | 상동 | 값 자체는 무관. 실패 메시지(`:68`)에만 다시 등장 |
| `writer` (파라미터) | `Consumer<BasicJsonWriter>` — "이 JSON writer에 문서를 써 달라"는 콜백 | `BasicJsonWriter` -> 없음 | `:64`에서 `accept` | 콜백 안쪽(`RuntimeHintsWriter`)은 charset을 전혀 모른다. **책임이 바깥에 있다**는 구조 |
| `createIfNecessary(filename)` (`:72`) | 출력 디렉터리 생성 + 빈 파일 생성 | 파일명 -> `File` | `writeTo` 첫 줄 | `File`을 돌려주기 때문에 대안 3(NIO 경로)이 변환을 추가로 요구한다(5장) |
| `basePath` / `groupId` / `artifactId` (`:40`, `:42`, `:44`) | 출력 위치를 정하는 세 필드 | -> `Path` / `String?` | 생성자 | 결함과 무관. groupId·artifactId는 둘 다 null이거나 둘 다 non-null이어야 한다(`:52-54`) |
| `file` (지역, `:62`) | 방금 만든 빈 파일 | -> `File` | `writeTo` | `FileWriter`의 첫 인자 |
| `out` (지역, `:63`) | **`FileWriter`. 문자를 바이트로 바꾸는 유일한 객체** | `char[]` -> 디스크 `byte[]` | `writeTo`가 try-with-resources로 열고 닫음 | **결함의 주인공.** 수정 전 `new FileWriter(file)`는 charset 인자가 없어 JVM 기본값을 쓴다 |
| `StandardCharsets.UTF_8` (수정으로 추가된 인자) | `FileWriter(File, Charset)` 오버로드(Java 11+)의 두 번째 인자 | - | `:63` | **수정의 본체.** 인코딩을 환경에서 떼어 낸다 |
| `createJsonWriter(out)` (`:83-85`) | `new BasicJsonWriter(out)` | `Writer` -> `BasicJsonWriter` | `:64` | Writer를 감싸는 지점. 여기서부터 아래는 charset을 모른다 |
| `BasicJsonWriter.writeValue(value)` (`:127`) | 값 타입별 JSON 표현 분기 | `Object` -> (writer로 출력) | `writeAttribute`/`writeArray` | `CharSequence` 분기(`:137-139`)가 `escape`를 거친다 |
| `escape(CharSequence)` (`:153`) | JSON 문법상 위험한 문자만 이스케이프 | `CharSequence` -> `String` | `writeValue`의 `CharSequence` 분기 | **결함 성립의 다른 절반.** `c <= 0x1F`만 `\uXXXX`로 바꾸고 그 위는 `(char) c`로 통과(`:165-172`) — 출력이 순수 ASCII가 아니게 되므로 charset이 결과를 좌우한다 |
| `quote(String)` (`:148-150`) | 앞뒤에 큰따옴표를 붙임 | `String` -> `String` | `writeAttribute`/`writeValue` | 무관 |
| `IndentingWriter` (`:179`) | 들여쓰기만 얹는 `Writer` 데코레이터 | `char[]` -> 하위 `Writer` | `BasicJsonWriter`가 소유 | `write(char[],int,int)`(`:262-273`)가 그대로 위임 — **인코딩을 하지 않는다.** 이 층이 charset을 소비하지 않는다는 사실이 "결정권자는 하나"를 만든다 |
| `IndentingWriter.out` (`:181`) | 데코레이터가 감싼 하위 writer = `FileWriter` | - | - | 실제 인코딩 수행자 |
| `ResourceHintsAttributes.toAttributes(ResourcePatternHint)` (`ResourceHintsAttributes.java:71-76`) | 리소스 패턴을 `{"glob": 패턴}` 맵으로 | `ResourcePatternHint` -> `Map` | `resources(...)` | **비ASCII가 문서에 들어오는 대표 통로.** 사용자가 등록한 패턴 문자열이 가공 없이 값이 된다 |
| `hints.resources().registerPattern(...)` | 리소스 패턴 힌트 등록 (사용자·프레임워크 코드) | 패턴 문자열 -> 힌트 | AOT 처리 중 | 회귀 테스트가 `"com/example/café/**"`로 비ASCII를 주입하는 지점 |
| `catch (IOException ex)` (`:67-69`) | 쓰기 실패를 `IllegalStateException`으로 번역 | - | `writeTo` | 결함과 무관. 인코딩 불일치는 **예외를 발생시키지 않는다**(그래서 조용하다) |

## 3. 결함 경로 단계 추적

인코딩 결함은 예외를 남기지 않으므로 관찰 대상은 반환값이 아니라 **디스크에 박히는 바이트**다.\
아래 표는 `hints.resources().registerPattern("com/example/café/**")`가 등록된 상태에서, 기본 charset이 windows-1252인 JVM과 UTF-8인 JVM, 그리고 수정 후를 나란히 추적한 것이다.\
추적 대상 문자는 `é`(U+00E9) 하나다.

| 단계 | 값 / 상태 | 수정 전 (기본 charset = windows-1252) | 수정 전 (기본 charset = UTF-8) | 수정 후 (모든 환경) |
|---|---|---|---|---|
| 1. 힌트 등록 | 패턴 문자열 | `"com/example/café/**"` | 동일 | 동일 |
| 2. `toAttributes` | `{"glob": 패턴}` | `é` 그대로 | 동일 | 동일 |
| 3. `escape(...)` `:165-172` | `c` = 0x00E9 > 0x1F | `(char) c` -> `é` 통과 | 동일 | 동일 |
| 4. `quote` + `IndentingWriter` | `char[]` | `é` (U+00E9) | 동일 | 동일 |
| 5. `FileWriter` 인코딩 | char -> byte | **`0xE9` 1바이트** | `0xC3 0xA9` 2바이트 | **`0xC3 0xA9` 2바이트** |
| 6. 디스크 파일 | 바이트열 | `... 63 61 66 E9 2F ...` | `... 63 61 66 C3 A9 2F ...` | `... 63 61 66 C3 A9 2F ...` |
| 7. GraalVM이 UTF-8로 디코딩 | 문자 | `0xE9` 뒤에 연속 바이트가 없어 **디코딩 실패 또는 대체 문자** | `é` | `é` |
| 8. 결과 | 리소스 매칭 | 패턴이 어긋나 해당 리소스가 이미지에 **미포함** | 정상 | 정상 |
| 9. 실패가 드러나는 시점 | - | 빌드가 아니라 **네이티브 이미지 런타임**의 리소스 누락 | - | - |

같은 입력(`"com/example/café/**"`)에 대해 수정 전 비UTF-8 환경과 수정 후가 각각 어떤 최종 상태로 끝나는지를 같은 칸 폭으로 놓으면 이렇다.

```text
 [수정 전 · 기본 charset = windows-1252]   [수정 후 · 모든 환경]
 +-----------------------------------+   +-----------------------------------+
 | new FileWriter(file)              |   | new FileWriter(file, UTF_8)       |
 +-----------------------------------+   +-----------------------------------+
 | 디스크 바이트                      |   | 디스크 바이트                      |
 |   ... 63 61 66 E9 2F ...          |   |   ... 63 61 66 C3 A9 2F ...       |
 +-----------------------------------+   +-----------------------------------+
 | GraalVM 이 UTF-8 로 디코딩         |   | GraalVM 이 UTF-8 로 디코딩         |
 |   0xE9 뒤에 연속 바이트 없음       |   |   0xC3 0xA9 -> é                  |
 |   -> 디코딩 실패 또는 대체 문자    |   |   -> 패턴 그대로 복원              |
 +-----------------------------------+   +-----------------------------------+
 | 리소스 매칭                        |   | 리소스 매칭                        |
 |   패턴이 어긋나 이미지에 미포함    |   |   정상 포함                        |
 +-----------------------------------+   +-----------------------------------+
 | 드러나는 시점                      |   | 드러나는 시점                      |
 |   빌드는 초록색, 네이티브 런타임   |   |   문제 없음                        |
 |   에서 리소스 누락으로 뒤늦게      |   |                                   |
 +-----------------------------------+   +-----------------------------------+

 같은 소스 · 같은 힌트인데 남는 바이트가 다르다 — 그 차이를 만드는 것은 생성자 인자 하나뿐이다.
```

행 5가 유일한 분기점이고, 행 9가 이 결함이 진단하기 어려운 이유다.\
빌드는 성공하고, JSON은 문법적으로 유효하며, 예외도 로그도 없다.\
원인(쓰기 시점 charset)과 증상(런타임 리소스 누락)이 시공간적으로 멀다.

> **조용한 실패(silent failure)** — 잘못된 결과가 나왔는데도 예외·로그·빨간불 같은 신호가 전혀 없는 상태.\
> 예: 여기서는 빌드가 성공하고 JSON도 유효하므로, 어긋난 바이트를 알려 주는 것이 아무것도 없다.

발동 조건이 **두 개의 AND**라는 점도 표에서 읽힌다.\
(a) 기본 charset이 UTF-8이 아닐 것, (b) 힌트 내용에 비ASCII가 있을 것.\
어느 하나만 빠져도 증상이 없다.\
그래서 회귀 테스트가 정직한 red/green을 만들지 못한다 — 기본 charset이 UTF-8인 CI에서는 수정 전에도 통과한다(4장·5장).

## 4. 계약

이 결함이 걸쳐 있는 계약은 다섯 개이고, 그중 셋을 어기며 나머지 둘은 수정이 기대는 전제다.

> **계약(contract)** — 코드가 "이건 이렇게 동작한다"고 약속한 내용. 문서·스펙·호출 관계에 흩어져 있다.\
> 예: "`FileWriter(File, Charset)`는 주어진 charset으로 인코딩한다"는 JDK가 문서로 건 약속이고, 이 PR의 수정은 그 약속에 기댄다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| 산출 파일의 바이트는 내용의 **UTF-8 인코딩**이어야 한다 | 소비자 GraalVM이 설정 파일을 UTF-8로 읽는다는 전제 | **어긴다** — 조건부(비UTF-8 기본 charset + 비ASCII 내용) |
| 빌드 산출물은 어느 머신에서 만들든 동일해야 한다 | 재현 가능한 빌드의 일반 원칙 | **어긴다** — 같은 입력에 대해 환경마다 다른 바이트가 나온다 |
| `FileWriter(File, Charset)`는 주어진 charset으로 인코딩한다 | JDK 계약 (Java 11+) | 수정이 이 계약에 **의존**한다. 그래서 수정의 정확성 근거는 테스트가 아니라 JDK 계약이다 |
| `escape`는 JSON 문법상 필요한 문자만 이스케이프한다 | `BasicJsonWriter.java:153-176` | 결함이 아니라 **전제**. JSON 스펙상 유효한 선택이지만, 이 선택 때문에 인코딩 책임이 한 층 아래로 내려간다. `escape`가 모든 비ASCII를 `\uXXXX`로 바꿨다면 charset이 무엇이든 결과가 같았을 것이다 |
| 모듈 내 파일 입출력은 charset을 명시한다 | 같은 `aot` 트리의 선례 — `InMemoryGeneratedFiles.java:71`, `AppendableConsumerInputStreamSource.java:45` | **어긴다** — 일관성 결함이기도 하다 |

기존 테스트가 고정하던 것: `FileNativeConfigurationWriterTests`의 기존 테스트들은 `Files.readString`으로 파일을 읽어 `JSONAssert`로 비교한다.\
`Files.readString`은 **읽기 charset을 UTF-8로 가정**하므로 읽기와 쓰기가 짝을 이뤄 상쇄되고, 쓰기 시점 인코딩 결함을 구조적으로 잡을 수 없다.\
그래서 신규 테스트는 `Files.readAllBytes`로 raw 바이트를 읽는다.

## 5. 수정안

프로덕션 diff는 `FileWriter` 생성자에 charset 인자를 하나 더하는 실질 한 줄이다.

before (`872b1addeb1^` 기준 `FileNativeConfigurationWriter.java:62`):

```java
			try (FileWriter out = new FileWriter(file)) {
```

after (`upstream/main` 기준 `FileNativeConfigurationWriter.java:63`, import `java.nio.charset.StandardCharsets` 추가 동반):

```java
			try (FileWriter out = new FileWriter(file, StandardCharsets.UTF_8)) {
```

**왜 그 위치인가.** 2장 그래프가 답을 준다 — 문자가 바이트가 되는 지점이 이 코드베이스에 **정확히 한 곳**이고, 그곳이 `FileWriter` 생성 지점이다.\
상류(`BasicJsonWriter`·`IndentingWriter`·`RuntimeHintsWriter`)는 모두 문자 층에서 일하므로 어디를 고쳐도 바이트를 바꿀 수 없고, 하류(디스크)는 이미 바이트다.\
인코딩 결정은 결정이 실제로 일어나는 곳에서 해야 한다.

검토된 대안과 기각 사유는 다음과 같다.

| 대안 | 형태 | 기각 사유 |
|---|---|---|
| `Files.newBufferedWriter(path, UTF_8)` | NIO 기반 writer로 교체 | `createIfNecessary`(`:72-81`)가 `File`을 돌려주므로 `Path` 변환이 추가되고, 파일 생성 로직까지 손대게 되어 diff가 넓어진다 |
| `escape`가 비ASCII를 `\uXXXX`로 이스케이프하도록 변경 | 출력을 순수 ASCII로 만들어 charset 무관하게 | 결함을 **다른 층에서** 우회하는 셈이고, JSON 출력 형식이 바뀌어 기존 골든 테스트와 사람이 읽는 산출물에 광범위한 영향. 인코딩 문제를 인코딩 지점에서 고치는 편이 옳다 |
| 수정하지 않음 | JDK 18+ 기본값이 UTF-8이므로 | Spring 7의 베이스라인은 Java 17이고 `-Dfile.encoding` 명시 환경도 남는다. 무엇보다 산출물 인코딩이 환경 의존이라는 점 자체가 결함 |

**테스트 전략과 그 한계.** 추가된 테스트는 raw 바이트를 검사한다.

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
(`upstream/main` 기준 `FileNativeConfigurationWriterTests.java:208-217`)

`Files.readString` 대신 `readAllBytes`를 쓰는 이유가 핵심이다 — 읽기 charset을 가정하는 순간 쓰기 결함이 상쇄되어 보이지 않게 된다.\
다만 이 테스트는 **기본 charset이 이미 UTF-8인 CI에서는 수정 전에도 통과한다.**\
즉 결정론적 red/green 회귀 테스트가 아니라, 비UTF-8 플랫폼에서만 실효가 있는 조건부 가드이자 의도를 문서화하는 장치다.\
수정의 정확성 근거는 테스트가 아니라 `FileWriter(File, Charset)`의 JDK 계약이며, PR 본문도 이 한계를 명시했다.\
JVM을 포크해 비UTF-8 로케일로 돌리는 방식은 빌드 침습이 커 기각되었다.

> **결정론적(deterministic) 테스트** — 실행 환경이나 타이밍과 무관하게 항상 같은 경로를 타고 같은 결과를 내는 테스트.\
> 예: 이 테스트는 실행 JVM의 기본 charset에 따라 수정 전 결과가 갈리므로 결정론적이지 않다.

**메인테이너 폴리시(`78dcdab3fc8`)가 무엇을 바꿨는가.** 이 커밋은 이 PR이 추가한 테스트뿐 아니라 파일 전체를 정리했다.\
`throws IOException, JSONException`을 `throws Exception`으로 통일하고 `org.json.JSONException` import를 제거했다.\
신규 테스트에 `// gh-36972` 주석을 붙이고, `assertEquals` 헬퍼를 `private static`으로 바꿨다.\
프로덕션 코드에는 손대지 않았다.

## 6. 범위 밖과 인접 영향

**같은 형태가 저장소에 남아 있는지 확인했다.** `upstream/main`에서 `new FileWriter(` 를 훑으면 세 곳이 나오는데, 하나는 이 PR이 고친 곳이고 나머지 둘은 `buildSrc`의 테스트 코드(`MultiReleaseJarPluginTests.java:159`, `:165`)다.\
즉 **스프링 프로덕션 코드에서 charset 미지정 `FileWriter`는 이제 남아 있지 않다.**

읽기 쪽으로 범위를 넓히면 charset 미지정 `InputStreamReader`가 두 곳 보인다 — `EncodedResource.java:162`(charset도 encoding도 지정되지 않았을 때의 문서화된 기본 동작이므로 의도된 것)와 `XmlValidationModeDetector.java:96`이다.\
후자가 실제 결함인지는 이번 조사에서 판정하지 않았다(미확인) — 쓰기가 아니라 읽기 경로이고, 그 검출기가 찾는 토큰이 ASCII라는 점에서 성격이 다르다.\
cglib 재패키징 사본의 `DebuggingClassWriter.java:99`도 charset 미지정이지만 디버그 전용 경로다.

하위호환 영향은 사실상 없다.\
산출 파일의 소비자는 GraalVM 하나이고 UTF-8을 기대하므로, 바뀐 바이트는 "원래 기대되던 바이트"다.\
스프링 런타임은 이 파일을 되읽지 않으므로 read 경로 단절도 없다.\
유일하게 관측 가능한 변화는 비UTF-8 기본 charset 환경에서 산출 바이트가 달라지는 것인데, 그 환경의 이전 산출물이 곧 결함이었다.

인접 PR과의 관계: 같은 클래스 계층에서 **출력 여부를 결정하는 게이트**(`NativeConfigurationWriter.hasAnyHint`, `:46`)의 결함이 이후 #36989로 별도 처리되었다.\
이 PR이 "쓸 때 어떻게 쓰는가"라면 #36989는 "쓸 것인가 말 것인가"이며, 무대는 같은 파일 계층이지만 층과 줄이 다르다.
