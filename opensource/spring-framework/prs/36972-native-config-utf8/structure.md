# PR #36972 — 무대 구조와 워크플로우

> PR #36972의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.\
> 기준: upstream main `526c706d1c3`.\
> 이 PR은 이미 머지되었으므로 `FileNativeConfigurationWriter.java:63`의 현재 코드는 "수정 후"다.\
> 수정 전 형태가 필요한 곳은 그때마다 명시한다.\
> 나머지 인용은 이 PR로 바뀌지 않았으므로 수정 전후가 동일하다.

이 문서가 다루는 것은 Spring AOT가 수집한 `RuntimeHints`를 GraalVM용 JSON 파일로 내려놓는 다섯 층짜리 직렬화 스택의 실구조다.\
층별 소유 관계에서 출발해, 힌트 하나가 디스크 바이트가 되기까지의 경로를 따라간다.\
그다음 세 층에 흩어진 분기로 결함이 성립하는 조건을 짚고, 이 스택이 AOT 파이프라인 전체에서 차지하는 자리와 배경 개념을 정리한다.

> **AOT(ahead-of-time)** — 애플리케이션을 실행하기 전 빌드 시점에 빈 정의·프록시·메타데이터를 미리 확정해 두는 Spring의 처리 방식.\
> 예: Gradle/Maven AOT 플러그인이 빌드 중에 `RuntimeHints`를 모아 이 문서의 스택으로 내려보낸다.

> **직렬화(serialization)** — 메모리 안의 객체를 파일·네트워크로 내보낼 수 있는 형태(여기서는 JSON 문자열, 최종적으로 바이트열)로 바꾸는 일.\
> 예: `RuntimeHints` 객체가 `reachability-metadata.json`의 바이트가 되는 이 다섯 층이 곧 직렬화 스택이다.

## 1. 무대 — 실구조

이 PR의 무대는 `spring-core`의 `org.springframework.aot.nativex` 패키지에 놓인 다섯 층짜리 직렬화 스택이다.\
위에서부터 "무엇을 쓸지 정하는 층", "문서 골격을 만드는 층", "힌트를 맵 속성으로 펼치는 층", "맵을 JSON 문자열로 찍는 층", 그리고 "문자를 바이트로 바꿔 디스크에 내려놓는 층"이다.\
PR이 건드리는 곳은 맨 아래 층, 정확히는 문자에서 바이트로 넘어가는 단 한 줄이다.

층별 클래스와 그 사이의 소유 관계는 다음과 같다.\
화살표는 호출 방향이다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ [1] 무엇을·어디에 쓸지 결정                                              │
│                                                                          │
│ abstract NativeConfigurationWriter      NativeConfigurationWriter.java:33│
│   + write(RuntimeHints)                                            :39   │
│   - hasAnyHint(RuntimeHints) : boolean       ★ 출력 여부 게이트     :46   │
│   - hasAnyDeprecatedHint(RuntimeHints) : boolean                   :57   │
│   # abstract writeTo(String fileName, Consumer<BasicJsonWriter>)   :67   │
│                             △                                            │
│                             │ extends                                    │
│ FileNativeConfigurationWriter      FileNativeConfigurationWriter.java:38 │
│   - basePath : Path                                                :40   │
│   - groupId : @Nullable String                                     :42   │
│   - artifactId : @Nullable String                                  :44   │
│   + FileNativeConfigurationWriter(Path)                            :46   │
│   + FileNativeConfigurationWriter(Path, String, String)            :50   │
│   # writeTo(String, Consumer<BasicJsonWriter>)   ★ 이 PR의 지점    :60   │
│   - createIfNecessary(String) : File                               :72   │
│   - createJsonWriter(Writer) : BasicJsonWriter                     :83   │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ writer.accept(createJsonWriter(out))  :64
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ [2] 문서 골격                                                            │
│ class RuntimeHintsWriter                     RuntimeHintsWriter.java:35  │
│   + write(BasicJsonWriter, RuntimeHints)                           :37   │
│       document = LinkedHashMap                                     :38   │
│         "comment"    ← SpringVersion.getVersion()                  :39~41│
│         "reflection" ← ReflectionHintsAttributes().reflection()     :43   │
│         "jni"        ← ReflectionHintsAttributes().jni()            :47   │
│         "resources"  ← ResourceHintsAttributes().resources()        :51   │
│       writer.writeObject(document)                                  :56   │
└───────────────┬──────────────────────────────┬───────────────────────────┘
                │                              │
                ▼                              ▼
