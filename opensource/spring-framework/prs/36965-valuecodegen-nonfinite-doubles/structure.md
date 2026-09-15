# PR #36965 — 무대 구조와 워크플로우

> PR #36965의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
> 기준: upstream main `526c706d1c3`. 이 PR은 아직 업스트림에 반영되지 않았으므로, 아래 file:line 인용은 그대로 "수정 전" 코드다.

이 문서가 다루는 것은 Spring AOT가 값 하나를 Java 소스 조각으로 번역하는 지점의 실구조다.\
진입점과 위임자 체인의 소유 관계에서 출발해, 수정 전 값이 소스 문자열이 되는 경로를 따라간다.\
그다음 분기도로 결함이 살던 자리를 짚고, 이 코드가 AOT 파이프라인 전체에서 차지하는 자리와 배경 개념을 정리한다.

> **AOT(ahead-of-time, 사전 처리)** — 애플리케이션을 실행하기 전 빌드 시점에 컨텍스트 조립을 Java 소스로 미리 써내는 Spring의 처리 방식.\
> 예: 빈이 들고 있던 프로퍼티 값 `0.2`가 빌드 중에 `(double) 0.2`라는 소스 텍스트로 옮겨 적힌다.

## 1. 무대 — 실구조

이 PR의 무대는 `spring-core`의 `org.springframework.aot.generate` 패키지에 있는 값 코드 생성기 삼각형이다.\
값 하나를 받아 그 값을 되살리는 Java 식으로 번역하는 진입점 `ValueCodeGenerator`, 타입별 번역 규칙을 담은 전략 인터페이스 `Delegate`, 그리고 그 구현들을 모아 둔 `ValueCodeGeneratorDelegates`가 전부다.\
PR이 실제로 건드리는 곳은 그중 맨 앞에 놓인 `PrimitiveDelegate` 한 클래스의 `generateCode` 메서드다.

> **위임자(Delegate)** — "이 값을 내가 처리할 수 있으면 결과를 내고, 못 하면 `null`을 돌려준다"는 계약을 가진 타입별 번역 규칙 하나.\
> 예: `PrimitiveDelegate`는 `Integer`·`Long`·`Float` 같은 박싱 원시 타입만 맡고, `List`가 오면 `null`을 돌려 다음 위임자에게 넘긴다.

> **박싱 원시 타입(boxed primitive)** — `int`·`double` 같은 원시 타입을 객체로 감싼 `Integer`·`Double` 등의 래퍼 타입.\
> 예: 빈 프로퍼티 값은 `Object`로 오가므로, 숫자 `0.2`는 여기에 `Double` 객체로 도착한다.

세 요소의 소유 관계와 핵심 필드는 다음과 같다.\
`ValueCodeGenerator`는 위임자 목록을 불변으로 들고, 자기 자신을 위임자에게 다시 넘겨 중첩 값을 재귀 처리한다.

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ ValueCodeGenerator (final)          ValueCodeGenerator.java:35            │
│                                                                           │
│  - delegates : List<Delegate>                                    :43      │
│  - generatedMethods : @Nullable GeneratedMethods                 :45      │
│  - INSTANCE : ValueCodeGenerator (static, 기본 위임자로 구성)     :37      │
│  - NULL_VALUE_CODE_BLOCK : CodeBlock = CodeBlock.of("null")      :40      │
│                                                                           │
│  + withDefaults() : ValueCodeGenerator                           :59      │
│  + with(Delegate...) / with(List<Delegate>)                      :68,77   │
│  + add(List<Delegate>) : ValueCodeGenerator     (뒤에 덧붙임)     :83      │
│  + scoped(GeneratedMethods) : ValueCodeGenerator                 :98      │
│  + generateCode(@Nullable Object) : CodeBlock   ★ 진입점          :107     │
└──────────────────────┬────────────────────────────────────────────────────┘
                       │ delegates (순서 있는 목록, 앞에서부터 시도)
                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ interface ValueCodeGenerator.Delegate            ValueCodeGenerator.java:140│
