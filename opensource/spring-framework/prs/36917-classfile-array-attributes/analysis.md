# PR #36917 분석 — 원시 배열 어트리뷰트가 박싱되는 결함, 그리고 의도 vs 버그 판별

> 기준: PR head `ec0df00afec`, PR base `0c60266986`. 2·3절의 "수정 전" file:line은 **PR base 기준**이다
> (structure.md는 메인테이너 커밋의 부모 `7de2b24d81c^`를 base로 쓰므로 `resolveArrayElementType`이 `:145`로 표기된다 —
> 같은 코드이고 앞쪽 5줄만큼 어긋난 것이다). "현재 HEAD"는 `upstream/main` `7daf1013aa8` 기준.
>
> 이 문서는 결함의 인과 사슬과 거절의 성격만 다룬다. 서사 해설은 README.md, 무대 지도는 structure.md,
> 테스트별 해설은 tests.md가 소유한다.

## 0. 결론

**결함**: JDK 24 전용 소스셋의 `ClassFileAnnotationDelegate#parseArrayValue`가 원시 배열 어트리뷰트를 `int`/`double`/`long` 세 종류만 전용 분기로 처리하고, 나머지 다섯(`byte`/`short`/`char`/`boolean`/`float`)은 `default` 분기로 흘려보내 **박싱된 참조 배열**(`Byte[]`, `Short[]`, `Character[]`, `Boolean[]`, `Float[]`)로 만들어 돌려준다.\
파싱은 조용히 끝나고, 값을 꺼내는 시점에 `TypeMappedAnnotation.adaptForAttribute`가 `byte[].class.isInstance(new Byte[]{...})`를 거짓으로 판정해 `IllegalStateException`을 던진다.

> **박싱(boxing)** — 원시 값을 그에 대응하는 래퍼 객체로 감싸는 것. `byte` → `Byte`.\
> 예: `Object o = (byte) 1;`의 `o.getClass()`는 `byte.class`가 아니라 `Byte.class`다.

**제안했던 수정**: 빠진 다섯 타입에 대해 전용 `case`를 다섯 개 추가한다(각 분기가 직접 원시 배열을 채운다).

**상태**: CLOSED / `status: declined`.\
2026-06-13 개설, 2026-08-05 라벨과 함께 닫힘.\
리뷰는 한 건도 없었다.\
거절 사유는 기술적 반박이 아니라 **중복**이다 — 같은 결함이 2026-07-22 메인테이너 커밋 `7de2b24d81c`(gh-37083)에서 먼저, 그리고 더 근본적으로 고쳐졌다.\
진단은 옳았고 사후적으로 증명되었으나, **수정의 층위**와 **가시성** 두 축에서 밀렸다(5.2절, 6.3절).

## 1. 무대

결함이 사는 자리와 그것이 예외로 드러나는 자리를 먼저 좌표로 고정한다.

| 축 | 값 |
|---|---|
| 모듈 | `spring-core`, JDK 24 전용 소스셋 `spring-core/src/main/java24/` |
| 파일 | `.../core/type/classreading/ClassFileAnnotationDelegate.java` |
| 결함 지점 | `parseArrayValue` `:110-132` (base). 특히 `default` 분기 `:125-130`와 `resolveArrayElementType` `:150-169` |
| 예외가 터지는 곳 | `TypeMappedAnnotation#adaptForAttribute` `:520-525` (HEAD 기준) |
| 공개 진입 API | `MetadataReaderFactory.create(...)` -> `getMetadataReader(...)` -> `AnnotationMetadata` |

Spring은 클래스를 로딩하지 않고 바이트코드만 읽어 어노테이션 메타데이터를 뽑는다.\
컴포넌트 스캔, `@Configuration` 처리, `@Autowired` 메타데이터 회수, AOT 생성 코드가 모두 이 층에 의존한다.\
JDK 24부터 Spring 7은 구현을 둘 갖는다 — JDK 24 미만은 ASM 기반 `SimpleMetadataReader`, JDK 24 이상은 JDK 표준 `java.lang.classfile` 기반 `ClassFileMetadataReader`.\
선택 주체는 `MetadataReaderFactoryDelegate`이고, 후자의 어노테이션 값 파싱을 `ClassFileAnnotationDelegate`가 맡는다.

> **AOT(ahead-of-time) 생성 코드** — 실행 전에 미리 계산해 자바 소스로 굳혀 둔 빈 등록·설정 코드.\
> 예: `ConfigurationClassPostProcessor`가 생성 코드 안에 `getMetadataReader(...)` 호출을 그대로 심는다.

**이 배치가 이 PR을 규정한다.**\
파싱 구현은 둘인데 소비 측(`TypeMappedAnnotation`)은 하나이고, 소비 측은 어느 리더가 값을 만들었는지 모른다.\
따라서 두 리더의 결과가 다르면 설계 의도를 추측할 필요 없이 한쪽이 반드시 틀린 것이다 — 이것이 "의도인가 버그인가" 판별의 결정적 근거였다(4절).

