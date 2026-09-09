# PR #37259 - Complete empty Uni instances from the Mutiny reactive adapter

## 0. 정향

이 문서는 `spring-core`의 `ReactiveAdapterRegistry`가 SmallRye Mutiny `Uni`의
**빈 값 공급자를 "영원히 아무 신호도 내지 않는 Uni"로 등록해 두었던** 결함의
해설이다. 결함도 한 줄이고 수정도 한 줄이지만, 그 한 줄이 만드는 증상은 예외가
아니라 **정지**다 - 스택트레이스도 로그도 없이 응답이 끝나지 않는다. 다 읽으면
"왜 빈 값이 완료되어야 하는가", "`nothing()`과 `nullItem()`이 각각 무엇을 만드는가",
"왜 이 결함이 4년 동안 아무에게도 안 보였는가"를 설명할 수 있어야 한다.

상태: **리뷰 대기**(2026-09-09 제출, 커밋 `c57215898bb`).

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md) -
[이해 게이트 기록](gates.md).
개념 문서: [Uni와 Mono - 빈 값을 서로 다르게 적는 두 단일 값 타입](../../concepts/uni-vs-mono-reactive-types/uni-vs-mono-reactive-types.md).

## 1. 배경 - 모든 비동기 타입을 Publisher 하나로 모으는 다리

Spring은 핸들러가 무엇을 반환하든 내부에서는 Reactive Streams `Publisher` 하나로
다룬다. `Mono`, `Flux`, RxJava `Flowable`, Kotlin `Deferred`, Mutiny `Uni`가 전부
같은 파이프로 들어와야 인코더·뷰·메시지 컨버터가 타입마다 분기하지 않는다. 그
정규화를 담당하는 것이 `ReactiveAdapterRegistry`이고, 타입 하나당 어댑터 하나가
등록된다.

어댑터는 세 조각이다 - 타입의 의미론을 서술하는 `ReactiveTypeDescriptor`, 정규화
함수 `toPublisher`, 복원 함수 `fromPublisher`(ReactiveAdapter.java:37-41). 이 문서의
주인공은 첫 조각 안의 작은 필드 하나, `emptySupplier`다.

```java
public boolean supportsEmpty() {
	return (this.emptySupplier != null);
}

public Object getEmptyValue() {
	Assert.state(this.emptySupplier != null, "Empty values not supported");
	Object emptyValue = this.emptySupplier.get();
	Assert.notNull(emptyValue, "Invalid null return value from emptySupplier");
	return emptyValue;
}
```
(ReactiveTypeDescriptor.java:91-104)

`supportsEmpty()`는 별도 boolean이 아니라 **공급자의 존재 여부**다. 즉 공급자를
등록하는 순간 그 타입은 "값 없이 완료될 수 있다"고 프레임워크에 선언한 것이 된다.
그리고 그 공급자가 실제로 호출되는 자리는 프로덕션 코드 전체에서 정확히 한 곳,
`toPublisher`가 `null` 소스를 받았을 때다.

```java
public <T> Publisher<T> toPublisher(@Nullable Object source) {
	if (source == null) {
		source = getDescriptor().getEmptyValue();
	}
	return (Publisher<T>) this.toPublisherFunction.apply(source);
}
```
(ReactiveAdapter.java:107-113)

**`getEmptyValue()`의 계약은 좁고 분명하다: "이 타입에서 비어 있으면서 완료된
인스턴스"를 내놓는 것.** 완료되지 않는 인스턴스를 내놓으면 계약 위반인데, 그것을
검사하는 장치는 어디에도 없다. `Assert.notNull`이 확인하는 것은 공급자가 null을
돌려주지 않았다는 사실뿐이고, 돌려준 그 객체가 실제로 완료하는지는 아무도 묻지
않는다.

## 2. 수정 전 동작 - 열세 등록 중 하나만 완료하지 않는다

레지스트리에 등록된 타입들은 각자 자기 세계의 "빈 값"을 하나씩 내놓는다. 고정 축으로
줄 세우면 수정 전 이탈이 한 눈에 보인다.

