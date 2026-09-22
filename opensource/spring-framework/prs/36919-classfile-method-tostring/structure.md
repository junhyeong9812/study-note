# PR #36919 — 무대의 실구조와 워크플로우

> PR #36919의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 커밋에는 PR #36919가 아직 반영되지 않았으므로,
> 아래 file:line 인용은 전부 **수정 전 코드**를 그대로 가리킨다.

## 1. 무대 — 실구조

무대는 JDK 24 전용 소스셋(`spring-core/src/main/java24/`)의 메서드 메타데이터 한 클래스와, 그 안의 `Source` 레코드다.\
결론부터 말하면, **`ClassFileMethodMetadata`는 자기 상태를 거의 갖지 않고 `equals`/`hashCode`/`toString`을 전부 `Source` 레코드에 위임하며, 그 레코드의 `toString()` 안에서 타입 이름을 만드는 규칙이 두 가지로 갈려 있다.**\
반환 타입 슬롯은 공용 헬퍼를 쓰고, 파라미터 슬롯은 옛 인라인 표현식을 쓴다.

> **레코드(record)** — 값 몇 개를 묶어 들고 다니기 위한 자바의 짧은 클래스 문법.\
> 예: `record Source(String declaringClassName, AccessFlags flags, String methodName, MethodTypeDesc descriptor)`는 네 값을 한 덩어리로 묶는다.

> **슬롯(slot)** — 한 문자열 안에서 한 종류의 값이 들어가는 자리.\
> 예: `public void Foo.bar(int)`에는 접근자·반환 타입·이름·파라미터 목록이라는 네 슬롯이 있다.

먼저 소유 관계다.

```text
org.springframework.core.type.MethodMetadata            (공용 인터페이스)
        ▲ implements
        │
┌───────┴──────────────────────────────────────────────────────────────────┐
│ ClassFileMethodMetadata      (ClassFileMethodMetadata.java:45, final)    │
│                                                                          │
│  필드                                                                     │
│    String      methodName          :47                                   │
│    AccessFlags accessFlags         :49                                   │
│    String      declaringClassName  :51  (@Nullable)                      │
│    String      returnTypeName      :53  ← resolveTypeName 으로 만든 값     │
│    Object      source              :56  ★ equals/hashCode/toString 위임처 │
│    MergedAnnotations mergedAnnotations :58                               │
│                                                                          │
│  접근자 (필드를 그대로 노출)                                               │
│    getMethodName()  :73 / getDeclaringClassName() :78                    │
│    getReturnTypeName() :83 / getAnnotations() :120                       │
│    isAbstract() :88 / isStatic() :93 / isFinal() :98 / isPrivate() :108   │
│    isOverridable() :103 / isSynthetic() :112 / isDefaultConstructor() :116│
│                                                                          │
│  위임 3종                                                                 │
│    equals(Object)  :127  → this.source.equals(that.source)               │
│    hashCode()      :132  → this.source.hashCode()                        │
│    toString()      :137  → this.source.toString()      ◀── 이 PR의 대상    │
│                                                                          │
│  정적 팩터리                                                              │
│    of(MethodModel, ClassLoader)  :142                                    │
│      methodName       = methodModel.methodName().stringValue()      :143 │
│      flags            = methodModel.flags()                         :144 │
│      declaringClassName = parent().thisClass() → 클래스명 변환       :145 │
│      returnType       = methodModel.methodTypeSymbol().returnType() :148 │
│      returnTypeName   = ClassFileAnnotationMetadata                      │
│                            .resolveTypeName(returnType)             :149 │
│      source           = new Source(declaringClassName, flags,            │
│                             methodName, methodModel.methodTypeSymbol()) :150│
│      mergedAnnotations = RuntimeVisibleAnnotationsAttribute 있으면        │
│                            ClassFileAnnotationDelegate.createMerged…()   │
│                                                                     :151-156│
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ record Source(String declaringClassName, AccessFlags flags,        │ │
│  │               String methodName, MethodTypeDesc descriptor)  :168  │ │
│  │                                                                    │ │
│  │   equals()   :170  네 값 비교 (descriptor 는 descriptorString() 로) │ │
│  │   hashCode() :179  같은 네 값                                       │ │
│  │   toString() :184  ◀── 문제의 메서드                                │ │
│  │       flags.flags() 를 소문자로 나열                          :187-190│ │
│  │       resolveTypeName(descriptor.returnType())                :191  │ │
│  │       declaringClassName + '.' + methodName                   :193-195│ │
│  │       '(' + 파라미터 목록 + ')'                                :196-200│ │
│  │            └ desc -> desc.packageName() + "." + desc.displayName()  │ │
│  │                                                        :198  ★ 버그 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                    │ 쓰는 헬퍼
                    ▼
ClassFileAnnotationMetadata.resolveTypeName(ClassDesc)
                             ClassFileAnnotationMetadata.java:225-235
    if (type.isPrimitive()) return type.displayName();                :226-228
    effectiveType = type;  while (effectiveType.isArray())            :229-232
        effectiveType = effectiveType.componentType();
    packageName = effectiveType.packageName();                        :233
    return packageName.isEmpty() ? type.displayName()
                                 : packageName + "." + type.displayName();  :234
```

