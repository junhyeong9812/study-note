# 스프링의 타입 메타데이터 층 — 제네릭 정보는 어떻게 표현·해석·보존되는가

> 기준 커밋: upstream `main` 526c706d1c3 (`Merge branch '7.0.x'`).
> [컴파일 타임과 두 개의 런타임](../compile-runtime-layers/compile-runtime-layers.md)이 "층이 셋이고 스프링의 타입
> 판별 코드는 2층에 있다"는 **개념**을 세운다면, 이 문서는 그 2층의 **실구조**를 읽는다.
> 개념 정리가 필요하면 그 문서를 먼저 보고 오는 편이 낫다.

## 0. 한 문장으로

스프링의 2층은 사실상 `ResolvableType` 하나로 이루어져 있고, 그 클래스는 **네 개의 필드**로
"이 타입이 무엇인가(`type`)", "어디서 왔는가(`typeProvider`)", "타입 변수를 누구에게 물어볼
것인가(`variableResolver`)", "배열이면 원소는 무엇인가(`componentType`)"를 표현한다. 제네릭
해석이란 이 네 필드를 들고 상위 타입을 걸어 올라가며 `TypeVariable`을 실제 타입으로 치환하는
작업이고, `SerializableTypeWrapper`는 그 과정에서 손에 쥔 JDK `Type`이 직렬화 불가일 때
"어느 필드/파라미터에서 왔는지"라는 좌표로 바꿔 보존하는 장치다. `MethodParameter`와
`TypeDescriptor`는 이 층 위에 각각 "선언 위치"와 "변환용 카드"를 얹은 것이다.

## 1. ResolvableType의 필드가 곧 설계다

`ResolvableType`은 JDK `Type` 하나를 감싸는 불변 값 객체이며, 필드는 다음과 같다
(`ResolvableType.java:103-133`).

- `type` — 감싸고 있는 실제 `java.lang.reflect.Type`. `Class`일 수도, `ParameterizedType`,
  `TypeVariable`, `WildcardType`, `GenericArrayType`일 수도 있다. 정보 없음은 `null`이 아니라
  `EmptyType.INSTANCE`이며 그 래퍼가 공개 상수 `NONE`이다(95행). 스프링이 `null` 대신 `NONE`을
  쓰는 이유는 `t.as(...).getGeneric(0).resolve()` 같은 체이닝을 NPE 없이 이어 붙이기 위해서다.
- `typeProvider` — `type`을 **다시 얻어 오는 방법**. 6절의 주인공이다.
- `variableResolver` — `TypeVariable`을 만났을 때 물어볼 상대. 보통은 "나를 만든 소유 타입"이다.
- `componentType` — 배열의 원소 타입을 명시적으로 지정한 경우에만 채워지고, 아니면 `type`에서
  유도한다(`getComponentType`, 433-448행).

여기에 캐시성 필드가 붙는다. `hash`는 캐시 키로 쓰기 위한 사전 계산값, `resolved`는 해석된
`Class`, `superType`/`interfaces`/`generics`는 지연 계산 결과다(123-131행). `resolved`가 미리
채워진다는 점이 중요하다 — 공개 메서드 `resolve()`는 계산하지 않고 필드를 그대로 돌려준다
(882-884행). **해석 비용은 생성 시점에 한 번 치르고, 조회는 공짜**라는 설계다.

생성자가 넷인 것도 이 사정 때문이다(140-194행). 캐시 **키**용(해석 안 함), 캐시 **값**용
(해석함 + hash 전달), 일반용(해석함 + hash 지연), 그리고 `Class` 전용 지름길이다. 마지막 것은
`instanceof` 검사를 전부 건너뛴다 — 스프링이 가장 자주 만드는 것이 평범한 `Class` 래퍼이기
때문이다.

## 2. 생성 경로별 특성

어느 팩토리로 만들었느냐에 따라 위 네 필드의 채움새가 달라지고, 그것이 그대로 능력 차이가
된다.