│   @Nullable CodeBlock generateCode(ValueCodeGenerator, Object)     :151   │
│   계약: 지원하지 않으면 null 반환 (예외 아님)                              │
└──────────────────────┬────────────────────────────────────────────────────┘
                       │ 기본 구현 10종 = INSTANCES
                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ ValueCodeGeneratorDelegates                ValueCodeGeneratorDelegates.java:48│
│  + INSTANCES : List<Delegate>                                     :68     │
│      [0] PrimitiveDelegate      ★ 이 PR의 무대                    :195    │
│      [1] StringDelegate                                           :249    │
│      [2] CharsetDelegate                                          :264    │
│      [3] EnumDelegate                                             :279    │
│      [4] ClassDelegate                                            :295    │
│      [5] ResolvableTypeDelegate                                   :310    │
│      [6] ArrayDelegate                                            :352    │
│      [7] ListDelegate      extends CollectionDelegate<List<?>>    :373    │
│      [8] SetDelegate       extends CollectionDelegate<Set<?>>     :384    │
│      [9] MapDelegate                                              :134    │
└───────────────────────────────────────────────────────────────────────────┘
```

버그가 살던 `PrimitiveDelegate`는 목록의 0번, 즉 어떤 값이든 가장 먼저 검사하는 자리에 있다.\
내부 상태는 문자 이스케이프 표 하나뿐이고 나머지는 전부 `generateCode` 안의 분기다.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ private static class PrimitiveDelegate implements Delegate      :195 │
│                                                                      │
│  - CHAR_ESCAPES : Map<Character,String>   (\b \t \n \f \r " ' \) :197 │
│                                                                      │
│  + generateCode(ValueCodeGenerator, Object) : @Nullable CodeBlock:210│
│      Boolean|Integer → CodeBlock.of("$L", value)                :211 │
│      Byte            → CodeBlock.of("(byte) $L", value)         :214 │
│      Short           → CodeBlock.of("(short) $L", value)        :217 │
│      Long            → CodeBlock.of("$LL", value)               :220 │
│      Float           → CodeBlock.of("$LF", value)         ← 버그 :223 │
│      Double          → CodeBlock.of("(double) $L", value) ← 버그 :226 │
│      Character       → CodeBlock.of("'$L'", escape(ch))         :229 │
│      그 외           → null (다음 위임자에게 양보)               :232 │
│                                                                      │
│  - escape(char) : String                                        :235 │
└──────────────────────────────────────────────────────────────────────┘
```

출력 타입인 `CodeBlock`은 Spring이 재패키징한 JavaPoet(`org.springframework.javapoet.CodeBlock`)의 타입으로, 소스 조각과 그 조각이 참조하는 타입 목록을 함께 들고 다니는 값 객체다.\
이 문서에서 반복해 나오는 `$L`과 `$T`가 그 포맷 플레이스홀더이며, 둘의 차이는 5장에서 다룬다.

> **`CodeBlock`** — 생성될 Java 소스의 한 조각을, 그 조각이 참조하는 타입 목록과 함께 들고 다니는 불변 값 객체.\
> 예: `CodeBlock.of("(double) $L", 0.2)`는 소스 텍스트 `(double) 0.2`를 담은 조각이 된다.

> **플레이스홀더(placeholder)** — 포맷 문자열 안에서 "여기에 인자를 끼워 넣어라"를 표시하는 자리표.\
> 예: `"$LF"`의 `$L`이 인자 `0.1`로 채워져 `0.1F`가 된다.

## 2. 수정 전 동작 워크플로우

대표 시나리오는 AOT 빌드가 빈 프로퍼티 값 하나를 소스 코드로 옮기는 흐름이다.\
아래는 `Double` 값 `0.2`가 `(double) 0.2`라는 문자열이 되기까지의 호출 경로다.

