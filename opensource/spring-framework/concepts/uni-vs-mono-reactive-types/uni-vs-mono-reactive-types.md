# 개념: Uni와 Mono — "빈 값"을 서로 다르게 적는 두 개의 단일 값 타입

> H3(Mutiny `Uni` 어댑터의 empty-value 결함) 작업의 배경 개념 문서.
> 실증 기준: spring-framework-fork `main`, Mutiny 1.10.0(framework-platform 고정판),
> Reactor 3.8.7.

## 한 줄 정의 — 둘 다 "값 하나"지만 없음의 표기법이 다르다

Reactor `Mono`와 SmallRye Mutiny `Uni`는 모두 비동기 단일 값을 나타내지만, **값이 없다는
사실을 서로 다른 자리에 적는다**. Mono는 아이템을 아예 내보내지 않고 완료 신호만 보내
"없음"을 표현하고, Uni는 **`null` 아이템을 하나 내보내며 완료**해 "없음"을 표현한다. 이
표기법 차이가 H3 결함의 무대다 — 두 세계를 잇는 다리에서 "빈 Uni"를 잘못 고른 것이 결함의
전부다.

## 두 타입의 정체

Mono는 Reactive Streams `Publisher`를 **직접 구현한다**. 그래서 Spring 입장에서 Mono는
변환할 것이 없고, 어댑터의 두 함수가 사실상 항등함수다
(`ReactiveAdapterRegistry.java:274-277`):

```java
registry.registerReactiveType(
        ReactiveTypeDescriptor.singleOptionalValue(Mono.class, Mono::empty),
        source -> (Mono<?>) source,
        Mono::from);
```

Uni는 `Publisher`를 구현하지 않는다. Mutiny 자체 구독 모델(`UniSubscriber`)을 쓰고, 결과는
아이템 이벤트 또는 실패 이벤트 **정확히 하나**다. Mutiny 1.10.0 `Uni` 클래스 javadoc이
그렇게 못박는다 — "An item event, forwarding the completion of the action (potentially
`null` if the item does not represent a value, but the action was completed successfully)".
즉 **`null`은 Uni에서 정상적인 성공 아이템**이며, `Uni<T>`가 완료했다는 것이 값이 있다는
뜻은 아니다. 그래서 Uni 어댑터는 진짜 변환 코드를 갖는다(Mutiny 1 분기,
`ReactiveAdapterRegistry.java:401-403`):

```java
registry.registerReactiveType(uniDesc,
        uni -> ((io.smallrye.mutiny.Uni<?>) uni).convert().toPublisher(),
        publisher -> io.smallrye.mutiny.Uni.createFrom().publisher(publisher));
```

## 신호 모델 비교

두 타입이 같은 상황을 각각 어떤 신호로 표현하는지를 나란히 두면 차이가 한눈에 보인다.

| 상황 | Mono | Uni |
|---|---|---|
| 구독 | `onSubscribe(Subscription)` + `request(n)` 백프레셔 | `UniSubscriber.onSubscribe(UniSubscription)`, 요청 개념 없음 |
| 값 있음 | `onNext(v)` 후 `onComplete()` (신호 2개) | `item(v)` (신호 1개) |
| 값 없음 | `onNext` 없이 `onComplete()` | `item(null)` |
| 에러 | `onError(t)` | `failure(t)` |
| 아무 일 없음 | `Mono.never()` | `Uni.createFrom().nothing()` |

핵심은 Mono가 "완료"와 "값"을 **분리된 신호 둘**로 다루는 반면 Uni는 하나의 결과 이벤트에
합쳤다는 점이다. 그 결과 Uni에는 Mono의 `Mono.empty()`에 해당하는 "아이템 없는 완료"라는
상태 자체가 없고, 대응물은 `nullItem()`이다.

## Spring이 두 세계를 잇는 방법

