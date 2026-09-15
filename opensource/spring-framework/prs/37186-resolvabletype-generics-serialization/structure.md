# PR #37186 — 무대의 실구조와 워크플로우

> PR #37186의 무대가 되는 실구조·워크플로우.\
> 문제·수정은 [README.md](README.md), 테스트는 [tests.md](tests.md), 리뷰 과정은 [review.md](review.md) 참조.
>
> 기준: 로컬 HEAD `3bb5ed1ae4f`(브랜치 `fix/typedescriptor-derived-serialization` — upstream main `89047909ea4` 리베이스 + fix 커밋).\
> **이 시점의 `ResolvableType.java`에는 이미 수정이 반영돼 있다** — 아래 file:line은 "수정 후" 좌표이고, 2절의 수정 전 워크플로우는 `gh pr diff 37186`의 `-`쪽(= 프록시 4블록이 없는 상태)으로 재구성한 것이다.

## 1. 무대 — 실구조

`ResolvableType`은 6개 필드만 스트림에 싣고 4개 캐시는 버리는 값 객체다.\
이 PR의 무대는 그중 **`type`과 `variableResolver` 두 자리**이고, 나머지 넷은 이미 직렬화를 감당하거나(Class·Integer) 애초에 실리지 않는다(transient).\
직렬화 관점에서 클래스를 다시 그리면 이렇다.

> **값 객체(value object)** — 정체성보다 담고 있는 값으로 같고 다름을 따지는 객체.\
> 예: 같은 `List<String>`을 나타내는 두 `ResolvableType`은 서로 다른 인스턴스여도 equals가 참이다.

> **transient** — "이 필드는 스트림에 싣지 말라"고 표시하는 자바 키워드.\
> 예: 계산해서 다시 채울 수 있는 캐시 필드는 transient로 두는 것이 정석이다.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ResolvableType implements Serializable                  ResolvableType.java:91│
│                                                                               │
│  [스트림에 실리는 6]                                                            │
│   Type                type            :108  ← ★ 무대 1. 무엇이 들어오냐가 관건   │
│   ResolvableType      componentType   :113    (배열일 때만; 재귀적으로 같은 규칙) │
│   TypeProvider        typeProvider    :118    Field/MethodParameter 경로 전용   │
│   VariableResolver    variableResolver:123  ← ★ 무대 2. extends Serializable   │
│   Integer             hash            :125    생성 시 미리 계산돼 함께 실림       │
│   Class<?>            resolved        :127    Class 는 직렬화 가능              │
│                                                                               │
│  [실리지 않는 4 — gh-36346(22bd8bd7043)이 transient 로 전환]                    │
│   transient volatile ResolvableType    superType            :129               │
│   transient volatile ResolvableType[]  interfaces           :131               │
│   transient volatile ResolvableType[]  generics             :133               │
│   transient volatile Boolean           unresolvableGenerics :135               │
└──────────────────────────────────────────────────────────────────────────────┘
```

`type`과 `variableResolver`에 무엇이 들어가는지는 **어느 팩토리를 탔는가**로 갈린다.\
필드·메서드 파라미터 경로는 `SerializableTypeWrapper`가 JDK Type을 직렬화 가능한 프록시로 감싸 주지만(`forType` :1538-1540 -> `SerializableTypeWrapper.forTypeProvider` — SerializableTypeWrapper.java:103), **`forClassWithGenerics`는 그 우회로를 타지 않는다** — 자기가 만든 `SyntheticParameterizedType`을 그대로 `type`에 넣는다.

```text
forField / forMethodParameter        forClass                forClassWithGenerics
        :1224 등                      :1106                       :1180
          │                             │                           │
          v                             v                           v
  typeProvider 경유                 type = Class                type = new SyntheticParameterizedType(...)
  SerializableTypeWrapper 프록시                                variableResolver = new TypeVariablesVariableResolver(...)
  (JDK Type 을 감싸 직렬화 가능)      (final·Serializable)        ← 감싸는 사람이 없다 = 이 PR의 무대
```

`VariableResolver` 계열은 인터페이스 선언부터 `extends Serializable`인데(:1575), 구현 둘의 처지가 다르다.

```text
        interface VariableResolver extends Serializable            :1575
        │  Object getSource()            (equals/hashCode 재료)     :1580
        │  ResolvableType resolveVariable(TypeVariable<?>)          :1587
        ├──────────────────────────┬───────────────────────────────────────────┐
        v                          v                                           │