┌──────────────────────────────┐  ┌──────────────────────────────────────┐
│ [3a] ReflectionHintsAttributes│  │ [3b] ResourceHintsAttributes         │
│   ReflectionHintsAttributes   │  │   ResourceHintsAttributes.java:43    │
│   .java:56                    │  │   + resources(ResourceHints)    :52  │
│   + reflection(RuntimeHints):73│ │   - toAttributes(ResourceBundleHint) │
│   + jni(RuntimeHints)      :98│  │        → {"bundle": …}          :64  │
│   - toAttributes(TypeHint):106│  │   - toAttributes(ResourcePatternHint)│
│   - toAttributes(LambdaHint)  │  │        → {"glob": pattern}      :71  │
│                          :118 │  │   - handleCondition(...)        :78  │
│   - toAttributes(JdkProxyHint)│  │                                      │
│                          :197 │  │  ★ 패턴 문자열이 그대로 값이 된다   │
└───────────────┬───────────────┘  └───────────────┬──────────────────────┘
                │  Map<String,Object> / List<...>  │
                └───────────────┬──────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ [4] 맵 → JSON 문자열                                                     │
│ class BasicJsonWriter                            BasicJsonWriter.java:34 │
│   - writer : IndentingWriter                                       :36   │
│   + BasicJsonWriter(Writer, String singleIndent)                   :43   │
│   + BasicJsonWriter(Writer)      (들여쓰기 = 공백 2칸)              :51   │
│   + writeObject(Map<String,Object>)                                :66   │
│   + writeArray(List<?>)                                            :77   │
│   - writeAll(Iterator<T>, Consumer<T>) : Runnable                 :107   │
│   - writeAttribute(String, Object)                                :121   │
│   - writeValue(Object)                     ★ 값 타입 분기          :127   │
│   - quote(String)                                                 :148   │
│   - escape(CharSequence) : String   ★ 비ASCII를 통과시키는 곳      :153   │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ print / println (char[] 단위)
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ [5] 들여쓰기 + 문자→바이트                                               │
│ static class BasicJsonWriter.IndentingWriter extends Writer       :179   │
│   - out : Writer          ← 여기 꽂히는 것이 FileWriter                  │
│   - singleIndent : String / level : int / currentIndent : String  :183~187│
│   - prependIndent : boolean                                       :189   │
│   + print(String) / println(String) / println()             :200,209,217 │
│   + indented(Runnable)                                            :234   │
│   @Override write(char[], int, int)   ← 들여쓰기만 얹고 out 에 위임:262   │
│                                △                                         │
│                                │ out                                     │
│                    java.io.FileWriter   ★ 문자→바이트 변환 지점          │
│                    수정 전: new FileWriter(file)          (플랫폼 기본)   │
│                    수정 후: new FileWriter(file, StandardCharsets.UTF_8)  │
│                                        FileNativeConfigurationWriter:63  │
└──────────────────────────────────────────────────────────────────────────┘
```

이 구조에서 읽어야 할 사실 하나는 "문자가 바이트가 되는 지점이 정확히 한 곳"이라는 점이다.\
`BasicJsonWriter`는 `String`을 다루고, `IndentingWriter`는 `char[]`를 받아 들여쓰기만 얹은 뒤 그대로 하위 `Writer`에 넘긴다(`BasicJsonWriter.java:262~273`).\
인코딩을 결정하는 것은 그 하위 `Writer`, 즉 `FileWriter` 하나뿐이다.

> **인코딩(encoding)과 charset** — 사람이 읽는 문자를 저장·전송용 바이트열로 바꾸는 규칙, 그리고 그 규칙의 이름표.\
> 예: 같은 문자 `é`가 UTF-8에서는 `0xC3 0xA9` 두 바이트, windows-1252에서는 `0xE9` 한 바이트가 된다.

## 2. 수정 전 동작 워크플로우

대표 시나리오는 리소스 패턴 힌트 하나가 등록된 `RuntimeHints`를 디스크에 쓰는 흐름이다.\
아래는 `hints.resources().registerPattern("com/example/café/**")` 한 줄이 최종 바이트가 되기까지의 경로다.\
`FileWriter` 생성 부분만 수정 전 형태(`new FileWriter(file)`)로 표기했다.

> **리소스 패턴 힌트(resource pattern hint)** — "이 경로에 맞는 파일들은 네이티브 이미지 안에 꼭 넣어 달라"고 GraalVM에 알려 주는 힌트.\
> 예: `registerPattern("com/example/café/**")`은 그 디렉터리 아래 리소스를 전부 포함 대상으로 등록한다.

```text
FileNativeConfigurationWriter(tempDir)              FileNativeConfigurationWriter.java:46
  └ basePath = tempDir, groupId = null, artifactId = null

