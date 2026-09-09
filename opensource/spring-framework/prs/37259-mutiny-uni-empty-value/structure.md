# PR #37259 - 무대의 실구조와 워크플로우

> PR #37259의 무대가 되는 실구조와 워크플로우. 문제와 수정은 [README.md](README.md),
> 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: 로컬 HEAD `c57215898bb`(브랜치 `fix/mutiny-uni-empty-value` = upstream main
> `572850bdcf1` 리베이스 + fix 커밋). **이 시점의 `ReactiveAdapterRegistry.java`에는
> 이미 수정이 반영돼 있다** - 아래 file:line은 "수정 후" 좌표다. 다만 수정이 한 줄
> 치환이라 줄 번호는 수정 전과 같다. Mutiny 쪽 좌표는 **Mutiny 1.10.0 sources jar**
> 안의 파일이며 이 저장소에는 없다.

## 1. 무대 - 실구조

이 결함의 무대는 **모든 비동기/리액티브 타입을 Reactive Streams `Publisher` 하나로
정규화하는 다리**이고, 그 다리의 각 칸이 `ReactiveAdapter`다. 어댑터는 변환 함수
둘과 의미론 서술 하나로 이뤄지는데, 이 PR이 건드린 것은 세 번째 조각 안의 필드
하나 - "빈 인스턴스를 만드는 공급자"다. 계층을 위에서 아래로 그리면 이렇다.

```
+------------------------------------------------------------------------------+
| 등록 (레지스트리 생성 시 1회)     spring-core/core/ReactiveAdapterRegistry.java |
|   생성자가 클래스패스를 보고 registrar 를 고른다                     :93-123    |
|     REACTOR_PRESENT        -> ReactorRegistrar                      :100-102  |
|     RXJAVA_3_PRESENT       -> RxJava3Registrar                      :105-107  |
|     COROUTINES_*           -> CoroutinesRegistrar                   :110-112  |
|     MUTINY_PRESENT         -> MutinyRegistrar                       :115-117  |
|     (Reactor 없으면)        -> FlowAdaptersRegistrar                 :120-122  |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| MutinyRegistrar (이번 무대의 등록자)                                 :370-409  |
|                                                                              |
|   uniDesc   = singleOptionalValue(Uni.class,   () -> ...nullItem())  :376-378 |
|                                                       ^^^^^^^^^^ 수정된 줄     |
|   multiDesc = multiValue(Multi.class,          () -> ...empty())     :379-381 |
|                                                                              |
|   UniConvert.toPublisher() 의 반환 타입이 Flow.Publisher 인가?        :383     |
|     예 -> Mutiny 2 분기: 리플렉션 + FlowAdapters 로 등록              :384-397 |
|     아니오 -> Mutiny 1 분기: 직접 등록                                :399-407 |
|          toPublisher   = uni.convert().toPublisher()                 :402     |
|          fromPublisher = Uni.createFrom().publisher(publisher)       :403     |
|                                                                              |
|   ** 두 분기가 uniDesc "한 개"를 공유한다                                      |
|      -> 공급자 한 줄이 Mutiny 1·2 양쪽을 덮는다 **                             |
|   ** 이 저장소는 mutiny 1.10.0 고정 (framework-platform.gradle:56)             |
|      -> 실제로 실행되고 테스트되는 것은 else(Mutiny 1) 분기 **                  |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| ReactiveTypeDescriptor (의미론 서술)    spring-core/core/ReactiveTypeDescriptor.java |
|                                                                              |
|  [상태] reactiveType / multiValue / noValue / emptySupplier / deferred :34-42 |
|                                                                              |
|  [질의] isMultiValue()  0..N 인가 0..1 인가                           :76-78  |
|         isNoValue()     값 없이 완료·에러만인가                        :84-86  |
|         supportsEmpty() = (emptySupplier != null)                     :91-93  |
|         getEmptyValue() = emptySupplier.get(), null 이 아닌지만 확인    :99-104 |
|             ** 반환 객체가 실제로 완료하는지는 검사하지 않는다 **               |
|         isDeferred()    구독 등으로 명시 시작해야 하는가               :112-114 |
|                                                                              |
|  [팩토리 5종]                                                        :139-178 |
|    multiValue(type, supplier)          0..N, 공급자 필수              :139-141 |
|    singleOptionalValue(type, supplier) 0..1, 공급자 필수  <- Uni       :148-150 |
|    singleRequiredValue(type)           반드시 1, 공급자 없음 <- Single :156-158 |
|    noValue(type, supplier)             값 없음, 공급자 필수            :165-167 |
|    nonDeferredAsyncValue(type, supplier) CompletableFuture 류         :176-178 |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| ReactiveAdapter (다리 한 칸)             spring-core/core/ReactiveAdapter.java |
|                                                                              |
|   descriptor + toPublisherFunction + fromPublisherFunction            :37-41  |
|                                                                              |
|   toPublisher(@Nullable Object source)                               :108-113 |
|     if (source == null) source = getDescriptor().getEmptyValue();     :109-110|
|         ** getEmptyValue() 의 프로덕션 유일 호출처가 이 한 줄이다 **            |
|     return toPublisherFunction.apply(source);                         :112    |
|                                                                              |
|   fromPublisher(Publisher<?> publisher)                              :120-122 |
|     return fromPublisherFunction.apply(publisher);                            |
|         ** 공급자를 전혀 참조하지 않는다 - 그래서 대칭의 기준점이 된다 **       |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| ReactorAdapter (Reactor 있을 때 buildAdapter 가 씌우는 하위 타입)      :250-264 |
|   toPublisher 결과를 isMultiValue() 에 따라 Flux/Mono 로 감싼다        :260-263 |
|     Uni 는 단일 값 -> Mono.from(publisher)                                     |
|     => 테스트의 assertThat(target).isInstanceOf(Mono.class) 가 통과하는 이유    |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| 소비자 - 프로덕션 42곳이 toPublisher 를 부른다 (3절)                            |
|   WebFlux 본문 쓰기 / ResponseEntity / SSE / @Transactional /                  |
|   @Cacheable / @Scheduled / RSocket 인코딩 / HTTP 서비스 인터페이스 ...          |
+------------------------------------------------------------------------------+
```