| 등록 | empty 공급자 | 구독했을 때 |
|---|---|---|
| Reactor `Mono` (:275) | `Mono::empty` | 즉시 `onComplete` |
| Reactor `Flux` (:280) | `Flux::empty` | 즉시 `onComplete` |
| `Publisher` (:285) | `Flux::empty` | 즉시 `onComplete` |
| `CompletionStage` (:290) | `EmptyCompletableFuture::new` (생성자가 `complete(null)`) | 이미 완료된 future |
| `Flow.Publisher` (:295) | `EMPTY_FLOW`(`Flux.empty()` 브리지) | 즉시 완료 |
| RxJava `Flowable` / `Observable` (:316, :323) | `empty()` | 즉시 완료 |
| RxJava `Maybe` (:336) | `Maybe::empty` | 즉시 완료 |
| RxJava `Completable` (:343) | `Completable::complete` | 즉시 완료 |
| Kotlin `Deferred` (:355-356) | `CompletableDeferred(null)` | 이미 완료 |
| Kotlin `Flow` (:361) | `FlowKt::emptyFlow` | 즉시 완료 |
| Mutiny `Multi` (:379-381) | `Multi.createFrom().empty()` | 즉시 완료 |
| **Mutiny `Uni`** (수정 전 :376-378) | **`Uni.createFrom().nothing()`** | **영원히 무신호** |

RxJava `Single`만 이 표에 없는데, 그것은 이탈이 아니라 정직한 선언이다 -
`singleRequiredValue`로 등록돼 공급자가 아예 없고(`ReactiveTypeDescriptor.java:156-158`),
따라서 `supportsEmpty()`가 false다. "빈 값을 못 만든다"고 말한 타입이다.

Mutiny `Uni`는 반대다. `singleOptionalValue`로 등록해 "빈 값을 만들 수 있다"고
선언해 놓고, 그 빈 값이 `nothing()`이었다.

```java
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
		io.smallrye.mutiny.Uni.class,
		() -> io.smallrye.mutiny.Uni.createFrom().nothing());
```
(수정 전 ReactiveAdapterRegistry.java:376-378)

`nothing()`의 javadoc은 "Creates a `Uni` that will never fire an `item` or `failure`
event"이고, 구현은 싱글턴 `UniNever.INSTANCE`를 돌려준다(Mutiny 1.10.0
`UniCreate.java:567-577`). 구독하면 `onSubscribe`만 한 번 하고 그걸로 끝이다.
**빈 Uni가 아니라 아무 일도 일어나지 않는 Uni**다. 같은 registrar 안의 `Multi`가
바로 아래 줄에서 `empty()`로 올바르게 등록돼 있다는 점이, 이것이 설계가 아니라
손이 미끄러진 자리라는 방증이다.

## 3. 문제 - 예외가 아니라 정지

발동 조건은 하나다: **`Uni`로 선언된 자리에 값이 `null`로 들어와 프레임워크가
`toPublisher(null)`을 부르는 경우.** 그러면 `getEmptyValue()`가 `UniNever`를 내놓고,
그것이 변환된 `Publisher`는 구독자에게 `onNext`도 `onComplete`도 `onError`도 주지
않는다.

### 증상 - 같은 코드를 Mono로 선언하면 되고 Uni로 선언하면 멈춘다

WebFlux 컨트롤러가 반환값 처리에 쓰는 길이 그 경로다. 반환값이 `null`이어도 어댑터
조회는 **선언 타입**으로 이뤄지므로(ReactiveAdapterRegistry.java:195-209) 조회는
성공하고, 그대로 `toPublisher(null)`에 들어간다(AbstractMessageWriterResultHandler.java:174-180).

| 컨트롤러가 반환한 것 | 내부에서 대체되는 빈 값 | 결과 |
|---|---|---|
| `Mono<String>` 자리에 `null` | `Mono.empty()` | 즉시 완료, 빈 본문으로 응답 종료 |
| `Multi<String>` 자리에 `null` | `Multi.createFrom().empty()` | 즉시 완료, 빈 본문으로 응답 종료 |
| `Uni<String>` 자리에 `null` | `UniNever.INSTANCE` | **신호 없음 - 응답이 쓰이지 않고 요청이 행** |

