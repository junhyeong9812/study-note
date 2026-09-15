# PR #37259 - 착수 분석: Mutiny Uni의 empty-value가 완료하지 않는다

> 원본: `docs/plans/2026-09-09/h3-mutiny-uni-empty-hang/analysis.md`(착수 전 작성).
> 학습 문서로 옮기면서 작업 진행용 절을 덜어내고, 수정이 적용된 현재 시점에 맞춰
> 시제를 정리했으며, `[구현 검증]`으로 이연했던 항목을 실측 결과로 승격하고
> 2.5절(두 팩토리가 만드는 객체와 신호)을 새로 붙였다. 결론은 PR #37259로 반영됐다
> (커밋 `c57215898bb`).
>
> **좌표 주의**: 결함 줄은 `ReactiveAdapterRegistry.java` L376-378이고, 수정이 한 줄
> 치환이라 **수정 전후 줄 번호가 같다**. 다른 파일의 좌표도 같은 커밋 기준이다.
> Mutiny 쪽 좌표는 **Mutiny 1.10.0 sources jar** 안의 파일이며 이 저장소에는 없다.
> 분기도와 전수 판별은 [structure.md](structure.md), 문제와 수정 요약은
> [README.md](README.md), 테스트는 [tests.md](tests.md).

## 0. 결론 먼저

`ReactiveAdapterRegistry`에서 빈 값을 선언한 등록 열세 개 중 Mutiny `Uni` 하나만 공급자가 "완료되지 않는 인스턴스"를 내놓았다(L376-378).\
`Uni.createFrom().nothing()`은 빈 Uni가 아니라 `UniNever.INSTANCE` - 구독해도 item·failure·completion이 **한 번도** 오지 않는 Uni다.

> **착수 분석(analysis)** — 코드를 고치기 전에 실파일을 읽어 결함의 위치·경로·영향 범위를 확정해 두는 문서.\
> 예: 여기서 호출 42곳을 먼저 세어 뒀기 때문에 "영향권 12곳"을 추정이 아니라 사실로 적을 수 있었다.

```java
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
		io.smallrye.mutiny.Uni.class,
		() -> io.smallrye.mutiny.Uni.createFrom().nothing());   // 형제 열두 개는 전부 즉시 완료
```

`ReactiveAdapter.toPublisher`가 `null` 소스를 받으면 이 공급자로 대체하므로(L109-110), `Uni<T>`로 선언된 자리에 `null`이 들어온 모든 경로에서 **완료 대신 무한 대기**가 나온다.\
예외도 로그도 없고 관측되는 것은 타임아웃뿐이다.\
수정은 공급자를 `nullItem()`으로 바꾸는 한 줄이고, 그 값이 정답인 근거는 이 어댑터 자신의 역방향(`fromPublisher`)이 이미 "빈 Publisher = null item Uni"로 정의돼 있다는 왕복 대칭이다.

> **왕복 대칭(round-trip symmetry)** — 한 방향으로 변환했다가 반대로 되돌리면 처음 것과 같아지는 성질.\
> 예: 빈 Publisher를 Uni로 바꿨다가 다시 Publisher로 되돌리면 다시 빈 Publisher가 되어야 한다.

## 1. 무대 - 객체와 역할

결함은 등록에서 구독까지 이어지는 사슬의 한가운데, 타입의 의미론을 서술하는 작은 값 객체 안에 있다.\
각 층이 무엇을 맡는지부터 편다.