write(hints)                                        NativeConfigurationWriter.java:39
  │
  ├ hasAnyHint(hints)                                                    :46
  │    hints.resources().resourcePatternHints().findAny().isPresent() → true :50
  │
  └ writeTo("reachability-metadata.json", writer -> …)                   :41~42
       │
       ▼ (파일 구현으로 내려감)
     FileNativeConfigurationWriter.writeTo(fileName, writer)             :60
       │
       ├ file = createIfNecessary(fileName)                              :62
       │    outputDirectory = basePath/META-INF/native-image             :73
       │    (groupId·artifactId 가 있으면 그 아래로 한 단계 더)          :74~76
       │    outputDirectory.toFile().mkdirs()                            :77
       │    file.createNewFile()                                         :79
       │
       ├ out = new FileWriter(file)        ★ 수정 전: charset 미지정      :63
       │       └ JVM 플랫폼 기본 charset 이 인코딩을 결정
       │
       └ writer.accept(createJsonWriter(out))                            :64
            │  createJsonWriter → new BasicJsonWriter(out)               :83~85
            │  (BasicJsonWriter(Writer) → IndentingWriter(out, "  "))    :51~53, :44
            ▼
          RuntimeHintsWriter.write(basicJsonWriter, hints)  RuntimeHintsWriter.java:37
            │  document.put("comment", "Spring Framework " + version)    :39~41
            │  document.put("resources",
            │      new ResourceHintsAttributes().resources(hints.resources()))  :51~53
            │        └ ResourceHintsAttributes.resources(...)  ResourceHintsAttributes.java:52
            │             resourcePatternHints() → getIncludes() → distinct → sorted :54~57
            │             toAttributes(hint) → {"glob": "com/example/café/**"}  :71~75
            │
            └ writer.writeObject(document)                               :56
                 │
                 ▼
               BasicJsonWriter.writeObject(attributes, true)  BasicJsonWriter.java:66,81
                 │  println("{") → indented(writeAll(...)) → print("}")  :86~87
                 │
                 └ writeAttribute("resources", List)                     :121
                      │ print(quote("resources") + ": ")                 :122
                      └ writeValue(list) → writeArray(list, false)       :127,131
                           └ writeValue(map) → writeObject(map, false)   :128~129
                                └ writeAttribute("glob", "com/example/café/**")
                                     └ writeValue(String) → print(quote(escape(s)))  :137~138
                                          escape: 'é' 는 0x1F 초과 → 그대로 통과 :165~172
                 │
                 ▼ IndentingWriter.write(char[], off, len)               :262
                      prependIndent 면 현재 들여쓰기 먼저 out 에 write    :264~267
                      out.write(chars, offset, length)                   :268
                 │
                 ▼
              FileWriter 가 char → byte 변환 (charset 은 위에서 정해짐)
                 │
                 ▼
              디스크: <tempDir>/META-INF/native-image/reachability-metadata.json
```

두 번째 시나리오로 groupId·artifactId가 주어진 경우를 보면 출력 경로만 달라진다.\
`createIfNecessary`가 네임스페이스 디렉터리를 한 단계 더 내려가고(`:74~76`), 나머지 파이프라인은 동일하다.

```text
new FileNativeConfigurationWriter(basePath, "foo.bar", "baz")           :50
   │  groupId 와 artifactId 는 둘 다 null 이거나 둘 다 non-null 이어야 함 :52~54
   ▼
createIfNecessary("reachability-metadata.json")                          :72
   basePath/META-INF/native-image                                        :73
        + /foo.bar/baz                                                   :75
        + /reachability-metadata.json                                    :78
```

## 3. 분기 처리 워크플로우

무대의 조건 분기는 세 층에 흩어져 있다.\
파일을 쓸지 말지를 정하는 게이트, 값 타입에 따라 JSON 표현을 고르는 분기, 그리고 문자마다 이스케이프 여부를 정하는 분기다.\
마지막 것이 이 PR의 결함과 직접 맞물린다.

> **이스케이프(escape)** — 그대로 두면 문법을 깨뜨리는 문자를 특별한 표기로 바꿔 적는 것.\
> 예: JSON 문자열 안의 큰따옴표는 `\"`로, 줄바꿈은 `\n`으로 바꿔 적어야 문자열이 거기서 끊기지 않는다.

