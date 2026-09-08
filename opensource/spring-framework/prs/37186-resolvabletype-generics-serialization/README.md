# PR #37186 — Make ResolvableType.forClassWithGenerics results serializable

## 0. 정향

이 문서는 `ResolvableType`의 직렬화 결함 수정 PR의 해설이다. 특이점이 둘 있다:
**조사 과정에서 목표 자체가 재정의된** 작업이고(원래 쫓던 증상이 "버그가 아니라
문서화된 계약 축소"로 판명), 이 시리즈에서 처음으로 **높음 등급 절차**(blind
테스트 워커·리뷰 루프 3회·마이크로벤치 2회)를 완주한 PR이다. 다 읽으면 "왜 as()
파생은 안 고치고 forClassWithGenerics만 고쳤는가"와 "직렬화 프록시가 무엇을 실어
보내는가"를 설명할 수 있어야 한다.

같은 폴더: [테스트 해설](tests.md) · [리뷰 과정](review.md) · [실구조](structure.md).
개념 문서: [직렬화 프록시와 버전 스큐](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md) ·
[JDK 제네릭 정보 instance-stability](../../concepts/jdk-generic-info-instance-stability/jdk-generic-info-instance-stability.md) ·
[직렬화 학습 시리즈](../../concepts/serialization-series/00-learning-index.md)

## 1. 배경 — 원래 쫓던 것과 실제로 잡은 것

출발점은 #37109(C4) 작업 중 발견해 그 본문에 선공개했던 증상이었다:
`getElementTypeDescriptor()` 결과가 `NotSerializableException: TypeVariableImpl`로
직렬화 실패. 착수 조사에서 재현 매트릭스를 넓혀 보니 범위가 훨씬 컸다 —
`TypeDescriptor.collection()`/`map()` **공개 팩토리 산출물 전부**, 그리고 그 토대인
`ResolvableType.forClassWithGenerics()` 자체가 비직렬화였다.

그런데 조사 워커가 결정적 사실을 발굴했다: 원 증상(as() 상위 타입 워크 파생)은
**SPR-17070(2018)이 의도적으로 만든 트레이드오프**였다. 그 커밋은
`SerializableTypeWrapper`의 파생 경로 감싸기를 성능을 위해 일부러 제거하고 "may
not be Serializable" javadoc까지 달아 **계약 자체를 축소**해 뒀다. 반면
`forClassWithGenerics`는 그 커밋이 건드리지도, 단서를 달지도 않은 **순수한 갭**
— 계약(Serializable)이 살아있는데 구현이 어기고 있었다.

그래서 범위가 갈렸다: 계약이 살아있는 쪽(Z)만 이 PR로 고치고, 계약이 축소된
쪽(X)은 "계약을 되넓히자는 제안"이라 코드가 아닌 별도 판단 대상으로 보류했다.
같은 "직렬화 깨짐"이라도 **javadoc(약속)의 상태가 버그와 제안을 가른다**.

## 2. 수정 전 동작 — 폭탄 운반자 두 곳

`forClassWithGenerics(List.class, String.class)`가 만드는 객체 그래프에는
비직렬화 JDK 객체가 두 자리에 실린다:

1. `TypeVariablesVariableResolver.variables` — 클래스의 raw `TypeVariable[]`.
   아이러니하게 `VariableResolver` 인터페이스는 `extends Serializable`로 계약을
   **선언**해 두고 있었다.
2. `SyntheticParameterizedType.typeArguments` — generics 인자가 null이거나 미해석
   `TypeVariable`이면 클래스의 raw 타입 파라미터가 인자 자리에 재주입된다.

직렬화하면 어느 쪽이든 `NotSerializableException: TypeVariableImpl`. 영향권은
`ResolvableType`을 비-transient로 보유한 Serializable들 — `TypeDescriptor`,
`NoSuchBeanDefinitionException`, `PayloadApplicationEvent` — 까지 번진다.
참고로 gh-36346(2026-02, Juergen)이 같은 문제 계열의 **캐시 필드**를 transient로
수선했지만, 본체 필드(type·variableResolver)는 그대로였다 — 이 PR은 그 미완결의
완성이기도 하다.

## 3. 수정 해설 — 직렬화 프록시 2쌍