```text
 등록 (레지스트리 생성 시 1회)
   ReactiveAdapterRegistry 생성자             spring-core/core/ReactiveAdapterRegistry.java
   |  MUTINY_PRESENT 이면 new MutinyRegistrar().registerAdapters(this)   :82, :115-117
   v
 MutinyRegistrar                                                        :370-409
   |  uniDesc   = singleOptionalValue(Uni.class, () -> ...nullItem())    :376-378  <- 이번 무대
   |  multiDesc = multiValue(Multi.class, () -> ...empty())              :379-381
   |  UniConvert.toPublisher() 의 반환 타입으로 Mutiny 2 / 1 분기          :383
   |    Mutiny 2 (Flow.Publisher 기반)  : 리플렉션 등록                    :384-397
   |    Mutiny 1 (Reactive Streams 기반): 직접 등록 <- 1.10.0 이라 활성    :399-407
   |      toPublisher   람다 = uni.convert().toPublisher()               :402
   |      fromPublisher 람다 = Uni.createFrom().publisher(publisher)     :403
   |  두 분기가 uniDesc "하나"를 공유 -> 공급자 한 줄이 양쪽을 덮는다
   v
 ReactiveTypeDescriptor (의미론 서술)        spring-core/core/ReactiveTypeDescriptor.java
   |  emptySupplier 필드                                                 :40
   |  supportsEmpty() = (emptySupplier != null)                          :91-93
   |  getEmptyValue() = emptySupplier.get() + notNull 검사                :99-104
   |       반환된 객체가 실제로 완료하는지는 검사하지 않는다
   |  팩토리 5종 (multiValue / singleOptionalValue / singleRequiredValue /
   |             noValue / nonDeferredAsyncValue)                        :139-178
   v
 ReactiveAdapter (다리 한 칸)                 spring-core/core/ReactiveAdapter.java
   |  descriptor + toPublisherFunction + fromPublisherFunction           :37-41
   |  toPublisher(source): source == null 이면 getEmptyValue() 로 대체    :108-113
   |       getEmptyValue() 의 프로덕션 유일 호출처가 이 L110 이다
   |  fromPublisher(publisher): fromPublisherFunction 만 호출 - 공급자 무관 :120-122
   v
 ReactorAdapter (Reactor 있을 때의 하위 타입)  ReactiveAdapterRegistry     :250-264
   |  결과를 isMultiValue() 에 따라 Flux/Mono 로 감쌈                      :260-263
   |    -> Uni 는 단일 값이므로 Mono.from(...) 이 씌워진다
   v
 소비자 (프로덕션 42곳이 toPublisher 를 부르고, 그중 12곳이 null 을 넘길 수 있다)
   WebFlux 본문 쓰기 / ResponseEntity / SSE / @Transactional /
   @Cacheable / @Scheduled / RSocket 인코딩            <- 전수 판별은 structure.md 3절
```

## 2. 핵심 이름표

이 결함을 읽을 때 헷갈리는 것은 "빈 값"이라는 말이 **선언**과 **인스턴스** 두 얼굴을 갖는다는 점이다.\
아래 표는 각 이름표가 둘 중 어느 쪽인지를 명시한다.

> **선언과 인스턴스** — "할 수 있다"고 말한 것과 "실제로 내놓는 물건"을 가리키는 두 층.\
> 예: `supportsEmpty()`가 선언이고, `getEmptyValue()`가 돌려주는 `UniNever` 객체가 인스턴스다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `emptySupplier` (ReactiveTypeDescriptor:40) | 빈 인스턴스를 만드는 `Supplier<?>`. null이면 "빈 값 미지원" | 이 필드에 들어간 람다가 결함의 전부다 |
| `supportsEmpty()` (:91-93) | **선언** - 공급자의 존재 여부를 boolean으로 노출 | 수정 전에도 true였다. 선언은 참인데 인스턴스가 계약을 어겼다 |
| `getEmptyValue()` (:99-104) | **인스턴스** - 공급자를 실행해 빈 값을 얻는다 | `Assert.notNull`은 "null이 아님"만 본다. 완료 여부는 안 본다 |
| `singleOptionalValue(type, supplier)` (:148-150) | 0..1개를 낼 수 있는 타입의 팩토리. 공급자 필수 | Uni가 이것으로 등록됐다 = "빈 값을 만들 수 있다"는 선언 |
| `singleRequiredValue(type)` (:156-158) | 반드시 1개를 내야 하는 타입. 공급자 없음 | RxJava `Single`이 이것 - **못 만든다고 정직하게 선언한 예** |
| `ReactiveAdapter.toPublisher` L109-110 | `source == null`이면 empty-value로 대체 | 공급자가 읽히는 **유일한 분기**. 비-null 경로는 무영향 |
| `ReactiveAdapter.fromPublisher` L120-122 | `fromPublisherFunction`만 호출 | 공급자와 무관. 그래서 왕복 대칭의 **기준점**이 될 수 있다 |
| `Uni.createFrom().nothing()` | `UniNever.INSTANCE` 반환 (UniCreate.java:567-577) | 수정 전 공급자. 신호를 하나도 보내지 않는다 |
| `Uni.createFrom().nullItem()` | `UNI_OF_NULL` 반환 (UniCreate.java:357-367) | 수정 후 공급자. null을 item으로 갖고 즉시 완료 |
| `Uni.createFrom().publisher(p)` | 등록된 `fromPublisher` 람다의 본체(:403) | 빈 스트림을 null item Uni로 만든다 - 왕복의 반대편 |
| `UniToMultiPublisher` (Mutiny) | Uni -> Publisher 변환의 실체 | null item을 "onNext 없이 onComplete"로 매핑한다 |
| `ReactorAdapter` (:250-264) | 결과를 Flux/Mono로 감싸는 하위 타입 | 테스트의 `isInstanceOf(Mono.class)`가 통과하는 이유 |