첫째는 파일을 쓸지 말지를 정하는 출력 여부 게이트다.

```text
NativeConfigurationWriter.write(hints)                                   :39
  │
  ├ hasAnyHint(hints) == false ──────────► 아무 파일도 만들지 않음        :40
  │     (힌트가 전혀 없는 애플리케이션에 빈 JSON 을 흩뿌리지 않기 위함)
  │
  └ hasAnyHint(hints) == true ───────────► writeTo("reachability-metadata.json", …) :41
        hasAnyHint 내부 = 하위 힌트 묶음을 손으로 나열한 OR 사슬          :46~54
          proxies().jdkProxyHints()              .findAny().isPresent()  :47
          reflection().typeHints()               .findAny().isPresent()  :48
          reflection().lambdaHints()             .findAny().isPresent()  :49
          resources().resourcePatternHints()     .findAny().isPresent()  :50
          resources().resourceBundleHints()      .findAny().isPresent()  :51
          jni().typeHints()                      .findAny().isPresent()  :52
          hasAnyDeprecatedHint(hints)  (javaSerializationHints)          :53, :57~59
```

이 게이트는 이 PR의 무대이면서 동시에 자매 PR #36989가 고친 자리이기도 하다.\
`:49`의 lambda 검사는 #36989가 추가한 줄이다.\
이 문서의 시나리오(리소스 패턴 힌트)는 `:50`에서 참이 되어 통과한다.

둘째, `BasicJsonWriter.writeValue`의 값 타입 분기.\
어떤 값이 어떤 JSON 형태가 되는지를 정한다.

```text
writeValue(value)                                     BasicJsonWriter.java:127
  │
  ├ value instanceof Map<?,?> ──────► writeObject(map, false)        :128~129
  │      └ 비어 있으면 "{ }", 아니면 "{" 개행 + 들여쓰기 + 속성들 + "}" :82~88
  │
  ├ value instanceof List<?> ───────► writeArray(list, false)        :131~132
  │      └ 비어 있으면 "[ ]", 아니면 "[" 개행 + 들여쓰기 + 항목들 + "]" :95~101
  │
  ├ value instanceof TypeReference ─► print(quote(name))             :134~135
  │      ★ escape 를 거치지 않는다 (타입 이름은 안전하다는 전제)
  │
  ├ value instanceof CharSequence ──► print(quote(escape(string)))   :137~138
  │      ★ 리소스 glob 패턴·번들 이름이 타는 경로 — 이 PR 시나리오
  │
  ├ value instanceof Boolean ───────► print(Boolean.toString(flag))  :140~141
  │
  └ 그 외 ──────────────────────────► throw IllegalStateException     :143~145
                                       ("unsupported type: …")
```

셋째, `escape(CharSequence)`의 문자별 분기.\
결함이 성립하는 데 필요한 두 조건 중 하나가 여기서 결정된다.

> **비ASCII 문자(non-ASCII)** — 7비트 ASCII 표(영문자·숫자·기본 기호) 밖에 있는 문자.\
> 예: `é`, 한글, 이모지가 전부 비ASCII이고, 이들은 charset에 따라 바이트 표현이 달라진다.

```text
escape(input)                                         BasicJsonWriter.java:153
  input.chars().forEach(c -> switch (c) {                            :155~156
    │
    ├ '"'  ──► "\\\""                                                :157
    ├ '\\' ──► "\\\\"                                                :158
    ├ '/'  ──► "\\/"                                                 :159
    ├ '\b' ──► "\\b"                                                 :160
    ├ '\f' ──► "\\f"                                                 :161
    ├ '\n' ──► "\\n"                                                 :162
    ├ '\r' ──► "\\r"                                                 :163
    ├ '\t' ──► "\\t"                                                 :164
    │
    └ default ─┬─ c <= 0x1F ──► String.format("\\u%04x", c)          :166~167
               │      (ASCII 제어문자만 유니코드 이스케이프)
               │
               └─ c >  0x1F ──► (char) c   ★ 그대로 통과              :169~171
                      'é'(U+00E9), 한글, 그 밖의 모든 비ASCII 가 여기
                      → 출력 문자열이 순수 ASCII 가 아니게 된다
                      → 최종 바이트 표현이 하위 Writer 의 charset 에 종속
  });
```

넷째, 그렇게 만들어진 문자열이 바이트가 되는 마지막 분기 — 정확히는 분기가 아니라 "결정권이 어디 있는가"의 문제다.\
버그가 살던 자리를 표시하면 다음과 같다.

