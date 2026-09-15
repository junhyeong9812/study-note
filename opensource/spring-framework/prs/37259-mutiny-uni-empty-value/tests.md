# PR #37259 - 테스트 해설 (테스트 하나하나)

> `ReactiveAdapterRegistryTests`의 중첩 클래스 `Mutiny`에 추가된 2건 + 같은 그룹의
> 기존 5건이 맡은 가드 역할. 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 /
> 단언 하나하나의 의미"로 해설한다. red와 가드의 역할 분담 개념은
> [../37153/guard-tests.md](../37153-enum-array-annotation-probe/guard-tests.md), 형식 원본은
> [../37153/tests.md](../37153-enum-array-annotation-probe/tests.md).

배치 전체를 먼저 본다.\
이 결함은 **어댑터의 한 방향(`toPublisher`)에서만, 그것도 소스가 `null`일 때만** 발화한다.\
그래서 새 테스트 둘이 "null 소스"와 "역방향의 빈 입력"을 각각 맡고 기존 다섯이 "비-null 소스"와 "형제 타입"을 맡는 구도가 된다.\
두 축으로 줄 세우면 이렇다.

> **red 테스트 / 가드 테스트** — red는 수정 전에 반드시 실패해야 하는 테스트, 가드는 수정 전후 모두 통과해야 하는 테스트.\
> 예: red 가 없으면 결함을 겨냥하지 못한 것이고, 가드가 깨지면 기존 동작을 망가뜨린 것이다.

| | 소스가 `null` (empty-value 경로) | 소스가 비-null |
|---|---|---|
| `toPublisher` (Uni -> Publisher) | T1 `fromNullValue` - **red** | T3 `fromUni`(기존) - 가드 |
| `fromPublisher` (Publisher -> Uni) | T2 `toUniFromEmptyPublisher` - 대칭 기준점 | T4 `toUni`(기존) - 가드 |

같은 배치를 fix 전후 결과까지 넣은 격자로 보면 각 칸이 무엇을 덮는지가 드러난다.

```text
                          |  fix 전   |  fix 후  |  결함 줄을 지나나
--------------------------+-----------+----------+-------------------
T1 fromNullValue          |  FAIL     |  PASS    |  지난다 (L110)
   (null -> Publisher)    |  Timeout  |  null    |
--------------------------+-----------+----------+-------------------
T2 toUniFromEmptyPublisher|  PASS     |  PASS    |  지나지 않는다
   (빈 Publisher -> Uni)  |  null     |  null    |  -> 기대값의 근거가 된다
--------------------------+-----------+----------+-------------------
T3 fromUni (비-null 정방향)|  PASS     |  PASS    |  지나지 않는다 (분기 false)
T4 toUni   (비-null 역방향)|  PASS     |  PASS    |  지나지 않는다
T5~T7 Multi / 등록 확인   |  PASS     |  PASS    |  지나지 않는다
```

-> 결함 줄을 지나는 테스트는 T1 하나뿐이고, 나머지 여섯은 전부 "안 건드렸음"을 지킨다.

T2가 왼쪽 아래 칸에 있는 것이 이 배치의 요점이다.\
그 칸은 **결함 줄을 지나지 않으면서** "빈 것의 Uni측 표현이 무엇인가"를 실행으로 고정하는 자리다.\
그래야 T1의 기대값이 임의로 고른 값이 아니라 T2가 고정한 표현에서 유도된 값임이 드러난다.

## T1. `fromNullValue` - red

새로 추가한 첫 건은 어댑터에 `null`을 넘겨 프레임워크가 empty-value로 대체하게 만든다.

```java
@Test
void fromNullValue() {
	Object target = getAdapter(Uni.class).toPublisher(null);
	assertThat(target).isInstanceOf(Mono.class);
	assertThat(((Mono<Integer>) target).block(FIVE_SECONDS)).isNull();
}
```
(ReactiveAdapterRegistryTests.java:303-308)