이 표에서 결함이 한 줄로 보인다.\
**`supportsEmpty()`라는 선언은 열세 등록에서 전부 참이었지만, 그 선언을 뒷받침하는 인스턴스가 계약을 지키는지는 아무도 검사하지 않는다.**\
계약을 강제하는 장치는 등록하는 사람의 손뿐이다.

검사가 무엇을 보고 무엇을 안 보는지 한 장으로 세우면 이렇다.

```text
  emptySupplier.get() 이 돌려준 객체
              |
              v
  Assert.notNull(emptyValue)          <- 여기까지만 검사한다
              |
      통과 (UniNever 도 null 이 아니다)
              |
              v
  이 객체가 구독하면 완료하는가?       <- 아무도 묻지 않는다
              |
        +-----+-----+
        |           |
   형제 12 종      Uni (수정 전)
   완료한다        완료하지 않는다
```

-> 검사의 경계가 "null 이 아니다"에서 멈추기 때문에, 계약 위반이 등록된 채로 통과한다.

## 2.5. `nothing()`과 `nullItem()`이 각각 만드는 객체와 신호

두 팩토리 메서드는 이름이 비슷해 보이지만 만드는 것이 전혀 다르다.\
Mutiny 1.10.0 sources를 열어 나란히 놓으면 차이가 코드 다섯 줄로 드러난다.

> **팩토리 메서드(factory method)** — `new` 대신 불러서 인스턴스를 얻는 정적 메서드.\
> 예: `Uni.createFrom().nothing()`과 `.nullItem()`은 둘 다 팩토리지만 전혀 다른 객체를 돌려준다.

### `nothing()` - 신호를 보내지 않기로 한 싱글턴

```java
/**
 * Creates a {@link Uni} that will never fire an {@code item} or {@code failure} event.
 */
public <T> Uni<T> nothing() {
    return (Uni<T>) UniNever.INSTANCE;
}
```
(UniCreate.java:567-577)

```java
public class UniNever<T> extends AbstractUni<T> {
    public static final UniNever<Object> INSTANCE = new UniNever<>();

    @Override
    public void subscribe(UniSubscriber<? super T> subscriber) {
        subscriber.onSubscribe(DONE);
    }
}
```
(UniNever.java:8-19)

구독자에게 하는 일이 `onSubscribe(DONE)` **한 줄뿐**이다.\
`DONE`은 `EmptyUniSubscription`의 공유 인스턴스이고 `cancel()`이 no-op이다(EmptyUniSubscription.java:24, :43-46).\
구독은 성립하고 취소도 받아 주지만, 그 뒤로 `onItem`도 `onFailure`도 영원히 오지 않는다.\
담을 상태가 없어서 인스턴스 하나를 전역에서 공유한다 - **아무 일도 하지 않는 객체이므로 하나면 충분한 것**이다.

> **no-op(무동작)** — 불러도 아무 일도 하지 않는 구현.\
> 예: `UniNever`의 구독을 취소해도 멈출 일이 없으므로 `cancel()`은 아무 일도 하지 않는다.

Mutiny에서 이 값의 정당한 용도는 "결코 끝나지 않는 스트림"을 표현할 때다.\
Reactor의 `Mono.never()`에 대응하고, 테스트에서 타임아웃을 만들거나 다른 조건이 만족될 때까지 합성할 때 쓴다.\
**"빈 값"과는 아무 상관이 없는 값**이다.

### `nullItem()` - null을 item으로 갖고 즉시 완료하는 싱글턴

