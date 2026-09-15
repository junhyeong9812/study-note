# PR #36911 — 무대 구조와 수정 전 워크플로우

> PR #36911의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 PR은 `f067d40f0a6`으로 **이미 머지**되어, 아래
> `Property.java` 인용은 수정 **후** 코드다. 수정 전 코드는 각 절에서 diff의 `-` 쪽을
> 별도 코드블록으로 병기한다.

## 1. 무대 — 실구조

이 PR의 무대는 "메서드 하나에서 프로퍼티 이름을 유도하는" 한 함수와, 그 이름을 소비하는 주변 객체들이다.\
중심은 `org.springframework.core.convert.Property` — JDK의 `java.beans.PropertyDescriptor` 없이 프로퍼티 한 개를 서술하는 경량 카드다 (`spring-core/src/main/java/org/springframework/core/convert/Property.java:51`).

> **PropertyDescriptor** — JDK `java.beans`가 프로퍼티 하나(읽기·쓰기 메서드와 이름)를 서술하는 표준 클래스.\
> 예: Spring의 `Property`는 `java.beans`가 없는 환경을 위해 같은 역할을 하는 경량 대체물이다.

아래는 `Property`가 들고 있는 것과, 그것을 만들고 소비하는 객체들의 소유 관계다.

```text
                         ┌──────────────────────────────────────────────┐
                         │ Property  (final class)             :51      │
                         │──────────────────────────────────────────────│
   생성자 2종            │ objectType   : Class<?>             :55      │
   (name 있음/없음)      │ readMethod   : @Nullable Method     :57      │
   :68  Property(3-arg)  │ writeMethod  : @Nullable Method     :59      │
   :72  Property(4-arg)  │ name         : String               :61      │◄── 이 PR의 대상
                         │ methodParameter : MethodParameter   :63      │
                         │ annotations  : Annotation[]         :65      │
                         │──────────────────────────────────────────────│
                         │ resolveName()          private     :135      │◄── 버그가 살던 곳
                         │ isPlainAccessor(Method) static     :167      │◄── 수정이 추가
                         │ resolveMethodParameter()           :182      │
                         │ resolveAnnotations()               :215      │
                         │ getField()             private     :238      │◄── 이름의 소비처
                         │ declaringClass()       private     :258      │
                         └───────────────┬──────────────────────────────┘
                                         │ 읽힘
        ┌────────────────────────────────┼─────────────────────────────────┐
        │                                │                                 │
        ▼                                ▼                                 ▼
┌───────────────────────┐   ┌──────────────────────────┐   ┌───────────────────────────┐
│ TypeDescriptor        │   │ ReflectivePropertyAccessor│  │ GenericTypeAware          │
│ (Property) 생성자     │   │ (spring-expression)       │  │ PropertyDescriptor        │
│ TypeDescriptor.java   │   │ :152 canRead              │  │ (spring-beans)            │
│   :111                │   │ :196 read                 │  │   :195 getTypeDescriptor  │
│ nested(Property,int)  │   │ :254 canWrite             │  │                           │
│   :725                │   │  → new Property(...)      │  │  → new Property(...,name) │
└───────────────────────┘   └──────────────────────────┘   └───────────────────────────┘
```

`Property`가 값이 아니라 **구조 정보**만 들고 있다는 점이 중요하다.\
생성자는 `methodParameter`를 먼저 만들고, 이름은 인자로 받았으면 그대로 쓰고 없으면 유도한다.

```java
// Property.java:72-80
public Property(
        Class<?> objectType, @Nullable Method readMethod, @Nullable Method writeMethod, @Nullable String name) {

    this.objectType = objectType;
    this.readMethod = readMethod;
    this.writeMethod = writeMethod;
    this.methodParameter = resolveMethodParameter();
    this.name = (name != null ? name : resolveName());
}
```

`name != null ? name : resolveName()` 이 한 줄이 이 PR 전체의 전제다.\
**이름 인자를 비운 호출만이 `resolveName()`을 실행한다.**