Spring은 모든 리액티브/비동기 타입을 Reactive Streams `Publisher`로 정규화한 뒤 내부 처리를
하고, 필요하면 원래 타입으로 되돌린다. 그 다리가 `ReactiveAdapterRegistry`이고, 다리 한
칸이 `ReactiveAdapter`다. `ReactiveAdapter`는 세 조각으로 이뤄진다 —
`ReactiveTypeDescriptor`(의미론 서술) + `toPublisher`(정규화) + `fromPublisher`(복원)
(`ReactiveAdapter.java:37-41`).

`ReactiveTypeDescriptor`가 서술하는 의미론은 세 축이다. `isMultiValue()`(0..N인가 0..1인가),
`isNoValue()`(값 없이 완료·에러만인가), 그리고 이 문서의 주인공인 `supportsEmpty()`다.
`supportsEmpty()`는 별도 boolean이 아니라 **empty 공급자의 존재 여부**다
(`ReactiveTypeDescriptor.java:91-93`):

```java
public boolean supportsEmpty() {
    return (this.emptySupplier != null);
}
```

그리고 그 공급자가 실제로 쓰이는 자리는 단 한 곳, `toPublisher`가 `null` 소스를 받았을
때다(`ReactiveAdapter.java:107-113`):

```java
public <T> Publisher<T> toPublisher(@Nullable Object source) {
    if (source == null) {
        source = getDescriptor().getEmptyValue();
    }
    return (Publisher<T>) this.toPublisherFunction.apply(source);
}
```

즉 `getEmptyValue()`는 "이 타입에서 **비어 있으면서 완료된** 인스턴스"를 돌려주기로 한
계약이다. 팩토리 이름도 그 계약을 말한다 — `singleOptionalValue(type, emptySupplier)`는
"0..1개를 낼 수 있는 타입"이고(`ReactiveTypeDescriptor.java:148-150`), Uni는 이 팩토리로
등록된다.

## H3 결함 — 타입은 맞는데 신호가 없다

결함의 자리는 Uni descriptor의 empty 공급자 한 줄이다
(`ReactiveAdapterRegistry.java:376-378`):

```java
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
        io.smallrye.mutiny.Uni.class,
        () -> io.smallrye.mutiny.Uni.createFrom().nothing());
```

`nothing()`의 javadoc은 "Creates a `Uni` that will never fire an `item` or `failure`
event"이고 구현은 `UniNever.INSTANCE`를 돌려준다(`UniCreate.java:567-576`, Mutiny 1.10.0
sources). **빈 Uni가 아니라 영원히 아무 신호도 내지 않는 Uni**다.

여기서 강조할 점은 이것이 **타입 문제가 아니라 의미론 문제**라는 것이다. `nothing()`이
돌려주는 것도 어엿한 `Uni`이고, `toPublisherFunction`은 성공적으로 `Publisher`를 만들고,
`ReactorAdapter`는 그것을 `Mono`로 감싼다(`ReactiveAdapterRegistry.java:259-263`). 어느
단계도 예외를 던지지 않는다. 다만 그 `Mono`는 구독해도 `onNext`도 `onComplete`도 `onError`도
받지 못한다. 컴파일도 되고 캐스팅도 되며 그저 **영원히 완료되지 않는다** — silent failure의
교과서적 형태다.

로컬 실증 결과가 그대로다. 빌드된 `spring-core` 클래스에 Mutiny 1.10.0 + Reactor 3.8.7을
물려 어댑터를 직접 호출하면:

```
emptyValue = io.smallrye.mutiny.operators.uni.UniNever@...
Mono.from(uniAdapter.toPublisher(null)).block(600ms) -> Timeout on blocking read
Mono.from(monoAdapter.toPublisher(null)).block(600ms) -> null    (정상 완료)
Flux.from(multiAdapter.toPublisher(null)).blockLast(600ms) -> null (정상 완료)
```

같은 registrar 안의 `Multi`는 `Multi.createFrom().empty()`로 등록돼
있어(`ReactiveAdapterRegistry.java:379-381`) 정상이다. **Uni 한 줄만 어긋났다**는 점이
오타성 실수라는 방증이다.

## 왜 `nullItem()`이 정답인가 — 왕복 대칭