- **주장**: `Uni` 어댑터에 `null` 소스를 주면 결과 Publisher가 값 없이 정상 완료한다.
- **fix 전 red인 이유**: `toPublisher`가 `source == null`을 보고 `getDescriptor().getEmptyValue()`로 대체하는데(ReactiveAdapter.java:109-110), 수정 전 공급자가 `Uni.createFrom().nothing()` = `UniNever.INSTANCE`였다.\
  구독해도 `onNext`·`onComplete`·`onError`가 하나도 오지 않으므로 `block`이 5초를 채우고 `IllegalStateException: Timeout on blocking read for 5000 ms`로 끝난다.

**세 줄이 각각 다른 것을 확인한다.**\
특히 둘째 줄과 셋째 줄이 갈라지는 지점이 이 결함의 성격을 그대로 보여 준다.

- 첫 줄 `getAdapter(Uni.class).toPublisher(null)` - **인자로 넘긴 `null`이 이 테스트의 전부다.**\
  `getAdapter`는 `Uni.class`라는 **선언 타입**으로 조회하므로 값이 없어도 어댑터를 정상적으로 찾는다(ReactiveAdapterRegistry.java:195-209).\
  프로덕션에서 `Uni<T>`를 반환하는 핸들러가 `null`을 반환했을 때와 정확히 같은 상황을 세 단어로 재현한 것이다.
- 둘째 줄 `isInstanceOf(Mono.class)` - **fix 전에도 통과한다.**\
  이 사실이 중요하다.\
  Reactor가 클래스패스에 있으므로 레지스트리는 어댑터를 `ReactorAdapter`로 감싸고(ReactiveAdapterRegistry.java:164-169), 그것이 단일 값 타입이면 결과를 `Mono.from(publisher)`로 한 번 더 감싼다(:259-263).\
  변환은 어느 단계도 실패하지 않는다.\
  **red의 정체는 타입 불일치가 아니다** - 둘째 줄이 깨졌다면 셋째 줄은 실행조차 되지 않았을 것이다.
- 셋째 줄 `block(FIVE_SECONDS)).isNull()` - **여기서 깨진다.**\
  `Mono.block()`은 세 갈래다.\
  아이템이 오면 그 값을, 아이템 없이 `onComplete`만 오면 `null`을 반환하고, 아무 신호도 없으면 타임아웃 예외를 던진다.\
  `UniNever`는 셋째 갈래로 떨어진다.

세 줄이 통과하는 관문을 세로로 보면 red가 어디에서 나는지가 한눈에 보인다.

```text
  getAdapter(Uni.class).toPublisher(null)
              |
              v
  어댑터를 찾았나?            -> 찾는다 (선언 타입 조회)      fix 전후 동일
              |
              v
  Mono 로 감싸졌나?           -> 감싸진다 (ReactorAdapter)    fix 전후 동일
              |
              v
  block(5s) 이 무엇을 받나?
        |                          |
   [fix 전]                   [fix 후]
   신호 0 건                  onComplete 1 건
        |                          |
        v                          v
   Timeout 예외                  null 반환
```

-> 변환은 전부 성공하고 마지막 관문에서만 갈린다. 그래서 red 의 형태가 값 불일치가 아니라 예외다.

**단언이 `null`을 기대하는 이유.**\
"빈 값"을 Java 값으로 관측하면 `null`이기 때문이다.\
Reactive Streams는 `onNext(null)`을 **금지**하므로 Mutiny의 Uni -> Publisher 변환은 null item을 "아이템 방출 없이 `onComplete`"로 매핑하고(`UniToMultiPublisher.java:90-96`), `Mono.block()`은 그 빈 완료를 받아 `null`을 반환한다.\
**null이라는 값이 파이프를 타고 이동한 것이 아니라, "비어 있는 정상 완료"의 Java 레벨 표현이 `null`인 것이다.**\
그리고 기대값이 "예외"가 아닌 이유는 이 어댑터가 `singleOptionalValue`로 등록돼 `supportsEmpty()`를 true로 선언했기 때문이다(ReactiveTypeDescriptor.java:91-93, :148-150).\
`toPublisher(null)`은 오류 경로가 아니라 정식 계약 경로다.

