# 03 내보내기

상위: [응답이 만들어져 나가기까지](../README.md)

`pipe` / `pipeImpl` 이다. 렌더를 부르고, 나온 것이 있으면 헤더를 붙여 소켓으로 보낸다. **나온 것이 없으면 그냥 돌아선다.**

## 위치

`packages/next` / `src/server` / `base-server.ts` L1832-L1911 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1832-L1911))

## 실제 코드

이 흐름 전체의 분기가 네 줄이다.

```ts
// base-server.ts L1870-L1873
    const payload = await fn(ctx)
    if (payload === null) {
      return
    }
```

## 동작 흐름

```text
 pipe  BASE L1832-1844  — 추적 껍데기
   L1841  => return getTracer().trace(BaseServerSpan.pipe, async () =>
   L1842       this.pipeImpl(fn, partialContext))

 pipeImpl  BASE L1846-1911

 --- 렌더 문맥을 만든다 ---
 L1855  ua = partialContext.req.headers['user-agent'] || ''
 L1857  ctx = {
          ...partialContext,
          renderOpts: {
            ...this.renderOpts,
 L1862       supportsDynamicResponse: !this.renderOpts.botType,
 L1863       serveStreamingMetadata: shouldServeStreamingMetadata(ua, htmlLimitedBots),
          },
        }
        주석 L1861 - botType 은 renderImpl 에서 누적된다
          ([요청 흐름]의 L2005 `this.renderOpts.botType = getBotType(ua)`)

 --- 부른다 ---
 L1870  payload = await fn(ctx)
 L1871  payload === null 이면
 L1872    => return                      ★★★ 여기서 끝난다. 대부분이 이 길이다

 --- payload 가 있을 때만 ---
 L1874  {req, res} = ctx
 L1875  originalStatus = res.statusCode
 L1876  {body} = payload
 L1877  {cacheControl} = payload  (let)
 L1878  res.sent 가 **아니면**
 L1879    {generateEtags, poweredByHeader} = this.renderOpts
 L1889    dev 이면
 L1890      Cache-Control 을 직접 박는다
 L1892        HMR 새로고침 헤더가 '1' 이면 'no-store'
 L1894        아니면 'no-cache, must-revalidate'
 L1896      cacheControl = undefined     ★ payload 가 준 것을 **버린다**
 L1899    cacheControl 이 있고 expire 가 없으면
 L1900      cacheControl.expire = this.nextConfig.expireTime
 L1903    await this.sendRenderResult(req, res, {
             result: body, generateEtags, poweredByHeader, cacheControl,
           })
 L1909    res.statusCode = originalStatus     ★ 상태 코드를 **되돌린다**
```

```text
 ★★★ `payload === null` 이 이 흐름의 기본값이다

 [README]에서 본 대로 base-server 가 payload 를 만드는 자리는 넷뿐이고
 넷 다 정적이거나 에러다.
 => 평범한 페이지 요청은 L1872 에서 끝난다.
    응답은 [02]가 넘긴 라우트 모듈의 handler 가 이미 다 썼다

 ★ 그런데 L1878 이 `if (!res.sent)` 로 한 번 더 막는다.
   payload 가 있더라도 누군가 이미 응답을 보냈으면 건드리지 않는다
   => 방어가 두 겹이다
```

```text
 ★★ 봇이면 동적 응답이 꺼진다 (L1862)

   supportsDynamicResponse: !this.renderOpts.botType

 botType 은 [요청 흐름]의 renderImpl L2005 에서 user-agent 로 정해졌다.
 그 값이 여기서 뒤집혀 렌더 옵션이 된다
 ★★ 다만 `this.renderOpts.botType` 은 **인스턴스 상태**다.
   renderImpl 을 거치지 않는 경로(render404 -> renderError -> renderErrorImpl -> pipe)에서는
   설정되지 않았거나 **직전 요청의 값이 남아 있다**
 => 봇에게는 스트리밍 대신 **완성된 HTML** 을 준다
 ★ [01]의 L2422 가 이 값을 한 번 더 좁힌다
      opts.supportsDynamicResponse = !isSSG && !isBotRequest && isSupportedDocument
   => 같은 플래그를 **두 군데서** 낮춘다. 여기서 켜고 [01]에서 다시 거른다
```

개발 모드의 캐시 헤더에 긴 주석이 붙어 있다.

```ts
// base-server.ts L1881-L1897
      // Dev responses use `no-cache` so the browser can restore them from the
      // HTTP cache on back/forward instead of reloading. HMR refresh responses
      // opt out into `no-store` because a superseded refresh's fetch is aborted
      // mid-write: under `no-cache` the response is stored, so the abort leaves
      // the cache entry shared with the superseding refresh (same URL)
      // half-written; Chromium then discards it and reissues the superseding
      // refresh on a second connection as a duplicate request. `no-store` keeps
      // that entry from being created.
      if (this.dev) {
        res.setHeader(
          'Cache-Control',
          req.headers[NEXT_HMR_REFRESH_HEADER] === '1'
            ? 'no-store'
            : 'no-cache, must-revalidate'
        )
        cacheControl = undefined
      }
```

