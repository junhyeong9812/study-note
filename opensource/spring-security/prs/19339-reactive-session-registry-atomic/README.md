# PR #19339 - Make InMemoryReactiveSessionRegistry updates atomic

## 0. 정향

이 문서는 `spring-security-core`의 `InMemoryReactiveSessionRegistry`가 **같은 사용자에 대한 동시 저장과 제거에서 방금 만든 세션을 잃어버리던** 레이스의 해설이다.\
이 결함은 앞의 두 건과 성격이 다르다.\
어느 한 줄도 그 자체로는 틀리지 않았고, 두 메서드가 각각 "확인한 뒤 행동한다(check-then-act)"는 형태를 취한 것이 문제이며, 그래서 **결정론적 단위 테스트로 잡을 수 없다.**\
다 읽으면 "왜 `ConcurrentHashMap`을 썼는데도 레이스가 나는가", "`computeIfAbsent(...).add(...)`의 원자 단위 경계가 어디까지인가", "레이스를 테스트로 어떻게 red 재현했는가"를 설명할 수 있어야 한다.

> **레이스(race condition, 경합 조건)** — 두 스레드의 실행 순서가 어떻게 섞이느냐에 따라 결과가 달라지는 상태.\
> 예: 여기서는 "제거 스레드가 키를 지우기 직전에 저장 스레드가 끼어드는" 순서에서만 세션이 사라진다.

> **check-then-act** — 먼저 조건을 확인하고 그 결과를 믿고 행동하는 패턴.\
> 예: "집합이 비었나?"를 확인한 뒤 "그러니 키를 지운다"로 넘어가는 사이에 다른 스레드가 집합을 다시 채우면, 확인 결과가 이미 낡은 것이 된다.

상태: **리뷰 대기**(2026-06-14 제출, 커밋 `fc4964f8d5` + 후속 `72feea0d33`, 라벨 `status: waiting-for-triage`).\
연결 이슈 gh-19338.\
메인테이너 리뷰는 아직 없고, 외부 기여자 `ronodhirSoumik`이 스타일 코멘트 3건을 남겨 그중 1건을 반영했다(6절).

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md).\
**이 PR은 4종 구성**이다.\
spring-framework 아카이브의 다섯째 문서(`gates.md`, 이해 게이트 기록)는 이 작업에 해당하는 원자료가 없어 만들지 않았다.

## 1. 배경 - 맵 두 개와 블로킹 형제 하나

`InMemoryReactiveSessionRegistry`는 WebFlux의 동시 세션 관리를 받치는 레지스트리다.\
누가 어떤 세션을 갖고 있는지를 맵 두 개로 기록한다.

```java
private final ConcurrentMap<Object, Set<String>> sessionIdsByPrincipal;    // :37
private final Map<String, ReactiveSessionInformation> sessionById;         // :39
```
(InMemoryReactiveSessionRegistry.java)

> **WebFlux** — 스프링의 논블로킹 웹 스택.\
> 예: 요청마다 전용 스레드를 붙이지 않고 소수의 event-loop 스레드가 여러 요청을 번갈아 처리하므로, 같은 객체가 여러 스레드에서 동시에 불린다.

> **principal(주체)** — "누구인가"에 해당하는 인증 주체 객체.\
> 예: 로그인한 사용자 하나가 principal이고, 그 사람이 휴대폰과 노트북에서 각각 로그인하면 세션 id 두 개가 같은 principal에 매달린다.

로그인하면 `saveSessionInformation`이 세션을 등록하고, 로그아웃이나 만료면 `removeSessionInformation`이 지운다.\
한 사용자가 여러 기기에서 여러 세션을 가질 수 있으므로 `sessionIdsByPrincipal`의 값은 집합이고, **어떤 사용자의 마지막 세션이 사라지면 그 사용자 키 자체를 맵에서 지운다**는 것이 이 클래스의 정리 규칙이다.

이 레지스트리에는 **블로킹 형제**가 있다.\
서블릿 스택의 `SessionRegistryImpl`이다.\
두 클래스는 필드 모양(`ConcurrentMap<Object, Set<String>>` + `Map<String, ...>`), 생성자 두 종(기본 + 맵 주입), 정리 규칙까지 같다.\
다른 것은 갱신 방식이다.

