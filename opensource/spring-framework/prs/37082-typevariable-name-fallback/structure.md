# PR #37082 — 무대 구조와 워크플로우: ResolvableType의 타입 변수 해석

> PR #37082의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. `resolveVariable`의 이름 폴백(`ResolvableType.java:966-971`)은 아직 PR 이전 상태(조건 없는 폴백)다.

## 1. 무대 — 실구조

이 PR의 무대는 자바 리플렉션의 `Type` 계층을 스프링이 감싼 `ResolvableType`, 그중에서도 **타입 변수를 실인자로 바꾸는 해석 경로**다. 무대에 서는 배우는 셋이다. 값 객체이자 해석 엔진인 `ResolvableType`, 그 객체가 "내가 모르는 변수는 이 사람에게 물어봐"라고 위임하는 `VariableResolver` 체인, 그리고 클래스 계층 전체를 훑으며 후보를 순서대로 시도하는 상위 진입점 `GenericTypeResolver`다. 버그는 가장 안쪽 `resolveVariable`의 마지막 폴백 하나에 있었다.

먼저 `ResolvableType`의 실제 모양이다. 필드가 무엇을 들고 있는지가 해석 알고리즘의 절반을 설명한다.

```
 ResolvableType implements Serializable                      ResolvableType.java:89
   ├─ static final ResolvableType NONE                                    :95
   │     "값 없음" 을 null 대신 표현하는 싱글턴 (EmptyType.INSTANCE 기반)
   ├─ static final ConcurrentReferenceHashMap<ResolvableType,ResolvableType> cache  :99
   ├─ final Type type                       ← 감싼 원본 java.lang.reflect.Type      :106
   ├─ final @Nullable ResolvableType componentType                                  :111
   ├─ final @Nullable TypeProvider typeProvider   ← 직렬화 가능한 Type 출처         :116
   ├─ final @Nullable VariableResolver variableResolver  ★ 변수 해석 위임처         :121
   ├─ @Nullable Class<?> resolved           ← 생성 시 resolveClass() 로 미리 계산   :125
   ├─ transient volatile superType / interfaces / generics  ← 지연 캐시  :127-131
   │
   ├─ resolveClass()                private                                  :901
   ├─ resolveType()                 package-private, 한 단계만 풀기           :920
   ├─ resolveVariable(TypeVariable) private  ★ 이 PR 의 대상                  :945
   ├─ getGenerics()                                                          :783
   ├─ asVariableResolver()          this 를 VariableResolver 로 감싼다        :1052
   ├─ static forType(Type)                                                   :1481
   ├─ static forType(Type, ResolvableType owner)   ← owner 를 resolver 로     :1494
   ├─ static forType(Type, VariableResolver)                                 :1521
   ├─ static forClass(Class)                                                 :1104
   ├─ static forClassWithGenerics(Class, ResolvableType...)                  :1178
   ├─ static forVariableBounds(TypeVariable)                                 :1463
   └─ static resolveBounds(Type[])  bounds[0]==Object.class 면 null           :1467
```

변수 해석의 위임 구조는 인터페이스 하나와 구현 둘로 되어 있다. 둘의 차이가 "누구에게 물어보는가"를 가른다.

```
 interface ResolvableType.VariableResolver extends Serializable      :1573
   ├─ Object getSource()                                             :1578
   └─ @Nullable ResolvableType resolveVariable(TypeVariable<?>)      :1585
        △
        ├── DefaultVariableResolver                                  :1590
        │     final ResolvableType source                            :1592
        │     resolveVariable(v) → source.resolveVariable(v)         :1599-1601
        │       ↳ 즉 "어떤 ResolvableType 하나에게 통째로 되묻는" 어댑터
        │         asVariableResolver() 가 만든다                      :1052-1057
        │
        └── TypeVariablesVariableResolver                            :1611
              final TypeVariable<?>[] variables / ResolvableType[] generics  :1613-1615
              resolveVariable(v) → variables[i] 와 v 를 equals 비교해 generics[i] 반환  :1623-1631
                ↳ forClassWithGenerics 가 만드는 "미리 짝지어 둔 표"   :1191-1192
                  ★ 이쪽은 동일성 비교만 하고 이름 폴백이 없다

 SyntheticParameterizedType implements ParameterizedType             :1640
   ├─ final Type rawType / final Type[] typeArguments                :1642-1644
   └─ getOwnerType() → 항상 null                                     :1665-1667
        ↳ forClassWithGenerics 로 만든 타입은 owner 가 없다 = 이름 폴백에 도달한다
```