| 팩토리 | type | typeProvider | variableResolver | 직렬화 |
|---|---|---|---|---|
| `forClass(C)` | `C` (Class) | 없음 | 없음 | 가능(Class는 Serializable) |
| `forRawClass(C)` | `C` (Class) | 없음 | 없음 | 제네릭을 항상 빈 배열로 보고(1120-1136행) |
| `forClassWithGenerics(C, G...)` | `SyntheticParameterizedType` | 없음 | `TypeVariablesVariableResolver` | 가능(합성 타입이 Serializable) |
| `forField(f)` | 프록시 또는 `Class` | `FieldTypeProvider` | 없음(또는 owner) | 가능 |
| `forMethodParameter(mp)` | 프록시 또는 `Class` | `MethodParameterTypeProvider` | owner의 resolver | 가능 |
| `forType(t, owner)` | `t` 그대로 | 없음 | `owner.asVariableResolver()` | `t`에 달림 |

두 가지가 눈에 띈다. 첫째, **`forClassWithGenerics`는 존재하지 않는 선언을 지어낸다.**
`List<String>`이라고 선언된 곳이 없어도 필요하면 만들어야 하므로,
`SyntheticParameterizedType`이라는 자체 `ParameterizedType` 구현을 조립하고
(`ResolvableType.java:1185-1192`, 클래스 정의는 1640행) 동시에 타입 변수 -> 지정 제네릭의
직접 매핑인 `TypeVariablesVariableResolver`를 함께 단다(1611-1637행). `TypeDescriptor.collection(...)`이
이 경로를 쓴다(`TypeDescriptor.java:595-601`).

둘째, **선언에서 온 것(`forField`/`forMethodParameter`)만 `typeProvider`를 갖는다.** 선언
좌표가 있어야 나중에 재구성할 수 있기 때문이며, 이것이 6절의 전제다.

## 3. 워크플로 (1) — 필드의 `List<String>`이 해석되는 흐름

가장 흔한 경로를 끝까지 따라가 보자. 대상은 `private List<String> names;`이고 호출은
`ResolvableType.forField(field).getGeneric(0).resolve()`다.

```
ResolvableType.forField(field)                                 ResolvableType.java:1222
  └─ forType(type=null, typeProvider=FieldTypeProvider(field), variableResolver=null)
        │                                                      ResolvableType.java:1533
        │  type 이 null 이고 provider 가 있으므로
        ▼
     SerializableTypeWrapper.forTypeProvider(provider)          SerializableTypeWrapper.java:103
        │  provider.getType() = field.getGenericType()
        │      = ParameterizedType "java.util.List<java.lang.String>"  (JDK 내부 구현체)
        │  이것은 Serializable 이 아니다  →  프록시로 감싼다
        ▼
     Proxy[ ParameterizedType, SerializableTypeProxy, Serializable ]
        handler = TypeProxyInvocationHandler(FieldTypeProvider)
        │
        ▼
   new ResolvableType(type=프록시, typeProvider=FieldTypeProvider, variableResolver=null)
        └─ 생성자에서 resolveClass() 를 즉시 수행                ResolvableType.java:901
              type 이 Class 도 GenericArrayType 도 아님 → resolveType()      920행
              type 이 ParameterizedType → forType(getRawType(), variableResolver)
                 └ getRawType() 호출이 프록시를 지나며
                   Type 반환 · 무인자 메서드이므로 다시 감싸려 시도          186-202행
                   → 이번엔 실제 값이 List.class = Serializable → 그대로 반환 105-108행
              → resolved = List.class

   .getGeneric(0)                                              ResolvableType.java:783
        type 이 ParameterizedType 이므로 getActualTypeArguments()
          └ Type[] 반환 메서드 → 원소마다 MethodInvokeTypeProvider 로 감싸기 시도
            원소 실제 값 = String.class = Serializable → 그대로 반환
        → forType(String.class, variableResolver=null)
   .resolve()  →  String.class
```

