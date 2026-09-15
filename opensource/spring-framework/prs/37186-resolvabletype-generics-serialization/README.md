# PR #37186 — Make ResolvableType.forClassWithGenerics results serializable

## 0. 정향

이 문서는 `ResolvableType`의 직렬화 결함 수정 PR의 해설이다.\
특이점이 둘 있다.\
**조사 과정에서 목표 자체가 재정의된** 작업이고(원래 쫓던 증상이 "버그가 아니라 문서화된 계약 축소"로 판명), 이 시리즈에서 처음으로 **높음 등급 절차**(blind 테스트 워커·리뷰 루프 3회·마이크로벤치 2회)를 완주한 PR이다.\
다 읽으면 "왜 as() 파생은 안 고치고 forClassWithGenerics만 고쳤는가"와 "직렬화 프록시가 무엇을 실어 보내는가"를 설명할 수 있어야 한다.

> **직렬화(serialization)** — 객체를 바이트 스트림으로 바꿔 파일·네트워크로 보내고 다시 객체로 되살리는 것.\
> 예: 톰캣이 클러스터의 다른 노드로 `HttpSession`을 복제할 때 그 안의 객체들을 전부 직렬화한다.

> **ResolvableType** — Spring이 제네릭 타입 정보를 다루려고 JDK `Type`을 감싼 값 객체.\
> 예: `List<String>`을 "raw는 List, 첫 인자는 String"으로 쪼개어 들고 다닌다.

> **blind 테스트 워커** — 구현 diff를 보지 않고 명세만 읽고 테스트를 설계하는 별도 작업자.\
> 예: 구현을 모르니 "구현이 이렇게 생겼을 테니 통과하겠지"라는 편향 없이 계약만 겨눈다.

같은 폴더: [테스트 해설](tests.md) · [리뷰 과정](review.md) · [실구조](structure.md).\
개념 문서: [직렬화 프록시와 버전 스큐](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md) · [JDK 제네릭 정보 instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md) · [직렬화 학습 시리즈](../../concepts/serialization-series/00-learning-index.md)

## 1. 배경 — 원래 쫓던 것과 실제로 잡은 것

출발점은 #37109(C4) 작업 중 발견해 그 본문에 선공개했던 증상이었다.\
`getElementTypeDescriptor()` 결과가 `NotSerializableException: TypeVariableImpl`로 직렬화 실패.\
착수 조사에서 재현 매트릭스를 넓혀 보니 범위가 훨씬 컸다 — `TypeDescriptor.collection()`/`map()` **공개 팩토리 산출물 전부**, 그리고 그 토대인 `ResolvableType.forClassWithGenerics()` 자체가 비직렬화였다.

> **NotSerializableException** — 직렬화하려는 그래프 안에 `Serializable`이 아닌 객체가 하나라도 있으면 그 자리에서 던져지는 예외.\
> 예: 메시지 끝에 `sun.reflect.generics...TypeVariableImpl`이 붙어 "이 녀석 때문에 못 싣는다"를 알려 준다.

> **TypeVariable** — `List<E>`의 `E`처럼 아직 정해지지 않은 타입 자리를 나타내는 JDK 리플렉션 객체.\
> 예: `List.class.getTypeParameters()[0]`이 그 `E`를 돌려준다.

그런데 조사 워커가 결정적 사실을 발굴했다.\
원 증상(as() 상위 타입 워크 파생)은 **SPR-17070(2018)이 의도적으로 만든 트레이드오프**였다.\
그 커밋은 `SerializableTypeWrapper`의 파생 경로 감싸기를 성능을 위해 일부러 제거하고 "may not be Serializable" javadoc까지 달아 **계약 자체를 축소**해 뒀다.\
반면 `forClassWithGenerics`는 그 커밋이 건드리지도, 단서를 달지도 않은 **순수한 갭** — 계약(Serializable)이 살아있는데 구현이 어기고 있었다.

같은 증상이 두 갈래로 갈리는 지점을 나란히 놓으면 이렇다.

```text
증상은 같다: NotSerializableException: TypeVariableImpl

  갈래 X — as() 파생                       갈래 Z — forClassWithGenerics
  +--------------------------------+         +--------------------------------+
  | javadoc : "may not be          |         | javadoc : 단서 없음            |
  |            Serializable"       |         | 계약    : Serializable 유효    |
  | 출처    : SPR-17070 (2018)     |         | 출처    : 아무도 축소 안 함    |
  | 성격    : 의도된 트레이드오프  |         | 성격    : 순수한 갭            |
  | 판정    : 버그 아님            |         | 판정    : 버그                 |
  +--------------------------------+         +--------------------------------+
    -> 고치려면 "계약을 되넓히자"는           -> 이 PR 의 대상
       별도 제안이 필요하다
```

그래서 범위가 갈렸다.\
계약이 살아있는 쪽(Z)만 이 PR로 고치고, 계약이 축소된 쪽(X)은 "계약을 되넓히자는 제안"이라 코드가 아닌 별도 판단 대상으로 보류했다.\
같은 "직렬화 깨짐"이라도 **javadoc(약속)의 상태가 버그와 제안을 가른다**.

