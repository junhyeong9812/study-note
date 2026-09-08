# PR #37153 — 이해 게이트 기록

> 출처: 세션 1761423a (2026-08-19 09:01~10:15), 작업 폴더
> `docs/plans/2026-08-19/c14-attributemethods-enum-array/`. 모드는 lazy —
> 계획과 매 diff마다 주관식 이해 게이트를 통과해야 다음 단계로 넘어간다.
> 답변은 사용자 원문 그대로(오타 포함), 판정과 정답은 대화·판정 워커 출력에
> 기록된 것만 옮긴다. 게이트 규칙상 1회차 fail이면 정답을 노출하지 않고
> 부족점만 지적해 재질문하며, 2회차는 fail이어도 지적 후 통과 처리한다.
> 판정 원문 6건은 전부 회수했다 — 4건(계획 2회차, diff 01 1·2회차, diff 02 1·2회차)은
> 세션 로그의 task-notification 결과에서, 2건(계획 1회차, diff 03 1회차)은 세션 로그에
> notification이 남지 않아 판정 워커의 서브에이전트 로그
> (`subagents/agent-a9beb1510643216ec.jsonl`, `agent-a363c37b0c3235450.jsonl`)에서 직접 회수했다.

## 게이트 목록

게이트는 계획 1건과 diff 3건으로 모두 네 번 있었고, 마지막 하나만 1회차에 통과했다.

| 번호 | 대상 | 시도 | 최종 판정 |
|---|---|---|---|
| G1 | 계획 (결함 메커니즘과 fix 방향) | 2 | fail-통과처리 (2/2) |
| G2 | diff 01 (red 테스트 5건) | 2 | fail-통과처리 (2/2) |
| G3 | diff 02 (fix 1줄 + 검증 결과) | 2 | fail-통과처리 (2/2) |
| G4 | diff 03 (리뷰 반영 — 개명 + 음성 가드) | 1 | pass |

판정 4회 중 pass 1건, fail 1건(1회차), fail-통과처리 3건(2회차). 게이트 밖에서
사용자가 요청한 학습 개입은 3건(CLI 재현 요청, 용어 질문, "놓친 부분 알려줘")이며
각각 아래 해당 게이트에 기록했다.

## G1 — 계획 이해 게이트

**질문** (원문)

> 이 버그가 **왜** 문제가 되는지(어떤 상황에서 사용자가 무엇을 겪는지), 그리고
> 이번 fix가 **어떤 메커니즘으로** 그것을 막는지 본인 말로 설명해 주세요.

**시도 1 — 답변** (사용자 원문)

> 우선 단순하게 보면 class 타입과 클래스타입 배열에 대해서는 타입탓페이런츠익셉션이
> 발생하는데 이넘에 대해서는 이넘 배열 속성은 예외에 대한 확인을 하고 있지 않는게
> 문제라는건데,
> 그렇다면, 그렇게 해서 인터페이스 내에 타입배열과 타입 컨텐츠에 대해서 이넘인지
> 확인하도록 추가적으로 확인 포인트를 늘리겠다는거잔항? 이때 실제 실패할떄 조용히
> 실패되는 이넘 클래스를 직접 보여줄래? 실제 이 문제가 어디서 어떤상황에서 나오는 지
> 그리고 이게 이렇게 나오면 안되는 이유를 cli상으로 표현해줄래?

**판정 1** — fail (1/2). 판정 워커 원문:

> {fail, 빠진 지점(무엇이 검사에서 누락됐나)은 짚었지만, 사용자 영향 — 어떤 상황에서
> 무엇을 겪게 되는지 — 을 본인 설명 대신 역질문으로 넘겼고, fix 후 이 플래그가 어떤
> 경로로 그 문제를 막는지(플래그가 true가 되면 무슨 일이 일어나는가)에 대한 설명이
> 없음. 이 두 가지를 본인 말로 채우면 됨}

**학습 개입 (게이트 밖)**: 답변에 섞인 CLI 재현 요청을 그대로 수행해, 스크래치패드에
`Color` enum v1(RED/GREEN/BLUE)으로 컴파일한 클래스를 BLUE가 제거된 v2 classpath로
실행하는 데모를 만들었다. 출력 요지:

