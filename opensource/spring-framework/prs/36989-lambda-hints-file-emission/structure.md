# PR #36989 — 무대 구조와 워크플로우

> PR #36989의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
> 기준: upstream main `526c706d1c3`.\
> 이 PR은 이미 반영되었으므로 `NativeConfigurationWriter.java:49`의 lambda 검사는 "수정 후" 코드다.\
> 수정 전 형태가 필요한 곳은 그때마다 명시한다.\
> 나머지 인용은 이 PR로 바뀌지 않았으므로 수정 전후가 동일하다.

이 문서가 다루는 것은 Spring AOT가 수집한 힌트를 네이티브 설정 파일로 내보낼지 말지 정하는 관문의 실구조다.\
힌트를 모으는 쪽과 직렬화하는 쪽 두 패키지의 소유 그래프에서 출발해, 게이트를 통과하는 경로와 끊기는 경로를 나란히 따라가고, 분기도로 결함이 살던 자리를 짚은 뒤, 이 관문이 AOT 파이프라인 전체에서 차지하는 자리와 배경 개념을 정리한다.

> **AOT(ahead-of-time) 처리** — 애플리케이션을 실행하기 전 빌드 시점에 빈 등록 코드와 네이티브 이미지용 메타데이터를 미리 확정해 두는 Spring의 처리 단계.\
> 예: `AbstractAotProcessor`가 빌드 중에 돌면서 `*__BeanDefinitions.java`와 `reachability-metadata.json`을 만들어 놓는다.

> **힌트(runtime hint)** — 정적 분석이 볼 수 없는 접근(리플렉션·프록시·리소스·lambda)을 "이건 런타임에 필요하다"고 미리 적어 두는 메타데이터 한 건.\
> 예: `registerLambda(Integer.class, …)` 한 번이 lambda 힌트 한 건을 만든다.

> **게이트(gate)** — 뒤쪽 작업을 할지 말지 앞에서 한 번 판정하는 관문.\
> 예: 여기서는 `hasAnyHint(hints)`가 거짓이면 직렬화 코드가 한 줄도 실행되지 않는다.

## 1. 무대 — 실구조

이 PR의 무대는 두 개의 대칭 구조와 그 사이를 잇는 게이트 하나다.\
왼쪽에는 힌트를 자바 객체로 모으는 `org.springframework.aot.hint` 패키지가 있고, 오른쪽에는 그 객체를 JSON으로 옮기는 `org.springframework.aot.nativex` 패키지가 있다.\
두 패키지가 "힌트 종류"라는 같은 목록을 각자 알고 있어야 하는데, 게이트 하나가 그 목록의 일부를 놓치고 있었던 것이 이 PR의 결함이다.

두 패키지와 그 사이의 게이트를 한 화면에 놓으면 이렇다.

```text
  수집 쪽                        게이트                      직렬화 쪽
  org.springframework.aot.hint                              org.springframework.aot.nativex
  +----------------------+                                  +--------------------------+
  | RuntimeHints         |                                  | RuntimeHintsWriter       |
  |   reflection         |      +------------------+        |   ReflectionHintsAttr..  |
  |     types       O    | ---> | hasAnyHint(...)  | -----> |   ResourceHintsAttr..    |
  |     lambdaHints O    |      |  종류를 손으로   |  true  |                          |
  |   resources     O    |      |  나열한 OR 사슬  |        | 아는 종류:               |
  |   proxies       O    |      +------------------+        |   types      O           |
  |   jni           O    |            |  false              |   lambdaHints O  <-- 안다 |
  |   serialization O    |            v                     |   resources  O           |
  +----------------------+      아무것도 안 함              |   proxies    O           |
                                 (파일 없음)                 |   jni(types) O           |
                                                            +--------------------------+

  수정 전: 게이트가 아는 종류에서 lambdaHints 만 빠져 있었다.
           직렬화 쪽은 알고 있었는데, 거기까지 가지를 못했다.
```

먼저 수집 쪽 소유 그래프다.\
`RuntimeHints`가 다섯 개의 하위 힌트 묶음을 필드로 들고, 각 묶음이 자기 컬렉션을 소유한다.

