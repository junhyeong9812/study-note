# PR #37109 분석 — TypeDescriptor 직렬화 회귀의 메서드 그래프와 이름표

> 기준 커밋: 결함 상태 = `e8729d04388`(PR 베이스, upstream main), 수정 상태 = `f92313cc3e1`(PR head). 아래 file:line 은 별도 표기가 없으면 **결함 상태(베이스)** 좌표이고, 5절의 after 스니펫만 PR head 좌표다.
> 이 문서의 역할: [README.md](README.md)가 서사를, [structure.md](structure.md)가 무대의 지도를, [tests.md](tests.md)가 테스트를 맡는다. 여기서는 **호출 그래프 위의 데이터 흐름**과 **이름표 하나하나의 정체**, 그리고 정상/결함 케이스의 **단계별 변수 값**만 다룬다.

> **호출 그래프(call graph)** — 어느 메서드가 어느 메서드를 부르는지를 이어 놓은 지도.\
> 예: 생성자 → 람다 생성 → `getAnnotatedElement()` → `supplier.get()`이 이 무대의 한 갈래다.

## 0. 결론

**결함**: `TypeDescriptor`의 `annotatedElementSupplier` 필드가 `transient`가 아니라서, 기본 직렬화가 그 자리에 담긴 람다를 `SerializedLambda`로 바꾸며 **람다가 캡처한 `Field`/`MethodParameter`/`Property`까지 스트림에 쓰려 하고**, 셋 다 비직렬화라 `NotSerializableException`으로 끝난다(`TypeDescriptor.java:76`, 캡처는 `:87`·`:99`·`:111`).

**수정**: 그 필드를 `transient`로 바꿔 스트림에서 빼고, `writeObject()`가 쓰기 직전에 애너테이션 조회를 한 번 강제해 이미 직렬화 가능한 `AnnotatedElementAdapter`가 대신 실려 가게 하며, `readObject()`가 `AnnotatedElementAdapter.from(...)`을 다시 태워 `EMPTY` 싱글턴 동일성과 공급자 필드를 복원한다(PR head `TypeDescriptor.java:79`, `:733-746`).

**상태**: OPEN, `status: waiting-for-triage` + `in: core`, 2026-08-04 제출, 리뷰어 미배정(2026-08-27 확인).

> **비직렬화(non-serializable)** — `Serializable`을 구현하지 않아 스트림에 쓸 수 없는 타입.\
> 예: `java.lang.reflect.Field`는 JDK가 직렬화를 지원하지 않으므로 쓰려는 순간 예외가 난다.

## 1. 무대 — 어디의 무엇인가

무대는 한 클래스와 그 협력자 둘이며, 결함이 실제로 드러나는 통로는 변환 예외 하나다.

- 모듈·파일: `spring-core` / `spring-core/src/main/java/org/springframework/core/convert/TypeDescriptor.java`
- 협력 클래스: `org.springframework.core.annotation.AnnotatedElementAdapter`(같은 모듈, 7.0 신설), `org.springframework.core.ResolvableType`(제네릭 담당, 이미 직렬화 가능)
- 공개 진입 API: 생성자 넷 — `TypeDescriptor(MethodParameter)`:87 / `TypeDescriptor(Field)`:99 / `TypeDescriptor(Property)`:111 / `TypeDescriptor(ResolvableType, Class, Annotation[])`:128.\
  그리고 애너테이션 표면 셋 — `getAnnotations()`:269 / `hasAnnotation(Class)`:280 / `getAnnotation(Class)`:296.
- 누가 부르나: 빈 프로퍼티 바인딩(`BeanWrapperImpl`), DI(`DependencyDescriptor`), SpEL(`ReflectivePropertyAccessor`), 웹·메시징 인자 변환 등 — 전역 호출 지도는 [structure.md](structure.md) 4절이 정본이다.
- 언제 직렬화되나: 이 클래스를 **직접** 스트림에 쓰는 프레임워크 코드는 없다.\
  실제 통로는 `ConversionFailedException`(:33/:35)·`ConverterNotFoundException`(:32/:34)이 `TypeDescriptor`를 비-transient 필드로 들고 프로세스 경계를 넘는 경우다.\
  즉 결함은 "변환 실패 예외를 원격으로 던지거나 세션에 복제할 때" 처음 드러난다.

