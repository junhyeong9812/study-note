# PR #19339 - 테스트 해설 (테스트 하나하나)

> `InMemoryReactiveSessionRegistryTests`에 추가된 1건 + 기존 테스트가 맡은 가드 역할.
> 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로 해설한다.
> 문제와 수정은 [README.md](README.md), 실구조는 [structure.md](structure.md),
> 착수 분석은 [analysis.md](analysis.md).

배치 전체를 먼저 본다. 이 결함은 **두 연산이 동시에 실행될 때만** 나타나므로, 새 테스트
하나가 "동시 실행"을 맡고 기존 네 건이 전부 "순차 실행"을 맡는 구도가 된다. 그래야 fix가
"순차 동작은 그대로 두고 동시 동작만 고쳤다"를 증명한다.

| 무대 | 동시 실행 | 순차 실행 |
|---|---|---|
| save + remove (같은 principal) | T1 `saveAndRemoveConcurrentlyThenAddedSessionNotLost` - **red** | T2 `removeSessionInformationThenSessionIsRemoved`(기존) - 가드 |
| save 만 | - | T3 `saveWhenPrincipalThenRegisterPrincipalSession` / `getAllSessionsWhenMultipleSessionsThenReturnAll`(기존) - 가드 |

테스트 파일이 `web` 모듈에 있다는 점을 먼저 짚어 둔다. 프로덕션 클래스는
`core/.../core/session/`에 있는데 테스트는
`web/src/test/java/org/springframework/security/web/server/authentication/session/`에 있다.
클래스가 web에서 core로 이관되면서 테스트가 따라가지 않은 흔적으로 보이며, 새 테스트도
같은 자리에 두는 것이 기존 테스트와 함께 실행되므로 자연스럽다고 판단했다.

## T1. 동시 save/remove 스트레스 - red

새로 추가한 한 건은 같은 principal에 대해 제거와 저장을 래치로 동시에 출발시키고, 방금
저장한 세션이 살아 있는지 묻는다. 아래는 후속 커밋(`72feea0d`)으로 헬퍼를 추출한
최종 형태다.

```java
@Test
void saveAndRemoveConcurrentlyThenAddedSessionNotLost() throws Exception {
	Authentication authentication = TestAuthentication.authenticatedUser();
	Object principal = authentication.getPrincipal();
	ExecutorService executor = Executors.newFixedThreadPool(2);
	try {
		for (int i = 0; i < 1000; i++) {
			assertAddedSessionSurvivesConcurrentSaveAndRemove(principal, "existing-" + i, "added-" + i, executor);
		}
	}
	finally {
		executor.shutdownNow();
	}
}
```

```java
// Runs one concurrent save/remove race for the principal and asserts the
// concurrently added session is not lost.
private void assertAddedSessionSurvivesConcurrentSaveAndRemove(Object principal, String existing, String added,
		ExecutorService executor) throws Exception {
	this.sessionRegistry.saveSessionInformation(new ReactiveSessionInformation(principal, existing, this.now))
		.block();
	CountDownLatch start = new CountDownLatch(1);
	Future<?> remove = executor.submit(() -> {
		awaitUninterruptibly(start);
		this.sessionRegistry.removeSessionInformation(existing).block();
	});
	Future<?> save = executor.submit(() -> {
		awaitUninterruptibly(start);
		this.sessionRegistry.saveSessionInformation(new ReactiveSessionInformation(principal, added, this.now))
			.block();
	});
	start.countDown();
	remove.get();
	save.get();
	List<ReactiveSessionInformation> sessions = this.sessionRegistry.getAllSessions(principal)
		.collectList()
		.block();
	assertThat(sessions).extracting(ReactiveSessionInformation::getSessionId).contains(added);
	this.sessionRegistry.removeSessionInformation(added).block();
}
```
(InMemoryReactiveSessionRegistryTests.java, 최종 형태)

- **주장**: 같은 principal의 마지막 세션을 제거하는 것과 새 세션을 저장하는 것이 동시에
  일어나도, 새로 저장한 세션은 조회 가능해야 한다.
- **fix 전 red인 이유**: 수정 전 `removeSessionInformation`이 조건 없는
  `map.remove(principal)`로 키를 지우므로(수정 전 `:80`), 그 직전에 `computeIfAbsent`로
  같은 집합을 받아 `added`를 넣은 저장 스레드의 결과가 키째로 사라진다. 그러면
  `getAllSessions(principal)`이 비어 있고 `contains(added)` 단언이 실패한다.

**설계 요소 하나하나에 이유가 있다.**