> **`RuntimeHints`** — 한 번의 AOT 처리에서 모인 모든 힌트를 종류별로 담아 두는 최상위 그릇.\
> 예: `hints.reflection()`·`hints.resources()`처럼 묶음별 접근자로 꺼내 쓴다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ RuntimeHints                                     RuntimeHints.java:34    │
│                                                                          │
│  - reflection    : ReflectionHints                                 :36   │
│  - resources     : ResourceHints                                   :38   │
│  - serialization : SerializationHints  @Deprecated(7.0.6, 제거예정):41   │
│  - proxies       : ProxyHints                                      :43   │
│  - jni           : ReflectionHints  ← reflection 과 같은 타입, 다른 인스턴스:45│
│                                                                          │
│  + reflection() / resources() / serialization() / proxies() / jni()      │
│                                              :52, :60, :71, :79, :87     │
│  ★ "비어 있는가"를 스스로 답하는 메서드가 없다 — 3장의 결함 원인          │
└───┬──────────────┬──────────────┬──────────────┬──────────────┬──────────┘
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
┌────────────────────────────────┐ ┌──────────────────────┐ ┌─────────────┐
│ ReflectionHints                │ │ ResourceHints        │ │ ProxyHints  │
│   ReflectionHints.java:46      │ │  ResourceHints.java  │ │ ProxyHints  │
│                                │ │                      │ │  .java      │
│ ★ 두 종류의 상태를 나란히 소유 │ │ - types         :42  │ │ - jdkProxies│
│  - types : Map<TypeReference,  │ │ - resourcePattern    │ │        :32  │
│      TypeHint.Builder>    :48  │ │     Hints       :44  │ │             │
│  - lambdaHints :               │ │ - resourceBundle     │ │ + jdkProxy  │
│      Set<LambdaHint>      :50  │ │     Hints       :46  │ │   Hints():39│
│                                │ │                      │ └─────────────┘
│  + typeHints() : Stream<TypeHint>│ │ + resourcePattern   │
│                           :56  │ │   Hints()       :60  │
│  + lambdaHints() : Stream<     │ │ + resourceBundle     │
│      LambdaHint>  (@since 7.0.6)│ │   Hints()       :69  │
│                           :66  │ └──────────────────────┘
│  + registerType(...) 4 오버로드 │
│                  :98,111,122,137│
│  + registerField / registerMethod / registerConstructor
│                       :218,242,230
│  + registerJavaSerialization(Class) (@since 7.0.6)   :253
│  + registerLambda(TypeReference, Consumer<LambdaHint.Builder>) :265
│  + registerLambda(Class, Consumer<LambdaHint.Builder>)         :279
└────────────────────────┬───────────────────────────────────────┘
                         │ lambdaHints 집합에 담기는 값
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ final class LambdaHint implements ConditionalHint    LambdaHint.java:31  │
│  - declaringClass  : TypeReference                                 :33  │
│  - reachableType   : @Nullable TypeReference                       :35  │
│  - declaringMethod : @Nullable DeclaringMethod                     :37  │
│  - interfaces      : List<TypeReference>                           :39  │
│  + of(TypeReference) / of(Class<?>) : Builder                  :53, :62 │
│  + getDeclaringClass() / getReachableType() / getDeclaringMethod()      │
│    / getInterfaces()                              :70, :75, :83, :91    │
│                                                                         │
│  static class Builder                                              :95  │
│    + onReachableType(...) / withDeclaringMethod(...) / withInterfaces() │
│                                    :115,126 / :137,148 / :157,167       │
│    + build() : LambdaHint                                          :172 │
│                                                                         │
│  record DeclaringMethod(String name, List<TypeReference> parameterTypes)│
│                                                                    :183 │
└──────────────────────────────────────────────────────────────────────────┘
```

다음은 직렬화 쪽이다.\
이 PR의 게이트가 사는 자리를 별표로 표시했다.

> **직렬화(serialization)** — 메모리 안의 객체를 파일·네트워크로 옮길 수 있는 형태(여기서는 JSON 텍스트)로 바꾸는 일.\
> 예: `LambdaHint` 객체 하나가 `{"type":{"lambda":{…}}}`라는 JSON 조각이 된다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ abstract NativeConfigurationWriter      NativeConfigurationWriter.java:33│
│   + write(RuntimeHints)                                            :39  │
│   ★ - hasAnyHint(RuntimeHints) : boolean      이 PR 의 무대         :46  │
│     - hasAnyDeprecatedHint(RuntimeHints) : boolean                 :57  │
│   # abstract writeTo(String, Consumer<BasicJsonWriter>)            :67  │
│                             △ extends                                   │
│ FileNativeConfigurationWriter     FileNativeConfigurationWriter.java:38  │
│   - basePath / groupId / artifactId                          :40,42,44  │
│   # writeTo(...)  → createIfNecessary + FileWriter(UTF_8)      :60~70   │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ class RuntimeHintsWriter                     RuntimeHintsWriter.java:35  │
│   + write(BasicJsonWriter, RuntimeHints)                           :37  │
│       "comment"    ← SpringVersion.getVersion()                :39~41   │
│       "reflection" ← new ReflectionHintsAttributes().reflection(hints)  │
│                                                                 :43~46  │
│       "jni"        ← new ReflectionHintsAttributes().jni(hints) :47~50  │
│       "resources"  ← new ResourceHintsAttributes().resources(…) :51~54  │
│       writer.writeObject(document)                                 :56  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ class ReflectionHintsAttributes       ReflectionHintsAttributes.java:56  │
│   - JDK_PROXY_HINT_COMPARATOR                                      :58  │
│   - LAMBDA_HINT_COMPARATOR  (declaringClass → declaringMethod.name):67  │
│   + reflection(RuntimeHints) : List<Map<String,Object>>            :73  │
│   - reflectionHints(RuntimeHints)                                  :82  │
│       ★ typeHints + javaSerializationHints + lambdaHints 를 병합   :93~95│
│   + jni(RuntimeHints)                                              :98  │
│   - toAttributes(TypeHint)                                        :106  │
│   ★ - toAttributes(LambdaHint) → {"type": {"lambda": {…}}}        :118  │
│   - toAttributes(JavaSerializationHint) / (JdkProxyHint)     :136, :197 │
└──────────────────────────────────────────────────────────────────────────┘
```