```java
// 블로킹 형제 - 등록
this.principals.compute(principal, (key, sessionsUsedByPrincipal) -> {
	if (sessionsUsedByPrincipal == null) {
		sessionsUsedByPrincipal = new CopyOnWriteArraySet<>();
	}
	sessionsUsedByPrincipal.add(sessionId);
	return sessionsUsedByPrincipal;
});
```
(SessionRegistryImpl.java:138-145)

```java
// 블로킹 형제 - 제거
this.principals.computeIfPresent(info.getPrincipal(), (key, sessionsUsedByPrincipal) -> {
	sessionsUsedByPrincipal.remove(sessionId);
	if (sessionsUsedByPrincipal.isEmpty()) {
		sessionsUsedByPrincipal = null;      // null 반환 = 키 제거
	}
	return sessionsUsedByPrincipal;
});
```
(SessionRegistryImpl.java:159-171, 로그 생략)

`compute`와 `computeIfPresent`는 `ConcurrentHashMap`에서 **키 하나에 대해 재매핑 전체가 원자적**이다.\
즉 블로킹 쪽은 이 동시성을 이미 막고 있다.\
**이 사실이 이 PR의 1순위 논거다** - 우리가 새 위험을 상상한 것이 아니라, 같은 팀이 같은 자료구조에서 이미 인정하고 막아 둔 동시성을 리액티브 쪽만 놓친 것이다.

> **재매핑 함수(remapping function)** — `compute` 계열에 넘기는 람다로, "지금 값이 이것일 때 새 값은 무엇인가"를 계산한다.\
> 예: `(key, set) -> { set.add(id); return set; }`이 재매핑 함수이고, `ConcurrentHashMap`은 이 함수가 도는 동안 그 키의 다른 갱신을 막는다.

> **원자적(atomic)** — 중간 상태가 다른 스레드에게 보이지 않고, 통째로 되거나 아예 안 되는 성질.\
> 예: 재매핑 함수 안의 "확인 + 수정 + 반환"이 한 덩어리로 처리되면 그 사이에 누구도 끼어들 수 없다.

## 2. 수정 전 동작 - 원자 단위 경계가 어긋난 두 자리

수정 전 리액티브 쪽은 두 메서드 모두 원자 단위 밖에서 집합을 만졌다.

```java
public Mono<Void> saveSessionInformation(ReactiveSessionInformation information) {
	this.sessionById.put(information.getSessionId(), information);
	this.sessionIdsByPrincipal.computeIfAbsent(information.getPrincipal(), (key) -> new CopyOnWriteArraySet<>())
		.add(information.getSessionId());
	return Mono.empty();
}
```
(수정 전 InMemoryReactiveSessionRegistry.java:59-65)

저장 한 번이 어느 단계에서 잠금 안에 있고 어느 단계에서 밖으로 나오는지를 세로로 내려 그리면 이렇다.

```text
saveSessionInformation(information)                       :59
        |
        v
  sessionById.put(sessionId, information)                 :60
        |            (맵 하나에 대한 단일 연산)
        v
  sessionIdsByPrincipal.computeIfAbsent(P, k -> new Set)  :61-62
        |
        +--- 여기까지가 한 원자 단위 ---------------------+
        |    "키 P 가 없으면 빈 집합을 넣는다"            |
        +------------------------------------------------+
        |
        |  << 잠금이 풀린다. 이 틈에 다른 스레드가 키 P 를 지울 수 있다 >>
        |
        v
  반환된 set.add(sessionId)                               :63
        |    집합 자체는 스레드 안전하지만
        |    그 집합이 아직 맵에 붙어 있는지는 아무도 보장하지 않는다
        v
  Mono.empty()                                            :64
```

갈림은 `computeIfAbsent`가 끝나는 자리다 - 그 뒤의 `.add(...)`는 잠금 밖의 별개 호출이다.

`computeIfAbsent`가 원자적으로 하는 일은 **"키가 없으면 빈 집합을 넣는다"까지**다.\
그 다음 줄의 `.add(...)`는 반환된 집합에 대한 별개 호출이고, 맵의 잠금 밖에서 일어난다.\
집합 자체는 `CopyOnWriteArraySet`이라 스레드 안전하지만, **집합이 안전한 것과 "맵에서 그 집합을 꺼내 더하는 동안 아무도 그 키를 지우지 않는 것"은 다른 문제**다.