이 구조에서 이 PR을 규정하는 사실이 세 가지 나온다.

**첫째, `Source`는 두 가지 역할을 겸한다.**\
하나는 `MethodMetadata`의 identity(`equals`/`hashCode`)이고, 다른 하나는 `MergedAnnotation`의 source다.\
후자 때문에 `toString()`의 결과가 어노테이션 처리 오류 메시지에 그대로 실린다(4절 참조).

> **identity(동일성)** — 두 객체를 "같은 것"으로 볼지 판정하는 기준.\
> 예: 여기서는 선언 클래스명·플래그·메서드명·디스크립터 네 값이 같으면 같은 메서드로 본다.

**둘째, 한 문자열 안에 타입 슬롯이 두 개 있고 규칙이 다르다.**

```text
 Source.toString() 이 만드는 문자열
 ┌──────────┬──────────────┬─────────────────────┬─────────────────────────┐
 │ 접근자    │ 반환 타입     │ 선언클래스.메서드명   │ (파라미터 목록)          │
 └──────────┴──────────────┴─────────────────────┴─────────────────────────┘
   :187-190     :191            :193-195               :196-200
              resolveTypeName                       desc.packageName()
              (헬퍼 경유)                            + "." + desc.displayName()
                   ▲                                     ▲
                   │                                     │
              gh-36577 이 옮긴 슬롯                  옮기지 않고 남긴 슬롯
```

**셋째, 헬퍼는 원래 이 파일에 있었다가 옮겨 갔다.**\
커밋 `b01fdb01408`("Fix ClassFileMethodMetadata return type names for primitives and arrays", See gh-36577)이 `returnTypeName` 계산을 `returnType.packageName() + "." + returnType.displayName()`에서 새로 만든 `resolveTypeName(...)` 호출로 바꾸면서 이 헬퍼를 `ClassFileMethodMetadata` 안에 private static으로 도입했다.\
이후 커밋에서 헬퍼가 `ClassFileAnnotationMetadata`로 올라가 공용이 되었고(현재 :225), 재귀 대신 while 루프 형태로도 다듬어졌다(`d4cc273c312`, "Avoid recursion in ClassFileAnnotationMetadata.resolveTypeName()").

즉 **:198의 인라인 표현식은 gh-36577이 고친 그 표현식과 글자 그대로 같은 형태**이며, 같은 파일 안에서 한 슬롯만 옮겨지고 다른 슬롯이 남은 결과다.

대비를 위해 ASM 쪽 대응물을 같이 놓으면 목표값이 분명해진다.

```text
ASM 변형   SimpleMethodMetadataReadingVisitor.Source   (src/main/java)
    static final class Source                                          :101
        필드: declaringClassName / methodName / int access / String descriptor
              + toStringValue 캐시                                      :111
        toString()                                                      :145
            access 비트를 public/protected/private/abstract/static/final
                 순서로 고정 출력                                        :150-166
            builder.append(returnType.getClassName())                   :168
            builder.append(declaringClassName + '.' + methodName)       :170-172
            Type[] argumentTypes = Type.getArgumentTypes(descriptor)    :173
            for (int i = 0; i < argumentTypes.length; i++)              :175
                builder.append(argumentTypes[i].getClassName())         :179
                                 └───────────┘
                     ASM Type.getClassName() 이 원시·배열·참조를
                     모두 정규 이름으로 낸다 — 슬롯이 하나의 규칙만 쓴다
```

