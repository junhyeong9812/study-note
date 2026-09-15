# issue1 — 동적 라우트 + 블루-그린 전환 내부 API

- 원본 PR: gateway #2 · devlog: `jun-bank/gateway/docs/devlog/pr-02-dynamic-route.md`

## 1. 무엇이 문제였나

무중단 배포를 블루-그린으로 한다는 결정은 있었지만, 전환이 "무엇을 조작하는가"는 오래 비어 있었다.\
엣지 nginx 설정 교체인가, compose 포트 스왑인가, 아니면 gateway 라우트 전환인가가 정해지지 않았다.

> **블루-그린 배포(blue-green)** — 같은 서비스를 두 벌(블루·그린) 띄워 두고, 트래픽을 한쪽에서 다른 쪽으로 통째로 옮겨 무중단으로 새 버전을 내보내는 방식.\
> 예: 손님을 받던 1번 창구를 닫는 대신, 미리 준비한 2번 창구로 줄을 옮기고 1번을 정리한다.

정적 라우트로는 전환이 불가능하다.\
라우팅 규칙이 `application.yml`에 선언돼 있으면 대상을 바꾸는 데 재시작이 필요하고, 그건 무중단이 아니다.

더 깊은 문제가 하나 더 있었다.\
배포 agent의 락 재확인과 gateway의 라우트 갱신은 별개의 부작용이라, 재확인 직후 lease를 잃은 낡은(stale) 실행자의 write가 최종 라우트로 남을 수 있다.\
이건 분산 락의 고전적 문제다.

> **fencing token** — 매번 1씩 커지는 번호표.\
> 늦게 도착한 낡은 실행자가 예전 번호표를 들고 오면, 자원 쪽이 "그건 지난 번호"라며 거부한다.

> **lease** — 시한부 소유권. 시간이 지나면 자동으로 풀린다.\
> lease가 풀린 줄 모르고 계속 쓰기를 하는 실행자가 위의 stale 실행자다.

## 2. 무엇을 고민했나

전환 수단을 무엇으로 삼을지 네 안을 놓고 봤다.

- **SCG 라우트 전환** — 전환은 "어느 인스턴스로 보내나"를 바꾸는 일이고, 그 결정은 이미 SCG가 라우트로 내리고 있다.\
  별도 스왑 기구를 새로 만들지 않아 도구가 늘지 않는다. (채택)
- **큐 기반 라우팅** — 모든 요청에 큐 홉 지연을 상시로 붙인다.\
  전환 제어는 큐 없이 드레인으로 성립하고, 가시성은 큐가 아니라 트레이싱의 몫이다. (기각)
- **엣지 nginx upstream 전환** — 내부 서비스 전환을 위해 공유 엣지를 건드리는 반경이 크다.\
  설정 오류의 반경이 남의 도메인까지 커진다. (기각)
- **compose 포트 스왑** — 스왑 순간의 원자성이 약하고 라우팅 결정을 두 곳으로 흩는다. (기각)

> **SCG(Spring Cloud Gateway)** — 스프링이 제공하는 API 게이트웨이. 들어온 요청을 라우트 규칙에 따라 뒤쪽 서비스로 넘긴다.\
> 예: "이 경로로 온 요청은 블루 슬롯으로"라는 규칙을 코드로 바꿔 끼우면 전환이 된다.

구현 후에 "서비스별 nginx를 앞에 두고 conf를 고쳐 전환하는 방식은 어떤가"를 다시 물어 재평가했다.\
결론은 "나쁘지 않으나 이득 없음"이었다.\
nginx reload가 드레인을 내장한다는 장점은 인정하되, fencing 검증을 sink(자원 쪽)에 둘 수 없다는 점이 결정적이었다 — conf 파일을 쓰는 쪽이 곧 실행자라 sink가 거부할 지점이 없다.\
운영 대상 +3과 홉 증가도 불리했다.

## 3. 그래서 이렇게

SCG 라우트 전환을 택하되, 상태의 정본을 한 곳으로 모으고 변경 경로를 하나로 좁혔다.

라우트 상태(활성 슬롯 + 마지막 수락 token)의 정본은 `CoreRouteRegistry` 하나다.\
gateway는 이 스냅샷 하나만 보고 라우트를 만들고, 조회 API도 같은 스냅샷을 읽는다.\
라우트 변경은 전환 API 한 경로로만 들어온다.

교체 순서는 write-ahead다.

> **write-ahead** — 실제로 바꾸기 전에 "무엇으로 바꿀지"를 먼저 기록해 두는 방식.\
> 예: 이사 가기 전에 새 주소를 먼저 등기해 두면, 중간에 쓰러져도 어디로 가려 했는지 남는다.