- `CountDownLatch start` - 두 작업을 `submit`한 뒤 래치를 내려 **동시에 출발**시킨다.
  래치 없이 그냥 제출하면 첫 작업이 끝난 뒤에 둘째가 시작될 수 있어 레이스 창이 열리지
  않는다. 좁은 창을 겨냥한 테스트에서 출발선을 맞추는 것이 적중률을 좌우한다.
- `Executors.newFixedThreadPool(2)` - 스레드 둘을 미리 만들어 루프 1000회 내내 재사용한다.
  회차마다 스레드를 만들면 생성 비용이 레이스 창보다 커져 오히려 인터리빙이 덜 일어난다.
- `existing-i` / `added-i`처럼 회차마다 다른 세션 id - 회차 간 상태가 섞이지 않게 한다.
  회차 끝에서 `removeSessionInformation(added)`로 정리까지 하므로, 각 회차는 "principal이
  세션 하나를 갖고 있는" 같은 출발 상태에서 시작한다. 3절에서 본 인터리빙의 전제가 바로
  그 상태다.
- **1000회 반복** - 이 결함의 창은 `isEmpty()` 확인과 `map.remove` 사이의 몇 나노초다.
  한 번 돌려서는 거의 안 걸리므로 반복이 필수다. 반대로 fix 후에는 어느 회차에서도
  실패하지 않아야 하므로 반복은 그린 쪽에서도 신뢰도를 높인다.
- `remove.get()` / `save.get()` - 두 작업이 **끝난 뒤에** 단언한다. `Future.get()`은 작업
  안에서 던진 예외도 여기서 다시 던지므로, 조용히 실패한 작업을 놓치지 않는다.
- `awaitUninterruptibly` 헬퍼 - `latch.await()`의 `InterruptedException`을 삼키지 않고
  인터럽트 플래그를 복원한 뒤 런타임 예외로 감싼다. 테스트 종료 시
  `executor.shutdownNow()`가 인터럽트를 보내므로 그 경로를 명시적으로 처리한다.

**단언이 `getAllSessions`를 거치는 이유.** 이 결함이 잃어버리는 것은 세션 정보 자체가
아니라 **principal -> sessionIds 매핑**이다. `sessionById`에는 `added`가 그대로 남아
있으므로 `getSessionInformation(added)`로 물으면 결함 상태에서도 값이 나온다.
`getAllSessions(principal)`은 `sessionIdsByPrincipal`을 거쳐 조회하므로(`:54-57`) 고아가 된
세션을 정확히 드러낸다. **어느 API로 관측하느냐가 red 여부를 가른다.**

`.extracting(ReactiveSessionInformation::getSessionId).contains(added)`에서
`hasSize(1)`이나 `containsExactly`가 아니라 `contains`를 쓴 것도 의도적이다. 두 작업의
실행 순서에 따라 최종 집합이 `{added}`일 수도 `{existing, added}`일 수도 있다 - 제거가
먼저 잡히면 전자, 저장이 먼저 잡히면 후자다. 둘 다 정상이며 **주장은 "added가 살아
있다"이지 "집합이 정확히 이것이다"가 아니다.** 단언을 좁게 잡았다면 fix 후에도
flaky해졌을 것이다.

### 후속 커밋 - 루프 본문을 헬퍼로

이 테스트는 처음에 루프 본문이 전부 인라인이었다. 외부 기여자 리뷰를 받아 후속
커밋(`72feea0d`)에서 위 형태로 추출했고, **동작은 한 줄도 바뀌지 않았다.** 추출 단위는
"레이스 하나 = 헬퍼 하나"이고, 그래서 루프가 "이 레이스를 1000번 돌린다"로 읽힌다.
단언을 헬퍼 밖으로 빼지 않고 안에 남긴 것이 요점인데, 실패 스택이 헬퍼의 그 줄을 가리키므로
추적성을 잃지 않는다. 처음 유지 결정을 낼 때의 반대 논거("추출하면 메커니즘이 가려진다")가
이 배치로 해소됐다.

## T2. 기존 `removeSessionInformationThenSessionIsRemoved` - 순차 제거 가드 (전후 green)

새 테스트가 "동시 실행"을 맡는 동안, 순차 실행에서 아무것도 안 바뀌었음을 고정하는 쪽은
기존 테스트다.

```java
@Test
void removeSessionInformationThenSessionIsRemoved() {
	Authentication authentication = TestAuthentication.authenticatedUser();
	ReactiveSessionInformation sessionInformation = new ReactiveSessionInformation(authentication.getPrincipal(),
			"1234", this.now);
	this.sessionRegistry.saveSessionInformation(sessionInformation).block();
	this.sessionRegistry.removeSessionInformation("1234").block();
	List<ReactiveSessionInformation> sessions = this.sessionRegistry.getAllSessions(authentication.getName())
		.collectList()
		.block();
	assertThat(this.sessionRegistry.getSessionInformation("1234").block()).isNull();
	assertThat(sessions).isEmpty();
}
```
(InMemoryReactiveSessionRegistryTests.java:77-89)