> **CopyOnWriteArraySet** — 원소를 더하거나 뺄 때 내부 배열을 통째로 복사해 새로 만드는 스레드 안전 집합.\
> 예: 읽기가 훨씬 잦은 자리에 쓰며, "이 집합을 동시에 만져도 깨지지 않는다"만 보장할 뿐 "이 집합이 맵에 계속 붙어 있다"는 보장하지 않는다.

```java
public Mono<ReactiveSessionInformation> removeSessionInformation(String sessionId) {
	return getSessionInformation(sessionId).doOnNext((sessionInformation) -> {
		this.sessionById.remove(sessionId);
		Set<String> sessionsUsedByPrincipal = this.sessionIdsByPrincipal.get(sessionInformation.getPrincipal());
		if (sessionsUsedByPrincipal != null) {
			sessionsUsedByPrincipal.remove(sessionId);
			if (sessionsUsedByPrincipal.isEmpty()) {
				this.sessionIdsByPrincipal.remove(sessionInformation.getPrincipal());
			}
		}
	});
}
```
(수정 전 InMemoryReactiveSessionRegistry.java:72-84)

이쪽은 네 단계가 전부 따로 논다 - `get`으로 집합을 꺼내고, 원소를 지우고, 비었는지 묻고, 키를 지운다.\
마지막 `remove(principal)`이 **조건 없는 제거**라는 점이 결정적이다.\
"조금 전에 비어 있었다"를 근거로 지우는데, 그 사이에 집합이 다시 채워졌을 수 있다.

## 3. 문제 - 방금 만든 세션이 통째로 사라진다

사용자 P가 세션 S1 하나를 갖고 있는 상태에서, 한 기기에서 로그아웃하고 다른 기기에서 로그인하는 순간을 생각하면 된다.

```text
      스레드 A (remove S1)                 스레드 B (save S2)
      --------------------                 -----------------
 1.   set = map.get(P)      -> {S1}
 2.   set.remove(S1)        -> {}
 3.   set.isEmpty()         -> true
                                     4.   map.computeIfAbsent(P, ...)
                                          키 P 가 아직 있다 -> 같은 set 반환
                                     5.   set.add(S2)      -> {S2}
 6.   map.remove(P)          <- 조건 없이 키 제거
                                          {S2} 를 담은 채로 사라진다

 결과: getAllSessions(P) 가 비어 있다. S2 는 sessionById 에만 남아
       어디에서도 P 의 세션으로 조회되지 않는 고아가 된다.
```

> **인터리빙(interleaving)** — 두 스레드의 단계들이 실제로 섞여 실행되는 순서.\
> 예: 위 그림의 1-2-3-4-5-6이 하나의 인터리빙이고, 4와 5가 3과 6 사이에 끼는 것이 이 결함의 유일한 조건이다.

> **고아(orphan) 세션** — 어느 색인에서도 가리켜지지 않아 찾아갈 수 없게 된 데이터.\
> 예: S2는 `sessionById`에 남아 있지만 `sessionIdsByPrincipal`에서는 사라져, "이 사용자의 세션 목록"에 절대 나타나지 않는다.

3번과 6번 사이에 4~5번이 끼어드는 것이 이 레이스의 전부다.\
창은 좁지만 WebFlux는 여러 event-loop 스레드에서 요청을 동시에 처리하므로 원리적으로 열려 있다.

> **event-loop 스레드** — 요청 하나마다 스레드를 붙이지 않고, 소수의 스레드가 일감을 돌아가며 처리하는 방식의 실행 스레드.\
> 예: WebFlux는 CPU 코어 수만큼의 event-loop 스레드로 수많은 요청을 처리하므로, 두 요청의 처리가 진짜로 같은 시각에 진행된다.

**결과는 데이터 손상이 아니라 계산 오류다.**\
세션 정보 자체는 `sessionById`에 남아 있고 그 세션으로 요청을 계속 처리할 수도 있다.\
다만 "이 사용자가 몇 개의 세션을 갖고 있는가"를 묻는 쪽 - 동시 세션 한도 계산, "다른 세션을 만료시킨다" 같은 정책 - 이 잘못된 답을 받는다.\
예외도 로그도 남지 않는다.

> **무음 실패(silent failure)** — 에러를 내지 않고 정상처럼 끝나는데 결과만 틀린 실패.\
> 예: 여기서는 예외도 로그도 없이 세션 개수만 하나 모자라게 세어지므로, 운영 지표로도 드러나지 않는다.