이 그림에서 읽어야 할 사실은 둘이다. 첫째, **`supportsEmpty()`라는 선언과 그 선언을
뒷받침하는 인스턴스가 다른 곳에서 만들어지고, 둘을 맞춰 주는 검사가 없다.**
`getEmptyValue()`가 확인하는 것은 공급자가 `null`을 돌려주지 않았다는 사실뿐이다.
둘째, **공급자가 읽히는 자리는 `ReactiveAdapter.java:110` 단 하나다.** 그래서 결함의
발화 조건도, 수정의 영향 범위도 정확히 그 한 줄에서 정해진다.

## 2. 수정 전 동작 워크플로우

등록은 애플리케이션당 한 번 굳고, 이후 어댑테이션은 그 descriptor를 읽기만 한다.
두 단계로 나눠 본다.

```
[등록 - 레지스트리 생성 시 1회]
new ReactiveAdapterRegistry()  또는  getSharedInstance()          :93 / :229-241
  |
  +- MUTINY_PRESENT 이면 new MutinyRegistrar().registerAdapters(this)    :115-117
       |
       +- uniDesc 생성  (여기서 empty 공급자 람다가 descriptor 에 박힌다)  :376-378
       |    [수정 전] () -> Uni.createFrom().nothing()    <- UniNever
       |    [수정 후] () -> Uni.createFrom().nullItem()   <- null item 으로 즉시 완료
       |
       +- Mutiny 1 분기라면 registerReactiveType(uniDesc, 람다, 람다)      :401-403
            +- buildAdapter 가 Reactor 유무를 보고 ReactorAdapter 로 감쌈  :164-169

[어댑테이션 - 값 하나마다]
소비자 (예: WebFlux 본문 쓰기)
  -> getAdapterRegistry().getAdapter(bodyType.resolve(), body)   Writer:174
  |    ** 선언 타입으로 조회한다 - body 가 null 이어도 어댑터를 찾는다 **  :195-209
  |
  -> adapter.toPublisher(body)                                   Writer:180
       |
       +- ReactorAdapter.toPublisher -> super.toPublisher        :260-261
       |
       +- ReactiveAdapter.toPublisher                            :108-113
       |    body != null 이면 ------------------------------> L112 직행 (무영향)
       |    body == null 이면 L110 에서 getEmptyValue() 호출  <- 결함이 사는 유일한 분기
       |
       +- toPublisherFunction.apply(source)                      :402
       |    = uni.convert().toPublisher()  -> UniToMultiPublisher
       |
       +- ReactorAdapter 가 Mono.from(...) 으로 감쌈              :262
```