- **fix 전후 모두 green**이다. 한 스레드가 저장하고 제거하므로 인터리빙이 없고, 결과는
  두 구현에서 같다.
- 이 가드가 검증하는 것은 **정리 규칙이 살아 있다**는 사실이다. 수정이
  `computeIfPresent`의 `null` 반환으로 키 제거 방식을 바꿨으므로, "마지막 세션이 사라지면
  키도 사라진다"가 여전히 성립하는지 확인해야 한다. `sessions`가 비어 있다는 단언이 그
  역할을 한다.
- 이 테스트가 없었다면 `computeIfPresent`가 빈 집합을 그대로 남기는 구현(예:
  `return sessionsUsedByPrincipal;`만 하는 실수)도 T1을 통과했을 것이다. 두 테스트가
  **원자성과 정리 규칙을 나눠서** 지킨다.

## T3. 기존 저장·조회 가드 - 기본 경로 (전후 green)

`saveWhenPrincipalThenRegisterPrincipalSession`(:42-54)과
`getAllSessionsWhenMultipleSessionsThenReturnAll`(:56-75)은 저장 경로를 지킨다.

- 앞의 것은 세션 하나를 저장한 뒤 `getAllSessions`가 1건을 돌려주고
  `getSessionInformation`도 값을 돌려주는지 본다. 수정이 `computeIfAbsent`를 `compute`로
  바꿨으므로, **키가 없을 때 새 집합을 만드는 분기**가 여전히 동작하는지가 여기서
  확인된다.
- 뒤의 것은 같은 principal로 세 번 저장해 3건이 조회되는지 본다. **키가 이미 있을 때
  기존 집합에 더하는 분기**를 지킨다. 수정 전에는 이 분기가 `computeIfAbsent`의 "이미
  있으면 그대로 반환" + 람다 밖 `.add()`였고, 수정 후에는 재매핑 함수 안의 `null` 검사
  실패 + `add()`다. 두 분기가 모두 green이어야 수정이 저장 동작을 보존했다고 말할 수 있다.
- `updateLastAccessTimeThenUpdated`(:91-104)는 `sessionById`만 만지므로 이 수정과 무관하고,
  변경이 그쪽으로 새지 않았음을 부수적으로 확인해 준다.

## 실측 요약

이 PR의 검증에서 가장 중요한 것은 테스트가 **실제로 red를 만들어 냈다**는 확인이다.

- **red 재현 기법**: 소스 수정만 `git stash`로 되돌리고 원본 코드에 같은 스트레스 테스트를
  돌렸다. `saveAndRemoveConcurrentlyThenAddedSessionNotLost` **FAILED** - 세션 유실 재현.
  수정을 복원하면 green. 레이스 결함에서 "결정론적 테스트가 불가능하다"가 검증 생략의
  근거가 되지 않도록 만든 절차다.
- **fix 후**: `InMemoryReactiveSessionRegistryTests` 5건 green,
  `org.springframework.security.core.session` 패키지 회귀 0.
- **후속 커밋 후**: `:spring-security-web:checkFormatTest` 통과, 테스트 클래스
  `BUILD SUCCESSFUL`(1000회 레이스 그대로 green).
- **스타일**: `checkstyle`/`checkFormat`(core main + web test) 통과. 깊은 들여쓰기
  (`doOnNext` 람다 안)에서 포맷터가 주석을 지저분하게 쪼개, 짧은 문장으로 다시 써서
  해결했다.
- **diff 규모**: 최초 커밋 2파일 +48/-10 (프로덕션 `+19/-8`), 후속 커밋은 테스트 1파일이며
  동작 변경 0.

## 남은 한계 - 확률적이라는 것

이 스트레스 테스트는 결정론적이지 않다. fix된 코드에서는 최종 상태가 어느 인터리빙에서도
같으므로 flaky하지 않지만, **옛 버그를 잡는 쪽은 스케줄 의존적**이다. 1000회에서 실제로
재현되는 것을 확인했으나 이론적으로는 놓칠 수 있다.

codex가 제안한 결정론적 대안은 이렇다 - 제거 도중(집합이 빈 직후, 키 제거 직전) 멈추는
맵 래퍼를 주입해 그 사이에 저장이 끼어들도록 순서를 강제한다. 더 우아하지만 테스트
복잡도가 크게 오르고, 이 결함의 red가 이미 실측으로 확보됐으므로 채택하지 않고 기록만
남겼다. 메인테이너가 결정론적 형태를 선호하면 전환할 수 있는 여지로 남아 있다.
