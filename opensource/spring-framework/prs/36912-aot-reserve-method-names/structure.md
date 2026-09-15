# PR #36912 — 무대 구조와 수정 전 워크플로우

> PR #36912의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 PR은 OPEN이므로 아래 `GeneratedClass.java` 인용은
> **수정 전 코드 그대로**다.

## 1. 무대 — 실구조

이 PR의 무대는 AOT 코드 생성기가 "생성될 메서드의 이름"을 발급하는 작은 상태 기계다.\
중심은 `GeneratedClass`가 들고 있는 카운터 맵 하나와, 그 맵을 읽고 쓰는 함수 하나다 (`spring-core/src/main/java/org/springframework/aot/generate/GeneratedClass.java:51`, `:90`).

아래는 AOT 생성 객체들의 소유 관계다.\
화살표는 "가지고 있다" 또는 "만든다"를 뜻한다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ GeneratedClasses                        GeneratedClasses.java:43         │
│   classNameGenerator : ClassNameGenerator                 :45            │
│   classes            : List<GeneratedClass>               :47            │
│   classesByOwner     : Map<Owner, GeneratedClass>         :49            │
│   addForFeature(featureName, type)                        :141           │
│   getOrAddForFeature(featureName, type)                   :79            │
│   writeTo(GeneratedFiles)                                 :194           │
└───────────────────────────┬──────────────────────────────────────────────┘
                            │ createAndAddGeneratedClass :180
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GeneratedClass  (final)                 GeneratedClass.java:39           │
│──────────────────────────────────────────────────────────────────────────│
│  enclosingClass : @Nullable GeneratedClass                :41            │
│  name           : ClassName                               :43            │
│  methods        : GeneratedMethods                        :45            │
│  type           : Consumer<TypeSpec.Builder>              :47            │
│  declaredClasses: Map<ClassName, GeneratedClass>          :49            │
│  methodNameSequenceGenerator                                             │
│                 : Map<MethodName, AtomicInteger>          :51  ◄── 상태 본체 │
│──────────────────────────────────────────────────────────────────────────│
│  reserveMethodNames(String...)                            :82  ◄── 버그 자리 │
│  generateSequencedMethodName(MethodName)  private         :90  ◄── 발급 함수 │
│  getOrAdd(name, type)                                     :129           │
│  generateJavaFile()                                       :135           │
└───────────┬──────────────────────────────────────────────────────────────┘
            │ 생성자에서 메서드 참조를 넘긴다 :70
            │   new GeneratedMethods(name, this::generateSequencedMethodName)
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GeneratedMethods                        GeneratedMethods.java:38         │
│   className           : ClassName                          :40           │
│   methodNameGenerator : Function<MethodName, String>       :42  ◄── 위 참조 │
│   prefix              : MethodName                         :44           │
│   generatedMethods    : List<GeneratedMethod>              :46           │
│   add(suggestedName, method)                               :87           │
│   add(String[] suggestedNameParts, method)                 :108          │
│   withPrefix(prefix)                                       :124          │
└───────────┬──────────────────────────────────────────────────────────────┘
            │ new GeneratedMethod(className, generatedName, method) :112
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GeneratedMethod (final)                 GeneratedMethod.java:33          │
│   className, name, methodSpec                                            │
│   생성자에서 Assert.state(name.equals(methodSpec.name()))                │
└──────────────────────────────────────────────────────────────────────────┘

        값 객체 ─────────────────────────────────────────────────────────