```java
private static final Uni UNI_OF_NULL = Uni.createFrom().item((Object) null);   // :37

/**
 * Creates a new {@link Uni} that completes with a {@code null} item.
 */
public <T> Uni<T> nullItem() {
    return UNI_OF_NULL;
}
```
(UniCreate.java:37, :357-367)

`item((Object) null)`이 만드는 것은 `UniCreateFromKnownItem<>(null)`이다(:334-345).

```java
public class UniCreateFromKnownItem<T> extends AbstractUni<T> {
    private final T item;

    @Override
    public void subscribe(UniSubscriber<? super T> subscriber) {
        new KnownItemSubscription(subscriber).forward();
    }

    private void forward() {
        subscriber.onSubscribe(this);
        if (!cancelled) {
            subscriber.onItem(item);      // item == null
        }
    }
}
```
(UniCreateFromKnownItem.java:13-46, 발췌)

`onSubscribe` 직후 곧바로 `onItem(null)`을 부른다.\
**Mutiny에서 `null` item은 오류가 아니라 정상적인 성공 결과다** - `Uni` javadoc이 "potentially `null` if the item does not represent a value, but the action was completed successfully"라고 못박는다.\
이것 역시 담을 상태가 없어(item이 항상 null) 싱글턴 하나를 공유한다.

두 객체가 구독자에게 하는 일을 나란히 놓으면 이렇다.

```text
        UniNever.INSTANCE                 UNI_OF_NULL
+---------------------------+   +---------------------------+
| subscribe(sub) {          |   | forward() {               |
|   sub.onSubscribe(DONE);  |   |   sub.onSubscribe(this);  |
| }                         |   |   sub.onItem(null);       |
|                           |   | }                         |
+---------------------------+   +---------------------------+
  구독자가 받는 것: 1 건          구독자가 받는 것: 2 건
  그 뒤로 영원히 없음             그리고 끝난다
```

### 두 객체가 Publisher가 됐을 때

이 결함이 관측되는 자리는 Uni 자체가 아니라 그것을 `Publisher`로 바꾼 뒤다.\
변환의 실체는 `UniToMultiPublisher`이고, 핵심은 `onItem` 하나다.

```java
@Override
public void onItem(T item) {
    if (STATE_UPDATER.compareAndSet(this, State.UNI_REQUESTED, State.DONE)) {
        if (item != null) {
            downstream.onNext(item);
        }
        downstream.onComplete();
    }
}
```
(UniToMultiPublisher.java:89-97)

**`if (item != null)` 이 한 줄이 두 세계의 번역기다.**\
Reactive Streams는 `onNext(null)`을 금지하므로 null item은 "아이템 없이 완료"로 옮겨진다.\
그래서 표가 이렇게 닫힌다.

> **`onNext(null)` 금지** — Reactive Streams 명세가 "값 신호로 null을 보내면 안 된다"고 못 박은 규칙.\
> 예: 그래서 "값이 없다"는 사실은 null을 보내는 대신 아무것도 안 보내고 `onComplete`만 보내는 것으로 적는다.

| | `nothing()` | `nullItem()` |
|---|---|---|
| 만드는 객체 | `UniNever.INSTANCE` (싱글턴, 필드 없음) | `UNI_OF_NULL` = `UniCreateFromKnownItem<>(null)` (싱글턴) |
| 구독 시 Uni 레벨 | `onSubscribe(DONE)` 1회, 끝 | `onSubscribe` 1회 + `onItem(null)` 1회 |
| Publisher로 변환 후 | `onNext` 0회, `onComplete` 0회, `onError` 0회 | `onNext` 0회, **`onComplete` 1회** |
| `Mono.block()` 결과 | 타임아웃 예외 | `null` 반환 |
| 대응하는 Reactor 값 | `Mono.never()` | `Mono.empty()` |

마지막 행이 결함을 한 문장으로 요약한다.\
**empty-value 자리에 들어가야 했던 것은 `Mono.empty()`의 Uni 대응물인데, 들어가 있던 것은 `Mono.never()`의 대응물이었다.**

그리고 "null item Uni", "아이템 없이 완료되는 Publisher", "`block()`이 돌려주는 `null`" 이 셋은 서로 다른 값이 아니라 **같은 사태를 세 층에서 적은 표기**다.\
`null`이라는 값이 파이프를 타고 흐르는 것이 아니다.