핵심은 두 그림의 비대칭이다.\
`ReflectionHintsAttributes`는 `lambdaHints()`를 알고 있고(`:95`, `:118`) 전용 직렬화 메서드까지 갖추었다.\
반면 `NativeConfigurationWriter.hasAnyHint`는 하위 힌트 묶음을 손으로 나열한 OR 사슬이며, 수정 전에는 그 목록에 lambda가 없었다.

> **OR 사슬(disjunction chain)** — 조건 여러 개를 `||`로 줄줄이 이어 놓은 판정식.\
> 예: `A() || B() || C()`는 셋 중 하나만 참이어도 전체가 참이 된다.

## 2. 수정 전 동작 워크플로우

대표 시나리오 두 개를 나란히 보면 결함의 성격이 드러난다.\
첫째는 타입 힌트가 있는 정상 경로, 둘째는 lambda 힌트만 있는 결함 경로다.\
아래 흐름에서 `hasAnyHint`는 수정 전 형태(lambda 검사 없음)로 서술한다.

시나리오 A — 타입 힌트가 하나라도 있을 때.\
게이트를 통과하고 파일이 만들어진다.

```text
hints.reflection().registerType(String.class, …)   ReflectionHints.java:122
   └ types.computeIfAbsent(TypeReference.of(String), TypeHint.Builder::new)  :99

new FileNativeConfigurationWriter(tempDir).write(hints)
   │
   ▼
NativeConfigurationWriter.write(hints)                                  :39
   │
   ├ hasAnyHint(hints)                                                  :46
   │    proxies().jdkProxyHints().findAny().isPresent()      → false    :47
   │    reflection().typeHints().findAny().isPresent()       → true ★   :48
   │    (단락 평가로 나머지는 평가되지 않음)
   │    → true
   │
   └ writeTo("reachability-metadata.json", writer -> …)                 :41~42
        │
        ▼
      FileNativeConfigurationWriter.writeTo(...)   FileNativeConfigurationWriter.java:60
        file = createIfNecessary(fileName)                              :62
        out  = new FileWriter(file, StandardCharsets.UTF_8)             :63
        writer.accept(new BasicJsonWriter(out))                         :64, :83~85
        │
        ▼
      RuntimeHintsWriter.write(jsonWriter, hints)      RuntimeHintsWriter.java:37
        reflection = new ReflectionHintsAttributes().reflection(hints)  :43
        │    └ reflectionHints(hints)         ReflectionHintsAttributes.java:82
        │         allTypeHints = typeHints().map(toAttributes)          :83~85
        │         + javaSerializationHints 병합                          :86~92
        │         Stream.concat(정렬된 타입힌트, 정렬된 lambda힌트)      :93~95
        │    document.put("reflection", reflection)                     :44~46
        │
        writer.writeObject(document)                                    :56
        │
        ▼
      디스크: META-INF/native-image/reachability-metadata.json  (생성됨)
```

시나리오 B — lambda 힌트만 있을 때.\
수정 전에는 여기서 흐름이 끊긴다.

> **lambda 힌트(`LambdaHint`)** — 어느 클래스의 어느 메서드 안에서 어떤 함수형 인터페이스를 구현하는 lambda가 만들어지는지를 적어 둔 힌트.\
> 예: `Integer.getCell(Integer, Integer)` 안에서 `Supplier`를 구현하는 lambda가 만들어진다는 기술.