```text
IndentingWriter.write(char[] chars, int offset, int length)          :262
  │
  ├ prependIndent == true ──► out.write(currentIndent…) 먼저          :264~267
  │
  └ out.write(chars, offset, length)                                 :268
        │
        ▼  out = FileWriter
        │
        ├─★ 수정 전: new FileWriter(file)          FileNativeConfigurationWriter:63
        │     charset = JVM 플랫폼 기본값
        │       ├ JDK 18+ 기본(JEP 400) ─────► UTF-8  → 'é' = 0xC3 0xA9  (정상)
        │       ├ -Dfile.encoding=windows-1252 ─► 'é' = 0xE9        (단일 바이트)
        │       └ 한국어 Windows MS949 등 ─────► 한글이 UTF-8 아닌 바이트열로
        │            → GraalVM 이 UTF-8 로 읽으면 디코딩 실패 또는 대체 문자
        │
        └── 수정 후: new FileWriter(file, StandardCharsets.UTF_8)
              charset 고정 → 실행 환경과 무관하게 동일한 바이트열
```

결함이 성립하려면 두 조건이 함께 필요하다.\
`escape`가 비ASCII를 통과시킬 것(`:169~171`), 그리고 `FileWriter`의 charset이 UTF-8이 아닐 것.\
어느 한쪽만으로는 문제가 되지 않는다.\
`escape`가 모든 비ASCII를 `\uXXXX`로 바꿨다면 출력이 순수 ASCII가 되어 charset과 무관해졌을 것이고, charset이 고정되어 있었다면 비ASCII가 통과해도 결과가 같았을 것이다.

두 조건이 어떻게 맞물리는지를 한 화면에 놓으면 이렇다.

```text
 조건 A: escape 가 비ASCII 를 통과시킨다   조건 B: FileWriter charset 이 UTF-8 이 아니다
   BasicJsonWriter.java:169~171             FileNativeConfigurationWriter.java:63 (수정 전)
        |                                            |
        +---------------+     +----------------------+
                        |     |
                        v     v
                     +-----------+
                     |  A AND B  |
                     +-----+-----+
                           |
             +-------------+-------------+
             |                           |
       둘 다 참                     하나라도 거짓
             |                           |
             v                           v
   디스크 바이트가 어긋난다          증상 없음
   (예: é -> 0xE9 한 바이트)        (예: é -> 0xC3 0xA9)
```

수정은 조건 B 쪽을 없앤다.\
`escape`의 통과 규칙(조건 A)은 그대로 두고, charset을 고정해 AND가 성립하지 않게 만든다.

## 4. 스프링 전역에서의 자리

이 스택은 Spring AOT 처리 파이프라인의 두 산출물 중 "네이티브 이미지 설정" 쪽 끝단이다.\
빌드 타임 코드 생성이 Java 소스를 내놓는 동안, 이 스택은 그 과정에서 수집된 `RuntimeHints`를 GraalVM이 읽을 JSON으로 내놓는다.\
즉 생산자는 Spring 빌드 플러그인, 소비자는 GraalVM `native-image` 컴파일러다.

> **네이티브 이미지(native image)** — JVM 없이 바로 실행되는 단일 실행 파일로 애플리케이션을 미리 컴파일해 둔 결과물.\
> 예: GraalVM `native-image` 컴파일러가 `META-INF/native-image/` 아래의 JSON을 읽어 그 실행 파일에 무엇을 넣을지 정한다.

파이프라인 전체에서의 위치를 grep으로 확인한 진입점과 함께 그리면 다음과 같다.