```text
generateValue("threshold", 0.2)            BeanDefinitionPropertiesCodeGenerator.java:310
   │  PropertyNamesStack.push("threshold")
   ▼
valueCodeGenerator.generateCode(0.2)       ValueCodeGenerator.java:107
   │
   ├─ value == null ?  ── 아니오
   │
   ▼ for (Delegate d : delegates)          ValueCodeGenerator.java:112
   │
   ├─[0] PrimitiveDelegate.generateCode(this, 0.2)   Delegates.java:210
   │        Boolean|Integer? 아니오 → Byte? 아니오 → Short? 아니오
   │        Long? 아니오 → Float? 아니오
   │        Double? 예 → CodeBlock.of("(double) $L", 0.2)      :226~227
   │                        └─ $L 은 인자를 가공 없이 리터럴로 인쇄
   │                           → "(double) 0.2"
   │
   ▼ code != null → 즉시 반환                ValueCodeGenerator.java:114~116
CodeBlock("(double) 0.2")
   │
   ▼
code.addStatement("$L.getPropertyValues().addPropertyValue($S, $L)",
                  "beanDefinition", "threshold", valueCode)
                                            BeanDefinitionPropertiesCodeGenerator.java:241~242
   │
   ▼ 생성 소스에 남는 문장
beanDefinition.getPropertyValues().addPropertyValue("threshold", (double) 0.2);
```

두 번째 시나리오는 중첩 값이다.\
`List.of(1.0F, 2.0F)` 같은 값이 오면 `ListDelegate`가 자기 안에서 다시 같은 생성기를 부른다.\
재귀가 위임자 목록을 다시 처음부터 훑기 때문에, 원소 하나하나가 `PrimitiveDelegate`를 거친다.

> **재귀(recursion)** — 어떤 함수가 처리 도중 자기 자신을 다시 부르는 것.\
> 예: `List.of(1.0F, 2.0F)`를 번역하던 생성기가 원소 `1.0F`를 번역하려고 자기 자신을 다시 부른다.

```text
generateCode(List.of(1.0F, 2.0F))            ValueCodeGenerator.java:107
   │
   ├─[0] PrimitiveDelegate → null (List 아님)         Delegates.java:232
   ├─[1..6] String/Charset/Enum/Class/ResolvableType/Array → null
   │
   └─[7] ListDelegate (CollectionDelegate)            Delegates.java:98
            │ collectionType.isInstance(value) → true
            │ collection.isEmpty()? 아니오
            ▼
         generateCollectionOf(gen, collection, List.class)   Delegates.java:113
            │  code.add("$T.of(", List.class)
            │
            ├─ 원소 1.0F → gen.generateCode(1.0F) ──┐  재귀
            │                                        └─ PrimitiveDelegate:223
            │                                             "$LF" → "1.0F"
            ├─ code.add(", ")
            ├─ 원소 2.0F → gen.generateCode(2.0F) ──── "2.0F"
            │
            ▼ code.add(")")
         CodeBlock("List.of(1.0F, 2.0F)")
```

이 재귀 구조가 파장의 크기를 결정한다.\
컬렉션·배열·맵 어디에 묻혀 있든 원시 값은 결국 `PrimitiveDelegate`를 통과하므로, 그 분기 하나의 결함이 값 구조 전체에 스며든다.

## 3. 분기 처리 워크플로우

`ValueCodeGenerator.generateCode`의 바깥 분기는 세 갈래다.\
null 상수, 위임자 성공, 전원 실패다.\
세 번째가 유일한 방어선인데 — 뒤에서 볼 결함은 이 방어선에 걸리지 않고 통과한다.

```text
generateCode(value)                                ValueCodeGenerator.java:107
   │
   ├── value == null ────────────────────► return NULL_VALUE_CODE_BLOCK  :108~110
   │                                        (= CodeBlock.of("null"))
   │
   └── try {                                                             :111
         for (delegate : delegates) {                                    :112
             code = delegate.generateCode(this, value)                   :113
             ├── code != null ──────────► return code    ★ 첫 성공에서 종료 :115
             └── code == null  ─────────► 다음 위임자로
         }
         ── 전원 null ──────────────────► throw UnsupportedTypeValue…    :118
       }
       catch (Exception ex) ─────────────► throw ValueCodeGenerationException(value, ex) :121
```

