# PR #37186 분석 — forClassWithGenerics 직렬화 프록시의 메서드 그래프와 이름표

> 기준 커밋: 수정 상태 = `3bb5ed1ae4f`(PR head, 로컬 브랜치 `fix/typedescriptor-derived-serialization`), 결함 상태 = `89047909ea4`(PR 베이스).\
> 아래 file:line 은 별도 표기가 없으면 **수정 상태(head)** 좌표다 — 이 PR은 순수 추가(137줄 추가, 0줄 삭제)라 기존 코드의 줄번호는 프록시 블록 앞까지 두 상태가 같다.
>
> 이 문서의 역할: [README.md](README.md)가 서사와 범위 판단을, [structure.md](structure.md)가 무대의 지도와 분기도를, [tests.md](tests.md)가 테스트를, [review.md](review.md)가 리뷰 과정을 맡는다.\
> 여기서는 **생성부터 폭발까지의 호출 그래프**, **이름표 하나하나의 정체**, **정상/결함 케이스의 단계별 값**만 다룬다.\
> 프록시 관용구 자체와 버전 스큐 일반론은 [개념 문서](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md)와 [instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md)가 정본이다.

## 0. 결론

**결함**: `ResolvableType.forClassWithGenerics()`가 만든 객체 그래프에는 JDK의 raw `TypeVariable`(비직렬화)이 두 자리에 실린다 — `TypeVariablesVariableResolver.variables`(:1615)와, 인자가 null이거나 미해석 변수일 때 재주입되는 `SyntheticParameterizedType.typeArguments`(:1693).\
그래서 `ResolvableType`이 `Serializable`을 선언하고 `VariableResolver`도 `extends Serializable`(:1575)인데도 스트림에 실을 수 없다.

**수정**: 두 내부 클래스에 `writeReplace()`/`readResolve()` 직렬화 프록시를 붙여, raw `TypeVariable` 대신 "선언 클래스 + 타입 파라미터 인덱스"라는 좌표를 싣고 역직렬화 때 `getTypeParameters()` 재조회로 그 JVM의 정본 인스턴스를 되찾는다(:1640-1653, :1662-1686, :1745-1781, :1791-1832).

**상태**: OPEN, `status: waiting-for-triage`, 2026-08-21 제출, 리뷰어 미배정(2026-08-27 확인).

> **객체 그래프(object graph)** — 어떤 객체와 그 객체가 필드로 참조하는 모든 객체를 이어 붙인 덩어리.\
> 예: 직렬화는 이 그래프 전체를 훑으므로, 저 안쪽에 비직렬화 객체가 하나만 있어도 전체가 실패한다.

> **정본(canonical) 인스턴스** — 같은 것을 나타내는 여러 사본 중 "이것이 진짜"로 정해진 하나.\
> 예: `List.class.getTypeParameters()[0]`이 돌려주는 `E`가 그 JVM에서의 정본이다.

## 1. 무대 — 어디의 무엇인가

결함이 사는 파일, 그 파일에 닿는 공개 API, 그리고 결함이 실제로 아픈 시점을 차례로 짚는다.

- 모듈·파일: `spring-core` / `spring-core/src/main/java/org/springframework/core/ResolvableType.java` 한 파일.\
  신설 클래스 둘은 모두 `private static final` 중첩 클래스라 공개 표면이 늘지 않는다.
- 공개 진입 API: `ResolvableType.forClassWithGenerics(Class, ResolvableType...)`:1180 및 그 오버로드.\
  그 위에 얹힌 공개 팩토리가 `TypeDescriptor.collection(Class, TypeDescriptor)`(TypeDescriptor.java:595)과 `TypeDescriptor.map(...)`(:618)이다.
- 누가 부르나: main 소스 31곳(core 4 / beans 1 / context 1 / test 3 / web 7 / webflux 3 / webmvc 1).\
  대표는 변환 서비스의 `collection`/`map`, 코덱의 `MultiValueMap<String,String>` 상수, `PayloadApplicationEvent.getResolvableType()`.\
  호출처 전체 지도는 [structure.md](structure.md) 4절.
- 언제 직렬화되나: 결함이 아픈 곳은 생성처가 아니라 **보유처**다 — `TypeDescriptor`, `NoSuchBeanDefinitionException`, `PayloadApplicationEvent`, `UnsupportedMediaTypeStatusException`, `RootBeanDefinition`이 `ResolvableType`을 비-transient 필드로 들고 세션 복제·분산 캐시·원격 예외 경계를 넘는 순간이다.
- 왜 이 갈래만 취약한가: `forField`/`forMethodParameter`는 `forType`:1538-1540에서 `SerializableTypeWrapper.forTypeProvider`(SerializableTypeWrapper.java:103)를 타서 JDK Type이 직렬화 가능한 동적 프록시로 감싸진다.\
  `forClassWithGenerics`는 자기가 만든 `SyntheticParameterizedType`을 그대로 넘기므로 그 보호막을 타지 않는다.