┌──────────────────────────────────────────────────────────────────────────┐
│ MethodName (final, package-private)     MethodName.java:33               │
│   PREFIXES = { "get", "set", "is" }                        :35           │
│   NONE = of()                                              :40           │
│   value : String                                           :42           │
│   static of(String... parts)  → new MethodName(join(parts)):56  ◄── 오타의 표적│
│   and(String... parts)                                     :76           │
│   join(String[])  camel-case 합성                          :110          │
│   equals / hashCode  (value 기준)                          :95 / :100    │
└──────────────────────────────────────────────────────────────────────────┘
```

> **패키지 프라이빗(package-private)** — 접근 제어자를 붙이지 않아 같은 패키지 안에서만 보이는 클래스·멤버. 외부 코드의 API 표면이 아니다.\
> 예: `MethodName`은 `org.springframework.aot.generate` 패키지 밖에서는 아예 보이지 않는다.

핵심은 두 가지다.\
첫째, `methodNameSequenceGenerator`의 키가 `MethodName`이고 `MethodName`의 동일성은 **합성된 문자열 값** 하나로 정해진다(`MethodName.java:95-102`).\
둘째, 이름을 발급하는 함수가 조회가 아니라 **소비**다.

```java
// GeneratedClass.java:90-94
private String generateSequencedMethodName(MethodName name) {
    int sequence = this.methodNameSequenceGenerator
            .computeIfAbsent(name, key -> new AtomicInteger()).getAndIncrement();
    return (sequence > 0 ? name.toString() + sequence : name.toString());
}
```

`getAndIncrement()`가 부작용이다.\
부르는 순간 그 이름의 카운터가 하나 올라가므로, 같은 이름에 대한 다음 호출은 `apply1`을 받는다.\
"예약"이라는 개념은 별도 자료구조 없이 **이 부작용을 한 번 미리 소비하는 것**으로만 구현돼 있다.

> **부작용(side effect)** — 함수가 값을 돌려주는 것 말고도 바깥 상태를 바꾸는 일. 같은 함수를 두 번 부르면 결과가 달라진다.\
> 예: `generateSequencedMethodName("apply")`는 첫 호출에 `apply`, 두 번째 호출에 `apply1`을 돌려준다 — 카운터를 올리기 때문이다.

그리고 `MethodName.of`는 varargs 조각들을 하나의 camel-case 이름으로 **합친다**.

```java
// MethodName.java:110-113
private static String join(String[] parts) {
    return StringUtils.uncapitalize(Arrays.stream(parts).map(MethodName::clean)
            .map(StringUtils::capitalize).collect(Collectors.joining()));
}
```

> **camel-case 합성** — 조각마다 첫 글자를 대문자로 올려 이어 붙인 뒤, 전체의 첫 글자만 다시 소문자로 내리는 이름 만들기 규칙.\
> 예: `["apply","test"]` -> `"Apply" + "Test"` -> `applyTest`.

여러 조각을 넘기면 여러 이름이 아니라 하나의 이름이 나온다.\
이 성질과 위 부작용이 만나는 자리가 `reserveMethodNames`다.

## 2. 수정 전 동작 워크플로우

BLUF: 예약은 "발급을 한 번 헛되이 소비해 다음 발급이 번호를 달게 만드는" 절차이고, 수정 전 코드는 그 소비를 **잘못된 이름**으로 해서 예약을 놓쳤다.

> **BLUF(Bottom Line Up Front)** — 결론을 맨 앞에 한 줄로 먼저 적는 서술 방식. 뒤따르는 내용은 그 결론의 근거다.\
> 예: 이 절의 첫 줄이 "예약은 소비이고, 소비를 잘못된 이름으로 했다"는 결론을 먼저 말한다.

먼저 정상적으로 굴러가는 in-tree 시나리오(이름 하나 예약)다.\
AOT 처리는 애플리케이션 컨텍스트를 빌드 시점에 자바 소스로 써 내는데, 그 진입 클래스가 `ApplicationContextInitializer`를 구현하므로 `initialize`라는 손코드 메서드 이름을 미리 잡아 둔다.

```text
ApplicationContextAotGenerator.processAheadOfTime(ctx, generationContext)
        ApplicationContextAotGenerator.java:51
        │
        ├─ applicationContext.refreshForAotProcessing(hints)
        │
        ▼
new ApplicationContextInitializationCodeGenerator(ctx, generationContext)
        ApplicationContextInitializationCodeGenerator.java:71
        │
        ├─ generationContext.getGeneratedClasses()
        │       .addForFeature("ApplicationContextInitializer", this::generateType)   :73
        │       └─▶ GeneratedClasses.createAndAddGeneratedClass  GeneratedClasses.java:180
        │             └─▶ new GeneratedClass(className, type)    GeneratedClass.java:61
        │                   methodNameSequenceGenerator = {}     (빈 맵)
        │
        ▼
generatedClass.reserveMethodNames("initialize")                                       :75
        │
        ▼