```text
  같은 사태, 세 층의 표기

  Mutiny 층    :  Uni(item = null)
                       |
                       v
  Publisher 층 :  onNext 없이 onComplete 1 회
                       |
                       v
  Java 값 층   :  block() 이 돌려주는 null
```

## 3. 왜 "완료"가 계약인가

`getEmptyValue()`의 javadoc은 한 줄이다 - "Return an empty-value instance for the underlying reactive or async type"(ReactiveTypeDescriptor.java:95-98).\
"empty"라는 단어만 있고 "completes"는 없다.\
그런데도 완료가 계약인 근거는 셋이다.

> **암묵의 계약(implicit contract)** — 문서에 적혀 있지 않지만 코드 전체가 그렇게 돌아가고 있어 사실상 약속이 된 규칙.\
> 예: javadoc에 "완료한다"는 말은 없지만 형제 열두 개가 전부 완료하므로 그것이 약속이 된다.

**첫째, 호출자가 그렇게 쓴다.**\
`toPublisher`의 javadoc이 "if the given object is `null`, `getEmptyValue()` is used"라고 적고(ReactiveAdapter.java:103-104), 그 결과는 곧장 구독자에게 넘어간다.\
구독자는 `null` 소스를 "값이 없다"로 처리하려는 것이지 "기다리라"는 뜻으로 받지 않는다.

**둘째, 형제 열두 개가 전부 그렇게 한다.**\
`Mono::empty`, `Flux::empty`, `Flux::empty`(`Publisher` 등록분), `EMPTY_FLOW`(`Flow.Publisher` 등록분), `Maybe::empty`, `Completable::complete`, `CompletableDeferred(null)`, `FlowKt::emptyFlow`, `Flowable::empty`, `Observable::empty`, `EmptyCompletableFuture`(생성자가 `complete(null)` - :302-307), `Multi.createFrom().empty()` - 열두 개 모두 즉시 완료되는 값이다.\
관례가 곧 계약인 상황이다.

**셋째, 팩토리 이름이 그렇게 말한다.**\
`singleOptionalValue`는 "0..1개를 낼 수 있는 타입"이라는 뜻이고(:148-150), 0개를 낸다는 것은 "완료하되 아무 값도 없음"이다.\
0개도 1개도 안 내는 것은 이 팩토리가 서술하는 상태가 아니다.\
그런 타입이 놓일 자리는 `singleRequiredValue`(:156-158)이고, 그쪽은 공급자를 아예 받지 않는다.

세 팩토리가 서술하는 상태를 수직선에 놓으면 `nothing()`이 어디에도 없다는 것이 보인다.

```text
  내는 값의 개수      0 ---------- 1 ---------- N
                      |            |            |
  singleRequiredValue |         [ 1 개 ]        |     공급자 없음
  singleOptionalValue [ 0 ~ 1 개 ]              |     공급자 필수 <- Uni
  multiValue          [ 0 개 ---------------- N 개 ]  공급자 필수

  nothing() 이 서술하는 상태 = "0 개도 1 개도 안 냄, 끝나지도 않음"
                              -> 위 세 칸 어디에도 없다
```

## 4. 결함 경로 단계 추적 (실측)

빌드된 `spring-core` 클래스에 Mutiny 1.10.0 + Reactor 3.8.7을 물려 어댑터를 직접 호출한 결과가 아래다.\
프로덕션과 수정안을 같은 축으로 대조한다.

| 단계 | 수정 전 (`nothing()`) | 수정 후 (`nullItem()`) |
|---|---|---|
| `getEmptyValue()` 반환 객체 | `io.smallrye.mutiny.operators.uni.UniNever` | `UniCreateFromKnownItem`(item=null) |
| `toPublisherFunction.apply(...)` (:402) | Publisher 생성 성공 | 성공 |
| `ReactorAdapter`가 감쌈 (:260-263) | `Mono` 생성 성공 | 성공 |
| 구독 후 도착하는 신호 | 없음 | `onComplete` 1회 |
| `Mono.block(600ms)` | **`IllegalStateException: Timeout on blocking read`** | `null` (즉시) |
| `fromPublisher(Mono.empty())` 후 `await()` | `null` item (수정과 무관하게 동일) | `null` item |
| 형제 `Mono` 어댑터의 같은 호출 | `null` (정상 완료) | 동일 |
| 형제 `Multi` 어댑터의 같은 호출 | `null` (정상 완료) | 동일 |