ASM 쪽은 반환 타입과 파라미터가 **같은 함수**(`Type#getClassName`)를 쓴다.\
ClassFile 쪽만 두 규칙으로 갈려 있다.

## 2. 수정 전 동작 워크플로우

### 2.1 대표 시나리오 — `void sample(int, String[])`의 메타데이터를 만들고 출력

먼저 메타데이터가 만들어지는 흐름이다.\
이 구간에서는 아직 문자열이 계산되지 않고, `Source`가 디스크립터 원본을 그대로 들고만 있다.

> **`MethodModel`** — `java.lang.classfile`이 클래스 파일을 파싱해 내놓는, 메서드 하나에 대응하는 읽기 전용 모델 객체.\
> 예: `methodModel.methodTypeSymbol()`을 부르면 그 메서드의 `MethodTypeDesc`가 나온다.

> **`MethodTypeDesc`** — 반환 타입 하나와 파라미터 타입 배열을 묶은 메서드 시그니처 값 객체.\
> 예: `void sample(int, String[])`이면 `returnType()`은 `ClassDesc(void)`, `parameterArray()`는 `[ClassDesc(int), ClassDesc(String[])]`이다.

```text
MetadataReaderFactory.create(resourceLoader)          (JDK 24+ → ClassFile 경로)
  │
  ▼
ClassFileMetadataReaderFactory.getMetadataReader(className)   ClassFileMetadataReaderFactory.java:61
  │
  ▼
new ClassFileMetadataReader(resource, classLoader)            ClassFileMetadataReader.java:43
  │   ClassFile.of().parse(bytes) → ClassModel                                    :50
  ▼
ClassFileAnnotationMetadata.of(classModel, classLoader)        ClassFileAnnotationMetadata.java:189
  │   classModel.elementStream() 순회                                             :193
  │     case MethodModel method -> Builder.method(method)                         :214
  ▼
Builder.method(MethodModel)                                                       :317
  │   ClassFileMethodMetadata.of(method, classLoader)                             :318
  │   synthetic 이거나 <init> 이면 declaredMethods 에 넣지 않는다                   :319-321
  ▼
ClassFileMethodMetadata.of(methodModel, classLoader)          ClassFileMethodMetadata.java:142
  │
  ├─ methodName = "sample"                                                        :143
  ├─ flags = methodModel.flags()                    (ACC_PUBLIC)                  :144
  ├─ declaringClassName = "….WithMethod"                                          :145-147
  ├─ returnType = methodTypeSymbol().returnType()   ClassDesc(void)               :148
  ├─ returnTypeName = resolveTypeName(returnType)   → "void"   ◀ 헬퍼 경유         :149
  ├─ source = new Source(declaringClassName, flags, methodName,
  │                      methodModel.methodTypeSymbol())                          :150
  │      · methodTypeSymbol() = MethodTypeDesc "(I[Ljava/lang/String;)V"
  └─ mergedAnnotations = RuntimeVisibleAnnotationsAttribute 있으면 파싱, 없으면 빈 것 :151-156
  ▼
new ClassFileMethodMetadata(methodName, flags, declaringClassName,
                            returnTypeName, source, mergedAnnotations)            :157
```

여기까지는 메타데이터를 만드는 흐름이고, 아직 문자열은 만들어지지 않는다.\
문자열은 누군가 `toString()`을 부를 때 계산된다.

### 2.2 문자열 생성 — `toString()` 호출 흐름

문자열은 누군가 `toString()`을 부를 때 네 조각으로 나뉘어 조립되고, 마지막 조각인 파라미터 목록에서만 규칙이 어긋난다.