### 왜 이 결함이 실재하는 동시성인가

레이스 결함에는 늘 "그런 동시 호출이 실제로 일어나나"라는 질문이 따라붙고, 이 질문에 답하지 못하면 PR이 이론 연습으로 읽힌다.\
근거는 셋이다.

1. **레지스트리의 존재 이유가 그것이다.**\
   서로 다른 요청이 독립적으로 세션을 등록하고 제거하라고 있는 컴포넌트이고, WebFlux는 그 요청들을 여러 스레드에서 동시에 처리한다.
2. **자료구조 선택이 그것을 전제한다.**\
   `ConcurrentMap`과 `CopyOnWriteArraySet`을 쓴다는 것 자체가 동시 접근을 상정했다는 뜻이다.\
   문제는 동시성을 상정해 놓고 원자 단위 경계를 잘못 그었다는 데 있다.
3. **가장 강한 근거 - 블로킹 형제가 이미 막고 있다.**\
   `SessionRegistryImpl`이 같은 자료구조에서 `compute`/`computeIfPresent`를 쓴다는 사실은, 이 동시성이 상상이 아니라 **팀이 이미 실재로 인정한 것**임을 보여 준다.\
   리액티브 쪽만 그 처리가 빠졌다.

## 4. 수정 해설 - 원자 단위 경계를 람다 안으로 옮기기

수정은 새 자료구조도 새 잠금도 도입하지 않는다.\
**집합을 만지는 코드를 재매핑 함수 안으로 옮기는 것**이 전부다.

```java
// Add the session id inside the compute so that it cannot race with the key
// removal performed by removeSessionInformation (which could otherwise drop a
// concurrently added session). This mirrors the blocking SessionRegistryImpl.
this.sessionIdsByPrincipal.compute(information.getPrincipal(), (key, sessionsUsedByPrincipal) -> {
	if (sessionsUsedByPrincipal == null) {
		sessionsUsedByPrincipal = new CopyOnWriteArraySet<>();
	}
	sessionsUsedByPrincipal.add(information.getSessionId());
	return sessionsUsedByPrincipal;
});
```
(수정 후 InMemoryReactiveSessionRegistry.java, `saveSessionInformation`)

```java
// Remove and prune atomically so the principal key is dropped only while its
// set is empty; otherwise a session added concurrently could be lost. Mirrors
// the blocking SessionRegistryImpl.
this.sessionIdsByPrincipal.computeIfPresent(sessionInformation.getPrincipal(),
		(key, sessionsUsedByPrincipal) -> {
			sessionsUsedByPrincipal.remove(sessionId);
			return sessionsUsedByPrincipal.isEmpty() ? null : sessionsUsedByPrincipal;
		});
```
(수정 후 InMemoryReactiveSessionRegistry.java, `removeSessionInformation`)

원자 단위의 경계가 어디로 옮겨 갔는지를 나란히 놓으면 이렇다.

```text
수정 전 - save                          수정 후 - save
+--------------------------------+     +--------------------------------+
| [원자] computeIfAbsent(P, ...)  |     | [원자] compute(P, (k,set) -> { |
+--------------------------------+     |          set 없으면 새로 만들고 |
|  잠금 밖                        |     |          set.add(sessionId)    |
|        set.add(sessionId)      |     |          return set            |
+--------------------------------+     |        })                      |
                                       +--------------------------------+
  원자 구간이 둘로 쪼개져 있다              집합 조작이 원자 구간 안에 있다

수정 전 - remove                        수정 후 - remove
+--------------------------------+     +--------------------------------+
| [원자] get(P)                   |     | [원자] computeIfPresent(P, ->{ |
+--------------------------------+     |          set.remove(sessionId) |
|  잠금 밖  set.remove(sessionId) |     |          return set.isEmpty()  |
|          set.isEmpty()         |     |                 ? null : set   |
+--------------------------------+     |        })                      |
| [원자] map.remove(P)  조건 없음  |     +--------------------------------+
+--------------------------------+       "비었을 때만" 이 같은 구간 안이다
```

`ConcurrentHashMap`은 같은 키에 대한 재매핑 함수 호출 전체를 원자적으로 실행하고, 그 동안 같은 키의 다른 갱신을 막는다.\
그래서 두 스레드의 작업이 **직렬화**되고 3절의 인터리빙이 성립하지 않는다.