상위 진입점은 `GenericTypeResolver`다. 이쪽은 클래스 계층을 넓이 방향으로 훑으며 `ResolvableType`에게 반복해서 묻는 역할만 한다.

```
 GenericTypeResolver (abstract utility)                    GenericTypeResolver.java
   ├─ public static Type resolveType(Type genericType, @Nullable Class<?> contextClass)   :154
   │     ├─ genericType 이 TypeVariable 이면 ─→ resolveVariable(...) 후 bounds 폴백   :156-172
   │     └─ genericType 이 ParameterizedType 이면 ─→ 미해석 인자마다 같은 처리        :173-205
   └─ private static ResolvableType resolveVariable(TypeVariable<?>, ResolvableType contextType)  :210
         ├─ contextType.hasGenerics() 이면 asVariableResolver() 로 직접 질의   :212-224
         ├─ superType 으로 재귀                                                :226-232
         ├─ 모든 인터페이스로 순서대로 재귀                                     :233-238
         └─ 못 찾으면 ResolvableType.NONE                                      :239
```

세 배우를 하나로 겹치면 이런 그림이 된다. 화살표는 "묻는 방향"이다.

```
  GenericTypeResolver.resolveType(genericType, contextClass)      :154
        │  후보를 순서대로 시도 (자기 자신 → superType → interfaces)
        ▼
  GenericTypeResolver.resolveVariable(typeVariable, contextType)  :210
        │  contextType.asVariableResolver()
        ▼
  DefaultVariableResolver.resolveVariable(v)                      :1599
        │  source.resolveVariable(v)
        ▼
  ResolvableType.resolveVariable(v)          ★ 실제 매칭이 일어나는 곳   :945
        ├─ 1) 변수 동일성 비교 (이름 + 선언)                       :957-961
        ├─ 2) owner 타입으로 재귀 (중첩 타입)                      :962-965
        ├─ 3) 이름만 비교하는 폴백                                 :966-971  ★ 버그
        ├─ 4) 와일드카드면 resolveType() 으로 한 단계 풀고 재시도    :973-978
        └─ 5) 자기 variableResolver 에게 넘김                      :979-981
```

## 2. 수정 전 동작 워크플로우

타입 변수 해석은 "묻는 대상을 계층 위로 옮겨 가며 후보를 시도하고, 첫 성공을 답으로 삼는" 구조다. 성공/실패의 판정이 안쪽 `resolveVariable` 한 곳에 있으므로, 그 한 곳이 틀린 답을 내면 상위 탐색이 조기에 멈춘다. 시나리오 세 개로 따라간다.

### 시나리오 A — 정상 해석 (중첩 선언, `Create<I,O>` @ `Controller`)

`GenericTypeResolverTests` 안에 중첩으로 선언된 기존 픽스처의 경로다.

```
 resolveType(Create#create 의 파라미터 타입 I, Controller.class)      GenericTypeResolver.java:154
   genericType 은 TypeVariable "I" (선언: interface Create)
   └→ resolveVariable(I, ResolvableType.forClass(Controller))         :157-158 → :210
        Controller 는 제네릭이 없다 → hasGenerics() false → 표 질의 건너뜀    :212
        superType = Object → NONE 이 아니므로 재귀했다가 실패              :226-232
        for (ifc : Controller.getInterfaces())                             :233
          ifc[0] = Search<String, Long>   ← ParameterizedType
            └→ resolveVariable(I, Search<String,Long>)                     :234
                 hasGenerics() true → asVariableResolver()                 :212-213
                   → DefaultVariableResolver(source = Search<String,Long>) :1590
                     → source.resolveVariable(I)      ResolvableType.java:945
                        this.type 은 ParameterizedType                     :950
                        resolved = Search.class                            :951
                        variables      = Search 의 [I, O]                  :955
                        typeArguments  = [String, Long]                    :956
                        1) 동일성 비교: Search 의 I 와 Create 의 I 는
                           getGenericDeclaration() 이 달라 equals 실패      :957-960
                        2) ownerType = GenericTypeResolverTests (중첩 선언이므로 not null)
                           → forType(owner).resolveVariable(I)             :962-964
                             owner 는 Class 라 위 분기 어디에도 걸리지 않고 null 반환
                           ★ return 이므로 3) 이름 폴백에 도달하지 않는다
                 결과 null → NONE                                          :218
          ifc[1] = Create<Long, Long>
            └→ 1) 동일성 비교 성공 (같은 Create 선언의 I)  → typeArguments[0] = Long
        → Long
```

