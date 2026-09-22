# PR #36917 — 무대의 실구조와 워크플로우

> PR #36917의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`.
>
> **주의 — 이 PR의 무대는 현재 HEAD와 다르다.** PR은 `status: declined`로 닫혔고,
> 같은 결함이 메인테이너 커밋 `7de2b24d81c`("Fix primitive array annotation attributes
> on Java 24 class reading")에서 먼저 다르게 고쳐졌다. 따라서 2·3절의 "수정 전"은
> 그 커밋의 부모(`7de2b24d81c^`) 코드를 기준으로 서술하고, 현재 HEAD 코드는 별도로
> 표시한다. 1·4·5절의 file:line은 별도 표기가 없으면 HEAD 기준이다.

## 1. 무대 — 실구조

무대는 JDK 24 전용 소스셋(`spring-core/src/main/java24/`)에 사는 클래스 다섯 개다.\
결론부터 말하면, **바이트코드의 어노테이션 어트리뷰트를 자바 값으로 되살리는 층이 `ClassFileAnnotationDelegate` 하나에 몰려 있고, 배열 어트리뷰트의 원소 타입을 정하는 결정이 그 안에서 두 갈래로 나뉘어 있었다.**\
그 두 갈래의 불일치가 이 PR의 대상이다.

> **소스셋(source set)** — 같은 모듈 안에서 조건에 따라 따로 컴파일되는 소스 디렉토리 묶음.\
> 예: `src/main/java24/`의 클래스는 JDK 24 이상에서만 컴파일·사용된다.

먼저 전체 배치다.\
같은 이름의 클래스가 두 소스셋에 각각 존재하는 멀티 릴리스 구조가 출발점이다.

> **멀티 릴리스(multi-release)** — 하나의 산출물 안에 JDK 버전별 구현을 나란히 담아, 실행 중인 JDK에 맞는 쪽이 선택되게 하는 구조.\
> 예: 같은 `MetadataReaderFactory.create(...)` 호출이 JDK 23에서는 ASM 리더를, JDK 24에서는 ClassFile 리더를 돌려준다.

```text
                     MetadataReaderFactory.create(...)
                       (public 정적 팩터리, MetadataReaderFactory.java:69,:79)
                                    │
                                    ▼
                     MetadataReaderFactoryDelegate.create(...)
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │ src/main/java (JDK 24 미만)          src/main/java24 (JDK 24+) │
        ▼                                                       ▼
  new SimpleMetadataReaderFactory(...)          new ClassFileMetadataReaderFactory(...)
      MetadataReaderFactoryDelegate.java:38         MetadataReaderFactoryDelegate.java:34,:38
        │ ASM 기반                                             │ java.lang.classfile 기반
        ▼                                                       ▼
  SimpleMetadataReader                            ClassFileMetadataReaderFactory :33
    └ ASM ClassReader                               └ getMetadataReader(Resource) :61
                                                         └ new ClassFileMetadataReader(...)
```

JDK 24 쪽 파이프라인을 펼치면 이렇다.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ ClassFileMetadataReader        (ClassFileMetadataReader.java:36, final)  │
│   Resource           resource            :38                            │
│   AnnotationMetadata annotationMetadata  :40                            │
│                                                                         │
│   생성자 :43   → parseClassModel(resource) :48                           │
│                   └ ClassFile.of().parse(inputStream.readAllBytes()) :50 │
│                 → ClassFileAnnotationMetadata.of(classModel, cl)  :45    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ClassFileAnnotationMetadata   (ClassFileAnnotationMetadata.java:51,final)│
│   implements AnnotationMetadata                                         │
│                                                                         │
│   String   className / AccessFlags accessFlags / Set<String> interfaceNames …│
│   Set<MethodMetadata> declaredMethods    :67                            │
│   MergedAnnotations   mergedAnnotations  :69                            │
│                                                                         │
│   static of(ClassModel, ClassLoader)  :189                              │
│     classModel.elementStream() 을 switch 로 훑으며 Builder 채움  :193-221 │
│       case RuntimeVisibleAnnotationsAttribute →                         │
│            ClassFileAnnotationDelegate.createMergedAnnotations(...) :205 │
│       case MethodModel → Builder.method(...) :214 → ClassFileMethodMetadata│
│                                                                         │
│   static resolveTypeName(ClassDesc)   :225  (원시/배열/패키지 처리 헬퍼)   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ClassFileAnnotationDelegate   (ClassFileAnnotationDelegate.java:47)     │
│   abstract (인스턴스 없음 — 정적 유틸 묶음)                                │
│                                                                         │
│   createMergedAnnotations(className, attr, cl)   :49                    │
│     └ attr.annotations() 스트림 → createMergedAnnotation 매핑 → of(...)  │
│   createMergedAnnotation(className, Annotation, cl)  :61                │
│     ├ resolveTypeName → AnnotationFilter.PLAIN 이면 null (java.* 제외)   │
│     ├ ClassUtils.forName 로 어노테이션 타입 선로딩 (:70)                  │
│     └ elements() 순회 → readAnnotationValue → attributes 맵 :72-77       │
│   readAnnotationValue(className, AnnotationValue, cl)  :87  ★ sealed switch│
│   parseArrayValue(className, cl, OfArray)              :109 ◀── 이 PR의 대상│
│   parseEnum / loadEnumClass                            :120,:125         │
│   resolveArrayElementType(List<AnnotationValue>, cl)   :135 ◀── 짝이 되는 곳│
│   record Source(String className)                      :154              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ 결과 = MergedAnnotation 들
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ TypeMappedAnnotation  (spring-core/src/main/java/.../annotation/)       │
│   getValue(...) 등으로 값을 꺼낼 때 선언 타입과 실제 값을 대조            │
│     adapt(...)             TypeMappedAnnotation.java:442                │
│     adaptForAttribute(...) TypeMappedAnnotation.java:499  ★ 여기서 터진다 │
└─────────────────────────────────────────────────────────────────────────┘
```

이 배치에서 이 PR을 규정하는 사실은 두 가지다.

**첫째, `AnnotationValue`는 sealed 계층이다.**\
JDK가 하위 타입을 고정해 두었다.

> **sealed 계층(sealed hierarchy)** — 하위 타입이 될 수 있는 클래스를 선언 시점에 못 박아, 밖에서 새 하위 타입을 만들 수 없게 한 상속 구조.\
> 예: `AnnotationValue`의 하위 타입은 아래 13개가 전부이며, 컴파일러가 그 사실을 알고 있다.

```text
java.lang.classfile.AnnotationValue  (sealed)
   ├─ OfConstant  (sealed)
   │     ├ OfByte  ├ OfShort  ├ OfChar    ├ OfInt
   │     ├ OfLong  ├ OfFloat  ├ OfDouble  └ OfBoolean
   │     └ OfString
   ├─ OfClass
   ├─ OfEnum
   ├─ OfAnnotation
   └─ OfArray        ← 원소로 위 타입들을 담는다
```

sealed이므로 `default` 없는 `switch`를 쓰면 컴파일러가 열거의 완전성을 강제한다.\
현재 HEAD의 `readAnnotationValue`(:87-107)와 `resolveArrayElementType`(:135-151)이 둘 다 `default` 없는 형태로 쓰여 있다.\
반면 **PR 시점의 `parseArrayValue`에는 `default` 분기가 있었다** — 그것이 누락을 조용히 삼킨 자리다.

> **완전성 검사(exhaustive switch)** — sealed 타입을 대상으로 한 switch에서, 하위 타입을 하나라도 빠뜨리면 컴파일러가 거부하는 규칙.\
> 예: `default`를 지워 두면 JDK가 `OfXxx`를 새로 추가하는 순간 이 파일이 컴파일되지 않는다.

**둘째, 배열의 "원소 타입"을 정하는 결정이 두 곳에 있었다.**\
PR 시점 코드에서 `parseArrayValue`는 `int`/`double`/`long`만 자기 안에서 원시 배열로 처리하고, 나머지는 `resolveArrayElementType`에 물어 `Object[]` 계열로 만들었다.\
같은 질문에 답하는 코드가 둘로 갈라져 있었고, 한쪽이 다른 쪽을 덮지 못했다.

```text
        "이 배열의 원소 타입은 무엇인가?"
                    │
        ┌───────────┴────────────────────┐
        ▼                                ▼
 parseArrayValue 안의 case 3개    resolveArrayElementType
 (OfInt / OfDouble / OfLong)      (나머지 전부)
   → 진짜 원시 배열                 → OfConstant 이면 resolvedValue().getClass()
                                      = Byte / Short / Character /
                                        Boolean / Float  (박싱된 클래스)
                                    → Array.newInstance(Byte.class, n) = Byte[]
```

## 2. 수정 전 동작 워크플로우

> 이 절의 코드·행번호는 **`7de2b24d81c^`**(PR base) 기준이다. 현재 HEAD와 다르다.

### 2.1 대표 시나리오 — `byte[] bytes()` 어트리뷰트 하나를 읽는다

`@ArrayTypesAnnotation(byteValue = 1)`이 붙은 클래스를 JDK 24 이상에서 읽는 흐름이다.

> **`ClassModel`** — `java.lang.classfile` API가 `.class` 파일 바이트를 읽어 만든, 클래스 하나의 읽기 전용 표현.\
> 예: `ClassFile.of().parse(bytes)`가 돌려주며, `elementStream()`으로 어트리뷰트·메서드를 훑는다.

```text
MetadataReaderFactory.create(resourceLoader)                 (JDK 24+ → ClassFile 경로)
  │
  ▼
ClassFileMetadataReaderFactory.getMetadataReader(className)
  │   AbstractMetadataReaderFactory 가 className → Resource 해소
  ▼
new ClassFileMetadataReader(resource, classLoader)
  │   ClassFile.of().parse(bytes)  →  ClassModel
  ▼
ClassFileAnnotationMetadata.of(classModel, classLoader)
  │   elementStream() 순회 중 RuntimeVisibleAnnotationsAttribute 발견
  ▼
ClassFileAnnotationDelegate.createMergedAnnotations(className, attr, cl)   base:50
  │   attr.annotations() → 각 Annotation 마다
  ▼
createMergedAnnotation(className, annotation, cl)                          base:62
  │   ├ typeName = resolveTypeName(annotation.classSymbol())
  │   ├ AnnotationFilter.PLAIN.matches(typeName) ? → java.* 계열이면 null
  │   ├ ClassUtils.forName(typeName, cl)  ← 로딩 불가면 catch 에서 null (base:81)
  │   └ for (AnnotationElement element : annotation.elements())
  │         readAnnotationValue(className, element.value(), cl)            base:88
  ▼
readAnnotationValue — elementValue 는 OfArray                              base:104
  │
  ▼
parseArrayValue(className, cl, arrayValue)                                 base:110
  │
  ├─ arrayValue.values().isEmpty() ?  → new Object[0] 로 조기 반환          base:111
  │
  ├─ stream = arrayValue.values().stream()                                 base:114
  │
  └─ switch (arrayValue.values().getFirst())                               base:115
        ├ OfInt    → mapToInt(...).toArray()      →  int[]                 base:116
        ├ OfDouble → mapToDouble(...).toArray()   →  double[]              base:119
        ├ OfLong   → mapToLong(...).toArray()     →  long[]                base:122
        └ default  →  ◀◀ byte/short/char/boolean/float 이 전부 여기로       base:125
              arrayElementType = resolveArrayElementType(values, cl)       base:126
                  └ OfConstant → constantValue.resolvedValue().getClass()  base:149
                       · OfByte 의 resolvedValue() 는 Byte(1)  (박싱)
                       · 따라서 반환값은 Byte.class
              return stream
                  .map(v -> readAnnotationValue(className, v, cl))         base:128
                  .toArray(len -> (Object[]) Array.newInstance(Byte.class, len))
                  ⇒ 결과는 Byte[]{1}  —  byte[] 가 아니다                  base:129
```

여기서 결정적인 두 줄을 나란히 놓으면 원인이 보인다.

```text
base:129   .toArray(length -> (Object[]) Array.newInstance(arrayElementType, length))
                              └────────┘
                              Object[] 로 캐스팅하므로 원시 배열이 될 수 없다.
                              Array.newInstance(byte.class, n) 은 byte[] 를 만들지만
                              그것은 Object[] 로 캐스팅되지 않는다(ClassCastException).
                              즉 이 표현식은 구조적으로 참조 배열만 만들 수 있다.

base:149   return constantValue.resolvedValue().getClass();
                  └──────────────────────────┘
                  resolvedValue() 의 정적 타입은 Object 이므로 반드시 박싱된다.
                  byte → Byte, char → Character, boolean → Boolean, float → Float
```

### 2.2 값이 소비되는 지점 — 예외가 실제로 터지는 자리

파싱 자체는 예외 없이 끝난다.\
문제는 값을 꺼낼 때다.

```text
호출자: annotation.getValue("byteValue")  또는  synthesize() 후 속성 접근
  │
  ▼
TypeMappedAnnotation.adapt(attribute, value, type)     TypeMappedAnnotation.java:442
  │  value = adaptForAttribute(attribute, value)                            :447
  ▼
adaptForAttribute(Method attribute, Object value)                           :499
  │
  ├─ attributeType = resolvePrimitiveIfNecessary(attribute.getReturnType()) :500
  │      · byte[] value() 이므로 attributeType = byte[].class
  │
  ├─ attributeType.isArray() && !value.getClass().isArray() ?  → 아니오      :501
  ├─ attributeType.isAnnotation() ?                            → 아니오      :505
  ├─ 원소가 애노테이션인 배열 ?                                 → 아니오      :508
  ├─ Class ↔ String 상호 변환 대상 ?                            → 아니오      :517
  ├─ attributeType.isArray() && isEmptyObjectArray(value) ?                 :523
  │      · isEmptyObjectArray = (value instanceof Object[] o && o.length==0) :535
  │      · Byte[]{1} 은 길이 1 이므로 여기서 안 걸린다
  │      ※ 빈 배열(Object[0])이었다면 여기서 구제되어 예외가 안 난다  ◀ 함정
  │
  └─ !attributeType.isInstance(value) ?                                     :526
         · byte[].class.isInstance(new Byte[]{1})  →  false
              (배열 공변성은 참조 타입 사이에서만 성립)
         ⇒ throw new IllegalStateException(
               "Attribute 'byteValue' in annotation ... should be compatible
                with byte[] but a java.lang.Byte[] value was returned")     :527-531
```

즉 결함은 **파싱 시점에 심어지고 소비 시점에 터진다.**\
그리고 빈 배열은 :523에서 구제되므로, 빈 배열만으로 시험하면 아무 문제가 없어 보인다.

> **무음 실패(silent failure)** — 잘못된 값이 만들어졌는데 그 자리에서는 아무 신호도 나지 않고, 한참 뒤 다른 곳에서 터지는 실패.\
> 예: `Byte[]`가 만들어지는 `parseArrayValue`는 조용히 끝나고, 값을 꺼내는 `adaptForAttribute`에 가서야 예외가 된다.

### 2.3 현재 HEAD는 어떻게 다른가

메인테이너 커밋 `7de2b24d81c`는 `parseArrayValue`의 타입별 분기를 통째로 없앴다.

```text
현재 HEAD                                       ClassFileAnnotationDelegate.java:109
─────────────────────────────────────────────────────────────────────────────
parseArrayValue(className, classLoader, arrayValue) {
    List<AnnotationValue> values = arrayValue.values();                     :110
    Class<?> arrayElementType =
        (values.isEmpty() ? Object.class
                          : resolveArrayElementType(values, classLoader));  :111
    Object array = Array.newInstance(arrayElementType, values.size());      :112
    for (int i = 0; i < values.size(); i++) {
        Array.set(array, i, readAnnotationValue(className, values.get(i), classLoader)); :114
    }
    return array;                                                           :116
}
```

바뀐 지점이 셋이다.\
첫째, `Object[]` 캐스팅이 사라져 `Array.newInstance(byte.class, n)`이 진짜 `byte[]`를 만든다.\
둘째, `Array.set`이 박싱된 값을 언박싱해 채운다.\
셋째, 빈 배열 조기 반환이 없어지고 `Object.class`로 길이 0 배열을 만든다.

그리고 `resolveArrayElementType`(:135-151)이 `default` 없는 exhaustive switch로 바뀌어 원시 클래스 리터럴(`byte.class` 등)을 직접 돌려준다.

> **언박싱(unboxing)** — 래퍼 객체에서 원시 값을 꺼내는 것. `Byte` → `byte`.\
> 예: `Array.set(byteArray, 0, Byte.valueOf((byte) 1))`은 내부에서 `byteValue()`를 불러 원시 값을 칸에 넣는다.

## 3. 분기 처리 워크플로우

### 3.1 수정 전 `parseArrayValue` 분기도 (base 기준)

base 코드의 분기는 두 층으로 갈린다.\
바깥에서 빈 배열을 조기 반환으로 걸러 내고, 안쪽 switch가 첫 원소의 타입에 따라 네 갈래로 나뉜다.

> **조기 반환(early return)** — 본류 흐름에 합류하지 않고 함수 앞머리에서 바로 값을 돌려주고 끝내는 분기.\
> 예: `if (values.isEmpty()) return new Object[0];`은 뒤에 오는 타입 결정 로직을 통째로 건너뛴다.

```text
parseArrayValue(className, classLoader, arrayValue)                    base:110
        │
        ▼
   values().isEmpty() ?
        │
   ┌────┴──────────────────────────┐
   │ 예                            │ 아니오
   ▼                               ▼
 return new Object[0]        switch (values().getFirst())         base:115
   base:112                        │
   · 선언 타입과 무관하게      ┌────┼────┬────────────────────────────┐
     항상 Object[0]           │    │    │                            │
   · TypeMappedAnnotation   OfInt OfDouble OfLong              default (그 외 전부)
     :523 이 나중에 보정       │    │    │                            │
   · 조용히 넘어가므로       int[] double[] long[]                    │
     빈 배열 테스트로는      (진짜 원시 배열)                          ▼
     결함을 못 잡는다  ◀ 함정                              resolveArrayElementType()
                                                                 base:145
                                                                     │
                                                    ┌────────────────┼──────────────┐
                                                    ▼                ▼              ▼
                                          OfConstant           OfAnnotation      OfEnum
                                          resolvedValue()      MergedAnnotation  loadEnumClass
                                            .getClass()          .class            (...)
                                              │                                  OfClass
                                              ▼                                  String.class
                                    Byte / Short / Character /                   default
                                    Boolean / Float / Integer /                  Object.class
                                    Long / Double / String
                                              │
                                              ▼
                                    Array.newInstance(박싱클래스, n)
                                    → Byte[] / Short[] / Character[] /
                                      Boolean[] / Float[]      ◀◀ 버그가 살던 분기
```

버그가 살던 분기는 `default`다.\
여기가 흡수하는 원소 타입은 열 가지인데(`OfByte`, `OfShort`, `OfChar`, `OfBoolean`, `OfFloat`, `OfString`, `OfClass`, `OfEnum`, `OfAnnotation`, `OfArray`), 그중 **원시 다섯 개만** 잘못된 결과가 된다.\
`String`·`Class`·`Enum`·`Annotation`·중첩 배열은 원래 참조 타입이므로 `Object[]` 캐스팅으로도 맞는 값이 나온다.\
이 비대칭이 결함을 오래 숨겼다.

타입별로 결과를 정리하면 이렇다.

| 어트리뷰트 선언 | base의 분기 | base 결과 | `adaptForAttribute` 결과 |
|---|---|---|---|
| `int[]`, `long[]`, `double[]` | 전용 `case` | `int[]` / `long[]` / `double[]` | 통과 |
| `byte[]`, `short[]`, `char[]` | `default` | `Byte[]` / `Short[]` / `Character[]` | **IllegalStateException** |
| `boolean[]`, `float[]` | `default` | `Boolean[]` / `Float[]` | **IllegalStateException** |
| `String[]`, `Class[]`, enum 배열 | `default` | `String[]` 등 참조 배열 | 통과 |
| 원소 0개(모든 타입) | 조기 반환 | `Object[0]` | :523이 보정해 통과 |

### 3.2 PR이 제안했던 분기 (거절됨)

PR은 `default`가 흡수하던 원시 다섯 개를 각각 전용 `case`로 끌어냈다.

```text
switch (values().getFirst())
   │
   ├ OfInt / OfDouble / OfLong        (기존 3개, 스트림 mapToXxx)
   │
   ├ OfByte    ─┐
   ├ OfShort    │  PR 이 추가한 5개.
   ├ OfChar     │  Stream 에 mapToByte 류가 없으므로
   ├ OfBoolean  │  각 case 가 직접 배열을 채운다:
   ├ OfFloat   ─┘    byte[] result = new byte[values.size()];
   │                 for (i…) result[i] = ((OfByte) values.get(i)).byteValue();
   │
   └ default                          (남은 참조 타입들 — 그대로)
```

이 형태는 표의 2·3행을 고치지만 **마지막 행(빈 배열 조기 반환)은 손대지 않고**, `default` 분기 자체도 남긴다.\
즉 sealed 계층에 새 원시 타입이 추가되면 같은 누락이 다시 조용히 발생할 수 있는 구조가 유지된다.

### 3.3 현재 HEAD의 분기 — 분기가 사라진 자리

현재 HEAD에서는 타입별 분기가 `resolveArrayElementType` 한 곳으로 모였고, `parseArrayValue`에는 빈 배열 여부를 보는 분기 하나만 남았다.

```text
parseArrayValue                                                            :109
        │
        ├─ values.isEmpty() ? → arrayElementType = Object.class             :111
        │                  아니면 resolveArrayElementType(values, cl)
        │                       ※ 분기이되 "조기 반환"이 아니다 —
        │                          이후 흐름은 동일하게 합류한다
        ▼
   Array.newInstance(arrayElementType, values.size())                       :112
        │
        ▼
   for (i…) Array.set(array, i, readAnnotationValue(...))                   :114
        │      · 원시 클래스면 언박싱되어 담긴다
        ▼
   return array                                                             :116


resolveArrayElementType(values, classLoader)                                :135
   return switch (values.getFirst()) {                    ← default 없음
       case OfByte    _ -> byte.class;                                      :137
       case OfChar    _ -> char.class;                                      :138
       case OfDouble  _ -> double.class;                                    :139
       case OfFloat   _ -> float.class;                                     :140
       case OfInt     _ -> int.class;                                       :141
       case OfLong    _ -> long.class;                                      :142
       case OfShort   _ -> short.class;                                     :143
       case OfBoolean _ -> boolean.class;                                   :144
       case OfString  _ -> String.class;                                    :145
       case OfAnnotation _ -> MergedAnnotation.class;                       :146
       case OfClass   _ -> String.class;                                    :147
       case OfEnum enumValue -> loadEnumClass(enumValue, classLoader);      :148
       case OfArray   _ -> Object.class;                                    :149
   };
        │
        └─ sealed 이므로 JDK 가 하위 타입을 추가하면 컴파일 실패
           ⇒ 같은 종류의 누락이 조용히 재발할 수 없다
```

세 분기도를 겹쳐 보면 차이는 "잎을 몇 개 더 만들었나"가 아니라 "**분기점을 몇 개로 줄였나**"다.\
base는 결정 지점이 둘(`parseArrayValue`의 switch + `resolveArrayElementType`), PR 제안도 둘, HEAD는 하나다.

## 4. 스프링 전역에서의 자리

이 파싱 층은 **클래스를 로딩하지 않고 어노테이션을 읽어야 하는 모든 기능**의 바닥에 있다.\
grep으로 확인한 실제 진입점은 다음과 같다.

> **AOT(ahead-of-time) 처리** — 애플리케이션을 실행하기 전에 빈 정의·어노테이션 정보를 미리 계산해 코드로 굳혀 두는 단계.\
> 예: `ConfigurationClassPostProcessor`가 생성 코드 안에 `metadataReaderFactory.getMetadataReader(...)` 호출을 그대로 심는다.

```text
ClassFileAnnotationDelegate.parseArrayValue   (JDK 24+ 에서만 선택되는 구현)
        ▲
        │ ClassFileAnnotationMetadata.of(...) :205
        ▲
        │ ClassFileMetadataReader 생성자 :45
        ▲
        │ ClassFileMetadataReaderFactory.getMetadataReader(Resource) :61
        ▲
        │ MetadataReaderFactory.create(...) → MetadataReaderFactoryDelegate.create(...)
        ▲
        ├── CachingMetadataReaderFactory                CachingMetadataReaderFactory.java:56,:65,:76
        │      · 리소스별 MetadataReader 캐시. 스캐닝 경로의 실제 사용 형태
        │
        ├── 컴포넌트 스캔
        │     ClassPathScanningCandidateComponentProvider
        │        .findCandidateComponents → scanCandidateComponents
        │           getMetadataReaderFactory().getMetadataReader(resource)  :464
        │        .isCandidateComponent / 타입 필터 경로
        │           getMetadataReaderFactory().getMetadataReader(type)      :417
        │     AbstractTypeHierarchyTraversingFilter.match(...)
        │           metadataReaderFactory.getMetadataReader(className)      :127
        │
        ├── @Configuration 처리
        │     ConfigurationClassUtils.checkConfigurationClassCandidate
        │           metadataReaderFactory.getMetadataReader(className)      :134
        │     ConfigurationClassParser.parse(...)                           :218
        │        · asSourceClass / @Import 해소                             :730,:1036,:1138
        │        · @Bean 메서드 메타데이터 회수                              :461,:468
        │
        ├── 의존성 주입 메타데이터
        │     AutowiredAnnotationBeanPostProcessor
        │        this.metadataReaderFactory = MetadataReaderFactory.create(classLoader)  :274
        │        …getMetadataReader(targetClass.getName()).getAnnotationMetadata()       :645
        │        …getAnnotatedMethods(Autowired.class.getName())                          :646
        │
        └── AOT
              ImportAwareAotBeanPostProcessor.getMetadataReader(importingClass)  :71
              ConfigurationClassPostProcessor 가 생성 코드에
                 metadataReaderFactory.getMetadataReader($S).getAnnotationMetadata()
                 를 그대로 심는다                                            :994,:999
```

이 경로들이 읽는 어노테이션에 원시 배열 어트리뷰트가 있으면, JDK 24 이상에서 `IllegalStateException`이 스캔 도중 터진다.\
실제로 그렇게 보고된 것이 README가 인용하는 gh-37083(Spring Boot 4 마이그레이션 중 `MetadataReader`로 `byte[]` 어트리뷰트를 읽다 실패)이다.

한편 값 소비 지점은 `spring-core`의 어노테이션 층 하나로 수렴한다.

```text
MergedAnnotation.getValue(...) / synthesize() / asMap(...)
        │
        ▼
TypeMappedAnnotation.adapt(...)               TypeMappedAnnotation.java:442
        └ adaptForAttribute(...)                                    :499
             ├ 빈 Object[] 보정                                      :523
             └ !attributeType.isInstance(value) → IllegalStateException :526
```

즉 **파싱 구현은 둘(ASM / ClassFile)인데 검증 지점은 하나**다.\
두 구현이 같은 `AnnotationMetadata` 계약을 만족해야 하는 이유가 여기서 구조적으로 드러난다 — 소비 측은 어느 리더가 값을 만들었는지 모른다.

> **계약(contract)** — 인터페이스가 구현마다 달라지면 안 된다고 약속한 동작의 내용. 시그니처뿐 아니라 "무엇을 돌려주는가"까지 포함한다.\
> 예: `AnnotationMetadata`는 `byte[] value()` 어트리뷰트에 대해 `byte[]`를 돌려준다고 약속한다. 어느 리더가 읽었든 마찬가지여야 한다.

## 5. 관련 개념

### 5.1 sealed 계층과 exhaustive switch — 컴파일러를 검사자로 쓰는 법

`AnnotationValue`가 sealed이라는 사실은 단순한 타입 정보가 아니라 **검증 수단**이다.

```text
default 가 있는 switch                    default 가 없는 switch (sealed 대상)
──────────────────────────────         ────────────────────────────────────
새 하위 타입이 생겨도 컴파일 통과        새 하위 타입이 생기면 컴파일 실패
누락이 런타임 동작으로 나타난다          누락이 빌드 시점에 나타난다
"나머지 전부"라는 잎이 서로 다른         모든 잎이 명시적으로 열거된다
  의미를 한꺼번에 흡수한다
```

base의 `parseArrayValue`는 `default`를 갖고 있었고, 그 잎이 **성격이 다른 아홉 가지 원소 타입**을 한꺼번에 흡수했다.\
그중 다섯이 잘못 처리되어도 컴파일러는 아무 말도 하지 않는다.\
반대로 같은 파일의 `readAnnotationValue`(HEAD :87-107)는 처음부터 `default` 없이 다섯 갈래를 명시했고, 그래서 같은 종류의 누락이 없다.\
재료는 이미 파일 안에 있었던 셈이다.

일반화하면 이렇다.\
**"기존 코드에서 여러 케이스가 한꺼번에 빠졌다"는 사실 자체가 열거를 손으로 하고 있다는 신호다.**\
그때 옳은 질문은 "빠진 것을 다 채웠나"가 아니라 "다음에 또 빠지는 것을 컴파일러가 막을 수 있나"다.

### 5.2 원시 배열과 참조 배열 — 공변성이 끊기는 자리

`Byte[]`가 `byte[]` 자리에 들어가지 못하는 이유는 배열 공변성의 적용 범위 때문이다.

> **배열 공변성(array covariance)** — `String`이 `Object`의 하위 타입이면 `String[]`도 `Object[]`의 하위 타입으로 취급되는 자바의 규칙.\
> 예: `Object[] a = new String[3];`은 되지만 `Object[] a = new int[3];`은 안 된다.

```text
참조 타입 사이 (공변)                     원시 타입과 (공변 아님)
──────────────────────────           ──────────────────────────────
String[]  →  Object[]   OK            byte[]   →  Object[]   컴파일 불가
Integer[] →  Number[]   OK            Byte[]   →  byte[]     불가
Byte[]    →  Object[]   OK            byte[]   와 Byte[] 는 무관한 타입

byte[] 의 상위 타입은 Object 하나뿐이다 (Object[] 가 아니다).
```

이 사실이 base:129의 `(Object[]) Array.newInstance(arrayElementType, length)` 표현식을 **구조적으로 원시 배열을 만들 수 없게** 만든다.\
`arrayElementType`에 `byte.class`를 넣어도 `Array.newInstance`는 `byte[]`를 만들고, 그것을 `Object[]`로 캐스팅하는 순간 `ClassCastException`이다.\
즉 그 캐스팅이 있는 한 원시 배열은 원리적으로 반환될 수 없다.

HEAD가 캐스팅을 없애고 반환 타입을 `Object`로 둔 것(:112, :116)이 이 제약을 푸는 방법이다.\
`Array.set`(:114)은 리플렉션 API라 대상 배열이 원시면 자동으로 언박싱한다.

> **`java.lang.reflect.Array`** — 배열을 타입을 모른 채 다루게 해 주는 리플렉션 유틸. `newInstance(타입, 길이)`로 만들고 `set(배열, i, 값)`으로 채운다.\
> 예: `Array.newInstance(byte.class, 2)`는 `byte[2]`를 만들고, `Array.set(arr, 0, Byte.valueOf((byte) 1))`은 그 칸에 원시 `1`을 넣는다.

한편 `Class#isInstance`도 같은 규칙을 따른다.

```text
byte[].class.isInstance(new byte[]{1})   → true
byte[].class.isInstance(new Byte[]{1})   → false   ← TypeMappedAnnotation:526 이 잡는 것
Object[].class.isInstance(new Byte[]{1}) → true
Object[].class.isInstance(new byte[]{1}) → false
```

### 5.3 어노테이션 값의 저장 형태 — 바이트코드에는 타입 태그만 있다

클래스 파일에서 어노테이션 어트리뷰트 값은 `element_value` 구조로 저장되고, 첫 바이트가 태그다.

> **태그(tag)** — 뒤따르는 바이트를 어떻게 해석할지 알려 주는 한 글자짜리 표시.\
> 예: `'B'`가 먼저 오면 그다음 값은 `byte`로, `'['`가 먼저 오면 길이와 원소 목록으로 읽는다.

```text
tag  의미            java.lang.classfile 대응
───  ──────────    ──────────────────────────
'B'  byte           AnnotationValue.OfByte
'S'  short          AnnotationValue.OfShort
'C'  char           AnnotationValue.OfChar
'I'  int            AnnotationValue.OfInt
'J'  long           AnnotationValue.OfLong
'F'  float          AnnotationValue.OfFloat
'D'  double         AnnotationValue.OfDouble
'Z'  boolean        AnnotationValue.OfBoolean
's'  String         AnnotationValue.OfString
'c'  Class          AnnotationValue.OfClass
'e'  enum           AnnotationValue.OfEnum
'@'  annotation     AnnotationValue.OfAnnotation
'['  array          AnnotationValue.OfArray
```

여기서 중요한 것은 **배열 태그 `[`가 원소 타입을 담지 않는다**는 점이다.\
배열은 그저 길이와 원소 목록이고, 각 원소가 자기 태그를 갖는다.\
그래서 파서는 "이 배열의 원소 타입"을 알기 위해 **첫 원소의 태그를 본다**.\
base와 HEAD 모두 `values.getFirst()`(base:115, HEAD:136)로 시작하는 이유가 이것이다.

그리고 원소가 하나도 없으면 볼 태그가 없다.\
그것이 빈 배열이 특수 처리되는 근본 이유이고, base가 `new Object[0]`으로, HEAD가 `Object.class`로 처리하는 갈림길이다.\
실제 선언 타입(`byte[]`)은 클래스 파일의 이 자리에 기록되지 않으므로, 파서만으로는 빈 `byte[]`와 빈 `String[]`을 구분할 수 없다.\
그 구분은 어노테이션 타입을 로딩해 `Method#getReturnType`을 보는 소비 측(`TypeMappedAnnotation.adaptForAttribute` :523)에서만 가능하다.

### 5.4 두 구현 한 계약 — 불일치가 곧 버그 판정의 근거

`AnnotationMetadata`는 세 가지 방식으로 구현된다.

```text
StandardAnnotationMetadata      리플렉션 (클래스를 실제로 로딩)
SimpleAnnotationMetadata        ASM     (src/main/java, JDK 24 미만)
ClassFileAnnotationMetadata     ClassFile API (src/main/java24, JDK 24+)
        └ 이 PR의 무대
```

셋은 같은 인터페이스를 만족해야 하고, 소비 측은 어느 것인지 모른다.\
그래서 **둘의 결과가 다르면 설계 의도를 추측할 필요 없이 한쪽이 틀렸다.**\
이 PR의 진단이 옳았던 근거가 정확히 이것이었다 — ASM 경로는 같은 어노테이션에서 진짜 원시 배열을 냈다.

README가 지적하듯 이 사실은 테스트 배치에도 답을 준다.\
검증을 한 구현 전용 테스트 클래스에 두면 "구현 간 불일치"라는 진단과 어긋난다.\
실제 upstream 수정은 `AbstractAnnotationMetadataTests`(세 구현이 함께 상속)의 공용 픽스처에 원시 배열 어트리뷰트를 추가하는 쪽을 택했다.

> **픽스처(fixture)** — 테스트가 대상으로 삼는, 미리 만들어 둔 고정 입력물.\
> 예: `@ComplexAttributes(...)`가 붙은 테스트용 클래스 하나가 세 구현의 공용 픽스처 역할을 한다.

관련 개념 문서로는 [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)가 컴파일 타임 정보와 런타임 정보가 어디에 남는지를 다룬다.\
어노테이션 어트리뷰트가 클래스 파일에 남는 형태(5.3)와 그것을 읽는 세 경로의 관계를 이해하는 데 인접한 배경이다.