## 2. 전체 메서드 그래프

아래 그래프는 리더 선택에서 파싱을 거쳐 값 소비까지를 세 구간으로 나눠 편 것이고, `[!]` 표시가 결함이 심어지거나 드러나는 지점이다.

```text
  [ 진입 — 어느 리더를 쓸지 결정 ]

  MetadataReaderFactory.create(resourceLoader | classLoader)   MetadataReaderFactory.java:69,:79
      |
      v
  MetadataReaderFactoryDelegate.create(...)
      |-- src/main/java   (JDK 24 미만) -> new SimpleMetadataReaderFactory(...)   [ASM 경로]
      +-- src/main/java24 (JDK 24 이상) -> new ClassFileMetadataReaderFactory(...)
                  |
                  v
      ClassFileMetadataReaderFactory.getMetadataReader(Resource)  :61
          -> new ClassFileMetadataReader(resource, classLoader)   :43
                 parseClassModel: ClassFile.of().parse(bytes)     :50
                 ClassFileAnnotationMetadata.of(classModel, cl)   :45


  [ 파싱 — 바이트코드의 어트리뷰트를 자바 값으로 ]

  ClassFileAnnotationMetadata.of(ClassModel, ClassLoader)        :189
      elementStream() 순회 중 RuntimeVisibleAnnotationsAttribute 발견  :205
                  |
                  v
  ClassFileAnnotationDelegate.createMergedAnnotations(className, attr, cl)   base:50
      attr.annotations() -> 각 Annotation 마다 createMergedAnnotation           :53-57
                  |
                  v
  createMergedAnnotation(className, annotation, cl)                          base:62
      typeName = ClassFileAnnotationMetadata.resolveTypeName(...)            base:65
      AnnotationFilter.PLAIN.matches(typeName) -> null (java.* 계열 제외)      base:66-68
      ClassUtils.forName(typeName, cl)  (로딩 불가면 catch 에서 null)          base:71, :82-85
      for (AnnotationElement element : annotation.elements())                base:73
          readAnnotationValue(className, element.value(), cl)                base:74
                  |
                  v
  readAnnotationValue(className, elementValue, cl)      (sealed switch, default 없음)  base:88
      OfConstant   -> constantValue.resolvedValue()      [!] 항상 박싱된 Object   base:92-94
      OfAnnotation -> createMergedAnnotation(...)                              base:95-97
      OfClass      -> resolveTypeName(...)  (String 으로)                       base:98-100
      OfEnum       -> parseEnum(...)                                           base:101-103
      OfArray      -> parseArrayValue(className, cl, arrayValue)               base:104-106
                  |
                  v
  parseArrayValue(className, cl, arrayValue)             [!] 결함이 사는 메서드  base:110
      values().isEmpty() -> return new Object[0]          [!] 조기 반환(함정)     base:111-113
      stream = arrayValue.values().stream()                                    base:114
      switch (arrayValue.values().getFirst())                                  base:115
          OfInt    -> mapToInt(...).toArray()      -> int[]                    base:116-118
          OfDouble -> mapToDouble(...).toArray()   -> double[]                 base:119-121
          OfLong   -> mapToLong(...).toArray()     -> long[]                   base:122-124
          default  -> [!] byte/short/char/boolean/float 이 전부 여기로           base:125-130
              arrayElementType = resolveArrayElementType(values, cl)           base:126
              return stream.map(v -> readAnnotationValue(className, v, cl))    base:128
                      .toArray(len -> (Object[]) Array.newInstance(arrayElementType, len))  base:129
                                      ^^^^^^^^^^ 이 캐스팅이 있는 한 원시 배열은 원리적으로 불가
                  |
                  v
  resolveArrayElementType(values, cl)                                          base:150
      OfConstant   -> constantValue.resolvedValue().getClass()   [!] 박싱 클래스  base:153-155
      OfAnnotation -> MergedAnnotation.class                                    base:156-158
      OfClass      -> String.class                                             base:159-161
      OfEnum       -> loadEnumClass(enumValue, cl)                             base:162-164
      default      -> Object.class                                             base:165-167


  [ 소비 — 예외가 실제로 터지는 자리 ]

  MergedAnnotation.getValue(...) / synthesize() / asMap(...)
      |
      v
  TypeMappedAnnotation.adapt(attribute, value, type)      TypeMappedAnnotation.java:437
      value = adaptForAttribute(attribute, value)                              :441
                  |
                  v
  adaptForAttribute(Method attribute, Object value)                            :493
      attributeType = ClassUtils.resolvePrimitiveIfNecessary(attribute.getReturnType())  :494
          byte[] value() 이므로 attributeType = byte[].class
      ... (배열/어노테이션/Class-String 변환 분기들, 전부 해당 없음) ...          :495-516
      attributeType.isArray() && isEmptyObjectArray(value) ?                    :517
          -> emptyArray(componentType)     [!] 빈 배열만 여기서 구제된다          :518
      !attributeType.isInstance(value) ?                                        :520
          -> throw IllegalStateException("... should be compatible with byte[]
              but a java.lang.Byte[] value was returned")                       :521-524
```

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 것은 "타입"이 세 층에 각각 다른 모습으로 존재한다는 점이다.\
클래스 파일의 **태그**(1바이트), 파싱 중간값의 **박싱된 자바 객체**, 그리고 어노테이션 선언의 **원시 배열 타입**.\
아래 항목은 각각이 어느 층의 타입을 들고 있는지를 밝힌다.