수정 전의 결함은 첫 단계(등록의 한 줄) 안에서 만들어지지만, 증상은 둘째 단계의 맨
끝, 구독자가 신호를 기다릴 때 관측된다. 신호 층위로 좁혀서 두 값을 나란히 추적하면
이렇다.

```
[수정 전]  toPublisher(null)
  L110  getEmptyValue()  ->  UniNever.INSTANCE
                             subscribe(sub) { sub.onSubscribe(DONE); }      UniNever:15-18
  L112  uni.convert().toPublisher()  ->  UniToMultiPublisher
                             request(n) -> AbstractUni.subscribe(uni, this) UniToMulti:73-75
                             onSubscribe 만 오고 onItem 은 영영 안 온다
  L262  Mono.from(...)     ->  Mono 는 정상 생성, 구독도 정상
        block(5s)          ->  onNext 0 / onComplete 0 / onError 0
                             => IllegalStateException: Timeout on blocking read

[수정 후]  toPublisher(null)
  L110  getEmptyValue()  ->  UNI_OF_NULL = UniCreateFromKnownItem(null)
                             forward() { onSubscribe(this); onItem(null); } KnownItem:35-40
  L112  uni.convert().toPublisher()  ->  UniToMultiPublisher
                             onItem(null): item==null 이므로 onNext 생략     UniToMulti:89-97
                                           downstream.onComplete()
  L262  Mono.from(...)
        block(5s)          ->  아이템 없는 정상 완료를 받고 즉시 null 반환
```

두 추적의 차이는 `UniToMultiPublisher.onItem`의 `if (item != null)` 한 줄에서 갈린다.
그 줄이 Reactive Streams의 `onNext(null)` 금지를 지키는 번역기이고, 그래서 **"null
item"은 "빈 완료"로 옮겨진다**. 수정 전에는 그 `onItem`이 애초에 호출되지 않는다.

## 3. `toPublisher(null)`에 실제로 도달하는 자리 - 전수 판별

이 결함의 영향권을 재려면 "누가 `toPublisher`에 `null`을 넘길 수 있나"를 세어야
한다. 프로덕션 코드(`spring-*/src/main`)의 `ReactiveAdapter.toPublisher(...)` 호출은
**42곳**이고, 판별 기준은 둘이다.

- (a) 넘기는 값이 그 자리에서 `null`일 수 있나(선행 null 가드가 없나).
- (b) 어댑터를 **선언 타입**에서 얻었나. `value.getClass()`로 얻었다면 값이 이미
  역참조된 뒤이므로 `null`이 구조적으로 불가능하다.

둘 다 만족하는 자리가 **12곳**이다.

| 모듈 | 자리 | 발화하는 상황 |
|---|---|---|
| spring-webflux | `AbstractMessageWriterResultHandler.java:180` | `@ResponseBody` 핸들러가 `null` 반환 |
| spring-webflux | `ResponseEntityResultHandler.java:141` | `Uni<ResponseEntity<T>>` 핸들러가 `null` 반환 |
| spring-webflux | `InvocableHandlerMethod.java:231-232` | async void(`Uni<Void>`) 핸들러가 `null` 반환 |
| spring-webflux | `ViewResolutionResultHandler.java:373` | SSE fragment 스트림 반환값이 `null`(형제 분기 :226-227은 가드가 있는데 이 분기만 없다) |
| spring-messaging | `AbstractEncoderMethodReturnValueHandler.java:135` | RSocket 응답 인코딩 대상이 `null` |
| spring-messaging | `InvocableHandlerMethod.java:156` | async void 메시지 핸들러가 `null` 반환 |
| spring-context | `ScheduledAnnotationReactiveSupport.java:162` | `@Scheduled` 리액티브 메서드가 `null` 반환 |
| spring-context | `CacheAspectSupport.java:1128`, `:1135` | `@Cacheable(sync=true)` 단일값 경로의 실제 호출이 `null` 반환 |
| spring-context | `CacheAspectSupport.java:1109`, `:1117` | 〃 다중값(Flux) 경로 |
| spring-tx | `TransactionAspectSupport.java:950` | `@Transactional` 리액티브 메서드가 `null` 반환 |