```
[1] JDK 직접 접근 — 단일/배열 모두 일관되게 EnumConstantNotPresentException (JDK는 대칭)
[2] Spring MergedAnnotations 스캔
    단일 enum 속성:  isPresent(SingleMarker) = false   <- probe가 감지, 필터링 + warn 로그
    enum 배열 속성:  isPresent(ArrayMarker)  = true    <- probe 누락, 오염된 annotation 통과
[3] 통과한 annotation의 속성을 읽는 순간
    asMap() = {value=java.lang.EnumConstantNotPresentException: Color.BLUE}
    getEnumArray("value", Color.class)  -> raw EnumConstantNotPresentException
    synthesize().value()                -> raw EnumConstantNotPresentException
```

`[3]`의 `asMap()` 오염(예외 객체가 값으로 들어간 맵이 조용히 반환됨)은 라운드5
findings에도 없던 추가 발견이었다.

**시도 2 — 질문** (2회차, 원문)

> 위 재현을 바탕으로, ① 이 버그로 사용자가 실제 어떤 상황에서 무엇을 겪게 되는지,
> ② 플래그가 true가 되면 어떤 경로로 그 문제가 막히는지 본인 말로 설명해 주세요.

**시도 2 — 답변** (사용자 원문)

> 아 어노테이션이 붙은 이넘 타입 내에 배열 객체 상수가 있을떄 이넘 타입 내에 배열
> 속성일 경우 probe에서 isPresent() <- 이건 어떤걸 표현하는 메서드야? 왜 이메서드가
> false여야되는거지?
> 이떄 어노테이션처리를 할때 그래서 결국 컴포넌트 스캔할때 어노테이션을 스캔하면
> 과정에서 문제가 있는 지 해당 내용이 문제가 되면 warn록 및 피렅링 해야되는데 true가
> 되면 해당 작업을 하지 않는다는거잖아? 정상으로 판단해서? 그리고 [3]의 경우 여기서만
> 쓰는 메서드인지 아니면 다른 곳에서도 쓰는 메서드라 고칠 필요가 있는 지알려줄래?

**판정 2** — fail-통과처리 (2/2). 판정 워커 원문:

> fail-통과처리, 지적:
> - 방향이 반대입니다. 플래그(canThrowTypeNotPresentException)가 true가 되면
>   probe(실호출 검사)를 "하지 않는" 것이 아니라 **하게 됩니다** — probe에서
>   EnumConstantNotPresentException이 나면 canLoad=false가 되어 스캔 단계에서 그
>   annotation을 warn 로그와 함께 제외합니다. 버그는 enum 배열 속성에서 이 플래그가
>   false라 probe가 스킵되어 오염된 annotation이 정상으로 통과하는 것입니다.
>   (isPresent()는 MergedAnnotations 조회에서 "그 annotation이 존재하는가"를 반환하는
>   메서드 — 오염된 annotation은 스캔에서 걸러져 false가 되는 것이 정상 설계입니다.)
> - ① 사용자 영향 설명이 빠졌습니다: 구버전 enum 상수를 참조하는 annotation이 걸러지지
>   않고 통과하여, 나중에 asMap()에 예외 객체가 값으로 섞이거나(silent corruption)
>   getEnumArray/synthesize().value() 호출 시점에 raw EnumConstantNotPresentException이
>   사용자 코드로 누출됩니다.
> - [3]의 메서드(getEnumArray 등)는 다른 곳에서도 쓰이는 공용 경로지만 고칠 대상이
>   아닙니다 — fix는 그 앞단(스캔 필터링)이 배열에도 작동하게 플래그 계산식만 고치는
>   것입니다.

**정답 정리**

- `isPresent()`는 `MergedAnnotations.from(대상).isPresent(X.class)` — "이 클래스에
  annotation X가 달려 있는가"를 묻는 진입 메서드다. 여기서 false는 "annotation이
  없다"가 아니라 "로드 불가로 판정되어 스캔 결과에서 제외됐다"는 뜻이며, 반쯤 깨진
  annotation을 "있다"고 보고하면 그 보고를 믿고 값을 읽는 후속 코드가 전부 터지기
  때문에 그것이 Spring의 설계 결정이다.