핵심은 "위임자가 null이 아닌 CodeBlock을 돌려준 순간 검증 없이 채택된다"는 점이다.\
반환된 조각이 유효한 Java 식인지 확인하는 단계는 없다.\
따라서 `UnsupportedTypeValueCodeGenerationException`은 "아무도 이 타입을 모른다"만 잡을 뿐, "안다고 했는데 잘못 썼다"는 잡지 못한다.

안쪽 분기, 즉 `PrimitiveDelegate.generateCode`의 타입 분기도는 다음과 같다.\
오른쪽에 각 분기가 만들어 내는 소스 형태를 붙였다.

```text
PrimitiveDelegate.generateCode(codeGenerator, value)        Delegates.java:210
   │
   ├─ value instanceof Boolean || Integer ──► "$L"           → true / 42      :211
   ├─ value instanceof Byte ───────────────► "(byte) $L"     → (byte) 5       :214
   ├─ value instanceof Short ──────────────► "(short) $L"    → (short) 5      :217
   ├─ value instanceof Long ───────────────► "$LL"           → 5L             :220
   │
   ├─ value instanceof Float ──────────────► "$LF"                            :223
   │     └─★ 버그가 살던 분기: value.toString()이 그대로 인쇄된다
   │          0.1F        → "0.1F"        (유효)
   │          Float.NaN   → "NaNF"        (컴파일 불가)
   │          +Infinity   → "InfinityF"   (컴파일 불가)
   │          -Infinity   → "-InfinityF"  (컴파일 불가)
   │
   ├─ value instanceof Double ─────────────► "(double) $L"                    :226
   │     └─★ 버그가 살던 분기: 같은 원인, 캐스트만 다름
   │          0.2          → "(double) 0.2"        (유효)
   │          Double.NaN   → "(double) NaN"        (컴파일 불가)
   │          +Infinity    → "(double) Infinity"   (컴파일 불가)
   │          -Infinity    → "(double) -Infinity"  (컴파일 불가)
   │
   ├─ value instanceof Character character ► "'$L'" + escape(ch)              :229
   │       └─ escape 내부 분기:                                     :235~242
   │            CHAR_ESCAPES에 있음 ──► 매핑값 (\b \t \n \f \r " ' \\)
   │            ISO 제어문자         ──► String.format("\\u%04x", ch)
   │            그 외               ──► 문자 그대로
   │
   └─ 그 외 ───────────────────────────────► return null (다음 위임자로)      :232
```

두 표시 분기의 공통점은 "`toString()` 결과가 언제나 유효한 Java 리터럴"이라는 암묵 가정에 서 있다는 것이다.\
`Byte`·`Short`·`Long`·`Integer`에서는 그 가정이 참이지만, `Float`·`Double`에서는 IEEE 754 비유한 값 세 종류에서 깨진다.\
값의 종류를 다시 나누는 안쪽 분기가 없기 때문에 결함이 조용히 통과한다.

> **비유한 값(non-finite value)** — 부동소수점이 표현하는, 유한한 수가 아닌 세 값 — NaN, 양의 무한대, 음의 무한대.\
> 예: `0.0 / 0.0`은 예외를 던지지 않고 `Double.NaN`이라는 값을 낸다.

이 가정을 분기마다 점검하면 어디서 깨지는지가 한 화면에 보인다.

```text
분기별 가정 점검 — "value.toString() 이 그대로 유효한 Java 리터럴인가"

타입        값            toString()     소스에 찍히는 것      유효?
---------  ------------  ------------   -------------------  ------
Boolean    true          "true"         true                 예
Integer    42            "42"           42                   예
Byte       5             "5"            (byte) 5             예
Short      5             "5"            (short) 5            예
Long       5             "5"            5L                   예
Float      0.1           "0.1"          0.1F                 예
Float      NaN           "NaN"          NaNF                 아니오
Float      +Infinity     "Infinity"     InfinityF            아니오
Float      -Infinity     "-Infinity"    -InfinityF           아니오
Double     0.2           "0.2"          (double) 0.2         예
Double     NaN           "NaN"          (double) NaN         아니오
Double     +Infinity     "Infinity"     (double) Infinity    아니오
Double     -Infinity     "-Infinity"    (double) -Infinity   아니오
Character  제어문자       -              escape() 를 거친 값   예  <- 검사가 있다
                                                                  :229,:235
```