```text
hints.reflection().registerLambda(Integer.class, builder -> builder
        .withDeclaringMethod("getCell", Integer.class, Integer.class)
        .withInterfaces(Supplier.class))          ReflectionHints.java:279
   │  └ registerLambda(TypeReference.of(Integer.class), lambdaHint)     :280
   │       LambdaHint.Builder builder = LambdaHint.of(declaringClass)   :266
   │       lambdaHint.accept(builder)                                   :267
   │       lambdaHints.add(builder.build())        ← Set<LambdaHint>    :268
   ▼
   상태: types = {} (비어 있음),  lambdaHints = { LambdaHint(Integer, …) }

new FileNativeConfigurationWriter(tempDir).write(hints)
   │
   ▼
NativeConfigurationWriter.write(hints)                                  :39
   │
   ├ hasAnyHint(hints)   ★ 수정 전 목록                                 :46
   │    proxies().jdkProxyHints()          .findAny().isPresent() → false
   │    reflection().typeHints()           .findAny().isPresent() → false
   │    ────────── lambdaHints() 검사가 목록에 없다 ──────────
   │    resources().resourcePatternHints() .findAny().isPresent() → false
   │    resources().resourceBundleHints()  .findAny().isPresent() → false
   │    jni().typeHints()                  .findAny().isPresent() → false
   │    hasAnyDeprecatedHint(hints)                               → false :57~59
   │    → false
   │
   └ if 가 거짓 ──► writeTo(...) 에 도달하지 않음                        :40
        예외 없음 · 경고 없음 · 파일 없음
        → 아래 직렬화 경로 전체가 한 번도 실행되지 않는다
              (RuntimeHintsWriter · ReflectionHintsAttributes.toAttributes(LambdaHint)
               모두 lambda 를 정상 처리할 준비가 되어 있었음에도)
```

시나리오 B 하나를 수정 전후로 나란히 놓으면 이렇다.\
입력은 완전히 같고, 게이트의 판정 한 칸만 다르다.

```text
  같은 입력: hints.reflection().registerLambda(Integer.class, ...) 한 번

  수정 전                              수정 후
  +---------------------------+        +---------------------------+
  | types       = {}          |        | types       = {}          |
  | lambdaHints = {LambdaHint}|        | lambdaHints = {LambdaHint}|
  +---------------------------+        +---------------------------+
             |                                    |
             v                                    v
  +---------------------------+        +---------------------------+
  | hasAnyHint :47 jdkProxy F |        | hasAnyHint :47 jdkProxy F |
  |            :48 typeHints F|        |            :48 typeHints F|
  |            (lambda 항 없음)|        |            :49 lambda   T |
  |            :50~53  전부 F |        |            (뒤는 평가 안함)|
  |            -> false       |        |            -> true        |
  +---------------------------+        +---------------------------+
             |                                    |
             v                                    v
  writeTo 호출 안 됨                    writeTo("reachability-metadata.json")
             |                                    |
             v                                    v
  +---------------------------+        +---------------------------+
  | 파일 없음                 |        | reachability-metadata.json|
  | 예외 없음 / 로그 없음     |        |   "reflection": [ {       |
  | 빌드 초록                 |        |     "type": { "lambda": ..|
  +---------------------------+        +---------------------------+

  차이를 만든 것은 게이트의 한 칸뿐이고, 직렬화 코드는 양쪽에서 같다.
```

수정 후에는 `hasAnyHint`에 `hints.reflection().lambdaHints().findAny().isPresent()`(`NativeConfigurationWriter.java:49`) 한 줄이 들어가 시나리오 B가 시나리오 A와 같은 경로를 탄다.\
그때 만들어지는 JSON의 모양은 `toAttributes(LambdaHint)`(`ReflectionHintsAttributes.java:118~133`)가 정한다.

```text
toAttributes(LambdaHint hint)                ReflectionHintsAttributes.java:118
   lambdaAttributes.put("declaringClass", hint.getDeclaringClass())     :121
   declaringMethod != null ?                                           :122~128
        methodAttributes.put("name", declaringMethod.name())            :124
        methodAttributes.put("parameterTypes", …parameterTypes())       :125
        lambdaAttributes.put("declaringMethod", methodAttributes)       :126
   lambdaAttributes.put("interfaces", hint.getInterfaces())             :129
   attributes.put("lambda", lambdaAttributes)                           :131
   return Map.of("type", attributes)                                    :132
   │
   ▼ BasicJsonWriter 를 거쳐 나오는 형태
{ "reflection": [ { "type": { "lambda": {
      "declaringClass": "java.lang.Integer",
      "declaringMethod": { "name": "getCell",
                           "parameterTypes": [ "java.lang.Integer", "java.lang.Integer" ] },
      "interfaces": [ "java.util.function.Supplier" ] } } } ] }
```

## 3. 분기 처리 워크플로우

무대의 결정적 분기는 하나, `write()`의 게이트다.\
버그는 그 게이트의 판정자 안에 살았다.

```text
NativeConfigurationWriter.write(hints)                                   :39
  │
  ├─ hasAnyHint(hints) == true ────► writeTo("reachability-metadata.json", …) :41
  │                                    → 파일 생성 + JSON 직렬화
  │
  └─ hasAnyHint(hints) == false ───► 아무것도 하지 않음 (조용히 반환)     :40
                                       계약: 힌트가 전혀 없으면 파일도 없다
```