여기서 핵심은 2)의 `return`이다. **owner가 있으면 그 결과가 무엇이든 즉시 반환**되므로 이름 폴백은 실행되지 않는다. 중첩 선언 픽스처가 "우연히" 옳은 답을 낸 이유가 이것이다.

### 시나리오 B — 수정 전 오답 (최상위 선언, `TopCreate<I,O>` @ `TopController`)

같은 구조를 파일 최상위에 선언하면 owner가 사라지고 3)에 도달한다.

```
 interface TopSearch<I, O> {}
 interface TopCreate<I, O> { default O create(I body) {...} }
 class TopController implements TopSearch<String, Long>, TopCreate<Long, Long> {}

 resolveVariable(TopCreate 의 I, forClass(TopController))       GenericTypeResolver.java:210
   for (ifc : interfaces)                                                     :233
     ifc[0] = TopSearch<String, Long>
       └→ ResolvableType.resolveVariable(I)                    ResolvableType.java:945
            resolved       = TopSearch.class
            variables      = TopSearch 의 [I, O]
            typeArguments  = [String, Long]
            1) 동일성 : TopSearch#I != TopCreate#I  (선언이 다름) → 실패      :957-960
            2) ownerType : 최상위 인터페이스이므로 null → 분기 자체를 타지 않음 :962-963
            3) 이름 폴백 : variables[0].getName()=="I" == variableToCompare.getName()=="I"
                 → return forType(typeArguments[0]) = String                  :967-970
                   ★ 선언 문맥을 무시했으므로 형제 인터페이스의 인자를 가져왔다
       → String 이 NONE 이 아니므로 루프는 여기서 끝난다                       :235-237
     ifc[1] = TopCreate<Long, Long>  ← 도달조차 하지 못한다
 결과 String   (기대: Long)
```

owner 유무 하나로 같은 구조가 다른 답을 내는 것이 이 결함의 성질이다. JDK 리플렉션이 실제로 그렇게 동작한다.

```
  TOP  TopSearch      ownerType = null            → 3) 이름 폴백에 도달
  TOP  TopCreate      ownerType = null
  NEST Probe$Search   ownerType = class Probe     → 2) 에서 즉시 반환, 3) 미도달
  NEST Probe$Create   ownerType = class Probe
```

### 시나리오 C — 수정 전 오답 (메서드 레벨 변수 shadowing)

메서드가 선언한 변수는 클래스 변수와 별개인데, 이름 폴백이 그 경계를 무시하고 클래스 인자를 가져온다.

```
 class TopRepo<T> { <T> T convert(Object o) { return null; } }
 class TopStringRepo extends TopRepo<String> {}

 resolveVariable(convert 의 메서드 레벨 T, forClass(TopStringRepo))
   TopStringRepo 는 제네릭 없음 → superType = TopRepo<String> 으로 재귀       :226-228
     └→ ResolvableType.resolveVariable(메서드 T)                              :945
          resolved      = TopRepo.class
          variables     = TopRepo 의 [클래스 T]
          typeArguments = [String]
          1) 동일성 : getGenericDeclaration() 이 각각 Method / Class → 실패    :957-960
          2) ownerType : TopRepo 는 최상위 → null                              :962
          3) 이름 폴백 : 둘 다 이름이 "T" → return String                       :967-970
                ★ 자바 언어 규칙상 메서드 T 는 클래스 T 를 가리는 별개 변수인데
                  클래스 레벨 인자가 메서드 레벨 변수로 새어 들어갔다
 결과 String   (기대: 미해석 = TypeVariable 그대로)
```