읽어 낼 성질 셋. 첫째, **`Class`는 절대 프록시되지 않는다** — `Class`가 이미 `Serializable`이므로
`forTypeProvider`가 즉시 원본을 돌려준다(`SerializableTypeWrapper.java:104-108`). 그래서
`private String name;` 같은 평범한 필드는 프록시가 전혀 만들어지지 않는다. 둘째, 해석은
`resolveType()`이라는 **한 단계 벗기기**의 반복이다(920-943행) — `ParameterizedType`은 raw
타입으로, `WildcardType`은 상·하한으로, `TypeVariable`은 resolver에게 물어 한 겹씩 줄어든다.
셋째, `forType`은 `Class`가 아닌 타입에 대해서만 정적 캐시를 조회한다(1543-1557행) —
`Class` 래퍼는 만드는 게 캐시 조회보다 싸다는 판단이다.

## 4. 해석 엔진 — resolveType과 variableResolver

`TypeVariable`을 만나면 `resolveType()`은 `variableResolver`에게 넘긴다(931-940행). 구현은 둘뿐이다.

`DefaultVariableResolver`는 "나를 만든 `ResolvableType`에게 되묻기"다(1590-1607행).
`asVariableResolver()`가 자기 자신을 감싸 만들며, `NONE`이면 `null`을 준다(1052-1057행).
실제 계산은 `ResolvableType.resolveVariable`이 한다(945-983행). 이 메서드가 이 층의 심장이다.

- `type`이 `ParameterizedType`이면 raw 클래스의 타입 파라미터 배열과 실제 인자 배열을 나란히
  놓고 이름이 아니라 **객체 동일성**으로 짝을 찾는다(955-961행).
- 못 찾으면 `ownerType`으로 한 번 더(962-965행), 그래도 못 찾으면 마지막에 **이름으로**
  비교하는 폴백이 있다(966-971행). 선언 컨텍스트가 달라 동일성이 깨지는 경우를 위한 안전망이다.
- 어느 쪽도 아니면 자신의 `variableResolver`에게 위임한다(979-981행) — 이 위임이 상위 타입
  사슬을 타고 내려가는 재귀를 만든다.

`TypeVariablesVariableResolver`는 반대로 "미리 받은 표에서 찾기"다(1611-1637행).
`forClassWithGenerics`로 만든 합성 타입에는 되물을 상위 타입이 없으므로, 변수 배열과 제네릭
배열을 직접 짝지어 둔다.

`equals`/`hashCode`가 `type`뿐 아니라 `typeProvider.getType()`과 `variableResolver.getSource()`까지
비교한다는 점도 여기서 이해된다(991-1047행). 같은 `List<E>`라도 **어느 소유 타입 아래서
해석되느냐에 따라 결과가 다르므로**, 캐시 키에 resolver의 정체가 반드시 포함돼야 한다.

## 5. 워크플로 (2) — as(Collection.class)가 TypeVariable을 해석하는 흐름

`as(Class)`는 상위 타입 사슬을 걸어 올라가며 목표 타입을 찾는다(485-500행). 인터페이스를
먼저 재귀 탐색하고, 실패하면 상위클래스로 간다. 걸어가는 동안 각 단계가 앞 단계를 owner로
잡으므로(`getSuperType`은 `forType(superclass, this)`, 520행) **resolver 사슬이 자동으로
엮인다.** `class StringList extends ArrayList<String> {}`로 확인해 보자.