생성자 두 종이 갈라지는 자리를 그림으로 두면, 결함이 왜 한쪽 진입에만 걸리는지가 보인다.

```text
new Property(objectType, read, write)          new Property(objectType, read, write, name)
+-----------------------------------+          +-----------------------------------+
| name 인자 없음 -> null 위임       |          | name 인자 있음                    |
| this.name = resolveName()         |          | this.name = name                  |
| 메서드 이름에서 유도              |          | 유도 자체를 건너뛴다              |
+-----------------------------------+          +-----------------------------------+
  -> 결함 경로 (수정 전 SpEL 3-arg)              -> 결함과 무관 (GenericTypeAware…)
```

이름이 실제로 무슨 일을 하는지는 `getField()`에 있다.\
애노테이션을 모을 때 카드는 getter, setter에 더해 **이름으로 찾은 backing field**의 애노테이션까지 합친다.

```java
// Property.java:215-226 (resolveAnnotations)
addAnnotationsToMap(annotationMap, getReadMethod());
addAnnotationsToMap(annotationMap, getWriteMethod());
addAnnotationsToMap(annotationMap, getField());   // ← 이름으로 필드를 찾는다

// Property.java:238-256 (getField)
String name = getName();
if (!StringUtils.hasLength(name)) {
    return null;                                   // ← 빈 이름이면 조용히 포기
}
Field field = ReflectionUtils.findField(declaringClass, name);
```

이름이 빈 문자열이면 `getField()`가 `null`을 돌려주고, **예외 없이** 필드 애노테이션이 누락된다.\
이 무음 경로가 잘못된 이름이 실피해로 이어지는 통로다.

한 가지 더, 이 PR이 도입한 `isPlainAccessor`는 `spring-beans`에 이미 있던 같은 이름 판별식의 핵심 신호를 옮겨온 것이다.\
두 판별식을 나란히 두면 무엇을 가져오고 무엇을 뺐는지가 보인다.

```text
CachedIntrospectionResults#isPlainAccessor          Property#isPlainAccessor
  (spring-beans …/CachedIntrospectionResults.java     (spring-core …/Property.java:167)
   :345)
  ┌────────────────────────────────────┐              ┌────────────────────────────────┐
  │ static 메서드 제외                 │              │ static 메서드 제외             │
  │ Object.class / Class.class 선언 제외│  ── 미포함 ──▶│ (없음 — 소비 맥락이 다름)     │
  │ 파라미터 0개                       │              │ 파라미터 0개                   │
  │ 반환 타입 != void                  │              │ 반환 타입 != void              │
  │ ClassLoader 등 위험 타입 제외      │  ── 미포함 ──▶│ (없음)                         │
  │ 같은 이름의 필드 존재?             │              │ 같은 이름의 필드 존재?         │
  │   → 존재하면 true                  │  ── 강화 ───▶│   → 존재 + 비static이면 true   │
  └────────────────────────────────────┘              └────────────────────────────────┘
```

`spring-beans` 쪽은 "이 메서드를 프로퍼티로 **승격**할까"를 묻고, `spring-core` 쪽은 "이 이름에서 접두사를 **벗길까**"를 묻는다.\
질문이 다르므로 위험 타입 배제 같은 조건은 따라오지 않았고, 대신 필드의 static 여부 검사가 추가됐다.

## 2. 수정 전 동작 워크플로우

BLUF: 수정 전에는 SpEL 표현식 평가가 `Property`를 **이름 없이** 만들었고, 그 안에서 `indexOf`가 이름 아무 데서나 `get`/`is`를 찾아 잘랐다.

> **BLUF(Bottom Line Up Front)** — 결론을 절 맨 앞에 먼저 쓰는 서술 방식.\
> 예: 이 절은 "이름 없이 만들어 `indexOf`가 잘못 잘랐다"는 결론을 먼저 놓고 경로를 뒤에 편다.

대표 시나리오는 record DTO에 SpEL로 접근하는 흐름이다.\
`record Order(String issue)`에 `"issue"` 표현식을 평가하면 다음 경로를 탄다.\
아래 file:line 중 `ReflectivePropertyAccessor` 쪽은 현재 HEAD 기준이며, `new Property(...)` 호출의 **인자 개수만** 당시와 다르다(3절 뒤 설명).