판정자 `hasAnyHint`의 내부는 종류별 존재 검사를 `||`로 이은 사슬이며, 단락 평가로 첫 참에서 끝난다.\
수정 전후를 겹쳐 그리면 다음과 같다.

> **단락 평가(short-circuit evaluation)** — `||`에서 앞쪽이 참이면 뒤쪽 식은 아예 실행하지 않는 자바의 규칙.\
> 예: `:48`에서 참이 나오면 `:49` 이하의 스트림은 만들어지지도 않는다.

```text
hasAnyHint(hints)                              NativeConfigurationWriter.java:46
  │
  ├─ hints.proxies().jdkProxyHints().findAny().isPresent()          → true? :47
  │      └ ProxyHints.jdkProxies (Set<JdkProxyHint>)      ProxyHints.java:32
  │
  ├─ hints.reflection().typeHints().findAny().isPresent()           → true? :48
  │      └ ReflectionHints.types (Map<TypeReference, Builder>) ReflectionHints:48
  │
  ├─★ hints.reflection().lambdaHints().findAny().isPresent()        → true? :49
  │      └ ReflectionHints.lambdaHints (Set<LambdaHint>)       ReflectionHints:50
  │      ┌──────────────────────────────────────────────────────────────┐
  │      │ 버그가 살던 분기: 수정 전에는 이 줄이 통째로 없었다.          │
  │      │  결과 — lambdaHints 만 채워진 RuntimeHints 는 "힌트 없음"     │
  │      │  으로 판정되어 파일이 생성되지 않았다.                       │
  │      │  실패 방식: 예외 없음 / 로그 없음 / 빌드 초록색.              │
  │      └──────────────────────────────────────────────────────────────┘
  │
  ├─ hints.resources().resourcePatternHints().findAny().isPresent() → true? :50
  │      └ ResourceHints.resourcePatternHints (List)        ResourceHints:44
  │
  ├─ hints.resources().resourceBundleHints().findAny().isPresent()  → true? :51
  │      └ ResourceHints.resourceBundleHints (Set)          ResourceHints:46
  │
  ├─ hints.jni().typeHints().findAny().isPresent()                  → true? :52
  │      └ RuntimeHints.jni 는 별도의 ReflectionHints 인스턴스 RuntimeHints:45
  │        ※ jni().lambdaHints() 는 여기서도 검사하지 않는다
  │
  └─ hasAnyDeprecatedHint(hints)                                    → true? :53
         hints.serialization().javaSerializationHints().findAny().isPresent() :58
         (@Deprecated(since 7.0.6, forRemoval) — reflection 쪽으로 이관 중)
  │
  └ 전부 false ─────────────────────────────► return false
```

분기도가 드러내는 구조적 사실은 이것이다.\
이 메서드는 "힌트가 있는가"를 힌트 모델에게 묻지 않고, 자기가 아는 종류를 손으로 나열해 묻는다.\
`RuntimeHints`에는 `isEmpty()` 같은 메서드가 없으므로(1장 그림의 별표) 이 열거는 모델의 종류 목록을 통째로 복제한 코드이며, 새 종류가 추가될 때 함께 갱신되지 않으면 조용히 틀린다.\
컴파일러는 이 누락을 잡아 주지 않는다.

대조적으로 직렬화 쪽 분기는 lambda를 이미 알고 있었다.

```text
ReflectionHintsAttributes.reflectionHints(hints)  ReflectionHintsAttributes.java:82
  │
  ├ allTypeHints = typeHints().map(toAttributes)
  │                  .collect(toMap(attributes.get("type"), attributes))     :83~85
  │
  ├ javaSerializationHints().forEach(hint -> allTypeHints.merge(...))        :86~92
  │      └ 이미 있는 타입이면 handleSerializable(current, true) 로 병합       :89
  │
  └ return Stream.concat(                                                    :93
        allTypeHints 정렬 스트림,                                             :94
        ★ hints.reflection().lambdaHints()
             .sorted(LAMBDA_HINT_COMPARATOR).map(this::toAttributes)         :95
      ).toList()
```

즉 게이트를 통과하기만 하면 lambda JSON은 정상적으로 나온다.\
두 계층의 준비 상태가 어긋나 있었다는 것이 결함의 요지이며, 그래서 수정이 한 줄로 끝난다.

## 4. 스프링 전역에서의 자리

이 게이트는 Spring AOT 처리 파이프라인이 네이티브 이미지 설정 파일을 "내놓을지 말지" 결정하는 마지막 관문이다.\
그 앞에서 빌드 타임 코드 생성이 `RuntimeHints`를 채우고, 그 뒤에서 GraalVM `native-image`가 그 파일을 읽는다.\
관문이 잘못 닫히면 메타데이터가 통째로 사라지고, 그 사실은 네이티브 런타임에 가서야 드러난다.