> **직렬화(serialization, 순서 강제)** — 동시에 들어온 작업을 한 줄로 세워 하나씩 끝내는 것.\
> 예: 두 스레드가 같은 키를 동시에 건드려도 하나가 끝난 뒤에 다른 하나가 시작되므로, "중간 상태에서 끼어들기"가 불가능해진다.

```text
 save 가 먼저 잡으면:   set = {S1, S2}  ->  remove 는 S1 만 지우고 {S2} 유지
 remove 가 먼저 잡으면: 키 P 제거       ->  save 가 새 set {S2} 를 만든다
```

어느 순서든 S2가 살아남는다.\
그것이 이 수정이 확립하는 불변식이다.

> **불변식(invariant)** — 어떤 일이 일어나도 늘 참이어야 하는 성질.\
> 예: "동시에 저장한 세션은 유실되지 않는다"가 이 수정이 세우는 불변식이고, 최종 집합이 `{S2}`인지 `{S1, S2}`인지는 그 불변식의 관심 밖이다.

`computeIfPresent`의 재매핑 함수가 `null`을 돌려주면 `ConcurrentHashMap`은 그 키를 제거한다.\
즉 "비었으면 키를 지운다"가 조건부 제거로 바뀌고, **비어 있음을 확인한 그 순간에만** 제거가 일어난다.\
수정 전의 `map.remove(principal)`이 조건 없는 제거였던 것과 대비된다.

한 가지는 그대로 두었다.\
`sessionById.remove(sessionId)`와 `sessionIdsByPrincipal` 갱신 사이에는 여전히 원자성이 없다.\
두 맵을 걸치는 원자성은 보고한 결함(S1/S2 고아 집합)과 별개이며 블로킹 형제도 갖고 있지 않다.\
범위를 넓히면 이 PR이 "레이스 하나 수정"이 아니라 "레지스트리 동시성 모델 재설계"가 된다.

### 검토했으나 기각한 대안

**재매핑 함수가 새 집합을 만들어 반환하는 안**을 검토했다가 기각했다.\
codex 교차검증이 제기한 것으로, 논거는 이렇다 - 2인자 생성자로 `ConcurrentHashMap`이 아닌 `ConcurrentMap` 구현을 주입하면 `compute`/`computeIfPresent`는 인터페이스 default 구현이 되고, 그것은 `get`/`replace`/`remove`를 쓰는 재시도 루프라 원자적이지 않다.\
그 경우 같은 집합 객체를 제자리에서 고치고 참조 동일성으로 CAS하므로 고아 집합이 다시 생길 수 있다.

> **CAS(compare-and-swap, 비교 후 교환)** — "값이 아직 내가 본 그것이면 새 값으로 바꿔라"를 한 번에 처리하는 하드웨어 수준 연산.\
> 예: 같은 집합 객체를 제자리에서 고치면 "값이 그대로인가" 비교가 참을 유지하므로, 실제로는 내용이 바뀌었는데도 교환이 성공해 버린다.

기술적으로 맞다.\
그럼에도 채택하지 않은 이유는 **블로킹 형제가 정확히 같은 가정 위에 있다**는 것이다.\
`SessionRegistryImpl`도 같은 맵 주입 생성자(`:66-70`)와 같은 compute 패턴을 쓰고 이미 출시돼 있다.\
이 수정은 형제와의 동등성을 회복할 뿐 새 한계를 들여오지 않는다.\
반대로 리액티브 쪽만 새 집합 반환으로 바꾸면 자료구조와 성능 특성이 형제와 갈리고, "왜 여기만 다른가"라는 질문이 남는다.\
임의 `ConcurrentMap` 주입을 계약으로 지원할지는 두 클래스 모두에 대한 별개 논의다.

**결정론적 인터리빙 테스트**(제거 도중 멈추는 맵 래퍼를 주입해 순서를 강제)도 검토했다.\
확률적 스트레스 테스트보다 우아하지만 복잡하고, 스트레스 테스트가 이미 red를 재현했으므로 현행을 유지했다.

### 성능 트레이드오프