```text
SpEL 표현식 "issue" 평가
        │
        ▼
ReflectivePropertyAccessor.canRead(ctx, target, "issue")            :133
        │
        ▼
findGetterForProperty("issue", Order.class, target)                 :369
        │  ├─ "get" + "Issue" 탐색  → 없음                          :391
        │  ├─ "is"  + "Issue" 탐색  → 없음                          :394
        │  └─ 접두사 없이 "issue" 탐색 → 발견 (record 접근자)       :400
        ▼
Method issue()
        │
        ▼
new Property(Order.class, issue(), null)     ← 수정 전: 이름 인자 없음
        │
        ▼
Property 생성자                                                     :72
        │  name == null 이므로
        ▼
resolveName()                                                       :135
        │
        │  수정 전 코드:
        │    int index = "issue".indexOf("get");   → -1
        │    index = "issue".indexOf("is");        → 0   ← 맞아 버린다
        │    index += 2;                           → 2
        │    return uncapitalize("issue".substring(2));
        ▼
name = "sue"                                       ← 틀린 이름
        │
        ▼
new TypeDescriptor(property)                    TypeDescriptor.java:111
        │  → property.getAnnotations() 호출 시
        ▼
resolveAnnotations() → getField()                                   :238
        │  ReflectionUtils.findField(Order.class, "sue") → null
        ▼
필드 애노테이션 누락 (예외 없음)
```

수정 전 `resolveName()`의 실제 코드는 다음과 같았다(diff의 `-` 쪽).

```java
// 수정 전 Property#resolveName() — 읽기 메서드 분기
int index = this.readMethod.getName().indexOf("get");
if (index != -1) {
    index += 3;
}
else {
    index = this.readMethod.getName().indexOf("is");
    if (index != -1) {
        index += 2;
    }
    else {
        // Record-style plain accessor method, for example, name()
        index = 0;
    }
}
return StringUtils.uncapitalize(this.readMethod.getName().substring(index));
```

두 번째 시나리오는 `budget()`처럼 `get`을 **중간에** 품은 이름이다.\
같은 경로를 타되 갈림길이 첫 분기에서 갈린다.

```text
Method budget()
   │
   ▼
"budget".indexOf("get") → 3        ← 이름 한가운데서 매칭
   │
   ▼
index = 3 + 3 = 6
   │
   ▼
"budget".substring(6) = ""         ← 빈 문자열
   │
   ▼
getField(): !StringUtils.hasLength("") → null 즉시 반환   Property.java:240
   │
   ▼
애노테이션 누락 (역시 무음)
```

## 3. 분기 처리 워크플로우

BLUF: 수정 전 분기도는 "`get` 포함 -> `is` 포함 -> 폴백" 3갈래였고, 앞 두 갈래가 **포함(contains)** 판정이라 무접두사 접근자를 잘못 삼켰다.\
수정 후에는 같은 3갈래가 **시작(startsWith)** 판정으로 바뀌고, 각 갈래 안에 `isPlainAccessor` 하위 분기가 생겼다.

수정 전 분기도.\
`[BUG]`로 표시한 두 갈래가 결함이 살던 자리다.

```text
resolveName()
   │
   ├─ readMethod != null ?
   │      │
   │      ├─ YES ──▶ indexOf("get") != -1 ?
   │      │             │
   │      │             ├─ YES ──▶ index = 매칭위치 + 3   [BUG] 매칭위치가 0이 아닐 수 있다
   │      │             │             예: budget → 3+3=6 → ""
   │      │             │                 isTarget → 5+3=8 → ""
   │      │             │
   │      │             └─ NO ───▶ indexOf("is") != -1 ?
   │      │                           │
   │      │                           ├─ YES ─▶ index = 매칭위치 + 2  [BUG]
   │      │                           │            예: issue → 0+2=2 → "sue"
   │      │                           │                history → 2+2=4 → "tory"
   │      │                           │
   │      │                           └─ NO ──▶ index = 0   (record 폴백, gh-26029)
   │      │                                        예: name → "name"  (정상)
   │      │
   │      └─ NO ───▶ writeMethod != null ?
   │                    ├─ YES ─▶ "set" 접두사 검사 → substring(3)
   │                    └─ NO ──▶ IllegalStateException
   │
   ▼
StringUtils.uncapitalize(substring(index))
```