```text
빌드 타임 (Gradle/Maven AOT 플러그인)
   │
   ▼
AbstractAotProcessor<T>.process()                    AbstractAotProcessor.java:81
   │   Settings: sourceOutput / resourceOutput / classOutput / groupId / artifactId
   │                                                                    :134~152
   ▼  doProcess()  ← 하위 클래스가 구현                                  :91
   │
   ├──────────────────────────────┬────────────────────────────────────┐
   │ [애플리케이션 컨텍스트 경로]  │ [테스트 컨텍스트 경로]              │
   ▼                              ▼                                    │
ContextAotProcessor.doProcess()   TestAotProcessor.performAotProcessing()
   ContextAotProcessor.java:81       TestAotProcessor.java:87           │
   │ deleteExistingOutput()          │ scanClasspathRoots()             │
   │ prepareApplicationContext(...)  │ createFileSystemGeneratedFiles() │
   ▼                                 ▼                                  │
performAotProcessing(ctx)  :102   TestContextAotGenerator               │
   │                                 .processAheadOfTime(testClasses)   │
   ├ ApplicationContextAotGenerator                                     │
   │    .processAheadOfTime(ctx, generationContext)                     │
   │      → 빈 등록 코드 생성 (PR #36965 의 무대)                        │
   │      → 그 과정에서 RuntimeHints 에 힌트 누적                        │
   │                                                                    │
   ├ registerEntryPointHint(...)                    :108                │
   │    reflection().registerType(applicationType)  :149                │
   │    reflection().registerType(generatedType, …) :150~151            │
   │                                                                    │
   ├ generationContext.writeGeneratedContent()      :109                │
   │    → sourceOutput 에 *__BeanDefinitions.java → javac               │
   │                                                                    │
   ├─★ writeHints(generationContext.getRuntimeHints())  :110 ◄──────────┘
   │        │                              TestAotProcessor.java:92 도 동일 호출
   │        ▼
   │   AbstractAotProcessor.writeHints(hints)     AbstractAotProcessor.java:124
   │        new FileNativeConfigurationWriter(                          :125
   │            getSettings().getResourceOutput(),
   │            getSettings().getGroupId(),
   │            getSettings().getArtifactId())                          :126
   │        writer.write(hints)                                         :127
   │             │
   │             ▼  ★ 이 문서의 무대 (1~3장)
   │        resourceOutput/META-INF/native-image/<groupId>/<artifactId>/
   │             reachability-metadata.json
   │
   └ writeNativeImageProperties(getDefaultNativeImageArguments(mainClass)) :111
          resourceOutput/META-INF/native-image/<groupId>/<artifactId>/
             native-image.properties        ContextAotProcessor.java:161~168
          (내용: "Args = -H:Class=… \ --no-fallback")            :136~141
   │
   ▼
GraalVM native-image 컴파일
   META-INF/native-image/** 아래의 JSON·properties 를 읽어
   리플렉션·리소스·프록시 메타데이터를 이미지에 반영 (UTF-8 로 읽음)
```

grep으로 확인한 `NativeConfigurationWriter` 계층의 프로덕션 호출처는 정확히 한 곳, `AbstractAotProcessor.writeHints`(`AbstractAotProcessor.java:124~128`)다.\
그리고 그 메서드를 부르는 곳이 두 곳이다 — `ContextAotProcessor.performAotProcessing:110`(애플리케이션 AOT)과 `TestAotProcessor.performAotProcessing:92`(테스트 컨텍스트 AOT).\
`AbstractAotProcessor`의 클래스 javadoc이 `@see FileNativeConfigurationWriter`(`:45`)로 이 관계를 명시한다.

좁은 진입점이라는 사실이 이 PR의 성격을 규정한다.\
인코딩 결정권이 한 곳에 모여 있으므로 한 줄 수정으로 전체 파이프라인의 출력이 고정되고, 반대로 그 한 줄이 환경 의존적이면 모든 AOT 산출물이 함께 흔들린다.

`resourceOutput` 아래에 놓인다는 점도 의미가 있다.\
생성 소스가 `sourceOutput`으로 가서 javac를 거치는 것과 달리, 이 JSON은 리소스로서 그대로 아티팩트에 실려 나간다.\
즉 컴파일 단계의 검증을 전혀 받지 않고 GraalVM에 도달한다.\
잘못된 바이트가 섞여도 빌드는 초록색이고, 증상은 네이티브 런타임의 리소스 누락으로 뒤늦게 나타난다.

두 산출물이 받는 검증의 차이를 나란히 놓으면 이렇다.

```text
 [생성 Java 소스]                      [네이티브 설정 JSON]
 sourceOutput/*__BeanDefinitions.java  resourceOutput/META-INF/native-image/
        |                                     reachability-metadata.json
        v                                          |
      javac 컴파일                                 v
        |                                   (컴파일 단계 없음)
        v                                          |
  문법·타입 오류면 빌드가 즉시 실패            그대로 아티팩트에 실림
                                                   |
                                                   v
                                            GraalVM 이 읽을 때 처음 해석
                                            바이트가 어긋나도 빌드는 초록색
```

## 5. 관련 개념

### 5.1 GraalVM 닫힌 세계 가정과 reachability metadata

GraalVM `native-image`는 닫힌 세계 가정(closed-world assumption) 위에서 동작한다.\
빌드 시점 정적 분석으로 도달 가능하다고 판단된 클래스·메서드·필드만 이미지에 남고 나머지는 제거된다.\
리플렉션·동적 프록시·리소스 로딩처럼 정적 분석이 볼 수 없는 접근은 별도 메타데이터로 알려 주어야 한다.