┌─────────────────────────┐  ┌──────────────────────────────────────────┐      │
│ DefaultVariableResolver │  │ TypeVariablesVariableResolver      :1613 │      │
│                  :1592  │  │                                          │      │
│  ResolvableType source  │  │  TypeVariable<?>[] variables      :1615  │◄─ ★ raw JDK
│                  :1594  │  │  ResolvableType[]  generics       :1617  │   TypeVariableImpl
│  (ResolvableType 자체   │  │  resolveVariable(): 선형 탐색     :1625  │   = 비직렬화
│   → Serializable)       │  │  getSource(): this.generics       :1636  │      │
└─────────────────────────┘  │  writeReplace()                   :1640  │◄─ 이 PR 신규
                             └──────────────────────────────────────────┘      │
                                             │ writeReplace 가 바꿔치기          │
                                             v                                 │
                             ┌──────────────────────────────────────────┐      │
                             │ SerializedTypeVariablesVariableResolver  │  이 PR 신규
                             │                    implements Serializable│      │
                             │                                   :1662  │      │
                             │  Class<?>        declaringClass   :1664  │      │
                             │  ResolvableType[] generics        :1666  │      │
                             │  readResolve()                    :1673  │      │
                             └──────────────────────────────────────────┘      │
```

`type` 자리에 앉는 `SyntheticParameterizedType`도 같은 모양의 짝을 얻었다.\
자기 자신은 `Serializable`을 선언하고 있지만, **필드 `typeArguments`에 raw `TypeVariable`이 섞여 들어올 수 있다**는 것이 문제의 절반이었다.

```text
┌────────────────────────────────────────────┐        ┌────────────────────────────────────────────┐
│ SyntheticParameterizedType           :1689 │        │ SerializedSyntheticParameterizedType :1791 │
│   implements ParameterizedType,            │ write  │   implements Serializable                  │
│              Serializable                  │Replace │                                            │
│                                            │ ─────► │  Class<?> rawType              :1793       │
│  Type   rawType          :1691             │        │  Object[] encodedArguments     :1795       │
│  Type[] typeArguments    :1693 ◄─ ★ 여기에 │        │      (Integer = 타입 파라미터 인덱스,       │
│                          raw TypeVariable  │        │       그 외 = Serializable Type 원본)      │
│                          가 실릴 수 있다    │ ◄───── │                                            │
│  getRawType()            :1719             │readRes │  readResolve()                 :1802       │
│  getActualTypeArguments():1724             │  olve  │                                            │
│  equals()/hashCode()     :1729/:1736       │        └────────────────────────────────────────────┘
│  writeReplace()          :1745 ◄─ 이 PR    │
│  indexOf() (identity)    :1774 ◄─ 이 PR    │
└────────────────────────────────────────────┘
```

## 2. 수정 전 동작 워크플로우

`forClassWithGenerics`는 **인자를 그대로 쓰지 않고 "클래스의 타입 파라미터"를 두 자리에 심어 둔다** — 이것이 폭탄의 출처다.\
생성 코드(:1180-1195)를 그대로 따라가면 이렇게 된다.

```text
forClassWithGenerics(clazz, generics)                                       :1180
  │
  ├─ variables = clazz.getTypeParameters()                                  :1182
  │      → JDK 가 클래스당 한 번 만들어 캐시하는 TypeVariableImpl[] (비직렬화)
  │
  ├─ arguments[i] 채우기 (i = 0..variables.length)                          :1187-1192
  │      generic = generics[i]  (generics 가 null 이면 항상 null)
  │      argument = generic != null ? generic.getType() : null
  │      arguments[i] = (argument != null && argument 가 TypeVariable 아님)
  │                       ? argument            ← String.class 같은 정상 인자
  │                       : variables[i]        ← ★ raw TypeVariable 재주입
  │
  └─ forType(new SyntheticParameterizedType(clazz, arguments),              :1193-1194
             generics != null ? new TypeVariablesVariableResolver(variables, generics)
                              : null)
             → forType :1535 → 캐시 조회 후 ResolvableType 반환 :1552-1559