### 시나리오 D — 폴백이 정당한 경우 (subtype narrowing)

이름 폴백을 삭제하면 안 되는 이유가 이 경로다. `ResolvableTypeTests.narrow()`가 고정하고 있다.

```
 ResolvableType type   = forField(Fields#stringList)      → List<String>
 ResolvableType narrow = ResolvableType.forType(ArrayList.class, type)        :1494
     forType(Type, owner) 은 owner.asVariableResolver() 를 붙인다              :1496-1499
       → narrow.type = ArrayList.class (raw Class)
         narrow.variableResolver = DefaultVariableResolver(source = List<String>)

 narrow.getGeneric().resolve()
   └→ getGenerics()                                                           :783
        this.type 은 Class 이므로 typeParams 경로                              :789-796
        generics[0] = forType(ArrayList 의 E, this)   ← owner 는 narrow 자신    :794
   └→ 그 generics[0].resolve() → resolveClass() → resolveType()               :901 → :920
        this.type 은 TypeVariable 이므로 variableResolver 에게 질의            :931-937
          → narrow.resolveVariable(ArrayList 의 E)                            :945
              narrow.type 은 Class 라 ParameterizedType 분기에 걸리지 않고
              5) 자기 variableResolver 로 위임                                 :979-980
                → List<String> 의 resolveVariable(ArrayList 의 E)
                    resolved      = List.class
                    variables     = List 의 [E]
                    typeArguments = [String]
                    1) 동일성 : ArrayList#E != List#E (선언이 다름) → 실패
                    2) ownerType : java.util.List 는 최상위 → null
                    3) 이름 폴백 : 둘 다 "E" → String   ★ 여기서 정답이 나온다
 결과 String
```

즉 3)은 실수로 들어간 코드가 아니라 **"하위 타입이 상위 타입의 인자를 이름으로 물려받는" 경우를 건지는 장치**였다. 문제는 그 장치에 조건이 없어 시나리오 B·C까지 함께 통과시켰다는 것뿐이다.

## 3. 분기 처리 워크플로우

이 무대의 분기는 두 층이다. 바깥층은 `GenericTypeResolver`가 후보를 고르는 순서이고, 안층은 `ResolvableType.resolveVariable`이 매칭 방식을 고르는 순서다. 브리핑에서 요구한 대로 안층 분기도를 먼저 완전히 펼친다.

### 3-1. `ResolvableType.resolveVariable` 분기도 (수정 전)

이 메서드는 다섯 갈래를 순서대로 시도하고, 결함은 그중 셋째에 있다.