GeneratedClass.reserveMethodNames(String... reservedMethodNames)   GeneratedClass.java:82
        │  루프 1회전: reservedMethodName = "initialize"
        │
        ├─ MethodName.of(reservedMethodNames)   ← 배열 전체를 넘긴다 (버그)
        │     원소 1개짜리 배열이므로 join → "initialize"   ← 우연히 같은 값
        │
        ├─ generateSequencedMethodName(MethodName("initialize"))                      :90
        │     카운터 0 → 1로 증가, "initialize" 반환
        │
        └─ Assert.state("initialize".equals("initialize")) → 통과                     :85
        │
        ▼
   맵 상태: { initialize → 1 }

  …이후 BeanFactoryInitializationAotContributions.applyTo 가 기여자들을 돌며
      codeGenerator.getMethods().add("initialize", ...) 를 호출하면

GeneratedMethods.add(suggestedName, method)              GeneratedMethods.java:87
        └─▶ add(new String[]{suggestedName}, method)                          :108
              └─ this.prefix.and(suggestedNameParts)      MethodName.java:76
              └─ methodNameGenerator.apply(name)          → generateSequencedMethodName
                    카운터 1 → 2, 반환 "initialize1"      ← 충돌 회피 성공
```

문제가 드러나는 시나리오는 이름을 둘 이상 넘기는 경우다.\
in-tree 호출처가 없어 한 번도 실행된 적 없는 경로다.

```text
generatedClass.reserveMethodNames("apply", "test")
        │
        ▼
for (String reservedMethodName : reservedMethodNames)          GeneratedClass.java:83
        │
        │  ── 1회전: reservedMethodName = "apply" ──────────────────────────────
        │
        ├─ MethodName.of(reservedMethodNames)                              :84
        │     join(["apply","test"])
        │       = uncapitalize( capitalize("apply") + capitalize("test") )
        │       = uncapitalize("ApplyTest")
        │       = "applyTest"                       ← 제3의 이름
        │
        ├─ generateSequencedMethodName(MethodName("applyTest"))            :90
        │     맵에 없음 → 카운터 생성, 0 → 1
        │     sequence == 0 이므로 "applyTest" 반환
        │
        └─ Assert.state("applyTest".equals("apply"))                       :85
              → false
              → IllegalStateException("Unable to reserve method name 'apply'")
        │
        ▼
   루프가 1회전에서 종료. 2회전("test")은 실행조차 되지 않는다.
   맵 상태: { applyTest → 1 }     ← 아무도 쓰지 않을 항목 하나만 남음
   "apply", "test" 는 예약되지 않았다.
```

수정 후에는 `MethodName.of(reservedMethodName)`(단수)이 되어 회전마다 자기 이름으로 카운터를 소비하고, 맵 상태가 `{ apply -> 1, test -> 1 }`이 된다.\
같은 호출이 남기는 맵 상태를 나란히 놓으면 이렇다.

```text
수정 전 map 상태                          수정 후 map 상태
+------------------------------+         +------------------------------+
| { applyTest -> 1 }           |         | { apply -> 1, test -> 1 }    |
| apply   : 키 없음 (seq 0)    |         | apply   : seq 1              |
| test    : 키 없음 (seq 0)    |         | test    : seq 1              |
+------------------------------+         +------------------------------+
  -> add("apply") 는 "apply" 를 받는다      -> add("apply") 는 "apply1" 을 받는다
```

## 3. 분기 처리 워크플로우

BLUF: 이 코드에는 조건 분기가 셋뿐이다 — 발급 함수의 시퀀스 판정, 예약의 검증문, 그리고 이름 합성 시 접두사 처리.\
결함은 분기 자체가 아니라 **분기에 들어가는 값**에 있었으므로, 분기도는 "어떤 값이 어느 갈래로 흘러가는가"를 보는 용도다.

```text
reserveMethodNames(String... names)                       GeneratedClass.java:82
   │
   ├─ names.length == 0 ? ──▶ 루프 0회전, 아무 일도 없음 (예외 없음)
   │
   ▼
  for each name in names
   │
   ├─ [수정 전] MethodName.of(names)        ← 루프 변수와 무관한 고정값
   │     │
   │     ├─ names.length == 1 ? ─▶ join 결과 == 그 원소 ─▶ 검증 통과 (우연)  [증상 없음]
   │     │
   │     └─ names.length >= 2 ? ─▶ join 결과 == 합쳐진 제3의 이름              [BUG]
   │                                 └─▶ 검증 실패 → IllegalStateException
   │
   └─ [수정 후] MethodName.of(name)         ← 회전마다 달라지는 값
         │
         ▼
      generateSequencedMethodName(methodName)                              :90
         │
         ├─ 맵에 키 없음 ─▶ computeIfAbsent 로 AtomicInteger(0) 생성
         │                    getAndIncrement → sequence = 0
         │                    sequence > 0 ? NO ─▶ 이름 그대로 반환
         │                    └─▶ Assert.state 통과 ─▶ 예약 성공
         │
         └─ 맵에 키 있음 ─▶ getAndIncrement → sequence >= 1
                              sequence > 0 ? YES ─▶ 이름 + 숫자 반환 ("apply1")
                              └─▶ Assert.state("apply1".equals("apply")) → false
                                    └─▶ IllegalStateException
                                          "Unable to reserve method name 'apply'"
                                          ← 기존 테스트
                                            reserveMethodNamesWhenNameUsedThrowsException
                                            이 고정하는 정상 동작