> **공개 표면(public surface)** — 라이브러리 밖에서 볼 수 있어 바꾸면 호환성이 깨지는 API의 집합.\
> 예: `private static final` 중첩 클래스를 둘 추가해도 사용자가 볼 수 있는 목록은 그대로다.

## 2. 전체 메서드 그래프 — 생성부터 폭발까지

공개 팩토리 진입에서 직렬화가 터지는 자리까지, 그리고 수정 후 같은 그래프에 게이트 둘이 어디에 끼어드는지를 한 그림에 펼친다.

```text
[공개 진입]
 TypeDescriptor.map(Map.class, keyTd, valueTd)               TypeDescriptor.java:618
   `-- ResolvableType.forClassWithGenerics(mapType, key, value)   TypeDescriptor.java:627
          |
          v
 ResolvableType.forClassWithGenerics(clazz, generics)        ResolvableType.java:1180
   |-- Assert.notNull(clazz)                                        :1181
   |-- variables = clazz.getTypeParameters()                        :1182
   |      -> JDK 가 클래스당 한 번 만들어 캐시하는 TypeVariableImpl[]  (비직렬화)
   |-- Assert.isTrue(variables.length == generics.length)           :1184  (generics != null 일 때만)
   |-- for i in 0..variables.length                                 :1188
   |      generic  = generics != null ? generics[i] : null          :1189
   |      argument = generic != null ? generic.getType() : null     :1190
   |            (generic.getType() 은 SerializableTypeWrapper.unwrap 을 거친다   :203)
   |      arguments[i] = (argument != null && !(argument instanceof TypeVariable))
   |                       ? argument          <- String.class 같은 정상 인자
   |                       : variables[i]      <- [폭탄 B] raw TypeVariable 재주입   :1191
   `-- forType(new SyntheticParameterizedType(clazz, arguments),                    :1193
               generics != null ? new TypeVariablesVariableResolver(variables, generics) : null)
                                                     ^
                                                     `-- [폭탄 A] variables 를 그대로 보관   :1615
          |
          v
 ResolvableType.forType(type, typeProvider, variableResolver)      :1535
   |-- type instanceof Class ? 즉시 래핑 후 반환                       :1547-1549   (여기선 아님)
   |-- resultType = new ResolvableType(type, provider, resolver)     :1552  -> hash = calculateHashCode()  :149
   |-- cache 조회/등록                                                :1553-1557
   `-- return resultType   (type=SyntheticParameterizedType, variableResolver=TypeVariablesVariableResolver)

[결함 지점 — 직렬화]
 oos.writeObject(resolvableType)
   |-- ResolvableType implements Serializable       :91                 -> 통과
   |-- 필드 type: SyntheticParameterizedType 도 Serializable  :1689      -> 통과, 내부 진입
   |     |-- rawType = Map.class                                        -> Class 는 직렬화 가능
   |     `-- typeArguments[i] 가 TypeVariableImpl 이면 [폭탄 B]  ------> NotSerializableException
   |-- 필드 variableResolver: VariableResolver extends Serializable :1575 -> 통과, 내부 진입
   |     |-- generics[i] = ResolvableType                               -> 통과(재귀)
   |     `-- variables[i] = TypeVariableImpl [폭탄 A]  ---------------> NotSerializableException
   `-- hash / resolved / componentType / typeProvider                   -> 통과

[수정 후 — 같은 그래프에 게이트 둘]
 writeObject
   |-- SyntheticParameterizedType.writeReplace()                        :1745
   |     -> 조건 통과 시 SerializedSyntheticParameterizedType(rawClass, encodedArguments)
   `-- TypeVariablesVariableResolver.writeReplace()                     :1640
         -> 조건 통과 시 SerializedTypeVariablesVariableResolver(declaringClass, generics)
 readObject
   |-- SerializedSyntheticParameterizedType.readResolve()               :1802
   |     -> 검증 3단 후 variables = rawType.getTypeParameters() 재조회 -> SyntheticParameterizedType 재구성
   |-- SerializedTypeVariablesVariableResolver.readResolve()            :1673
   |     -> 검증 2단 후 variables = declaringClass.getTypeParameters() 재조회 -> 리졸버 재구성
   `-- ResolvableType.readResolve()                                     :1064   (EmptyType -> NONE 싱글턴)