```

결과 객체 그래프를 그리면 비직렬화 JDK 객체가 실리는 자리가 정확히 둘이고, 어느 자리가 켜지는지는 **인자 모양에 따라 다르다**.

```text
ResolvableType.forClassWithGenerics(Map.class, String.class, Integer.class)

  ResolvableType
   ├ type ─────────► SyntheticParameterizedType
   │                   ├ rawType        = Map.class            [OK]
   │                   └ typeArguments  = {String.class, Integer.class}  [OK]
   ├ variableResolver► TypeVariablesVariableResolver
   │                   ├ variables      = {K, V}  ← TypeVariableImpl     [폭탄 A]
   │                   └ generics       = {RT(String), RT(Integer)}      [OK]
   ├ hash            = Integer                                           [OK]
   └ resolved        = Map.class                                         [OK]

ResolvableType.forClassWithGenerics(List.class, (ResolvableType[]) null)   // List<?>

  ResolvableType
   ├ type ─────────► SyntheticParameterizedType
   │                   ├ rawType        = List.class                     [OK]
   │                   └ typeArguments  = {E}  ← TypeVariableImpl        [폭탄 B]
   └ variableResolver = null            ← generics == null 이라 아예 안 만들어짐
```

어떤 입력에서 어느 폭탄이 켜지는지를 격자로 정리하면 이렇다.

```text
  입력 모양                              | 폭탄 A    | 폭탄 B    |
                                        | (리졸버)   | (타입인자) |
  --------------------------------------+------------+-----------+
  인자가 모두 구체 타입                   |   켜짐    |   꺼짐    |
  (Map, RT(String), RT(Integer))         |           |           |
  --------------------------------------+------------+-----------+
  generics 배열 자체가 null              |   꺼짐    |   켜짐    |
  (List, (ResolvableType[]) null)        | 리졸버를  |           |
                                        | 안 만든다  |           |
  --------------------------------------+------------+-----------+
  배열은 있고 원소가 null                 |   켜짐    |   켜짐    |
  (Map, null, null)                      |           |           |
  --------------------------------------+------------+-----------+
  타입 파라미터가 없는 클래스              |   꺼짐    |   꺼짐    |
  (String, new ResolvableType[0])        | 원래부터 잘 직렬화되던 |
                                        | 케이스                |
  --------------------------------------+------------+-----------+
```

즉 **폭탄 A(리졸버)와 폭탄 B(타입 인자)는 서로 다른 입력에서 켜지고**, `forClassWithGenerics(Map.class, (ResolvableType) null, null)`처럼 배열은 있고 원소가 null이면 **둘 다** 켜진다.\
그래서 수정도 두 클래스 각각에 필요했다.

수정 전에 이 그래프를 `ObjectOutputStream`에 넣으면 다음처럼 끝난다.\
참고로 실패 지점은 그래프를 **깊이 우선으로 훑다가** 만나는 첫 비직렬화 객체이므로, 어느 필드에서 터지는지는 위 두 모양에 따라 달라진다.

```text
oos.writeObject(resolvableType)
  │
  ├─ ResolvableType 은 Serializable            :91        → 통과
  ├─ type: SyntheticParameterizedType 도 Serializable :1689 → 통과, 내부로 진입
  │     ├ rawType = Map.class                             → Class 는 직렬화 가능
  │     └ typeArguments[i]
  │           ├ String.class 등                           → 통과
  │           └ TypeVariableImpl (폭탄 B)  ──────────────► NotSerializableException
  │                                                         "sun.reflect.generics...TypeVariableImpl"
  ├─ variableResolver: TypeVariablesVariableResolver       → VariableResolver 가
  │     │                                                    extends Serializable :1575 이라 통과
  │     ├ generics[i] = ResolvableType                     → 통과(재귀)
  │     └ variables[i] = TypeVariableImpl (폭탄 A) ──────► NotSerializableException
  │
  └─ hash / resolved / componentType / typeProvider        → 통과