```

여기서 주의할 점은 **같은 예외가 두 가지 다른 사유로 난다**는 것이다.\
수정 전 다중 이름 경로의 예외는 "이름이 이미 사용됐다"가 아니라 "합성 결과가 요청과 다르다"인데, 메시지가 같아 구분되지 않는다.\
검증문이 상태 충돌과 인자 오류를 한 갈래로 모아 버린 셈이다.

이름 합성 쪽 분기도 함께 둔다.\
`GeneratedMethods.add`가 프리픽스를 붙일 때 타는 경로다.

```text
MethodName.and(String... parts)                              MethodName.java:76
   │
   ├─ joined = join(parts)
   │
   ▼
  getPrefix(joined)                                                        :84
   │
   ├─ joined 가 "get"/"set"/"is" 로 시작 ? ─▶ YES ─▶ prefix = 그 접두사
   │                                                  suffix = 나머지
   │                                                  결과 = of(prefix, this.value, suffix)
   │                                                    예: prefix="myBean", parts=["getInstance"]
   │                                                        → "getMyBeanInstance"
   │
   └─ NO ─▶ prefix = ""
              결과 = of("", this.value, joined)
                예: prefix="myBean", parts=["instance"] → "myBeanInstance"
```

이 분기가 `MethodName.of`의 varargs 합성 성질을 정상적으로 활용하는 자리다.\
즉 `MethodName.of(String...)`가 여러 조각을 합치는 것 자체는 설계 의도이고, 결함은 그 API를 "여러 이름을 각각 처리하는" 루프 안에서 쓴 데 있다.

## 4. 스프링 전역에서의 자리

BLUF: 이 코드는 **AOT 빌드 시점**에만 실행된다.\
런타임 요청 경로에는 없고, `mvn`/`gradle`의 AOT 처리 태스크가 애플리케이션 컨텍스트를 소스 코드로 써 내는 동안 한 번 돌아간다.

실제 호출처는 grep으로 확인하면 프로덕션 코드에 단 하나다.

```text
$ grep -rn "reserveMethodNames" --include=*.java . | grep -v /test/

spring-context/…/context/aot/ApplicationContextInitializationCodeGenerator.java:75
spring-core/…/aot/generate/GeneratedClass.java:82        (선언 자체)
```

그 하나로 이어지는 진입 사슬은 다음과 같다.

```text
빌드 도구의 AOT 태스크 (Spring Boot AOT plugin 등)
        │
        ▼
ContextAotProcessor.doProcess()                          ContextAotProcessor.java:81
        │  deleteExistingOutput()
        │  prepareApplicationContext(applicationClass)     (추상 — 부트가 구현)
        ▼
ContextAotProcessor.performAotProcessing(applicationContext)              :102
        │  new DefaultGenerationContext(createClassNameGenerator(), generatedFiles)
        ▼
