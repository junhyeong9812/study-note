# PR #37153 — 무대의 실구조와 워크플로우

> PR #37153의 무대가 되는 실구조·워크플로우.\
> 문제·수정은 [README.md](README.md), 테스트는 [tests.md](tests.md), 리뷰 과정은 [review.md](review.md) 참조.
>
> 기준: 로컬 HEAD `526c706d1c3`.\
> 이 시점의 `AttributeMethods.java`는 **수정 전** 상태이므로(플래그 계산식 :84가 base 그대로), 아래 file:line은 그대로 "수정 전 코드"의 좌표다.
>
> 이 문서는 `AttributeMethods`의 **기본 구조** — 플래그 계산, `canLoad`/`validate`, `AnnotationsScanner` 소비처 — 를 담당한다.\
> 같은 무대에 재귀가 얹힌 뒤의 구조와 nested 값 트리 워크플로우는 [`../37157/structure.md`](../37157-nested-annotation-probe/structure.md)를 보라.\
> probe라는 장치 자체의 개념은 [probe-pattern.md](probe-pattern.md)에 있으므로 여기서는 반복하지 않는다.

## 1. 무대 — 실구조

`AttributeMethods`는 annotation 타입 하나당 하나씩 만들어져 캐시되는 **속성 메서드 목록 + 사전 계산된 성질 플래그** 묶음이다.\
이번 PR이 건드리는 것은 그 플래그 중 하나(`canThrowTypeNotPresentException`)의 계산식 한 줄이다.

> **사전 계산된 플래그(precomputed flag)** — 매번 다시 따지지 않으려고 만들 때 한 번 계산해 두는 boolean.\
> 예: "이 속성은 읽는 순간 터질 수 있다"를 속성마다 미리 계산해 `boolean[]`에 담아 둔다.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ final class AttributeMethods                          AttributeMethods.java:41 │
│                                                                             │
│  static IntrospectionFailureLogger failureLogger = WARN          :43        │
│  static AttributeMethods NONE = new AttributeMethods(null, new Method[0]) :45│
│  static Map<Class<? extends Annotation>, AttributeMethods> cache  :47        │
│         (ConcurrentReferenceHashMap — AnnotationUtils.clearCache:1346 이 비움)│
│  static Comparator<Method> methodComparator (이름 오름차순)        :49        │
│                                                                             │
│  Class<? extends Annotation> annotationType (@Nullable)          :57        │
│  Method[]  attributeMethods              ← 이름순 정렬된 속성 메서드 :59      │
│  boolean[] canThrowTypeNotPresentException ← 인덱스별 위험 표시    :61   *    │
│  boolean   hasDefaultValueMethod                                  :63        │
│  boolean   hasNestedAnnotation                                    :65        │
└────────────────────────────────────────────────────────────────────────────┘
        │                                    │
        │ 생성(캐시 미스 시 1회)               │ 소비(매 probe 시)
        v                                    v
  forAnnotationType(type) :256          canLoad(annotation, source)  :102
    └ cache.computeIfAbsent             validate(annotation)         :136
        └ compute(type)   :263            └ 둘 다 canThrowTypeNotPresentException(i) :191
             ├ getDeclaredMethods()         로 게이트하고, 통과한 속성만 실호출
             ├ isAttributeMethod() 필터 :282
             ├ 이름순 정렬 :277
             └ new AttributeMethods(...)  :68  ← 플래그 계산이 여기서 일어난다
```

플래그 셋은 생성자의 단일 루프에서 한꺼번에 계산된다.\
세 줄이 나란히 붙어 있다는 점이 이 PR의 이야기에서 중요하다.

```java
// AttributeMethods.java:74-85 (수정 전)
for (int i = 0; i < attributeMethods.length; i++) {
    Method method = this.attributeMethods[i];
    Class<?> type = method.getReturnType();
    if (!foundDefaultValueMethod && (method.getDefaultValue() != null)) {          // :77
        foundDefaultValueMethod = true;
    }
    if (!foundNestedAnnotation && (type.isAnnotation() ||
            (type.isArray() && type.componentType().isAnnotation()))) {            // :80  ← 스칼라+배열
        foundNestedAnnotation = true;
    }
    ReflectionUtils.makeAccessible(method);                                        // :83
    this.canThrowTypeNotPresentException[i] =
            (type == Class.class || type == Class[].class || type.isEnum());       // :84  ← enum은 스칼라만
}
```

실호출 자체는 이 클래스가 직접 하지 않고 헬퍼를 통한다.\
JDK 동적 프록시면 `InvocationHandler`를 직접 부르고, 실패하면 리플렉션으로 폴백한다.

> **동적 프록시(dynamic proxy)** — 인터페이스만 주면 런타임에 그 인터페이스를 구현한 객체를 만들어 주는 JDK 기능.\
> 예: `@Foo`를 읽으면 JDK가 `Foo` 인터페이스의 프록시 객체를 만들어 주고, 속성 호출은 전부 `InvocationHandler`로 간다.

> **폴백(fallback)** — 먼저 시도한 길이 막혔을 때 대신 타는 두 번째 길.\
> 예: `InvocationHandler.invoke`가 실패하면 평범한 리플렉션 호출(`ReflectionUtils.invokeMethod`)로 다시 시도한다.

```text
AnnotationUtils.invokeAnnotationMethod(Method, Object)          AnnotationUtils.java:1082
   ├ Proxy.isProxyClass(annotation) → handler.invoke(...)   :1086-1090
   └ 아니면 ReflectionUtils.invokeMethod(method, annotation) :1095