`Uni`가 실제로 놓일 수 있는 자리는 이 중 열이다. `CacheAspectSupport:1109`·`:1117`은
`adapter.isMultiValue()`가 참인 분기라(:1105) `Uni`는 그 형제인 `:1128`·`:1135` 쪽으로
간다. 반대로 `TransactionAspectSupport:950`은 `Uni`에게 **유일한** 경로다 - 그 위의
`Mono` 전용 분기(:930)는 `Objects.requireNonNull`로 막혀 있고, "그 밖의 리액티브
타입"으로 내려온 쪽만 가드가 없다.

도달하지 않는 30곳이 왜 안전한지도 축으로 정리해 두면, 이 결함이 "리액티브 어댑터를
쓰는 모든 곳"의 문제가 아니라 **어댑터를 선언 타입으로 찾는 곳만의 문제**임이 보인다.

| 사유 | 자리 |
|---|---|
| 어댑터를 `value.getClass()`에서 얻는다(값이 이미 역참조됨) | `DisposableBeanAdapter:507`, `ApplicationListenerMethodAdapter:506`, `FragmentsRendering:120`, `DefaultRSocketRequester:174/189/200`, `MetadataEncoder:144`, `DefaultRSocketRequesterBuilder:278`, `AsyncServerResponse:107`, `DefaultEntityResponseBuilder:217`, `ModelAttributeMethodArgumentResolver:167`, `ReactiveTypeHandler:283/519`, `BodyInserters:427` |
| 호출 직전에 null 가드가 있다 | `MethodValidationInterceptor:261/263`(:245 continue), `AbstractRetryInterceptor:178`(:101 early return), `CacheAspectSupport:1172/1232/1238`(어댑터 자체를 result에서 얻음), `AbstractView:256/262`(:244 continue), `ViewResolutionResultHandler:227/234`(`!= null` 삼항), `PayloadArgumentResolver:77`(:59-63), `RequestBodyArgumentResolver:100`(:84-87), `RequestPartArgumentResolver:111`(호출자 :202-205), `ReactiveReturnValueHandler:64`(호출자 가드), `ModelInitializer:126`(:120), `RequestAttributeMethodArgumentResolver:86`(:71-76) |

`RequestAttributeMethodArgumentResolver`는 대비로 읽을 만하다. 값이 없을 때 이
resolver는 `toAdapter.fromPublisher(Mono.empty())`를 쓴다(:74-77) - 즉 **empty-value
공급자 대신 역방향 변환으로 빈 값을 만든다.** 그쪽 경로는 수정 전에도 옳게 동작했고,
그것이 곧 "빈 것의 Uni측 표현은 이미 null item으로 정해져 있었다"는 사실의 또 다른
증거다. 같은 프레임워크 안에서 빈 값을 만드는 두 방법이 서로 다른 답을 내고 있었던
것이다.

## 4. 두 개의 "없음" - Reactor와 Mutiny의 표기법 차이

이 결함을 만드는 인지적 함정은 하나다. **Mono는 "완료"와 "값"을 별개 신호로 다루고,
Uni는 하나의 결과 이벤트에 합쳤다.** 그래서 "빈 값"을 적는 자리가 다르다. 고정 축으로
비교하면 이렇다.

