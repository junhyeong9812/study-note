# PR #19339 - 무대의 실구조와 워크플로우

> PR #19339의 무대가 되는 실구조와 워크플로우.
> 문제와 수정은 [README.md](README.md), 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: fork `main`(`ed7ae7969ed`) - **수정 전** 상태다.
> 아래 file:line은 별도 표시가 없으면 수정 전 좌표이고, 수정은 `saveSessionInformation`(`:59-65`)과 `removeSessionInformation`(`:72-84`) 두 메서드다.

## 1. 무대 - 실구조

이 결함의 무대는 **맵 두 개로 세션을 양방향 색인하는 레지스트리 하나**, 그리고 그것과 쌍둥이인 블로킹 구현 하나다.\
두 맵 중 결함이 있는 쪽은 `principal -> sessionIds`이고, 그 맵의 값이 컬렉션이라는 점이 원자성 문제를 만든다.\
층을 위에서 아래로 그리면 이렇다.

> **양방향 색인** — 같은 데이터를 두 방향에서 찾을 수 있게 맵을 둘 두는 것.\
> 예: "이 사용자의 세션 목록"과 "이 세션 id의 정보"를 각각 다른 맵으로 찾으며, 둘이 어긋나면 한쪽에서만 보이는 데이터가 생긴다.

```text
+------------------------------------------------------------------------------+
| 호출자 (WebFlux 동시 세션 관리)                                                |
|   로그인 성공        -> saveSessionInformation                                |
|   로그아웃 / 만료    -> removeSessionInformation                              |
|   한도 계산, 세션 만료 정책 -> getAllSessions(principal)                       |
|   ** 서로 다른 요청이 여러 event-loop 스레드에서 동시에 이들을 부른다 **         |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| ReactiveSessionRegistry (인터페이스)                                          |
|   getAllSessions / saveSessionInformation / getSessionInformation /          |
|   removeSessionInformation / updateLastAccessTime                            |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| InMemoryReactiveSessionRegistry   core/.../core/session/InMemoryReactiveSessionRegistry.java
|                                                                              |
|  [상태 - 맵 두 개]                                                             |
|    ConcurrentMap<Object, Set<String>> sessionIdsByPrincipal           :37     |
|      값 = CopyOnWriteArraySet<String>    <- 이번 결함의 무대                   |
|    Map<String, ReactiveSessionInformation> sessionById                :39     |
|                                                                              |
|  [생성자 두 종]                                                                |
|    기본       - 둘 다 new ConcurrentHashMap<>()                       :41-44  |
|    맵 주입    - 호출자가 준 ConcurrentMap/Map 을 그대로 보관           :46-50  |
|                                                                              |
|  [연산]                                                                       |
|    getAllSessions        sessionIdsByPrincipal -> sessionById 로 매핑  :52-57 |
|    saveSessionInformation                                             :59-65 |
|    getSessionInformation sessionById 조회만                            :67-70 |
|    removeSessionInformation                                           :72-84 |
|    updateLastAccessTime  sessionById 만 만짐                           :86-93 |
+------------------------------------------------------------------------------+
                                    |
                        형제 (같은 구조, 다른 스택)
                                    |
                                    v
+------------------------------------------------------------------------------+
| SessionRegistryImpl (블로킹)      core/.../core/session/SessionRegistryImpl.java
|    ConcurrentMap<Object, Set<String>> principals                      :56     |
|    Map<String, SessionInformation> sessionIds                         :59     |
|    기본 생성자 / 맵 주입 생성자                                        :61-70  |
|    registerNewSession   -> principals.compute(...)                    :138-145|
|    removeSessionInformation -> principals.computeIfPresent(...)       :159-171|
|                                                                              |
|   ** 필드 모양·생성자·정리 규칙이 같고, 갱신 방식만 원자적이다 **                |
+------------------------------------------------------------------------------+
```

> **블로킹 스택 / 리액티브 스택** — 요청 하나에 스레드 하나를 붙여 기다리게 하는 전통 서블릿 방식과, 적은 스레드로 여러 요청을 번갈아 처리하는 방식.\
> 예: `SessionRegistryImpl`이 서블릿(블로킹) 쪽, `InMemoryReactiveSessionRegistry`가 WebFlux(리액티브) 쪽이며, 하는 일은 같다.