```

수정 후에는 같은 경로에 게이트가 둘 끼어든다.\
**원래 실패하던 그래프만** 프록시로 바꿔치기되고, 원래 성공하던 그래프는 스트림 형식까지 그대로다.

```text
[직렬화]
oos.writeObject(resolvableType)
  │
  ├─ type: SyntheticParameterizedType.writeReplace()                 :1745
  │     └─ (게이트 통과 시) SerializedSyntheticParameterizedType 로 교체
  │            rawType = Map.class,  encodedArguments = {0, 1}  ← 인덱스로 인코딩
  │
  └─ variableResolver: TypeVariablesVariableResolver.writeReplace()  :1640
        └─ (게이트 통과 시) SerializedTypeVariablesVariableResolver 로 교체
               declaringClass = Map.class,  generics = {RT(String), RT(Integer)}

   ⇒ 스트림에는 TypeVariable 이 한 개도 실리지 않는다. 실리는 것은 "클래스 + 좌표".

[역직렬화]
ois.readObject()
  │
  ├─ SerializedSyntheticParameterizedType.readResolve()              :1802
  │     ├ 검증 3단 (3절)
  │     ├ variables = rawType.getTypeParameters()   ← ★ 재조회
  │     ├ encodedArguments[i] 가 Integer → typeArguments[i] = variables[index]
  │     │                      그 외 Type → typeArguments[i] = 그 Type 그대로
  │     └ new SyntheticParameterizedType(rawType, typeArguments)
  │
  ├─ SerializedTypeVariablesVariableResolver.readResolve()           :1673
  │     ├ 검증 3단 (3절)
  │     ├ variables = declaringClass.getTypeParameters()  ← ★ 재조회
  │     └ new TypeVariablesVariableResolver(variables, generics)
  │
  └─ ResolvableType.readResolve()                                    :1064
        └ type == EmptyType.INSTANCE 면 NONE 싱글턴으로, 아니면 this
```

위 다이어그램에서 별표로 표시한 **재조회**가 이 설계의 심장이다.\
JDK는 클래스당 제네릭 정보를 한 번만 만들어 캐시하므로 `getTypeParameters()`가 매번 같은 인스턴스를 돌려주고([JDK 제네릭 정보 instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md)), 그래서 복원본의 `TypeVariable`이 **같은 JVM에서 새로 만든 인스턴스와 `==`로 동일**하다.\
이 동일성이 성립해야 `resolveVariable`(:1625)의 선형 비교와 `SyntheticParameterizedType.equals`(:1729)·`hashCode`(:1736)가 원본과 같은 답을 낸다.

관측 하나(범위 밖): `hash`는 transient가 아니라 **송신 측 값이 그대로 실려 온다**(:125, `hashCode()`는 저장값을 그대로 반환 :1034).\
그 값의 뿌리에는 `Class.hashCode()`(identity 기반)가 있으므로, 다른 JVM에서 읽으면 저장된 hash와 그 JVM에서 재계산한 값이 갈릴 수 있다.\
이는 `forField` 경로 등에도 똑같이 있는 **기존 성질**이고 이 PR이 만든 것도, 이 PR이 손댄 것도 아니다.

## 3. 분기 처리 워크플로우

두 `writeReplace`는 **"프록시를 쓸 자격"을 각각 3분기로 심사**하고, 어느 하나라도 걸리면 `this`를 돌려 기본 직렬화로 되돌아간다.\
`this` 반환은 "수정 전과 동일하게 행동한다"는 뜻이지 "성공한다"는 뜻이 아니다 — 폭탄이 남아 있으면 예전처럼 터진다(무악화 폴백).

> **무악화(no-worse-than-before) 폴백** — 새 장치가 못 다루는 입력을 만나면 기존과 똑같이 행동하도록 물러서는 설계.\
> 예: 인코딩할 수 없는 인자를 만나면 `this`를 돌려줘서, 고치기 전에 터지던 것은 그대로 터지고 그 이상 나빠지지는 않는다.

```text
TypeVariablesVariableResolver.writeReplace()                            :1640
  │
  ├─[1] variables.length == 0 ?                                         :1641
  │        예 → return this          (실을 TypeVariable 이 없다 = 원래 잘 되던 케이스,
  │                                    스트림 형식 보존)
  │        아니오 ↓
  ├─[2] variables[0].getGenericDeclaration() 이 Class<?> 인가 ?          :1647
  │        아니오 → return this      (메서드·생성자가 선언한 변수 등 →
  │                                    Class 한 개로 재조회 불가)
  │        예 ↓
  ├─[3] Arrays.equals(this.variables, declaringClass.getTypeParameters())? :1648
  │        아니오 → return this      (한 클래스의 타입 파라미터 전체가 아님 →
  │                                    인덱스 좌표로 복원 불가)
  │        예 ↓
  └─ return new SerializedTypeVariablesVariableResolver(declaringClass, generics)  :1652