- 인과 방향은 한 방향이다. 현행: 플래그 false -> probe 스킵 -> 예외를 관측할 기회 자체가
  없음 -> `canLoad` = true(오판) -> 오염된 annotation 통과. fix 후: 플래그 true -> probe
  수행 -> `EnumConstantNotPresentException` 관측 -> `canLoad` = false -> warn 로그 + 필터링.
- `asMap()`/`getEnumArray`/`synthesize()`는 결함이 아니라 하류 피해자다.
  `asMap()` 계열은 `AnnotatedElementUtils.getMergedAnnotationAttributes`의 토대이고
  `AnnotationBeanNameGenerator`, `QualifierAnnotationAutowireCandidateResolver` 등이
  이 경로를 쓴다. 결함은 상류 한 곳(probe 대상 계산식)이고, 거기를 고치면 오염된
  annotation이 애초에 이 메서드들에 도달하지 않는다.

## G2 — diff 01 (red 테스트 5건)

**질문** (원문)

> 이 테스트 5건 중 **왜 3건은 fix 전에 실패하고 2건은 fix 전에도 통과하는지**,
> 그리고 canLoad 실패 케이스에서 mock의 `value()`가 예외를 던지게 만든 것이
> **실제 상황의 무엇을 흉내 내는 것인지** 본인 말로 설명해 주세요.

**시도 1 — 답변** (사용자 원문)

> 1번 지금은 배열 이넘타입에 대해 probe가 true라서 검사를 안하잖아? 그래서 저 예외가
> 발생하지 않아. 그리고 이떄 probe라는 용어에 대해 어떻게 이해하면 되는거야?
> 번역한다며늬 의미적인 용어뜻을 알고 싶어.
> 2번 똑같이 배열 이넘에 대해서 잘못된 어노테이션 객체를 만나면 예외가 정상적으로
> 발생하고, 이 예외기반 처리가 되어야 하는데 지금은 그게 되지 않는다는거잖아? 왜냐면
> 배열 이넘에 대해서 false가 나오고 그걸 바탕으로 probe를 해야되는데 지금은 그 작업을
> 하지 않아서 true로 조용히 동작해버린다는게 문제인거고,
> 3번은 그 외 정상적인 내부 객체 클래스에 대해서는 제대로 어노테이션이 통과해야되ㅡㄴ게
> 맞지.
> 4번은 실제 예외를 확인하는 거 아니야?
> 5번은 실제 인터페이스 객체로 어노테이션 스캔 시 문제가 없는지 제대로 확인하기 위해
> 객체를 만들고 예외, 실험용 이넘 객체를 추가한건데 맞아?

**판정 1** — fail (1/2). 판정 워커 원문:

> {fail, 부족점: (1) mock의 value()가 던지는 예외가 실제 세계의 어떤 상황을 재현하는지
> — "잘못된 어노테이션 객체"라는 표현에 머물렀고, 그 어노테이션이 어쩌다/어떤 환경
> 조건에서 그렇게 되는지(컴파일 시점과 런타임 사이에 무엇이 어긋난 상황인지)를 본인
> 말로 짚지 못함. (2) 4번은 설명이 아니라 되물음으로 끝남 — validate 실패 케이스가
> fix 전 red인 이유와, 실패 시 어떤 방식으로 예외가 보고되는지를 1~2문장으로 직접 설명
> 필요. (인과 사슬 자체 — 플래그 오계산 → probe 스킵 → 조용히 통과 — 는 2번에서
> 실질적으로 맞게 짚었으니, 위 두 지점만 보완하면 됨. 참고로 probe는 "사전 시험 호출/
> 탐침" 정도로 번역하면 됨 — 본검사 전에 미리 한 번 찔러보는 호출.)}

**학습 개입 (게이트 밖)**: 답변에 섞인 용어 질문("probe라는 용어에 대해 어떻게 이해하면
되는거야?")에 답했다 — probe는 값이 필요해서 읽는 호출이 아니라 "문제가 있는지 미리
찔러보는 시험 호출"이고, `canLoad`는 속성 메서드를 한 번 실제로 호출한 뒤 결과값을
버린다. 관심사는 오직 "이 호출이 예외 없이 성공하는가"뿐이다. 한국어로는 "사전 시험
호출"이 가장 가깝다.

**시도 2 — 질문** (2회차, 원문 요지)

> 1. canLoad 실패 테스트에서 mock의 `value()`가 예외를 던지게 만든 것은 실제 세계의
>    어떤 상황을 재현한 것인가요? 힌트: `Color` enum을 v1으로 컴파일하고 v2로 실행했던
>    구성 — 컴파일 시점과 런타임 사이에 무엇이 어긋난 상황인지.
> 2. validate 실패 테스트는 왜 fix 전에 red이고, fix 후에는 실패가 어떤 방식으로
>    보고되나요?

**시도 2 — 답변** (사용자 원문)

> 1번에 대해서 raw에 대해 probe 과정에서 관측하는 과정의 실패가 바로 Enum관련 어류가
> 아니라 이건 관측 시 나온 오류라 IllegalStateEception으로 나와야되는데 이게 나오는
> 이유가 제대로 관측에 대한 오류인지 확인하는 거같고, 이에 대해서 보는 거 맞지?
> 2번에 대해서도 똑같이 validate 실패에 대해서는 처음에는 probe를 하지 않기 때문에
> 레드가 나오는거고, probe를 하게 만들면서 Illagel오류가 발생한다고 봐야겠구나.

**판정 2** — fail-통과처리 (2/2). 판정 워커 원문:

> {fail-통과처리, ① 핵심 누락: mock 예외는 "구버전 enum 상수(BLUE 등)로 컴파일된
> annotation + 그 상수가 제거된 신버전 enum이 런타임 classpath에 로드된" 컴파일↔런타임
> 어긋남(부분 업그레이드)을 재현한 것 — 답변은 이를 짚지 못하고 probe 관측/
> IllegalStateException 얘기(②의 내용)로 대체함. 또한 canLoad 테스트에서는
> IllegalStateException이 아니라 boolean false로 보고됨 — 예외로 감싸는 쪽은
> validate뿐. ② 대체로 정확(probe 미수행→red, fix 후 probe 수행→Illegal 오류 보고)하나,
> "EnumConstantNotPresentException을 IllegalStateException으로 감싸서 던진다"는 보고
> 방식의 구체 구조는 명시되지 않음.}

**학습 개입 (게이트 밖)**: 게이트를 내리고 다음 단계로 넘어가려던 지점에서 사용자가
요청했다 — "잠시만 그냥 넘기지말고 내가 놓친 부분을 알려줄래? 제대로 알아야될 꺼 같은데,".
이에 두 지점을 정면으로 설명했고, 사용자의 후속 질문 3건이 이어졌다.

후속 질문 1 (사용자 원문 요지):

> 여기서 jar A로 구동중인데 jar B로 재구동할떄 서로 겹칠 일이 있어? 없지않아? 빌드
> 구동은 jar파일 1개를 기준으로 처리하잖아? 이 말의 의미를 제대로 모르겠는데?
> 애초에 컴파일할때 어노테이션에 대해서 그대로 현 버그로 enum배열이 통과된다고 할때
> jdk에서는 BLUE를 인식을 못하는데 스프링에서는 통과해서 어노테이션 객체를 만드는게
> 문제라는 거 아니야? 그런데 1번 문제가 왜 발생해?

답: jar A와 jar B는 같은 앱을 두 번 빌드한 두 버전이 아니라 한 앱의 classpath에 동시에
들어 있는 서로 다른 두 라이브러리다. `acme-monitoring-1.0.jar`의 클래스들이
`@AlertOn({Severity.FATAL})`을 달고 있는데(2년 전 acme-core 1.0 기준 컴파일),
`acme-core`만 2.0으로 올려 FATAL이 제거되면 JVM에는 2.0의 `Severity` 하나만 로드된다.
"재구동할 때 겹치는" 것이 아니라 한 번의 구동 안에서 "옛 이름을 기억하는 바이트코드"와
"이름이 사라진 새 클래스"가 공존하는 것 — 의존성 버전 스큐다.

후속 질문 2 (사용자 원문):

> 아 그럼 서로 다른 의존성 jar에 대해서 그런데 이떄 궁금한건 FATAL이라는 상수가 박혀있고
> 이때 core에서 로드된 enum이 없을수가 있나?

답: 세 층 어디에도 대조 검사가 없다. (1) `javac`는 지금 컴파일하는 내 소스만 검사하고
이미 컴파일된 jar의 바이트코드는 다시 검사하지 않는다. (2) Gradle/Maven은 좌표와 버전만
맞출 뿐 바이너리 호환성은 확인하지 않으며, 메이저 버전에서 enum 상수를 개명/제거하는 것은
허용된 breaking change다. (3) JVM 클래스 로드도 annotation 값을 해석하지 않는다 —
annotation은 이름으로 저장되고 읽는 순간에 해석되도록 JDK가 일부러 설계했다.

후속 질문 3 (사용자 원문):

> 아 모니터에 fatal이 아니라 core의 fatal과 맞는지 다른지 검사를 하지 않는다는거야?

답: 맞다. 대조가 일어나는 유일한 순간이 "누군가 그 속성값을 읽을 때"이고, Spring의
probe는 "어차피 언젠가 읽다 터질 거면 스캔 단계에서 내가 먼저 읽어보고 터지는 놈은
격리하자"는 조기 대조 장치다. 이번 버그는 그 조기 대조에서 enum 배열만 빠진 것이다.
이후 사용자가 "진행하자"로 게이트를 마무리했다.

**정답 정리**

- `willThrow(EnumConstantNotPresentException)`이 흉내 내는 실제 상황: 컴파일 시점에
  `@ArrayMarker({Color.BLUE})`의 .class에는 Color 객체가 아니라 "상수명 BLUE"라는
  문자열이 기록되고, 런타임에 JDK가 그 이름으로 지금 로드된 Color에서 상수를 찾는다
  (사실상 `Color.valueOf("BLUE")`). classpath가 부분 업그레이드되어 그 상수가 없으면
  이름 조회가 실패한다. 단위 테스트에서 enum 두 버전 컴파일과 클래스로더 조작을 매번 할
  수 없으니, 그 상황에서 JDK가 던지는 바로 그 예외를 Mockito 한 줄로 압축한 것이다.
- canLoad와 validate는 같은 probe를 돌리되 보고 방식이 다르다.

  | | canLoad | validate |
  |---|---|---|
  | 실패 보고 | boolean `false` 반환 (예외 안 던짐) | `IllegalStateException`을 던짐 |
  | 소비자 | `AnnotationsScanner` — false면 스캔 결과에서 제외 + warn 로그 | 반드시 읽혀야 한다는 명시적 검증 경로 |

  감싸는 지점은 `AttributeMethods.java:146-150`의
  `catch (Throwable ex) { throw new IllegalStateException("Could not obtain annotation
  attribute value for " + get(i).getName() + ...", ex); }`이며, 원인 예외는 어디까지나
  `EnumConstantNotPresentException`이고 validate가 그것을 cause로 감싸는 것이다.
  "Enum 오류가 아니라 관측 오류"가 아니라 "Enum 오류를 관측했고 그 사실을
  IllegalStateException으로 보고"가 맞다.
- 정리하면 probe(사전 시험 호출)는 하나, 출구가 둘이다 — 스캐너용 조용한 출구
  (canLoad -> false -> 필터링)와 명시 검증용 시끄러운 출구(validate -> IllegalStateException).
- JDK 층과 Spring 층의 구분: JDK는 이 상황에서 즉시 죽지 않고 `getAnnotation()` 시점에
  예외 폭탄을 심은 프록시를 정상적으로 만들어 준다. 여기까지는 JDK의 정의된 동작이지
  누구의 버그도 아니다. Spring 버그는 그 전제에서의 대응 누락 — enum 배열만 probe 목록에서
  빠져 격리되지 않는 것이다.

## G3 — diff 02 (fix 1줄 + 검증 결과)

적용된 diff (`AttributeMethods.java:84`):

```java
// before
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class || type.isEnum());
// after
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class ||
		type.isEnum() || (type.isArray() && type.componentType().isEnum()));
```

**질문** (원문)

> 1. fix 후 `asMap()`이 `{}`(빈 맵)를, `getEnumArray`가 `NoSuchElementException`을
>    주는 것이 fix 전의 각 결과보다 **왜 더 나은가**? (fix 전에 각각 무엇이 나왔는지
>    떠올리면서)
> 2. 이 1줄 추가가 **기존의 멀쩡한 annotation들을 깨뜨리지 않는다**는 확신은 어디서
>    오나? (오늘 실행한 검증 중 무엇이 그걸 보증하는지)

**시도 1 — 답변** (사용자 원문)

> 1번에서 asMap을 통해 잘못된 어노테이션 맵 객체가 생성되지 않으니 다른 곳에서 컴포넌트
> 검사할떄 문제가 없을꺼고, 이를 바탕으로 제대로 예외처리 되는걸 확인 가능했으니,
> 2번에서 어노테이션 스캔을 하는 과정에서 중간에 깨지지 않으니 다른 어노테이션은 문제
> 없다는 테스트를 바탕으로 확신할 수 있는거지

**판정 1** — fail (1/2). 판정 워커 원문:

> {fail, ①은 오염된 맵이 하류로 퍼지지 않는다는 취지를 자기 말로 짚어 인정되나, ②가
> "깨지지 않는다는 테스트" 수준의 불특정 근거에 머묾 — 오늘 실행한 검증 중 정확히 어떤
> 것이 "멀쩡한 annotation은 그대로"를 보증하는지 구체적으로 짚어야 함.}

**시도 2 — 질문** (2회차, 원문 요지)

> ②만 다시: "테스트가 있으니까"가 아니라, 오늘 실행한 검증 중 정확히 어떤 것이 "이 1줄을
> 추가해도 멀쩡한 annotation은 여전히 통과한다"를 보증하는지 짚어주세요.
> 힌트 1: 오늘 추가한 테스트 5건이 전부 "실패 케이스"는 아니었습니다 — fix 전에도
> green이던 2건이 무엇을 지키는 가드였는지.
> 힌트 2: 기존 probe 대상(Class·Class[]·단일 enum) 포함 전반이 안 깨졌다는 건 어떤 규모의
> 어떤 실행으로 확인했나요?

**시도 2 — 답변** (사용자 원문)

> 우선 1번과 2번 테스트에 대해서 probe에 대해서 제대로 인식하고 이에 대해서 true를 통해
> 예외를 인식 가능한 형태로 하는것,
> 2번 테스트에 대해서는 실제 제대로 필터를 canLoad에서 false가 되어서 필터링이 되어
> 어노테이션 자체 문제가 안생기도록 하는 작업이였지. 즉 제대로 넘겨낼 수 있는 지
> 그리고 오늘 테스트 중 기존의 어노테이션 배치 구조가 제대로 매핑 되는 지 확인할 필요가
> 있으니깐, 실제 기존의 어노테이션 로드에서 제대로 된게 제대로 로드되는 지확인할 수
> 있지않을까?

**판정 2** — fail-통과처리 (2/2). 판정 워커 원문:

> {fail-통과처리, 지적: ① 양성 가드 2건의 실질을 반대로 짚음 — 질문의 표적은 "정상 enum
> 배열 annotation이 canLoad=true·validate 무예외로 여전히 통과한다"는 가드(fix 전에도
> green)인데, 답변은 예외 인식·canLoad=false 필터링(red 실패 케이스) 쪽으로 설명함.
> ② 전반 무회귀 근거를 "기존 로드가 제대로 되는지 확인할 수 있지 않을까?"라는 추측형
> 되물음으로 남김 — 오늘 실제 실행한 annotation 패키지 전체 스위트 733 tests / 0 failures를
> 구체적으로 지목했어야 함. ③ 요지 정리: 이 fix의 무회귀 보증 = (a) 양성 가드 2건이
> "멀쩡한 annotation은 새 probe를 통과"를 직접 보증 + (b) 733건 전체 스위트가 기존 probe
> 대상(Class/Class[]/단일 enum)과 MergedAnnotations 등 전반이 안 깨졌음을 보증.}

**학습 개입 (게이트 밖)**: 게이트 통과 후 사용자가 요청했다 — "어딜 어떻게 놓쳤는지
테스트 하나하나 cli에 diff와 각 테스트마다 설명을 작성한번 해줄래?". 리뷰가 도는 동안
테스트 5건을 "무엇을 주장하나 / fix 전 결과와 이유 / 게이트에서 놓친 지점"으로 해설했고,
그 내용이 [tests.md](tests.md)의 원본이 됐다. 역할 분담 표:

| | 오염된 annotation (willThrow) | 멀쩡한 annotation (willReturn) |
|---|---|---|
| 플래그 | 테스트 1: probe 대상으로 표시되나 (red -> green) | — |
| canLoad | 테스트 2: false로 걸러지나 (red -> green) | 테스트 3: true로 통과하나 (항상 green, 과잉 필터링 가드) |
| validate | 테스트 4: IllegalStateException 던지나 (red -> green) | 테스트 5: 무예외인가 (항상 green, 가드) |

**정답 정리**

- 왼쪽 열 3건이 "버그가 고쳐졌다"의 증명이고, 오른쪽 열 2건이 "고치면서 아무것도 안
  깨뜨렸다"의 증명이다. 게이트 (2)의 정답이 바로 이 오른쪽 열 + annotation 패키지 733건
  스위트였는데, 답변은 왼쪽 열(실패 케이스) 쪽으로 설명했다.
- 테스트 3이 fix 전에 green인 이유는 "probe를 안 하면 무조건 true"라서지만, 이 테스트의
  존재 이유는 fix 후에도 green이라는 것 — probe가 실제로 도는데도 정상 값이라 예외가 없어
  여전히 true다. 즉 "새로 추가한 probe가 무고한 annotation까지 걸러버리는 과잉 필터링을
  하지 않는다"를 지킨다.
- 테스트 2의 red는 "예외가 안 터져서" 실패하는 것이 아니라 "터질 기회조차 없어서" 오판
  (true)이 나오는 것이다.
- fix 후 실물 스모크(mock이 아닌 진짜 stale enum 상황): `isPresent(ArrayMarker) = false`
  + warn 로그, `asMap() = {}`, typed 접근은 `NoSuchElementException`(Unable to get
  attribute value for missing annotation). raw `EnumConstantNotPresentException`이라는 JDK
  내부 사정 누출 대신 Spring의 missing-annotation 계약으로 정리되며, "필터링된 annotation은
  없는 것"이라는 일관된 의미론이 된다.

## G4 — diff 03 (리뷰 반영: 테스트 개명 + String[] 음성 가드)

**질문** (원문)

> ① 개명에서 "예외 축으로 통일"이 왜 이 파일에서는 속성 축보다 나은 선택인지,
> ② `String[]` 음성 가드 테스트가 없을 때 생길 수 있는 회귀(미래의 어떤 잘못된 수정을
> 못 잡는지)를 본인 말로 설명해 주세요.

**시도 1 — 답변** (사용자 원문)

> 결국 예외가 그 동작 계약에 대한 구체니깐 속성보다 예외 축을 기반으로 계약기반ㅇ 예외
> 설계로 바꾼거네. 그리고 이때 type에 대해서 이게 Enum에 한정되어야 한다는 가드레일을
> 위해 String[]에 대해서는 해당 작동을 안하도록 하는 테스트 가드레일을 추가하는거네

**판정 1** — pass. 판정 워커 원문:

> {pass, ①은 예외 이름이 동작 계약을 직접 드러낸다는 근거를, ②는 조건이 enum 배열
> 밖(String[])으로 과확장되는 것을 막는 가드 역할을 본인 말로 포착 — 루브릭 충족}

**정답 정리** (판정 워커 packet의 그라운드 트루스)

- 개명의 핵심 이유는 파일 내 일관성이다. 이 파일의 기존 Class 계열 쌍이 이미 예외 축
  관용구(`isValidWhenHasTypeNotPresentExceptionReturnsFalse` /
  `isValidWhenDoesNotHaveTypeNotPresentExceptionReturnsTrue`)를 쓰고 있어, 신규 4건을 그
  축으로 맞추면 기존 4건과 완전 병렬이 된다. 사용자가 짚은 "예외 이름이 검증되는 계약을
  직접 드러낸다"는 것은 부수 효과이며, 루브릭이 둘 중 하나만 포착해도 pass로 인정했다.
- `String[]` 음성 가드(`canThrowTypeNotPresentExceptionWhenHasNonEnumArrayAttributeReturnsFalse`)가
  없으면, 미래에 조건이 실수로 넓어져도(예: `componentType` 검사 누락으로 모든 배열을
  probe) 테스트가 잡지 못한다 — probe가 불필요한 속성까지 리플렉션 호출이 늘어나는 회귀가
  무음으로 통과한다.

## 반복된 오해 패턴

네 게이트에 걸쳐 되풀이된 오해는 다섯 갈래이고, 대부분 인과의 방향이나 층을 뒤집는 형태였다.

1. **플래그의 인과 방향 뒤집기 (G1·G2에서 반복)**. "probe가 true라서 검사를 안 한다",
   "false가 나오고 그걸 바탕으로 probe를 해야" — 두 게이트에서 같은 방향 오류가 나왔다.
   실제는 플래그 true = probe 수행, false = probe 스킵이며, 스킵이 곧 오판(canLoad=true)의
   원인이다. 결론부("probe를 안 해서 조용히 통과한다")는 매번 맞았고 주어만 틀렸다.
2. **canLoad와 validate의 보고 방식 혼동 (G2 두 시도 모두)**. 같은 probe를 돌린다는 것까지는
   맞게 봤으나 canLoad의 실패 보고(boolean false)에도 IllegalStateException을 끌어왔다.
   보고 방식이 다르다는 것 자체가 각각 별도 테스트로 고정된 계약이다.
3. **양성 가드를 실패 케이스로 설명 (G3)**. "안 깨뜨린다는 확신은 어디서 오나"라는 질문에
   red 테스트(필터링 동작)를 근거로 들었다. 무회귀 근거는 항상 green인 가드 쪽과 전체
   스위트 규모다.
4. **되물음으로 답을 대체 (G1 시도 1, G2 시도 1의 4번, G3 시도 2)**. 세 게이트 모두에서
   판정 워커가 "역질문으로 넘겼다", "추측형 되물음으로 남겼다"를 fail 사유로 명시했다.
   질문 자체는 유익했고 별도로 답을 받았지만, 게이트 판정에서는 설명의 공백으로 계산됐다.
5. **환경 전제와 프레임워크 결함의 층 혼동 (G2)**. classpath 버전 스큐(어긋남)는 환경이
   만드는 전제 조건이고 JDK의 지연 실패는 정의된 동작이다. Spring 버그는 그 전제에서의
   대응 누락 한 곳이다. 이 층 분리가 안 되면 "JDK가 인식 못 하는데 왜 Spring이 문제냐"는
   질문에서 막힌다.

## 교훈

이 기록이 남긴 것은 재현 요구·통과 거부·판정 근거처럼 게이트를 실제로 작동시킨 장치들이다.

- **재현 요구가 이해를 앞당겼다.** G1에서 사용자가 CLI 재현을 요구한 결과 `asMap()` 오염이
  발견됐고, 그것이 PR 본문 Problem 절의 두 번째 항목(silent corruption)이 됐다. 게이트가
  fail이어도 그 과정에서 나온 요구가 산출물을 개선한 사례다.
- **"그냥 넘기지 말고 알려줘"가 결정적이었다.** G2의 2회차는 규칙상 자동 통과였는데, 사용자가
  통과를 거부하고 설명을 요구해 컴파일-런타임 어긋남과 두 출구 구조를 제대로 잡았다. 그
  이해가 G4에서 1회 pass로 이어졌다 — 네 게이트 중 유일한 1회차 pass다.
- **판정 워커의 그라운드 트루스는 메인의 해설이 아니라 실코드였다.** G1 판정 packet은
  `AttributeMethods` 생성자 원문을 싣고 "메인의 해설이 아니라 아래 실제 코드와 대조하라"고
  명시했다. 메인이 이미 정답을 말해 준 뒤라도 판정이 무르지 않게 하는 장치다.
- **게이트 질문이 리뷰 findings와 겹쳤다.** G3의 (2)("안 깨뜨린다는 확신")는 이후 듀얼 리뷰의
  완전성 렌즈가 제기한 음성 가드 부재(Q2)와 같은 축이고, 그 채택 결과가 G4의 소재가 됐다.
  이해 게이트와 리뷰가 같은 빈칸을 서로 다른 방향에서 짚은 셈이다.
