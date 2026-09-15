# PR #37109 — 무대의 실구조와 워크플로우

> PR #37109의 무대가 되는 실구조·워크플로우. 문제·수정은 [README.md](README.md), 테스트는 [tests.md](tests.md) 참조.
>
> 기준: 로컬 HEAD `526c706d1c3`. 이 시점의 `TypeDescriptor.java`는 아직 PR #37109가 적용되지 않은 **수정 전** 상태이므로, 아래 file:line은 그대로 "수정 전 코드"의 좌표다.

## 1. 무대 — 실구조

`TypeDescriptor`는 필드 넷을 가진 값 객체이고, 그중 애너테이션을 담당하는 둘이 이번 PR의 무대다.\
나머지 둘(`type`, `resolvableType`)은 이미 직렬화를 감당하도록 오래전에 정리된 영역이라 이 PR이 건드리지 않는다.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ TypeDescriptor implements Serializable          TypeDescriptor.java:56  │
│                                                                          │
│  Class<?> type                       :72   ← 직렬화 가능 (Class)          │
│  ResolvableType resolvableType       :74   ← SerializableTypeWrapper가    │
│                                              내부 Type을 프록시로 감쌈     │
│  AnnotatedElementSupplier                                                │
│      annotatedElementSupplier        :76   ← final, transient 아님        │
│  volatile AnnotatedElementAdapter                                        │
│      annotatedElement                :78   ← 지연 캐시, transient 아님    │
└─────────────────────────────────────────────────────────────────────────┘
        │                                        │
        │ 공급자 인터페이스                        │ 캐시가 가리키는 값
        v                                        v
┌───────────────────────────────────┐   ┌──────────────────────────────────┐
│ interface AnnotatedElementSupplier │   │ AnnotatedElementAdapter          │
│   extends Supplier<...>,           │   │   implements AnnotatedElement,   │
│           Serializable      :730   │   │              Serializable        │
│                                    │   │   AnnotatedElementAdapter.java:38│
│ (private nested interface —        │   │                                  │
│  람다 하나만 담는 자리)             │   │  static EMPTY            :40     │
└───────────────────────────────────┘   │  Annotation[] annotations :63    │
                                        │  static from(Annotation[]) :55   │
                                        │  getAnnotations()          :92   │
                                        │  isEmpty()                 :110  │
                                        └──────────────────────────────────┘
```

> **volatile(볼러틸)** — 한 스레드가 쓴 값이 다른 스레드에 곧바로 보이도록 보장하는 자바 필드 수식어.\
> 예: `annotatedElement` 지연 캐시는 여러 스레드가 동시에 읽으므로 `volatile`로 선언돼 있다.

공급자 필드에 무엇이 들어가는지는 **어느 생성자를 탔는가**로 완전히 결정된다.\
생성자 넷이 각각 다른 것을 캡처한다.

```text
TypeDescriptor(MethodParameter)  :87   supplier = () -> from(mp.getParameterAnnotations()
                                                       또는 mp.getMethodAnnotations())   → MethodParameter 캡처
TypeDescriptor(Field)            :99   supplier = () -> from(field.getAnnotations())     → Field 캡처
TypeDescriptor(Property)         :111  supplier = () -> from(property.getAnnotations())  → Property 캡처
TypeDescriptor(ResolvableType,
               Class, Annotation[]) :128  supplier = () -> from(annotations)             → Annotation[] 캡처