```text
호출자: methodMetadata.toString()   (예: 오류 메시지 조립, 로깅, 테스트 단언)
  │
  ▼
ClassFileMethodMetadata.toString()                                                :137
  │   return this.source.toString();                                              :138
  ▼
Source.toString()                                                                 :184
  │
  ├─ StringBuilder builder = new StringBuilder()                                  :186
  │
  ├─ flags.flags().forEach(flag -> {                                              :187
  │      builder.append(flag.name().toLowerCase(Locale.ROOT));  → "public"
  │      builder.append(' ');
  │   })                                                                          :190
  │                                       현재까지: "public "
  │
  ├─ builder.append(resolveTypeName(descriptor.returnType()))                     :191
  │      └ ClassDesc(void).isPrimitive() → true → displayName() = "void"
  │                                       현재까지: "public void "
  │
  ├─ builder.append(this.declaringClassName)                                      :193
  ├─ builder.append('.')                                                          :194
  ├─ builder.append(this.methodName)                                              :195
  │                                       현재까지: "public void ….WithMethod.sample"
  │
  ├─ builder.append('(')                                                          :196
  │
  ├─ builder.append(Stream.of(this.descriptor.parameterArray())                   :197
  │        .map(desc -> desc.packageName() + "." + desc.displayName())            :198 ★
  │        .collect(Collectors.joining(",")))                                     :199
  │
  │    파라미터 1: ClassDesc(int)
  │        packageName() = ""   displayName() = "int"
  │        → "" + "." + "int"  =  ".int"                     ◀◀ 선행 점
  │    파라미터 2: ClassDesc(String[])
  │        packageName() = ""   displayName() = "String[]"
  │            · 배열의 packageName() 은 빈 문자열이다
  │              (원소의 패키지를 물려받지 않는다)
  │        → "" + "." + "String[]"  =  ".String[]"           ◀◀ 선행 점 + 패키지 소실
  │
  ├─ builder.append(')')                                                          :200
  ▼
  "public void ….WithMethod.sample(.int,.String[])"
        └────────────┬────────────┘  └──────┬──────┘
             앞은 정상(헬퍼 경유)        괄호 안만 깨져 있다
```

한 문자열 안에서 앞은 맞고 뒤는 틀리다는 것이 이 결함의 특징이다.\
그리고 **파싱이나 비교 로직은 전혀 영향받지 않는다** — `equals`/`hashCode`(:170, :179)는 `descriptor.descriptorString()`을 쓰지 `toString()`을 쓰지 않고, `getReturnTypeName()`(:83)이 돌려주는 값은 :149에서 헬퍼로 따로 계산된 것이다.\
즉 손상 반경은 **사람이 읽는 진단 문자열 한 줄**로 한정된다.

> **손상 반경(blast radius)** — 결함이 잘못 만들면 함께 망가지는 범위.\
> 예: 여기서는 오류 메시지 한 줄뿐이고, 빈 선택·주입·스캔 결과는 하나도 바뀌지 않는다.

## 3. 분기 처리 워크플로우

### 3.1 두 슬롯의 분기 대조

문제는 조건문의 잘못된 분기가 아니라 **한쪽 슬롯에 분기 자체가 없다**는 것이다.

```text
반환 타입 슬롯  :191                        파라미터 슬롯  :198
resolveTypeName(ClassDesc)                 desc.packageName() + "." + desc.displayName()
        │                                          │
        ▼                                          ▼
   type.isPrimitive() ?                     (분기 없음 — 무조건 이어 붙인다)
   ┌────┴────┐                                     │
   │ 예      │ 아니오                               ▼
   ▼         ▼                              packageName() 이 "" 이면
displayName()  effectiveType = type          결과가 "." 으로 시작한다
  "int"       while (isArray())
  "void"        effectiveType =
  "double"        componentType()
              ┌───────────────┴──────────┐
              ▼                          ▼
        packageName 이 비었나?
        ┌────┴────┐
        │ 예      │ 아니오
        ▼         ▼
   displayName()  packageName + "." + displayName()
     "String[]"     "java.lang.String[]"
     (디폴트        (배열이면 패키지는 원소에서,
      패키지)         대괄호는 전체 displayName 에서)
```

### 3.2 `ClassDesc`가 내는 값 — 분기가 필요한 이유

`packageName()`이 빈 문자열을 돌려주는 경우가 셋이다.\
그 셋이 정확히 깨지는 경우와 일치한다.

