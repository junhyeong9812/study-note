# 어긋남

상위: [하이드레이션](../README.md)

서버가 보낸 HTML 과 클라이언트가 그리려는 것이 안 맞을 때. **사용자에게 보이는 그 긴 에러 메시지가 여기서 만들어지고**, 던지는 것은 그 에러가 아니라 센티널이다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L388-L416 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L388-L416))

센티널 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L383-L386 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L383-L386))

## 실제 코드

에러를 만들어 **큐에 담고**, 던지는 것은 따로다.

```js
// ReactFiberHydrationContext.js L388-L416
function throwOnHydrationMismatch(fiber: Fiber, fromText: boolean = false) {
  let diff = '';
  if (__DEV__) {
    // Consume the diff root for this mismatch.
    // Any other errors will get their own diffs.
    const diffRoot = hydrationDiffRootDEV;
    if (diffRoot !== null) {
      hydrationDiffRootDEV = null;
      diff = describeDiff(diffRoot);
    }
  }
  const error = new Error(
    `Hydration failed because the server rendered ${fromText ? 'text' : 'HTML'} didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:
` +
      '\n' +
      "- A server/client branch `if (typeof window !== 'undefined')`.\n" +
      "- Variable input such as `Date.now()` or `Math.random()` which changes each time it's called.\n" +
      "- Date formatting in a user's locale which doesn't match the server.\n" +
      '- External changing data without sending a snapshot of it along with the HTML.\n' +
      '- Invalid HTML tag nesting.\n' +
      '\n' +
      'It can also happen if the client has a browser extension installed which messes with the HTML before React loaded.\n' +
      '\n' +
      'https://react.dev/link/hydration-mismatch' +
      diff,
  );
  queueHydrationError(createCapturedValueAtFiber(error, fiber));
  throw HydrationMismatchException;
}
```

던지는 것이 이것이다. 모듈 로드 때 한 번 만드는 싱글톤이다.

```js
// ReactFiberHydrationContext.js L383-L386
export const HydrationMismatchException: mixed = new Error(
  'Hydration Mismatch Exception: This is not a real error, and should not leak into ' +
    "userspace. If you're seeing this, it's likely a bug in React.",
);
```

> Hydration Mismatch Exception: This is not a real error, and should not leak into userspace. If you're seeing this, it's likely a bug in React.

## 동작 흐름

```text
 throwOnHydrationMismatch  HYD L388-416

 L388  (fiber, fromText: boolean = false)
        ★ 둘째 인자가 메시지를 가른다

 L390  [__DEV__]
 L393    diffRoot = hydrationDiffRootDEV
 L394    null 이 아니면
 L395      hydrationDiffRootDEV = null        ★ **소비한다**
 L396      diff = describeDiff(diffRoot)
          주석 L391-392 - "Consume the diff root for this mismatch.
                          Any other errors will get their own diffs."

 L399  error = new Error(...)
 L400    `Hydration failed because the server rendered
         ${fromText ? 'text' : 'HTML'} didn't match the client. ...`

 L414  queueHydrationError(createCapturedValueAtFiber(error, fiber))
 L415  throw HydrationMismatchException
```

```text
 ★★ 만든 에러와 던지는 값이 다르다

 L414  진짜 에러는 **큐에 담긴다**
 L415  던지는 것은 의미 없는 센티널이다

 그래서 렌더가 되감기는 동안 에러가 사라지지 않는다.
 나중에 upgradeHydrationErrorsToRecoverable(L907)이 모아 쓴다
 (마지막 줄은 내가 이름으로 짐작한 것이고 본문은 안 읽었다)
```

```text
 ★ 메시지가 둘로 갈린다

 L400  `server rendered ${fromText ? 'text' : 'HTML'} didn't match the client`

 호출처가 아홉인데 true 를 넘기는 것은 둘뿐이다
   L579  prepareToHydrateHostInstance 의 !didHydrate
   L650  prepareToHydrateHostTextInstance 의 !didHydrate
 나머지 일곱은 기본값 false - L482 / L502 / L513 / L525 / L554 / L796 / L813

 ★★ 그런데 짝이 뒤집혀 보인다
   **텍스트를 집다가** 실패하면 (L502) 기본값이라 "HTML" 이라고 나오고,
   **호스트 인스턴스를 수화하다가** 실패하면 (L579) "text" 라고 나온다

 뒤엣것은 의도한 것이다. DOM 의 hydrateProperties 는 **텍스트 내용이
 안 맞을 때만** false 를 돌려주기 때문이다
 (그 판정은 ReactDOMComponent 쪽이라 여기서는 안 읽었다)