같은 값 `1`이 세 층에서 어떤 모습인지 세로로 내려 보면 이렇다.

```text
클래스 파일         태그 'B' + 상수 풀 인덱스        원시 타입 정보가 여기까지만 있다
      |
      v
java.lang.classfile  AnnotationValue.OfByte           태그가 sealed 하위 타입이 된다
      |
      v
파싱 중간값          Byte.valueOf((byte) 1)           resolvedValue() 가 Object 라 박싱된다
      |
      v
담을 배열            Byte[] (수정 전) / byte[] (수정 후)   여기가 갈라지는 지점
      |
      v
어노테이션 선언      byte[] byteValue()               소비 측이 기대하는 타입
```

### 2.5.1 파싱 층 (`ClassFileAnnotationDelegate.java`, base 기준)

파싱 층의 이름표들은 클래스 파일의 태그를 박싱된 자바 객체로 바꾸는 단계에 속한다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `createMergedAnnotations(...)` `:50` | `RuntimeVisibleAnnotationsAttribute` 하나를 `MergedAnnotations`로 | (className, attr, cl) -> `MergedAnnotations` | `ClassFileAnnotationMetadata.of` `:205` | 결함 경로의 진입점 |
| `createMergedAnnotation(...)` `:62` | 어노테이션 하나의 어트리뷰트 맵을 만든다. **타입을 먼저 로딩**해 실패를 앞당긴다 | (className, Annotation, cl) -> `MergedAnnotation` 또는 null | 위, 그리고 중첩 어노테이션 재귀 `:96` | 여기서 만든 attributes 맵에 박싱 배열이 들어간다 |
| `readAnnotationValue(...)` `:88` | 값 하나를 자바 객체로. `default` 없는 sealed switch | `AnnotationValue` -> `Object` 또는 null | `createMergedAnnotation` `:74`, `parseArrayValue` `:128` | 스칼라는 이미 exhaustive했다. 결함은 배열 쪽에만 있었다 |
| `AnnotationValue.OfConstant#resolvedValue()` | 상수 값을 자바 객체로 | -> `Object` | `readAnnotationValue` `:93`, `resolveArrayElementType` `:154` | 정적 타입이 `Object`라 **반드시 박싱된다**. `byte`는 `Byte` |
| `parseArrayValue(...)` `:110` | 배열 어트리뷰트를 자바 배열로 | (className, cl, `OfArray`) -> `Object` | `readAnnotationValue` `:105` | **결함 지점** |
| `arrayValue.values()` | 배열 원소 목록 | -> `List<AnnotationValue>` | 위 메서드 전반 | 클래스 파일의 배열 태그는 원소 타입을 담지 않으므로 `getFirst()`의 태그를 보고 추정한다 |
| `stream` (지역) `:114` | `values().stream()` | - | 세 원시 case와 default가 공유 | 이 스트림이 `toArray(IntFunction)`로 끝나므로 결과는 참조 배열 |
| `switch (values().getFirst())` `:115` | 첫 원소의 sealed 하위 타입으로 분기 | - | `parseArrayValue` | **`default` 분기가 있어 누락이 조용히 흡수된다** — 컴파일러가 완전성을 강제하지 못한다 |
| `default` 분기 `:125` | 나머지 열 가지 원소 타입을 전부 흡수 | - | 위 | `byte/short/char/boolean/float` 다섯만 틀린 결과가 되고, `String/Class/Enum/Annotation/중첩배열`은 원래 참조라 맞는다. **이 비대칭이 결함을 오래 숨겼다** |
| `arrayElementType` (지역) `:126` | 만들 배열의 원소 타입 | -> `Class<?>` | `Array.newInstance`의 인자 `:129` | 박싱 클래스(`Byte.class`)가 들어온다 |
| `(Object[]) Array.newInstance(...)` `:129` | 스트림 결과를 담을 배열 생성 | -> `Object[]` | `toArray(IntFunction)` | **이 캐스팅이 있는 한 원시 배열은 구조적으로 불가능하다.** `byte[]`는 `Object[]`로 캐스팅되지 않는다 |
| `resolveArrayElementType(...)` `:150` | 원소 타입 결정의 **두 번째 결정 지점** | (values, cl) -> `Class<?>` | `parseArrayValue`의 default `:126` | 같은 질문("이 배열의 원소 타입은?")에 답하는 코드가 둘로 갈라져 있었고 한쪽이 다른 쪽을 덮지 못했다 |
| `constantValue.resolvedValue().getClass()` `:154` | 박싱된 값의 런타임 클래스 | -> `Class<?>` | 위 | `Byte`/`Short`/`Character`/`Boolean`/`Float` 반환. 원시 클래스 리터럴이 아니다 |
| `resolveArrayElementType`의 `default` `:165` | `Object.class` | - | 위 | 여기에도 `default`가 있어 완전성이 강제되지 않았다 |
| `parseEnum` / `loadEnumClass` `:135` / `:140` | enum 상수 복원 / enum 클래스 로딩 | - | `readAnnotationValue`, `resolveArrayElementType` | 범위 밖 |
| `record Source(Annotation annotation)` `:172` | 메타데이터 출처 표시 | - | `MergedAnnotation.of` `:80` | 범위 밖. HEAD에서는 `Source(String className)`로 바뀌었다 |

