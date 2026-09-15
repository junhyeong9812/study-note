# PR #37139 — 무대의 실구조와 워크플로우

> PR #37139의 무대가 되는 실구조·워크플로우. 문제·수정은 [README.md](README.md), 테스트는 [tests.md](tests.md) 참조.
>
> 기준: 로컬 HEAD `526c706d1c3`. 이 시점의 `Property.java`에는 **이미 #36911과 #37139의 수정이 반영되어 있다**(각각 커밋 `f067d40f0a6`, `e8e293a7060`). 따라서 아래 file:line은 수정 후 좌표이며, "수정 전" 코드는 PR diff의 `-` 쪽으로 재구성해 별도 표기한다.
>
> 이 문서는 `resolveName()`의 **write(setter) 분기**에 집중한다. 같은 메서드의 read 분기 구조와 `Property`의 전체 성격은 [`../36911/structure.md`](../36911-property-name-resolution/structure.md)와 [`../36911/README.md`](../36911-property-name-resolution/README.md)가 담당하므로 여기서는 다시 서술하지 않는다.

## 1. 무대 — 실구조

`Property`는 `java.beans.PropertyDescriptor` 없이 "읽기 메서드 + 쓰기 메서드 + 선언 타입"을 한 장의 카드로 묶는 값 객체이고, 이번 PR의 무대는 그 카드가 **이름을 스스로 유도할 때 타는 write 가지 하나**다.

> **값 객체(value object)** — 식별자 없이 담고 있는 값들로만 동일성이 정해지는 객체. 만들어진 뒤에는 바뀌지 않는다.\
> 예: `Property`는 타입·읽기 메서드·쓰기 메서드·이름이 모두 같으면 같은 카드로 취급된다.

> **`java.beans.PropertyDescriptor`** — 프로퍼티 하나를 서술하는 JDK 표준 클래스. 이 패키지가 없는 환경이 있어 Spring이 자체 경량 표현을 따로 만들었다.\
> 예: `Property`는 그 경량 대체물이다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Property (final)                                       Property.java:51  │
│                                                                           │
│  static Map<Property, Annotation[]> annotationCache        :53            │
│      (ConcurrentReferenceHashMap — 키가 Property 자신)                     │
│                                                                           │
│  Class<?>  objectType          :55   ← 선언 소유 타입                      │
│  Method    readMethod  (@Nullable) :57                                    │
│  Method    writeMethod (@Nullable) :59   ← write 분기의 입력               │
│  String    name                :61   ← 생성자에서 확정, 이후 불변          │
│  MethodParameter methodParameter :63  ← 타입 정보 담당                     │
│  Annotation[] annotations (@Nullable) :65  ← 지연 조회 캐시                │
└──────────────────────────────────────────────────────────────────────────┘
        │                       │                        │
        │ name 확정              │ 타입 확정               │ 애너테이션 확정
        v                       v                        v
  resolveName()  :135     resolveMethodParameter() :182   resolveAnnotations() :215
    ├ read 분기  :136-154    ├ resolveReadMethodParameter()  :201   ├ read/write/field 순회
    ├ write 분기 :155-161    └ resolveWriteMethodParameter() :208   └ getField() :238 이 name 소비
    └ else(둘 다 없음) :162                                              (name 이 여기서 재사용됨)
```

그림 해설: 카드가 들고 있는 필드 여섯 개가 아래 세 갈래(이름·타입·애너테이션)로 각각 확정되고, 그중 `name`만이 `getField()`에서 다시 쓰인다.

> **MethodParameter** — 메서드의 특정 파라미터(또는 반환값)의 타입 정보를 제네릭까지 포함해 들고 다니는 Spring의 객체.\
> 예: `resolveWriteMethodParameter()`는 setter의 0번 파라미터를 가리키는 `MethodParameter`를 만든다.

> **애너테이션(annotation)** — 코드에 붙여 두는 부가 표시. 값이 아니라 "이 요소를 어떻게 다뤄라"를 알린다.\
> 예: 필드에 붙은 검증 애너테이션을 카드가 모아 두면 타입 변환이 그것을 참고한다.

> **`ConcurrentReferenceHashMap`** — 키·값을 약한 참조로 들고 있어 메모리가 모자라면 스스로 비워지는 동시성 맵.\
> 예: `annotationCache`는 이 맵이라 카드가 더 이상 쓰이지 않으면 항목이 회수된다.

생성자는 둘인데, 이 PR이 문제 삼는 경로는 **이름을 받지 않는 쪽**이다.

```text
Property(Class, Method read, Method write)              :68
    └─ this(objectType, readMethod, writeMethod, null)   ← name = null → resolveName() 강제