같은 입력 하나가 수정 전후로 어떤 최종 상태에 도달하는지만 떼어 놓으면 이렇다.

```text
        수정 전 (nothing())                     수정 후 (nullItem())
+--------------------------------+     +--------------------------------+
| getEmptyValue()                |     | getEmptyValue()                |
|   -> UniNever                  |     |   -> UniCreateFromKnownItem    |
+--------------------------------+     +--------------------------------+
| 변환 성공 / Mono 생성 성공     |     | 변환 성공 / Mono 생성 성공     |
+--------------------------------+     +--------------------------------+
| 도착 신호      : 0 건          |     | 도착 신호      : onComplete 1  |
| block(600ms)   : Timeout 예외  |     | block(600ms)   : null (즉시)   |
| 형제 Mono/Multi: 정상 완료     |     | 형제 Mono/Multi: 정상 완료     |
+--------------------------------+     +--------------------------------+
  최종 상태: 요청이 매달린다              최종 상태: 형제와 같아진다
```

-> 변환 단계는 수정 전후가 똑같고, 마지막 신호 층에서만 갈린다.

여섯째 행이 착수 명세의 `[구현 검증]` 이연 항목을 해소한 자리다.\
"빈 Publisher가 null item Uni로 완료된다"는 서술은 착수 시점에 Mutiny 문서에만 근거했는데(UniCreate.java:265-287의 javadoc - "If the publisher emits the completion signal before having emitted a value, the produced `Uni` emits a `null` item event"), red 확인 회차에 `toUniFromEmptyPublisher`가 green으로 나오면서 실행으로 확정됐다.\
그 문장의 구현은 `UniCreateFromPublisher`의 `onComplete`가 `subscriber.onItem(null)`을 부르는 것이다(UniCreateFromPublisher.java:85-91).

> **`[구현 검증]` 이연** — 문서만 읽어서는 참·거짓을 못 가리는 판정을, 실제로 코드를 돌려 볼 때까지 미뤄 두고 표시해 두는 것.\
> 예: "Mutiny 문서에 그렇게 적혀 있다"는 근거는 실행으로 확인하기 전까지 가정으로 남겨 둔다.

일곱째·여덟째 행이 이 결함을 설계가 아닌 실수로 읽게 하는 근거다.\
**같은 registrar 안에서 바로 아래 줄에 등록된 `Multi`는 올바르다.**

## 5. 계약

이 무대가 지키기로 한 약속을 네 줄로 세우고 수정 전 코드가 그중 무엇을 어겼는지 대조한다.

| 계약 | 출처 | 수정 전 위반 여부 |
|---|---|---|
| `supportsEmpty()`가 참인 타입의 empty-value는 구독 시 유한 시간 안에 완료한다 | 형제 등록 10종 + `singleOptionalValue`/`noValue` 팩토리의 의미 | **Uni만 위반** |
| `toPublisher(null)`은 오류 경로가 아니라 정식 계약 경로다 | `ReactiveAdapter.java:103-104` javadoc | 위반 아님 - 호출 규약은 지켜졌다 |
| `toPublisher`와 `fromPublisher`는 서로의 역함수다 | 같은 registrar가 두 함수를 함께 등록한다는 구조 | **위반** - 빈 값의 표현이 두 방향에서 달랐다 |
| 비-null 소스의 어댑테이션은 empty-value와 무관하다 | `ReactiveAdapter.java:109` 분기 | 위반 아님 - 그래서 수정이 안전하다 |

셋째 줄이 이 PR의 수정값을 결정한 계약이다.\
첫째 줄만 보면 "완료되기만 하면 되니 아무 완료값이나 좋다"가 되지만, 셋째 줄까지 보면 **완료값이 하나로 정해진다** - 역방향이 이미 정한 표현과 같아야 한다.

## 6. 발화 조건 - 왜 아무도 못 봤나

발화 조건은 한 문장이다.\
**`Uni`로 선언된 자리에 값이 `null`로 들어와 프레임워크가 `toPublisher(null)`을 부르는 경우**다.\
그런데도 2021년 도입 이후 보고가 없었던 이유는 셋이다.

> **발화 조건(trigger condition)** — 잠재된 결함이 실제 증상으로 드러나기 위해 만족돼야 하는 조건.\
> 예: 여기서는 참조가 실제로 `null`이어야 하고, 그 자리에 Mutiny를 쓰고 있어야 한다.