```text
ClassDesc 종류        isPrimitive  isArray  packageName()   displayName()
──────────────────   ───────────  ───────  ─────────────   ──────────────
int                    true        false     ""              "int"
void                   true        false     ""              "void"
java.lang.String       false       false     "java.lang"     "String"
String[]               false       true      ""              "String[]"
int[][]                false       true      ""              "int[][]"
(디폴트 패키지 클래스)   false       false     ""              "Foo"
```

수정 전 :198의 결과를 대조하면 이렇다.\
오른쪽은 ASM 변형(`SimpleMethodMetadataReadingVisitor.java:179`, `Type#getClassName`)이 같은 자리에서 내는 값이다.

```text
파라미터 타입      수정 전 ClassFile 렌더링   ASM 렌더링             판정
───────────────  ────────────────────────  ──────────────────  ──────
int                ".int"                    "int"               불일치
long               ".long"                   "long"              불일치
String[]           ".String[]"               "java.lang.String[]" 불일치(패키지 소실)
int[][]            ".int[][]"                "int[][]"           불일치
java.lang.String   "java.lang.String"        "java.lang.String"  일치 ◀ 우연히 맞음
java.lang.Integer  "java.lang.Integer"       "java.lang.Integer" 일치 ◀ 우연히 맞음
```

**마지막 두 줄이 이 결함이 오래 살아남은 이유다.**\
패키지가 있는 참조 타입은 `packageName()`이 비지 않으므로 분기 없이 이어 붙여도 맞는 값이 나온다.\
그리고 기존 공유 테스트가 파라미터 축에서 검증하던 타입이 전부 그런 타입이었다.

```text
기존 픽스처의 축 교차 (README 5절 참조)

            │ 반환 타입 슬롯      │ 파라미터 슬롯
────────────┼────────────────────┼──────────────────
원시 타입    │ 검증됨(gh-36577)    │ 빈칸  ◀ 버그 통과
배열        │ 검증됨(gh-36577)    │ 빈칸  ◀ 버그 통과
참조 타입    │ 검증됨              │ 검증됨(우연히 green)
```

### 3.3 버그가 살던 분기 — 요약

네 조각을 한 화면에 놓으면 분기가 없는 조각이 하나뿐이라는 사실이 드러난다.

```text
Source.toString()
   │
   ├─ 접근자 나열       :187-190   flags 순회 — 문제 없음
   ├─ 반환 타입         :191       resolveTypeName ── 3갈래 분기 ── 정상
   ├─ 선언클래스.메서드  :193-195   문자열 연결 — 문제 없음
   └─ 파라미터 목록     :197-199
          .map(desc -> desc.packageName() + "." + desc.displayName())   :198
                        └────────────────────────────────────────┘
                        ◀◀ 분기 없는 단일 표현식. 원시·배열·디폴트패키지에서
                           선행 점이 붙고, 배열은 패키지까지 잃는다.
```

PR의 수정은 이 표현식을 메서드 참조 하나로 바꾼다.

```text
   .map(ClassFileAnnotationMetadata::resolveTypeName)
```

새 규칙을 만들지 않고 **같은 문자열의 다른 슬롯이 이미 쓰던 함수**를 재사용하므로, 분기도상으로는 파라미터 슬롯이 반환 타입 슬롯과 같은 3갈래 분기를 갖게 되는 것이 전부다.

## 4. 스프링 전역에서의 자리

이 문자열은 **로직이 소비하는 값이 아니라 사람이 읽는 진단 값**이다.\
그 사실을 코드로 확인하면 이렇다.

### 4.1 메타데이터가 만들어지는 진입점

`ClassFileMethodMetadata`는 `ClassFileAnnotationMetadata`의 빌더에서만 만들어지고(`ClassFileAnnotationMetadata.java:318`), 그 위로는 36917과 같은 파이프라인을 공유한다.

> **AOT(ahead-of-time)** — 애플리케이션을 실행하기 전 빌드 시점에 빈 정의·프록시 같은 것을 미리 확정해 두는 Spring의 처리 방식.\
> 예: 아래 경로의 `ImportAwareAotBeanPostProcessor`·`ConfigurationClassPostProcessor`가 그 단계에서 같은 메타데이터 리더를 쓴다.