```

앞의 셋은 리플렉션/맥락 객체를 붙잡고, 넷째만 이미 직렬화 가능한 배열을 붙잡는다.\
그리고 파생 디스크립터를 만드는 내부 경로들은 전부 넷째 생성자로 수렴한다 — `narrow(Object)`:218, `upcast(Class)`:234, `getElementTypeDescriptor()`:370, `getRelatedIfResolvable(ResolvableType)`:477, `array(TypeDescriptor)`:641, `valueOf(Class)`:575가 그것이다.\
즉 파생 디스크립터의 공급자는 **원본의 애너테이션 배열을 이미 조회한 결과**를 캡처한다(`getAnnotations()`를 인자로 넘기므로).

> **파생 디스크립터(derived descriptor)** — 이미 있는 디스크립터에서 한 단계 들어가 만든 새 디스크립터.\
> 예: `Map<K, V>`를 서술한 디스크립터에 `getMapValueTypeDescriptor()`를 부르면 값 타입 `V`의 디스크립터가 파생된다.

애너테이션을 실제로 읽는 표면은 세 개뿐이고, 셋 다 지연 캐시 하나를 통과한다.

```text
getAnnotations()      :269 ┐
hasAnnotation(Class)  :280 ├─→ getAnnotatedElement() :256 ─→ (캐시 null이면) supplier.get()
getAnnotation(Class)  :296 ┘                                  → this.annotatedElement 에 저장
```

같은 문제를 이미 푼 선례가 같은 모듈 안에 있다.\
`ResolvableType`이 품는 `java.lang.reflect.Type`은 직렬화 불가능하지만, `SerializableTypeWrapper`의 provider들이 리플렉션 객체를 `transient`로 빼고 `readObject()`에서 되찾는다.

```text
SerializableTypeWrapper.java
  FieldTypeProvider                :229   transient Field field        :235   readObject() :253
  MethodParameterTypeProvider      :269   transient MethodParameter    :279   readObject() :299
  MethodInvokeTypeProvider         :322   transient Method method      :332   readObject() :361
```

마지막으로, 이 클래스가 실제로 스트림을 타는 통로는 변환 예외 두 개다.\
둘 다 필드가 `transient`가 아니다.

```text
ConversionFailedException.java:33   @Nullable TypeDescriptor sourceType
ConversionFailedException.java:35   TypeDescriptor targetType
ConverterNotFoundException.java:32  @Nullable TypeDescriptor sourceType
ConverterNotFoundException.java:34  TypeDescriptor targetType
```

## 2. 수정 전 동작 워크플로우

두 시나리오를 따라가면 구조가 왜 그 결과를 내는지가 드러난다.\
하나는 정상 동작(지연 조회), 다른 하나가 이 PR이 겨냥한 실패(직렬화)다.

**시나리오 A — 필드에서 만들어 애너테이션을 읽기까지.**\
생성자는 애너테이션을 건드리지 않고, 첫 조회에서만 리플렉션이 일어난다.

```text
new TypeDescriptor(field)                                    TypeDescriptor.java:99
   │
   ├─ resolvableType = ResolvableType.forField(field)              :100
   ├─ type = resolvableType.resolve(field.getType())               :101
   └─ annotatedElementSupplier = () -> from(field.getAnnotations()) :102
          (람다 생성만 — field.getAnnotations()는 아직 호출 안 됨)
   │
   v  (한참 뒤, 어떤 컨버터가)
td.getAnnotations()                                                :269
   └─ getAnnotatedElement()                                        :256
        ├─ this.annotatedElement == null ?  → yes (첫 호출)
        ├─ supplier.get() ─→ field.getAnnotations()  ← 여기서 처음 리플렉션
        │      └─ AnnotatedElementAdapter.from(...)   AnnotatedElementAdapter.java:55
        │            ├─ null 또는 length==0 → EMPTY 싱글톤 반환      :57
        │            └─ 그 외 → new AnnotatedElementAdapter(anns)    :59
        └─ this.annotatedElement = 어댑터 (이후 호출은 캐시 히트)
   └─ 어댑터.getAnnotations()                                       :92
        └─ isEmpty() ? 배열 그대로 : 배열.clone()  ← 방어적 복사