Property(Class, Method read, Method write, String name) :72
    ├─ this.methodParameter = resolveMethodParameter()   :78   ← 이름보다 먼저 실행
    └─ this.name = (name != null ? name : resolveName()) :79   ← name 이 있으면 유도 자체를 건너뜀
```

그림 해설: 3-인자 생성자는 `null` 이름을 넘겨 이름 유도를 강제하고, 4-인자 생성자에 이름을 주면 유도 자체가 실행되지 않는다.

즉 `resolveName()`은 **3-인자 생성자(또는 4-인자에 `null` 이름)를 탄 경우에만** 실행되는 내부 헬퍼다.\
그리고 그 안의 write 분기는 read 메서드가 없을 때에만 도달한다.

```text
현재(수정 후)                                  수정 전(PR diff의 '-' 쪽)
────────────────────────────────────           ─────────────────────────────────────
else if (this.writeMethod != null) {  :155     else if (this.writeMethod != null) {
  String methodName =                            int index = writeMethod.getName()
      this.writeMethod.getName();   :156                        .indexOf("set");
  if (!methodName.startsWith("set")) :157        if (index == -1) {
    throw new IllegalArgumentException(            throw new IllegalArgumentException(
        "Not a setter method");      :158              "Not a setter method");
  }                                              }
  return StringUtils.uncapitalize(               index += 3;
      methodName.substring(3));      :160        return StringUtils.uncapitalize(
}                                                    writeMethod.getName().substring(index));
```

그림 해설: 오른쪽은 `index` 하나가 판정과 오프셋을 겸하고, 왼쪽은 판정(`startsWith`)과 오프셋(상수 3)이 분리돼 있다.

이 카드를 소비하는 쪽은 두 갈래다.\
하나는 `TypeDescriptor(Property)`(`TypeDescriptor.java`:111)로, `property.getMethodParameter()`와 `property.getAnnotations()`만 쓴다.\
다른 하나는 `Property` 자신의 내부 — `getField()`가 유도된 `name`으로 실제 필드를 찾아 애너테이션을 모은다.

> **TypeDescriptor** — Spring의 타입 변환에서 "출발 타입/도착 타입"을 애너테이션까지 포함해 서술하는 객체.\
> 예: `new TypeDescriptor(property)`로 만들면 그 프로퍼티 자리의 변환 맥락이 된다.

> **backing field(뒷받침 필드)** — 접근자 메서드가 실제로 읽고 쓰는, 값이 저장된 그 필드.\
> 예: `setName(String)`의 backing field는 같은 클래스의 `private String name`이다.

## 2. 수정 전 동작 워크플로우

대표 시나리오는 "setter만 있는 카드를 이름 없이 만들 때"다.\
생성자 안에서 타입 해석이 먼저 끝나고, 그다음에 이름 유도가 실행된다는 순서가 중요하다.

```text
new Property(TestBean.class, null, TestBean::offsetX)        Property.java:68
   │
   ├─ [1] resolveMethodParameter()                                   :182
   │        ├ resolveReadMethodParameter() → null (readMethod 없음)  :201
   │        ├ resolveWriteMethodParameter() → MethodParameter(write, 0) :208
   │        └ write != null 이므로 write 파라미터 채택                 :198
   │           (여기까지는 이름과 무관 — 타입은 정상적으로 잡힌다)
   │
   └─ [2] resolveName()                                              :135
            ├ readMethod == null → read 분기 건너뜀
            └ writeMethod != null → write 분기 진입
                 수정 전:  "offsetX".indexOf("set") == 3   (≠ -1 이므로 통과)
                           index = 3 + 3 = 6
                           substring(6) = "X" → uncapitalize → "x"
                 결과:     예외 없이 name = "x"  ← 무음 오탐
   │
   v