```
 resolveVariable(TypeVariable<?> variable)                   ResolvableType.java:945
   │
   ├─ variableToCompare = SerializableTypeWrapper.unwrap(variable)          :946
   │     (직렬화용 프록시로 감싸인 변수를 원본으로 되돌린다 — equals 를 성립시키기 위해 필수)
   │
   ├─ [A] this.type instanceof TypeVariable ?                              :947
   │        └─ 예 ──→ return resolveType().resolveVariable(variableToCompare)  :948
   │                   (자기 자신이 변수면 한 단계 풀고 그 결과에 다시 묻는다)
   │
   ├─ [B] this.type instanceof ParameterizedType ?                         :950
   │        ├─ resolved = resolve()                                        :951
   │        │    └─ null 이면 ──→ return null                              :952-954
   │        ├─ variables     = resolved.getTypeParameters()                :955
   │        ├─ typeArguments = parameterizedType.getActualTypeArguments()  :956
   │        │
   │        ├─ [B1] 동일성 루프 : variables[i].equals(variableToCompare) ?  :957-960
   │        │        ├─ 일치 ──→ return forType(typeArguments[i], variableResolver)
   │        │        │            ★ 정상 경로. TypeVariable 의 equals 는
   │        │        │              이름 + getGenericDeclaration() 을 함께 본다
   │        │        └─ 불일치 ──→ 다음 단계
   │        │
   │        ├─ [B2] ownerType = parameterizedType.getOwnerType()           :962
   │        │        ├─ != null ──→ return forType(ownerType, resolver)
   │        │        │                       .resolveVariable(variableToCompare)   :964
   │        │        │              ★ return 이다 — 결과가 null 이어도 아래로 안 간다
   │        │        │                (중첩 선언이면 여기서 끝나 [B3] 미도달)
   │        │        └─ == null ──→ [B3] 으로
   │        │
   │        └─ [B3] 이름 폴백 루프 : variables[i].getName().equals(...getName()) ?  :967-970
   │                 ├─ 일치 ──→ return forType(typeArguments[i], variableResolver)
   │                 │            ★ 결함: 선언 문맥을 전혀 보지 않는다
   │                 │              · 형제 인터페이스 (TopSearch vs TopCreate)  → 오답
   │                 │              · 메서드 레벨 shadowing (Method vs Class) → 오답
   │                 │              · subtype narrowing (ArrayList vs List)   → 정답
   │                 └─ 불일치 ──→ 아래로 흘러감
   │
   ├─ [C] this.type instanceof WildcardType ?                              :973
   │        └─ resolveType().resolveVariable(...) 이 null 이 아니면 반환     :974-977
   │
   ├─ [D] this.variableResolver != null ?                                  :979
   │        └─ 예 ──→ return this.variableResolver.resolveVariable(variableToCompare)  :980
   │                   (자기가 모르면 owner 체인으로 넘긴다 — 시나리오 D 의 경로)
   │
   └─ [E] return null                                                      :982
             "여기서는 못 찾았다" = 상위 탐색이 다음 후보로 넘어가라는 신호
```

PR이 바꾸는 것은 [B3] 하나다. 루프를 없애는 대신 **게이트를 앞에 세운다**.

```
 [B3] 수정 후
   ├─ variableToCompare.getGenericDeclaration() instanceof Class<?> declaringClass ?
   │     ├─ 아니오 (Method / Constructor 선언) ──→ 폴백 건너뜀   ← 시나리오 C 차단
   │     └─ 예 ──→ 다음 조건
   ├─ resolved.isAssignableFrom(declaringClass) ?
   │     ├─ 아니오 ──→ 폴백 건너뜀                               ← 시나리오 B 차단
   │     │              TopSearch.isAssignableFrom(TopCreate) == false
   │     └─ 예 ──→ 이름 비교 루프 실행                           ← 시나리오 D 유지
   │                List.isAssignableFrom(ArrayList) == true
   └─ 건너뛴 경우 [C]→[D]→[E] 로 흘러 최종적으로 null 을 반환한다
        = 틀린 답 대신 "모름" 을 돌려주고 상위 탐색에 길을 비켜 준다
```

`getGenericDeclaration()`이 돌려줄 수 있는 값은 자바 명세상 `Class`·`Method`·`Constructor` 셋뿐이므로, 첫 조건은 "클래스나 인터페이스가 선언한 변수만"이라는 뜻이 된다. 둘째 조건의 방향에 주의해야 한다. `resolved`(지금 보고 있는 파라미터화 타입의 raw 클래스)가 **상위**, `declaringClass`(찾는 변수를 선언한 클래스)가 **하위**여야 한다. 이것이 "subtype narrowing"의 정확한 의미다.

### 3-2. 상위 탐색 분기 — 후보 순서가 답을 바꾼다

바깥층은 문맥 클래스 자신, 상위 클래스, 인터페이스 선언 순서로 후보를 시도하고 첫 성공을 답으로 삼는다.