수정 후 분기도.\
세 갈래의 조건이 `startsWith`로 바뀌고, 접두사 갈래 안쪽에 두 번째 질문이 생겼다.

```text
resolveName()  (Property.java:135-165)
   │
   ├─ readMethod != null ?
   │      │
   │      ├─ YES ──▶ methodName.startsWith("get") ?                         :142
   │      │             │
   │      │             ├─ YES ──▶ isPlainAccessor(readMethod) ?            :143
   │      │             │             ├─ true  ─▶ index = 0   (이름 보존)
   │      │             │             │              예: getWidget 컴포넌트 → "getWidget"
   │      │             │             └─ false ─▶ index = 3   (접두사 제거)
   │      │             │                            예: getName → "name"
   │      │             │
   │      │             └─ NO ───▶ methodName.startsWith("is") ?            :145
   │      │                           │
   │      │                           ├─ YES ─▶ isPlainAccessor ?           :146
   │      │                           │           ├─ true  ─▶ index = 0
   │      │                           │           │              예: issue → "issue"
   │      │                           │           │                  isUrgent(동명 필드) → "isUrgent"
   │      │                           │           └─ false ─▶ index = 2
   │      │                           │                          예: isEnabled → "enabled"
   │      │                           │
   │      │                           └─ NO ──▶ index = 0                   :151
   │      │                                        예: name → "name", budget → "budget"
   │      │
   │      └─ NO ──▶ (setter 분기 — 이 PR에서 변경 없음)                     :155
   ▼
uncapitalize(methodName.substring(index))                                   :153
```

`isPlainAccessor` 자체도 분기 셋이다.\
어느 조건에서 빠져나가는지가 tests.md의 static 엣지 2건과 정확히 대응한다.

```text
isPlainAccessor(method)                            (Property.java:167-180)
   │
   ├─ static 메서드 ?               ──▶ YES ─▶ return false   (테스트: getLabel)
   ├─ 파라미터 0개 아님 ?           ──▶ YES ─▶ return false
   ├─ 반환 타입 void ?              ──▶ YES ─▶ return false
   │
   ▼
   getDeclaredField(method.getName())
   │
   ├─ NoSuchFieldException 등 ──▶ catch ─▶ return false   (테스트: getWidget)
   │
   ▼
   필드가 static ?
   ├─ YES ─▶ return false   (테스트: getCount)
   └─ NO  ─▶ return true    (record backing field, 데이터 클래스 필드)
```

이름이 정해진 뒤의 소비 분기도 결함의 무음성을 설명하므로 함께 둔다.

```text
getField()                                          (Property.java:238-256)
   │
   ├─ 이름이 빈 문자열 ? ──▶ YES ─▶ return null            :240   ← "budget" 케이스
   │
   ▼
   findField(declaringClass, name)
   │  ├─ 발견 ─▶ 반환
   │  └─ null ─▶ findField(uncapitalize(name))              :249   ← "sue" 케이스는
   │               └─ null ─▶ findField(capitalize(name))   :251      셋 다 실패
   │                            └─ null ─▶ return null
   ▼
  (null이면 resolveAnnotations는 필드 애노테이션 없이 진행 — 예외 없음)
```

## 4. 스프링 전역에서의 자리

BLUF: `Property`는 **타입 변환 시스템의 입력 카드**이고, 이름을 비운 채 카드를 만드는 실제 진입점은 SpEL 프로퍼티 접근자 하나였다.\
나머지 진입점은 이름을 명시로 넘긴다.

`new Property(...)` 호출처를 실제로 grep하면 프로덕션 코드에는 넷뿐이다.