**첫째, 정상 경로가 이 줄을 지나지 않는다.**\
`Uni<T>`를 반환하는 메서드가 실제로 `Uni`를 반환하면 `source != null`이라 L110이 아예 실행되지 않는다.\
결함이 발화하려면 참조 자체가 `null`이어야 하고, 그것은 조건 분기에서 빈손을 `null`로 표현했거나 레거시 코드가 섞인 경우다.

**둘째, Mutiny 어댑터 자체가 틈새다.**\
Spring에서 Mutiny를 쓰는 조합 - Quarkus 세계의 타입을 Spring MVC/WebFlux에서 쓰는 조합 - 자체가 Reactor·RxJava에 비해 드물다.\
최초 도입 PR #27331(hantsy, 2021-08, 5.3.10) 이후 이 등록을 건드린 PR은 버전 업그레이드(#27555)뿐이고, 이슈 검색(`Mutiny Uni`, `getEmptyValue`, `Uni never`)에서 관련 보고 0건이었다(2026-09-08·09 재검색).

**셋째, 증상이 예외가 아니라 타임아웃이다.**\
행이 걸린 요청 하나를 보고 "리액티브 어댑터의 empty-value 등록"을 의심하는 사람은 없다.\
무한 대기의 용의자 목록에서 네트워크·DB·스레드 풀·백프레셔가 앞에 서고, 타입 어댑테이션은 끝에도 없다.

> **백프레셔(backpressure)** — 받는 쪽이 감당할 수 있는 만큼만 보내라고 요구하는 흐름 제어.\
> 예: 구독자가 "2개만 더 줘"라고 요청하면 Publisher는 그만큼만 보낸다. 요청이 안 오면 값도 안 오므로 무한 대기의 흔한 용의자가 된다.

기원 커밋도 확인했다.\
`1dc128361f8` "Add SmallRye Mutiny adapters"(2021-08)의 리뷰 코멘트에 empty-value 선택에 대한 논의가 없다 - 머지 인사뿐이다.\
즉 `nothing()`은 검토를 거쳐 채택된 값이 아니라 **검토되지 않은 채 들어온 초기 선택**이었다.

## 7. 수정안

### 7.1 채택안 - 공급자 한 줄

```java
// before (L376-378)
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
		io.smallrye.mutiny.Uni.class,
		() -> io.smallrye.mutiny.Uni.createFrom().nothing());

// after
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
		io.smallrye.mutiny.Uni.class,
		() -> io.smallrye.mutiny.Uni.createFrom().nullItem());
```

새 임포트도 새 분기도 없다.\
`uniDesc`가 Mutiny 1·2 두 등록에 공유되므로(:389-397 / :401-406) 한 줄이 두 경로를 덮는다.

### 7.2 기각한 대안

**(a) `getEmptyValue()`에서 완료 여부를 검증한다.**\
성립하지 않는다.\
완료는 구독해 봐야 알 수 있는 속성인데, `getEmptyValue()`는 어댑테이션 경로 한복판에서 불리므로 그 자리에서 구독해 소진할 수 없다.\
구독은 부수 효과가 있고, 반환값은 아직 소비자에게 넘어가지도 않았다.

> **부수 효과(side effect)** — 값을 돌려주는 것 말고 바깥 상태를 바꾸거나 동작을 시작시키는 일.\
> 예: 리액티브 타입은 구독하는 순간 실행이 시작되므로, 확인하려고 한 번 구독하면 그 자체가 동작이 된다.

**(b) `toPublisher`에서 `null`을 다르게 처리한다.**\
예를 들어 empty-value 대신 `Mono.empty()`를 쓰면 Uni 어댑터만 자기 타입 밖의 값을 내놓게 되어 어댑터의 정의가 무너진다.\
게다가 이 결함은 Uni 등록의 문제이지 `toPublisher` 골격의 문제가 아니다.

**(c) `singleRequiredValue`로 재등록해 `supportsEmpty()`를 false로 만든다.**\
결함은 사라지지만 기능이 축소된다.\
Mutiny `Uni`는 명백히 빈 결과를 표현할 수 있는 타입이고(null item), 그 표현을 갖고 있는데 "못 만든다"고 선언하는 것은 사실과 다르다.\
`supportsEmpty()`를 신뢰하는 소비자들(structure.md 5절)의 판정이 함께 뒤집히는 부작용도 생긴다.