```

[3]에서 **비교의 좌우 순서가 의도적**이다.\
JDK의 `TypeVariable` 구현은 `equals`에서 자기 클래스만 받아들이므로, 래핑된 변수가 언패킹된 상대와 매칭되려면 수신자 쪽이 `this.variables`여야 한다(:1644-1646 주석).\
순서를 뒤집으면 정상 케이스가 조용히 [3]에서 탈락해 폴백으로 새어 나간다.

```text
SyntheticParameterizedType.writeReplace()                               :1745
  │
  ├─[1] rawType 이 Class<?> 인가 ?                                       :1746
  │        아니오 → return this      (getTypeParameters() 로 좌표를 못 만든다)
  │        예 ↓
  ├─[2] typeArguments 를 하나씩 인코딩                                    :1752-1767
  │        ├ indexOf(variables, argument) != -1  (identity 비교 :1774)
  │        │     → encodedArguments[i] = i번 인덱스,  encodedVariable = true   [마커 분기]
  │        ├ else argument instanceof Serializable
  │        │     → encodedArguments[i] = argument 그대로                     [원본 분기]
  │        └ else
  │              → return this       (인코딩 불가 → 예전 실패 모드 그대로)     [폴백]
  │        ↓
  └─[3] encodedVariable 인가 ?                                           :1769
           아니오 → return this      (마커가 하나도 없다 = 원래 직렬화되던 인스턴스
                                      → 스트림 형식 불변, 롤링 업그레이드 안전)
           예 → return new SerializedSyntheticParameterizedType(rawClass, encodedArguments)
```

[2]에서 **마커(identity) 검사가 `instanceof Serializable`보다 먼저**인 것도 설계 조건이었다.\
어떤 런타임에서 `TypeVariable` 구현이 `Serializable`이기도 하다면, 순서가 반대일 때 그 인자는 복사본으로 실려 나가 복원 시 정본 identity가 깨지고 `resolveVariable`이 조용히 매칭에 실패한다.\
순서가 정확성을 결정하는 분기다.

> **identity 비교(`==`)** — 값이 같은지가 아니라 **같은 객체인지**를 묻는 비교.\
> 예: 복사본은 equals로는 같아도 `==`로는 다르므로, 정본만 통과시키고 싶을 때 `==`를 쓴다.

역직렬화 쪽은 반대로 **스트림을 신뢰하지 않는 3단 검증**이다.\
두 `readResolve`가 같은 골격을 쓰되, `SerializedSyntheticParameterizedType`만 인덱스라는 추가 자유도가 있어 4단째를 갖는다.

```text
readResolve()                          :1673 (리졸버)        :1802 (타입)
  │
  ├─[1] null 검사                       declaringClass·generics   rawType·encodedArguments
  │       위반 → InvalidObjectException("Incomplete serialization proxy for ...")
  │       (기본 직렬화는 생성자를 우회하므로 final 필드도 null 로 도착할 수 있다)
  │       ↓
  ├─[2] arity 검사                       variables.length          encodedArguments.length
  │        vs                            generics.length           variables.length
  │       위반 → InvalidObjectException("Mismatched type variables/arguments for <클래스>")
  │       (버전 스큐 — 송신 측과 수신 측의 클래스 타입 파라미터 개수가 다름)
  │       ↓
  ├─[3] (타입 쪽 전용) 원소별 인코딩 검사                          :1815-1828
  │        Integer  → 범위 검사 0 <= index < variables.length
  │                     위반 → InvalidObjectException("Invalid type variable index ...")
  │        Type     → 그대로 사용
  │        그 외    → InvalidObjectException("Invalid type argument encoding ...")
  │       ↓
  └─ 실물 재구성 (2절의 재조회 경로)
