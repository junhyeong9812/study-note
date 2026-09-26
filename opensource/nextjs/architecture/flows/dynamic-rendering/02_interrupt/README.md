# 02 흐름을 끊는 두 오류

상위: [무엇이 동적인지 가려내기](../README.md)

렌더를 중간에서 끊는 수단 중 **식별이 필요한 것**이 둘이다. React 의 `postpone` 과 Next.js 자신의 중단 오류. (셋째로 `BailoutToCSRError` 가 있는데 그쪽은 클래스로 알아보므로 이 구획의 문제가 아니다 — import L56, 쓰이는 곳 L562 · L743.) 둘 다 나중에 "이게 그거였나" 를 알아봐야 하는데, **알아보는 방법이 서로 다르다** — 하나는 문자열을 뒤지고 하나는 필드를 본다.

## 위치

`packages/next` / `src/server/app-render` / `dynamic-rendering.ts` L396-L554 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/dynamic-rendering.ts#L396-L554))

## 실제 코드

문자열로 알아보는 쪽은 그 계약을 **모듈이 로드될 때 스스로 검사한다**.

```ts
// dynamic-rendering.ts L462-L466
if (isDynamicPostponeReason(createPostponeReason('%%%', '^^^')) === false) {
  throw new Error(
    'Invariant: isDynamicPostpone misidentified a postpone reason. This is a bug in Next.js'
  )
}
```

```text
 ★★★ 모듈 최상위에 **자기 검사**가 있다

   L462  isDynamicPostponeReason(createPostponeReason('%%%', '^^^')) 이 false 면
     => throw new Error('Invariant: isDynamicPostpone misidentified a
          postpone reason. This is a bug in Next.js')

 => 만드는 쪽(createPostponeReason)과 알아보는 쪽(isDynamicPostponeReason)이
    **문자열로만 이어져 있다.** 한쪽 문구를 고치면 조용히 끊긴다
 => 그래서 더미 값('%%%' · '^^^')으로 한 번 왕복시켜 보고,
    안 맞으면 **import 시점에 프로세스를 세운다**
 ★ 테스트가 아니라 런타임 코드다. 프로덕션 번들에도 들어간다.
   모듈 최상위의 이런 검사는 이 파일에 **하나**뿐이다
 ★★ 문자열 결합으로 만든 계약을 지키는 방법이 이것뿐이었던 것으로 보인다
 ※ 뒷문장은 내 해석이다
```

## 동작 흐름

```text
 ── postpone 쪽 ──

 Postpone({ reason, route })            L403  React 컴포넌트다. 반환형이 never
   L404  prerenderStore = workUnitAsyncStorage.getStore()
   L406  type === 'prerender-ppr' 일 때만 dynamicTracking 을 꺼낸다. 아니면 null
   L409  => postponeWithTracking(route, reason, dynamicTracking)

 postponeWithTracking(route, expression, dynamicTracking)   L412  => never
   ★ 호출처가 이 파일 밖에도 있다 — `useDynamicRouteParams`(L675),
     `server/request/cookies.ts` L87 · `headers.ts` L113 등, `use-cache-wrapper.ts` L1862
   L417  assertPostpone()                     React.unstable_postpone 이 있는지 본다
   L419  dynamicTracking 이 있으면 dynamicAccesses 에 밀어 넣는다
   L429  React.unstable_postpone(createPostponeReason(route, expression))

 createPostponeReason(route, expression)   L432
   `Route ${route} needs to bail out of prerendering at this point because it
    used ${expression}. React throws this special object to indicate where.
    It should not be caught by your own try/catch.
    Learn more: https://nextjs.org/docs/messages/ppr-caught-error`

 isDynamicPostpone(err)          L440  객체이고 message 가 문자열이면 아래로
 isDynamicPostponeReason(reason) L451  **두 조각을 모두 포함**하는지 본다
   'needs to bail out of prerendering at this point because it used'
   'Learn more: https://nextjs.org/docs/messages/ppr-caught-error'
```

```text
 ── 중단 오류 쪽 ──

 NEXT_PRERENDER_INTERRUPTED = 'NEXT_PRERENDER_INTERRUPTED'   L468

 createPrerenderInterruptedError(message)   L470
   L471  error = new Error(message)
   L472  ;(error as any).digest = NEXT_PRERENDER_INTERRUPTED
   L473  return error

 isPrerenderInterruptedError(error)   L480  => error is DigestError
   객체 · null 아님 · **digest === NEXT_PRERENDER_INTERRUPTED** ·
   'name' in error · 'message' in error · error instanceof Error
