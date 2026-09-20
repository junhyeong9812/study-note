# 비트 배치

상위: [lane 흐름](../README.md)

lane 은 **31비트를 연속으로** 쓴다. 자리 순서가 곧 우선순위라서, 이 배치 하나가 뒤의 모든 비교를 한 줄로 만든다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberLane.js` L41-L123 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberLane.js#L41-L123))

## 실제 코드

가장 급한 쪽.

```js
// ReactFiberLane.js L43-L59
export const NoLanes: Lanes = /*                        */ 0b0000000000000000000000000000000;
export const NoLane: Lane = /*                          */ 0b0000000000000000000000000000000;

export const SyncHydrationLane: Lane = /*               */ 0b0000000000000000000000000000001;
export const SyncLane: Lane = /*                        */ 0b0000000000000000000000000000010;
export const SyncLaneIndex: number = 1;

export const InputContinuousHydrationLane: Lane = /*    */ 0b0000000000000000000000000000100;
export const InputContinuousLane: Lane = /*             */ 0b0000000000000000000000000001000;

export const DefaultHydrationLane: Lane = /*            */ 0b0000000000000000000000000010000;
export const DefaultLane: Lane = /*                     */ 0b0000000000000000000000000100000;

export const SyncUpdateLanes: Lane =
  SyncLane | InputContinuousLane | DefaultLane;

export const GestureLane: Lane = /*                     */ 0b0000000000000000000000001000000;
```

그리고 가장 안 급한 쪽.

```js
// ReactFiberLane.js L102-L115
export const SelectiveHydrationLane: Lane = /*          */ 0b0000100000000000000000000000000;

const NonIdleLanes: Lanes = /*                          */ 0b0000111111111111111111111111111;

export const IdleHydrationLane: Lane = /*               */ 0b0001000000000000000000000000000;
export const IdleLane: Lane = /*                        */ 0b0010000000000000000000000000000;

export const OffscreenLane: Lane = /*                   */ 0b0100000000000000000000000000000;
export const DeferredLane: Lane = /*                    */ 0b1000000000000000000000000000000;

// Any lane that might schedule an update. This is used to detect infinite
// update loops, so it doesn't include hydration lanes or retries.
export const UpdateLanes: Lanes =
  SyncLane | InputContinuousLane | DefaultLane | TransitionUpdateLanes;
```

> Any lane that **might** schedule an update. This is used to detect infinite update loops, so it doesn't include hydration lanes or retries.

## 자리표

| bit | lane | 선언 |
|---|---|---|
| 0 | `SyncHydrationLane` | L46 |
| 1 | `SyncLane` | L47 |
| 2 | `InputContinuousHydrationLane` | L50 |
| 3 | `InputContinuousLane` | L51 |
| 4 | `DefaultHydrationLane` | L53 |
| 5 | `DefaultLane` | L54 |
| 6 | `GestureLane` | L59 |
| 7 | `TransitionHydrationLane` | L61 |
| 8-21 | `TransitionLane1` ~ `TransitionLane14` | L63-76 |
| 22-25 | `RetryLane1` ~ `RetryLane4` | L95-98 |
| 26 | `SelectiveHydrationLane` | L102 |
| 27 | `IdleHydrationLane` | L106 |
| 28 | `IdleLane` | L107 |
| 29 | `OffscreenLane` | L109 |
| 30 | `DeferredLane` | L110 |

```text
 31개이고 빈 자리가 없다

 L41  TotalLanes = 31

 리터럴이 전부 31자리이므로 인덱스는 0~30 이다.
 TransitionLane14(21) 다음이 곧장 RetryLane1(22)이고,
 가장 안 급한 DeferredLane 이 bit 30 이다

 최상위 비트(2^31)는 어느 lane 도 쓰지 않는다

 왜 31인지는 **소스에 적혀 있지 않다.**
 (파일의 유일한 관련 주석 L38-40 은 DevTools 와 값을 맞추라는 내용이다)

 다만 이 파일의 lane 순회가 대부분 while (lanes > 0) 꼴이라
 최상위 비트를 쓰면 값이 음수가 되어 루프가 곧장 끝난다 -
 정황은 맞는다. 이것은 내 추론이다