```

데이터 흐름의 요점: **스트림을 건너는 것은 객체가 아니라 좌표**다.\
보내는 쪽은 `TypeVariable`을 인덱스(또는 선언 클래스)로 바꾸고, 받는 쪽은 그 좌표로 `getTypeParameters()`를 다시 불러 자기 JVM의 정본을 얻는다.\
정본이 하나뿐이라는 JDK 성질 덕분에 복원본이 원본과 `==`이 되고, 그래야 `resolveVariable`:1625의 선형 비교와 `SyntheticParameterizedType.equals`:1729·`hashCode`:1736이 원본과 같은 답을 낸다.

> **좌표(coordinate) 인코딩** — 객체 자체를 싣는 대신 "어디에 있는 몇 번째 것"이라는 위치 정보만 싣는 방식.\
> 예: `E`라는 객체 대신 "List.class의 0번 타입 파라미터"를 싣고, 받는 쪽이 그 자리에서 다시 찾아온다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 것은 "타입 변수"가 네 가지 모습으로 돌아다닌다는 점이다.\
JDK 정본 `TypeVariableImpl`, `SerializableTypeWrapper`가 감싼 프록시, 인덱스로 인코딩된 `Integer`, 그리고 재조회로 되찾은 정본.\
아래 표는 각 이름표가 그중 무엇을 들고 있는지를 명시한다.

| 이름표 | 무엇인가 / 입력·출력 | 누가 언제 만지나 | 이 결함과의 관계 |
|---|---|---|---|
| `forClassWithGenerics(clazz, generics)` :1180 | 공개 팩토리. 입력 = raw 클래스 + 제네릭 인자(가변인자, 배열 자체와 원소 모두 nullable), 출력 = `ResolvableType` | `TypeDescriptor.collection`/`map`, 코덱 상수, 이벤트 페이로드 등 31곳 | 결함의 생성처. 인자 모양에 따라 폭탄 A/B가 각각 켜진다 |
| 지역변수 `variables` :1182 | `clazz.getTypeParameters()` 결과. JDK가 클래스당 한 번 만들어 캐시하는 정본 배열 | 이 팩토리 안에서만 | 두 폭탄의 공통 출처. 배열은 매번 복제되지만 **원소는 동일 인스턴스** |
| 지역변수 `argument` :1190 | `generic.getType()` — 인자로 받은 `ResolvableType`의 내부 Type. `null`일 수 있다 | 루프 안 | 이 값이 null이거나 `TypeVariable`이면 대신 `variables[i]`가 들어간다(:1191) = 폭탄 B의 발동 조건 |
| 지역변수 `arguments` :1187 | `SyntheticParameterizedType`에 넘길 `Type[]` | 루프가 채움 | 정상 인자와 raw 변수가 **섞일 수 있는** 배열. 그래서 인코딩이 원소별 분기다 |
| `ResolvableType.type` :108 | 관리 대상 JDK `Type`. 여기서는 `SyntheticParameterizedType` | 생성자 4종, `getType()`:202 | 무대 1. 이 자리에 무엇이 앉느냐가 팩토리마다 다르다 |
| `ResolvableType.variableResolver` :123 | 타입 변수 해석 전략(`@Nullable`) | 생성자, `resolveVariable`, `calculateHashCode`:1046 | 무대 2. `generics == null`이면 아예 만들어지지 않는다 |
| `ResolvableType.hash` :125 | 생성 시 미리 계산된 해시(`@Nullable Integer`). 비-transient | `forType`:1552/:1555, `hashCode()`:1034이 그대로 반환 | 프록시가 바꾸지 않는 값. 다른 JVM에서 `Class.hashCode()` 기반 값이 갈릴 수 있다는 성질은 `forField` 경로에도 있는 **기존** 성질이다 |
| `VariableResolver` (인터페이스) :1575 | `extends Serializable`. `getSource()`:1580 + `resolveVariable(TypeVariable)`:1587 | 두 구현이 상속 | 계약을 **선언**만 해 두고 구현 하나가 그것을 어기고 있었다 — #37109의 `AnnotatedElementSupplier`와 같은 형태의 함정 |
| `DefaultVariableResolver.source` :1594 | `ResolvableType` 자체 | `asVariableResolver()`:1054 | `ResolvableType`은 직렬화 가능하므로 이 구현은 애초에 문제없음 (대조군) |
| `TypeVariablesVariableResolver.variables` :1615 | raw `TypeVariable[]` | 생성자 :1619, `resolveVariable` :1627, `writeReplace` :1641-1652 | **폭탄 A**. 이 필드 하나 때문에 리졸버 전체가 비직렬화였다 |
| `TypeVariablesVariableResolver.generics` :1617 | 대응하는 `ResolvableType[]`(원소 nullable) | 위와 동일 + `getSource()`:1636 | 직렬화 가능. 프록시가 **그대로 실어 보내는** 절반 |
| `resolveVariable(TypeVariable)` :1625 | 변수 -> `ResolvableType` 해석. `SerializableTypeWrapper.unwrap`(:90)으로 프록시를 벗긴 뒤 선형 탐색 | 제네릭 해석 전 경로 | 복원본이 정본과 `==`이 아니면 여기서 **조용히 null**이 나온다. 재조회 설계가 방어하는 실패 |
| `TypeVariablesVariableResolver.writeReplace()` :1640 | 프록시 자격 심사 후 교체 또는 `this`. 출력 `Object` | JDK 직렬화 런타임만 호출 | 수정 (1). `this` 반환 = "수정 전과 동일하게 행동" (성공을 뜻하지 않는다) |
| `Arrays.equals(this.variables, declaringClass.getTypeParameters())` :1648 | 이 리졸버가 **한 클래스의 타입 파라미터 전체**를 들고 있는지 확인 | `writeReplace` 안 | 좌우 순서가 의도적이다 — JDK `TypeVariable` 구현의 `equals`는 자기 클래스만 받으므로 수신자가 `this.variables`여야 래핑된 변수와 언패킹된 상대가 매칭된다(:1644-1646 주석). 뒤집으면 정상 케이스가 조용히 폴백으로 샌다 |
| `SerializedTypeVariablesVariableResolver.declaringClass` :1664 | 좌표의 절반 — 선언 클래스(이름으로 직렬화됨) | 생성자 :1668, `readResolve` :1676-1684 | 재조회의 열쇠 |
| `SerializedTypeVariablesVariableResolver.readResolve()` :1673 | null 검사 -> arity 검사 -> `getTypeParameters()` 재조회 -> 리졸버 재구성 | 직렬화 런타임 | 기본 직렬화는 생성자를 우회하므로 `final` 필드도 null로 도착할 수 있다 — 그래서 null 검사가 형식적 방어가 아니다 |
| `SyntheticParameterizedType.rawType` :1691 | 선언형 `Type`(실제로는 대개 `Class`) | 생성자 :1695, `getRawType()`:1719, `writeReplace` :1746 | `Class`가 아니면 좌표를 만들 수 없어 폴백 |
| `SyntheticParameterizedType.typeArguments` :1693 | 실제 타입 인자 배열. **raw `TypeVariable`이 섞일 수 있다** | `getActualTypeArguments()`:1724, `equals`:1732, `writeReplace` :1752 | **폭탄 B**. 클래스 자신은 `Serializable`을 선언하고 있어 더 헷갈린다 |
| `SyntheticParameterizedType.writeReplace()` :1745 | 원소별 인코딩 후 프록시 또는 `this` | 직렬화 런타임 | 수정 (2) |
| 지역변수 `encodedArguments` :1750 | `Object[]` — 원소는 `Integer`(변수 인덱스) 또는 원본 `Type`(Serializable인 것) | `writeReplace` -> 프록시 생성자 | 두 종류가 섞인 배열이라 `readResolve`가 원소별로 다시 분기한다 |
| 지역변수 `encodedVariable` :1751 | "마커를 하나라도 썼는가" 불리언 | :1758에서 true, :1769에서 판정 | **무악화의 핵심**. false면 `this`를 반환해 원래 직렬화되던 인스턴스의 스트림 형식을 그대로 둔다 |
| `indexOf(TypeVariable[], Type)` :1774 | **identity(`==`) 선형 탐색**. 출력 = 인덱스 또는 -1 | `writeReplace` :1754 | equals가 아니라 identity인 것이 의도. JDK가 정본을 캐시한다는 성질에 기대고, 빗나가면 폴백 |
| 인코딩 분기 순서 :1755 vs :1760 | 마커(identity) 검사가 `instanceof Serializable`보다 **먼저** | `writeReplace` 루프 | 순서가 정확성을 결정한다. `TypeVariable` 구현이 `Serializable`이기도 한 런타임에서 순서가 반대면 복사본이 실려 복원 시 정본성이 깨지고 `resolveVariable`이 조용히 실패한다 |
| `SerializedSyntheticParameterizedType.encodedArguments` :1795 | 위 배열을 그대로 보관 | `readResolve` :1805-1830 | null·arity·원소 인코딩 3단 검증의 대상 |
| `SerializedSyntheticParameterizedType.readResolve()` :1802 | 검증 후 `variables[index]`로 인자를 복원해 원본 클래스 재구성 | 직렬화 런타임 | 리졸버 쪽보다 자유도가 하나 많아(인덱스) 범위 검사 :1816가 추가된다 |
| `InvalidObjectException` (:1677, :1681, :1806, :1810, :1817, :1826) | "역직렬화 입력이 잘못됐다"의 표준 신호 | 위 두 `readResolve` | 검증이 없으면 같은 오류가 한참 뒤 `resolveVariable`의 조용한 null이나 AIOOBE로 나타난다. 실패를 역직렬화 지점으로 앞당기는 장치 |
| `ResolvableType.readResolve()` :1064 | `type == EmptyType.INSTANCE`면 `NONE` 싱글턴 반환 | 직렬화 런타임 | 이 PR이 만든 것이 아닌 기존 훅. 같은 파일에 이미 프록시성 관용구가 있었다는 선례 |

## 3. 결함 경로 단계 추적

폭탄 A와 B는 **서로 다른 입력에서 켜진다**.\
그래서 정상/결함을 한 줄로 대비하기보다 세 변형을 나란히 놓는 편이 정확하다.\
아래 세 입력은 모두 `forClassWithGenerics`를 통과하지만 결과가 다르다.

```java
// V1: 인자가 모두 구체 타입      -> 폭탄 A만
ResolvableType.forClassWithGenerics(Map.class, ResolvableType.forClass(String.class),
                                               ResolvableType.forClass(Integer.class));