```

**시나리오 B — 그 디스크립터를 직렬화하려 할 때(수정 전).**\
`TypeDescriptor`에는 `writeObject`/`readObject`가 없으므로 기본 직렬화가 필드 넷을 그대로 훑는다.

> **기본 직렬화(default serialization)** — 클래스가 훅을 정의하지 않았을 때 JDK가 대신 수행하는 동작. `transient`가 아닌 모든 필드를 차례로 스트림에 쓴다.\
> 예: `TypeDescriptor`에는 훅이 없어서 필드 4개가 그대로 순회된다.

```text
ObjectOutputStream.writeObject(td)
   │
   └─ 기본 직렬화: TypeDescriptor의 non-transient 필드 4개를 순회
        │
        ├─ type            : Class            → OK
        ├─ resolvableType  : ResolvableType   → OK (SerializableTypeWrapper가 처리)
        ├─ annotatedElement: AnnotatedElementAdapter 또는 null
        │      → null이면 그냥 null이 나감 (애너테이션 미조회 상태였다면)
        │      → 값이 있으면 Annotation[] 이 직렬화됨
        │
        └─ annotatedElementSupplier : Serializable 람다
               → 자바가 SerializedLambda 로 변환
               → SerializedLambda 는 "캡처된 인자"를 함께 씀
               → 캡처된 인자 = java.lang.reflect.Field
                      │
                      v
               java.io.NotSerializableException: java.lang.reflect.Field
```

핵심은 두 필드가 **서로 보완하지 않는다**는 점이다.\
캐시(`annotatedElement`)가 채워져 있어도 공급자 필드는 여전히 스트림에 쓰이고, 그래서 애너테이션을 미리 조회해 두어도 실패는 동일하다.\
반대로 공급자가 없으면 캐시가 `null`인 채 나가 애너테이션이 사라진다 — 이 대칭이 PR이 `writeObject()`에서 조회를 강제하는 이유다(README §4).

네 조합을 한 판에 놓으면 왜 한 칸만 답이 되는지가 보인다.

```text
                     공급자가 스트림에 실린다        공급자가 transient 로 빠진다
                     (수정 전)                      (수정 후)
                  +----------------------------+ +----------------------------+
 캐시가 null      | Field 캡처가 실려 폭발       | | 애너테이션이 조용히 소실    |
 (아무도 안 물음) | NotSerializableException   | | 예외 없이 값만 잃는다        |
                  +----------------------------+ +----------------------------+
 캐시가 채워짐    | Field 캡처가 실려 폭발       | | 성공, 애너테이션 보존       |
 (미리 조회함)    | 미리 조회해도 결과 같다      | | <- writeObject 가 만드는 칸 |
                  +----------------------------+ +----------------------------+
```

그림이 말하는 것 하나 — `transient` 하나만으로도, 조회 강제 하나만으로도 답이 안 되고 둘이 같이 있어야 오른쪽 아래 칸에 도달한다.

## 3. 분기 처리 워크플로우

이 무대의 분기는 셋으로 갈린다.\
생성자 선택 분기, 어댑터 생성 분기, 그리고 조회 지름길 분기다.\
버그가 살았던 곳은 첫 번째다.

```text
[분기 1] 어느 생성자로 만들어졌나 → 공급자가 무엇을 캡처하나 → 직렬화 성패
│
├─ (MethodParameter)  :87  ─ 캡처: MethodParameter ─→ 직렬화 X  ← 버그 분기
├─ (Field)            :99  ─ 캡처: Field           ─→ 직렬화 X  ← 버그 분기
├─ (Property)         :111 ─ 캡처: Property        ─→ 직렬화 X  ← 버그 분기
└─ (ResolvableType,
    Class, Annotation[]) :128 ─ 캡처: Annotation[] ─→ 직렬화 OK
        ^
        └── valueOf(Class):575 · narrow():218 · upcast():234 ·
            getElementTypeDescriptor():370 · getRelatedIfResolvable():477 ·
            array():641  ← 파생 경로는 전부 여기로 수렴
```

기존 테스트 `serializable()`이 회귀를 못 잡은 이유가 이 분기도에 그대로 보인다.\
`TypeDescriptor.forObject("")`:561 -> `valueOf(String.class)`:575 -> 넷째 생성자, 즉 유일하게 성한 가지만 밟는다.

```text
[분기 2] AnnotatedElementAdapter.from(annotations)     AnnotatedElementAdapter.java:55
│
├─ annotations == null  ─┐
├─ annotations.length==0 ─┴→ EMPTY 싱글톤 반환 :57   ← 정체성(==)이 의미를 갖는 가지
└─ 그 외                   → new 인스턴스 :59

