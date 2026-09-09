# PR #37259 - 이해 게이트 기록

> 출처: 세션 1761423a (2026-09-09), 작업 폴더
> `docs/plans/2026-09-09/h3-mutiny-uni-empty-hang/`.
> 모드 lazy - 매 diff마다 사용자가 주관식으로 설명하고 독립 판정 워커가 pass/fail을
> 매긴다. 최대 2회, 2회째는 정답을 제시하고 통과 처리한다.
> 답변은 대화에 남은 원문 그대로 옮겼다(오타와 비문 포함). 판정과 정답은 세션
> 덤프에서 회수한 것만 적었고, 기록에 없는 내용은 추가하지 않았다. 덤프에 HTML
> 엔티티로 이스케이프돼 있던 부등호(`&gt;` 등)는 원래 기호로 되돌렸고, 화살표는
> ASCII `->`로 통일했다.

## 게이트 목록

게이트는 diff 2건에 대해 두 번 있었고, 계획 게이트는 없었다.

| 번호 | 대상 | 시도 | 최종 판정 |
|---|---|---|---|
| G1 | diff 01 - `ReactiveAdapterRegistryTests`에 테스트 2건 추가(red 1 + 대칭 기준점 1) | 2 | pass (통과 처리, 2/2) |
| G2 | diff 02 - `MutinyRegistrar`의 empty-value 공급자 1줄 | 2 | pass (통과 처리, 2/2) |

계획 게이트가 없는 것은 착수 흐름 때문이다. 분석(`analysis.md`)을 먼저 제시하고
그 자리에서 spec 6칸 요지를 붙여 "진행할까요?"로 물었고, 사용자가 "진행해보자"로
합의한 뒤 곧바로 diff 01로 갔다. 두 게이트 모두 1회차 fail, 2회차 통과 처리로 같은
패턴이었다.