### 2.5.2 소비 층 (`TypeMappedAnnotation.java`, HEAD 기준)

소비 층의 이름표들은 그 박싱된 값을 어노테이션 선언 타입과 대조하는 단계에 속한다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `adapt(Method, Object, Class<T>)` `:437` | 저장된 값을 요청 타입으로 변환 | (attribute, value, type) -> `T` | `getValue`/`synthesize`/`asMap` 경로 | `adaptForAttribute`를 첫 단계로 부른다 `:441` |
| `adaptForAttribute(Method, Object)` `:493` | 값이 **선언된 어트리뷰트 타입과 호환되는가**를 최종 판정 | (attribute, value) -> `Object` 또는 throw | `adapt` `:441` | 결함이 예외로 드러나는 유일한 지점 |
| `attributeType` (지역) `:494` | `resolvePrimitiveIfNecessary(attribute.getReturnType())` | -> `Class<?>` | 이하 모든 분기 | `byte[] value()`면 `byte[].class`. 배열 타입은 언박싱 대상이 아니라 그대로다 |
| `isEmptyObjectArray(Object)` `:529` | `value instanceof Object[] && length == 0` | -> `boolean` | `:517`의 구제 분기 | **함정의 핵심.** `Object[0]`은 여기서 걸려 선언 타입의 빈 배열로 교체되므로 빈 배열 테스트로는 결함을 못 잡는다 |
| `emptyArray(Class<?>)` `:533` | 컴포넌트 타입의 길이 0 배열(캐시 `EMPTY_ARRAYS` `:72`) | -> `Object` | `:518` | 빈 배열이 조용히 통과하는 이유 |
| `!attributeType.isInstance(value)` `:520` | 최종 관문 | -> `boolean` | `adaptForAttribute` 끝 | `byte[].class.isInstance(new Byte[]{1})`이 **false**. 배열 공변성은 참조 타입 사이에만 성립한다 |
| `IllegalStateException` 메시지 `:521-524` | "should be compatible with byte[] but a java.lang.Byte[] value was returned" | - | 위 | gh-37083 신고자의 스택트레이스와 PR 본문에 적은 것이 같은 문장이다 |

### 2.5.3 배경 상수와 개념

두 층 어디에도 속하지 않지만 판정의 근거가 된 배경 개념 넷을 따로 모은다.

| 이름표 | 무엇인가 | 결함과의 관계 |
|---|---|---|
| `AnnotationValue` (sealed) | JDK가 하위 타입을 고정한 계층. `OfConstant`(`OfByte`/`OfShort`/`OfChar`/`OfInt`/`OfLong`/`OfFloat`/`OfDouble`/`OfBoolean`/`OfString`), `OfClass`, `OfEnum`, `OfAnnotation`, `OfArray` | sealed이므로 `default` 없는 switch를 쓰면 **컴파일러가 열거의 완전성을 강제한다**. 이 사실이 메인테이너 수정의 핵심 재료였다 |
| `element_value` 태그 | 클래스 파일에서 어트리뷰트 값의 첫 바이트(`B`/`S`/`C`/`I`/`J`/`F`/`D`/`Z`/`s`/`c`/`e`/`@`/`[`) | 배열 태그 `[`는 **원소 타입을 담지 않는다.** 그래서 파서가 첫 원소의 태그를 보고 추정하고, 원소가 없으면 볼 태그가 없다 |
| 배열 공변성 | 참조 타입 사이에서만 성립. `byte[]`의 상위 타입은 `Object` 하나뿐이고 `Object[]`가 아니다 | `(Object[]) Array.newInstance(byte.class, n)`은 `ClassCastException`. 그래서 캐스팅이 있는 한 원시 배열이 불가능하다 |
| `AnnotationMetadata` | 세 구현(`StandardAnnotationMetadata`=리플렉션, `SimpleAnnotationMetadata`=ASM, `ClassFileAnnotationMetadata`=ClassFile)이 만족해야 하는 하나의 계약 | **불일치가 곧 버그 판정의 근거**였다(4절) |