this.name = "x"   (이후 불변, 카드가 조용히 완성된다)
```

그림 해설: 타입은 [1]에서 정상으로 확정되기 때문에, [2]의 이름 오염만으로는 아무 신호도 뜨지 않는다.

유도된 이름이 잘못돼도 생성은 성공하므로, 오염은 **나중에 이름을 소비하는 지점**에서 드러난다.

```text
property.getAnnotations()                                            :125
   └─ resolveAnnotations()                                           :215
        ├ annotationCache 조회 (키 = Property, equals/hashCode 가 name 포함) :216
        ├ addAnnotationsToMap(map, getReadMethod())   → null 이므로 skip :219
        ├ addAnnotationsToMap(map, getWriteMethod())  → setter 애너테이션 :220
        └ addAnnotationsToMap(map, getField())        → 필드 애너테이션   :221
               └─ getField()                                          :238
                    ├ name = "x"  (hasLength → 통과)                   :240
                    ├ findField(declaringClass, "x")        → 없음
                    ├ findField(declaringClass, "x")(uncapitalize) → 없음 :249
                    └ findField(declaringClass, "X")(capitalize)   → 없음 :251
                    ⇒ null — 실제 필드 `offsetX` 는 끝내 발견되지 않는다
```

그림 해설: 세 변형을 모두 시도하고도 못 찾으면 `null`을 돌려줄 뿐이라, 조회 실패가 예외로 올라오지 않는다.

`upset(String)` 케이스는 한 걸음 더 나쁘다.\
`indexOf("set")==2`, `+3=5`, `substring(5)`가 빈 문자열이 되어 `name = ""`이 되고, `getField()`는 240행의 `hasLength` 가드에 걸려 **조회 자체를 하지 않고** `null`을 돌려준다.\
게다가 빈 이름은 `equals`(:271)·`hashCode`(:280)의 구성요소이므로 `annotationCache`의 키로도 그대로 쓰인다.

> **가드 절(guard clause)** — 본 로직에 들어가기 전에 "이 경우는 볼 것도 없다"를 먼저 걸러 내고 빠져나가는 조건문.\
> 예: `getField()`의 `hasLength(name)` 검사는 빈 이름이면 필드 조회를 아예 시작하지 않는다.

> **캐시 키(cache key)** — 캐시에서 값을 찾을 때 쓰는 식별자.\
> 예: `annotationCache`의 키는 `Property` 자신이므로, 이름이 오염되면 캐시에서 다른 항목으로 잡힌다.

## 3. 분기 처리 워크플로우

`resolveName()`의 분기도가 이 PR의 전부다.\
버그가 살았던 자리는 write 가지의 판별식 하나다.

```text
resolveName()                                                   :135
│
├─ readMethod != null ─────────────────────────────────────────┐  :136
│     get/is 접두사 + isPlainAccessor 폴백 (record 접근자 등)     │
│     └ 상세는 ../36911/structure.md 로 위임 — 이 문서 범위 밖    │
│     - 특징: "규약 밖 이름이면 이름 전체를 쓴다"는 폴백이 있다     │
│                                                               │
├─ writeMethod != null ────────────────────────────────────────┤  :155
│     - 특징: 폴백이 없다 — setXxx 규약을 못 맞추면 거부한다       │
│                                                               │
│     ┌ 수정 전 판별: indexOf("set")                              │
│     │    ├ == -1        → IllegalArgumentException("Not a setter method")
│     │    │                  예: updateName  (정상 거부)
│     │    ├ == 0         → substring(3)  예: setName → "name"    (정상)
│     │    └ >  0         → substring(idx+3)                      * 버그 분기
│     │         예: offsetX (idx=3) → "x"       — 무음 통과
│     │         예: upset   (idx=2) → ""        — 무음 통과, 빈 이름
│     │
│     └ 수정 후 판별: startsWith("set")
│          ├ false → IllegalArgumentException("Not a setter method")
│          │           예: updateName · offsetX · upset  (셋 다 거부)
│          └ true  → substring(3)   예: setName → "name"          (불변)
│
└─ 둘 다 null ─────────────────────────────────────────────────┘  :162
      IllegalStateException("Property is neither readable nor writable")
      (같은 조건을 resolveMethodParameter():187 이 먼저 검사하므로,
       실제로는 그쪽에서 먼저 터진다 — 생성자가 :78 을 :79 보다 먼저 실행하기 때문)