```

```text
 ★★★ 어긋남을 던지는 자리가 단계 둘에 걸쳐 있다

 집기(begin)   HYD L482  tryToClaimNextHydratableInstance
                         -> 노드를 **맞춰만** 본다
 수화(complete) HYD L579  prepareToHydrateHostInstance
                         -> 속성과 텍스트를 **실제로 맞춘다**

 CW L1407  const wasHydrated = popHydrationState(workInProgress)
 CW L1408  wasHydrated 이면
 CW L1411    prepareToHydrateHostInstance(workInProgress, currentHostContext)
 TODO CW L1409-1410 - "Move this and createInstance step into the beginPhase
                       to consolidate."

 => 호스트 fiber 하나가 **두 번 어긋날 수 있다**. 문구도 다르다
 => 그래서 "집었다" 가 "수화했다" 가 아니다
```

```text
 사용자가 보는 문구  L400-411

 "Hydration failed because the server rendered HTML didn't match the client.
  As a result this tree will be regenerated on the client.
  This can happen if a SSR-ed Client Component used:

  - A server/client branch `if (typeof window !== 'undefined')`.
  - Variable input such as `Date.now()` or `Math.random()` which changes
    each time it's called.
  - Date formatting in a user's locale which doesn't match the server.
  - External changing data without sending a snapshot of it along with the HTML.
  - Invalid HTML tag nesting.

  It can also happen if the client has a browser extension installed which
  messes with the HTML before React loaded.

  https://react.dev/link/hydration-mismatch"

 그리고 L412 에서 DEV diff 가 뒤에 붙는다 ([04]가 그것을 만든다)
```

```text
 ★ 이상한 자리 하나

 L513 / L525  throw throwOnHydrationMismatch(fiber);

 그 함수는 언제나 L415 에서 던지므로 값을 돌려주지 않는다.
 앞에 붙은 throw 는 실행될 수 없다
 ※ Flow 의 제어 흐름 분석을 만족시키려는 것으로 보인다. 내 추측이다