> **GraalVM `native-image`** — 자바 애플리케이션을 JVM 없이 바로 뜨는 실행 파일로 미리 컴파일해 주는 도구.\
> 예: 빌드 시점에 `META-INF/native-image/**`의 메타데이터를 읽어 어떤 클래스를 이미지에 남길지 정한다.

grep으로 확인한 진입 경로는 다음과 같다.

```text
빌드 타임 (Gradle/Maven AOT 플러그인)
   │
   ▼
AbstractAotProcessor<T>.process() → doProcess()      AbstractAotProcessor.java:81, :91
   │   Settings(sourceOutput, resourceOutput, classOutput, groupId, artifactId) :134
   │
   ├───────────────────────────────┬─────────────────────────────────────┐
   ▼                               ▼                                     │
ContextAotProcessor.doProcess()  TestAotProcessor.performAotProcessing() │
   ContextAotProcessor.java:81      TestAotProcessor.java:87             │
   │                                │ TestContextAotGenerator            │
   ▼ performAotProcessing(ctx) :102 │   .processAheadOfTime(testClasses) │
   │                                │                                    │
   ├ ApplicationContextAotGenerator.processAheadOfTime(ctx, generationContext)
   │      ApplicationContextAotGenerator.java:51                          │
   │      │  빈 등록 코드를 생성하면서 RuntimeHints 에 힌트를 누적        │
   │      │  (BeanDefinitionPropertiesCodeGenerator 가 리플렉션 힌트 등록:│
   │      │   registerMethod/registerType — 이 경로가 types 를 채운다)    │
   │      ▼                                                              │
   ├ registerEntryPointHint(generationContext, generatedInitializerClassName) :108
   │      reflection.registerType(applicationType)                  :149  │
   │      reflection.registerType(generatedType, typeHint -> …)     :150  │
   │                                                                      │
   ├ generationContext.writeGeneratedContent()                      :109  │
   │      → sourceOutput 의 *__BeanDefinitions.java → javac                │
   │                                                                      │
   ├─★ writeHints(generationContext.getRuntimeHints())              :110 ◄┘
   │        │                                 TestAotProcessor.java:92 도 동일
   │        ▼
   │   AbstractAotProcessor.writeHints(hints)      AbstractAotProcessor.java:124
   │        new FileNativeConfigurationWriter(resourceOutput, groupId, artifactId) :125
   │        writer.write(hints)                                          :127
   │             │
   │             ▼  ★ 이 문서의 무대 — 게이트 판정
   │        hasAnyHint(hints) ?
   │             ├ true  → resourceOutput/META-INF/native-image/<groupId>/
   │             │            <artifactId>/reachability-metadata.json
   │             └ false → 파일 없음  ← lambda 전용 힌트가 여기 빠졌다
   │
   └ writeNativeImageProperties(...)                ContextAotProcessor.java:111
          → 같은 디렉터리의 native-image.properties            :161~168
   │
   ▼
GraalVM native-image 컴파일
   META-INF/native-image/** 를 읽어 리플렉션·lambda·리소스 메타데이터 반영
   파일이 없으면 → 해당 lambda 가 이미지에서 재구성되지 않음
   → JVM 에서는 정상, 네이티브 런타임에서만 실패
```

grep으로 확인한 프로덕션 호출처는 정확히 한 곳이다.\
`NativeConfigurationWriter`/`FileNativeConfigurationWriter`를 쓰는 곳은 `AbstractAotProcessor.writeHints`(`AbstractAotProcessor.java:124~128`)뿐이고, 그것을 부르는 곳이 `ContextAotProcessor.performAotProcessing:110`과 `TestAotProcessor.performAotProcessing:92` 두 곳이다.\
`AbstractAotProcessor`의 javadoc이 `@see FileNativeConfigurationWriter`(`:45`)로 이 관계를 명시한다.

호출처가 좁다는 사실이 결함의 파장을 오히려 넓힌다.\
AOT 산출물의 네이티브 메타데이터가 전부 이 한 게이트를 지나므로, 게이트가 한 종류를 놓치면 그 종류만 빠지는 것이 아니라 — 다른 종류가 하나도 없는 경우 — 파일 자체가 빠진다.\
실전에서 `RuntimeHints`가 lambda 힌트만 담는 상황은 라이브러리나 모듈 단위 AOT 처리에서 충분히 발생한다.

`resourceOutput` 아래에 놓인다는 점도 짚어 둘 만하다.\
생성 소스가 javac를 거치는 것과 달리 이 JSON은 리소스로 그대로 실려 나가므로 컴파일 단계의 검증을 받지 않는다.\
파일이 없어도 빌드는 끝까지 초록색이다.

## 5. 관련 개념

### 5.1 GraalVM 닫힌 세계 가정과 reachability metadata