> **계약 경로(contract path)** — 예외 상황이 아니라 API가 정식으로 지원한다고 약속한 사용 방식.\
> 예: `supportsEmpty()`가 true인 타입에 `null`을 넘기는 것은 잘못된 사용이 아니라 설계된 사용이다.

`FIVE_SECONDS`는 이 파일이 이미 갖고 있던 상수이고 형제 테스트가 전부 같은 값을 쓴다.\
여기서는 그 상수가 성격을 바꾼다.\
다른 테스트에서는 "느려도 이만큼은 기다려 준다"는 여유였는데, 이 테스트에서는 **red를 만드는 장치**다 - 5초가 지나야 실패가 확정된다.\
그래서 fix 전 이 그룹을 돌리면 실행 시간이 눈에 띄게 길어진다.

## T2. `toUniFromEmptyPublisher` - 대칭 기준점 (전후 green)

둘째 건은 반대 방향을 본다.\
빈 `Publisher`를 `Uni`로 되돌렸을 때 무엇이 나오는지를 고정한다.

```java
@Test
void toUniFromEmptyPublisher() {
	Object target = getAdapter(Uni.class).fromPublisher(Mono.empty());
	assertThat(target).isInstanceOf(Uni.class);
	assertThat(((Uni<Integer>) target).await().atMost(FIVE_SECONDS)).isNull();
}
```
(ReactiveAdapterRegistryTests.java:310-315)

- **주장**: 빈 `Publisher`를 `Uni`로 바꾸면 `null` item으로 완료된다.
- **fix 전에도 green인 이유**: 이 테스트는 **결함 줄을 지나가지 않는다.**\
  `ReactiveAdapter.fromPublisher`(L120-122)는 `fromPublisherFunction`만 호출하고, 거기엔 `emptySupplier`가 전혀 등장하지 않는다.\
  이 저장소가 고정한 Mutiny는 1.10.0이라(`framework-platform.gradle:56`) `MutinyRegistrar`의 `else` 분기(Mutiny 1)가 활성이고, 그 람다는 `publisher -> Uni.createFrom().publisher(publisher)`다(:403).\
  빈 스트림이 들어오면 `UniCreateFromPublisher`의 `onComplete`가 `subscriber.onItem(null)`을 부른다(`UniCreateFromPublisher.java:86-91`).

**그렇다면 왜 red도 아닌 테스트를 추가했나.**\
두 가지 일을 한다.

첫째, **T1의 기대값을 정당화한다.**\
T1이 "빈 완료"를 기대하는 근거는 이 어댑터 자신의 역방향이 이미 "빈 것 = null item 완료"로 정의돼 있다는 사실이다.\
T2가 그 정의를 실행으로 못 박으면, empty-value로 무엇을 골라야 왕복이 닫히는지가 코드에서 따라 나온다.

```text
빈 Publisher --fromPublisher(:403)--> Uni(null item 완료)     <- T2가 고정
Uni(null item) --toPublisher(:402)--> onNext 없이 onComplete  <- T1이 요구
```

> **대칭 기준점(symmetry anchor)** — 한쪽 방향의 동작을 실행으로 못 박아, 반대 방향의 정답을 유도하는 기준으로 삼는 테스트.\
> 예: "빈 것을 Uni로 적으면 null item"을 T2가 고정하면, empty-value로 무엇을 써야 하는지가 취향이 아니라 결과가 된다.

수정값 `nullItem()`은 이 두 화살표를 잇는 유일한 값이다.\
`nothing()`은 왼쪽 화살표만 성립시킨 채 오른쪽에서 끊긴다.

둘째, **회귀 가드**다.\
이 PR은 empty-value만 건드리지만, 누군가 나중에 Mutiny 분기의 변환 람다를 손보면 왕복 계약이 조용히 깨질 수 있다.\
T2가 그 계약을 테스트로 붙잡아 둔다.

착수 명세에서 "빈 Publisher가 null item으로 완료된다"는 서술은 Mutiny 문서에만 근거한 `[구현 검증]` 이연 항목이었다.\
**T2가 red 확인 회차에 green으로 나오면서 그 이연이 실행으로 해소됐다** - 문서를 믿고 쌓아 올린 것이 아니라 실행 결과 위에 fix를 얹었다는 뜻이다.