수정 전 `computeIfAbsent`는 키가 이미 있으면 재매핑 없이 즉시 반환하므로 갱신 잠금을 피했다.\
새 `compute`는 매번 재매핑을 거치므로 같은 principal에 대한 경합이 조금 늘어난다.\
**의도한 교환**이다.\
원자성을 위해 지불하는 비용이고, 블로킹 형제가 이미 같은 비용을 지불하고 있다.\
재매핑 함수 안에서 하는 일은 집합 하나에 대한 add/remove뿐이고 맵으로 재진입하지 않으므로 데드락 경로도 없다.

> **경합(contention)** — 여러 스레드가 같은 잠금을 두고 서로 기다리게 되는 상황.\
> 예: 같은 사용자의 세션을 동시에 여럿 저장하면 이제 그 키의 잠금을 차례로 기다리므로, 아주 조금 느려진다.

> **데드락(deadlock)** — 서로가 가진 잠금을 기다리며 둘 다 영원히 멈추는 상태.\
> 예: 재매핑 함수 안에서 다시 같은 맵을 부르면 그런 경로가 생길 수 있는데, 여기서는 집합만 만지므로 그 경로가 없다.

## 5. 검증

레이스는 결정론적 단위 테스트로 잡을 수 없다는 것이 이 결함의 출발점이었다.\
그래서 **1000회 반복 + 래치 동기화 스트레스 테스트**를 쓰고, 그것이 진짜 가드인지를 실측으로 확인했다.

> **래치(CountDownLatch)** — 여러 스레드를 한 지점에 세워 두었다가 동시에 출발시키는 동기화 장치.\
> 예: 두 작업을 제출한 뒤 래치를 내리면 둘이 같은 순간에 달리기 시작하므로, 좁은 레이스 창에 들어갈 확률이 크게 오른다.

확인 방법이 이 PR의 핵심 절차다.\
**소스 수정만 `git stash`로 되돌리고 같은 테스트를 원본 코드에 돌렸다.**\
결과는 `saveAndRemoveConcurrentlyThenAddedSessionNotLost` FAILED - 세션 유실이 실제로 재현됐다.\
수정을 복원하면 green.\
이로써 "이론상 가능한 인터리빙"이 "실측으로 재현된 결함"이 됐고, 테스트가 회귀를 실제로 막는다는 것도 함께 증명됐다.

> **git stash** — 작업 중인 변경을 잠시 떼어 보관했다가 나중에 되돌려 붙이는 git 기능.\
> 예: 프로덕션 수정만 떼어 내고 새 테스트는 그대로 둔 채 돌리면, "이 테스트가 옛 코드에서 정말 실패하나"를 확인할 수 있다.

fix 후 `InMemoryReactiveSessionRegistryTests` 5건 green, `core.session` 패키지 회귀 0, `checkstyle`/`checkFormat`(core main + web test) 통과.\
상세는 [tests.md](tests.md).

stakes는 **중간**으로 판정했다(동시성·세션 무결성 문제이고 동시 세션 제어 계산이 어긋날 수 있지만 데이터 손상은 아니다).\
codex 교차검증은 **조건부 승인**이었다 - 기본 `ConcurrentHashMap`에서는 정확하고, 임의 `ConcurrentMap` 주입 시 의문이 남는다는 판정.\
그 의문은 위에서 본 대로 형제 동등성 논거로 답했고 코드는 바꾸지 않았다.

## 6. 상태와 리뷰 대응

제출 후 메인테이너 리뷰는 아직 없다.\
대신 외부 기여자 `ronodhirSoumik`이 인라인 코멘트 3건을 남겼고, 모두 버그 지적이 아니라 스타일·모듈화 제안이었다.\
그 대응 과정이 이 PR에서 가장 많은 것을 남겼다.

| 코멘트 | 제안 | 1차 결정 | 최종 |
|---|---|---|---|
| 프로덕션 add/remove 로직 | `addSessionToSet`/`removeSessionFromSet` 헬퍼로 추출 | 유지 | 유지 |
| 람다 파라미터 이름 | `sessionsUsedByPrincipal` -> `sessions` | 유지 | 유지 |
| 테스트 1000회 루프 본문 | 함수로 추출 | 유지 | **반영** |

앞의 둘을 유지한 근거는 같다 - **블로킹 형제가 같은 변경을 인라인으로 수행하고 같은 파라미터 이름을 쓴다.**\
이 PR의 목적 자체가 형제와의 정합이므로 정합 논거가 취향 제안을 이긴다고 판단했다.\
헬퍼 추출은 원자성을 깨지는 않지만 "이 코드는 반드시 compute 블록 안에서 돌아야 한다"는 의도가 덜 보이게 되고, 제안된 시그니처에는 쓰이지 않는 `principal` 파라미터도 있었다.