> **프로세스 경계(process boundary)** — 한 JVM 안에서 끝나지 않고 다른 프로세스·다른 장비로 객체가 넘어가는 지점.\
> 예: 원격 호출로 예외를 던지거나, 세션을 옆 서버로 복제할 때 그 경계를 지난다.

## 2. 전체 메서드 그래프 — 진입점부터 결함 지점까지

두 갈래를 하나의 그림으로 놓으면 결함이 "두 필드가 서로를 보완하지 않는다"는 한 문장으로 보인다.\
왼쪽은 애너테이션을 읽는 정상 경로, 오른쪽이 직렬화 경로다.

```text
[생성]
 new TypeDescriptor(field)                               TypeDescriptor.java:99
   |-- resolvableType = ResolvableType.forField(field)          :100
   |-- type           = resolvableType.resolve(...)             :101
   `-- annotatedElementSupplier = () -> AnnotatedElementAdapter.from(field.getAnnotations())   :102
            (람다 객체만 생성. field.getAnnotations() 는 아직 호출 안 됨.
             람다는 자유변수 field 를 캡처한다 -> 이 캡처가 결함의 씨앗)

[읽기 경로 — 정상]                          [직렬화 경로 — 결함]
 getAnnotations()        :269                ObjectOutputStream.writeObject(td)
 hasAnnotation(Class)    :280                  |
 getAnnotation(Class)    :296                  |  TypeDescriptor 에 writeObject 훅 없음
   |                                           v
   `--> getAnnotatedElement()      :256      defaultWriteObject 상당 경로
          |  캐시 hit?  -> 반환                  |  non-transient 필드 4개를 이름 오름차순으로
          |  miss ->                             |  (annotatedElement, annotatedElementSupplier,
          `-- supplier.get()                     |   resolvableType, type)  실측 확인
                |                                v
                `-- field.getAnnotations()      [1] annotatedElement        -> null 또는 어댑터, OK
                      |                          [2] annotatedElementSupplier
                      `-- AnnotatedElementAdapter.from(anns)                 |
                            AnnotatedElementAdapter.java:55                  |  선언 타입이 Serializable 이므로
                              |-- null/length 0 -> EMPTY 반환   :57          |  JDK 가 SerializedLambda 로 치환
                              `-- else -> new AnnotatedElementAdapter :59    |
                                                                             v
                                                                   SerializedLambda.capturedArgs[0]
                                                                             = java.lang.reflect.Field
                                                                             v
                                                            NotSerializableException:
                                                              java.lang.reflect.Field       [결함 지점]
                                                                   (3·4번 필드는 도달조차 못 함)
```

데이터 흐름으로 요약하면, 애너테이션이라는 하나의 값이 **두 개의 자리**(공급자 람다와 지연 캐시)에 나뉘어 살고 있는데 직렬화는 그 둘을 각각 독립적으로 다룬다.\
캐시가 채워져 있어도 공급자는 그대로 쓰이고(그래서 미리 조회해도 실패는 같다), 공급자를 빼면 캐시가 `null`인 채 나간다(그래서 애너테이션이 조용히 사라진다).\
수정은 이 대칭을 깬다 — 공급자를 빼되, 빼기 직전에 캐시를 채운다.

같은 값이 두 자리에 나뉘어 산다는 사실을, 수정 전과 후로 나란히 놓으면 이렇게 보인다.