```
 GenericTypeResolver.resolveVariable(typeVariable, contextType)   GenericTypeResolver.java:210
   │
   ├─ contextType.hasGenerics() ?                                          :212
   │     ├─ 예 ──→ variableResolver = contextType.asVariableResolver()      :213
   │     │          ├─ null 이면 return NONE                                :214-216
   │     │          ├─ resolveVariable 결과가 not null 이면                 :217-218
   │     │          │    while (결과의 type 이 아직 TypeVariable) resolveType() 으로 한 단계씩 풀기  :219-221
   │     │          │    return 결과                                        :222
   │     │          └─ null 이면 아래로
   │     └─ 아니오 ──→ 아래로 (raw Class 문맥)
   │
   ├─ superType = contextType.getSuperType()                                :226
   │     └─ NONE 이 아니면 재귀 → NONE 이 아니면 즉시 반환                   :227-232
   │
   ├─ for (ifc : contextType.getInterfaces())                               :233
   │     └─ 재귀 → NONE 이 아니면 즉시 반환                                  :234-237
   │          ★ 선언 순서가 곧 우선순위다. 시나리오 B 에서 TopSearch 가
   │            먼저 오답을 내놓는 바람에 TopCreate 는 시도되지 않았다
   │
   └─ return NONE                                                           :239

 resolveType(genericType, contextClass)                                     :154
   ├─ contextClass == null ──→ return genericType (원본 그대로)              :155, :207
   ├─ genericType 이 TypeVariable                                            :156
   │     ├─ resolveVariable 결과가 NONE 이면 forVariableBounds 로 폴백        :159-161
   │     │     resolveBounds: bounds[0] == Object.class 면 null → NONE       :1467-1472
   │     ├─ NONE 이 아니면
   │     │     ├─ 결과 type 이 ParameterizedType ──→ resolveType 재귀        :164-166
   │     │     └─ resolve() 가 not null ──→ 그 Class 반환                    :167-170
   │     └─ 끝까지 실패 ──→ return genericType (TypeVariable 그대로)  ★ 시나리오 C 의 기대값
   └─ genericType 이 ParameterizedType                                       :173
         hasUnresolvableGenerics() 일 때만 인자별로 같은 처리를 반복          :175-204
         → forClassWithGenerics(rawClass, generics).getType()                :202
```

시나리오 C가 수정 후 "미해석"으로 끝나는 경로가 여기서 확인된다. 어떤 후보도 답을 주지 못해 `NONE`이 되고, 메서드 `T`의 bound는 `Object`뿐이라 `resolveBounds`가 `null`을 돌려주므로(`ResolvableType.java:1468-1469`) bound 폴백도 `NONE`이며, 결국 `return genericType`(`GenericTypeResolver.java:207`)이 실행돼 `TypeVariable`이 그대로 나온다.

### 3-3. 두 가지 VariableResolver의 분기 차이

같은 인터페이스를 구현하지만 매칭 규칙이 다르다. 이 차이가 "어떤 경로가 이름 폴백에 노출되는가"를 결정한다.

```
 DefaultVariableResolver.resolveVariable(v)                :1599
   └─ source.resolveVariable(v)  → 위 3-1 의 5단계 전부를 그대로 탄다 (이름 폴백 포함)

 TypeVariablesVariableResolver.resolveVariable(v)          :1623
   ├─ variableToCompare = unwrap(v)                        :1624
   ├─ for i : variables[i].equals(variableToCompare) ?     :1625-1628
   │     └─ 일치 ──→ generics[i] 반환   ← 동일성 비교만 한다
   └─ return null                                          :1630
        ★ 이름 폴백이 없다. forClassWithGenerics 로 만든 타입은
          미리 짝지어 둔 표로만 답하고, 못 찾으면 정직하게 null 을 낸다
```

## 4. 스프링 전역에서의 자리

`ResolvableType`은 스프링 전역의 제네릭 처리 기반이지만, 이 PR이 건드리는 `resolveVariable`의 이름 폴백에 실제로 도달하는 경로는 `GenericTypeResolver.resolveType(Type, Class)`를 통과하는 계열이다. grep으로 확인한 그 진입점은 다음과 같고, 공통점은 전부 **메시지 본문을 어떤 타입으로 역/직렬화할지 정하는 자리**라는 것이다.

