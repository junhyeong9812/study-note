# 만료

상위: [lane 흐름](../README.md)

**기아를 막는 안전장치**다. 오래 기다린 lane 을 만료로 표시하면 [렌더 루프](../../render-loop/README.md)가 양보를 끄고 동기로 밀어붙인다.

## 위치

등급별 시각 `packages/react-reconciler` / `src` / `ReactFiberLane.js` L477-L539 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberLane.js#L477-L539))

표시 `packages/react-reconciler` / `src` / `ReactFiberLane.js` L541-L588 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberLane.js#L541-L588))

## 실제 코드

사용자 상호작용은 더 빨리 만료한다. 그 주석이 자기비판을 담는다.

```js
// ReactFiberLane.js L484-L493
      // User interactions should expire slightly more quickly.
      //
      // NOTE: This is set to the corresponding constant as in Scheduler.js.
      // When we made it larger, a product metric in www regressed, suggesting
      // there's a user interaction that's being starved by a series of
      // synchronous updates. If that theory is correct, the proper solution is
      // to fix the starvation. However, this scenario supports the idea that
      // expiration times are an important safeguard when starvation
      // does happen.
      return currentTime + syncLaneExpirationMs;
```

> User interactions should expire **slightly** more quickly. ... When we made it larger, a product metric in www regressed, **suggesting** there's a user interaction that's being starved by a series of synchronous updates. **If that theory is correct**, the proper solution is to fix the starvation. However, this scenario supports the idea that expiration times are an important safeguard when starvation does happen.

retry 쪽에도 TODO 가 붙어 있다.

```js
// ReactFiberLane.js L516-L523
      // TODO: Retries should be allowed to expire if they are CPU bound for
      // too long, but when I made this change it caused a spike in browser
      // crashes. There must be some other underlying bug; not super urgent but
      // ideally should figure out why and fix it. Unfortunately we don't have
      // a repro for the crashes, only detected via production metrics.
      return enableRetryLaneExpiration
        ? currentTime + retryLaneExpirationMs
        : NoTimestamp;
```

> TODO: Retries **should be allowed to** expire **if they are CPU bound for too long**, but when I made this change it caused a spike in browser crashes. **There must be some other underlying bug**; **not super urgent but ideally** should figure out why and fix it. Unfortunately we don't have a repro for the crashes, only detected via production metrics.

## 등급표

| 그룹 | lane | 만료 시각 |
|---|---|---|
| 사용자 상호작용 (5) | SyncHydration, Sync, InputContinuousHydration, InputContinuous, **Gesture** | `+ syncLaneExpirationMs` (L493) |
| 기본·트랜지션 (17) | **DefaultHydration**, Default, TransitionHydration, TransitionLane1~14 | `+ transitionLaneExpirationMs` (L511) |
| retry (4) | RetryLane1~4 | 플래그가 켜져야 만료 (L521-523) |
| idle 이하 (5) | SelectiveHydration, IdleHydration, Idle, Offscreen, Deferred | `NoTimestamp` (L530) |
| default | — | DEV 에서 `console.error` 후 `NoTimestamp` |

case 레이블은 31개 + `default` 하나다. `TotalLanes` 와 같은 수다.

```text
 ★ 만료는 2패스로 일어난다

 markStarvedLanesAsExpired 가 한 번 불릴 때
 lane 하나에 대해 둘 중 하나만 한다

 (가) L570  expirationTimes[index] === NoTimestamp 이면
              아직 시계가 안 걸린 lane 이다
     L575    서스펜드 안 됐거나
     L576    ping 됐으면
     L579      expirationTimes[index] = computeExpirationTime(lane, currentTime)
              => 시계를 건다

 (나) L581  expirationTime <= currentTime 이면
     L583    root.expiredLanes |= lane
              => 만료로 표시한다

 한 번에 둘 다 하지 않는다.
 시계를 건 뒤, 나중 호출에서 시각이 지났을 때 표시한다

 ★ L583 이 expiredLanes 를 세우는 **유일한 줄**이다
   (저장소 전체에서 세움 L583, 지움 L916, 읽음 L699 뿐)
```

```text
 서스펜드된 채 ping 도 안 된 lane 은 시계를 안 건다

 L575-576 의 조건이 그것이다

 => I/O 를 기다리는 것은 기아가 아니라는 판단이다.
    CPU 에 묶여 못 나아가는 것만 기아로 본다
```

```text
 ★ idle 이 만료되지 않는 기전은 순회 제외가 아니다

 idle lane 도 pendingLanes 에 있으면 **매번 순회된다**.
 L562-564 가 빼는 것은 retry 뿐이다

 막는 것은 computeExpirationTime 의 반환값이다 -
 idle 계열은 L524-530 에서 NoTimestamp 를 돌려주므로
 L579 가 NoTimestamp 를 다시 써 넣고,
 다음 호출도 (가) 갈래로만 돈다. 영원히 L581 에 닿지 않는다

 반면 retry 는 기전이 다르다 -
 enableRetryLaneExpiration 이 꺼져 있어
 L562-564 에서 **순회 대상에서 아예 빠진다**
   주석 L559-560 - retry lane 은 언제나 시간 분할돼야 한다.
   캐시되지 않은 promise 를 풀어내야 하기 때문이다
   바로 옆 L561 에 "TODO: Write a test for this" 가 붙어 있다

 => "만료 안 함" 이 두 가지 다른 이유로 일어난다
 (이 구분은 검증 과정에서 확인된 것이고,
  나는 L562-564 와 L524-530 의 구조를 직접 봤다)
```

```text
 부르는 곳이 하나뿐이다

 [스케줄링]의 scheduleTaskForRootDuringMicrotask 맨 앞

 그래서 TODO 가 붙어 있다 (L545-547)
   "This gets called every time we yield. We can optimize by storing
    the earliest expiration time on the root. Then use that to quickly
    bail out of this function."

 매 마이크로태스크마다 lane 전체를 훑는다는 뜻이다
```

```text
 만료가 쓰이는 곳은 한 줄이다

 includesExpiredLane (L696) -> [렌더 루프]의 shouldTimeSlice

 shouldTimeSlice 가 거짓이 되면 양보 없이 동기로 끝까지 간다

 주석 L697-698 이 includesBlockingLane 과 따로 둔 이유를 적는다 -
 렌더가 시작된 뒤에도 만료될 수 있기 때문이다
```

## 결과가 쓰이는 곳

```text
 root.expirationTimes[index]
      --> 시계다. 한 번 걸리면 그 lane 이 언제 급해지는지 정해진다
      --> markRootSuspended 가 서스펜드된 lane 의 시계를 지운다
          (I/O 대기는 기아가 아니므로)

 root.expiredLanes
      --> includesExpiredLane 이 읽는다
      --> shouldTimeSlice 를 꺼서 동기 렌더로 만든다
      --> markRootFinished 가 remainingLanes 와 AND 해서 정리한다
```

## 다루지 않는 것

`syncLaneExpirationMs` / `transitionLaneExpirationMs` / `retryLaneExpirationMs` 의 빌드별 값, `markRootSuspended`(L851)가 만료 시각을 지우는 규칙, `markRootFinished`(L894)의 정리, `Scheduler.js` 쪽의 대응 상수, `getLanesToRetrySynchronouslyOnError`(L596)와 에러 복구용 동기 재시도는 같은 뼈대의 곁가지라 요약만 했다.
