# markSuspenseBoundaryShouldCapture

상위: [에러와 Suspense 흐름](../README.md)

서스펜스 경계에 **"되감기 때 네가 잡아라"** 를 표시한다. 그런데 concurrent 경로의 실코드는 두 줄이고, 그 앞에 주석이 마흔 줄이다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberThrow.js` L241-L362 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberThrow.js#L241-L362))

## 실제 코드

머리 주석이 목적을 밝힌다.

```js
// ReactFiberThrow.js L248-L249
  // This marks a Suspense boundary so that when we're unwinding the stack,
  // it captures the suspended "exception" and does a second (fallback) pass.
```

> This marks a Suspense boundary so that when we're unwinding the stack, it captures the suspended "exception" and does a second (fallback) pass.

concurrent 경로로 들어서는 자리.

```js
// ReactFiberThrow.js L316-L321
  // Confirmed that the boundary is in a concurrent mode tree. Continue
  // with the normal suspend path.
  //
  // After this we'll use a set of heuristics to determine whether this
  // render pass will run to completion or restart or "suspend" the commit.
  // The actual logic for this is spread out in different places.
```

> The actual logic for this is spread out in different places.

그리고 실제로 하는 일.

```js
// ReactFiberThrow.js L357-L361
  suspenseBoundary.flags |= ShouldCapture;
  // TODO: I think we can remove this, since we now use `DidCapture` in
  // the begin phase to prevent an early bailout.
  suspenseBoundary.lanes = rootRenderLanes;
  return suspenseBoundary;
```

> TODO: **I think** we can remove this, since we now use `DidCapture` in the begin phase to prevent an early bailout.

## 동작 흐름

```text
 TH L241  function markSuspenseBoundaryShouldCapture(
            suspenseBoundary, returnFiber, sourceFiber, root, rootRenderLanes)

 L250  [FLAG:!disableLegacyMode] 이고 경계가 concurrent 가 아니면
        (OSS 웹 빌드에서는 안 돈다. React Native 빌드에서는 돈다)

 L260    suspenseBoundary === returnFiber 이면
 L276      flags |= ShouldCapture
            주석 L261-275 - React.lazy 가 Suspense 의 직계 자식일 때다.
            서스펜스 경계는 여러 fiber 로 되어 있는데
            "서스펜드한 fiber" 가 안쪽 Offscreen 래퍼라
            레거시 방식(null 로 커밋한 척)이 통하지 않는다

 L277    아니면
 L278      suspenseBoundary.flags |= DidCapture      (ShouldCapture 를 건너뛴다)
 L279      sourceFiber.flags |= ForceUpdateForLegacySuspense
 L284      sourceFiber.flags &= ~(LifecycleEffectMask | Incomplete)
            주석 L281-283 - 완료되지 않았는데도 이 fiber 를 커밋할 것이다.
            다만 생명주기 메서드나 콜백은 부르면 안 되니 효과 태그를 지운다
 L286-308  tag 에 따라 IncompleteClassComponent / IncompleteFunctionComponent 로 바꾸거나
            ForceUpdate 를 큐에 넣는다
 L312      sourceFiber.lanes 에 SyncLane 을 합친다
            주석 L310-311 - 이 fiber 는 완료되지 않았다.
            아직 할 일이 남았음을 Sync 우선순위로 표시한다
 L314    => return suspenseBoundary

 --- concurrent 경로 ---
 L316-356  주석 41줄 (L331 은 빈 줄이라 주석은 40줄)

 L357  suspenseBoundary.flags |= ShouldCapture
 L360  suspenseBoundary.lanes = rootRenderLanes
 L361  => return suspenseBoundary
```

```text
 ★ 주석 마흔 줄에 코드 두 줄이다

 L316-356 이 Suspense 휴리스틱을 길게 설명한다
   언제 재시작하고 언제 fallback 을 보여 줄지,
   500ms 스로틀이 왜 있는지, 배치가 모호할 때 무엇을 우선하는지

 그런데 그 주석이 스스로 적는다 (L321)
   "The actual logic for this is spread out in different places."

 그리고 이 함수가 실제로 하는 일은
   L357  flags |= ShouldCapture
   L360  lanes = rootRenderLanes
 두 줄뿐이다

 => 설명은 여기 모여 있는데 구현은 흩어져 있다
    (주석의 "this" 는 이 함수가 아니라 휴리스틱을 가리킨다)
```

```text
 TODO 가 가리키는 줄

 L357  suspenseBoundary.flags |= ShouldCapture;
 L358  // TODO: I think we can remove this, since we now use `DidCapture` in
 L359  // the begin phase to prevent an early bailout.
 L360  suspenseBoundary.lanes = rootRenderLanes;

 주석은 **뒤따르는 문장**인 L360 을 가리킨다.
 "조기 바이아웃을 막는다" 는 lanes 를 세우는 이유이고,
 begin phase 가 DidCapture 로 그것을 대신한다는 말이다

 ShouldCapture(L357)는 되감기에 필요하므로 지울 대상이 아니다
```

```text
 레거시 갈래가 두 플래그의 출처다

 L278  suspenseBoundary.flags |= DidCapture
       => ShouldCapture 를 거치지 않고 곧장 DidCapture 를 세우는 유일한 자리다

 L279  sourceFiber.flags |= ForceUpdateForLegacySuspense
       => 저장소 전체에서 이 플래그를 세우는 유일한 자리다
          [beginWork] 흐름에서 그 플래그의 갈래가 죽었다고 본 이유가 이것이다

 L284  sourceFiber.flags &= ~(LifecycleEffectMask | Incomplete)
       => Incomplete 를 지우는 두 자리 중 하나다
          이 갈래를 타면 되감기가 아니라 completeWork 로 간다

 셋 다 disableLegacyMode 아래에 있다.
 OSS 웹 빌드에서는 안 돌고, React Native 빌드에서는 돈다
```

```text
 부르는 곳이 둘이다

 TH L439  서스펜션의 본줄기 (Activity / Suspense / SuspenseList)
 TH L575  수화 중 에러 경로

 그리고 부르지 **않는** 자리가 하나 있다
 TH L489  서스펜션인데 핸들러가 OffscreenComponent 일 때는
          이 함수를 거치지 않고 flags |= ShouldCapture 를 직접 세운다
          => lanes 도 안 세우고 ForceClientRender 도 안 지운다
```

## 결과가 쓰이는 곳

```text
 ShouldCapture
      --> [03] unwindWork 가 DidCapture 로 바꾼다
      --> 그 경계가 되감기의 종착지가 된다

 lanes = rootRenderLanes
      --> 경계가 조기 바이아웃하지 않게 한다
      --> TODO 는 이 줄을 지울 수 있다고 본다

 반환한 suspenseBoundary
      --> 부른 쪽이 그대로 쓰거나 무시한다
```

## 다루지 않는 것

L316-356 주석이 설명하는 Suspense 휴리스틱의 실제 구현(여러 파일에 흩어져 있다), 레거시 갈래의 `IncompleteClassComponent` / `IncompleteFunctionComponent` tag 교체(L286-308), `enqueueUpdate` 로 ForceUpdate 를 넣는 부분, `LifecycleEffectMask` 의 구성, 500ms 스로틀의 실제 구현은 같은 뼈대의 곁가지라 요약만 했다.