[분기 3] 조회 지름길 — isEmpty()가 참이면 AnnotatedElementUtils를 아예 안 부른다
│
├─ hasAnnotation(Class) :280 ─ annotatedElement.isEmpty() ? false 즉시반환 : isAnnotated(...)
├─ getAnnotation(Class) :296 ─ annotatedElement.isEmpty() ? null 즉시반환  : getMergedAnnotation(...)
└─ 어댑터.getAnnotations() :92 ─ isEmpty() ? 원본 배열 그대로 : clone()
       │
       └─ isEmpty()는 값 비교가 아니라 `this == EMPTY` 동일성 비교  :110
             → 역직렬화로 복원된 빈 어댑터는 EMPTY가 아니게 되어
               세 지름길이 모두 죽는다 (PR이 readObject에서 from(...)을 다시 태우는 이유)
```

> **지름길(fast path)** — 흔한 경우를 먼저 알아채고 비싼 일반 처리를 건너뛰는 분기.\
> 예: 애너테이션이 하나도 없으면 `hasAnnotation()`이 `AnnotatedElementUtils`를 아예 부르지 않고 즉시 `false`를 준다.

> **싱글턴(singleton)** — 인스턴스가 딱 하나만 존재하도록 만든 객체.\
> 예: `AnnotatedElementAdapter.EMPTY`는 "애너테이션 없음"을 뜻하는 단 하나의 공유 인스턴스다.

한편 `equals()`:494는 `annotationsMatch()`:511을 거쳐 애너테이션 배열까지 비교하므로, 왕복이 애너테이션을 잃으면 동등성부터 깨진다.\
즉 "직렬화 성공"과 "애너테이션 보존"은 이 클래스에서 분리된 관심사가 아니다.

## 4. 스프링 전역에서의 자리

`TypeDescriptor`는 변환 서비스의 좌표계이므로, 문제의 세 생성자는 프레임워크 전역에서 불린다.\
아래는 grep으로 확인한 main 소스의 실제 진입점들이다(테스트 제외).

```text
[빈 프로퍼티 바인딩]
  BeanWrapperImpl.java:248/255/290                → new TypeDescriptor(MethodParameter/...)
  GenericTypeAwarePropertyDescriptor.java:195-196 → new Property(...) → new TypeDescriptor(property)
  TypeConverterSupport.java:52/60                 → new TypeDescriptor(methodParam) / (field)
  DirectFieldAccessor.java:115/125/131            → 넷째 생성자 (직렬화 안전 경로)

[의존성 주입]
  DependencyDescriptor.java:286-287               → (ResolvableType,...) 또는 (MethodParameter)

[SpEL]
  ReflectivePropertyAccessor.java:153/197/255     → new TypeDescriptor(property)
  ReflectivePropertyAccessor.java:162/220/265/569 → new TypeDescriptor(field)
  ReflectiveMethodExecutor.java:115 · FunctionReference.java:148
  ReflectionHelper.java:279/289/297 · ReflectiveMethodResolver.java:170
  ReflectiveConstructorResolver.java:77           → new TypeDescriptor(MethodParameter)

[데이터 매핑]
  SimplePropertyRowMapper.java:120/156/163 · DataClassRowMapper.java:102 (jdbc)
  DataClassRowMapper.java:95 (r2dbc)              → new TypeDescriptor(MethodParameter/Field)

[웹·메시징 인자 변환]
  messaging AbstractNamedValueMethodArgumentResolver.java:108(reactive)/116(support)
  web AbstractNamedValueArgumentResolver.java:195 · RequestParamMethodArgumentResolver.java:256
  webmvc PathVariableMethodArgumentResolver.java:136 · ServletModelAttributeMethodProcessor.java:138