```

실패를 알리는 두 출구 중 조용한 쪽(`canLoad`)은 로거를 통해 흔적만 남긴다.

```text
IntrospectionFailureLogger (enum)            IntrospectionFailureLogger.java:33
   ├ DEBUG / INFO / WARN                              :35/:46/:57
   └ log(message, source, ex)                         :72
        (AttributeMethods.failureLogger = WARN :43 — 기본이 경고 수준)
```

## 2. 수정 전 동작 워크플로우

두 단계로 나뉜다.\
annotation **타입**당 한 번 일어나는 플래그 계산, 그리고 annotation **인스턴스**를 만날 때마다 일어나는 probe다.

**단계 1 — 플래그 계산(타입당 1회, 캐시됨).**

```text
어떤 코드가 @Foo 를 처음 만난다
   │
   v
AttributeMethods.forAnnotationType(Foo.class)                    :256
   ├ annotationType == null → NONE 반환                          :257
   └ cache.computeIfAbsent(Foo.class, AttributeMethods::compute)  :260
        │
        └─ compute(Foo.class)                                    :263
             ├ Foo.class.getDeclaredMethods()                    :265
             ├ isAttributeMethod 아닌 것 제거(파라미터 0개 + void 아님) :268/:282
             ├ size == 0 → NONE                                  :274
             ├ Arrays.sort(methods, methodComparator)  ← 이름순 고정 :277
             └ new AttributeMethods(Foo.class, attributeMethods)  :279
                  └ 루프 :74-85
                       for 각 속성:
                         반환 타입 검사 → canThrowTypeNotPresentException[i] 결정 :84
                         ReflectionUtils.makeAccessible(method)                 :83
```

**단계 2 — 스캔 중 probe(인스턴스를 만날 때마다, element 단위 캐시 있음).**\
아래는 단일 enum 속성과 enum 배열 속성이 같은 오염을 어떻게 다르게 통과했는지를 나란히 놓은 것이다.

```text
AnnotationsScanner.getDeclaredAnnotations(source, defensive)   AnnotationsScanner.java:432
   ├ declaredAnnotationCache.get(source) 히트면 그대로 사용        :434
   └ 미스면 source.getDeclaredAnnotations() 로 실제 조회           :439
        │
        └ 각 annotation 마다                                       :442
             isIgnorable(type) || !AttributeMethods
                   .forAnnotationType(type).canLoad(annotation, source)   :445-446
                              │
                              v
        ┌──────────────────── canLoad(annotation, source) :102 ────────────────────┐
        │ for i in 0..size-1:                                                       │
        │    if (!canThrowTypeNotPresentException(i)) → 이 속성은 건너뜀   :105      │
        │    else invokeAnnotationMethod(get(i), annotation)              :107      │
        └───────────────────────────────────────────────────────────────────────────┘

  ── 레인 A: 속성이 `ExampleEnum value()` (단일 enum) ──────────────────
     플래그: type.isEnum() == true            → :84 에서 true
     probe : invoke → EnumConstantNotPresentException 발생
     결과  : catch (Throwable) :113 → warn 로그 :116 → return false :119
             → 스캐너가 annotations[i] = null :447 → 그 annotation 은 "없는 것"

  ── 레인 B: 속성이 `ExampleEnum[] value()` (enum 배열) ── 수정 전 ──────
     플래그: type.isEnum() == false (배열 클래스는 enum 이 아니다)
             type == Class.class / Class[].class 도 아님   → :84 에서 false
     probe : 게이트 :105 에서 걸러져 실호출 자체가 없음
     결과  : 예외를 관측할 기회 없음 → canLoad == true → 스캔 통과
             → 오염된 annotation 이 정상 행세 (README §3 의 세 갈래 누출)