// V2: generics 배열 자체가 null  -> 폭탄 B만  (List<?>)
ResolvableType.forClassWithGenerics(List.class, (ResolvableType[]) null);
// V3: 배열은 있고 원소가 null    -> 폭탄 A와 B 동시
ResolvableType.forClassWithGenerics(Map.class, (ResolvableType) null, null);
```

세 입력을 생성부터 역직렬화 관측까지 같은 단계표에 통과시키면 두 폭탄이 언제 켜지고
언제 프록시가 발동하지 않는지가 드러난다.

| 단계 | V1 (Map<String,Integer>) | V2 (List<?>) | V3 (Map, 원소 null) |
|---|---|---|---|
| S1 `variables` :1182 | `{K, V}` 정본 | `{E}` 정본 | `{K, V}` 정본 |
| S2 `arguments` :1187-1192 | `{String.class, Integer.class}` | `{E}` <- 재주입 | `{K, V}` <- 둘 다 재주입 |
| S3 `variableResolver` :1194 | `TypeVariablesVariableResolver({K,V}, {RT(String),RT(Integer)})` | **null** (generics == null) | `TypeVariablesVariableResolver({K,V}, {null,null})` |
| S4 결함 상태 직렬화 | `type` 통과 -> `variableResolver.variables`에서 폭발 (폭탄 A) | `type.typeArguments[0]`에서 폭발 (폭탄 B) | `type.typeArguments[0]`에서 먼저 폭발 (깊이 우선) |
| S5 수정 상태 `SyntheticParameterizedType.writeReplace` :1745 | 인자 둘 다 `indexOf` 미스, 둘 다 `Serializable` -> `encodedVariable=false` -> **`this` 반환**(스트림 형식 불변) | `indexOf({E}, E) = 0` -> `encodedArguments={0}`, `encodedVariable=true` -> 프록시 | `encodedArguments={0,1}` -> 프록시 |
| S6 수정 상태 `TypeVariablesVariableResolver.writeReplace` :1640 | `variables.length != 0`, `K.getGenericDeclaration()`이 `Map.class`, `Arrays.equals` 성립 -> 프록시(`Map.class`, `{RT(String),RT(Integer)}`) | 리졸버가 null이라 해당 없음 | 프록시(`Map.class`, `{null,null}`) |
| S7 스트림 내용 | `TypeVariable` 0개. `Map.class` + 두 `ResolvableType` | `List.class` + `Integer 0` | `Map.class` + `{0,1}` + `Map.class` + `{null,null}` |
| S8 역직렬화 재조회 | `Map.class.getTypeParameters()` -> `{K,V}` 정본, 리졸버 재구성 | `List.class.getTypeParameters()[0]` -> `E` 정본 | 양쪽 모두 재조회 |
| S9 관측 | 왕복 성공, `hashCode` 동일, `resolveVariable(K)`가 `RT(String)` 반환 | 왕복 성공, `getType()`의 인자가 원본과 `==` | 왕복 성공 |

같은 인스턴스가 결함 상태와 수정 상태에서 어떤 최종 상태로 끝나는지를 두 대표 입력으로 나란히 보면 이렇다.

```text
  V1 (Map<String,Integer>) — 인자가 모두 구체 타입
  결함 상태                                수정 상태
  +------------------------------+        +-------------------------------+
  | type        : 통과           |        | type        : this 폴백       |
  | resolver    : variables 폭발 |        | resolver    : 프록시로 교체   |
  | 스트림      : 없음(실패)      |        | 스트림      : Map.class  +    |
  |                              |        |               RT 두 개        |
  | 결과        : 예외           |        | 결과        : 왕복 성공       |
  +------------------------------+        +-------------------------------+

  V2 (List<?>) — generics 배열 자체가 null
  결함 상태                                수정 상태
  +------------------------------+        +-------------------------------+
  | type        : typeArgs 폭발  |        | type        : 프록시로 교체   |
  | resolver    : 없음(null)     |        | resolver    : 없음(null)      |
  | 스트림      : 없음(실패)      |        | 스트림      : List.class +   |
  |                              |        |               Integer 0       |
  | 결과        : 예외           |        | 결과        : 왕복 성공       |
  +------------------------------+        +-------------------------------+

  두 경우 모두 스트림에 TypeVariable 은 한 개도 실리지 않는다.