세 줄이 전부 같은 컨트롤러 코드이고 다른 것은 반환 타입 선언 하나뿐이다. 그런데
Mutiny를 고른 쪽만 응답이 끝나지 않는다.

이 결함의 성격은 여기서 정해진다. **던져지는 예외가 없다.** 타입 변환은 전부
성공하고, `ReactorAdapter`는 그 Publisher를 정상적으로 `Mono`로 감싸며
(ReactiveAdapterRegistry.java:259-263), 구독도 정상적으로 성립한다. 다만 신호가 오지
않는다. 그래서 로그에 남는 것도 없고, 관측되는 것은 클라이언트나 서버 타임아웃뿐이다
- 원인을 어댑터 등록 한 줄로 되짚기가 대단히 어렵다.

이 결함이 닿는 자리는 WebFlux 본문 쓰기 하나가 아니다. 프로덕션 코드의
`ReactiveAdapter.toPublisher(...)` 호출 **마흔두 곳**을 전수로 훑어 `null`이 실제로
들어갈 수 있는 자리를 세면 **열두 곳**이고, WebFlux뿐 아니라 `@Transactional`·
`@Cacheable`·`@Scheduled`·RSocket까지 걸친다. 도달하는 열두 곳과 도달하지 않는
서른 곳의 판별 근거는 [structure.md](structure.md) 3절에 표로 있다.

### 왜 지금까지 안 보였나

세 겹의 조건이 이 결함을 덮고 있었다.

1. **정상 경로가 이 줄을 지나지 않는다.** `Uni<T>`를 반환하는 메서드가 실제로
   `Uni`를 반환하는 흔한 경우는 `source != null`이라 공급자가 호출조차 되지 않는다
   (ReactiveAdapter.java:109). 결함이 발화하려면 참조 자체가 `null`이어야 한다.
2. **Mutiny 어댑터 자체가 틈새다.** 2021년 도입(`1dc128361f8`, 5.3.10) 이후 Spring
   MVC/WebFlux에서 Mutiny를 쓰는 사용자는 Reactor·RxJava 사용자보다 훨씬 적다.
   Quarkus 세계의 타입을 Spring에서 쓰는 조합이다.
3. **증상이 예외가 아니라 타임아웃이다.** 행이 걸린 요청 하나를 보고 "리액티브
   어댑터의 empty-value 등록"을 의심하는 사람은 없다. 무한 대기는 네트워크나 DB나
   스레드 풀부터 의심하게 만든다.

기원도 확인했다. 최초 도입 PR #27331(hantsy, 2021-08)의 리뷰 코멘트에 empty-value
선택에 대한 논의가 없다 - 머지 인사뿐이다. 즉 `nothing()`은 검토를 거쳐 채택된
값이 아니라 검토되지 않은 채 들어온 초기 선택이었다.

## 4. 수정 해설 - 왕복이 닫히는 한 줄

수정은 공급자를 바꾸는 것뿐이다.

```java
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
		io.smallrye.mutiny.Uni.class,
		() -> io.smallrye.mutiny.Uni.createFrom().nullItem());
```
(ReactiveAdapterRegistry.java:376-378)

이 값이 정답인 근거는 취향이 아니라 **이 어댑터 자신의 반대 방향**에 있다.
같은 registrar가 등록한 `fromPublisher`는 빈 Publisher를 "null item으로 완료되는
Uni"로 바꾼다(Mutiny 1 분기 :403, Mutiny 2 분기 :392-393 동형). Mutiny 문서가
그렇게 정의하고 있고 - "If the publisher emits the completion signal before having
emitted a value, the produced `Uni` emits a `null` item event"(`UniCreate.java:265-287`)
- 소스를 열어 보면 `UniCreateFromPublisher`의 `onComplete`가 `subscriber.onItem(null)`을
부른다(`UniCreateFromPublisher.java:85-91`).