```
[ HTTP 메시지 컨버터 — 본문 역직렬화 타입 결정 ]
  AbstractJacksonHttpMessageConverter#getJavaType                  AbstractJacksonHttpMessageConverter.java:491
    → defaultMapper.constructType(GenericTypeResolver.resolveType(type, contextClass))
  AbstractJackson2HttpMessageConverter#getJavaType                 AbstractJackson2HttpMessageConverter.java:542
    → 같은 형태 (gh-36890 이슈가 보고된 경로)
  AbstractJsonHttpMessageConverter#readInternal                    AbstractJsonHttpMessageConverter.java:94
    → readResolved(GenericTypeResolver.resolveType(type, contextClass), inputMessage)

[ WebFlux 코덱 — 리액티브 본문 디코딩 타입 결정 ]
  JacksonCodecSupport#getJavaType                                  JacksonCodecSupport.java:220
  Jackson2CodecSupport#getJavaType                                 Jackson2CodecSupport.java:232

[ 메시징 ]
  AbstractMessageConverter#getResolvedType                         AbstractMessageConverter.java:314
    → GenericTypeResolver.resolveType(genericParameterType, contextClass)

[ HTTP 인터페이스 클라이언트 — 반환 타입 결정 ]
  HttpServiceMethod                                                HttpServiceMethod.java:438, :446, :550, :563, :589
    → ParameterizedTypeReference.forType(GenericTypeResolver.resolveType(type, serviceType))

[ Spring MVC — 응답 본문 직렬화 타입 결정 ]
  AbstractMessageConverterMethodProcessor                          AbstractMessageConverterMethodProcessor.java:221
    → GenericTypeResolver.resolveType(getGenericType(returnType), returnType.getContainingClass())
```

즉 `@RequestBody`/`@ResponseBody` 처리, WebFlux 본문 디코딩, `@HttpExchange` 인터페이스 클라이언트, 메시징 컨버터가 전부 이 한 함수의 판정에 의존한다. 시나리오 B 같은 오답은 "컨트롤러가 JSON 본문을 엉뚱한 타입으로 읽어 400을 낸다" 형태로 사용자에게 도달한다.

한편 이름 폴백에 **도달하지 않는** 경로도 명확히 해 두는 편이 낫다. `forClassWithGenerics`로 만든 타입은 `TypeVariablesVariableResolver`(동일성 비교 전용, `ResolvableType.java:1623`)를 쓰고, `forField`/`forMethodParameter` 계열은 `owner.asVariableResolver()`로 `DefaultVariableResolver`를 붙이므로(`ResolvableType.java:1239-1240`, `:1408-1410`) 3-1의 전체 사슬을 탄다. 빈 팩토리의 제네릭 매칭처럼 `ResolvableType`을 직접 쓰는 자리들은 대부분 동일성 비교 단계([B1])에서 답이 나오므로 이 결함과 무관하다.

## 5. 관련 개념

### 5-1. TypeVariable의 동일성 — 이름만으로는 부족하다

자바 리플렉션에서 `TypeVariable`의 `equals`는 **이름과 `getGenericDeclaration()`을 함께** 본다. 그래서 다음 셋은 이름이 모두 같아도 서로 다른 객체다.

```
  List<E>       의 E   → getGenericDeclaration() = interface java.util.List
  ArrayList<E>  의 E   → getGenericDeclaration() = class java.util.ArrayList
  TopRepo<T>    의 T   → getGenericDeclaration() = class TopRepo
  <T> T convert 의 T   → getGenericDeclaration() = public TopRepo.convert(Object)
```

`getGenericDeclaration()`이 돌려주는 것은 `GenericDeclaration` 인터페이스이고, 그 구현은 `Class`·`Method`·`Constructor` 셋뿐이다. PR의 첫 조건 `instanceof Class<?>`가 "클래스/인터페이스 선언 변수만"을 정확히 표현하는 이유이며, 메서드 레벨 shadowing이 그 검사에 걸리는 이유다.

`resolveVariable`이 맨 처음 `SerializableTypeWrapper.unwrap`을 호출하는 것도(`ResolvableType.java:946`) 이 동일성 때문이다. 스프링은 `Type`을 직렬화 가능하게 만들려고 프록시로 감싸는데, 감싼 채로 `equals`를 하면 원본과 맞지 않으므로 비교 전에 벗겨 낸다.

### 5-2. owner type — 중첩 선언이 만드는 추가 문맥

`ParameterizedType.getOwnerType()`은 그 타입이 **다른 타입 안에 중첩 선언**돼 있을 때 바깥 타입을 돌려주고, 최상위 선언이면 `null`이다.