> **`[구현 검증]` 이연** — 문서만 읽어서는 참·거짓을 못 가리는 판정을, 실제로 코드를 돌려 볼 때까지 미뤄 두고 표시해 두는 것.\
> 예: "Mutiny 문서에 그렇게 적혀 있다"는 근거는 실행으로 확인하기 전까지 가정으로 남겨 둔다.

## T3~T7. 기존 Mutiny 테스트 5건 - 무회귀 가드 (전후 green)

새 테스트 둘이 empty-value 경로를 맡는 동안, 나머지 경로가 그대로임을 고정하는 쪽은 이미 있던 다섯이다.\
별도로 추가한 것이 아니라 **기존 테스트가 가드 역할을 하도록 배치를 짠 것**이다.

| 테스트 | 지키는 것 | 이 수정과의 관계 |
|---|---|---|
| `defaultAdapterRegistrations` (:281-285) | `Uni`·`Multi` 어댑터가 등록돼 있음 | 등록 자체를 깨뜨리지 않았음 |
| `toUni` (:287-293) | `fromPublisher(Mono.just(1))` -> item 1인 Uni | 비-null 역방향 무영향 |
| `fromUni` (:295-301) | `toPublisher(Uni.item(1))` -> block 결과 1 | **비-null 정방향 무영향 - 핵심 가드** |
| `toMulti` (:317-324) | `Multi` 역방향 | 같은 registrar의 형제 등록 무영향 |
| `fromMulti` (:326-333) | `Multi` 정방향 | 〃 |

`fromUni`가 이 중 핵심이다.\
`fromNullValue`와 **같은 메서드**를 부르는데 소스만 비-null이다.

```java
@Test
void fromUni() {
	Uni<Integer> source = Uni.createFrom().item(1);
	Object target = getAdapter(Uni.class).toPublisher(source);
	assertThat(target).isInstanceOf(Mono.class);
	assertThat(((Mono<Integer>) target).block(FIVE_SECONDS)).isEqualTo(Integer.valueOf(1));
}
```
(ReactiveAdapterRegistryTests.java:295-301)

두 테스트가 한 메서드의 두 분기를 어떻게 나눠 맡는지 보면 이렇다.

```text
                ReactiveAdapter.toPublisher(source)
                              |
              +---------------+---------------+
        source == null                  source != null
              |                               |
              v                               v
     getEmptyValue() 호출              그대로 변환 (L112 직행)
              |                               |
              v                               v
       T1 fromNullValue                 T3 fromUni
       (fix 전 FAIL)                    (fix 전후 PASS)
              |                               |
              v                               v
     "수정이 결함을 고쳤다"          "기존 사용자에게 무영향이다"
```

`toPublisher`의 `if (source == null)` 분기(ReactiveAdapter.java:109)가 false이므로 `getEmptyValue()`는 호출조차 되지 않고 사용자가 준 Uni가 그대로 변환된다.\
즉 이 수정이 관측될 수 있는 유일한 경로가 `source == null` 분기다.\
그래서 `fromUni`가 fix 전후 모두 green이라는 사실이 **"기존 비-null 사용자에게 무영향"의 실행 증거**가 된다.\
두 테스트가 한 메서드의 두 분기를 나눠 맡는 짝이다.

## 실측 요약

실행 결과는 실패 건수뿐 아니라 실패 형태까지 예측과 일치했다.

- **fix 전**: `ReactiveAdapterRegistryTests`의 `Mutiny` 그룹 **7 tests, 1 failed**.\
  `fromNullValue`가 `IllegalStateException: Timeout on blocking read`로 실패했고 나머지 6건은 green.\
  `toUniFromEmptyPublisher`가 fix 전에 green이었다는 점이 명세의 `[구현 검증]` 가정 2를 해소했다.
- **fix 후**: 같은 그룹 **7/7 green**(`fromNullValue` red -> green), 파일 전체 green, `spring-core` 전체 **5,186 tests, 0 failures**, checkstyle EXIT=0.
- **diff 규모**: 2파일 +15/-1.\
  프로덕션 변경은 `ReactiveAdapterRegistry.java` 한 줄뿐이다.