## 2. 원자 단위의 경계 - 결함의 실체

이 결함을 한 그림으로 보려면 "어디까지가 한 원자 연산인가"를 표시해야 한다.\
수정 전후를 같은 형식으로 나란히 놓는다.

```text
[수정 전 - save]                          [수정 후 - save]
 +-- 원자 -----------------------+         +-- 원자 --------------------------+
 | computeIfAbsent(P, k -> set)  |         | compute(P, (k, set) -> {         |
 +-------------------------------+         |    if (set == null) set = new..  |
        .add(sessionId)   <- 원자 밖        |    set.add(sessionId)            |
                                           |    return set                    |
                                           | })                               |
                                           +----------------------------------+

[수정 전 - remove]                        [수정 후 - remove]
 +-- 원자 --+ get(P)                       +-- 원자 --------------------------+
   set.remove(sessionId)  <- 원자 밖        | computeIfPresent(P, (k, set) -> {|
   set.isEmpty()          <- 원자 밖        |    set.remove(sessionId)         |
 +-- 원자 --+ map.remove(P)  조건 없음      |    return set.isEmpty() ? null   |
                                           |                    : set         |
                                           | })                               |
                                           +----------------------------------+
```

수정 전에는 원자 연산이 여러 개이고 그 **사이**가 열려 있다.\
수정 후에는 재매핑 함수 호출 전체가 한 원자 단위이므로 사이가 없다.\
`ConcurrentHashMap`은 같은 키에 대한 재매핑 동안 그 키의 다른 갱신을 막으므로, 두 스레드의 작업이 직렬화된다.

> **원자 단위(atomicity boundary)** — "여기서부터 여기까지는 통째로 처리된다"는 구간.\
> 예: `computeIfAbsent`는 "없으면 넣는다"까지만 그 구간이고, 그 뒤 `.add()`는 이미 밖이다.

`return null`이 하는 일도 짚어 둔다.\
`computeIfPresent`의 재매핑 함수가 `null`을 돌려주면 `ConcurrentHashMap`은 그 키를 제거한다.\
즉 "비었으면 키 제거"가 **비어 있음을 확인한 그 원자 구간 안에서** 일어나는 조건부 제거가 된다.\
수정 전 `map.remove(P)`는 조건 없는 제거였고, 그 무조건성이 3절 인터리빙의 마지막 조각이다.

> **조건부 제거 / 조건 없는 제거** — "지금도 조건이 참일 때만 지운다"와 "일단 지운다"의 차이.\
> 예: 제거 직전에 집합이 다시 채워졌다면, 조건부 제거는 지우지 않고 조건 없는 제거는 그냥 지운다.

## 3. 워크플로우 - 동시 save/remove 한 번

principal P가 세션 S1 하나를 가진 상태에서 두 요청이 동시에 들어오는 흐름이다.\
왼쪽이 수정 전, 오른쪽이 수정 후다.

```text
[수정 전]                                   [수정 후 - save 가 먼저 잡은 경우]
 A: get(P)          -> {S1}                  A: computeIfPresent(P) 대기
 A: set.remove(S1)  -> {}                    B: compute(P) 진입 (원자)
 A: isEmpty()       -> true                     set = {S1} 에 S2 추가 -> {S1,S2}
 B: computeIfAbsent(P) -> 같은 set            A: computeIfPresent(P) 진입 (원자)
 B: set.add(S2)     -> {S2}                     S1 제거 -> {S2}, 비지 않음
 A: map.remove(P)   -> 키 제거                  return set
    {S2} 가 키째 사라진다                     결과: {S2} 유지
 결과: getAllSessions(P) 가 비어 있다
                                            [수정 후 - remove 가 먼저 잡은 경우]
                                             A: computeIfPresent(P) 진입 (원자)
                                                S1 제거 -> {} -> return null -> 키 제거
                                             B: compute(P) 진입 (원자)
                                                set == null -> 새 집합 생성, S2 추가
                                             결과: {S2} 유지
```