## 3. 결함 경로 단계 추적

`@ArrayTypesAnnotation(intValue = 3, byteValue = 1)`처럼 선언된 어트리뷰트 두 개를 같은 축으로 따라간다.
셋째 열은 원소가 없는 경우다.

| 단계 | 정상 `int[] intValue()` = `{3}` | 결함 `byte[] byteValue()` = `{1}` | 함정 `byte[] byteValue()` = `{}` |
|---|---|---|---|
| 클래스 파일 태그 | `[` 안에 `I` 하나 | `[` 안에 `B` 하나 | `[` 안에 아무것도 없음 |
| `readAnnotationValue` `:105` | `OfArray` -> `parseArrayValue` | `OfArray` -> `parseArrayValue` | `OfArray` -> `parseArrayValue` |
| `values().isEmpty()` `:111` | false | false | **true -> `return new Object[0]`** `:112` |
| `switch (getFirst())` `:115` | `case OfInt` `:116` | **`default`** `:125` [!] | 도달 안 함 |
| 배열 생성 | `mapToInt(...).toArray()` -> `int[]{3}` | `resolveArrayElementType` -> `Byte.class` `:154` | 해당 없음 |
| 〃 | - | `(Object[]) Array.newInstance(Byte.class, 1)` -> `Byte[]{1}` `:129` | 해당 없음 |
| 파싱 결과 | `int[]{3}` | **`Byte[]{1}`** (예외 없음) | `Object[0]` |
| 소비: `attributeType` `:494` | `int[].class` | `byte[].class` | `byte[].class` |
| 소비: `:517` 빈 배열 구제 | `isEmptyObjectArray` 거짓 | 거짓(길이 1) | **참 -> `emptyArray(byte.class)`** [!] 구제됨 |
| 소비: `:520` `isInstance` | `int[].class.isInstance(int[])` = true | `byte[].class.isInstance(Byte[])` = **false** | 도달 안 함 |
| 최종 | 값 반환 | **`IllegalStateException`** `:521` | 정상 통과 |

세 번째 열이 이 결함의 함정이다. **빈 배열만 시험해 보면 아무 문제가 없어 보인다.**
결함을 재현하려면 반드시 원소가 하나 이상 있어야 하고, 그래서 PR의 두 테스트도 "비어 있지 않은 것"과
"비어 있는 것"을 나눠 두었다(후자는 red가 아니라 함정을 문서화하는 항상 green 가드다).

**타입별 귀결을 한 장으로.** `default` 분기가 흡수하는 원소 타입은 열 가지인데 그중 원시 다섯만 틀린다.

| 어트리뷰트 선언 | base의 분기 | base 결과 | `adaptForAttribute` 결과 |
|---|---|---|---|
| `int[]`, `long[]`, `double[]` | 전용 case | 원시 배열 | 통과 |
| `byte[]`, `short[]`, `char[]` | `default` | `Byte[]`, `Short[]`, `Character[]` | **IllegalStateException** |
| `boolean[]`, `float[]` | `default` | `Boolean[]`, `Float[]` | **IllegalStateException** |
| `String[]`, `Class[]`, enum 배열, 중첩 어노테이션 배열 | `default` | 참조 배열(원래 참조 타입) | 통과 |
| 원소 0개(모든 타입) | 조기 반환 `:112` | `Object[0]` | `:517`이 보정 -> 통과 |

## 4. 계약과 위반 — "의도인가 버그인가"를 무엇으로 판별했나

이 무대에 걸린 계약 넷과, 결함이 그중 무엇을 어기는지를 먼저 표로 세운다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| 어노테이션 어트리뷰트 값의 타입은 **선언 타입과 같다**(`byte[] x()`면 `byte[]`) | `TypeMappedAnnotation.adaptForAttribute` `:520-524`가 런타임에 강제 | 위반. 다섯 타입에서 박싱 배열이 나온다 |
| `AnnotationMetadata`의 세 구현(리플렉션 / ASM / ClassFile)은 **같은 값을 낸다** | 소비 측이 어느 리더인지 모른다는 구조 자체 | 위반. ASM 경로는 같은 어노테이션에서 진짜 원시 배열을 낸다 |
| `readAnnotationValue`는 sealed 계층을 `default` 없이 열거한다 | base `:88-107` | 지켜짐(스칼라 경로). 배열 경로만 `default`를 남겼다 |
| 빈 배열은 선언 타입의 빈 배열로 보정된다 | `TypeMappedAnnotation` `:517-519` | 위반 아님. 다만 이 보정이 결함을 부분적으로 가린다 |