```text
$ grep -rn "new Property(" --include=*.java | grep -v /test/

spring-expression/…/spel/support/ReflectivePropertyAccessor.java:152   canRead
spring-expression/…/spel/support/ReflectivePropertyAccessor.java:196   read
spring-expression/…/spel/support/ReflectivePropertyAccessor.java:254   canWrite
spring-beans/…/beans/GenericTypeAwarePropertyDescriptor.java:195       getTypeDescriptor
```

두 갈래의 성격이 다르다.\
아래는 두 진입 경로를 나란히 그린 것이다.

```text
[갈래 A] SpEL 표현식 평가 — 이 PR의 실제 노출 지점
  Expression.getValue(ctx, root)
      └─▶ PropertyOrFieldReference.readProperty  (spring-expression)  :251/:258
            └─▶ ReflectivePropertyAccessor.canRead :133 / read :174 / canWrite :240
                  ├─ findGetterForProperty(name, ...)          :389
                  │     get 접두사 → is 접두사 → 무접두사 폴백  :391/:394/:400
                  └─▶ new Property(type, method, null)         :152  ← 수정 전: 이름 없음
                        └─▶ resolveName() 실행 ★ 버그 노출

[갈래 B] 빈 프로퍼티 바인딩 — 이름을 이미 알고 있어 resolveName 미실행
  BeanWrapperImpl.convertForProperty(value, propertyName)      :180
      └─ CachedIntrospectionResults.getPropertyDescriptor(name)
      └─ ((GenericTypeAwarePropertyDescriptor) pd).getTypeDescriptor()  :187
      └─▶ GenericTypeAwarePropertyDescriptor.getTypeDescriptor :192
            └─▶ new Property(beanClass, read, write, getName()) :195  ← 이름 명시
                  └─▶ resolveName() 실행 안 함
```

갈래 A가 왜 `resolveName()`을 태웠는지는 `findGetterForProperty`의 구조가 설명한다.\
이 메서드는 요청받은 프로퍼티 이름으로 `getXxx` -> `isXxx` -> **접두사 없는 `xxx`** 순으로 찾는데(`ReflectivePropertyAccessor.java:389-408`), 세 번째 폴백이 record·Kotlin data class 접근자를 잡아 준다.\
즉 SpEL은 이미 정확한 이름을 손에 쥔 채 메서드를 찾아 놓고, 그 이름을 버리고 메서드 이름에서 다시 유도하게 만들고 있었다.

```java
// ReflectivePropertyAccessor.java:396-402
if (method == null) {
    // Plain accessor method for a data class, for example, a Java
    // record component accessor or a Kotlin data class accessor
    // such as name()
    method = findMethodForProperty(new String[] {propertyName},
            "", clazz, mustBeStatic, 0, ANY_TYPES);
}
```

이 구조적 낭비를 sbrannen이 별도로 처리했다.\
커밋 `fd95ab16baa` ("Use verified property names when constructing Property instances in SpEL", 2026-08-10, `Closes gh-37123`, `See gh-36911`)가 세 호출을 4-arg 생성자로 바꿔 이름을 그대로 넘긴다.\
그래서 **현재 HEAD에서는 갈래 A도 `resolveName()`을 타지 않는다.**\
이 PR의 수정은 그럼에도 유효한데, `Property`가 public 생성자를 노출하므로 3-arg 호출은 프레임워크 외부에서 언제든 들어올 수 있기 때문이다.

카드가 만들어진 다음 어디로 흘러가는지도 실코드로 확인된다.

```text
Property
   │
   ▼
new TypeDescriptor(property)                     TypeDescriptor.java:111
   │   resolvableType = ResolvableType.forMethodParameter(property.getMethodParameter())
   │   annotatedElementSupplier = () -> property.getAnnotations()   ← 이름이 여기서 소비된다
   ▼
ConversionService.canConvert / convert 의 소스·대상 카드로 사용
   │
   └─▶ (또는) TypeDescriptor.nested(property, level)   TypeDescriptor.java:725
```