```

> **arity(개수)** — 배열이나 파라미터 목록의 원소 개수.\
> 예: `Map<K,V>`의 타입 파라미터 arity는 2이고, 인코딩된 인자 배열도 2개여야 짝이 맞는다.

검증이 없다면 [2] 위반은 복원 시점이 아니라 **한참 뒤 `resolveVariable`이 조용히 null을 돌려주는 오매칭**이나 원소 접근 시 AIOOBE로 나타난다.\
세 단은 "실패를 역직렬화 지점으로 앞당기는" 장치다(자세한 원리는 [직렬화 프록시와 버전 스큐](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md)).

**버그가 살았던 분기**는 위 그림에서 프록시가 생기기 전, 즉 `writeReplace` 게이트 자체가 없던 자리다.\
반대로 SPR-17070이 의도적으로 남긴 비직렬화 영역 — `as()`(:487)·`getSuperType()`(:510)·`getInterfaces()`(:540)이 만드는 파생 인스턴스, 그리고 `resolveType()`(:917-921 javadoc "cannot be serialized") — 은 이 PR이 손대지 않았다.\
그 셋의 javadoc에는 지금도 "may not be Serializable"이 붙어 있다(:507, :537).

## 4. 스프링 전역에서의 자리

`forClassWithGenerics`는 **"클래스는 아는데 제네릭 인자를 코드로 직접 지정해야 하는" 모든 자리의 공용 생성기**다.\
main 소스에서 31곳이 호출하고, 모듈 분포는 spring-core 4 / spring-beans 1 / spring-context 1 / spring-test 3 / spring-web 7 / spring-webflux 3 / spring-webmvc 1이다(`grep -rn "forClassWithGenerics(" spring-*/src/main/java`).\
대표 진입점은 세 갈래다.

```text
[변환 서비스]  TypeDescriptor.collection(Class, TypeDescriptor)     TypeDescriptor.java:595
                 └─► ResolvableType.forClassWithGenerics(collectionType, element)      :601
               TypeDescriptor.map(Class, TypeDescriptor, TypeDescriptor)               :618
                 └─► ResolvableType.forClassWithGenerics(mapType, key, value)          :627
                        ⇒ 사용자가 직접 만나는 공개 팩토리 = 이 결함의 최대 노출면

[코덱·바디 바인딩]  FormHttpMessageReader:59 / FormHttpMessageWriter:70
                    MultipartHttpMessageReader:54 / DefaultServerWebExchange:72,74
                    BodyExtractors:52,54 / BodyInserters:63,65
                    DefaultServerRequestBuilder:317,319 / ReactiveTypeHandler:567
                        ⇒ MultiValueMap<String,String> 같은 상수 타입을 static final 로 미리 만든다

[빈 팩토리·이벤트]  ConstructorResolver:1038  → forClassWithGenerics(Class.class, clazz)
                    GenericTypeResolver:202   → ...forClassWithGenerics(rawClass, generics).getType()
                    PayloadApplicationEvent.getResolvableType():74
                                              → forClassWithGenerics(getClass(), payloadType)
```

그런데 **직렬화 결함이 실제로 아픈 곳은 생성처가 아니라 보유처**다.\
`ResolvableType`을 비-transient 필드로 들고 있으면서 자신도 `Serializable`인 클래스들이 그 폭탄을 그대로 물려받는다(`grep -rn "ResolvableType [a-zA-Z]*;" --include=*.java spring-*/src/main/java`로 확인).

```text
Serializable 이면서 ResolvableType 을 비-transient 로 보유
┌──────────────────────────────────────────────────────────────────────────────┐
│ TypeDescriptor                     :56 implements Serializable               │
│   private final ResolvableType resolvableType            TypeDescriptor.java:74│
│   ← collection()/map() 산출물이 곧바로 여기 들어간다 = 직행 노출               │
├──────────────────────────────────────────────────────────────────────────────┤
│ NoSuchBeanDefinitionException      :37 extends BeansException (RuntimeException)│
│   private final ResolvableType resolvableType   NoSuchBeanDefinitionException:41│
│   ← 예외는 원격 호출·로깅·저장 과정에서 직렬화되기 쉬운 캐리어                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ PayloadApplicationEvent<T>         :39 extends ApplicationEvent(→EventObject) │
│   private final ResolvableType payloadType     PayloadApplicationEvent.java:43│
├──────────────────────────────────────────────────────────────────────────────┤
│ UnsupportedMediaTypeStatusException:39 / UnsupportedMediaTypeException :35    │
│   private final ResolvableType bodyType              (각각 :49 / :41)         │
├──────────────────────────────────────────────────────────────────────────────┤
│ RootBeanDefinition                 :64 (→ AttributeAccessorSupport :41        │
│                                          implements Serializable)            │
│   volatile ResolvableType targetType / factoryMethodReturnType   :77 / :86    │
└──────────────────────────────────────────────────────────────────────────────┘