```

V1에서 `type` 쪽이 `this` 폴백인데도 전체가 성공하는 것은, 그 자리에 애초에 폭탄이 없었기 때문이다.

핵심은 S5의 V1 칸이다.\
**마커가 하나도 필요 없는 인스턴스는 프록시로 바뀌지 않는다.**\
이것이 없으면 원래 잘 직렬화되던 스트림의 형식까지 바뀌어, 롤링 업그레이드 중 구버전이 신버전 스트림을 못 읽는 순수 회귀가 생긴다.\
즉 `encodedVariable` 판정(:1769)은 최적화가 아니라 호환성 장치다.

폴백이 도는 경우도 같은 표로 읽을 수 있다.\
`writeReplace`의 어느 조건이든 탈락하면 `this`가 반환되고, 그 순간의 동작은 **결함 상태와 완전히 동일**하다 — 성공하던 것은 성공하고, 터지던 것은 그대로 터진다.\
대표적으로 리졸버 쪽 :1647에서 `getGenericDeclaration()`이 `Class`가 아닌 경우(메서드·생성자가 선언한 타입 변수)와, 타입 쪽 :1763에서 인자가 마커도 `Serializable`도 아닌 경우다.\
이 셋 중 어느 것도 새로운 실패를 만들지 않는다는 점이 "무악화" 주장의 내용이다.

## 4. 계약 — 무엇이 고정돼 있고 결함이 무엇을 어기나

이 무대가 고정한 약속을 하나씩 세우고 결함이 그중 무엇을 어기는지 대조한다.\
어긴 것은 위의 둘이고, SPR-17070이 축소해 둔 계약은 어긴 것이 아니라 범위 밖이다.

> **계약 축소(contract narrowing)** — 원래 약속했던 보장을 문서로 줄여서 "이건 이제 보장하지 않는다"로 바꾸는 것.\
> 예: javadoc에 "may not be Serializable"을 붙이면 그 갈래의 직렬화 실패는 더 이상 버그가 아니다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| `ResolvableType`은 `Serializable`이다 | 클래스 선언 :91 | 어긴다 — `forClassWithGenerics` 산출물이 실리지 않는다 |
| `VariableResolver` 구현은 직렬화 가능해야 한다 | 인터페이스 선언 :1575 (`extends Serializable`) | 어긴다 — `TypeVariablesVariableResolver`가 비직렬화 필드를 보유 |
| `getSuperType()`/`getInterfaces()` 결과는 직렬화되지 않을 수 있다 | javadoc :507, :537 ("may not be Serializable") — SPR-17070이 명시적으로 축소한 계약 | **어기지 않는다.** 그래서 이 갈래는 버그가 아니라 "계약을 되넓히자는 제안"이고, 이 PR의 범위 밖으로 분리됐다 |
| `resolveType()` 결과는 직렬화될 수 없다 | javadoc :917-921 | 범위 밖 (동일 근거) |
| 같은 JVM에서 `getTypeParameters()`는 매번 같은 인스턴스를 준다 | JDK 구현 성질(명세 강제 아님) — [instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md) | 수정이 **의존하는** 성질. 그래서 `indexOf`:1774 미스 시 폴백을 둔다 |
| `hashCode()`는 생성 시 계산된 값을 그대로 반환한다 | :1034, `hash` 필드 :125 | 프록시가 바꾸지 않는다. 재조회로 정본이 복원되므로 `SyntheticParameterizedType.hashCode`:1736도 원본과 일치 |
| 역직렬화 입력은 신뢰하지 않는다 | 이 PR이 도입한 규범(:1674-1675, :1803-1804 주석) | 신설 계약. 위반 시 `InvalidObjectException` |
| 런타임(직렬화하지 않는 경로) 동작은 불변이어야 한다 | 무악화 원칙 | 훅은 직렬화 시점에만 호출되므로 바이트 하나 안 바뀐다. 가드 테스트 `forClassWithGenericsUsesJdkTypesDirectly`가 고정 |
| 버전 간 스트림 호환은 Spring의 계약이 아니다 | gh-36346 논의 | 위반 아님 — 다만 "보증하지 않음"과 "미정의 동작을 해도 됨"은 다르다는 것이 검증 3단의 근거 |

## 5. 수정안 — before / after

이 PR은 순수 추가다.\
기존 코드는 한 줄도 지워지거나 바뀌지 않았고, 두 클래스에 훅이 붙고 프록시 클래스 둘이 생겼다.

> **훅(hook)** — 프레임워크가 정해진 이름·시그니처를 보고 알아서 불러 주는 메서드.\
> 예: `writeReplace()`는 직접 부르는 사람이 없고, 자바 직렬화 런타임이 객체를 쓰기 직전에 찾아 부른다.

### 5.1 리졸버 쪽

리졸버에는 자격 심사를 거쳐 좌표로 교체하거나 원래 자신을 돌려주는 훅 하나가 붙었다.

```java
// before: TypeVariablesVariableResolver 는 getSource() 로 끝난다 (89047909ea4)
		@Override
		public Object getSource() {
			return this.generics;
		}
	}