> **닫힌 세계 가정(closed-world assumption)** — 빌드 시점에 프로그램이 쓸 코드와 자원이 전부 정해져 있다고 보고, 그 밖의 것은 없는 셈 치는 전제.\
> 예: 실행 중에 이름으로 클래스를 찾아 쓰는 리플렉션은 이 전제 아래서 보이지 않으므로 미리 목록으로 신고해야 한다.

> **reachability metadata(도달 가능성 메타데이터)** — 정적 분석이 스스로 찾지 못하는 접근 대상을 적어 둔 신고서.\
> 예: `reachability-metadata.json`의 `{"glob": "com/example/café/**"}` 한 줄이 "이 리소스들도 이미지에 넣어라"라는 신고다.

그 메타데이터가 `META-INF/native-image/` 아래에 놓이는 JSON이고, 최신 GraalVM에서는 여러 파일로 나뉘어 있던 것이 `reachability-metadata.json` 하나로 통합되었다.\
`NativeConfigurationWriter.write`가 이 파일명을 하드코딩하고 있는 것(`NativeConfigurationWriter.java:41`)이 그 통합의 반영이다.

Spring 쪽에서 이 메타데이터를 자바 객체로 모으는 API가 `org.springframework.aot.hint` 패키지의 `RuntimeHints`이고, 그것을 JSON으로 옮기는 것이 이 문서의 무대인 `org.springframework.aot.nativex` 패키지다.\
두 패키지의 분리가 "수집"과 "직렬화"의 경계다.

### 5.2 플랫폼 기본 charset — `FileWriter`와 JEP 400

`java.io.FileWriter`를 charset 인자 없이 생성하면 JVM의 플랫폼 기본 charset으로 인코딩한다.\
이 기본값은 `file.encoding` 시스템 프로퍼티가 결정하며, 역사적으로 OS와 로케일에 따라 달랐다 — 한국어 Windows의 MS949, 서유럽권의 windows-1252가 대표적이다.

> **플랫폼 기본 charset(platform default charset)** — 프로그램이 charset을 명시하지 않았을 때 JVM이 대신 골라 주는 인코딩.\
> 예: 같은 코드가 리눅스에서는 UTF-8로, 한국어 Windows에서는 MS949로 파일을 쓰게 된다.

JDK 18의 JEP 400이 이 기본값을 UTF-8로 통일했다.\
다만 `-Dfile.encoding=...`으로 명시 지정하면 여전히 다른 값이 될 수 있고, JDK 18 미만 환경도 남아 있다.\
즉 "요즘은 대부분 UTF-8"이지만 "언제나 UTF-8"은 아니다.

> **JEP 400** — "UTF-8 by Default", JDK 18에서 플랫폼 기본 charset을 OS·로케일과 무관하게 UTF-8로 고정한 변경 제안.\
> 예: JDK 18 이전 Windows에서 돌던 같은 코드가 JDK 18부터는 같은 머신에서도 UTF-8로 쓴다.

`FileWriter(File, Charset)`는 JDK 11에서 추가된 생성자다.\
Spring Framework 7.x의 baseline이 그보다 높으므로 사용에 제약이 없다.

이런 종류의 API — 인코딩·로케일·타임존처럼 "플랫폼 기본값"에 암묵적으로 의존하는 API — 는 그 자체가 잠재적 결함이다.\
개발 환경에서는 기본값이 우연히 맞아떨어져 조용히 지나가고, 다른 환경에서 원인과 동떨어진 증상으로 터진다.\
그리고 빌드 산출물이라면 문제가 한층 더 나쁘다.\
어느 머신에서 빌드했느냐에 따라 산출물의 바이트가 달라지기 때문이다.

같은 소스, 같은 힌트를 서로 다른 머신에서 빌드했을 때 무엇이 갈라지는지를 나란히 놓으면 이렇다.

```text
 [빌드 머신 A]  기본 charset = UTF-8      [빌드 머신 B]  기본 charset = windows-1252
 +--------------------------------+      +--------------------------------+
 | 소스 동일 · 힌트 동일          |      | 소스 동일 · 힌트 동일          |
 | new FileWriter(file)           |      | new FileWriter(file)           |
 +--------------------------------+      +--------------------------------+
        |                                        |
        v                                        v
 é -> 0xC3 0xA9                           é -> 0xE9
        |                                        |
        v                                        v
 GraalVM 이 UTF-8 로 읽어 é 복원          GraalVM 이 UTF-8 로 읽어 실패/대체 문자
        |                                        |
        v                                        v
 리소스 포함                              리소스 누락 (런타임에야 드러남)
```