```
ResolvableType.forClass(StringList.class)              type=StringList.class, resolver=없음
   │  .as(Collection.class)                            485행
   │     resolved=StringList ≠ Collection → 인터페이스 없음 → getSuperType()
   ▼
RT_A : type = ParameterizedType  ArrayList<String>     resolver = Default(StringList RT)
   │     resolved = ArrayList ≠ Collection → getInterfaces()  538행
   ▼
RT_B : type = ParameterizedType  List<E_ArrayList>     resolver = Default(RT_A)
   │     resolved = List ≠ Collection → getInterfaces()
   ▼
RT_C : type = ParameterizedType  Collection<E_List>    resolver = Default(RT_B)
         resolved = Collection == Collection → 여기서 반환

   .getGeneric(0)                                      783행
      actualTypeArguments[0] = E_List (TypeVariable)
      → forType(E_List, resolver = RT_C 의 variableResolver = Default(RT_B))
   .resolve()  →  resolveClass → resolveType → variableResolver.resolveVariable(E_List)

      RT_B.resolveVariable(E_List)                     945행
        type = List<E_ArrayList> (ParameterizedType)
        List 의 타입 파라미터 [E] 와 E_List 가 동일 → 인자 E_ArrayList 를 채택
        → forType(E_ArrayList, RT_B 의 resolver = Default(RT_A))
             다시 TypeVariable 이므로 한 번 더 위임
             RT_A.resolveVariable(E_ArrayList)
               type = ArrayList<String>
               ArrayList 의 타입 파라미터 [E] 와 일치 → 인자 String.class 채택
        → String.class
```

한 문장으로 줄이면, **`as()`는 타입 변수를 해석하지 않고 "해석할 수 있는 사슬"만 만들어
둔다.** 실제 치환은 `resolve()`가 호출되는 순간 그 사슬을 거슬러 내려가며 일어난다. 사슬의
각 칸이 자기 바로 위 칸만 알면 되고, 그것이 이 층이 임의 깊이의 제네릭 상속을 다룰 수 있는
이유다. `TypeDescriptor.getElementTypeDescriptor()`가 `getResolvableType().asCollection().getGeneric(0)`
한 줄인 것도(`TypeDescriptor.java:377`) 이 사슬을 믿기 때문이다.

## 6. SerializableTypeWrapper — 좌표로 바꿔 보존하기

문제의 형태부터 정확히 하자. `ResolvableType`은 `Serializable`을 구현한다(89행). 그런데 그
핵심 필드인 `type`에 들어가는 JDK `Type` 구현체는 대체로 직렬화 대상이 아니다 —
`java.lang.Class`는 `Serializable`이지만, `getGenericType()`이 돌려주는
`ParameterizedTypeImpl` 같은 JDK 내부 구현체는 그렇지 않다. 스프링이 `ResolvableType`을 담은
객체(예: 캐시된 `TypeDescriptor`)를 직렬화하려면 이 간극을 메워야 한다.

해법은 **"타입 자체를 저장하는 대신, 타입을 다시 얻는 방법을 저장한다"**이다. 그 방법이
`TypeProvider`이고(`SerializableTypeWrapper.java:150-164`), 직렬화 가능한 형태로 감싼 것이
`Type` 인터페이스의 동적 프록시다.

```
                       forTypeProvider(provider)          SerializableTypeWrapper.java:103
                                 │
              providedType = provider.getType()
                                 │
         ┌───────────────────────┴────────────────────────┐
         │ Serializable 인가?                              │
         ▼ 예 (예: Class)                                  ▼ 아니오
   원본을 그대로 반환                            지원 4종인지 확인   (59-60행)
   (프록시 없음, 104-108행)                      GenericArrayType /
                                                ParameterizedType /
                                                TypeVariable / WildcardType
                                                       │
                                                       ▼
                              Proxy.newProxyInstance(
                                  interfaces = { 해당 Type 종류,
                                                 SerializableTypeProxy,
                                                 Serializable },
                                  handler    = TypeProxyInvocationHandler(provider) )
                                                       │  (120-129행, 프록시는 캐시됨)
                                                       ▼
                              호출이 프록시를 지날 때 (invoke, 182행)
                                ├ equals/hashCode → provider.getType() 기준으로 위임
                                ├ getTypeProvider() → provider 반환 (unwrap 용)
                                ├ 반환형이 Type    → MethodInvokeTypeProvider 로 다시 감쌈
                                ├ 반환형이 Type[]  → 원소마다 index 를 기억해 다시 감쌈
                                └ 그 외           → 실제 타입에 그대로 위임
```

두 가지 설계 결정이 이 그림에 있다.