## 2. 수정 전 동작 — 폭탄 운반자 두 곳

`forClassWithGenerics(List.class, String.class)`가 만드는 객체 그래프에는 비직렬화 JDK 객체가 두 자리에 실린다.

1. `TypeVariablesVariableResolver.variables` — 클래스의 raw `TypeVariable[]`.\
   아이러니하게 `VariableResolver` 인터페이스는 `extends Serializable`로 계약을 **선언**해 두고 있었다.
2. `SyntheticParameterizedType.typeArguments` — generics 인자가 null이거나 미해석 `TypeVariable`이면 클래스의 raw 타입 파라미터가 인자 자리에 재주입된다.

만드는 호출에서 터지는 자리까지 세로로 따라가면 이렇다.

```text
TypeDescriptor.collection(List.class, valueOf(String))
        |
        v
ResolvableType.forClassWithGenerics(List.class, RT(String))
        |
        +-- variables = List.class.getTypeParameters()   -> {E}  (raw TypeVariable)
        |
        +-- arguments[i] 채우기
        |      |
        |      +-- 인자가 정상 타입    -> arguments[i] = String.class      [안전]
        |      +-- 인자가 null/미해석  -> arguments[i] = variables[i]      [폭탄 B]
        |
        +-- type            = new SyntheticParameterizedType(List, arguments)
        +-- variableResolver= new TypeVariablesVariableResolver(variables, generics)
                                                              ^
                                                              +-- variables 를 그대로 보관  [폭탄 A]
        |
        v
완성된 ResolvableType 을 TypeDescriptor 가 필드로 들고 다닌다
        |
        v
세션 복제 / 분산 캐시 / 원격 예외가 그 객체를 직렬화한다
        |
        +-- type 안의 TypeVariable      -> NotSerializableException  (폭탄 B)
        +-- variableResolver 안의 variables -> NotSerializableException  (폭탄 A)
```

두 폭탄은 **서로 다른 입력에서 켜진다** — 인자가 다 구체 타입이면 A만, generics 배열 자체가 null이면 B만, 배열은 있고 원소가 null이면 둘 다.

직렬화하면 어느 쪽이든 `NotSerializableException: TypeVariableImpl`.\
영향권은 `ResolvableType`을 비-transient로 보유한 Serializable들 — `TypeDescriptor`, `NoSuchBeanDefinitionException`, `PayloadApplicationEvent` — 까지 번진다.\
참고로 gh-36346(2026-02, Juergen)이 같은 문제 계열의 **캐시 필드**를 transient로 수선했지만, 본체 필드(type·variableResolver)는 그대로였다 — 이 PR은 그 미완결의 완성이기도 하다.

> **transient** — "이 필드는 스트림에 싣지 말라"고 표시하는 자바 키워드.\
> 예: 캐시 필드를 transient로 두면 직렬화에서 빠지고 복원 후 다시 계산된다.

## 3. 수정 해설 — 직렬화 프록시 2쌍

두 내부 클래스에 `writeReplace()`/`readResolve()` 직렬화 프록시를 달았다.\
원리는 [개념 문서](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md)가 정본이고, 여기선 설계 결정만 요약한다.

> **직렬화 프록시(serialization proxy)** — 실어 보내기 어려운 객체 대신, 같은 내용을 담은 간단한 대역 객체를 스트림에 싣는 관용구.\
> 예: `writeReplace()`가 "나 대신 이걸 보내라"를, `readResolve()`가 "받은 걸 원래 객체로 되돌려라"를 맡는다.

- **보내는 것은 좌표**: raw TypeVariable 대신 "선언 Class(이름으로 직렬화됨) + 타입 파라미터 인덱스".\
  복원은 `getTypeParameters()` **재조회** — JDK가 정본 인스턴스를 캐시하므로(instance-stability) 복원본이 원본과 identical, 그래서 equals/hashCode/ResolvableType의 사전 계산된 hash까지 전부 정합.
- **마커(identity) 분기 우선**: 한 인자가 마커 대상이면서 Serializable일 수도 있는 환경에서 Serializable 분기가 먼저 잡히면 복사본이 복원돼 정본성이 깨진다 — 의미 기반 인코딩이 항상 우선.
- **무악화 폴백**: 인코딩 불가한 인자를 만나면 `this`를 반환해 오늘과 동일한 실패를 유지한다.\
  마커가 하나도 필요 없으면 역시 `this`를 반환하므로 **원래 직렬화되던 인스턴스의 스트림 형식이 불변**이다(롤링 업그레이드 안전).
- **검증**: `readResolve`가 null·개수(arity)·인덱스 범위를 검사해 위반 시 `InvalidObjectException` — 버전 스큐·조작 스트림이 raw NPE/AIOOBE나 조용한 오매칭으로 새지 않게.
- **런타임 0 변화**: 훅은 직렬화 시점에만 호출된다.\
  비직렬화 경로는 바이트 하나 안 바뀌며, I4 가드 테스트가 이를 고정한다.