```

```text
 ★★ 던진 뒤 — [에러와 Suspense]가 받는다

 THROW L562  hydrationBoundary !== null 이면      (경계를 **찾았다**)
 THROW L575    markSuspenseBoundaryShouldCapture(...)
 THROW L585    value !== HydrationMismatchException 이면
 THROW L586      wrapperError = new Error(
 THROW L587-588    'There was an error while hydrating but React was able to
                    recover by instead client rendering from the nearest
                    Suspense boundary.'
 THROW L589        {cause: value}          ★ 원래 예외를 안에 담는다
 THROW L591      queueHydrationError(...)
 THROW L595    => return false

 THROW L596  아니면                                 (경계를 **못 찾았다**)
 THROW L597    value !== HydrationMismatchException 이면
 THROW L600      문구만 다르다 - 'instead client rendering the entire root.'

 ★ 센티널이면 감싸지 **않는다**. 진짜 에러는 이미 L414 에서 담겼기 때문이다
 ★ 센티널이 아니면(수화 중 난 진짜 예외) 감싸서 담는다
   주석 THROW L583-584 - "Even though the user may not be affected by this
   error, we should still log it so it can be fixed."

 => 어긋나면 그 경계부터(없으면 루트 전체를) **클라이언트 렌더로 다시 그린다**
```

```text
 ★★★ 센티널이 다섯이다 — 이 지도가 "셋" 이라 적었던 것을 고친다

 SuspenseException            Thenable L51    use / 렌더 중
 SuspenseyCommitException     Thenable L61    completeWork 의 리소스 대기
 SuspenseActionException      Thenable L66    useActionState
 HydrationMismatchException   HYD L383        ★ 여기
 SelectiveHydrationException  BW L313         ★ 선택적 수화

 다섯 중 **둘이 하이드레이션 것**이다

 ★★ 그런데 다섯이 동급이 아니다. **넷만 work loop 가 알아본다**
   WL L2305  SuspenseException
   WL L2306  SuspenseActionException
   WL L2321  SuspenseyCommitException
   WL L2324  SelectiveHydrationException  -> SuspendedOnHydration (L2334)
   WL L2335  } else {
   WL L2336    // This is a regular error.   <- 이것이 여기로 떨어진다

 => HydrationMismatchException 은 work loop 에게 **그냥 보통 에러**다.
    알아보는 곳이 THROW L585 / L597 뿐이고, 거기서 하는 일도
    "두 번 감싸지 마라" 하나다
 => 나머지 넷은 "무엇 때문에 멈췄나" 를 분류하는 표식이고,
    이것은 "이미 기록했다" 는 표식이다. 쓰임이 다르다

 그리고 문구의 태도가 갈린다
   use 와 useActionState 쪽은 "새어 나갈 수 있으니 **반드시 되던지라**" 고 당부하고
   나머지 셋은 "새어 나가면 **React 버그**다" 라고 한다
 => 앞의 둘만 사용자 코드 안에서 던져지기 때문이다
    (마지막 줄은 내 추론이다)
```

```js
// ReactFiberThenable.js L49-L64
// An error that is thrown (e.g. by `use`) to trigger Suspense. If we
// detect this is caught by userspace, we'll log a warning in development.
export const SuspenseException: mixed = new Error(
  "Suspense Exception: This is not a real error! It's an implementation " +
    'detail of `use` to interrupt the current render. You must either ' +
    'rethrow it immediately, or move the `use` call outside of the ' +
    '`try/catch` block. Capturing without rethrowing will lead to ' +
    'unexpected behavior.\n\n' +
    'To handle async errors, wrap your component in an error boundary, or ' +
    "call the promise's `.catch` method and pass the result to `use`.",
);

export const SuspenseyCommitException: mixed = new Error(
  'Suspense Exception: This is not a real error, and should not leak into ' +
    "userspace. If you're seeing this, it's likely a bug in React.",
);
```

```text
 ★★★ 왜 예외를 제어 흐름으로 쓰는가 — 근거가 적혀 있다

 BW L1034-1041 (SelectiveHydrationException 을 던지기 직전)

   "Throw a special object that signals to the work loop that it should
    interrupt the current render.

    Because we're inside a React-only execution stack, we don't strictly
    need to throw here — we could instead modify some internal work loop
    state. But using an exception means we don't need to check for this
    case on every iteration of the work loop. So doing it this way moves
    the check out of the fast path."

 => work loop 의 **매 반복마다 검사하지 않으려고** 예외를 쓴다.
    이 설계 이유가 다섯 센티널 전부에 걸린다
    (마지막 문장은 내 판단이다. 주석은 이 자리만 말한다)
```

```text
 ★★ 서스펜드 뒤의 어긋남은 diff 가 비어 있다

 HYD L158  didSuspendOrErrorDEV = true   (markDidThrowWhileHydratingDEV)
 세우는 곳이 둘뿐이다 - THROW L392 / THROW L556

 그리고 warnNonHydratedInstance 가 그것을 보고 곧장 나간다
   HYD L232  didSuspendOrErrorDEV 이면
   HYD L236    return                  ★ **diff 노드를 아예 안 만든다**
   주석 L233-235 - "Inside a boundary that already suspended. We're currently
     rendering the siblings of a suspended node. The mismatch may be due to
     the missing data, so it's probably a false positive."

 => 던지기는 여전히 던지는데(L415), L394 의 diffRoot 가 null 이라
    **메시지 끝의 diff 가 빈 채로** 나간다
 ★ 같은 플래그가 L269 / L435 / L594 도 가른다
```

## 결과가 쓰이는 곳

```text
 queueHydrationError 로 담긴 에러
      --> upgradeHydrationErrorsToRecoverable 이 복구 가능 에러로 올린다
      --> onRecoverableError 로 사용자에게 간다

 throw HydrationMismatchException
      --> [렌더 루프]의 handleThrow 가 받는다
      --> [에러와 Suspense]가 경계를 찾아 되감는다

 hydrationDiffRootDEV
      --> 소비되어 메시지 끝에 붙는다. 한 번 쓰면 null 이 된다
```

## 다루지 않는 것

`queueHydrationError`(L925) / `upgradeHydrationErrorsToRecoverable`(L907) / `emitPendingHydrationWarnings`(L933)의 본문과 `onRecoverableError` 로 가는 길([커밋](../../commit/README.md)에 있다), `describeDiff`(`ReactFiberHydrationDiffs`)가 트리를 문자열로 바꾸는 방식, `markSuspenseBoundaryShouldCapture`(THROW L241)의 본문([에러와 Suspense](../../throw/README.md)에 있다), `SelectiveHydrationException` 을 던지는 두 자리(BW L1042 / L3058)의 전체 문맥과 선택적 수화가 우선순위를 올리는 규칙, `createCapturedValueAtFiber` 의 스택 수집은 이 문서의 범위 밖이다.