대조군 — transient 라서 애초에 안전한 쪽
┌──────────────────────────────────────────────────────────────────────────────┐
│ DependencyDescriptor               :49 implements Serializable               │
│   private transient volatile ResolvableType resolvableType                   │
│                                          DependencyDescriptor.java:69        │
│   ← 같은 타입을 들고도 스트림에 싣지 않는다. 그래서 이 결함의 영향권 밖.        │
│     ResolvableType 자신의 캐시 4개(:129-135)도 gh-36346 이 같은 처방을 썼다.   │
└──────────────────────────────────────────────────────────────────────────────┘
```

이 목록이 곧 **"직렬화가 실제로 일어나는 상위 맥락"의 지도**다.\
`ResolvableType`이 `Serializable`인 이유는 그 자체를 저장하려는 것이 아니라, 위 캐리어들이 통째로 실려 나가는 자리 — 세션 속성 복제(클러스터 노드 간 `HttpSession` 전파), 분산 캐시에 담긴 값 객체, 원격 경계를 건너는 예외, 이벤트 페이로드 — 를 견디기 위해서다.\
그래서 이 결함은 "단위 테스트에서 `writeObject`를 부를 때"보다 **다중 노드 배포에서 세션·캐시가 복제되는 순간** 처음 드러나는 종류였고, 컴파일도 되고 평소 실행도 멀쩡한 채 숨어 있었다.

> **세션 복제(session replication)** — 여러 서버가 같은 사용자 세션을 공유하려고 세션 내용을 서로 직렬화해 주고받는 것.\
> 예: 노드 A에서 로그인한 사용자가 노드 B로 넘어가도 로그인 상태가 유지되게 한다.

또 하나 주목할 대비: 같은 `ResolvableType`이라도 `forField`/`forMethodParameter`로 만든 것은 `SerializableTypeWrapper`(SerializableTypeWrapper.java:57)가 JDK Type을 프록시로 감싸 두어 **오래전부터 직렬화가 됐다**.\
`forClassWithGenerics`만 그 보호막 없이 살아온 것 — 이 PR은 그 한 갈래에 동등한 보호막을 다른 방식(프록시 패턴)으로 붙인 셈이다.

## 5. 관련 개념

이 구조를 읽는 데 필요한 개념은 이미 개념 문서로 분리돼 있다.\
여기서 다시 설명하지 않고 어느 대목에서 필요한지만 짚는다.

- [직렬화 프록시와 버전 스큐](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md) — 3절의 `writeReplace`/`readResolve` 게이트가 무슨 관용구이고, 스트림에 실리는 것이 왜 "identity"도 "주소"도 아닌 **이름 기반 좌표**인지.\
  `this` 반환이 왜 안전장치인지도 여기.
- [JDK 제네릭 정보 instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md) — 2절 다이어그램에서 별표로 표시한 재조회가 성립하는 근거.\
  `getTypeParameters()`가 매번 같은 인스턴스를 주는 성질이 없으면 이 설계 전체가 무너진다.
- [직렬화 학습 시리즈](../../concepts/serialization-series/00-learning-index.md) — 기본기: [직렬화 기본](../../concepts/serialization-series/03-serialization-basics.md), [transient와 volatile](../../concepts/serialization-series/04-transient-and-volatile.md)(1절의 필드 6+4 구분), [직렬화 훅](../../concepts/serialization-series/05-serialization-hooks.md)(3절 검증이 "생성자를 우회한 객체"를 왜 의심해야 하는지), [동일성과 싱글턴](../../concepts/serialization-series/08-identity-and-singleton.md)(`NONE` readResolve :1064), [serialVersionUID](../../concepts/serialization-series/11-serialversionuid.md).
- [PR #37109의 실구조](../37109-typedescriptor-serialization/structure.md) — 같은 직렬화 계열의 인접 작업.\
  그쪽 무대는 같은 `TypeDescriptor`의 **애너테이션 공급자 필드**이고, 이쪽 무대는 그 옆의 `resolvableType` 필드(TypeDescriptor.java:74)가 가리키는 그래프다.\
  두 문서를 겹쳐 읽으면 `TypeDescriptor` 네 필드의 직렬화 사정이 전부 채워진다.