맨 아랫줄이 대조군이다.\
같은 클래스의 `Character` 분기는 `toString()`을 그대로 믿지 않고 `escape(char)`를 한 번 거치는데, 부동소수점 두 분기에만 그 한 겹이 없다.

## 4. 스프링 전역에서의 자리

`ValueCodeGenerator`는 Spring AOT 처리 파이프라인의 마지막 잎사귀 노드다.\
빌드 타임에 애플리케이션 컨텍스트를 Java 소스로 다시 써내는 과정에서, 빈 정의가 들고 있던 값 하나하나가 반드시 이곳을 지난다.

전체 파이프라인은 두 갈래 산출물을 낸다.\
하나는 생성 Java 소스(이 PR의 무대), 다른 하나는 네이티브 이미지 설정 JSON(자매 PR #36972·#36989의 무대)이다.\
아래 그림에서 왼쪽 줄기가 이 문서의 관심사다.

```text
빌드 타임 (Gradle/Maven AOT 플러그인이 기동)
   │
   ▼
ContextAotProcessor.process() → doProcess()          ContextAotProcessor.java:81
   │   deleteExistingOutput()
   │   prepareApplicationContext(applicationClass)    (refresh 하지 않은 컨텍스트)
   ▼
performAotProcessing(applicationContext)             ContextAotProcessor.java:102
   │
   ├─ ApplicationContextAotGenerator.processAheadOfTime(ctx, generationContext)
   │                                    ApplicationContextAotGenerator.java:51
   │      │
   │      ▼  빈마다 등록 코드 생성
   │   BeanRegistrationCodeGenerator.generateCode(generationContext)
   │                                    BeanRegistrationCodeGenerator.java:78
   │      │
   │      ▼  codeFragments.generateSetBeanDefinitionPropertiesCode(...)
   │                                    BeanRegistrationCodeGenerator.java:82
   │      ▼
   │   DefaultBeanRegistrationCodeFragments
   │        .generateSetBeanDefinitionPropertiesCode(...)
   │                            DefaultBeanRegistrationCodeFragments.java:166
   │      │   new BeanDefinitionPropertiesCodeGenerator(...)             :173
   │      ▼
   │   BeanDefinitionPropertiesCodeGenerator.generateCode(rootBeanDefinition)
   │                            BeanDefinitionPropertiesCodeGenerator.java:116
   │      ├─ addConstructorArgumentValues(...)                           :198
   │      ├─ addPropertyValues(...)                                      :234
   │      └─ addQualifiers(...)                                          :264
   │            │  세 곳 모두 generateValue(name, value) 경유            :310
   │            ▼
   │   ★ ValueCodeGenerator.generateCode(value)   ValueCodeGenerator.java:107
   │            │
   │            └─ PrimitiveDelegate ← 이 PR이 고치는 지점
   │
   ├─ generationContext.writeGeneratedContent()      ContextAotProcessor.java:109
   │      → *__BeanDefinitions.java 등을 sourceOutput 에 기록 → javac
   │
   ├─ writeHints(generationContext.getRuntimeHints())ContextAotProcessor.java:110
   │      → AbstractAotProcessor.writeHints         AbstractAotProcessor.java:124
   │      → FileNativeConfigurationWriter → reachability-metadata.json
   │        (PR #36972 / #36989 의 무대 — 이 PR과는 자매 경로)
   │
   └─ writeNativeImageProperties(...)                ContextAotProcessor.java:111
          → META-INF/native-image/<groupId>/<artifactId>/native-image.properties
```

grep으로 확인한 실제 진입점은 네 부류다.

첫째, 빈 정의 경로.\
`BeanDefinitionPropertiesCodeGenerator:98`이 인스턴스 필드로 생성기를 들고, `generateValue`(`:310`)를 통해 생성자 인자(`:198`)·프로퍼티(`:234`)·qualifier(`:264`) 세 곳에서 부른다.\
사용하는 위임자 목록은 기본 목록이 아니라 `BeanDefinitionPropertyValueCodeGeneratorDelegates.createValueCodeGenerator(generatedMethods, customDelegates)`(`BeanDefinitionPropertyValueCodeGeneratorDelegates.java:90~96`)가 만든 확장 목록이다.\
조립 순서는 커스텀 위임자가 먼저, 그다음 빈 정의 전용 위임자(`INSTANCES`, `:69`), 마지막이 코어 위임자(`ValueCodeGeneratorDelegates.INSTANCES`, `:95`)이며, 마지막에 `ValueCodeGenerator.with(allDelegates).scoped(generatedMethods)`(`:96`)로 감싼다.\
따라서 `PrimitiveDelegate`는 이 목록에서 0번이 아니라 코어 블록의 첫 자리로 밀리지만, 앞선 위임자들(`ManagedList`·`BeanReference`·`TypedStringValue` 등 빈 정의 고유 타입)이 박싱 원시 타입을 매칭하지 않으므로 실제로 원시 값을 받아 처리하는 것은 여전히 `PrimitiveDelegate`다.

둘째, 빈 타입 경로.\
`DefaultBeanRegistrationCodeFragments:57`이 `ValueCodeGenerator.withDefaults()`를 정적 필드로 두고, `generateBeanTypeCode`(`:148~153`)에서 `Class`와 `ResolvableType`을 소스로 옮긴다.

셋째, 모듈이 기여하는 커스텀 위임자.\
`spring-web`의 `GroupsMetadataValueDelegate`(`GroupsMetadataValueDelegate.java:40`)가 `ValueCodeGenerator.Delegate`를 구현해 HTTP 서비스 그룹 메타데이터를 소스로 옮긴다.\
이는 "위임자 목록은 모듈이 확장한다"는 설계가 실제로 쓰이는 증거다.

넷째, 테스트 컨텍스트 경로.\
`TestAotProcessor.performAotProcessing`(`TestAotProcessor.java:87~93`)이 같은 `AbstractAotProcessor` 기반 위에서 테스트 컨텍스트를 AOT 처리한다.\
소스 생성 줄기는 `TestContextAotGenerator`를 거치지만 값 번역은 같은 생성기로 수렴한다.

정리하면 이 코드의 자리는 빌드 타임 코드 생성에서 javac로 이어지는 파이프라인의 가장 안쪽이며, 여기서 잘못된 문자열이 나오면 실패는 코드 생성이 아니라 그 다음 컴파일 단계에서 사용자가 쓰지 않은 파일의 오류로 나타난다.

그 어긋남을 시간 축에 놓으면 이렇다.

```text
잘못된 문자열이 만들어지는 자리와 그것이 드러나는 자리

ValueCodeGenerator.generateCode(Double.POSITIVE_INFINITY)   ValueCodeGenerator.java:107
        |
        v
PrimitiveDelegate  Double 분기 "(double) $L"                Delegates.java:226
        |
        v
CodeBlock("(double) Infinity")            <- 예외 없음. 여기까지는 성공으로 보인다
        |
        v
generationContext.writeGeneratedContent() ContextAotProcessor.java:109
        |
        v
*__BeanDefinitions.java 에 기록            <- 사용자가 작성하지 않은 파일
        |
        v
javac                                     <- 실패가 처음 보이는 자리
```

만들어진 자리와 드러나는 자리 사이에 파일 기록 단계가 하나 끼어 있다는 것이 이 결함을 다루기 어렵게 만드는 지점이다.

## 5. 관련 개념

### 5.1 JavaPoet의 `$L`과 `$T`

`CodeBlock.of(format, args...)`의 포맷 문자열은 JavaPoet 규약을 따른다.\
이 무대에서 중요한 것은 두 개다.

> **JavaPoet** — Java 소스 코드를 문자열 조립 대신 API로 만들어 내기 위한 라이브러리.\
> 예: Spring은 이것을 `org.springframework.javapoet`로 재패키징해 AOT 생성 소스를 만든다.

`$L`은 리터럴(literal) 플레이스홀더다.\
인자를 아무 가공 없이 문자열로 붙여 넣는다.\
숫자 객체를 넘기면 그 `toString()` 결과가 그대로 소스 텍스트가 된다.\
그래서 `"$LL"`은 `Long` 값 `5`를 `5L`로, `"$LF"`는 `Float` 값 `0.1`을 `0.1F`로 만든다.\
가공이 없다는 성질이 정확히 이 PR이 다루는 결함의 통로다.

`$T`는 타입(type) 플레이스홀더다.\
인자를 `Class`나 `TypeName`으로 다루어 이름을 인쇄하면서, 동시에 생성 중인 파일의 import 목록을 관리한다.\
같은 단순 이름의 타입이 이미 그 파일에 있으면 정규화 이름으로 낮춰 쓴다.\
같은 파일 안에서 `EnumDelegate`(`Delegates.java:284`)가 `"$T.$L"`로 열거 상수를, `ClassDelegate`(`:300`)가 `"$T.class"`로 클래스 리터럴을, `CharsetDelegate`(`:269`)가 `"$T.forName($S)"`로 정적 팩토리 호출을 만든다.\
즉 "값을 이름 있는 상수로 가리키는" 표현 수단은 이 무대에 이미 존재했고, 원시 타입 분기만 그것을 쓰지 않고 있었다.

> **정규화 이름(fully qualified name)** — 패키지까지 전부 붙인 타입의 전체 이름.\
> 예: 단순 이름 `Float`의 정규화 이름은 `java.lang.Float`다.

두 플레이스홀더가 같은 파일 안에서 각각 무엇을 만들어 내는지 나란히 놓으면 이렇다.

```text
 $L — 가공 없이 인쇄                   $T — 타입으로 다뤄 인쇄
 +------------------------------+     +----------------------------------+
 | "$L"           -> true       |     | EnumDelegate    "$T.$L"    :284  |
 | "$L"           -> 42         |     |    -> 열거 상수를 가리킨다        |
 | "$LL"    (5)   -> 5L         |     | ClassDelegate   "$T.class" :300  |
 | "$LF"    (0.1) -> 0.1F       |     |    -> 클래스 리터럴              |
 | "(double) $L"  -> (double) 0.2|    | CharsetDelegate                  |
 |                              |     |    "$T.forName($S)"        :269  |
 | 인자의 toString() 이 곧 소스  |     |    -> 정적 팩토리 호출            |
 |                              |     | 이름을 인쇄하며 import 도 관리    |
 +------------------------------+     +----------------------------------+
   원시 타입 분기가 쓰는 쪽              "이름 있는 상수로 가리키기" 가
   = 결함의 통로                         이미 있던 쪽
```

`$S`도 곁가지로 등장한다.\
문자열(string) 플레이스홀더로, 인자를 따옴표로 감싸고 이스케이프까지 처리한다.\
`StringDelegate`(`:254`)가 이것 하나로 끝나는 이유다.

### 5.2 Delegate 체인은 왜 "null을 돌려주는" 계약인가

`Delegate.generateCode`는 지원하지 않는 값에 대해 예외가 아니라 `null`을 돌려주도록 규정되어 있다(`ValueCodeGenerator.java:142~151`).\
이 계약 덕분에 `ValueCodeGenerator`는 "첫 성공을 채택하고 나머지는 무시"라는 단순한 루프 하나로 임의 개수의 위임자를 조합할 수 있고, 모듈이 `add(List<Delegate>)`(`:83`)로 목록 뒤에 자기 규칙을 덧붙일 수 있다.

대가는 순서 의존성이다.\
목록은 앞에서부터 시도되므로, 넓게 매칭하는 위임자가 앞에 있으면 뒤의 좁은 위임자는 영영 불리지 않는다.\
`PrimitiveDelegate`가 0번인 것은 박싱 원시 타입이 가장 좁고 흔한 경우라 안전하기 때문이다.\
그리고 이 구조에는 "채택된 결과가 옳은가"를 묻는 단계가 없다.\
검증은 오직 "아무도 처리하지 못했는가"(`:118`)뿐이다.

### 5.3 IEEE 754 비유한 값과 Java 리터럴 문법의 간극

`float`와 `double`은 IEEE 754 이진 부동소수점이며, 유한한 수 외에 NaN(not-a-number)과 양·음의 무한대를 값으로 가진다.\
산술이 정의역을 벗어날 때 예외 대신 이 값들이 나온다.\
그런데 Java 언어 명세에는 이 셋을 직접 쓰는 리터럴 문법이 없다.\
소스에서는 `Float.NaN`·`Double.POSITIVE_INFINITY`처럼 JDK가 제공하는 `public static final` 상수 필드를 이름으로 참조해야 한다.

> **리터럴(literal)** — 소스 코드에 값을 직접 적어 넣는 표기법.\
> 예: `42`·`0.1F`·`'a'`는 리터럴이지만, `Float.NaN`은 리터럴이 아니라 상수 필드를 이름으로 참조하는 식이다.

한편 `Float.toString`·`Double.toString`은 이 값들에 대해 `"NaN"`, `"Infinity"`, `"-Infinity"`라는 단어를 돌려준다.\
이 문자열은 사람이 읽기 위한 표현이지 소스 리터럴이 아니다.\
즉 "toString 결과 = 유효한 리터럴"이라는 가정이 정확히 이 세 값에서만 깨진다.

```text
값                        toString()      소스에 쓰는 법
-----------------------  -------------   -----------------------------
0.1f  (유한)              "0.1"           0.1F                  리터럴 문법 있음
Float.NaN                "NaN"           Float.NaN             상수 필드 참조뿐
Float.POSITIVE_INFINITY  "Infinity"      Float.POSITIVE_INFINITY   같음
Float.NEGATIVE_INFINITY  "-Infinity"     Float.NEGATIVE_INFINITY   같음
                              |
                              v
                 사람이 읽는 표현이지 리터럴이 아니다
                 -> 그대로 소스에 찍으면 컴파일되지 않는다
```

부수적으로 NaN의 비교 규칙도 이 무대에서 의미가 있다.\
IEEE 754에서 NaN은 자기 자신과도 같지 않으므로 `Float.NaN == Float.NaN`은 `false`다.\
따라서 NaN을 판별하려면 `Float.isNaN(x)`를 써야 하고, 무한대는 통상적인 `==` 비교로 판별할 수 있다.\
두 판별 방식이 섞이는 것은 이 명세의 직접적 귀결이다.

### 5.4 AOT 처리와 GraalVM 닫힌 세계 가정

Spring AOT가 컨텍스트를 소스로 다시 써내는 이유는 GraalVM `native-image`의 닫힌 세계 가정(closed-world assumption) 때문이다.\
네이티브 이미지는 빌드 시점에 도달 가능하다고 판단된 코드만 포함하므로, 런타임 리플렉션으로 빈을 조립하는 방식은 정적 분석이 추적하지 못한다.\
그래서 AOT 처리는 컨텍스트 조립을 "빌드 타임에 실행할 수 있는 평범한 Java 코드"로 낮춘다.

> **닫힌 세계 가정(closed-world assumption)** — 빌드 시점에 도달 가능하다고 판정된 코드만 최종 실행 파일에 넣는다는 전제.\
> 예: 런타임에만 이름으로 찾아 쓰는 클래스는 그 판정에 걸리지 않아 이미지에서 빠진다.

이 관점에서 `ValueCodeGenerator`의 역할이 분명해진다.\
리플렉션으로 세팅되던 프로퍼티 값이 생성 소스의 평범한 메서드 인자가 되어야 하고, 그러려면 모든 값이 소스 텍스트로 표현 가능해야 한다.\
표현할 수 없는 값을 만나면 그것은 코드 생성기의 표현력 한계이며, 이 PR이 메우는 것이 그 한계 중 하나다.

관련 개념 문서로 [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)가 컴파일 타임과 런타임의 층 구분을 다룬다.\
이 무대는 그 층 구분이 물리적으로 드러나는 곳이다 — 실행 중인 JVM의 값(런타임)이 다음 빌드 단계의 소스 텍스트(컴파일 타임 입력)로 옮겨 적히는 지점이기 때문이다.