GraalVM `native-image`는 닫힌 세계 가정(closed-world assumption) 위에서 동작한다.\
빌드 시점에 도달 가능하다고 판단되지 않은 클래스와 멤버는 이미지에서 제거되므로, 리플렉션·프록시·리소스처럼 정적 분석이 볼 수 없는 접근은 별도 메타데이터로 알려야 한다.

> **닫힌 세계 가정(closed-world assumption)** — "빌드 시점에 보이는 것이 전부"라고 못 박고, 보이지 않은 것은 실행 파일에 넣지 않는 원칙.\
> 예: 문자열로만 이름이 등장하는 클래스는 정적 분석이 못 보므로 메타데이터로 따로 알려 주지 않으면 이미지에서 사라진다.

> **도달 가능성 메타데이터(reachability metadata)** — 정적 분석이 못 보는 접근을 빌드 도구에 알려 주는 설정 파일.\
> 예: `META-INF/native-image/…/reachability-metadata.json`이 그 파일이다.

Spring은 이 메타데이터를 자바 객체 모델로 모으는 API를 `org.springframework.aot.hint`에 두었고 그 최상위가 `RuntimeHints`(`RuntimeHints.java:34`)다.\
직렬화는 `org.springframework.aot.nativex`가 맡는다.\
두 패키지의 분리가 "수집"과 "출력"의 경계이며, 이 PR의 결함은 정확히 그 경계에 있는 게이트에서 났다.

최신 GraalVM에서는 여러 파일로 나뉘어 있던 설정이 `reachability-metadata.json` 하나로 통합되었고, `NativeConfigurationWriter.write`가 그 이름을 하드코딩한다(`:41`).

### 5.2 lambda 힌트가 왜 별도 종류인가

자바 lambda는 컴파일 시점에 이름 있는 클래스로 남지 않는다.\
바이트코드에는 `invokedynamic` 호출 지점만 남고, 실제 구현 클래스는 런타임에 `LambdaMetafactory`가 만들어 낸다.\
닫힌 세계 가정 아래에서는 이 생성 과정을 빌드 시점으로 당겨와야 하므로, "어느 클래스의 어느 메서드 안에서 어떤 함수형 인터페이스를 구현하는 lambda가 만들어지는가"를 별도 형식으로 기술해야 한다.

> **`invokedynamic`** — 어떤 메서드를 부를지 컴파일 때 정하지 않고 첫 호출 때 런타임에 정하도록 미뤄 두는 JVM 명령.\
> 예: lambda 식 자리에는 이 명령 하나만 남고, 실제 구현 클래스는 `LambdaMetafactory`가 그때 만든다.

`LambdaHint`가 담는 것이 정확히 그 세 가지다 — `declaringClass`(`LambdaHint.java:33`), `declaringMethod`(`:37`, 레코드 `DeclaringMethod(name, parameterTypes)` `:183`), `interfaces`(`:39`).\
여기에 조건부 등록용 `reachableType`(`:35`)이 더해진다.

타입 힌트와 형태가 다르기 때문에 저장소도 분리된다.\
`ReflectionHints`는 타입 힌트를 `Map<TypeReference, TypeHint.Builder>`(`ReflectionHints.java:48`)에, lambda 힌트를 `Set<LambdaHint>`(`:50`)에 따로 담는다.\
타입 힌트는 같은 타입에 대해 여러 번 등록하면 하나의 빌더로 병합되지만(`registerType:99`의 `computeIfAbsent`), lambda 힌트는 집합에 값으로 쌓인다(`registerLambda:268`).\
이 구조적 분리가 존재 검사도 두 번 해야 하는 이유이며, 수정 전에는 그중 한 번이 빠져 있었다.

이 지원은 7.0.6에 추가되었다.\
`lambdaHints()`(`:66`)와 두 `registerLambda` 오버로드(`:265`, `:279`)의 `@since 7.0.6` 태그가 그 시점을 기록한다.

### 5.3 목록 복제와 컴파일러가 지켜 주지 않는 확장 지점

`hasAnyHint`는 "힌트 종류의 열거"를 코드로 복제한 형태다.\
원본 열거는 `RuntimeHints`의 필드 목록(`:36~45`)과 각 하위 클래스의 컬렉션 목록에 흩어져 있고, 게이트는 그 목록을 손으로 옮겨 적었다.\
이런 복제는 두 가지 성질을 갖는다.

> **목록 복제(duplicated enumeration)** — 같은 "종류 목록"을 서로 다른 두 곳에 손으로 적어 두어, 한쪽만 고쳐도 컴파일이 되는 상태.\
> 예: 여기서는 직렬화 쪽 목록에 lambda가 들어갔는데 게이트 쪽 목록에는 들어가지 않았다.