// after: ResolvableType.java:1640-1653 (3bb5ed1ae4f)
		private Object writeReplace() throws ObjectStreamException {
			if (this.variables.length == 0) {
				return this;
			}
			// Arrays.equals invokes equals on this.variables elements: JDK TypeVariable
			// implementations only accept their own class, so the receiver side must be
			// this.variables for wrapped variables to match their unwrapped counterparts.
			if (!(this.variables[0].getGenericDeclaration() instanceof Class<?> declaringClass) ||
					!Arrays.equals(this.variables, declaringClass.getTypeParameters())) {
				// Not the type parameters of a single declaring class -> retain default serialization.
				return this;
			}
			return new SerializedTypeVariablesVariableResolver(declaringClass, this.generics);
		}
```

### 5.2 타입 쪽 (인코딩 루프)

타입 쪽은 인자마다 마커·직렬화 가능·인코딩 불가 셋으로 갈리므로 훅 안에 루프가 들어간다.

```java
// after: ResolvableType.java:1745-1770 (3bb5ed1ae4f)
		private Object writeReplace() throws ObjectStreamException {
			if (!(this.rawType instanceof Class<?> rawClass)) {
				return this;
			}
			TypeVariable<?>[] variables = rawClass.getTypeParameters();
			Object[] encodedArguments = new Object[this.typeArguments.length];
			boolean encodedVariable = false;
			for (int i = 0; i < this.typeArguments.length; i++) {
				Type argument = this.typeArguments[i];
				int variableIndex = indexOf(variables, argument);
				if (variableIndex != -1) {
					// Re-derivable from the raw class -> encode as a type parameter index.
					encodedArguments[i] = variableIndex;
					encodedVariable = true;
				}
				else if (argument instanceof Serializable) {
					encodedArguments[i] = argument;
				}
				else {
					// Not encodable -> retain default serialization (and its failure mode).
					return this;
				}
			}
			// Only use the proxy for instances that would otherwise fail to serialize.
			return (encodedVariable ? new SerializedSyntheticParameterizedType(rawClass, encodedArguments) : this);
		}