```

```text
 ★★★ 알아보는 방법이 둘로 갈린 이유

   postpone            **문자열 두 조각**을 포함하는지 본다
   prerender-interrupt **digest 필드**가 상수와 같은지 본다

 => postpone 객체는 **React 가 만든다.** Next.js 가 넘기는 것은 이유 문자열뿐이고(L429)
    돌려받은 객체에 필드를 붙일 자리가 없다. 그래서 문자열에 표식을 심었다
 ※ "필드를 붙일 수 없어서" 는 내 추론이다. 소스는 이유를 적지 않는다 —
   기계적으로 확인되는 것은 Next.js 가 문자열만 넘긴다는 것까지다
 => 중단 오류는 Next.js 가 만드니 `digest` 를 붙이면 그만이다
 ★★ 그래서 자기 검사(위 실제 코드)가 postpone 쪽에만 있다.
   digest 쪽은 상수 하나를 공유하므로 어긋날 수가 없다
 ★ `digest` 는 Next.js 가 오류를 분류하는 공통 수단이다 —
   [응답 나가기]의 오류 처리도 같은 필드를 보고,
   `ClientHookDynamicError` 도 digest `'CLIENT_HOOK_DYNAMIC'` 로 알아본다
   (`dynamic-rendering-utils.ts` L37-63)
```

```text
 ★★ 이유 문자열이 사용자에게 두 가지를 말한다 (L432-437)

   "React throws this special object to indicate where.
    **It should not be caught by your own try/catch.**"

 => postpone 은 오류처럼 생겼지만 오류가 아니다.
    사용자 코드가 try/catch 로 삼키면 PPR 이 망가진다
 ★ 그래서 링크가 `ppr-caught-error` 다 — 삼켰을 때 보라는 문서다
 ★ 그리고 그 링크 문자열 자체가 위 `isDynamicPostponeReason` 의 판별 조각이다.
   문구를 사람이 읽으라고 넣은 것과 기계가 읽으라고 넣은 것이 같은 줄에 있다
```

```text
 ★ assertPostpone (L548)

   hasPostpone = typeof React.unstable_postpone === 'function'    L87  모듈 최상위

 => React 버전에 `unstable_postpone` 이 없으면 postpone 경로 자체가 불가능하다.
    파일 맨 위에서 한 번 보고 상수로 들고 있는다
 ★ import 주석 L32 - "Once postpone is in stable we should switch to importing
   the postpone export directly"
```

```text
 ★ 쌓인 것을 꺼내 쓰는 함수 셋 (L493-546)

 accessedDynamicData(dynamicAccesses)       L493  길이 > 0 인지
 consumeDynamicAccess(serverDynamic, ...)   L499
 formatDynamicAPIAccesses(...)              L510  사람이 읽을 문구로 만든다

 => 밀어 넣는 곳은 셋이다 — `abortOnSynchronousDynamicDataAccess`(L317) ·
    `postponeWithTracking`(L419) · `annotateDynamicAccess`(L638).
    쌓기와 꺼내기가 같은 파일 안에 있다
```

## 결과가 쓰이는 곳

```text
 React.unstable_postpone(reason)
      --> [정적 응답]의 PPR prerender 가 그 자리를 구멍으로 남긴다.
          셸은 그대로 완성된다

 digest 가 붙은 Error
      --> [01]의 `controller.abort(error)` 가 이 오류를 신호에 싣는다.
          받는 쪽이 `isPrerenderInterruptedError` 로 "내가 낸 중단" 임을 확인한다

 isDynamicPostpone / isPrerenderInterruptedError
      --> 오류 처리 경로가 **사용자 오류와 구분**하는 수단.
      --> 그리고 흘려보내지 않는다. app-render.tsx L9145-9165 가
          `isPrerenderInterruptedError(err) || signal.aborted` 이면
          `errorInfo.componentStack` 을 꺼내 **[03]의 사다리로 넘긴다**
          (내비게이션 경로는 L7266-7271 에서 trackDynamicHoleInNavigation 으로)
      ★ 즉 [01]이 만든 중단 오류 → [02]의 식별 → [03]의 사다리가 한 줄로 이어진다

 Postpone 컴포넌트
      --> 트리 안에 직접 놓아 그 자리를 구멍으로 만든다.
          함수 호출이 아니라 **JSX 로 쓰는 중단**이다
      ★ 놓는 곳은 저장소에 하나 — [트리 조립] [03] CCTREE L782 의 force-dynamic + PPR 갈래다.
        그 갈래는 v16.3.6 사용자 설정으로 닿을 수 없다 (그 문서 참조)
```

## 다루지 않는 것

`React.unstable_postpone` 의 구현과 React 가 postpone 을 받아 셸을 완성하는 과정, `Postpone` 컴포넌트를 트리에 놓는 쪽(저장소에서 한 곳 — [트리 조립] [03]의 CCTREE L782. v16.3.6 사용자 설정으로는 닿지 않는 갈래다), `digest` 필드를 읽는 오류 처리 경로 전체(`app-render` 의 `onError` 계열)와 다른 digest 상수들, `consumeDynamicAccess`(L499) · `formatDynamicAPIAccesses`(L510)의 본문과 그 문구가 실제로 찍히는 자리, `assertPostpone`(L548)의 오류 문구, `createRenderInBrowserAbortSignal`(L560) · `createHangingInputAbortSignal`(L571)의 신호 만들기는 이 문서의 범위 밖이다.