세 대안이 각각 무엇을 건드리는지 나란히 놓으면 채택안만 범위가 좁다.

```text
  채택안      : Uni 등록 한 줄        -> 다른 열두 등록 무영향
  대안 (a)    : 검사 골격 전체        -> 구독 부수 효과 때문에 성립 불가
  대안 (b)    : toPublisher 골격      -> 어댑터 정의가 무너진다
  대안 (c)    : Uni 의 선언 자체      -> supportsEmpty 소비자 전부가 흔들린다
```

### 7.3 영향 범위와 검증 계획

변경 범위는 파일 둘이고, 회귀 위험은 `ReactiveAdapter.java:109`의 분기 하나로 좁혀진다.

> **test-first(테스트 우선)** — 고치기 전에 실패하는 테스트를 먼저 써 두고, 그 테스트가 통과하도록 코드를 고치는 순서.\
> 예: 여기서는 red 를 먼저 확인했기 때문에 "정말 이 결함이 맞나"를 추측이 아니라 실행으로 확정했다.

- 변경 파일: `ReactiveAdapterRegistry.java` 한 줄 + `ReactiveAdapterRegistryTests.java` 테스트 2건 추가.
- 회귀 위험: 공급자가 읽히는 유일한 경로가 `source == null`이므로, 비-null Uni를 넘기는 기존 사용자는 정의상 무영향이다.\
  기존 `fromUni` 테스트가 그 경로의 가드다.
- 테스트(test-first): `toPublisher(null)`이 빈 완료가 되는지(red) + 왕복 대칭을 고정하는 역방향 테스트(fix 전후 green).
- 스모크: 빌드 클래스에 직접 어댑터를 물려 프로브 재실행.

## 8. 범위 밖 - 인접하지만 이번에 안 건드린 것

같은 파일·같은 계열이지만 이번 PR이 손대지 않은 항목과, 확인하지 않은 것을 남긴다.

> **범위 밖(out of scope)** — 눈에 띄었지만 이번 변경에서 일부러 손대지 않기로 정한 것.\
> 예: 계약을 강제하는 레지스트리 레벨 테스트를 두는 일은 값어치가 있지만, 이 PR 한 줄과는 별개 작업이다.

- **`getEmptyValue()`가 계약을 검사하지 않는다는 구조 자체.**\
  7.2 (a)에서 본 대로 런타임 검사는 성립하지 않는다.\
  하려면 "모든 `supportsEmpty()` 어댑터의 empty-value가 유한 시간에 완료하는가"를 도는 레지스트리 레벨 테스트를 두는 별개 작업이 된다.\
  제안 가치는 있으나 이 PR의 범위가 아니다.
- **Mutiny 2 분기의 실행 검증.**\
  이 저장소는 1.10.0에 고정돼 있어(`framework-platform.gradle:56`) `else` 분기만 실행된다.\
  Mutiny 2 분기가 `uniDesc`를 공유한다는 것은 코드로 확인했지만 실행으로 확인하지는 않았다.
- **`Uni<Void>`의 `isNoValue()` 판정.**\
  프로브에서 `isNoValue()=false`임을 확인했는데, `Uni<Void>`를 `noValue`로 볼지 여부는 별개 설계 논의다.
- **`nothing()`이 정당하게 쓰여야 할 자리가 이 저장소에 있는가.**\
  검색 결과 `createFrom().nothing()`의 사용처는 이 한 줄뿐이었고(수정으로 0건), 따라서 "never" 의미가 필요한 자리는 없었다.
- **엔드투엔드 행 재현.**\
  WebFlux 서버를 실제로 띄워 요청이 타임아웃까지 매달리는 것을 확인하지는 않았다.\
  확인한 것은 어댑터 레벨의 무신호이고, 그 위의 응답 미완료는 `AbstractMessageWriterResultHandler.java:174-180`의 코드 추적이다.

> **엔드투엔드(end-to-end)** — 부품 하나가 아니라 사용자 요청부터 응답까지 전체 경로를 실제로 돌려 보는 검증.\
> 예: 어댑터만 직접 부르는 프로브와 달리, 서버를 띄우고 HTTP 요청을 보내 응답이 오는지 보는 것이다.
