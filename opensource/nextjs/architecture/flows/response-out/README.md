# 응답이 만들어져 나가기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[요청이 들어와서 렌더로 가기까지](../request-to-render/README.md)의 끝에서 이어진다. 라우트와 컴포넌트가 정해진 뒤, 응답이 실제로 만들어져 소켓으로 나가기까지를 따라간다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `BASE` = `server/base-server.ts`(3195줄).

## 위치

`packages/next` / `src/server` / `base-server.ts` L315-L318 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L315-L318))

## 실제 코드

이 흐름이 다루는 것은 이 타입 하나가 만들어지느냐다.

```ts
// base-server.ts L315-L318
type ResponsePayload = {
  body: RenderResult
  cacheControl?: CacheControl
}
```

## 동작 흐름

```text
 ★★★ 머리기사 — base-server 는 응답을 **거의 만들지 않는다**

 파일 3195줄 전체에서 ResponsePayload 를 실제로 만드는 자리는 **넷뿐**이다
   L2402  RenderResult.fromStatic(components.Component, ...)  완전 정적 페이지
   L2953  RenderResult.EMPTY                                  dev 의 /favicon.ico
   L3063  RenderResult.fromStatic(폴링 스크립트 HTML)           dev, 에러 컴포넌트 분실
   L3156  RenderResult.fromStatic('Internal Server Error')     마지막 바닥

 => **넷 다 정적이거나 에러다.** 평범한 페이지 렌더는 payload 를 하나도 안 만든다
```

```text
 그럼 평범한 페이지는 어떻게 응답이 되는가

 BASE renderToResponseWithComponentsImpl L2110-2609 (500줄)
   L2122-2353  플래그 스물셋을 세운다                      [01]
               (최상위 const/let 선언 기준. 중첩된 것은 빼고 센 수다)
   L2540-2571  요청 메타를 **원본 노드 req/res 로 옮긴다**   [02]
   L2603       await components.ComponentMod.handler(handlerReq, handlerRes, {...})
   L2607       // response is handled fully in handler
   L2608       => return null

 => 응답은 **라우트 모듈의 handler 가 직접 쓴다.**
    base-server 는 플래그를 계산해 넘겨 주고 null 을 돌려준다

 ★★ 다만 이것은 **노드 런타임 한정**이다.
    요청한 페이지가 Edge 함수면 NEXTSRV renderPageComponent L781 이 먼저 가로채
    runEdgeFunction 을 돌리고 L806 에서 null 을 돌린다.
    L2603 의 ComponentMod.handler 에는 **닿지 않는다**
```

```text
 ★★ 그 null 을 받는 자리 (pipeImpl L1870-1873)

   const payload = await fn(ctx)
   if (payload === null) {
     return
   }

 => 아무것도 안 하고 끝낸다. 응답은 이미 나갔기 때문이다             [03]
```

1. [무엇을 할지 정하기](01_decide/README.md) — 플래그 스물셋과 이른 출구 다섯, 그리고 죽은 조건 둘.
2. [라우트 모듈로 넘기기](02_delegate/README.md) — 쌓아 온 메타가 원본 객체로 건너가는 자리.
3. [내보내기](03_pipe/README.md) — `pipe` / `pipeImpl` 과 `sendRenderResult`.
4. [에러 페이지](04_error/README.md) — 폴백이 세 겹인 사슬.

```text
 ★★ 이 파일에 responseCache 가 **없다**

 `responseCache` · `doRender` · `ResponseCache` 를 파일 전체에서 grep 하면 0건이다
 => ISR·재검증·캐시 판정이 base-server 에 없다. 라우트 모듈이 가져갔다
 ※ 언제 옮겨졌는지는 확인하지 않았다 (내 관찰이다)

 남아 있는 캐시 흔적은 둘뿐이다
   L2450  getIncrementalCache(...) 로 인스턴스를 얻어
   L2456  incrementalCache.resetRequestCache()
          주석 L2455 - "TODO: investigate, this is not safe across
                        multiple concurrent requests"
```

```text
 ★★ 이 흐름에서 `null` 은 "응답이 이미 나갔다" 는 뜻이다

 [요청 흐름]의 감시값과 나란히 놓으면 이렇다
   handleRSCRequest 의 false        "아무것도 안 했다" (계약 위반)
   handleCatchall.. 의 true         "내가 끝냈다"
   renderPageComponent 의 false     "내 것이 아니다. 다음 매치로"   (BASE L2678)
   renderPageComponent 의 **null**  "Edge 로 이미 다 썼다"        (NEXTSRV L806)
   renderToResponse* 의 **null**    "내가 직접 다 썼다. 더 할 것 없다"

 => **같은 함수**가 false 와 null 을 다른 뜻으로 돌려준다.
    BASE L2772 의 `result !== false` 가 그 둘을 갈라 준다
```

## 결과가 쓰이는 곳

```text
 ResponsePayload (드물게 만들어질 때)
      --> [03]의 pipeImpl 이 받아 sendRenderResult 로 넘긴다

 null (대부분)
      --> [03]의 pipeImpl 이 그대로 돌아선다. 소켓에는 이미 응답이 있다

 원본 노드 req 에 옮겨 심은 요청 메타
      --> 라우트 모듈의 handler 가 읽는다. [요청 흐름]이 쌓은 상태가
          여기서 프레임워크 경계를 넘는다

 res.statusCode
      --> 이른 출구들이 307 · 404 · 405 를 직접 박는다. payload 없이 나가는 응답들이다
      ★ 400 만은 다르다 — L2536 은 상태 코드를 박지 않고
        `sendResponse(req, res, new Response(null, {status: 400}))` 으로 통째로 보낸다
```

## 다루지 않는 것

`components.ComponentMod.handler` 안쪽(라우트 모듈의 실제 렌더 — App Router 의 `app-render.tsx`, Pages Router 의 `render.tsx`), `route-modules/` 의 모듈 종류와 `isAppPageRouteModule` / `isAppRouteRouteModule` 판별, `IncrementalCache` 의 구현과 ISR·재검증 정책, `RenderResult` 의 스트리밍 구현, `sendRenderResult`(L388, abstract)를 하위 클래스가 채우는 방식, PPR(`isRoutePPREnabled` · postponed 상태)의 재개 절차, `getStaticPaths`(L2033)와 `generateStaticParams`, `setVaryHeader`(L2226)의 헤더 규칙, `findPageComponents`(L365, abstract)가 컴포넌트를 찾는 방식은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 무엇을 할지 정하기](01_decide/README.md)
- [02 라우트 모듈로 넘기기](02_delegate/README.md)
- [03 내보내기](03_pipe/README.md)
- [04 에러 페이지](04_error/README.md)