```

그림 해설: 세 가지 이름이 수정 전에는 세 갈래로 흩어졌다가, 수정 후에는 `updateName`·`offsetX`·`upset`이 한 갈래로 모인다.

두 판별식의 차이가 만드는 집합은 정확히 "`set`을 포함하되 `set`으로 시작하지 않는 이름"이다.\
그 밖의 입력에서는 전후 동작이 같다.

두 판별식이 각각 무엇을 거부하는지를 나란히 놓으면 차이가 한눈에 보인다.

```text
수정 전 거부 집합                       수정 후 거부 집합
+-----------------------------+       +-----------------------------+
| set 이 한 글자도 없는 이름    |       | set 으로 시작하지 않는 이름  |
|                             |       |                             |
|   updateName                |       |   updateName                |
|                             |       |   offsetX                   |
|                             |       |   upset                     |
+-----------------------------+       +-----------------------------+
  -> 통과 집합이 너무 넓다                -> 통과 집합은 setName 뿐
```

그림 해설: 거부 집합이 넓어진 만큼 통과 집합이 좁아졌고, 늘어난 두 줄이 이 PR이 바꾸는 전부다.

같은 생성자 안의 다른 분기 하나도 배경으로 알아 둘 만하다.\
타입을 고를 때는 read/write 중 무엇을 쓸지 판단이 들어간다.

```text
resolveMethodParameter()                                        :182
│
├─ write == null ─┬─ read == null → IllegalStateException        :187
│                 └─ read != null → read 채택                     :189
└─ write != null ─┬─ read != null 이고
                  │    writeType != readType && writeType.isAssignableFrom(readType)
                  │      → read 채택 (더 좁은 쪽)                  :194-196
                  └─ 그 외 → write 채택                            :198
```

그림 해설: 이쪽 분기의 판정 재료는 문자열이 아니라 두 타입의 대입 가능 관계다.

이름 유도와 달리 이 분기는 문자열이 아니라 타입 관계로 판정하므로, write 분기의 이름 결함이 타입 해석까지 오염시키지는 않는다.\
오염되는 것은 `name`과 그것을 소비하는 `getField()`·`equals`·`hashCode`뿐이다.

> **`isAssignableFrom`(대입 가능)** — "이 타입 자리에 저 타입의 값을 넣어도 되는가"를 묻는 리플렉션 검사.\
> 예: `Number.class.isAssignableFrom(Integer.class)`는 true다.

## 4. 스프링 전역에서의 자리

`Property`는 "빈 프로퍼티"라는 개념을 `java.beans` 없이 표현하기 위한 spring-core의 어휘이고, `TypeDescriptor`를 프로퍼티 위치에서 만들 때 쓰인다.\
main 소스에서 `new Property(...)`를 부르는 곳은 grep으로 확인한 결과 넷뿐이다.

```text
spring-beans
  GenericTypeAwarePropertyDescriptor.java:195
      new Property(getBeanClass(), getReadMethod(), getWriteMethod(), getName())
          → 4-인자, 이름 명시(JavaBeans introspection 결과)
          → :196 new TypeDescriptor(property) → BeanWrapper 계열의 프로퍼티 변환

spring-expression (SpEL — ReflectivePropertyAccessor)
  :152  canRead()  → new Property(type, method, null, name)    (read 경로)
  :196  read()     → new Property(type, method, null, name)    (read 경로)
  :254  canWrite() → new Property(type, null,   method, name)  ← write 분기가 도달할 뻔한 자리
```

그림 해설: 네 호출 모두 마지막 인자에 이름이 들어가 있어, 이름 유도 자체가 시작되지 않는다.

> **introspection(내성 조회)** — 클래스가 어떤 메서드·필드를 갖고 있는지 실행 중에 들여다보는 것.\
> 예: JavaBeans introspection은 `getName`/`setName` 쌍을 찾아 프로퍼티 `name`이 있다고 판단한다.

네 곳 모두 **4-인자 생성자에 이름을 명시**한다.\
특히 SpEL의 세 곳은 커밋 `fd95ab16baa`("Use verified property names when constructing Property instances in SpEL", 2026-08-10, gh-37123)로 그렇게 바뀌었다 — 그 시점에 SpEL은 이미 요청받은 프로퍼티 이름으로 접근자를 찾아낸 뒤이므로, 이름을 다시 유도할 이유가 없다는 논리였다.

결과적으로 **현재 main에서 `resolveName()`의 write 분기에 도달하는 프레임워크 내부 호출은 없다**.\
도달 경로는 두 가지로 좁혀진다.

```text
[경로 A] 사용자 코드 / 서드파티가 public 3-인자 생성자를 직접 사용
             new Property(objectType, null, writeMethod)      :68
                  └→ resolveName() → write 분기

[경로 B] 테스트 코드
             PropertyTests.java:153  new Property(TestBean.class, null, writeMethod)
             (TypeDescriptorTests 의 Property 사용례는 전부 read+write 쌍이라 read 분기로 간다)