```text
 => dev 는 'no-cache' 다. 'no-store' 가 아니다.
    브라우저가 뒤로/앞으로 갈 때 HTTP 캐시에서 복원하게 하려는 것이다

 => 그런데 HMR 새로고침만 'no-store' 다. 이유가 주석에 있다
    앞선 새로고침의 fetch 가 쓰는 도중에 중단되면
    'no-cache' 아래서는 그 응답이 **저장되어** 같은 URL 의 뒤따르는
    새로고침과 캐시 항목을 공유한 채 반쯤 쓰인 상태로 남는다.
    Chromium 이 그것을 버리고 뒤따르는 새로고침을 **두 번째 연결로 다시 보낸다**.
    'no-store' 는 그 항목이 만들어지지 않게 한다

 ★ dev 에서는 payload 가 준 cacheControl 을 **버린다** (L1896)
```

```text
 ★★★ 그런데 `payload.cacheControl` 은 **이 파일에서 한 번도 채워지지 않는다**

 `cacheControl` 전수 (base-server.ts)
   L317   타입 정의의 선택 필드        L395  sendRenderResult 의 인자 타입
   L1877  payload 에서 꺼내는 자리     L1896 dev 에서 undefined 로 덮는 자리
   L1899  expire 를 채우는 조건        L1900 expire 대입      L1907 넘기는 자리

 payload 를 만드는 네 자리(L2401 · L2952 · L3061 · L3155) **어디에도 cacheControl 키가 없다**
 => L1877 의 cacheControl 은 언제나 undefined 다
 => L1896 은 no-op 이고, L1899-1901 은 **도달할 수 없다**
 => sendRenderResult 는 이 경로에서 언제나 `cacheControl: undefined` 로 불린다.
    `nextConfig.expireTime` 이 여기서는 적용되지 않는다

 ★ [01]이 L2233 에서 찾은 죽은 조건과 **같은 유형**이다.
   선언과 소비는 있는데 생산이 없다
 ※ 예전에는 payload 가 cacheControl 을 실어 왔을 것이다. 그 이력은 확인하지 않았다
```

```text
 ★★ pipeImpl 의 호출자는 **둘**이다

 L2025  renderImpl   => this.pipe((ctx) => this.renderToResponse(ctx), {...})
 L2918  renderErrorImpl => this.pipe(async (ctx) => {...}, {...})

 뒤쪽은 단순 위임이 아니다 (L2919-2925)
   response = await this.renderErrorToResponse(ctx, err)
   if (this.minimalMode && res.statusCode === 500) {
     throw err
   }
   return response

 => **minimalMode 에서 500 이면 payload 대신 예외가 나간다.**
    [04]가 말한 "에러 페이지도 정상 렌더와 같은 길" 에 예외가 하나 있다
 ★ renderErrorImpl 은 그 전에 Cache-Control 을 직접 박는다 (L2911-2916,
   setHeaders 가 참일 때) — 'private, no-cache, no-store, max-age=0, must-revalidate'
```

```text
 ★ 상태 코드를 되돌리는 줄 (L1909)

   const originalStatus = res.statusCode      L1875
   await this.sendRenderResult(...)           L1903
   res.statusCode = originalStatus            L1909

 => sendRenderResult 가 상태 코드를 바꿀 수 있다는 뜻이다.
    바꾼 것을 되돌려 놓는다
 ※ 무엇이 왜 바꾸는지는 sendRenderResult(L388, abstract) 안쪽이라
   이 문서에서 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 sendRenderResult 로 넘긴 것
      --> 하위 클래스가 채우는 abstract(BASE L388)다.
          여기서 실제로 소켓에 쓴다. 이 흐름의 끝이다

 ctx.renderOpts
      --> [01]이 이어받아 supportsDynamicResponse 를 더 좁히고
          [02]가 라우트 모듈에 넘긴다

 (반환 없음)
      --> pipeImpl 은 Promise<void> 다. 위로 돌려줄 값이 없다.
          [요청 흐름]의 renderImpl L2025 가 이것을 그대로 return 한다
```

## 다루지 않는 것

`sendRenderResult`(L388, abstract)의 구현과 etag 생성 · `x-powered-by` 헤더, `RenderResult` 의 스트리밍 구조와 `fromStatic` / `EMPTY`, `CacheControl` 타입과 `expireTime` 설정, `shouldServeStreamingMetadata` 와 `htmlLimitedBots` 목록, `getBotType` / `isBot` 의 user-agent 판별, `getStaticHTML`(L1913)이 같은 `fn` 을 다르게 쓰는 방식, `BaseServerSpan.pipe` 스팬의 속성은 이 문서의 범위 밖이다.