```

**왜 이 위치인가.**\
세 가지 대안 위치가 있었고 각각 다른 곳을 건드린다.

1. **생성 시점에 감싼다** — `forClassWithGenerics`가 `variables`를 `SerializableTypeWrapper`로 미리 감싸는 안.\
   모든 호출에 비용이 붙고(마이크로벤치 12ns -> 37ns 실측), 직렬화하지 않는 절대다수 경로가 손해를 본다. 기각.
2. **필드를 `transient`로 빼고 `readObject`에서 복원** — #37109가 쓴 처방.\
   여기서는 `variables`가 `final`이자 생성자 인자이고, 복원에 필요한 좌표(선언 클래스)가 그 필드 자신에서만 나오므로 훅 안에서 좌표를 따로 저장해야 한다.\
   결국 프록시와 같은 정보를 담으면서 클래스 형식만 더럽힌다. 기각.
3. **`writeReplace`/`readResolve` 프록시** — 채택.\
   스트림 형식과 런타임 표현을 분리하고, 자격 미달이면 `this`로 축퇴해 기존 동작을 보존할 수 있는 유일한 위치다.

세부 결정 세 가지는 각각 관측 가능한 실패를 막는다.\
(1) `Arrays.equals`의 좌우 순서(:1648) — 뒤집으면 정상 케이스가 조용히 폴백으로 샌다.\
(2) 마커 검사 우선(:1755 이전에 :1760이 오면 안 됨) — 순서가 반대면 복사본이 실려 정본성이 깨진다.\
(3) `encodedVariable` 판정(:1769) — 없으면 멀쩡하던 스트림 형식이 바뀐다.

### 5.3 검증 쪽 (readResolve)

받는 쪽은 스트림을 신뢰하지 않고, 복원 전에 세 단계로 자기 일관성을 검사한다.

```java
// after: ResolvableType.java:1802-1812 (발췌, 3bb5ed1ae4f)
		private Object readResolve() throws ObjectStreamException {
			// The stream is not trusted to be self-consistent: incomplete or mismatched
			// proxy state fails with InvalidObjectException rather than downstream errors.
			if (this.rawType == null || this.encodedArguments == null) {
				throw new InvalidObjectException("Incomplete serialization proxy for SyntheticParameterizedType");
			}
			TypeVariable<?>[] variables = this.rawType.getTypeParameters();
			if (this.encodedArguments.length != variables.length) {
				throw new InvalidObjectException("Mismatched type arguments for " + this.rawType.getName());
			}
```

null 검사가 형식적이지 않은 이유는 기본 직렬화가 **생성자를 우회**하기 때문이다 — `final` 필드도 조작된 스트림에서는 null로 도착할 수 있다.\
arity 검사는 버전 스큐(송신 측과 수신 측의 타입 파라미터 개수가 다른 경우)를 역직렬화 지점에서 잡는다.\
검증이 없다면 같은 상황이 한참 뒤 `resolveVariable`의 조용한 null이나 원소 접근 시 AIOOBE로 나타난다.

> **생성자 우회** — 자바의 기본 역직렬화가 객체를 만들 때 생성자를 부르지 않고 필드에 값을 직접 꽂는 성질.\
> 예: 생성자에서 `Assert.notNull`을 해 뒀어도 역직렬화로 들어온 객체는 그 검사를 통과한 적이 없다.

## 6. 범위 밖과 인접 영향

이 PR이 일부러 남겨 둔 영역, 같은 문제를 다르게 푸는 이웃 코드, 그리고 실측하지 않은 항목을 정리한다.

- **SPR-17070 영역(`as()`/`getSuperType()`/`getInterfaces()` 파생, `resolveType()`)**: javadoc이 "may not be Serializable"로 계약을 이미 축소해 둔 곳이라 손대지 않았다.\
  가드 테스트 `serializeSuperTypeIsNotSupported`가 그 경계를 명시적으로 고정해 "이 PR이 우발적으로 계약을 넓히지 않았음"을 증명한다.\
  계약을 되넓히려면 별도 제안이 필요하다.
- **같은 패턴의 다른 위치**: `SerializableTypeWrapper`(SerializableTypeWrapper.java:57 이하)가 `forField`/`forMethodParameter` 경로에서 **다른 방식**(동적 프록시 + TypeProvider)으로 같은 문제를 이미 풀고 있다.\
  이 PR은 그 보호막이 닿지 않는 한 갈래에 프록시 관용구로 동등한 보호를 붙인 것이다.\
  gh-36346(`22bd8bd7043`)이 캐시 필드 4개를 `transient`로 돌린 것도 같은 계열의 부분 처방이었고, 본체 필드(`type`·`variableResolver`)를 남겨 둔 그 미완결을 이 PR이 마저 채운다.
- **`hash` 필드의 JVM 간 성질**: `hash`는 비-transient라 송신 측 값이 그대로 실려 온다(:125, :1034).\
  그 뿌리에 `Class.hashCode()`(identity 기반)가 있어 다른 JVM에서 재계산 값과 갈릴 수 있다.\
  이는 `forField` 경로에도 있는 기존 성질이고 이 PR이 만들지도, 손대지도 않았다.
- **하위호환**: 공개 API 시그니처 변화 없음.\
  신설 클래스는 둘 다 `private static final`.\
  런타임 경로는 불변이고, 스트림 형식이 바뀌는 것은 **원래 직렬화가 실패하던 인스턴스뿐**이다(성공하던 인스턴스는 `this` 폴백으로 형식 보존).
- **미확인**: 비-HotSpot JVM에서 `TypeVariable` 구현이 `Serializable`인 사례가 실제로 존재하는지는 코드 주석·설계 논의 수준에서만 다뤘고 실측하지 않았다(분기 순서는 그 가능성에 대한 방어).\
  또한 이 PR의 7.0.x 백포트 여부는 트리아지 전이라 미정이다.

> **백포트(backport)** — 최신 브랜치에 들어간 수정을 이전 버전 브랜치에도 옮겨 적용하는 것.\
> 예: main에 머지된 fix를 7.0.x 유지보수 브랜치에도 넣을지는 별도 판단이다.