```

그림 해설: 살아 있는 두 경로 모두 프레임워크 바깥에서 오는 호출이다.

`Property`는 `public final class`이고 두 생성자 모두 `public`이므로, 이 분기는 프레임워크 내부에서 죽어 있어도 **공개 API 표면으로는 살아 있다**.\
이 PR이 "무음 오탐"을 "생성 시점 예외"로 바꾸는 동작 강화(behavior change)로 분류되는 이유이자, blast radius가 실질적으로 작다고 말할 수 있는 근거가 바로 이 그림이다.

> **공개 API 표면(public API surface)** — 라이브러리 바깥에서 부를 수 있도록 열어 둔 타입·메서드·생성자의 전체.\
> 예: `Property`의 3-인자 생성자는 `public`이므로 내부에서 안 쓰여도 사용자에게는 여전히 열려 있다.

> **blast radius(영향 반경)** — 어떤 변경이 실제로 망가뜨릴 수 있는 범위.\
> 예: 여기서는 3-인자 생성자를 직접 부르는 사용자 코드까지가 반경이고, 프레임워크 내부는 포함되지 않는다.

한편 위 소비 사슬의 다음 단계도 함께 보아 두면 이름의 영향 범위가 분명해진다.

```text
new TypeDescriptor(property)              TypeDescriptor.java:111
   ├─ resolvableType = forMethodParameter(property.getMethodParameter())  :113
   ├─ type           = resolve(property.getType())                        :114
   └─ annotatedElementSupplier = () -> from(property.getAnnotations())    :115
                                              └─ 여기서만 name 이 다시 쓰인다
                                                 (resolveAnnotations → getField)
```

그림 해설: 세 줄 중 이름에 의존하는 것은 마지막 한 줄뿐이다.

즉 잘못 유도된 이름은 타입 정보에는 영향을 주지 않고, **필드 애너테이션 수집의 누락**으로만 나타난다.\
조용한 오동작이 되는 구조적 이유다.

## 5. 관련 개념

**JavaBeans 이름 규약과 그 경계.**\
setter 규약은 `set` + 대문자로 시작하는 프로퍼티 이름이다.\
`startsWith("set")`은 그중 접두사 조건만 검사하므로, `settle(String)`처럼 `set` 다음이 소문자인 이름은 여전히 통과해 `"tle"`로 해석된다(README §4가 "남는 공백"으로 공개한 부분).\
접두사 매칭만으로 규약 준수를 완전히 판정할 수 없다는 점은 read 분기가 `isPlainAccessor()`(:167)라는 별도 신호 — 같은 이름의 인스턴스 필드가 존재하는가 — 를 동원하는 이유와 같은 뿌리다.

> **JavaBeans** — 필드마다 `getXxx()`/`setXxx()`(boolean은 `isXxx()`)를 두는 자바의 오래된 접근자 관례.\
> 예: `setName(String)`은 프로퍼티 `name`을 쓰는 메서드라는 약속이다.

**부분 일치와 접두사 일치.**\
`indexOf(token) != -1`은 "토큰이 어디에든 있다"를, `startsWith(token)`은 "토큰이 맨 앞에 있다"를 뜻한다.\
이름 규약 판정은 언제나 후자여야 하는데, 전자를 쓰면 거부되는 집합이 좁아지는 방향으로만 틀린다 — 즉 **실패가 예외가 아니라 잘못된 값으로 나타난다**.\
같은 결함이 read 분기에도 있었고 그쪽이 #36911이다([`../36911/README.md`](../36911-property-name-resolution/README.md) §2-3).

**생성자에서 파생 상태를 확정하는 값 객체.**\
`Property`는 `name`을 생성자에서 계산해 `final`로 굳힌다(:79).\
덕분에 `equals`/`hashCode`(:271/:280)와 정적 `annotationCache`(:53)가 이름에 안전하게 의존할 수 있지만, 동시에 **잘못된 이름도 그 자리에서 굳는다**.\
유도 실패를 나중에 고칠 여지가 없으므로, 판정은 생성 시점에 엄격해야 한다는 것이 이 PR의 설계 논리다.

> **파생 상태(derived state)** — 다른 입력으로부터 계산해 만들어 둔 값.\
> 예: `name`은 write 메서드 이름에서 계산된 파생 상태이고, 생성자에서 한 번 굳으면 다시 계산되지 않는다.