**전이적 보존.** `Type`을 반환하는 메서드의 결과를 다시 감싸기 때문에
(`SerializableTypeWrapper.java:200-213`), `ParameterizedType`에서 꺼낸 타입 인자도, 그 인자가
또 제네릭이면 그 안쪽도 직렬화 가능한 상태를 유지한다. 감쌀 때 쓰는
`MethodInvokeTypeProvider`는 "어느 provider의, 어느 메서드의, 몇 번째 결과"라는 좌표만
저장하고 실제 호출은 필요할 때 한 번 수행해 캐시한다(322-354행). 3절에서 본 대로 결과가
이미 `Serializable`이면 감싸지 않고 원본을 통과시키므로, 프록시는 필요한 곳에만 생긴다.

**좌표의 정체.** 루트 provider 둘이 저장하는 것은 타입이 아니라 **선언 위치**다.
`FieldTypeProvider`는 선언 클래스와 필드 이름을(229-262행), `MethodParameterTypeProvider`는
선언 클래스·메서드 이름·파라미터 타입들·파라미터 인덱스를(269-315행) 담고, 역직렬화 시
`readObject`에서 `getDeclaredField`/`getDeclaredMethod`로 원본을 다시 찾는다. 찾지 못하면
`IllegalStateException("Could not find original class structure")`으로 명시 실패한다.
[compile-runtime-layers.md](../compile-runtime-layers/compile-runtime-layers.md)의 표현을 빌리면, 이 층은 값이 아니라
**선언을 가리키는 주소**를 직렬화하는 셈이다.

반대 방향도 있다. `unwrap`은 프록시에서 원본 `Type`을 꺼낸다(89-96행). 공개 API
`ResolvableType.getType()`이 이것을 거치므로(200-202행) **밖에서는 프록시가 보이지 않는다.**
`resolveVariable`이 비교 전에 `unwrap`을 부르는 것도(946행) 같은 이유다 — 프록시와 원본을
섞어 비교하면 동일성 판정이 깨진다.

마지막으로 환경 분기 하나. GraalVM 네이티브 이미지처럼 타입 아티팩트가 애초에 직렬화되지
않는 런타임에서는 감싸기 시도 자체를 건너뛰고 원본을 그대로 쓴다(109-113행). 프록시 생성
비용과 리플렉션 등록 부담을 피하기 위한 선택이다.

## 7. 위에 얹히는 것들 — MethodParameter와 TypeDescriptor

**`MethodParameter`**는 "메서드/생성자의 파라미터(또는 반환값) 한 자리"를 가리키는 좌표
객체다. 보유하는 것은 `Executable`과 `parameterIndex`이며, 파라미터 타입·제네릭 타입·
annotation 등을 지연 계산해 `volatile` 필드에 캐시한다(`MethodParameter.java:72-99`).
`nestingLevel`과 `typeIndexesPerLevel`이라는 개념이 있어 `List<Optional<String>>`처럼 중첩된
자리를 "몇 겹 안쪽의 몇 번째 인자"로 지목할 수 있다(359-381행).

이 좌표를 `ResolvableType`으로 바꾸는 다리가 `forMethodParameter`다
(`ResolvableType.java:1403-1412`).

```java
ResolvableType owner = implementationType.as(methodParameter.getDeclaringClass());
return forType(null, new MethodParameterTypeProvider(methodParameter), owner.asVariableResolver())
        .getNested(methodParameter.getNestingLevel(), methodParameter.typeIndexesPerLevel);
```

세 층이 한 문장에 다 있다. `as(...)`로 5절의 resolver 사슬을 만들고, `MethodParameterTypeProvider`로
6절의 좌표를 심고, `getNested(...)`로 중첩 위치를 파고든다. 구현 클래스가 선언 클래스와 다를
때(제네릭 인터페이스를 구현한 빈의 메서드 같은 경우) 파라미터의 타입 변수가 실제 타입으로
풀리는 것이 바로 첫 줄의 효과다.