한편 `spring-beans` 쪽에는 record 스타일 접근자를 프로퍼티로 승격시키는 별도 경로가 있다.\
`CachedIntrospectionResults.introspectPlainAccessors` (`spring-beans/…/CachedIntrospectionResults.java:332-343`)가 `isPlainAccessor`로 걸러 `GenericTypeAwarePropertyDescriptor`를 만든다.\
이 경로가 존재한다는 사실이, `spring-core`의 `Property`도 같은 모양의 메서드를 알아봐야 한다는 근거를 준다 — 두 모듈이 같은 자바 코드를 서로 다른 규칙으로 읽고 있으면 그 자체가 결함이다.

> **인트로스펙션(introspection)** — 클래스가 어떤 프로퍼티를 갖고 있는지 실행 중에 조사해 목록으로 만드는 일.\
> 예: `CachedIntrospectionResults`가 클래스를 한 번 조사해 `PropertyDescriptor` 목록을 캐시해 둔다.

## 5. 관련 개념

이 구조를 이해하는 데 필요한 개념 중 이미 별도 문서가 있는 것은 링크로 대신한다.

- 프로퍼티 관례 일반(JavaBeans 접두사 규약, record 접근자, 이름이 결합 키인 이유):
  [`../../concepts/property-accessor-conventions/property-accessor-conventions.md`](../../concepts/property-accessor-conventions/property-accessor-conventions.md)
- `Property` 객체의 수명주기·소비자·이름 유도 규칙 심화:
  [`../../concepts/property-metadata-deep-dive/property-metadata-deep-dive.md`](../../concepts/property-metadata-deep-dive/property-metadata-deep-dive.md)
- 선언 메타데이터 층과 값 런타임의 구분(왜 이름 유도가 값 없이 일어나는가):
  [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)

별도 문서가 없어 여기서 설명하는 개념은 둘이다.

**record의 backing field와 접근자 이름의 동일성.**\
`record Order(String issue)`를 컴파일하면 `private final String issue` 필드와 `public String issue()` 메서드가 함께 생성된다.\
둘의 이름이 **정확히 같다**는 것이 `isPlainAccessor`가 record API 없이도 record를 알아볼 수 있는 근거다.\
판별의 기준은 언어가 아니라 **모양**이므로, 같은 모양을 만드는 다른 언어·손코드도 자동으로 같은 규칙 아래 들어온다.\
PR 본문이 드는 예가 Kotlin의 `val isUrgent`인데, Kotlin은 `is`로 시작하는 프로퍼티에 한해 접근자 이름에 `get`을 붙이지 않고 `isUrgent()`를 그대로 쓰므로 `private final boolean isUrgent` + `isUrgent()`, 즉 record 컴포넌트 `isUrgent`와 **바이트코드상 구분 불가능한** 모양이 나온다.\
이 모양을 어느 쪽으로 읽을지가 PR 본문 "Note on impact"가 공개한 트레이드오프다.

> **바이트코드(bytecode)** — 자바 소스를 컴파일해 나온, JVM이 실제로 읽는 형태.\
> 예: Kotlin `val isUrgent`와 record 컴포넌트 `isUrgent`는 소스는 달라도 바이트코드에서는 "private final 필드 + 동명 무인자 메서드"로 똑같이 보인다.

**포함 판정과 시작 판정의 차이가 언제 드러나는가.**\
`indexOf(prefix) != -1`은 `startsWith(prefix)`보다 넓은 조건이고, 두 조건이 갈리는 입력은 "접두사를 품고 있지만 그것으로 시작하지는 않는 이름"이다.\
JavaBeans만 존재하던 시절에는 그런 입력이 애초에 들어올 수 없었으므로(읽기 메서드는 반드시 `get`/`is`로 시작) 두 조건이 관측상 동치였다.\
gh-26029가 무접두사 접근자를 입력 집합에 추가하는 순간 동치가 깨졌는데, 코드는 그대로 남아 있었다 — 조건식이 틀린 게 아니라 **전제가 사라진** 유형의 결함이다.