> **instance-stability(인스턴스 안정성)** — 같은 JVM에서 같은 질문을 다시 해도 매번 **같은 객체**가 돌아오는 성질.\
> 예: `List.class.getTypeParameters()[0]`은 몇 번을 불러도 `==`로 같은 `E`다.

> **롤링 업그레이드(rolling upgrade)** — 서버를 한 대씩 새 버전으로 바꾸는 배포 방식. 잠시 구버전과 신버전이 함께 돈다.\
> 예: 신버전이 만든 스트림을 아직 안 바뀐 구버전 노드가 읽어야 하므로 스트림 형식이 바뀌면 곤란하다.

> **버전 스큐(version skew)** — 보내는 쪽과 받는 쪽이 보고 있는 클래스 정의가 서로 다른 상태.\
> 예: 송신 측 `Map`은 타입 파라미터가 2개인데 수신 측에서 3개로 바뀌어 있으면 개수가 안 맞는다.

같은 객체가 수정 전후에 스트림에서 어떻게 달라지는지를 나란히 놓으면 이렇다.

```text
대상: forClassWithGenerics(List.class, (ResolvableType[]) null)   // List<?>

  수정 전                                  수정 후
  +-------------------------------+        +--------------------------------+
  | 스트림에 싣는 것:             |        | 스트림에 싣는 것:              |
  |   SyntheticParameterizedType  |        |   SerializedSynthetic...       |
  |     rawType   = List.class    |        |     rawType   = List.class     |
  |     typeArgs  = {E}           |        |     encodedArgs = {0}          |
  |                  ^ 비직렬화   |        |                   ^ 그냥 정수  |
  | 결과 : NotSerializable        |        | 결과 : 왕복 성공               |
  |        Exception              |        | 복원 : List.getTypeParameters  |
  |                               |        |        ()[0] 재조회 -> 정본 E  |
  +-------------------------------+        +--------------------------------+
    -> 객체를 그대로 실으려다 실패           -> 객체 대신 "좌표"를 싣는다
```

스트림을 건너는 것은 객체가 아니라 **좌표**이고, 받는 쪽은 그 좌표로 자기 JVM의 정본을 다시 찾는다.

**범위 밖 유지**: as()/getSuperType()/getInterfaces() 파생은 SPR-17070대로 여전히 비직렬화 — 가드 테스트가 그 경계를 명시적으로 고정해 "이 PR이 우발적으로 계약을 넓히지 않았음"을 증명한다.

## 4. 검증 — 높음 등급 사슬

검증은 조사에서 리뷰까지 여덟 단계로 이어졌다.\
재현 매트릭스 12케이스로 범위를 확정한 뒤 연구 워커가 19개 생성 경로를 라운드트립하고 후보 3종을 실증했고, codex 설계 선검증이 반영할 조건 5개를 돌려줬다.\
그다음 **blind 테스트 워커**가 구현을 열람하지 않은 채 15건을 설계했는데, red 10건이라는 예측이 실측과 정확히 일치했다.\
fix를 얹은 뒤 spring-core 전체 **5,173 tests 0 failures**를 확인했고, 실물 스모크로 팩토리 4케이스가 OK로 전환되며 범위 밖은 불변임을 봤다.\
마지막이 **리뷰 루프 3회**다 — 1회차에서 채택 6건을 반영했고, 2회차는 주석 1건, 3회차는 양측이 "신규 채택 없음"과 전 렌즈 verified로 닫았다.\
상세는 [review.md](review.md).

> **라운드트립(round-trip)** — 객체를 직렬화했다가 다시 역직렬화해 원래대로 돌아오는지 확인하는 왕복 검사.\
> 예: 써서 바이트로 만들고, 읽어서 객체로 되살린 뒤 원본과 equals·hashCode가 같은지 본다.

## 5. 교훈

이 시리즈 첫 높음 등급 작업이 남긴 것은 버그의 정의, 측정의 역할, 프록시 발동 조건, 그리고 blind 설계의 실효성 넷이다.

1. **계약의 상태가 버그를 정의한다.**\
   같은 증상이라도 javadoc이 살아있으면 버그, 문서로 축소돼 있으면 제안 — 조사 없이 "고장 = 버그"로 달리면 SPR-17070 같은 의도를 뒤집는 PR을 냈을 것이다.
2. **측정이 설계 논쟁을 끝낸다.**\
   "생성 시점 wrapping" 후보는 12->37ns 실측으로 기각됐고, 핫패스 비용 질문도 벤치 수치로 종결됐다.
3. **프록시는 원래 실패하던 그래프에만.**\
   무악화는 폴백만이 아니라 "발동 조건"의 문제이기도 하다 — 마커 없는 인스턴스까지 프록시화하면 스트림 형식 회귀가 생긴다.
4. **blind 테스트 설계는 실제로 잡는다.**\
   구현을 모르는 설계자가 "Synthetic 래퍼 자체가 아니라 내부 JDK Type에 identity를 걸어라"는 fix-agnostic 함정을 미리 찾아냈다.