```

## 묶음 상수

```text
 L56   SyncUpdateLanes = SyncLane | InputContinuousLane | DefaultLane
       ★ 수화 lane 은 **안 들어간다**
       [02]의 getHighestPriorityLanes 가 이것을 먼저 본다

 L62   TransitionLanes        bit 8-21
       ★ TransitionHydrationLane(bit 7)은 **안 들어간다**
       [02]의 끼어들기 판정(L353)이 이 마스크를 쓴다

 L80   TransitionUpdateLanes   TransitionLane1~10
 L91   TransitionDeferredLanes TransitionLane11~14
 L94   RetryLanes              bit 22-25
 L104  NonIdleLanes            bit 0-26
       ★ SelectiveHydrationLane(26)을 **포함한다**
 L114  UpdateLanes = SyncLane | InputContinuousLane | DefaultLane
                     | TransitionUpdateLanes
 L117  HydrationLanes          수화 lane 여섯
```

```text
 수화 lane 은 다섯이 아니라 여섯이다

 등급마다 짝으로 붙은 것이 다섯
   Sync / InputContinuous / Default / Transition / Idle

 거기에 짝이 없는 것이 하나 더 있다
   SelectiveHydrationLane (bit 26)

 반대로 Gesture 와 Retry 에는 전용 수화 lane 이 없다.
 retry 와 transition 은 TransitionHydrationLane 하나로 모인다

 (여섯이라는 것과 매핑은 검증 과정에서 확인된 것이고,
  나는 HydrationLanes 선언과 짝 다섯까지 직접 봤다)
```

```text
 ★ "idle 이하" 의 경계가 함수마다 한 칸 다르다

 NonIdleLanes(L104)는 SelectiveHydrationLane 을 **포함한다**
 => [02] getNextLanes 는 그것을 "idle 이 아닌 일" 로 본다

 그런데 computeExpirationTime L524 는 그것을
 "idle priority or lower" 그룹에 넣는다
 => [03]에서는 만료하지 않는 쪽이다

 같은 lane 이 한쪽에서는 비idle, 다른 쪽에서는 idle 로 분류된다
```

```text
 트랜지션 14개가 둘로 갈린다

 L80  TransitionUpdateLanes    1~10   실제 트랜지션 갱신용
 L91  TransitionDeferredLanes  11~14  useDeferredValue 가 낳는 것용

 [02]의 getHighestPriorityLanes 가 그 둘을 다른 case 로 처리한다
   L215  lanes & TransitionUpdateLanes
   L220  lanes & TransitionDeferredLanes

 14개를 돌려 쓰는 커서가 따로 있다 (L176-177)
```

```text
 UpdateLanes 의 주석이 구성보다 적게 말한다

 주석 L112-113 은 "수화 lane 과 retry 는 안 넣는다" 고만 적는데
 실제로는 Gesture, TransitionLane11~14, Idle, Offscreen, Deferred 도 빠져 있다

 (주석 자체가 불완전한 자리다)
```

## 결과가 쓰이는 곳

```text
 비트 순서
      --> getHighestPriorityLane 이 lanes & -lanes 로 최하위를 뽑는다
      --> 끼어들기 판정이 비트 크기를 그대로 비교한다

 묶음 상수
      --> includes* 술어들이 이것으로 성질을 묻는다
      --> 다른 흐름들이 그 술어를 부른다

 lane 인덱스 (31 - clz32)
      --> root.expirationTimes / entanglements 가 인덱스 배열이다
```

## 다루지 않는 것

`getLabelForLane`(L127)의 DevTools 이름표, `SomeTransitionLane`(L78) / `SomeRetryLane`(L100)의 쓰임, `claimNext*Lane`(L726/738/747)이 커서를 돌리는 방식, `getBumpedLaneForHydration`(L1092)의 수화 lane 승급 매핑, `createLaneMap`(L815)과 인덱스 배열, `NoTimestamp`(L174)는 같은 뼈대의 곁가지라 요약만 했다. 묶음별 술어는 [spi](../spi/README.md)에 있다.