**판별을 옳게 만든 것은 두 가지 근거였다.**

첫째, **같은 계약의 다른 구현**. ASM 리더와 ClassFile 리더는 같은 `AnnotationMetadata` 인터페이스를 만족해야 하고
소비 측은 둘을 구분하지 않는다. 둘의 결과가 다르면 설계자의 의도를 추측할 필요가 없다 — 계약이 하나뿐이므로
둘 중 하나는 반드시 틀렸고, 나중 것이 JDK 24 전용 신규 구현이었으니 틀린 쪽은 명백했다.

둘째, **하위 타입의 비대칭**. `int`/`long`/`double`만 특별 취급하고 `byte`/`short`/`char`/`boolean`/`float`을
빼는 설계 의도는 존재할 수 없다. 규칙이 같은 종류의 원소 일부에만 적용되면 그것은 정책이 아니라 누락이다.

**반대로 의도를 의심해야 하는 신호**도 정리해 둘 만하다. (1) 동작이 javadoc이나 레퍼런스에 문서화되어 있다,
(2) 그 동작을 못 박는 테스트가 있다, (3) 주석이 이유를 설명하고 있다, (4) 같은 결정을 내린 선행 커밋 메시지가 있다.
이 사례에는 넷 중 하나도 없었다. (참고로 PR #37053의 `AbstractNestedMatcher.match(byte)`는 정반대 사례다 —
미스매치 시 리셋하지 않는 것이 버그처럼 보이지만, protected 접근자의 사용처와 형제 구현들이
"되감기는 하위 클래스 몫"이라는 의도를 증명한다. 그래서 그쪽은 base가 아니라 하위 클래스를 고쳤다.)

## 5. 수정안

### 5.1 제안했던 수정 — `default`가 흡수하던 다섯을 전용 case로 끌어낸다

제안한 패치는 기존 세 case 뒤에 다섯 case를 더 얹는 형태였고, `default` 분기 자체는 그대로 두었다.

```java
// before (base 0c60266986, ClassFileAnnotationDelegate.java:115-131)
switch (arrayValue.values().getFirst()) {
	case AnnotationValue.OfInt _ -> {
		return stream.map(AnnotationValue.OfInt.class::cast).mapToInt(AnnotationValue.OfInt::intValue).toArray();
	}
	case AnnotationValue.OfDouble _ -> { ... }
	case AnnotationValue.OfLong _ -> { ... }
	default -> {
		Class<?> arrayElementType = resolveArrayElementType(arrayValue.values(), classLoader);
		return stream
				.map(rawValue -> readAnnotationValue(className, rawValue, classLoader))
				.toArray(length -> (Object[]) Array.newInstance(arrayElementType, length));
	}
}

// after (PR head ec0df00afec) — OfInt/OfDouble/OfLong 뒤, default 앞에 다섯 case 삽입
case AnnotationValue.OfByte _ -> {
	List<AnnotationValue> values = arrayValue.values();
	byte[] result = new byte[values.size()];
	for (int i = 0; i < result.length; i++) {
		result[i] = ((AnnotationValue.OfByte) values.get(i)).byteValue();
	}
	return result;
}
// OfShort / OfChar / OfBoolean / OfFloat 도 같은 형태를 반복 (총 +40줄)
```

**왜 그 형태였나.** `Stream`에는 `mapToByte` 계열이 없다. `IntStream`/`LongStream`/`DoubleStream` 셋만
원시 특수화가 존재하므로, 나머지 다섯은 스트림으로 원시 배열을 만들 수 없고 각 분기가 직접 루프를 돌아야 했다.
기존 세 case가 `mapToInt(...).toArray()` 한 줄인 것과 대비되어 다섯 case가 각각 6줄이 된 이유가 이것이다.

**테스트**: `spring-core/src/test/java24/`에 새 클래스 `ClassFileAnnotationDelegatePrimitiveArrayTests`를 만들고
여덟 원시 배열 어트리뷰트를 가진 `@ArrayTypesAnnotation`을 선언한 뒤, `ClassFileMetadataReaderFactory`로 읽어
값이 원시 배열로 나오는지 확인했다. `parsesNonEmptyPrimitiveArrayAttributes`(red)와
`parsesEmptyPrimitiveArrayAttributes`(항상 green, 함정 문서화) 두 건이다.