```text
수정 전 — 두 자리가 따로 논다              수정 후 — 한 자리로 합류한다
+----------------------------------+      +----------------------------------+
| annotatedElement  = null         |      | annotatedElement  = 어댑터        |
|   (물어본 적 없으면 비어 있다)    |      |   (writeObject 가 채워 놓는다)    |
|                                  |      |                                  |
| annotatedElementSupplier         |      | annotatedElementSupplier          |
|   = 람다[capture: Field]         |      |   = transient (스트림 밖)         |
|   -> 스트림에 실린다              |      |                                  |
+----------------------------------+      +----------------------------------+
  스트림에 나가는 애너테이션 = 없음          스트림에 나가는 애너테이션 = 어댑터 1개
  스트림에 나가는 리플렉션 객체 = Field      스트림에 나가는 리플렉션 객체 = 없음
```

그림이 말하는 것 하나 — 수정은 자리를 늘리지 않고, 실어 나르는 주체를 람다에서 어댑터로 옮긴다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 것은 "애너테이션을 들고 있는 것"이 이름만 넷이라는 점이다: 람다(`annotatedElementSupplier`), 어댑터(`annotatedElement`), 어댑터 내부 배열(`annotations`), 그리고 어댑터가 밖으로 내주는 복사본.\
아래 표는 각각이 무엇을 들고, 누가 언제 만지며, 이 결함과 어떤 관계인지를 한 줄씩 붙인다.