```text
ClassFileMethodMetadata.of(...)                   ClassFileMethodMetadata.java:142
        ▲
        │ ClassFileAnnotationMetadata.Builder.method(MethodModel) :317
        ▲
        │ ClassFileAnnotationMetadata.of(ClassModel, ClassLoader)  :189,:214
        ▲
        │ ClassFileMetadataReader 생성자                            :45
        ▲
        │ ClassFileMetadataReaderFactory.getMetadataReader(Resource) :61
        ▲
        │ MetadataReaderFactory.create(...) → MetadataReaderFactoryDelegate.create(...)
        │      (JDK 24+ 소스셋: MetadataReaderFactoryDelegate.java:34,:38)
        ▲
        ├─ CachingMetadataReaderFactory            CachingMetadataReaderFactory.java:56,:65,:76
        ├─ ClassPathScanningCandidateComponentProvider :417, :464      (컴포넌트 스캔)
        ├─ ConfigurationClassUtils :134 / ConfigurationClassParser :218, :730, :1036, :1138
        ├─ AutowiredAnnotationBeanPostProcessor :274, :645             (주입 메타데이터)
        └─ ImportAwareAotBeanPostProcessor :71 / ConfigurationClassPostProcessor :994, :999  (AOT)
```

### 4.2 `MethodMetadata` 인스턴스가 실제로 쓰이는 곳

grep으로 확인한 소비처는 둘이다.\
둘 다 **어노테이션이 붙은 메서드를 골라내는** 용도다.

```text
ConfigurationClassParser.retrieveBeanMethodMetadata(...)      ConfigurationClassParser.java:461
    Set<MethodMetadata> beanMethods = original.getAnnotatedMethods(Bean.class.getName());
      └ @Bean 메서드 목록. ASM/ClassFile 순서 문제로 :468 에서 재확인하는 경로도 있다

AutowiredAnnotationBeanPostProcessor                  AutowiredAnnotationBeanPostProcessor.java:646
    Set<MethodMetadata> asmMethods = asm.getAnnotatedMethods(Autowired.class.getName());
```

두 소비처 모두 `getMethodName()`·`getAnnotations()` 등 **구조화된 접근자**를 쓰고 `toString()`을 파싱하지 않는다.\
즉 이 PR의 변경은 프레임워크 로직의 어떤 분기도 바꾸지 않는다.

> **구조화된 접근자(structured accessor)** — 값을 문자열로 짜내는 대신 타입이 붙은 전용 메서드로 꺼내는 방식.\
> 예: 메서드 이름이 필요하면 `toString()`을 잘라 쓰지 않고 `getMethodName()`을 부른다.

### 4.3 `toString()`이 실제로 새어 나가는 자리

`Source`는 `MergedAnnotation`의 source로 쓰이므로, 어노테이션 처리 오류 메시지에 그대로 실린다.\
대표 소비처는 `@AliasFor` 미러 검증이다.

> **미러(mirror)** — `@AliasFor`로 서로 별칭이 된 속성 묶음. 값이 서로 어긋나면 안 된다.\
> 예: `value`와 `path`에 다른 값을 동시에 주면 이 검증이 예외를 던지고, 그 메시지에 source 문자열이 실린다.

```text
AnnotationTypeMapping … MirrorSets 의 미러 값 검증        AnnotationTypeMapping.java:649
    String on = (source != null) ? " declared on " + source : "";
    throw new AnnotationConfigurationException(String.format(
        "Different @AliasFor mirror values for annotation [%s]%s; attribute '%s' "
        + "and its alias '%s' are declared with values of [%s] and [%s].",
        …, on, …));                                                         :650-657
                    ▲
                    │ source 가 MethodMetadata 쪽에서 온 경우
                    │ 여기에 "public void ….sample(.int,.String[])" 가 박힌다
```

정리하면 진입 경로는 이렇다.