두 내부 클래스에 `writeReplace()`/`readResolve()` 직렬화 프록시를 달았다. 원리는
[개념 문서](../../concepts/serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md)가 정본이고, 여기선
설계 결정만 요약한다:

- **보내는 것은 좌표**: raw TypeVariable 대신 "선언 Class(이름으로 직렬화됨) +
  타입 파라미터 인덱스". 복원은 `getTypeParameters()` **재조회** — JDK가 정본
  인스턴스를 캐시하므로(instance-stability) 복원본이 원본과 identical, 그래서
  equals/hashCode/ResolvableType의 사전 계산된 hash까지 전부 정합.
- **마커(identity) 분기 우선**: 한 인자가 마커 대상이면서 Serializable일 수도 있는
  환경에서 Serializable 분기가 먼저 잡히면 복사본이 복원돼 정본성이 깨진다 —
  의미 기반 인코딩이 항상 우선.
- **무악화 폴백**: 인코딩 불가한 인자를 만나면 `this`를 반환해 오늘과 동일한 실패를
  유지한다. 마커가 하나도 필요 없으면 역시 `this`를 반환하므로 **원래 직렬화되던
  인스턴스의 스트림 형식이 불변**이다(롤링 업그레이드 안전).
- **검증**: `readResolve`가 null·개수(arity)·인덱스 범위를 검사해 위반 시
  `InvalidObjectException` — 버전 스큐·조작 스트림이 raw NPE/AIOOBE나 조용한
  오매칭으로 새지 않게.
- **런타임 0 변화**: 훅은 직렬화 시점에만 호출된다. 비직렬화 경로는 바이트 하나
  안 바뀌며, I4 가드 테스트가 이를 고정한다.

**범위 밖 유지**: as()/getSuperType()/getInterfaces() 파생은 SPR-17070대로 여전히
비직렬화 — 가드 테스트가 그 경계를 명시적으로 고정해 "이 PR이 우발적으로 계약을
넓히지 않았음"을 증명한다.

## 4. 검증 — 높음 등급 사슬

검증은 조사에서 리뷰까지 여덟 단계로 이어졌다. 재현 매트릭스 12케이스로 범위를
확정한 뒤 연구 워커가 19개 생성 경로를 라운드트립하고 후보 3종을 실증했고, codex
설계 선검증이 반영할 조건 5개를 돌려줬다. 그다음 **blind 테스트 워커**가 구현을
열람하지 않은 채 15건을 설계했는데, red 10건이라는 예측이 실측과 정확히 일치했다.
fix를 얹은 뒤 spring-core 전체 **5,173 tests 0 failures**를 확인했고, 실물 스모크로
팩토리 4케이스가 OK로 전환되며 범위 밖은 불변임을 봤다. 마지막이 **리뷰 루프
3회**다 — 1회차에서 채택 6건을 반영했고, 2회차는 주석 1건, 3회차는 양측이 "신규
채택 없음"과 전 렌즈 verified로 닫았다. 상세는 [review.md](review.md).

## 5. 교훈

이 시리즈 첫 높음 등급 작업이 남긴 것은 버그의 정의, 측정의 역할, 프록시 발동 조건,
그리고 blind 설계의 실효성 넷이다.

1. **계약의 상태가 버그를 정의한다.** 같은 증상이라도 javadoc이 살아있으면 버그,
   문서로 축소돼 있으면 제안 — 조사 없이 "고장 = 버그"로 달리면 SPR-17070 같은
   의도를 뒤집는 PR을 냈을 것이다.
2. **측정이 설계 논쟁을 끝낸다.** "생성 시점 wrapping" 후보는 12->37ns 실측으로
   기각됐고, 핫패스 비용 질문도 벤치 수치로 종결됐다.
3. **프록시는 원래 실패하던 그래프에만.** 무악화는 폴백만이 아니라 "발동 조건"의
   문제이기도 하다 — 마커 없는 인스턴스까지 프록시화하면 스트림 형식 회귀가 생긴다.
4. **blind 테스트 설계는 실제로 잡는다.** 구현을 모르는 설계자가 "Synthetic 래퍼
   자체가 아니라 내부 JDK Type에 identity를 걸어라"는 fix-agnostic 함정을 미리
   찾아냈다.