```
빈 Publisher --fromPublisher(:403)--> Uni(null item으로 즉시 완료)
Uni(null item) --toPublisher(:402)--> 아이템 없이 onComplete = 빈 Publisher
```

즉 **"빈 것"의 Uni측 표현은 이 어댑터 안에서 이미 null item으로 정해져 있었다.**
빈 값을 만들어야 할 때 쓸 Uni도 그것과 같아야 왕복이 닫힌다. `nothing()`은 왕복의
절반만 성립시킨다 - 빈 Publisher를 Uni로 바꿀 수는 있는데, 그 어댑터가 스스로 만든
"빈 Uni"는 다시 Publisher로 돌아오지 못한다.

### `nothing()`과 `nullItem()`이 각각 만드는 것

두 팩토리 메서드의 차이는 "빈 값이냐 아니냐"가 아니라 **신호를 보내느냐 마느냐**다.

| | `nothing()` | `nullItem()` |
|---|---|---|
| 돌려주는 객체 | `UniNever.INSTANCE` (싱글턴) | `UNI_OF_NULL` = `UniCreateFromKnownItem<>(null)` (싱글턴) |
| 구독 시 동작 | `onSubscribe(DONE)` 한 번, 그 뒤 아무것도 없음 | `onSubscribe` 후 곧바로 `onItem(null)` |
| item / failure / completion | 0회 / 0회 / 0회 | item 1회(값은 null) |
| Publisher로 변환하면 | 구독자에게 신호 0건 | `onNext` 없이 `onComplete` 1회 |

**`nullItem()`이 `null`을 흘려보내는 것이 아니라는 점이 중요하다.** Reactive Streams는
`onNext(null)`을 금지하므로, Mutiny의 Uni -> Publisher 변환은 null item을 "아이템
방출 없이 `onComplete`"로 매핑한다(`UniToMultiPublisher.java:90-96`의
`if (item != null) downstream.onNext(item); downstream.onComplete();`). 그리고
`Mono.block()`은 아이템 없는 정상 완료를 받으면 `null`을 반환한다. **null item Uni,
빈 Publisher, `block()` 결과 null - 이 셋은 같은 사태의 세 표기다.** 두 객체의
내부 구조는 [analysis.md](analysis.md) 2.5절에 더 있다.

### Mutiny 1과 2를 한 줄로 덮는 이유

`MutinyRegistrar`는 `UniConvert.toPublisher()`의 반환 타입이 `Flow.Publisher`인지를
보고 Mutiny 2 분기와 Mutiny 1 분기로 갈린다(:383-407). 두 분기는 변환 람다만 다르고
descriptor는 위에서 만든 `uniDesc` **하나를 공유**한다. 그래서 공급자 한 줄이 두
경로를 다 커버한다. 이 저장소가 고정한 버전은 Mutiny 1.10.0이므로
(`framework-platform.gradle:56`) 실제로 실행되고 테스트되는 것은 `else` 분기 쪽이다.

### 검토했으나 기각한 대안

`ReactiveTypeDescriptor` 쪽에서 공급자가 내놓은 값이 실제로 완료되는지 검증하는
방안은 성립하지 않는다. 완료 여부는 구독해 봐야 알 수 있고, `getEmptyValue()`는
어댑테이션 경로 한복판에서 불리므로 그 자리에서 구독해 볼 수 없다. 이 계약은
런타임 검사가 아니라 **등록하는 쪽이 지키는 관례**이고, 결함은 관례 위반이지
관례의 결함이 아니다 - 형제 열두 종이 이미 그 관례를 지키고 있다.

### 호환성