```text
컴포넌트 스캔 / @Configuration 파싱 (JDK 24+)
        │
        ▼
ClassFileMethodMetadata.Source 생성                     :150
        │
        ├─ 정상 경로: getAnnotatedMethods(...) 로 구조화된 값만 소비  ← toString 안 씀
        │
        └─ 오류 경로: @AliasFor 미러 불일치 등
              AnnotationTypeMapping:649  " declared on " + source
                    └→ source.toString()  ClassFileMethodMetadata.Source:184
                          └→ 파라미터 슬롯이 ".int,.String[]" 로 렌더링   ◀ 피해 지점
```

**피해의 성격은 "오류를 조사하는 사람이 타입을 특정하지 못한다**"이다.\
특히 배열은 점 하나가 더 붙는 데 그치지 않고 패키지가 통째로 사라지므로, `java.lang.String[]`이어야 할 이름이 `.String[]`이 된다.\
그래서 동명의 클래스가 여러 패키지에 있을 때 메시지만으로는 어느 것인지 알 수 없다.

## 5. 관련 개념

### 5.1 멀티 릴리스 소스셋 — 같은 이름의 클래스가 두 벌

Spring 7.0은 JDK 24의 `java.lang.classfile` 표준화를 이용하기 위해 멀티 릴리스 구조를 쓴다.\
`spring-core/spring-core.gradle:5`가 `org.springframework.build.multiReleaseJar` 플러그인을 적용하고 `:13-14`의 `multiRelease { releaseVersions 21, 24 }`가 소스셋을 등록한다.\
빌드는 `src/main/java24`를 `java24` 소스셋으로(`:23`의 `java24Api` 설정 참조), `src/test/java24`를 `java24Test` 태스크로 만든다.

```text
src/main/java/…/classreading/MetadataReaderFactoryDelegate.java
      create(...) → new SimpleMetadataReaderFactory(...)      (ASM)         :38
src/main/java24/…/classreading/MetadataReaderFactoryDelegate.java
      create(...) → new ClassFileMetadataReaderFactory(...)   (ClassFile)   :34,:38
             ▲
             │ 클래스 이름·패키지가 동일하다.
             │ 멀티 릴리스 JAR 규칙에 따라 JDK 24 이상에서 java24 쪽이 우선한다.
             ▼
     런타임 JDK 버전이 구현을 고른다 — 호출자는 어느 쪽인지 모른다
```

이 구조가 만드는 요구사항은 하나다.\
**두 구현이 같은 값을 내야 한다.**\
그렇지 않으면 같은 애플리케이션이 JDK 버전에 따라 다르게 동작한다.\
이 PR이 ASM 쪽 렌더링을 목표값으로 삼는 근거가 여기 있고, 36917에서 "구현 간 불일치는 곧 버그 판정"이라는 논리가 성립한 근거도 같다.

테스트 배치도 이 구조를 따른다.\
`src/test/java`의 공유 테스트(`AbstractMethodMetadataTests` 등)는 `java24Test` 태스크에서 java24 클래스와 함께 다시 실행되므로, 한 벌의 단언이 두 구현을 동시에 잰다.\
반면 `src/test/java24`에 놓인 테스트는 ClassFile 구현만 잰다.

### 5.2 `ClassDesc` — 디스크립터를 감싼 값 객체

`java.lang.constant.ClassDesc`는 클래스 파일의 타입 디스크립터를 표현하는 불변 값 객체다.\
`MethodTypeDesc`는 그것들의 묶음이다.

> **불변 값 객체(immutable value object)** — 만들어진 뒤 내용이 바뀌지 않고, 내용이 같으면 같은 것으로 취급되는 객체.\
> 예: `ClassDesc(int)` 두 개는 서로 다른 인스턴스여도 같은 타입을 가리킨다.

```text
소스 선언            디스크립터                MethodTypeDesc
──────────────    ────────────────────    ────────────────────────────
void sample(         "(I[Ljava/lang/       returnType()      → ClassDesc(void)
     int,             String;)V"           parameterArray()  → [ClassDesc(int),
     String[])                                                 ClassDesc(String[])]
                                           descriptorString() → 위 문자열 그대로
```

`ClassDesc`가 제공하는 이름 관련 메서드는 셋이고, 각각 답하는 질문이 다르다.