```

두 레인의 갈림은 오직 `:84`의 판정 하나에서 발생하고, 그 뒤의 기계장치(`canLoad`·스캐너·로거)는 완전히 동일하다.\
이 PR이 한 줄 수정으로 충분했던 구조적 이유가 여기 있다.

## 3. 분기 처리 워크플로우

세 개의 분기 묶음이 이 무대를 구성한다.\
첫째가 버그가 살았던 자리다.

```text
[분기 1] 플래그 계산식                                     AttributeMethods.java:84
│
├─ type == Class.class            → true   (스칼라 Class)
├─ type == Class[].class          → true   (배열 Class — 배열까지 다룬다)
├─ type.isEnum()                  → true   (스칼라 enum)
└─ 그 외                           → false
      └ ExampleEnum[] 이 여기로 떨어진다                    * 버그 분기
        (수정 후 추가되는 가지: type.isArray() && type.componentType().isEnum())

   - 비교: 바로 윗줄 :80 의 nested annotation 검사는
     type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation())
     로 이미 배열까지 다루고 있었다 — 같은 생성자 안의 비대칭
```

```text
[분기 2] probe 결과 처리 — 두 소비자가 다르게 갈린다

canLoad(annotation, source)  :102              validate(annotation)  :136
│                                              │
├ 플래그 false → 건너뜀            :105         ├ 플래그 false → 건너뜀            :139
└ 플래그 true → invoke  :107                   └ 플래그 true → invoke  :141
     ├ 정상 반환 → 계속 (반환값은 버림)              ├ 정상 반환 → 계속
     ├ catch IllegalStateException :109             ├ catch IllegalStateException :143
     │    → 삼킴(주석: 값 조회 시점에 로깅됨)          │    → 그대로 재던짐 :144
     └ catch Throwable :113                          └ catch Throwable :146
          → failureLogger.log(...) :116                   → IllegalStateException 으로 감싸
          → return false :119                               (원인은 cause 로 보존) :147-149
│                                              │
└ 전부 통과 → return true :123                  └ 전부 통과 → 정상 종료
```

> **조용한 출구 / 시끄러운 출구** — 같은 검사를 돌리되 실패를 boolean으로 알리느냐 예외로 알리느냐의 차이.\
> 예: `canLoad`는 false를 돌려주고 끝내지만, `validate`는 `IllegalStateException`을 던져 호출자를 멈춰 세운다.

```text
[분기 3] 스캐너가 canLoad 결과를 소비하는 방식      AnnotationsScanner.java:442-464
│
├ isIgnorable(type) (java.lang.annotation 계열 필터) :445/:467
│      또는 !canLoad(...)                            :446
│          → annotations[i] = null   (그 자리를 비운다)  :447
├ 하나라도 살아남으면 allIgnored = false               :450
├ 전부 걸러졌으면 annotations = NO_ANNOTATIONS         :453
├ source 가 Class 또는 Member 면 declaredAnnotationCache 에 저장 :454-457
└ defensive 요청이고 캐시된 배열이면 clone() 반환        :461-464
```

분기 3의 캐시가 probe 비용의 반복 빈도를 제한한다 — 같은 element를 다시 스캔하면 실호출 없이 앞선 판정 결과를 재사용한다.\
다만 캐시 미스마다 probe는 다시 일어난다.

## 4. 스프링 전역에서의 자리

이 코드는 Spring의 **annotation 스캔 파이프라인 최하단 게이트**다.\
위쪽 어느 기능에서 출발하든 "선언된 annotation을 실제로 읽는" 순간에는 아래 한 지점을 지난다.

> **메타-annotation(meta-annotation)** — annotation 위에 또 붙어 있는 annotation.\
> 예: `@Service` 선언부에 `@Component`가 붙어 있어서, `@Service`를 찾으면 `@Component`도 따라 나온다.

```text
[MergedAnnotations 계열 — 컴포넌트 스캔, 조건 평가, AOP 포인트컷, 테스트 컨텍스트 등]
   MergedAnnotations.from(element, ...)
      └ TypeMappedAnnotations.java:242  AnnotationsScanner.scan(criteria, element, ...)
           └ AnnotationsScanner.java:79 scan → :86 process
                ├ :99  processClass → :110 processClassInheritedAnnotations → :126
                ├ :165/:173 processClassHierarchy                            → :185
                ├ :235 processMethod → :261 processMethodHierarchy           → :338
                ├ :385 processMethodAnnotations                              → :388/:395
                └ :406 processElement                                        → :412
                        └ 전부 getDeclaredAnnotations(source, ...)  :432
                              └ :446  AttributeMethods.forAnnotationType(...).canLoad(...)  *

[메타-annotation 그래프 탐색]
   AnnotationTypeMappings.java:93  AnnotationsScanner.getDeclaredAnnotations(annotationType, false)
        → annotation 위에 붙은 annotation 을 훑을 때도 같은 게이트를 지난다
        → 즉 오염된 메타-annotation 역시 여기서 걸러진다
        (canLoad 의 warn 메시지가 "Failed to introspect meta-annotation @..." :116 인 이유)