```

그러나 이 진입점들이 곧바로 직렬화를 유발하지는 않는다.\
디스크립터가 실제로 스트림을 타는 통로는 **변환 예외에 실려 나가는 경로** 하나다.

```text
GenericConversionService.convert(...)  ─ 컨버터 없음/변환 실패
        │
        ├─→ throw new ConverterNotFoundException(sourceType, targetType)
        │        └ 필드 :32/:34 — transient 아님
        └─→ throw new ConversionFailedException(sourceType, targetType, value, cause)
                 └ 필드 :33/:35 — transient 아님
        │
        v
  이 예외가 원격 호출·세션 복제 등 직렬화 경계를 넘는 순간
  → 안에 담긴 TypeDescriptor 도 직렬화 대상이 된다
  → 위 [분기 1]의 세 가지 중 하나였다면 NotSerializableException
```

즉 전역에서의 자리는 "변환의 좌표계"이자 "예외에 실려 프로세스 경계를 넘는 값 객체"다.\
앞의 역할은 3.0부터 변함이 없고, 뒤의 역할이 이 PR이 복구하려는 계약이다.

## 5. 관련 개념

**선언 메타데이터를 읽는 런타임.**\
`TypeDescriptor`가 `Class` 하나로 부족한 이유 — 제네릭·애너테이션이 어느 층에 살아 있는가 — 는 [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)가 다룬다.\
이 문서는 그 위에서 "그 카드를 어떻게 들고 다니느냐"만 본다.

**직렬화 가능한 람다와 캡처.**\
`Serializable`을 상속한 함수형 인터페이스(:730)의 람다는 `SerializedLambda`로 직렬화되는데, 이 표현은 람다가 캡처한 인자를 **함께** 쓴다.\
그래서 인터페이스에 `Serializable`을 붙이는 것은 "이 자리를 스트림에 쓰겠다"는 선언일 뿐, 캡처 내용물의 직렬화 가능성은 보장하지 않는다.\
컴파일러는 캡처 대상을 검사하지 않으므로 실패는 전부 런타임으로 미뤄진다.

> **함수형 인터페이스(functional interface)** — 추상 메서드가 딱 하나뿐이라 람다로 구현할 수 있는 인터페이스.\
> 예: `AnnotatedElementSupplier`는 `Supplier`의 `get()` 하나만 가지므로 `() -> ...` 한 줄로 채워진다.

**transient + 재구성 패턴.**\
같은 상황의 정답이 같은 모듈에 이미 있다: 리플렉션 객체를 `transient`로 빼고, 그것을 되찾을 재료(이름·선언 클래스)만 스트림에 실은 뒤 `readObject()`에서 복원한다(`SerializableTypeWrapper.FieldTypeProvider`:229/235/253).\
PR #37109는 같은 패턴을 적용하되, 되찾을 재료가 "리플렉션 객체를 다시 찾는 좌표"가 아니라 "이미 조회해 둔 애너테이션 배열"이라는 점만 다르다.

같은 패턴의 두 적용을 나란히 놓으면 차이가 한 줄로 좁혀진다.

```text
SerializableTypeWrapper.FieldTypeProvider     PR #37109 의 TypeDescriptor
+--------------------------------------+      +--------------------------------------+
| transient Field field                |      | transient AnnotatedElementSupplier    |
|   -> 스트림에 안 나간다               |      |   -> 스트림에 안 나간다                |
| String  fieldName       <- 싣는다     |      | AnnotatedElementAdapter               |
| Class<?> declaringClass <- 싣는다     |      |     annotatedElement    <- 싣는다      |
+--------------------------------------+      +--------------------------------------+
  readObject: 이름으로 Field 를 다시 찾음        readObject: 배열로 어댑터를 다시 만듦
  싣는 재료 = "다시 찾을 좌표"                   싣는 재료 = "이미 조회해 둔 결과"
```

그림이 말하는 것 하나 — 패턴은 같고, 무엇을 재료로 싣느냐만 다르다.

**싱글톤 정체성이 의미를 갖는 값 객체.**\
`AnnotatedElementAdapter.EMPTY`(:40)는 `isEmpty()`(:110)가 `this == EMPTY`로 판정하기 때문에, 값이 같은 다른 인스턴스로 대체되면 조용히 성능 특성이 바뀐다(위 [분기 3]).\
이런 타입에는 보통 `readResolve()`가 필요한데 이 어댑터에는 없고, 그래서 복원 책임이 소유자 쪽으로 넘어온다.