동작이 바뀌는 경로는 `Uni` 어댑터의 `toPublisher(null)` 하나뿐이고, 그 경로의
기존 동작은 "영원히 완료되지 않음"이다. 거기에 의존하는 코드는 상정하기 어렵고,
의존했다면 그것이 곧 행 버그다. 비-null `Uni`를 넘기는 모든 기존 사용자는
`ReactiveAdapter.java:109`의 분기를 통째로 건너뛰므로 정의상 무영향이다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다. `ReactiveAdapterRegistryTests`의
`Mutiny` 중첩 클래스에 2건을 추가했다 - `fromNullValue`가 결함 재현(red)이고,
`toUniFromEmptyPublisher`는 fix 전후 모두 green인 **회귀 가드 겸 왕복 대칭의
기준점**이다. fix 전 실측은 Mutiny 그룹 **7 tests, 1 failed**이고, 실패 형태가
`IllegalStateException: Timeout on blocking read`였다는 점이 "이 결함은 값이 틀리는
것이 아니라 신호가 없는 것"을 그대로 보여 준다. fix 후 Mutiny 그룹 7/7 green,
`spring-core` 전체 **5,186 tests, 0 failures**, checkstyle EXIT=0. 상세는
[tests.md](tests.md).

커밋에 남기지 않은 실행 프로브도 두 번 돌렸다. 빌드된 `spring-core` 클래스에
Mutiny 1.10.0 + Reactor 3.8.7을 물려 어댑터를 직접 호출해 `getEmptyValue()`가
`UniNever`임과 `block(600ms)` 타임아웃을 확인했고, 같은 프로브로 `Mono`·`Multi`는
정상 완료함을 대조했다.

stakes는 **낮음~중간**으로 판정했다(변경은 한 줄이고 blast radius가
`toPublisher(null)` 한 분기지만, 대상이 리액티브 타입의 공개 계약이다). 그래서
리뷰는 셀프체크 + diff self-review였고 듀얼 리뷰는 돌리지 않았다 - 이 폴더에
`review.md`가 없는 것은 누락이 아니라 그 판정의 결과다. 셀프 리뷰에서 확인한 것:
diff 2파일 +15/-1, `createFrom().nothing()`의 저장소 내 다른 사용처 0건, 무신호
empty에 의존하는 테스트 없음(전 스위트 green이 그 증명).

## 6. 교훈

이 한 줄짜리 결함이 남긴 것은 선언과 실물의 어긋남, 침묵하는 실패, 왕복 대칭이라는
판정 기준, 그리고 형제 대조라는 탐지법 넷이다.

1. **"할 수 있다"는 선언과 "실제로 하는 것"은 따로 검사된다.**
   `singleOptionalValue`로 등록하는 순간 `supportsEmpty()`는 true가 되고, 그것을
   신뢰하는 코드가 프레임워크 곳곳에 있다. 그런데 그 신뢰의 대상인 empty 인스턴스가
   계약을 지키는지는 아무도 확인하지 않았다. **불변식을 선언하는 자리와 그것을
   충족하는 자리가 떨어져 있으면 그 사이는 관례로만 이어진다.**
2. **가장 나쁜 실패는 아무 일도 일어나지 않는 실패다.** 예외는 스택트레이스를
   남기고 잘못된 값은 단언에 걸리지만, 무신호는 흔적이 없다. 이 결함의 관측 가능한
   유일한 형태가 타임아웃이었고, 그래서 4년 동안 아무도 보고하지 않았다. 리액티브
   코드를 읽을 때 "이 구독자에게 신호가 몇 개 오는가"를 세는 습관이 곧 이런 결함의
   탐지기다.
3. **왕복 대칭이 "무엇이 옳은 값인가"의 판정 기준이 된다.** `nullItem()`을 고른
   근거는 Mutiny 문서를 읽어서가 아니라 이 어댑터의 `fromPublisher`가 이미 그렇게
   행동하고 있어서다. 같은 객체가 양방향 변환을 다 갖고 있다면, 한 방향이 정한
   표현이 다른 방향의 답을 강제한다.
4. **탐지법은 논리 추적이 아니라 형제 대조였다.** 등록 열세 개를 나란히 놓고 "빈
   값이 완료되는가"라는 한 축으로 줄 세우면 이탈 하나가 즉시 보인다. #37235의
   setter 열 개 대조와 정확히 같은 방법이고, 이 방법이 두 번 다 통했다는 것이
   기억할 부분이다.