셋째는 결정을 **번복**했다.\
처음에는 같은 논거(동시성 테스트는 setup·동시 실행·단언을 한자리에 둬야 감사하기 쉽다)로 유지했는데, 리뷰어가 "유지보수가 아니라 가독성 때문에 제안한 것"이라고 의도를 명확히 했다.\
그 관점에서 다시 보니 **테스트는 신규 코드라 미러링 대상이 없다** - 앞의 둘을 지탱하던 정합 논거가 여기서는 성립하지 않고, 남는 것은 순수 가독성 판단이다.\
그리고 루프가 "이 레이스를 1000번 돌린다"로 읽히는 편이 낫고, 단언을 헬퍼 안에 남기면 실패 추적성도 잃지 않는다.\
헬퍼 `assertAddedSessionSurvivesConcurrentSaveAndRemove(...)`로 추출하고 후속 커밋을 올렸다.

그 후속 커밋에서 DCO 사고가 하나 있었다.\
처음 올린 커밋(`ed74f650`)에 sign-off가 빠져 DCO 체크가 실패했는데, **DCO는 PR의 모든 커밋을 검사하므로 새 커밋을 얹어서는 고칠 수 없다.**\
`git commit --amend -s` + `--force-with-lease`로 커밋 객체 자체를 다시 만들어야 했고, amend가 SHA를 바꾸는 바람에(`ed74f650` -> `72feea0d`) 리뷰 답글에 적어 둔 짧은 SHA가 가리키는 대상이 없어져 그 코멘트도 갱신해야 했다.

> **DCO(Developer Certificate of Origin)** — 커밋마다 `Signed-off-by:` 줄로 "이 코드를 내가 기여할 권리가 있다"고 밝히는 절차.\
> 예: 스프링 프로젝트의 CI가 PR의 모든 커밋에서 그 줄을 찾으므로, 한 커밋에만 빠져도 체크가 빨갛게 뜬다.

## 7. 교훈

이 레이스가 남긴 것은 원자 단위 경계, 재현 기법, 형제 정합, 결정 번복 넷이다.

1. **스레드 안전한 컬렉션을 스레드 안전하지 않게 쓸 수 있다.**\
   `ConcurrentMap`과 `CopyOnWriteArraySet`을 썼는데도 레이스가 난 이유는 원자 단위의 경계가 각 호출 안에만 있고 **호출 사이에는 없기** 때문이다.\
   `computeIfAbsent(...).add(...)`는 한 줄처럼 보이지만 원자 연산 하나와 그 밖의 연산 하나다.\
   자료구조 선택이 아니라 **경계를 어디에 긋는가**가 문제다.
2. **레이스도 red를 만들 수 있다.**\
   "결정론적 테스트가 불가능하다"가 "검증 없이 낸다"의 근거가 되면 안 된다.\
   소스 수정만 되돌려 원본 코드에 같은 스트레스 테스트를 돌리는 방법으로, 이론상의 인터리빙을 실측 재현으로 바꿨다.\
   그 실측이 PR의 설득력과 테스트의 가드 자격을 동시에 확보했다.
3. **형제 구현과의 정합은 강력한 논거다.**\
   "이 동시성이 실재하나"라는 의문에도, codex의 임의 맵 주입 지적에도, 리뷰어의 스타일 제안에도 같은 답이 통했다 - 블로킹 `SessionRegistryImpl`이 같은 자료구조에서 같은 방식으로 이미 하고 있다.\
   새 위험을 상상하지 않고 **이미 인정된 위험의 미적용 지점**을 지목하는 것이 리뷰 부담을 크게 줄인다.
4. **정합 논거가 성립하지 않는 자리에서는 취향 제안이 이길 수 있다.**\
   프로덕션 코드는 미러링 대상이 있어 유지했지만 테스트는 신규 코드라 그 논거가 없었다.\
   같은 리뷰의 세 코멘트를 일괄 처리하지 않고 건별로 판정한 것, 새 정보(리뷰어의 의도 설명)가 들어왔을 때 이전 결정을 번복한 것이 이 PR에서 배운 태도다.