**이 형태가 남겨 둔 것**이 결말을 갈랐다. (1) `default` 분기가 그대로 남아, JDK가 sealed 계층에 하위 타입을
추가하면 같은 종류의 누락이 다시 조용히 발생할 수 있다. (2) `resolveArrayElementType`의 `resolvedValue().getClass()`
경로와 `(Object[])` 캐스팅이 손대지 않은 채 남는다. (3) 빈 배열 조기 반환(`:111-113`)도 그대로라,
빈 배열은 여전히 소비 측의 보정에 의존한다.

### 5.2 메인테이너가 거절한 이유와, 그쪽이 고정한 계약

거절 코멘트는 한 줄이다.

> Thanks @junhyeong9812 , this has been addressed in 7de2b24d81c02681c8e8cb764de0690726eb1a8c already.

**시간선.** PR 개설 2026-06-13 -> 39일간 리뷰 없음 -> 2026-07-22 07:57 UTC 외부 사용자 `gsruisch`가
gh-37083 개설(Spring Boot 4 마이그레이션 중 `MetadataReader`로 `byte[]` 어트리뷰트를 읽다 실패,
스택트레이스는 PR 본문의 것과 동일) -> 08:49 UTC 커밋 `7de2b24d81c` -> 08:55 이슈 close ->
2026-08-05 이 PR `declined`. 신고에서 수정까지 한 시간이 채 걸리지 않았다.

**그 커밋이 한 일.** 타입별 분기를 더 추가하는 대신 `parseArrayValue`의 switch를 통째로 지웠다.

```java
// 현재 HEAD, ClassFileAnnotationDelegate.java:109-117
private static Object parseArrayValue(String className, @Nullable ClassLoader classLoader, AnnotationValue.OfArray arrayValue) {
	List<AnnotationValue> values = arrayValue.values();
	Class<?> arrayElementType = (values.isEmpty() ? Object.class : resolveArrayElementType(values, classLoader));
	Object array = Array.newInstance(arrayElementType, values.size());
	for (int i = 0; i < values.size(); i++) {
		Array.set(array, i, readAnnotationValue(className, values.get(i), classLoader));
	}
	return array;
}

// 현재 HEAD, :135-151 — default 가 없다
private static Class<?> resolveArrayElementType(List<AnnotationValue> values, @Nullable ClassLoader classLoader) {
	return switch (values.getFirst()) {
		case AnnotationValue.OfByte _ -> byte.class;
		case AnnotationValue.OfChar _ -> char.class;
		case AnnotationValue.OfDouble _ -> double.class;
		case AnnotationValue.OfFloat _ -> float.class;
		case AnnotationValue.OfInt _ -> int.class;
		case AnnotationValue.OfLong _ -> long.class;
		case AnnotationValue.OfShort _ -> short.class;
		case AnnotationValue.OfBoolean _ -> boolean.class;
		case AnnotationValue.OfString _ -> String.class;
		case AnnotationValue.OfAnnotation _ -> MergedAnnotation.class;
		case AnnotationValue.OfClass _ -> String.class;
		case AnnotationValue.OfEnum enumValue -> loadEnumClass(enumValue, classLoader);
		case AnnotationValue.OfArray _ -> Object.class;
	};
}
```

**그 수정이 고정한 계약 네 가지.**

1. **원소 타입 결정 지점이 하나로 줄었다.** base와 제안 패치는 결정 지점이 둘(`parseArrayValue`의 switch +
   `resolveArrayElementType`)이었는데 HEAD는 하나다. "이 배열의 원소 타입은 무엇인가"에 답하는 코드가 한 곳뿐이다.
2. **`default`가 사라져 컴파일러가 검사자가 되었다.** `AnnotationValue`가 sealed이므로 JDK가 하위 타입을
   추가하면 컴파일이 깨진다. 커밋 메시지가 그 점을 이유로 든다 — "Because the `AnnotationValue` hierarchy
   is sealed, we can now ma[k]e sure that the implementation is exhaustive."
3. **`(Object[])` 캐스팅이 사라져 원시 배열이 원리적으로 가능해졌다.** 반환 타입을 `Object`로 두고
   `Array.newInstance(byte.class, n)`이 진짜 `byte[]`를 만들며, `Array.set`이 박싱된 값을 언박싱해 채운다.
   `readAnnotationValue`는 여전히 박싱된 `Object`를 돌려주지만 배열에 담기는 순간 원시로 풀린다.
4. **빈 배열의 별도 경로가 없어졌다.** 조기 반환 대신 `Object.class`로 길이 0 배열을 만들고 같은 흐름에 합류한다.