수정 후에는 두 순서 중 어느 쪽이든 S2가 살아남는다.\
그것이 이 수정이 확립하는 불변식이고, 테스트가 `contains(added)`로만 단언하고 `containsExactly`를 쓰지 않는 이유이기도 하다 - 최종 집합이 `{S2}`일 수도 `{S1, S2}`일 수도 있으며 둘 다 정상이다.

> **불변식(invariant)** — 실행 순서가 어떻게 되든 늘 참이어야 하는 성질.\
> 예: "동시에 저장한 세션은 유실되지 않는다"는 불변식이고, "최종 집합의 크기가 1이다"는 불변식이 아니다.

## 4. 두 맵 사이 - 이 PR이 다루지 않는 것

`sessionById`와 `sessionIdsByPrincipal`은 여전히 **각각** 갱신되고 둘을 걸치는 원자성은 없다.\
다음 두 가지가 그 결과로 남는다.

- **일시적 불일치.**\
  `getAllSessions`(`:54-57`)가 `sessionIdsByPrincipal`에서 id를 꺼내 `sessionById`로 매핑하는 사이에 다른 스레드가 갱신하면, 순간적으로 어긋난 상태를 볼 수 있다.\
  `mapNotNull`이 붙어 있어 사라진 id는 결과에서 빠지므로 예외는 나지 않는다.
- **같은 sessionId의 동시 제거·재저장.**\
  `removeSessionInformation`의 `sessionById.remove(sessionId)`(`:75`)가 조건 없는 제거이므로, 같은 id로 방금 저장한 매핑을 지울 수 있다.

둘 다 보고한 결함(S1/S2 고아 집합)과 **별개이고 더 좁은 케이스**이며, 블로킹 형제도 동일하게 갖고 있다.\
이 PR의 범위를 그 밖으로 넓히면 "레이스 하나 수정"이 "레지스트리 동시성 모델 재설계"가 되므로 범위 밖으로 명시하고 기록만 남겼다.

> **범위(scope) 관리** — 이 변경이 무엇을 고치고 무엇을 안 고치는지를 미리 선 긋는 것.\
> 예: 알게 된 문제를 전부 한 PR에 담으면 리뷰가 불가능해지므로, 별개 문제는 문서에 적어 두고 코드는 건드리지 않는다.

## 5. 맵 주입 생성자 - 원자성이 기대는 전제

`compute`/`computeIfPresent`가 원자적이라는 보장은 `ConcurrentMap` 인터페이스가 아니라 **`ConcurrentHashMap` 구현**에서 나온다.\
`ConcurrentMap`의 default 구현은 `get`/`replace`/`remove`를 쓰는 재시도 루프이고, 재매핑 함수가 여러 번 호출될 수 있다.

> **default 구현의 재시도 루프** — 인터페이스가 제공하는 기본 몸체가 "읽고, 계산하고, 바뀌지 않았으면 교체하고, 바뀌었으면 처음부터 다시"를 반복하는 형태.\
> 예: 이 방식은 값 객체를 새로 만들어 교체할 때는 맞지만, 같은 객체를 제자리에서 고치면 "바뀌지 않았다" 비교가 속아 넘어간다.

그래서 2인자 생성자(`:46-50`)로 `ConcurrentHashMap`이 아닌 구현을 주입하면 이 수정의 전제가 깨진다.\
같은 집합 객체를 제자리에서 고치고 참조 동일성으로 CAS하므로 고아 집합이 다시 생길 수 있다.

> **참조 동일성(reference identity)** — 두 변수가 같은 객체를 가리키는지를 내용이 아니라 주소로 비교하는 것.\
> 예: 집합의 내용이 `{S1}`에서 `{S2}`로 바뀌어도 객체 자체는 같으므로, 주소로 비교하면 "안 바뀌었다"가 된다.

이 한계를 감수한 근거는 **블로킹 형제가 정확히 같은 전제 위에 있다**는 것이다.\
`SessionRegistryImpl`도 같은 맵 주입 생성자(`:66-70`)와 같은 compute 패턴을 쓰고 이미 출시돼 있다.\
이 수정은 형제와의 동등성을 회복할 뿐 새 한계를 들여오지 않으며, 임의 `ConcurrentMap` 주입을 계약으로 지원할지는 두 클래스 모두에 대한 별개 논의다.\
기본 생성자는 양쪽 다 `ConcurrentHashMap`이다.