**`TypeDescriptor`**는 변환 시스템이 쓰는 카드이며, 필드가 셋뿐이다
(`TypeDescriptor.java:72-76`): `resolvableType`, 해석된 `type`, 그리고 annotation 공급자.
생성자 셋(`MethodParameter`/`Field`/`Property`)이 하는 일은 동일한 패턴이다
(87-115행) — 대응하는 `ResolvableType` 팩토리를 부르고, `resolve(...)`에 **폴백을 주어**
해석 실패 시에도 최소한 소거된 타입은 확보한다.

```java
this.resolvableType = ResolvableType.forField(field);
this.type = this.resolvableType.resolve(field.getType());   // 폴백 = 소거된 타입
```

그 위의 편의 메서드는 모두 `resolvableType`으로의 위임이다. `getElementTypeDescriptor()`는
배열이면 `getComponentType()`, `Stream`이면 `as(Stream.class).getGeneric(0)`, 그 외에는
`asCollection().getGeneric(0)`으로 갈린다(370-377행). `upcast(...)`는 `as(superType)`(234-239행),
`narrow(value)`는 값의 실제 클래스를 기존 타입을 owner로 삼아 다시 감싼다(218-222행).
정리하면 **`TypeDescriptor` = `ResolvableType` + annotation + 변환용 어휘**이며, 새로운 타입
해석 능력을 더하지는 않는다.

## 8. 캐시 지도

이 층도 캐시가 성능의 전제다.

| 캐시 | 키 -> 값 | 위치 | 비고 |
|---|---|---|---|
| ResolvableType | `ResolvableType` -> `ResolvableType` | `ResolvableType.java:99` | `Class` 래퍼는 캐시하지 않음(1543-1547행) |
| 타입 프록시 | `Type` -> `Type` | `SerializableTypeWrapper.java:62` | 같은 원본에 프록시 하나 |
| 인스턴스 내부 | `superType`/`interfaces`/`generics`/`resolved` | `ResolvableType.java:125-133` | 지연 계산 후 보관 |
| TypeDescriptor 공통 | `Class` -> `TypeDescriptor` | `TypeDescriptor.java:58` | 기동 시 고정 적재, `valueOf`가 조회(579행) |

앞의 두 정적 캐시는 `ConcurrentReferenceHashMap`이라 GC 압력이 오면 스스로 비워지고,
`ResolvableType.clearCache()` 호출 시에는 **함께** 비워진다(1564-1567행) — 프록시 캐시가
`ResolvableType` 캐시의 값에 물려 있으므로 따로 비우면 정합성이 깨지기 때문이다. 반면
`commonTypesCache`는 기동 시 한 번 채우고 끝나는 고정 표라 평범한 `HashMap`이다.

## 9. 코드를 읽을 때의 판별 질문

첫째, 이 `ResolvableType`에 **`variableResolver`가 있는가?** 없으면 타입 변수를 만나는 즉시
상한(bound)으로 폴백한다(940행) — `List<E>`가 `List<Object>`처럼 보이는 현상 대부분이 여기서
온다. 둘째, **`typeProvider`가 있는가?** 있으면 선언에서 온 타입이고 좌표가 남아 있다.
`forType(someType, ...)`로 직접 만든 것은 좌표가 없다. 셋째, 지금 보는 값이 **`getType()`으로
꺼낸 것인가 필드 `type`인가?** 전자는 `unwrap`을 거친 원본, 후자는 프록시일 수 있다 —
동일성 비교를 다룰 때 이 구분이 결과를 바꾼다.

## 10. 한 문장 요약

스프링의 타입 메타데이터 층은 `ResolvableType`의 네 필드(`type`/`typeProvider`/`variableResolver`/
`componentType`)로 선언 타입을 표현하고, 상위 타입을 걸어 올라가며 엮은 resolver 사슬을
거슬러 내려가 `TypeVariable`을 치환하는 방식으로 제네릭을 해석하며, 직렬화가 필요한 자리에서는
`SerializableTypeWrapper`가 JDK `Type`을 "어느 선언에서 왔는가"라는 좌표로 바꿔 보존한다.
`MethodParameter`는 그 좌표를 표현하는 객체이고, `TypeDescriptor`는 그 위에 annotation을 얹어
변환 시스템에 건네는 카드다.