**테스트 배치도 달랐다.** 제안 패치는 JDK 24 전용 소스셋에 새 테스트 클래스를 만들어 **한쪽 구현에만** 붙였다.
메인테이너는 `AbstractAnnotationMetadataTests`의 `ComplexAttributes`에 `bytes`/`floats`/`shorts`/`chars`/`booleans`
어트리뷰트를 추가했다. 이 추상 클래스는 `StandardAnnotationMetadataTests`(리플렉션),
`SimpleAnnotationMetadataTests`(ASM), `DefaultAnnotationMetadataTests`가 함께 상속하고,
셋째가 `MetadataReaderFactory.create(...)`를 쓰므로 JDK 24 이상에서 ClassFile 리더를 태운다.
한 곳에 어트리뷰트를 추가하는 것만으로 **세 구현이 동시에 같은 계약으로 검증된다.**

문제를 "구현 간 불일치"로 진단해 놓고 정작 테스트는 한쪽 구현 전용 클래스에 붙인 것이 제안 패치의 모순이었다.
불일치를 근거로 삼았다면 테스트도 불일치를 잴 수 있는 자리에 놓았어야 했다.

**거절의 성격.** 셋 중 어느 것도 아니다 — 의도된 동작이라 반려된 것이 아니고, 범위를 벗어나 반려된 것도 아니며,
구현이 틀렸다고 지적받은 것도 아니다. 결함은 실재했고 메인테이너가 직접 고쳤다. 실제로 제안 패치의 두 테스트는
메인테이너 수정에 대고 돌려도 통과한다. 폐기된 주장이 아니라 **다른 패치로 충족된 주장**이다.

## 6. 범위 밖과 인접 영향

### 6.1 하위 호환

제안 패치도 HEAD 수정도 "예외로 죽던 것이 값을 돌려준다" 방향이므로 계약을 좁히지 않는다.
다만 HEAD 수정에는 관측 가능한 추가 변화가 하나 있다 — **빈 배열의 파싱 결과 자체가 달라진다.**
base는 선언 타입과 무관하게 `Object[0]`을 돌려주고 소비 측이 보정했지만, HEAD는 `Object.class`로 만든
길이 0 배열을 돌려준다. `MergedAnnotation`을 거치지 않고 파싱 결과를 직접 들여다보는 코드가 있다면 차이가 보인다.
그런 소비자가 `spring-core` 안에 있는지는 **미확인**이다.

### 6.2 같은 패턴의 다른 위치

같은 종류의 누락이 다른 곳에도 있는지 확인한 결과, 나머지 경로는 모두 안전하거나 범위 밖이었다.

- **`readAnnotationValue`** `:88-107`: 이미 `default` 없는 sealed switch였다. 스칼라 경로에는 같은 결함이 없다.
- **ASM 경로(`MergedAnnotationMetadataVisitor` 계열)**: 원시 배열을 올바르게 만든다. 이 PR의 판별 근거 자체가
  그 사실이었고, 그래서 그쪽은 손댈 것이 없다.
- **리플렉션 경로(`StandardAnnotationMetadata`)**: 자바 리플렉션이 선언 타입 그대로 돌려주므로 무관.
- **JDK 24 소스셋의 다른 `default` 분기**: HEAD 시점에는 `parseArrayValue`와 `resolveArrayElementType`의
  `default`가 모두 제거되었다. 같은 소스셋의 다른 파일에 남은 `default` switch가 있는지는 **미확인**.

### 6.3 되돌아보기 — 이 PR이 갈린 두 축

**축 하나: 가시성.** 결함이 진짜여도 트리아지 큐에 보이지 않으면 존재하지 않는 것과 같다.
이 PR은 연결된 이슈가 없었고 본문에 `Closes gh-` 참조도 없었다. 39일간 라벨조차 붙지 않았다.
반면 사용자가 실제 마이그레이션 중 막힌 사연과 재현 코드를 이슈로 올리자 한 시간 만에 고쳐졌다.
**재현 코드와 영향받는 실사용 시나리오는 패치 자체만큼 값이 나간다.** 이슈를 먼저 열고 PR을 거기에
연결했다면 최소한 같은 큐에 들어갔을 것이다.

**축 둘: 수정의 층위.** 결함이 한 값에서 났다고 해서 수정이 한 값짜리여야 하는 것은 아니다.
**다섯 타입이 한꺼번에 빠졌다는 사실 자체가 "타입을 손으로 열거하는 구조"가 원인이라는 신호였다.**
그 신호를 읽었다면 옳은 질문은 "빠진 것을 다 채웠나"가 아니라 "다음에 또 빠지는 것을 컴파일러가 막을 수 있나"였을 것이다.
sealed 계층에서 `default`를 지우는 선택이 정확히 그 질문에 대한 답이었고, 재료는 이미 코드 안에 다 있었다 —
`AnnotationValue`가 sealed이고 `readAnnotationValue`가 이미 `default` 없는 exhaustive switch를 쓰고 있었다.

채워 넣는 패치와 지우는 패치의 차이가 이 PR의 결말이었다.