```text
displayName()     "사람이 읽는 짧은 이름"      int / String[] / String
packageName()     "패키지"                    "" / "" / "java.lang"
descriptorString() "JVM 디스크립터"            I / [Ljava/lang/String; / Ljava/lang/String;
```

여기서 함정은 **배열의 `packageName()`이 원소의 패키지를 물려받지 않는다**는 점이다.\
배열 타입 자체는 어떤 패키지에도 속하지 않는다고 보는 것이 JVM의 관점이고, `ClassDesc`가 그것을 그대로 반영한다.\
그래서 `String[]`에 대해 `packageName() + "." + displayName()`을 하면 `java.lang`이 아니라 `""`가 붙어 `.String[]`이 된다.

> **원소 타입(component type)** — 배열이 담는 것의 타입.\
> 예: `String[][]`의 원소 타입은 `String[]`이고, 한 번 더 벗기면 `String`이다.

`resolveTypeName`(`ClassFileAnnotationMetadata.java:225`)이 `while (isArray())`로 원소까지 벗겨 내려가 그 패키지를 쓰는 것(:229-234)이 정확히 이 함정을 피하는 코드다.\
대괄호는 벗기지 않은 원본 `type.displayName()`에서 가져오므로 `java.lang` + `.` + `String[]` = `java.lang.String[]`이 만들어진다.

### 5.3 헬퍼 추출의 미완 — 규칙을 뽑았으면 호출부를 전부 훑어야 한다

이 PR이 다루는 결함의 형태는 "코드가 틀렸다"보다 "**리팩토링이 덜 끝났다**"에 가깝다.

```text
gh-36577 (커밋 b01fdb01408) 이 한 일
   ① 문제의 인라인 표현식을 진단:  returnType.packageName() + "." + returnType.displayName()
   ② 규칙을 함수로 추출:           resolveTypeName(ClassDesc)
   ③ 호출부 교체:                  returnTypeName 계산 1곳            ← 여기서 멈췄다
   ④ (하지 않음) 같은 표현식의 다른 인라인 사용처 전수 확인
         └ Source.toString() 의 파라미터 슬롯이 남았다
```

같은 파일 안에서 문자열 검색 한 번이면 걸리는 형태였는데도 남았다는 점이 시사적이다.\
일반화하면 규칙은 이렇다.\
**규칙을 함수로 추출했다면, 그 규칙의 옛 인라인 표현을 전부 훑는 것까지가 추출 작업의 일부다.**\
추출만 하고 호출부를 일부만 바꾸면, 남은 호출부는 "고쳐진 규칙과 다른 규칙"을 쓰는 코드가 되어 결함이 오히려 발견하기 어려워진다.

### 5.4 진단 문자열의 stakes — 낮지만 0은 아니다

`toString()`은 계약 표면이 아니다.\
로직이 파싱하지 않고, 테스트가 문자열을 고정하는 곳도 공유 테스트 몇 줄뿐이다.\
그래서 이 결함의 손상 반경은 작다.

> **stakes** — 이 변경이 틀렸을 때 치르는 대가의 크기.\
> 예: 빈 주입이 어긋나면 애플리케이션이 뜨지 않지만(높음), 진단 문자열이 어긋나도 동작은 그대로다(낮음).

```text
계약 값 (로직이 소비)                 진단 값 (사람이 소비)
────────────────────────────      ────────────────────────────────
getReturnTypeName()  :83           toString()  :137
getMethodName()      :73           MergedAnnotation source 로서의 문자열
equals()/hashCode()  :127,:132
        │                                  │
   틀리면 동작이 깨진다                 틀려도 동작은 그대로다
   → stakes 높음                       → stakes 낮음
                                          다만 "오류를 조사하는 순간"에만
                                          쓰이므로, 틀리면 가장 도움이
                                          필요한 시점에 도움이 사라진다
```

오른쪽 열의 마지막 문장이 이 PR의 값이다.\
진단 문자열은 평소에 아무도 보지 않다가 장애 조사 중에만 읽힌다.\
그 순간에 `java.lang.String[]`이 `.String[]`으로 보이면, 비용은 "메시지가 조금 이상하다"가 아니라 "원인 특정에 실패한다"가 된다.