ApplicationContextAotGenerator.processAheadOfTime(ctx, generationContext)
        ApplicationContextAotGenerator.java:51
        │
        ├─ ctx.refreshForAotProcessing(hints)
        │
        ├─▶ new ApplicationContextInitializationCodeGenerator(ctx, generationContext)   :57
        │        └─ generatedClasses.addForFeature("ApplicationContextInitializer", …)
        │             ApplicationContextInitializationCodeGenerator.java:73
        │        └─ generatedClass.reserveMethodNames(INITIALIZE_METHOD)               :75
        │             ★ 이 PR의 무대 — "initialize" 하나를 예약
        │
        ├─▶ new BeanFactoryInitializationAotContributions(beanFactory).applyTo(...)     :59
        │        └─ 각 기여자가 codeGenerator.getMethods().add(...) 로 메서드를 추가
        │             ApplicationContextInitializationCodeGenerator.java:136 (getMethods)
        │             └─▶ GeneratedMethods.add → generateSequencedMethodName
        │                   예약된 "initialize" 는 이 시점에 카운터가 1이므로
        │                   자동 생성 메서드는 "initialize1" 부터 받는다
        │
        └─▶ codeGenerator.getClassName() 반환
        │
        ▼
generationContext.writeGeneratedContent()                ContextAotProcessor.java:109
        └─▶ GeneratedClasses.writeTo(generatedFiles)     GeneratedClasses.java:194
              └─▶ generatedClass.generateJavaFile()      GeneratedClass.java:135
                    └─ methods.doWithMethodSpecs(type::addMethod)  GeneratedMethods.java:135
```

예약이 없으면 무슨 일이 나는지는 생성 결과물의 모양이 설명한다.\
`ApplicationContextInitializationCodeGenerator.generateInitializeMethod()` (`:89-96`)가 `MethodSpec.methodBuilder("initialize")`로 손코드 메서드를 직접 써 넣는데, `GeneratedMethods`가 발급한 자동 생성 메서드가 우연히 같은 이름을 받으면 같은 클래스 안에 같은 시그니처의 메서드가 둘이 되어 **생성된 소스가 컴파일되지 않는다.**\
즉 이 예약은 런타임 정합성이 아니라 **생성물의 컴파일 가능성**을 지키는 장치다.

수정 전 결함이 오래 숨은 이유도 이 지도에서 읽힌다.\
유일한 호출처가 이름을 **하나만** 넘기고, 한 원소 배열은 `MethodName.of(배열)`과 `MethodName.of(원소)`가 같은 값을 만든다.\
`reserveMethodNames`가 public varargs API인데도 "2개 이상" 경로를 실행하는 코드가 트리 안에 없었으므로, 잘못된 인자가 결과에 나타날 기회가 없었다.

## 5. 관련 개념

이 구조를 이해하는 데 필요한 개념 세 가지를 본문 밖에서 정리한다.

**AOT 코드 생성과 "생성될 이름"의 소유권.**\
Spring AOT는 런타임 리플렉션으로 하던 일을 빌드 시점에 자바 소스로 옮긴다.\
생성기는 메서드 이름을 직접 짓지 않고 제안(`suggestedName`)만 하며, 실제 이름은 `GeneratedClass`가 결정한다 (`GeneratedMethods.java:87-115`).\
여러 기여자가 독립적으로 코드를 보태는 구조라서, 이름 충돌 해소를 한 곳에 모아 둔 설계다.\
예약은 그 중앙 결정권자에게 "이 이름은 이미 임자가 있다"고 미리 알리는 유일한 수단이다.

**부작용으로 구현된 예약.**\
예약된 이름의 집합을 따로 들고 있는 자료구조는 없다.\
예약 여부는 `methodNameSequenceGenerator` 맵의 카운터 값에만 존재하고, 밖에서 조회할 공개 API도 없다.\
그래서 tests.md가 설명하듯 테스트도 내부 맵을 들여다보는 대신 "다음 발급 이름"이라는 관측 가능한 계약으로 예약 사실을 확인한다.\
상태를 값으로 노출하지 않는 설계에서는 **관측 가능한 후속 동작**이 사실상의 계약 표면이 된다.

**varargs 파라미터와 루프 변수의 이름 충돌.**\
`String... reservedMethodNames`와 루프 변수 `reservedMethodName`은 `s` 한 글자만 다르다.\
그리고 `MethodName.of`도 `String...`을 받으므로 배열을 넘겨도 타입이 맞아 컴파일러가 막지 못한다.\
타입 검사가 무력한 자리에서는 이름이 유일한 방어선인데, 그 이름조차 단수/복수로만 갈리면 방어선이 사실상 없다.\
같은 이유로 `MethodName.of(String...)`처럼 "여러 인자를 하나로 합치는" API는 컬렉션 순회 안에서 특히 오용되기 쉽다.