### 5.3 JSON과 비ASCII — 이스케이프는 선택 사항이다

JSON 명세는 문자열 안의 비ASCII 문자를 그대로 두는 것도, `\uXXXX`로 이스케이프하는 것도 모두 허용한다.\
반드시 이스케이프해야 하는 것은 따옴표·역슬래시·제어문자뿐이다.\
`BasicJsonWriter.escape`가 `c <= 0x1F`만 유니코드 이스케이프하고 나머지를 통과시키는 것(`BasicJsonWriter.java:166~171`)은 이 명세에 부합하는 선택이다.

> **제어문자(control character)** — 화면에 글자로 보이지 않고 동작을 지시하는 문자. 코드값 `0x00`~`0x1F` 구간.\
> 예: 줄바꿈(`\n`)·탭(`\t`)이 여기 속하고, 그래서 JSON 문자열 안에서는 반드시 이스케이프해야 한다.

대신 이 선택은 출력이 순수 ASCII가 아님을 뜻하고, 그 순간 "파일의 바이트 표현"이 charset에 종속된다.\
만약 모든 비ASCII를 이스케이프했다면 출력은 ASCII만으로 이루어져 어떤 charset으로 써도 같은 바이트가 나왔을 것이다.\
두 설계 선택 — 이스케이프 범위와 charset 지정 — 이 맞물려야 이 PR이 다루는 결함이 성립한다는 것이 3장 분기도의 요지다.

### 5.4 `Writer` 데코레이터 사슬과 인코딩 경계

`java.io.Writer` 계열은 문자 스트림이고 `OutputStream` 계열은 바이트 스트림이다.\
둘 사이를 잇는 것이 `OutputStreamWriter`이며 `FileWriter`는 그 서브클래스다.\
즉 `FileWriter`가 이 스택에서 문자를 바이트로 바꾸는 유일한 경계다.

> **데코레이터(decorator)** — 같은 인터페이스를 유지한 채 원본 객체를 감싸, 일부 동작만 얹고 나머지는 그대로 넘기는 구조.\
> 예: `IndentingWriter`는 들여쓰기만 앞에 붙이고 쓰기 자체는 안쪽 `FileWriter`에 그대로 넘긴다.

이 무대의 사슬을 다시 짚으면 이렇다.\
`BasicJsonWriter`는 `String`을 조립하고, `IndentingWriter`(`BasicJsonWriter.java:179`)는 `Writer`를 상속하지만 하는 일은 들여쓰기 삽입뿐이다 — `write(char[], int, int)`가 현재 들여쓰기를 앞에 붙인 뒤 `out.write(...)`로 그대로 위임한다(`:262~273`).\
개행도 `System.lineSeparator()`를 그대로 쓴다(`:218`).\
어느 층도 인코딩을 건드리지 않는다.

데코레이터 사슬에서 인코딩 같은 횡단 관심사는 경계 층 하나에만 존재하며, 그 층에서 명시하지 않으면 기본값이 조용히 개입한다.\
이 무대는 그 원리를 그대로 보여 준다 — 다섯 층 중 네 층이 문자만 다루고, 마지막 한 층의 생성자 인자 하나가 전체 산출물의 바이트를 결정한다.

> **횡단 관심사(cross-cutting concern)** — 여러 층에 걸쳐 영향을 주지만 어느 한 층에서만 실제로 결정되는 관심사.\
> 예: 인코딩은 다섯 층 전부의 출력에 영향을 주지만 결정은 `FileWriter` 생성 한 줄에서만 일어난다.

### 5.5 자매 PR과의 관계

같은 스택을 무대로 하는 PR이 두 건 더 있다.\
`NativeConfigurationWriter.hasAnyHint`의 게이트에 lambda 힌트 검사를 추가한 [#36989](../36989-lambda-hints-file-emission/structure.md)가 3장 첫 분기도의 `:49`를 만들었다.\
`ValueCodeGenerator`를 무대로 하는 [#36965](../36965-valuecodegen-nonfinite-doubles/structure.md)는 같은 AOT 파이프라인의 다른 줄기 — 생성 Java 소스 쪽 — 를 다룬다.\
4장 파이프라인 그림에서 세 PR의 자리를 함께 확인할 수 있다.