```text
목표 상태를 파일에 먼저 기록          기록 실패면 전환을 시작조차 안 함
        ↓
라우트를 원자 교체                    registry.replace
        ↓
요청을 태우는 캐시를 다시 읽어 확인    우리 상태만 다시 읽으면 자기증명이라 안 됨
        ↓
반영됐으면 Applied                    실패면 이전 슬롯으로 원복
        ↓
원복까지 확인돼야 "미전환 보증" 응답   원복 미확인이면 Indeterminate
```

## 4. 코드 — 실제 커밋에서

라우트 변경 경로를 하나로 막는다.

```kotlin
// routeswitch/CoreRouteRegistry.kt:94-99
// 라우트 변경은 /internal/routes/core/switch 한 경로로만 들어온다 — 임의 write는 막는다.
override fun save(route: Mono<RouteDefinition>): Mono<Void> =
    Mono.error(UnsupportedOperationException("core route is switched via /internal/routes/core/switch"))
```

전환은 단조 fencing token으로 보호한다 — 같은 token 재요청은 멱등 재시도로 수락하고, 작은 token만 거부한다.

```kotlin
// routeswitch/RouteSwitchService.kt:62-67 (발췌)
fun switchTo(target: Slot, token: Long): Result = synchronized(writeLock) {
    val before = registry.snapshot()
    if (token < before.lastAcceptedToken) {
        return Result.Stale(before.lastAcceptedToken)
    }
    ...
```

교체 순서(write-ahead → 원자 교체 → 반영 확인 → 실패 시 원복)를 코드가 그대로 밟는다.

```kotlin
// routeswitch/RouteSwitchService.kt:84-107 (발췌)
// ⑴ write-ahead: 라우트를 바꾸기 전에 목표 상태를 먼저 남긴다(기록 실패 = 전환 시작 안 함).
stateStore.write(CoreStateStore.State(target, token))
// ⑵ 원자 교체 + 반영 확인
registry.replace(CoreRouteRegistry.Snapshot(target, token))
if (refreshAndAwait(expected)) { ... return Result.Applied(target, token) }
// ⑶ 반영 확인 실패 → 원복. 원복까지 확인돼야 "미전환 보증"을 답할 수 있다.
return if (rollback(before, token)) Result.RolledBack(reason)
       else Result.Indeterminate("$reason; rollback not verified")
```

## 5. 구현 중 마주친 문제

가장 크게 뒤집힌 것은 **실패 응답의 보증 계약**이다.\
처음에는 전환 실패(409든 500이든 전송 실패든)를 일괄 "미전환"으로 접고 유휴 슬롯을 내렸다.\
그런데 409는 소유권 상실 신호다 — 그 순간 내려가는 슬롯은 새 소유자(승자)가 방금 올린 쪽일 수 있다.\
그래서 실패 응답에 상태를 싣는 계약을 신설했다.

```kotlin
// routeswitch/InternalRouteController.kt:25-28 (계약 주석)
// 실패 응답 계약: 호출자(배포 agent)는 "미전환이 보증되는 실패"와 "실상태 불명 실패"를
// 구별해야 한다 — 불명인데 미전환으로 오판하면 서비스 중인 slot을 내리게 된다.
// NOT_ATTEMPTED(409) · ROLLED_BACK(500) 은 미전환 보증, INDETERMINATE(500) 은 재확인 필요.
```

agent는 보증 없는 실패에 어느 슬롯도 내리지 않는다.

되돌린 것 셋이 더 있었다.

- 원복이 스냅샷 전체를 복구해 token 최고수위가 후퇴하던 것을, 슬롯만 복구하도록 정정했다(stale 재수락 차단).
- 재시작이 env 기본값으로 복귀해 죽은 슬롯을 가리키던 것을, `CoreStateStore`(write-ahead 상태 파일)로 해소했다.
- 조회가 전환 임계구역 밖에서 잠정 상태를 노출하던 것을 직렬화했다.

상태 파일은 부재만 env 폴백을 허용하고, 손상·I/O 오류는 기동을 거절한다.\
손상을 조용히 접으면 이미 내려간 슬롯을 가리키고 지나간 token을 다시 수락하게 되기 때문이다.

## 6. 결론

라우트 상태의 정본이 한 곳으로 모였고, 전환은 write-ahead + fencing token으로 보호된다.\
검증은 테스트 21건, 실서버 무중단 관측 누계 5,475건 실패 0(배포 관통 3회 포함), 부분 실패 1회의 안전 거동(배포 미시작·부작용 0·락 해제)이었다.

남은 빚은 그대로 다음 이슈가 됐다.

- `/internal`이 무인증이다 — fencing은 순서 보호지 인가가 아니다 → issue4(#6 인가).
- CI가 테스트를 안 돌린다 → PR #5(issue3).
- 재기동 교체 경로가 없다 → #3/#4(issue2).