| 상황 | Reactor `Mono` | Mutiny `Uni` |
|---|---|---|
| 값 있음 | `onNext(v)` + `onComplete()` (신호 2개) | `onItem(v)` (신호 1개) |
| **값 없음** | `onNext` 없이 `onComplete()` | **`onItem(null)`** |
| 에러 | `onError(t)` | `onFailure(t)` |
| 아무 일 없음 | `Mono.never()` | `Uni.createFrom().nothing()` |
| 빈 값 팩토리 | `Mono.empty()` | `Uni.createFrom().nullItem()` |

마지막 두 행이 이 PR의 전부다. 수정 전 등록은 **넷째 행의 값을 다섯째 행 자리에
넣어 두었다.** `nothing()`이 잘못된 값인 것이 아니라 잘못된 자리에 있었다 - 그 값의
정당한 용도는 "결코 끝나지 않는 스트림"이다.

Uni에는 `Mono.empty()`에 대응하는 "아이템 없는 완료"라는 상태 자체가 없다. Mutiny의
결과 이벤트는 item 아니면 failure 둘 중 하나이고, 값이 없다는 사실은 **item의 값이
`null`이라는 것으로** 적는다. 그래서 두 세계를 잇는 변환기가 필요하고, 그 변환기가
`UniToMultiPublisher.onItem`의 `if (item != null)` 한 줄이다.

## 5. 스프링 전역에서의 자리

`ReactiveAdapterRegistry`는 spring-core에서 **"프레임워크 안쪽은 Publisher 하나로
통일한다"는 정책을 실행하는 단일 지점**이다. 이 정책 덕에 인코더·메시지 컨버터·뷰·
캐시·트랜잭션 어드바이스가 반환 타입마다 분기하지 않는다.

```
[핸들러가 반환한 것]        [정규화]                  [프레임워크 내부]        [복원]
Mono / Flux            \                                                  /
Uni  / Multi            \                                                /
Flowable / Observable    >-- adapter.toPublisher --> Publisher<?> -------<  adapter.fromPublisher
Maybe / Completable     /      (null 이면 empty-value)   |               \
Deferred / Flow        /                                 |                \
CompletableFuture     /                                  v
                                              인코딩 / 캐싱 / 트랜잭션 /
                                              뷰 렌더링 / SSE / RSocket
```

`ReactiveTypeDescriptor`가 서술하는 세 축(`isMultiValue`·`isNoValue`·`supportsEmpty`)은
그 내부 처리가 타입마다 무엇을 가정해도 되는지를 정한다. 그중 `supportsEmpty()`는
프레임워크 곳곳에서 **신뢰의 근거**로 쓰인다.

- `PayloadMethodArgumentResolver:221`·`AbstractMessageReaderArgumentResolver:148` -
  "빈 값을 못 만드는 타입이면 본문이 필수다"라는 판정.
- WebFlux `InvocableHandlerMethod:296`·messaging `InvocableHandlerMethod:203` -
  async void 반환인지 판정.

이 소비자들이 보는 것은 **선언**(`supportsEmpty()`)뿐이고, 그 선언 뒤의 **인스턴스**는
`ReactiveAdapter.java:110`만이 만진다. 수정 전에는 선언이 참인데 인스턴스가 계약을
어긴 상태였고, 그래서 선언을 믿은 코드들은 아무 잘못 없이 정상 동작했으며 인스턴스를
실제로 쓰는 한 줄에서만 침묵이 발생했다.

영향권은 **Mutiny를 Spring MVC/WebFlux와 함께 쓰면서 `Uni` 자리에 `null`이 들어가는
사용자**다. 2021년 도입(`1dc128361f8`, 5.3.10) 이후 이 등록을 건드린 PR은 버전
업그레이드뿐이고, 이슈 보고도 0건이었다.

## 6. 관련 개념

이 무대의 배경은 별도 문서로 정리돼 있으므로 링크로 연결한다.

- [Uni와 Mono - 빈 값을 서로 다르게 적는 두 단일 값 타입](../../concepts/uni-vs-mono-reactive-types/uni-vs-mono-reactive-types.md) -
  두 타입의 신호 모델 대조, `ReactiveAdapter`가 두 세계를 잇는 방식, 그리고 이
  결함의 실측 매트릭스. 이 PR의 이해 게이트에서 파생된 문서다.