실패 메시지가 단언 실패(`expected: null but was: ...`)가 아니라 **예외**였다는 점을 기록해 둘 만하다.\
이 결함은 "값이 틀린" 것이 아니라 "값이 오지 않는" 것이므로, red의 형태도 값 비교가 아니라 시간 초과로 나타난다.

## 실측 probe - 커밋에 남기지 않은 확인

테스트로 커밋한 것 외에, 별도 프로브 클래스를 만들어 돌려 보고 결과만 취한 확인이 둘 있다.\
커밋에는 없지만 결함 판정과 수정 검증의 근거이므로 기록해 둔다(원본: 세션 scratchpad `Probe.java` / `Probe2.java`).

> **프로브(probe)** — 커밋하지 않고 한 번 돌려 사실만 확인하고 버리는 임시 실행 코드.\
> 예: 빌드된 클래스에 라이브러리를 직접 물려 어댑터를 부르고 결과만 눈으로 확인하는 작은 `main` 하나.

**probe 1 - 결함 확정과 왕복 실증.**\
빌드된 `spring-core` 클래스에 Mutiny 1.10.0 + Reactor 3.8.7을 물려 `ReactiveAdapterRegistry.getSharedInstance()`를 직접 호출했다.

```text
emptyValue = io.smallrye.mutiny.operators.uni.UniNever@...
Mono.from(uniAdapter.toPublisher(null)).block(600ms)                  -> Timeout
uniAdapter.fromPublisher(Mono.empty()) -> Uni, await()                -> null
Mono.from(uniAdapter.toPublisher(Uni.createFrom().nullItem())).block  -> null (완료)
```

세 줄이 각각 결함·역방향 정의·수정안의 대칭성을 실행으로 확인한다.\
테스트 하네스 바깥에서 재현했다는 점이 중요하다 - JUnit 설정이나 어댑터 조회의 문제가 아니라 어댑터 자체의 동작임을 고립시킨다.

> **테스트 하네스(test harness)** — 테스트를 찾아 실행하고 결과를 모아 주는 틀(JUnit 같은 것).\
> 예: 하네스 밖에서 같은 결과가 나오면, 원인이 테스트 설정이 아니라 대상 코드 자체임이 확정된다.

**probe 2 - 형제 대조.**\
같은 환경에서 `Mono`와 `Multi` 어댑터에 같은 호출을 걸었다.

```text
Mono  adapter: toPublisher(null) -> block(500ms)      -> null (완료)
Multi adapter: toPublisher(null) -> blockLast(500ms)  -> null (완료)
Uni   descriptor: isNoValue=false, isDeferred=true
```

같은 호출을 세 어댑터에 건 결과를 나란히 두면 이탈이 하나로 좁혀진다.

```text
       Mono                 Multi                  Uni (수정 전)
+----------------+   +----------------+   +----------------------+
| toPublisher    |   | toPublisher    |   | toPublisher          |
|   (null)       |   |   (null)       |   |   (null)             |
+----------------+   +----------------+   +----------------------+
| block -> null  |   | blockLast      |   | block -> Timeout     |
| (완료)         |   |   -> null (완료)|   | (신호 0 건)          |
+----------------+   +----------------+   +----------------------+
  같은 registrar 안의 형제가 정상이다        -> 설계가 아니라 실수
```

**같은 registrar 안의 `Multi`가 정상이라는 것**이 이 결함을 설계가 아닌 실수로 읽게 하는 근거다.\
그리고 `isDeferred=true`는 `@Scheduled` 리액티브 경로가 이 어댑터를 받아들인다는 뜻이므로(`ScheduledAnnotationReactiveSupport.java:152-155`), 결함의 도달 범위를 넓히는 확인이기도 했다.

> **deferred(지연 타입)** — 구독하기 전에는 아무 일도 시작하지 않는 리액티브 타입.\
> 예: `Uni`는 만들어 두기만 해서는 실행되지 않고, 누군가 구독해야 비로소 동작을 시작한다.