올바른 empty 값은 `Uni.createFrom().nullItem()`이고, 근거는 **`fromPublisher`가 이미 그렇게
행동하고 있다**는 왕복 대칭이다. `fromPublisher`가 쓰는 `UniCreate.publisher()`의 javadoc은
"If the publisher emits the completion signal before having emitted a value, the produced
`Uni` emits a `null` item event"라고 명시한다(`UniCreate.java:265-282`). 반대 방향인
`Uni -> Publisher` 변환도 짝이 맞는다 — Mutiny의 `ToPublisher` 주석이 "If the uni item is
`null` the stream is completed"라고 적는다(`ToPublisher.java:17-18`).

두 방향을 붙이면 표는 이렇게 닫힌다.

| 방향 | 입력 | 출력 | 실증 |
|---|---|---|---|
| `fromPublisher` | `Mono.empty()` | `Uni`, await 결과 `null` | 확인 |
| `toPublisher` | `Uni.createFrom().nullItem()` | `Mono`, block 결과 `null`(완료) | 확인 |
| `toPublisher` | `Uni.createFrom().nothing()` (현행) | `Mono`, 영원히 미완료 | 확인 |

즉 `nullItem()`으로 고치면 `toPublisher`와 `fromPublisher`가 서로의 역함수가 되고,
`nothing()`은 그 대칭을 깬 채로 한쪽만 블랙홀이 된다.

## 실무 감각 — 컨트롤러가 `null`을 반환하면

WebFlux 컨트롤러의 반환값 처리는 선언 타입으로 어댑터를 찾고 값을 `toPublisher`에 넘긴다
(`AbstractMessageWriterResultHandler.java:174-180`). 반환값이 `null`이어도 어댑터 조회는
선언 타입(`Uni`/`Mono`)으로 성공하므로(`ReactiveAdapterRegistry.java:195-209`), 그대로
`toPublisher(null)` 경로에 들어간다. 결과는 선언 타입에 따라 갈린다.

| 컨트롤러 반환 | 내부 경로 | 현재 동작 |
|---|---|---|
| `Mono<T>` 자리에 `null` | `Mono.empty()` -> 즉시 완료 | 빈 본문으로 응답 완료 |
| `Uni<T>` 자리에 `null` | `UniNever` -> 신호 없음 | 응답이 끝나지 않음(요청 행) |
| `Multi<T>` 자리에 `null` | `EmptyMulti` -> 즉시 완료 | 빈 본문으로 응답 완료 |

주의할 것은 `Uni<T>` 메서드가 정상적으로 `Uni`를 반환하는 흔한 경우는 이 경로를 타지 않아
멀쩡하다는 점이다. 문제는 **참조 자체가 `null`인 경로** — 조건 분기에서 빈손을 `null`로
표현했거나, `@ModelAttribute`/`@RequestBody` 계열의 빈 값 경로처럼 프레임워크가 값 없음을
`null`로 전달하는 자리다. 그래서 증상은 항상 나지 않고 특정 분기에서만 요청이 행으로 남는다.

## 정리

- Mono의 "없음" = 아이템 없이 `onComplete`. Uni의 "없음" = `null` 아이템으로 완료. 두 타입은
  단일 값이라는 점만 같고 없음의 표기가 다르다.
- Spring은 `ReactiveTypeDescriptor`로 타입의 의미론을 서술하고, 그중 `emptySupplier`는
  "`toPublisher(null)`일 때 대신 쓸 빈 인스턴스"라는 좁고 분명한 계약을 갖는다.
- H3 결함은 그 계약에 `nothing()`(무신호)을 넣은 것이다. 타입 변환은 전부 성공하고 예외도
  없으며 다만 완료 신호가 오지 않는다.
- `nullItem()`이 `fromPublisher`와 왕복 대칭을 이루는 유일한 값이고, 같은 registrar의
  `Multi`가 이미 `empty()`로 올바르게 등록돼 있다.

## 관련

- `ReactiveAdapterRegistry.java:370-409` — MutinyRegistrar 전체(Mutiny 1/2 분기 포함)
- `ReactiveTypeDescriptor.java:139-178` — descriptor 팩토리 다섯 종