첫째, 새 종류가 추가될 때 함께 갱신되어야만 정확하다.\
둘째, 갱신을 빠뜨려도 컴파일 오류가 나지 않는다.\
`findAny().isPresent()` 사슬은 항목이 몇 개든 문법적으로 완전하기 때문이다.\
gh-36339이 `LambdaHint`·`ReflectionHints`·`ReflectionHintsAttributes`를 확장하면서 `NativeConfigurationWriter`만 옛 목록에 남겨 둔 것이 이 성질의 직접적 결과다.

그 어긋남을 종류별로 펼치면 빠진 칸이 하나라는 것이 보인다.

```text
  힌트 종류                        직렬화 쪽이 아는가   게이트가 아는가(수정 전)
  ------------------------------  ------------------  ----------------------
  proxies().jdkProxyHints()              O                    O   :47
  reflection().typeHints()               O                    O   :48
  reflection().lambdaHints()             O                    X   <-- 빠진 칸
  resources().resourcePatternHints()     O                    O   :50
  resources().resourceBundleHints()      O                    O   :51
  jni().typeHints()                      O                    O   :52
  serialization().javaSerialization..    O                    O   :53 -> :58

  X 가 하나뿐인데, 그 하나만 가진 hints 는 파일이 통째로 안 생긴다.
```

근본 대안은 `RuntimeHints`에 "비어 있는가"를 스스로 답하는 API를 두어 복제를 없애는 것이다.\
그러면 종류가 늘어날 때 갱신 지점이 한 곳이 된다.\
다만 그것은 public API 확장이라 버그 수정의 범위를 넘고, 기존 계약(`emptyConfig` 테스트가 고정하는 "힌트가 없으면 파일도 없다")도 함께 검토해야 한다.\
이 PR이 한 줄로 닫은 것은 그 판단의 결과다.

일반화하면, 존재 검사 목록·switch 나열·문자열 상수 배열처럼 "종류를 손으로 세는 코드"는 확장 지점의 상습 사각지대다.\
새 종류를 추가할 때는 그것을 소비하는 코드뿐 아니라 종류를 열거하는 모든 지점을 함께 찾아야 한다.

### 5.4 단락 평가와 `findAny()`

`hasAnyHint`의 `||` 사슬은 자바의 단락 평가를 그대로 쓴다.\
앞쪽에서 참이 나오면 뒤쪽 스트림은 만들어지지도 않는다.\
그리고 각 항목의 `findAny()`는 요소 하나만 확인하고 종료하는 단축 연산이므로, 컬렉션 크기와 무관하게 비용이 상수다.

> **단축 연산(short-circuiting operation)** — 스트림 전체를 끝까지 돌지 않고 조건이 정해지는 순간 멈추는 연산.\
> 예: `findAny()`는 요소가 백만 개든 첫 하나를 보고 끝낸다.

그래서 lambda 검사를 목록의 어디에 넣든 성능 차이가 없다.\
`typeHints()` 바로 다음(`:49`)에 놓인 것은 같은 `hints.reflection()` 묶음에서 나오는 두 검사를 나란히 두어 읽을 때 종류별로 묶여 보이게 하려는 가독성 판단이다.

한 가지 남는 비대칭도 분기도에 표시해 두었다.\
`hints.jni()`는 `RuntimeHints:45`에서 보듯 `reflection`과 같은 `ReflectionHints` 타입의 별도 인스턴스이므로 `lambdaHints()`를 가질 수 있지만, 게이트는 `jni().typeHints()`만 검사한다(`:52`).\
다만 `RuntimeHintsWriter`의 `jni` 직렬화도 `ReflectionHintsAttributes.jni(hints)`(`:98~104`)에서 타입 힌트만 다루므로 두 쪽이 일치한다 — 이 경우는 게이트와 직렬화가 어긋나지 않는다.

> **JNI(Java Native Interface)** — 자바 코드와 C/C++ 같은 네이티브 코드가 서로를 부를 때 쓰는 규약.\
> 예: 네이티브 쪽에서 이름으로 찾아 쓰는 자바 클래스도 리플렉션처럼 별도 힌트로 알려야 한다.

### 5.5 자매 PR과의 관계

같은 스택을 무대로 하는 PR이 두 건 더 있다.\
[#36972](../36972-native-config-utf8/structure.md)는 이 게이트를 통과한 뒤 파일을 실제로 쓰는 층 — `FileNativeConfigurationWriter.writeTo`의 `FileWriter` charset — 을 다루며, `BasicJsonWriter`·`IndentingWriter`까지 내려가는 직렬화 스택 전체를 그 문서가 상세히 그린다.\
[#36965](../36965-valuecodegen-nonfinite-doubles/structure.md)는 같은 AOT 파이프라인의 다른 줄기, 즉 생성 Java 소스 쪽의 `ValueCodeGenerator`를 다룬다.\
4장의 파이프라인 그림에서 세 PR의 자리를 함께 확인할 수 있다.