```
  interface TopSearch<I,O> {}                     → getOwnerType() = null
  class Tests { interface Search<I,O> {} }        → getOwnerType() = class Tests
```

중첩 클래스는 바깥 클래스의 타입 변수를 쓸 수 있으므로, 변수를 못 찾았을 때 바깥으로 한 단계 올라가 다시 묻는 것이 타당하다. 그것이 `resolveVariable`의 [B2] 분기다(`ResolvableType.java:962-965`). 다만 이 분기가 `return`이라 **owner가 있기만 하면 뒤의 이름 폴백은 실행되지 않는다**. 같은 구조가 중첩이냐 최상위냐에 따라 다른 답을 내는 비대칭이 여기서 생기고, gh-36890의 회귀 테스트가 중첩 픽스처로 쓰인 탓에 대상 경로를 밟지 못한 것도 이 때문이다.

참고로 `SyntheticParameterizedType.getOwnerType()`은 언제나 `null`이므로(`ResolvableType.java:1665-1667`), `forClassWithGenerics`로 만든 타입은 항상 [B3]까지 흘러간다. PR의 긍정 테스트가 `forClassWithGenerics(Container.class, String.class)`로 픽스처를 만드는 것은 그 경로를 확실히 밟기 위해서다.

### 5-3. NONE과 null — 두 가지 "없음"

이 무대에는 "값 없음"을 표현하는 두 관용구가 공존한다.

```
  ResolvableType.NONE   :95   공개 API 수준의 "없음". 메서드 체이닝이 NPE 없이 이어지도록 하는 싱글턴
                              GenericTypeResolver 의 탐색 루프는 NONE 여부로 다음 후보를 판단  :229, :235
  null                        내부 resolveVariable 의 "여기서는 못 찾았다" 신호               :982
                              DefaultVariableResolver 를 지나 GenericTypeResolver 에서 NONE 으로 번역  :217-218
```

PR의 수정이 "틀린 답 대신 모름을 반환한다"는 말은 정확히 [B3]을 건너뛰어 `null`(-> `NONE`)로 흘려보낸다는 뜻이고, 그 결과 상위 루프가 다음 인터페이스 후보를 시도하게 된다. 오답을 조기 반환하는 대신 탐색을 계속하게 만드는 것이 수정의 작동 원리다.

### 5-4. bound 폴백 — 해석 실패 시의 마지막 그물

변수를 끝내 해석하지 못하면 `GenericTypeResolver`는 그 변수의 상한(bound)을 답으로 쓰려 시도한다(`GenericTypeResolver.java:160`, `:184`). `forVariableBounds`는 `resolveBounds`에 위임하는데, 이 함수는 `bounds[0]`이 `Object.class`면 `null`을 돌려준다(`ResolvableType.java:1467-1472`).

```
  <T extends Number> 의 T  → bounds[0] = Number  → forVariableBounds = Number
  <T> 의 T                 → bounds[0] = Object  → null → NONE → 원본 TypeVariable 그대로
```

`Object`를 답으로 주지 않는 이유는 그것이 정보가 아니기 때문이다. "아무거나"라고 답하느니 "모른다"고 답하는 편이 호출자에게 더 유용하다. 시나리오 C의 기대값이 `Object.class`가 아니라 `TypeVariable`인 근거가 여기 있다.

### 5-5. 컴파일 타임과 런타임의 제네릭 정보

타입 변수 해석이 필요한 이유 자체는 "제네릭 정보가 어디까지 살아남는가"의 문제다. 이 주제는 이미 개념 문서가 있으므로 링크로 대신한다: [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md). 요지만 적으면, 필드·메서드 시그니처에 쓰인 제네릭은 클래스 파일의 시그니처 속성으로 남아 리플렉션이 `ParameterizedType`·`TypeVariable`로 되돌려 주지만, 인스턴스에 담긴 값의 제네릭 인자는 남지 않는다. `ResolvableType`이 다루는 것은 전자이며, `resolveVariable`은 그 남아 있는 정보끼리 짝을 맞추는 작업이다.