| 이름표 | 무엇인가 / 입력·출력 | 누가 언제 만지나 | 이 결함과의 관계 |
|---|---|---|---|
| `type` :72 | 원시 타입 `Class<?>`. 생성자에서 확정 | 생성자 4개가 쓰고 `getType()`이 읽음 | 직렬화 가능. 무관 |
| `resolvableType` :74 | 제네릭 정보 `ResolvableType`. `forField`/`forMethodParameter` 결과 | 생성자 4개 | `SerializableTypeWrapper`가 내부 JDK Type을 프록시로 감싸 이미 직렬화 가능. 무관(단, `forClassWithGenerics` 갈래는 PR #37186의 무대) |
| `annotatedElementSupplier` :76 | **애너테이션 조회를 미룬 람다**. 입력 없음, 출력 `AnnotatedElementAdapter` | 생성자 4개가 대입, `getAnnotatedElement()`:256이 최초 1회 호출 | **결함의 자리**. `final`이고 `transient`가 아니라 스트림에 실린다 |
| `AnnotatedElementSupplier` (인터페이스) :730 | `Supplier<AnnotatedElementAdapter>` + `Serializable`인 private 중첩 인터페이스 | 필드 :76의 선언 타입 | `Serializable` 상속은 "이 자리를 스트림에 쓰겠다"는 선언일 뿐, **캡처 내용물의 직렬화 가능성은 보장하지 않는다**. 컴파일은 통과하고 실패는 런타임으로 밀린다 |
| 람다가 캡처하는 자유변수 :90-91/:102/:115/:131 | 생성자별로 `MethodParameter` / `Field` / `Property` / `Annotation[]` | 람다 생성 시 값 복사(캡처) | 앞의 셋이 비직렬화 -> `SerializedLambda.capturedArgs`에 실려 폭발. 넷째만 안전 |
| `annotatedElement` :78 | 조회 결과를 담는 `volatile` **지연 캐시**(`@Nullable`) | `getAnnotatedElement()`:256이 쓰고, 세 접근자가 읽음 | 직렬화 가능하지만 `null`일 수 있다 -> 공급자를 그냥 빼면 애너테이션 소실. 수정이 `writeObject`를 도입한 이유 |
| `getAnnotatedElement()` :256 | 캐시 miss면 공급자를 호출해 캐시를 채우고 어댑터 반환. 입력 없음, 출력 어댑터 | `getAnnotations`:269 / `hasAnnotation`:280 / `getAnnotation`:296, 그리고 수정 후에는 `writeObject` | 읽는 방향은 :76 -> :78 (반대가 아니다). 수정은 이 메서드를 손대지 않고 **호출 시점만 하나 추가**한다 |
| `getAnnotations()` :269 | 어댑터의 배열을 반환. 출력 `Annotation[]`(빈 배열 가능, null 아님) | 컨버터, `annotationsMatch()`:511, 파생 생성자들 | 왕복 후 이 값이 보존되는지가 테스트 단언의 축 |
| `hasAnnotation()` :280 / `getAnnotation()` :296 | 어댑터가 비어 있으면 `AnnotatedElementUtils`를 아예 부르지 않고 즉시 `false`/`null` | SpEL·바인딩 경로 | 이 지름길이 `isEmpty()` 판정에 걸려 있어서, 역직렬화가 `EMPTY` 동일성을 잃으면 조용히 느려진다 |
| `AnnotatedElementAdapter.EMPTY` (AnnotatedElementAdapter.java:40) | 빈 애너테이션 배열을 가진 `private static final` 싱글턴 | `from()`:55이 반환 | 역직렬화는 생성자와 정적 팩토리를 우회하므로 **복원본은 EMPTY가 아니다**. 이 어댑터에는 `readResolve()`가 없어 복원 책임이 소유자(TypeDescriptor)로 넘어온다 |
| `AnnotatedElementAdapter.from(Annotation[])` (:55) | `null` 또는 길이 0이면 `EMPTY`, 아니면 새 인스턴스. 입력 `@Nullable Annotation[]`, 출력 어댑터 | 생성자 람다 4개, 수정 후 `readObject` | 수정의 `readObject`가 이 팩토리를 **다시 태우는 것**이 EMPTY 동일성 복구의 전부다 |
| `AnnotatedElementAdapter.isEmpty()` (:110) | `this == EMPTY` — **값 비교가 아니라 동일성 비교** | 세 지름길과 `getAnnotations()`:92 | 값 기반으로 읽으면 이 수정의 절반을 놓친다. 게이트 기록에서 실제로 반복된 오해 |
| `AnnotatedElementAdapter.getAnnotations()` (:92) | `isEmpty() ? this.annotations : this.annotations.clone()` | `TypeDescriptor.getAnnotations()`:269 | 두 번 호출해 같은 배열이면 EMPTY, 다르면 아니다 -> 테스트가 이 성질을 관측 수단으로 쓴다 |
| `equals()` :495 / `annotationsMatch()` :511 | 타입·제네릭에 더해 애너테이션 배열까지 비교 | 캐시 키, 테스트 헬퍼 | "직렬화 성공"과 "애너테이션 보존"이 이 클래스에서 분리되지 않는 이유. 왕복이 애너테이션을 잃으면 동등성부터 깨진다 |
| `writeObject(ObjectOutputStream)` (head :733) | 조회를 강제한 뒤 `defaultWriteObject()`. 반환 없음 | JDK 직렬화 런타임이 리플렉션으로만 호출 | **수정 (1)**. 지연 조회를 유지한 채 애너테이션을 캐시로 옮겨 싣는 유일한 지점 |
| `readObject(ObjectInputStream)` (head :740) | `defaultReadObject()` 후 어댑터를 `from()`으로 재생성하고 두 필드를 다시 채움 | 직렬화 런타임 | **수정 (2)**. EMPTY 동일성 복구 + `transient`로 비워진 공급자 재장전 |
| `readObject` 안의 지역변수 `annotatedElement` (head :742) | 재생성한 어댑터. 필드가 아니라 **지역변수**여야 한다 | 같은 메서드 안에서 두 번 사용 | 마지막 줄의 람다가 이 지역변수를 캡처한다. 필드를 캡처하면 `this`를 캡처하게 되어 다시 직렬화 대상이 늘어난다 |
| 재장전된 공급자 람다 (head :745) | `() -> annotatedElement` — 상수 반환 | 이후 `getAnnotatedElement()`가 부를 수도 있음(캐시가 이미 차 있어 실제로는 거의 안 불림) | 이 람다가 캡처하는 것은 **직렬화 가능한 어댑터 하나뿐**이다. 즉 복원된 객체를 다시 직렬화해도 안전 |
| `serialVersionUID` (선언 없음, `@SuppressWarnings("serial")` :58) | JDK가 필드 목록에서 자동 계산 | 스트림 헤더 | 직렬화 필드가 4개에서 3개로 줄어 값이 바뀐다(README §4에 실측값). 버전 간 스트림 호환은 원래 계약이 아니었고, PR은 UID 고정을 **의도적으로 기각**했다 |

## 3. 결함 경로 단계 추적

같은 프로그램을 두 상태에서 돌린다.\
대상은 애너테이션이 붙은 필드로 만든 디스크립터이고, 애너테이션을 **미리 조회하지 않은 채** 바로 직렬화한다(PR 테스트 헬퍼가 택한 것과 같은 조건).

```java
TypeDescriptor td = new TypeDescriptor(getClass().getField("fieldAnnotated"));
new ObjectOutputStream(out).writeObject(td);
```

아래 표는 왼쪽이 결함 상태(베이스), 오른쪽이 수정 상태다.\
각 단계의 값은 코드 규칙에서 유도한 것이다.

| 단계 | 결함 상태(베이스 `e8729d04388`) | 수정 상태(head `f92313cc3e1`) |
|---|---|---|
| S1 생성자 :99 | `type=String.class`, `resolvableType=RT(String)`, `supplier=lambda[capture: field]`, `annotatedElement=null` | 동일 |
| S2 `writeObject(td)` 진입 | 훅 없음 -> 곧바로 기본 필드 직렬화 | `TypeDescriptor.writeObject`:733 실행 -> `getAnnotatedElement()` 호출 |
| S3 조회 | 일어나지 않음 | 캐시 miss -> `supplier.get()` -> `field.getAnnotations()` -> `from(anns)` -> `annotatedElement = 어댑터(anns)` |
| S4 필드 1 `annotatedElement` | `null` 기록 | 어댑터 기록(내부 `Annotation[]`은 직렬화 가능) |
| S5 필드 2 `annotatedElementSupplier` | 선언 타입이 `Serializable` -> `SerializedLambda`로 치환 -> `capturedArgs[0] = Field` -> **`NotSerializableException: java.lang.reflect.Field`** | `transient`라 **건너뜀** |
| S6 필드 3·4 | 도달 못 함 | `resolvableType`, `type` 정상 기록 |
| S7 역직렬화 | 실행되지 않음 | `readObject`:740 -> `defaultReadObject()` 후 `annotatedElement != null` -> `from(어댑터.getAnnotations())` |
| S8 EMPTY 동일성 | 해당 없음 | 애너테이션이 있으면 새 어댑터, 없으면 **`EMPTY` 싱글턴으로 접힘** -> `isEmpty()` 지름길 복구 |
| S9 공급자 재장전 | 해당 없음 | `annotatedElementSupplier = () -> annotatedElement`(지역변수 캡처) -> 재직렬화도 안전 |
| S10 최종 관측 | 예외 | `readObject.getAnnotations()`가 원본과 동등, `equals()` 성립, 조회 횟수는 정확히 1 |

정상 케이스(넷째 생성자, 예: `TypeDescriptor.forObject("")` -> `valueOf(String.class)`:575 -> `new TypeDescriptor(RT, null, null)`:128)를 같은 표에 대면 대비가 분명하다.\
S5에서 `capturedArgs[0]`이 `null`(애너테이션 배열)이라 직렬화가 통과하고, 그래서 **기존 테스트 `serializable()`은 수정 전에도 green**이었다.\
회귀가 릴리스를 여럿 건너 살아남은 원인이 이 한 칸에 있다.

S5 한 칸에서 두 케이스가 어떻게 갈리는지만 떼어 보면 이렇다.

```text
결함 케이스: new TypeDescriptor(field)     정상 케이스: forObject("")
        |                                          |
        v                                          v
 supplier = 람다[capture: Field]            supplier = 람다[capture: null]
        |                                          |
        v                                          v
 SerializedLambda.capturedArgs[0]           SerializedLambda.capturedArgs[0]
        = java.lang.reflect.Field                  = null
        |                                          |
        v                                          v
 NotSerializableException                   통과 -> 기존 테스트가 green
```

그림이 말하는 것 하나 — 두 케이스의 차이는 `capturedArgs[0]` 한 칸뿐이고, 기존 테스트는 오른쪽만 밟았다.

두 상태의 차이를 관측 가능한 축으로 두 개만 뽑으면 이렇다.\
하나는 "예외가 나는가", 다른 하나는 "지연 조회가 살아 있는가"다.\
후자는 `MethodParameter`를 익명 서브클래스로 감싸 `getParameterAnnotations()` 호출 횟수를 세면 보인다 — 생성 직후 0, 직렬화 후 정확히 1.\
0->1이 아니라 0->0이면 애너테이션이 소실된 것이고, 1->1이면 gh-33948의 성능 개선이 되돌아간 것이다.\
두 단언이 함께 있어야 수정의 경계가 고정된다(테스트 상세는 [tests.md](tests.md) 7절).

## 4. 계약 — 무엇이 고정돼 있고 결함이 무엇을 어기나

이 클래스가 지키기로 되어 있던 계약 여덟 가지와, 결함 또는 수정이 그중 무엇을 건드리는지를 나란히 놓는다.

> **계약(contract)** — 코드가 바깥에 약속한 성질. 시그니처만이 아니라 javadoc·클래스 선언·기존 동작이 다 계약이 된다.\
> 예: `implements Serializable`이라는 선언 한 줄이 "이 객체는 스트림에 쓸 수 있다"는 계약이다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| `TypeDescriptor`는 `Serializable`이다 | 클래스 선언 :59, 3.0부터 유지 | 어긴다 — 네 생성자 중 셋이 만든 인스턴스가 스트림에 못 실린다 |
| 변환 예외는 `TypeDescriptor`를 그대로 실어 나른다 | `ConversionFailedException`:33/:35, `ConverterNotFoundException`:32/:34 (비-transient) | 간접 위반 — 예외 자체가 직렬화 불가가 된다 |
| 애너테이션 조회는 지연된다(성능 계약) | gh-33948 / 커밋 `1a573d6e3c7`, `getAnnotatedElement()`:256 | 수정이 이 계약을 지켜야 한다는 **제약**. 생성자에서 즉시 조회로 되돌리는 해법이 기각된 이유 |
| `getAnnotations()`는 null이 아니라 빈 배열을 반환한다 | javadoc :270-271 | 결함과 무관하나, 공급자만 제거하는 반쪽 수정은 이 계약을 깨뜨린다(캐시 null -> NPE 또는 소실) |
| `isEmpty()`인 어댑터는 배열을 복사하지 않는다 | AnnotatedElementAdapter.java:92-93, :110 | 역직렬화가 동일성을 잃으면 조용히 위반. 수정의 `from()` 재호출이 이를 지킨다 |
| `equals()`는 애너테이션까지 비교한다 | :495, `annotationsMatch()`:511 | 왕복이 애너테이션을 잃으면 동등성 계약이 깨진다 |
| 버전 간 스트림 호환은 계약이 아니다 | `serialVersionUID` 미선언 + `@SuppressWarnings("serial")` :58 | 위반 아님 — UID 변화를 허용 가능하게 만드는 근거 |
| 기존 테스트 `serializable()`이 고정하던 것 | `TypeDescriptorTests` | **넷째 생성자 한 갈래뿐**. 이름은 계약 전체를 지키는 것처럼 보이지만 실제 커버리지는 1/4 |

## 5. 수정안 — before / after

### 5.1 필드 선언 (핵심 한 줄)

수정의 본체는 공급자 필드의 수식어를 바꾸는 한 줄이다.

> **수식어(modifier)** — 필드·메서드 선언 앞에 붙어 성질을 정하는 키워드(`private`·`final`·`transient`·`volatile` 등).\
> 예: `final`은 "한 번 대입하면 못 바꾼다", `transient`는 "직렬화에서 제외한다"를 뜻한다.

```java
// before  TypeDescriptor.java:76 (e8729d04388)
	private final AnnotatedElementSupplier annotatedElementSupplier;

// after   TypeDescriptor.java:79 (f92313cc3e1)
	private transient AnnotatedElementSupplier annotatedElementSupplier;
```

`final`이 빠진 것은 목적이 아니라 결과다.\
`readObject`에서 재대입해야 하므로 `final`을 유지할 수 없다.

### 5.2 직렬화 훅 두 개 (신설)

빠진 통로를 메우는 것은 쓰기 직전의 강제 조회와 읽기 직후의 어댑터 재생성 두 훅이다.

```java
// after   TypeDescriptor.java:733-746 (f92313cc3e1)
	private void writeObject(ObjectOutputStream outputStream) throws IOException {
		// Resolve the annotations up front since the supplier is transient: it captures
		// the Field/MethodParameter/Property this descriptor has been created from.
		getAnnotatedElement();
		outputStream.defaultWriteObject();
	}

	private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
		inputStream.defaultReadObject();
		AnnotatedElementAdapter annotatedElement = AnnotatedElementAdapter.from(
				this.annotatedElement != null ? this.annotatedElement.getAnnotations() : null);
		this.annotatedElement = annotatedElement;
		this.annotatedElementSupplier = () -> annotatedElement;
	}
```

**왜 이 위치인가.**\
세 조각이 각각 다른 문제를 막고, 하나라도 빠지면 다른 것이 깨진다.

1. `transient` (필드) — 캡처된 리플렉션 객체를 스트림에서 제거.\
   결함의 직접 원인 제거.
2. `writeObject`의 `getAnnotatedElement()` — 공급자가 빠진 자리를 캐시가 메우게 한다.\
   이 한 줄이 없으면 애너테이션이 **조용히** 사라진다(예외 없이 값만 잃는 최악의 실패 모드).
3. `readObject`의 `from(...)` 재호출 — 역직렬화가 생성자와 정적 팩토리를 우회하므로 `EMPTY` 동일성이 깨진 채 복원된다.\
   이 줄이 없으면 왕복 후 `isEmpty()` 지름길 셋이 조용히 죽는다.

> **정적 팩토리(static factory)** — 생성자 대신 객체를 만들어 주는 static 메서드. 캐싱이나 싱글턴 재사용 같은 판단을 안에 넣을 수 있다.\
> 예: `AnnotatedElementAdapter.from(null)`은 새 객체를 만들지 않고 `EMPTY`를 돌려준다.

세 조각 중 하나씩 빼 보면 어떤 실패가 되돌아오는지가 갈린다.

```text
transient   writeObject   readObject          결과
  있음        있음          있음        ->  성공, 애너테이션 보존, 지름길 유지
  없음         -             -         ->  NotSerializableException (원래 결함)
  있음        없음          있음        ->  예외는 없지만 애너테이션이 조용히 소실
  있음        있음          없음        ->  값은 맞지만 isEmpty() 지름길 셋이 죽는다
```

그림이 말하는 것 하나 — 셋 중 하나만 빠져도 실패 모드가 "시끄러운 예외"에서 "조용한 손실"로 바뀐다.

비용 위치도 이 배치의 근거다.\
조회 강제가 `writeObject` 안에 있으므로 **직렬화하지 않는 모든 경로의 성능은 그대로**다 — gh-33948이 얻은 이득이 유지되고, 추가 조회는 실제로 스트림에 쓰는 순간에만 한 번 발생한다.

### 5.3 검토된 대안과 기각 이유

같은 회귀를 없애는 다섯 가지 접근을 검토했고, 각각 다음 이유로 밀렸다.

- **생성자에서 즉시 조회로 되돌린다**: 결함은 사라지지만 gh-33948의 성능 회귀가 그대로 복귀한다.\
  계약(4절 3행)에 정면 위배 -> 기각.
- **공급자 필드만 `transient`로 바꾸고 훅은 두지 않는다**: 쓰기는 성공하지만 캐시가 `null`인 채 나가 애너테이션이 소실되고, 복원 후 `supplier.get()`이 NPE를 낸다 -> 기각.\
  이 반쪽 수정을 red로 붙잡는 것이 테스트 설계의 한 축이다.
- **`readObject`에서 어댑터를 그대로 대입**: `EMPTY` 동일성이 복구되지 않아 `isEmpty()` 지름길이 죽는다.\
  관측 가능한 계약 위반 -> 기각.
- **`AnnotatedElementAdapter`에 `readResolve()`를 추가**: 어댑터 쪽에서 EMPTY를 접는 더 일반적인 해법이지만, 이 PR의 범위(회귀 복원)를 넘어 공개 클래스의 직렬화 형식을 바꾼다.\
  소유자 쪽 `from()` 재호출로 같은 효과를 얻을 수 있으므로 채택하지 않았다 — 다만 어댑터를 직접 직렬화하는 다른 사용처가 생기면 재검토 대상이다.
- **이전 `serialVersionUID`를 고정**: 옛 스트림의 공급자 필드는 읽혀서 버려지고, 옛 코드는 조회를 강제하지 않았으므로 `annotatedElement`가 `null`로 도착한다 — 결과는 **애너테이션의 조용한 소실**.\
  게다가 문제의 세 생성자로 만든 옛 스트림은 애초에 존재할 수 없다(그것을 쓰는 일이 지금 실패하는 동작이다).\
  시끄러운 실패를 택해 기각.

## 6. 범위 밖과 인접 영향

이 PR이 손대지 않은 인접 실패와, 수정이 남기는 영향은 다음 네 갈래로 정리된다.

- **`getElementTypeDescriptor()` 등 파생 경로의 `NotSerializableException: TypeVariableImpl`**: 원인이 애너테이션 공급자가 아니라 `resolvableType` 쪽이라 이 PR 전후가 동일하다.\
  그중 계약이 살아 있던 `forClassWithGenerics` 갈래가 [PR #37186](../37186-resolvabletype-generics-serialization/README.md)로 분리됐고, `as()` 상위 타입 워크 갈래는 SPR-17070이 문서로 계약을 축소해 둔 영역이라 손대지 않았다.
- **같은 패턴의 다른 위치**: `Serializable` 함수형 인터페이스로 지연 조회를 만드는 코드가 있으면 같은 함정에 빠진다.\
  `spring-core` 안의 선례이자 정답은 `SerializableTypeWrapper`의 provider 3종(`FieldTypeProvider`:229/:235/:253, `MethodParameterTypeProvider`:269/:279/:299, `MethodInvokeTypeProvider`:322/:332/:361)으로, 리플렉션 객체를 `transient`로 빼고 "다시 찾을 좌표"를 실어 `readObject`에서 복원한다.\
  이번 수정은 같은 패턴이되 싣는 재료가 좌표가 아니라 **이미 조회해 둔 결과**라는 점만 다르다.
- **하위호환**: 런타임 동작·API 시그니처는 불변.\
  바뀌는 것은 (1) 자동 계산되는 `serialVersionUID` (2) 애너테이션 클래스가 클래스패스에 없을 때의 예외 종류 — 이전에는 `NotSerializableException`, 이후에는 `writeObject`에서 올라오는 `TypeNotPresentException`.\
  둘 다 실패이고 후자가 원인 정보를 더 담는다.
- **미확인**: 이 PR이 7.0.x 백포트 대상인지, 회귀가 들어간 정확한 릴리스 구간(6.2.1~6.2.13 사이로 추정)의 하한은 PR 본문 기준으로만 확인했고 각 릴리스 태그에서 재현하지는 않았다.

> **백포트(backport)** — 최신 브랜치에 들어간 수정을 이전 버전 브랜치에도 옮겨 싣는 것.\
> 예: 7.0 main에 머지된 이 수정을 6.2.x 유지보수 브랜치에도 반영할지는 아직 확인되지 않았다.