**이 PR이 자기완결 패킷 재질문(신형식)을 실제로 적용한 첫 사례다.** 이전 형식은
"정답을 주지 말고 다시 볼 파일:줄만 지목"이었는데(#37235), 이번에는 fail 시
**원래 질문 재게시 + 이전 답변 판정표 + 관련 코드 전부 인라인 + 힌트**를 한 메시지에
담아 그 메시지 하나만 읽고도 재답변할 수 있게 했다. 두 게이트 모두 그 패킷 이후
시도 2에서 본질에 도달했다.

---

## G1 - diff 01 (테스트 2건 추가)

대상 diff: `ReactiveAdapterRegistryTests`의 `Mutiny` 중첩 클래스에 `fromNullValue`와
`toUniFromEmptyPublisher` 추가. 실행 결과 **7 tests, 1 failed** - `fromNullValue`가
5초 타임아웃(`Timeout on blocking read`)으로 red, `toUniFromEmptyPublisher`는
**fix 전에도 green**(spec의 `[구현 검증]` 가정 2가 실행으로 해소됐다).

**질문** (원문)

> **diff 01 이해 게이트** - 자기완결 플로우 브리핑입니다.
>
> (테스트 2건 + `ReactiveAdapter.toPublisher` + `MutinyRegistrar`의 공급자 +
> 역방향 등록 람다 + Mono 형제 등록을 코드 블록으로 인라인 제시)
>
> **질문 2개** (주관식):
> 1. `toUniFromEmptyPublisher`가 **fix 전에도 green인 이유**는 무엇이고, 그 green이 "수정값을 `nullItem()`으로 골라야 한다"는 선택을 어떻게 정당화하나요? (힌트: 왕복 - 빈 Publisher를 Uni로 바꿨다가 다시 Publisher로 바꾸면 무엇이 나와야 대칭인가)
> 2. `fromNullValue`에서 단언이 "예외"가 아니라 **`block()` 결과 null**을 기대하는 이유와, 지금 red가 나는 정확한 사슬 - (1)에서 무엇이 들어가고 (2)의 변환을 거쳐 `Mono.block(FIVE_SECONDS)`가 왜 값도 완료도 못 받는지 - 를 위 스니펫의 줄을 짚어 설명해 주세요.

**시도 1 - 답변** (사용자 원문)

> 애초에 1번에서 나오는 결과가 Uni객체이며 Mono가 아니라 그런거잖아? 이때 Uni랑 Mono타입에 대한 콘셉 설명 문서가 필요하겠네 이건 추가해야겠다. 아
> 이건 uni로 바꿔서 처리하고 유니를 Publisher로 변환했다가 유니로 해놓으면 타겟 자체가 null로 반환되니깐 문제가 없다는거네. 유니여도 문제가 없는건 애초에 퍼블리셔가 유니 객체로 반환해서 유니의 null인 상태로 반환되고 있으니 그런거구나.
> 그런데 이때 Mono가 들어가면 Mono가 null로 와야되는데 이때도 uni로 바꾸는게 문제라는 거 아니야?
> block은 Mono객체를 확인한다는거구나. 모노 객체가 아니라 유니 객체라 문제가 발생한다는거잖아?

**판정 1** - verdict: fail

판정 워커 결과 원문(발췌):

> Q1 - 불충분. 방향 감각("퍼블리셔 -> 유니로 갔을 때 유니가 null 상태로 온다")은 어렴풋이 잡았으나, 게이트가 요구한 두 가지가 빠졌습니다.
> - (a) `toUniFromEmptyPublisher`가 **fix 전에도** green인 이유를 "Uni 객체라서/타입이 Uni라서"로 설명했는데, 이 테스트가 Uni를 받는 건 `fromPublisher`의 정의상 당연한 것이라 green의 이유가 되지 못합니다. green을 만드는 주체가 **어느 코드 경로**인지(그 경로는 이번에 고치려는 `uniDesc`의 empty-value 공급자와 무관하다는 점 포함)를 지목해야 합니다.
> - (b) 그 사실이 **왜 수정값 `nullItem()` 선택의 근거가 되는지**(왕복 대칭 논리)가 답변에 없습니다. 두 방향 변환이 "빈 것"을 각각 무엇으로 표현하느냐를 나란히 놓고, 한쪽만 다른 표현을 쓰면 무엇이 깨지는지의 형태로 진술이 필요합니다.
>
> Q2 - 오답. 핵심 오해를 먼저 정정합니다(정답은 비노출).
> - "block은 Mono 객체를 확인하는 것 / 모노가 아니라 유니 객체라서 문제"는 **실측과 어긋납니다**. `fromNullValue`는 세 줄짜리이고, 두 번째 줄이 `assertThat(target).isInstanceOf(Mono.class)`입니다. 이 줄이 실패했다면 세 번째 줄의 `block`은 실행조차 되지 않습니다. 그런데 log.md에 기록된 실패는 `block`에서 난 `IllegalStateException: Timeout on blocking read`입니다 - 즉 **타입 단언은 통과했고, target은 진짜 Mono입니다**. `toPublisher`는 Uni를 Mono로 정상 변환합니다. 실패 원인은 타입 불일치가 아닙니다.
> - 따라서 다시 답해야 할 것: target이 정상적인 Mono인데도 `block(5초)`이 값도 완료도 못 받은 이유. (...) 타입 이야기가 아니라 "신호가 오느냐 안 오느냐"의 이야기입니다.
> - 또한 "왜 예외가 아니라 `block()==null`을 기대하는가"에 대한 답이 아직 없습니다. 이 어댑터가 `singleOptionalValue`로 등록돼 있다는 사실이 무엇을 선언하는 것인지, 그리고 형제 타입들(Mono·Maybe 등)이 같은 자리에서 어떻게 동작하는지를 근거로 삼으면 됩니다.
>
> 참고로 사용자가 요청한 "Uni vs Mono 개념 설명 문서" 필요성 자체는 타당한 판단이나, 이번 결함은 두 타입의 차이가 아니라 **한 타입 안에서 '빈 값'을 무엇으로 표현했는가**의 문제이므로, 재답변은 타입 대조가 아니라 신호 흐름으로 해 주세요.

**재질문 - 자기완결 패킷** 이 게이트에서 처음 쓴 형식이다. 정답은 주지 않되 다음
넷을 한 메시지에 담았다.

1. 원래 질문 재게시(Q1·Q2).
2. 이전 답변 판정표 - 어느 문장이 맞았고 어느 문장이 틀렸는지를 행으로 나눔.
   특히 "Mono가 아니라 Uni 객체라서 block이 실패"에 **틀림** 표시와 함께,
   `fromNullValue`가 3줄이고 둘째 줄이 통과했다는 핵심 정정.
3. 관련 코드 전부 인라인 - 테스트 두 건에 (A)~(E) 라벨을 붙이고,
   `ReactiveAdapter.toPublisher` 본문에 (1)(2) 주석, `MutinyRegistrar`의 공급자와
   역방향 람다, 형제 `Mono` 등록까지 한 화면에 모음.
4. 힌트 - Q1은 "빈 Publisher -> (fromPublisher) -> ??? -> (toPublisher) -> 다시
   Publisher가 됐을 때 무엇이 나와야 출발점과 같아지나", Q2는 "`block`은 item이 오면
   그 값, onComplete만 오면 null, 아무 신호도 없으면 타임아웃 세 갈래인데 지금 사슬은
   어디로 떨어지나".

**시도 2 - 답변** (사용자 원문)

> 아 1번에서 유니 자체는 결국 nothing인 경우 그냥 publisher에 아무것도 안들어가니 완료가 됬는지 유무를 알 수가 없는데 nullitem이면 대기열 자체에 완료로 null이 들어가니 끝났다는걸 받을 수 있다는거구나.그래서 대기할떄 무사히 타겟 객체가 받으니 문제가 없으니 5초동안 막고 그 내부 객체가 null인지 확인할 수 있으니,
> 2. block일떄 item이 오면 그 값 자체라 문제없을텐데 이때 nothing일 경우 객체 Uni.createFrom().nothing()이니깐, Mono는 받을 수 없어서 그런 거 아니야? 결국 모노에 대해서 item 자체에서 값이 없으니 타임아웃이 나오는거고 null로 나와줘야 singleOptionalValue라는 여기서 null item을 넣어서 Mono에서 null이라고 전달 가능한 형태로 전달해야된다는거구나.

**판정 2** - verdict: pass (시도 2/2 통과 처리)

맞은 것: "nothing이면 완료됐는지 알 수 없고, nullItem이면 '끝났다'는 걸 받을 수
있다" - **무신호(no signal)와 완료 신호(onComplete)의 구분**. 판정 워커가 "이게 이
결함의 본질이고, 이번에 정확히 짚었다"고 인정했다.

Q1 정답 확정 - **green의 주체 경로.** `ReactiveAdapter.fromPublisher`(L120-122)는
`fromPublisherFunction`만 호출한다. 이 프로젝트가 쓰는 Mutiny는
**1.10.0**(framework-platform.gradle:56)이라 `MutinyRegistrar`의 **else 분기(Mutiny 1,
L399-407)**가 활성이고, 그 람다는

```java
publisher -> io.smallrye.mutiny.Uni.createFrom().publisher(publisher)   // L403
```

이다. 여기엔 `emptySupplier`가 **전혀 등장하지 않는다.** 고칠 `nothing()`(L378)은
오직 `ReactiveAdapter.toPublisher`가 `source == null`일 때 `getEmptyValue()`를 부르는
경로(L109-111)에서만 읽힌다. 즉 이 테스트는 **결함 줄을 지나가지 않으므로** fix
전에도 후에도 green이고, red가 아니라 **회귀 가드 + 대칭 기준점**이 존재 이유다.
(답변의 "대기열에 null이 들어가니 완료를 받는다"는 서술은 `fromNullValue`(Q2) 쪽
이야기이지, 이 테스트가 green인 이유는 아니다.)

Q1 정답 확정 - **왕복 대칭이 `nullItem()` 선택의 논리.**

```
빈 Publisher --fromPublisher(L403)--> Uni(= null item으로 즉시 완료)   <- Mutiny가 이미 이렇게 정의함
Uni(null item) --toPublisher(L402)--> 아이템 없이 onComplete = 빈 Publisher   <- 되돌아옴
```

`toUniFromEmptyPublisher`는 왼쪽 화살표를 **실행으로 고정**한다("빈 Publisher의
Uni측 표현 = null item 완료"). 그러면 "이 어댑터가 빈 값을 만들어야 할 때 쓸 Uni"는
그 고정된 표현과 같아야 왕복이 닫힌다 -> `nullItem()`. `nothing()`은 왕복의
**절반만 성립**한다.

Q2 정정 (a) - **"null이 Mono로 전달된다"가 아니다.** Reactive Streams는
`onNext(null)`을 **금지**한다. 그래서 Mutiny의 Uni -> Publisher 변환은 null item을
"**아이템 방출 없이 onComplete**"로 매핑하고(`UniToMultiPublisher:92`),
`Mono.block()`은 **빈 정상 완료**를 받으면 `null`을 **반환**한다. 즉 null이라는 값이
파이프를 타고 이동한 게 아니라, "비어 있는 정상 완료"의 Java 레벨 표현이 null인
것이다. **null item Uni -> 빈 Publisher -> block()==null, 이 세 표현이 같은 사태의
세 표기다.**

Q2 정정 (b) - **"Mono가 받을 수 없어서"가 아니다.** `nothing()`일 때도 Mono는
정상적으로 만들어지고 정상적으로 구독한다. 문제는 **받을 신호 자체가 발생하지 않는
것**이다. 실패 원인은 타입이 아니라 시간(타임아웃)이다.

Q2 정답 확정 - **왜 예외가 아니라 null 기대인가.** `uniDesc`는 `singleOptionalValue`로
등록돼 있고(L376), 이 팩토리는 `emptySupplier`를 non-null로 채운다
(ReactiveTypeDescriptor L148-150) -> `supportsEmpty() == true`(L91-93) = "이 타입은
값 없이 완료될 수 있다"는 **선언**이다. `toPublisher`의 javadoc(L103-104)도 "source가
null이면 getEmptyValue()를 쓴다"고 명시한다. 즉 `toPublisher(null)`은 오류 경로가
아니라 **정식 계약 경로**이고, 형제 등록(`Mono::empty`·`Maybe::empty`·
`Completable::complete`)과 같은 "빈 완료" 계약을 따라야 한다.

Q2 정답 확정 - **red 사슬 (신호 관점).**

1. `getAdapter(Uni.class).toPublisher(null)` -> `ReactorAdapter.toPublisher`(L260-263)가
   `super.toPublisher` 호출
2. `ReactiveAdapter.toPublisher` L109-110: source==null -> `getDescriptor().getEmptyValue()`
3. `ReactiveTypeDescriptor.getEmptyValue()` L99-104 -> `emptySupplier.get()` =
   **`Uni.createFrom().nothing()`(L378)** = UniNever
4. `toPublisherFunction`(L402) `uni.convert().toPublisher()` -> 무신호 Publisher
5. `ReactorAdapter`가 `isMultiValue()==false`이므로 `Mono.from(publisher)`로 감싼다
   -> **`isInstanceOf(Mono.class)` 단언은 통과**(여기서 안 깨진다)
6. `block(FIVE_SECONDS)` - 구독은 성립, 신호 0건 -> 5초 후
   `IllegalStateException: Timeout on blocking read for 5000 ms` -> **red**

green 이후: 3에서 `nullItem()` -> item=null Uni -> 4에서 onNext 없이 onComplete만
-> 6에서 `block()`이 즉시 `null` 반환 -> 단언 통과.

---

## G2 - diff 02 (fix 1줄)

대상 diff (`ReactiveAdapterRegistry.java` L376-378):

```java
// before
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
        io.smallrye.mutiny.Uni.class,
        () -> io.smallrye.mutiny.Uni.createFrom().nothing());
```
```java
// after
ReactiveTypeDescriptor uniDesc = ReactiveTypeDescriptor.singleOptionalValue(
        io.smallrye.mutiny.Uni.class,
        () -> io.smallrye.mutiny.Uni.createFrom().nullItem());
```

적용 결과 `ReactiveAdapterRegistryTests` 전체 green(Mutiny 그룹 7/7, `fromNullValue`
red -> green)이고, spring-core 전체 스위트는 백그라운드로 돌리는 중에 질문했다.

**질문** (원문)

> **diff 02 이해 게이트** (마지막, 짧게 - 필요한 코드는 위와 직전 패킷에 전부 있습니다):
> 1. 이 1줄이 `fromNullValue`를 green으로 만드는 사슬을 **신호 관점 한 문장**으로 요약해 주세요 (nullItem -> ? -> block이 ?를 받아 ? 반환).
> 2. 이 수정이 **기존 비-null Uni 사용자에게 아무 영향이 없는 이유**는? - empty-value 공급자가 읽히는 유일한 조건이 무엇인지로 답해 주세요.

**시도 1 - 답변** (사용자 원문)

> 이때 nothing과 nullItem()의 동작 방식과 어떤 객체를 생성하는지 별도 나중에 스터디 문서쪽 만들떄 필요해보이고,
> 결국 nullItem은 io에서 block객체가 Descriptor에 대해서 null을 받아 null을 받아 받은 값이 null이라고 리엑티브한테 제대로 받게 된거고,
> 2번에서 기존의 nothing 자체는 uni의 null객체 그 자체가 문제없었고 저렇게 바꿔도 가져오는 값은 null이라 문제 없는거지,
> 기존에 nothing의 uni의 null값은 block으로 mono의 null읇 받은게 아니니깐, 문제가생겼던거구나

**판정 1** - verdict: fail

판정 워커 결과 원문(발췌):

> Q1 (부족) - 결론("block이 null을 받는다")은 맞지만 요구한 **사슬의 중간 고리**가 비어 있습니다.
> - `nullItem()`이 만든 Uni가 Publisher로 변환됐을 때 구독자에게 **어떤 신호가 몇 번 오는지**를 한 마디도 지목하지 않았습니다. diff 01 게이트에서 본인이 정리했던 "null은 전달이 아니라 빈 완료의 표현(RS는 onNext(null) 금지)"이 여기서 다시 쓰여야 하는데, 그 항이 빠진 채 "null을 받아 null을 받아"로 결과만 두 번 반복됩니다.
> - 용어 오류: "block객체가 Descriptor에 대해서 null을 받아" - Descriptor(정확히는 `getEmptyValue()`)가 내놓는 것은 null이 아닙니다. L378에서 람다가 무엇을 반환하는지, 그 반환값이 L110에서 `source`에 대입된 뒤 L112에서 무엇에 넘겨지는지 다시 짚으세요.
> - 마지막 문장("nothing은 block으로 mono의 null을 받은 게 아니니까")은 방향은 맞으나, `nothing()` 쪽이 **무엇을 안 보내서** block이 5초 타임아웃까지 갔는지를 신호 이름으로 말해야 대비가 성립합니다. 또 "nothing 자체는 uni의 null객체 그 자체"라는 표현은 틀렸습니다 - `nothing()`이 만드는 것은 값이 null인 Uni가 아닙니다.
>
> Q2 (부족) - **결과만** 답하고 요구한 **유일 조건**을 지목하지 않았습니다.
> - "바꿔도 가져오는 값은 null이라 문제없다"는 empty-value 경로 안에서의 결과 진술입니다. 질문은 "비-null Uni 사용자에게 이 1줄이 애초에 **닿지 않는** 이유"였고, 답은 코드상의 특정 분기 한 줄로 지목돼야 합니다.
> - 재확인할 것: `ReactiveAdapter.java` L108-113 전체를 다시 읽고, (1) empty-value 공급자가 호출되는 지점이 몇 줄인지 (2) 그 줄에 도달하는 조건이 무엇인지 (3) `fromUni` 테스트(비-null source)와 `fromNullValue` 테스트(null source)가 같은 메서드에서 각각 어느 줄을 지나는지 - 이 셋을 문장 하나로 묶어 답하세요.
>
> 참고로 "nothing() vs nullItem()이 각각 어떤 객체를 만드는가"를 스터디 문서로 빼자는 판단은 타당합니다 - 다만 이 게이트는 그 내부 구현이 아니라 **신호 수준의 사슬**만 요구하므로, 문서 작업 없이 위 두 항목만 다시 답하면 됩니다.

**재질문 - 자기완결 패킷 (2회차)** G1과 같은 형식이되, 관련 코드를 **더 좁혀서**
제시했다. `ReactiveAdapter.toPublisher` 본문 여섯 줄에 "(조건)", "공급자가 호출되는
'유일한' 지점", "반환값 = Uni 객체 (null 아님!)" 주석을 직접 달았고, `fromUni`와
`fromNullValue`가 그 메서드에서 각각 어느 줄을 지나는지를 주석으로 표시했다.
힌트는 **빈 칸 채우기** 형태였다.

> - **Q1**: "`nullItem()`이 만든 Uni를 L112가 Publisher로 바꾸면 구독자에게 [___] 신호가 [_]회 온다 -> `block()`은 [___]을 받으면 [___]을 반환한다."
> - **Q2**: "이 수정이 비-null 사용자에게 무영향인 이유 = L110은 [___]일 때만 실행되는데, 비-null 소스는 [___]" 형태로 한 문장이면 됩니다.

**시도 2 - 답변** (사용자 원문)

> Q1에서 응답이 왔다고 완료가 되었다고 신호가 1회 오고 신호를 받으면 이때 아 null item Uni 객체를 받아 그걸 보고 null을 반환하는구나,
> Q2에 대해서, source가 null일때만 해당 동작이 진행해서 비-null인 경우는 해당 소스가 uni객체가 되고 그걸 잘 반환해서 넘어가니깐 문제 없는게 맞다는거거네

**판정 2** - verdict: pass (시도 2/2 통과 처리)

Q1 - "완료 신호가 1회 온다"는 핵심을 잡았다. **미세 정정 한 개가 정답으로
확정됐다**: block이 받는 것은 "null item Uni 객체"가 아니라 **아이템 없는 정상
완료(onComplete) 신호**다. Uni 객체는 `ReactiveAdapter.toPublisher`의
L110(`source = getDescriptor().getEmptyValue()`)에서 만들어져
L112(`toPublisherFunction.apply(source)`)로 넘어가는 **그 두 줄 사이에만 존재하고**,
변환이 끝난 뒤 구독자(block)에게 도달하는 것은 Uni 인스턴스가 아니라 신호뿐이다.
사슬 전체:

```
nullItem() Uni -> UniConvert.toPublisher() 변환 -> 구독 시 onNext 없이 onComplete 1회
               -> Mono.block()이 아이템 없는 완료를 받고 null 반환
```

Reactive Streams는 onNext(null)을 금지하므로, 빈 정상 완료의 Java 표현이 곧 null이다.
수정 전 `nothing()`은 UniNever여서 이 사슬의 세 번째 칸에 **아무 신호도 오지 않아**
5초 타임아웃으로 끝났다 - red의 정체는 타입 불일치가 아니라 신호 부재였다.

Q2 - 정답 도달, 인정. `toPublisher(@Nullable Object source)`는 L109
`if (source == null)`일 때만 L110에서 descriptor의 empty-value 공급자를 호출한다.
비-null Uni가 들어오면 그 분기를 통째로 건너뛰고 L112로 직행해 사용자가 준 Uni
자체가 변환된다. 즉 **이번 수정이 관측되는 유일한 경로가 `source == null` 분기이므로,
기존 비-null 경로의 동작은 정의상 변할 수 없다.**

---

## 게이트 중 보조 질문

게이트 답변과 별개로 사용자가 던진 요청들이다. 판정 대상은 아니었고, 둘 다 산출물로
이어졌다.

### 1. Uni와 Mono 개념 문서를 만들자 (G1 시도 1 안에서)

> 이때 Uni랑 Mono타입에 대한 콘셉 설명 문서가 필요하겠네 이건 추가해야겠다.

그 자리에서 개념 문서 작성 워커를 판정 워커와 **병렬로** 띄웠고,
`concepts/uni-vs-mono-reactive-types/`가 이 요청에서 태어났다. 워커가 빌드된
`spring-core` 클래스에 Mutiny 1.10.0 + Reactor 3.8.7을 물려 실행 실증까지 해서,
문서가 문서 인용이 아니라 실측 매트릭스를 갖게 됐다.

```
Uni   getEmptyValue() = UniNever      -> block(600ms) 타임아웃   (H3 재현)
Mono  toPublisher(null)               -> null (정상 완료)
Multi toPublisher(null)               -> null (정상 완료 - empty() 라 올바름)
Uni   fromPublisher(Mono.empty())     -> null item Uni          (왕복 비대칭 확인)
Uni   toPublisher(nullItem())         -> null (완료)            (수정안의 대칭 확인)
```

판정 워커는 같은 자리에서 **범위 정정**도 했다. "이번 결함은 두 타입의 차이가 아니라
**한 타입 안에서 '빈 값'을 무엇으로 표현했는가**의 문제이므로, 재답변은 타입 대조가
아니라 신호 흐름으로 해 달라" - 개념 문서의 필요성은 인정하되 게이트의 축은 흐리지
말라는 구분이었다.

이 워커에게서 나온 부수 기록이 둘 더 있다. 하나는 **lazy 모드의 실무적 한계**다.
워커가 개념 문서를 Write한 순간 `PENDING_GATE=1`이 서고, 이어서 하려던 `index.md`
행 추가와 분량 축소 편집이 전부 gate-guard에 막혔다. 워커는 우회하지 않고 "추가해야
할 행"과 막힌 사실을 보고로 돌려줬고, 그 행은 메인이 게이트 통과 후 반영했다.
다른 하나는 **확신 낮은 서술의 자진 신고**다 - WebFlux 행 시나리오는 코드 추적이지
서버를 띄운 실행이 아니라는 점, 신호 모델 비교표의 Uni 열은 타입 형태를 읽은 것이지
런타임 프로브가 아니라는 점을 워커가 스스로 표시해 보고했다.

### 2. `nothing()`과 `nullItem()`이 만드는 객체를 문서로 (G2 시도 1 앞부분)

> 이때 nothing과 nullItem()의 동작 방식과 어떤 객체를 생성하는지 별도 나중에 스터디 문서쪽 만들떄 필요해보이고,

판정 대기 중에 log의 **문서화 백로그**로 기록했고, 이 PR 문서 세트의
[analysis.md 2.5절](analysis.md)이 그 요청의 결과다. 요점만 옮기면
`nothing()`은 `UniNever.INSTANCE`(구독 시 `onSubscribe(DONE)` 한 번, 그 뒤 무신호)를,
`nullItem()`은 `UNI_OF_NULL` = `UniCreateFromKnownItem<>(null)`(구독 직후
`onItem(null)`)을 돌려주며, 둘 다 상태가 없어 싱글턴을 공유한다.

판정 워커는 이 요청에 대해 **게이트의 요구 범위와 구분**해 줬다. "그 판단은
타당하지만 이 게이트는 내부 구현이 아니라 신호 수준의 사슬만 요구하므로, 문서 작업
없이 두 항목만 다시 답하면 된다" - 학습 욕구와 게이트 통과 조건을 섞지 않게 한
지적이다.

---

## 반복된 오해 패턴

두 게이트에서 같은 종류의 착오가 반복됐다.

1. **"타입이 틀렸다"로 신호 문제를 설명함** - G1 시도 1의 "모노 객체가 아니라 유니
   객체라 문제가 발생한다"가 그것이다. 이 결함은 변환이 전부 성공하고 신호만 오지
   않는 것이므로, 타입 어휘로는 설명이 안 된다. 판정 워커가 "3줄 중 둘째 줄이
   통과했다"는 실측으로 이 오해를 깼는데, **테스트가 몇 줄이고 어디서 깨졌는지를
   보는 것**이 그 자체로 진단 도구였다.
2. **"null이 전달된다"와 "빈 완료가 온다"를 섞음** - 두 게이트 모두에서 나왔다.
   Reactive Streams가 `onNext(null)`을 금지한다는 사실을 알면 "null이 흐른다"는
   그림이 불가능해지고, `block()`의 반환값 null은 **관측 결과의 표기**일 뿐임이
   드러난다. 이 구분이 없으면 왜 `nullItem()`이 "빈 값"인지 설명할 수 없다.
3. **결과만 말하고 경로를 지목하지 않음** - G1의 "green이 되는 이유", G2의 "비-null
   무영향의 이유"가 둘 다 그랬다. 두 질문 모두 답이 **코드 한 줄**(각각 L403, L109)로
   지목돼야 하는 것이었는데, 답변은 그 줄 대신 결과 상태를 서술했다. 판정 워커가
   두 번 다 "어느 코드 경로인지 지목하라"로 되돌려 보냈다.
4. **객체와 신호를 같은 층위로 봄** - G2 시도 2의 "null item Uni 객체를 받아"가
   그것이다. Uni 객체는 `toPublisher`의 두 줄 사이에만 존재하고 구독자에게 가는
   것은 신호뿐이다. 리액티브 코드에서 "무엇이 어디까지 흘러가는가"를 층으로 나눠
   보는 습관이 필요한 자리다.
5. **"공급자가 null을 준다"** - G2 시도 1의 "Descriptor에 대해서 null을 받아"가
   그것이다. `getEmptyValue()`는 오히려 `Assert.notNull`로 null을 **금지**한다
   (ReactiveTypeDescriptor L102). 공급자가 주는 것은 Uni 객체이고, null은 그 Uni가
   품은 item의 값이자 최종 관측값이다 - 같은 단어가 세 층에서 다른 것을 가리킨다.

## 교훈

이 기록이 남긴 것은 결함의 한 문장 요약, 새 재질문 형식의 효과, 게이트가 산출물을
늘린 사례, 그리고 워커가 자기 한계를 보고한 방식 넷이다.

- 이 결함의 학습 핵심은 한 문장으로 압축된다: **"빈 값을 지원한다"는 선언과 "그 빈
  값이 실제로 완료한다"는 사실은 서로 다른 자리에서 정해지고, 둘을 맞추는 검사는
  없다.** 두 게이트의 질문이 전부 이 문장의 다른 각도였다 - G1은 그 빈 값이
  무엇이어야 하는가(왕복 대칭), G2는 그 빈 값이 언제 읽히는가(유일 분기)였다.
- **자기완결 패킷이 효과가 있었다.** #37235에서 쓰던 "다시 볼 파일:줄만 지목" 방식은
  사용자가 파일을 열어 읽는 동작을 전제하는데, 이번 결함은 코드가 네 파일에 흩어져
  있어 그 방식이면 왕복이 길어질 상황이었다. 관련 코드를 한 메시지에 모으고 라벨을
  붙이자 두 게이트 모두 시도 2에서 본질에 도달했다. 다만 **정답은 여전히 주지
  않았다** - 준 것은 코드와 빈 칸이다.
- **G2에서 힌트를 빈 칸 채우기로 바꾼 것**이 특히 잘 들었다. "구독자에게 [___]
  신호가 [_]회 온다"는 형태가 답변에서 빠져 있던 중간 고리를 정확히 그 자리에
  요구했고, 시도 2의 답변이 "신호가 1회 온다"로 곧장 그 칸을 채웠다.
- **게이트에서 나온 질문이 산출물을 늘렸다.** Uni/Mono 개념 문서 한 편이 G1에서,
  `nothing()`/`nullItem()` 객체 해설 절이 G2에서 나왔다. 둘 다 게이트 통과에는
  필요 없던 것이고, 그래서 판정 워커가 "게이트는 이것까지 요구하지 않는다"고 범위를
  그어 줬다 - 학습 욕구는 문서로, 통과 조건은 게이트로 분리한 셈이다.
- **워커가 막힌 것을 우회하지 않고 보고했다.** 개념 문서 워커는 `PENDING_GATE`에
  막힌 두 편집을 포기하고 "추가할 행"과 막힌 사유를 텍스트로 돌려줬으며, 실행으로
  확인하지 않은 서술 넷을 스스로 낮은 확신으로 표시했다. 게이트 기록에 "누가 무엇을
  확인했는가"만큼이나 "누가 무엇을 확인하지 못했다고 말했는가"가 남을 필요가 있다.