[AliasFor 해석]
   AnnotationTypeMapping.java:119/:319  AnnotationsScanner.getDeclaredAnnotation(attribute, AliasFor.class)
        └ AnnotationsScanner.java:421 → :422 getDeclaredAnnotations(...)  → 같은 게이트

[시끄러운 출구 — @Configuration 클래스 파싱]
   ConfigurationClassParser.java:688-692
        for (Annotation ann : classType.getDeclaredAnnotations())
            AnnotationUtils.validateAnnotation(ann);        AnnotationUtils.java:775
                 └ AttributeMethods.forAnnotationType(...).validate(annotation)  :776  *
        catch (Throwable) → asSourceClass(classType.getName(), filter)
        - 리플렉션으로 읽을 수 없는 클래스는 ASM 기반 파싱으로 폴백한다.
          여기서 validate 가 던지는 IllegalStateException 이 그 폴백의 트리거다.
```

> **ASM 파싱** — 클래스를 JVM에 로드하지 않고 바이트코드 파일 자체를 읽어 정보를 뽑는 방식.\
> 예: 리플렉션으로 읽으면 터지는 `@Configuration` 클래스라도, 바이트코드만 훑으면 어떤 annotation이 붙었는지는 알 수 있다.

플래그의 다른 소비자 둘도 같은 클래스에서 갈라진다(이 PR의 변경과는 무관하지만, 플래그 필드들이 어떤 결정에 쓰이는지를 보여 준다).

```text
hasNestedAnnotation()   :246 ─→ AnnotationTypeMapping.java:279  synthesizable 여부 계산
                              ─→ AnnotationUtils.java:917       기본값 맵 계산 경로 선택
hasDefaultValueMethod() :237 ─→ AnnotationUtils.java:913        기본값이 없으면 빈 맵 지름길
```

정리하면, 이 게이트가 잘못 판정하면 그 영향은 특정 기능이 아니라 **annotation을 읽는 모든 상위 기능**에 균일하게 퍼진다.\
컴포넌트 스캔이 빈을 못 찾거나, `@Qualifier` 매칭이 어긋나거나, 조건 평가가 다르게 도는 식이다.

## 5. 관련 개념

이 무대를 이해하는 데 필요한 개념 넷은 이미 같은 폴더/개념 폴더에 있으므로 링크로 대신한다.

- [probe(사전 시험 호출) — 하나의 검사, 두 개의 출구](probe-pattern.md) — 위 [분기 2]의 두 출구가 왜 그렇게 설계됐는지.
- [annotation의 enum 값은 이름으로 저장되고, 읽는 순간 해석된다](enum-annotation-name-resolution.md) — probe가 성립하는 전제(지연 실패).
- [classpath 버전 스큐](classpath-version-skew.md) — 오염된 annotation이 애초에 왜 생기는지.
- [JDK의 annotation 동작 방식 vs Spring의 동작 방식](jdk-vs-spring-annotation-handling.md) — 이 게이트가 JDK 계약 위에 무엇을 덧씌우는지.

추가로 이 문서의 구조에서만 드러나는 성질 하나를 적어 둔다.\
**플래그는 타입당 1회, probe는 인스턴스마다**라는 비대칭이다.\
계산식(:84)을 바꾸는 비용은 annotation 타입 수에 비례해 한 번뿐이지만, 그 결과로 늘어나는 probe는 스캔되는 element 수에 비례한다.

두 축이 각각 어떤 캐시에 눌려 있는지를 나란히 놓으면 이렇다.

```text
축 1 — 플래그 계산                        축 2 — probe 실호출
+---------------------------------+        +--------------------------------+
| 단위 : annotation 타입 1개      |        | 단위 : element 1개 x 속성      |
| 횟수 : 타입당 1회               |        | 횟수 : 캐시 미스마다 다시      |
| 캐시 : AttributeMethods.cache   |        | 캐시 : declaredAnnotationCache |
|        :47                      |        |        :55                     |
| 이번 fix 가 바꾼 것 : 판정식    |        | 이번 fix 가 바꾼 것 : 대상 수  |
+---------------------------------+        +--------------------------------+
  -> 한 번 잘못 계산되면 캐시에            -> probe 하나가 늘면 스캔하는
     그 값이 그대로 눌러앉는다                element 수만큼 곱해서 늘어난다
```

`AttributeMethods.cache`(:47)가 전자를, `AnnotationsScanner.declaredAnnotationCache`(:55)가 후자를 각각 제한한다 — 캐시 두 개가 서로 다른 축을 맡고 있다.
