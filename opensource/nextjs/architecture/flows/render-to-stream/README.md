# 동적 응답을 스트림으로 내보내기

상위: [Next.js 아키텍처 지도](../../README.md)

[App Router 가 페이지를 만드는 길](../app-render/README.md)의 갈림길에서 아래쪽(동적) 갈래가 마지막에 부르는 것이 `renderToStream` 이다. **React 를 두 번 돌린다** — RSC 한 번, HTML 한 번.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `APPR` = `server/app-render/app-render.tsx`(10598줄).

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3258-L4369 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3258-L4369))

## 실제 코드

시그니처가 이 함수의 입력 전부다. 인자 열 중 `createRequestStore` 와 `fallbackParams` 는 **갈래 1(개발 전용)에서만** 쓰인다 — [02]에 적었다.

```tsx
// app-render.tsx L3258-L3269
async function renderToStream(
  requestStore: RequestStore,
  req: BaseNextRequest,
  res: BaseNextResponse,
  ctx: AppRenderContext,
  tree: LoaderTree,
  formState: any,
  postponedState: PostponedState | null,
  metadata: AppPageRenderResultMetadata,
  createRequestStore: (() => RequestStore) | undefined,
  fallbackParams: OpaqueFallbackRouteParams | null
): Promise<AnyStream> {
```

## 동작 흐름

```text
 renderToStream  APPR L3258-4369 (1112줄)

 L3270-3397  준비 — 스크립트·폴리필·스팬                          [01]
 L3399       return getTracer().withSpan(renderSpan, async () => {
 L3400-3449    에러 핸들러 둘과 상태 변수                          [01]
 L3451         try {
 L3452-3798      ★ RSC 페이로드를 만든다 (세 갈래)                 [02]
 L3803           await waitAtLeastOneReactRenderTask()
 L3805-4085      ★ HTML 을 만든다                                 [03]
 L4087-4366    } catch (err) {
                 ★ 에러 화면을 **다시 렌더한다** (280줄)           [04]
              }
             })
```

```text
 ★★★ 머리기사 — catch 가 본문의 4할이다

 준비   L3258-3450  193줄   ★ **try 밖이다**
 try    L3451-4086  636줄
 catch  L4087-4366  280줄
                    ---- 합 1109 + 닫는 줄들 = 1112

 => 에러가 나면 로그만 찍고 끝내지 않고 **에러 화면을 다시 렌더한다**.
    그래서 catch 가 이렇게 크다
 ★ 앞 193줄은 try 가 감싸지 않는다. 그 안에 await 가 하나 있고(L3365),
   renderSpan 은 L3372 에서 열린다 — L3372-3450 에서 던지면 스팬이 안 닫힌다
   (endSpanWithError 는 L3384 에 정의만 되고 try 안에서만 쓰인다)
 ★ catch 안에도 try 가 둘 더 있다 (L4175 · L4208, Edge 판 L4273 · L4306)
```

```text
 ★★★ if/else **셋** 중 한쪽이 빌드에서 사라진다

 L3714  if (process.env.__NEXT_USE_NODE_STREAMS) { ... } else { ... }   RSC
 L3806  〃                                                            HTML
 L4170  〃                                                            에러 화면
 (각 MARK 주석은 그 바로 위 줄이다 — L3713 · L3805 · L4171)

 build/define-env.ts L192
   'process.env.__NEXT_USE_NODE_STREAMS': isEdgeServer ? false : true,
 ★ 이것은 사용자 앱·Edge SSR 번들용이다. 이 파일이 미리 번들되는 Node 서버 런타임에는
   next-runtime.webpack-config.js L264 가 JSON.stringify(true) 로 박는다

 => **빌드타임 상수다.** 번들러가 한쪽을 통째로 지운다.
    런타임 분기가 아니라 **Node 빌드 / Edge 빌드**의 차이다
 => 소스를 읽을 때는 갈래가 둘로 보이지만, 실제로 도는 코드에는 하나뿐이다

 같은 스위치가 파일 여럿을 가른다
   stream-ops.ts L27        node 판과 web 판 중 하나를 require 한다
   debug-channel-server.ts L21
   app-render-prerender-utils.ts L19
   make-get-server-inserted-html.tsx L91
```

1. [준비와 에러 핸들러](01_setup/README.md) — 스크립트·폴리필과 에러를 담는 그릇.
2. [RSC 페이로드](02_rsc/README.md) — 세 갈래로 갈리는 첫 번째 렌더.
3. [HTML](03_html/README.md) — 두 번째 렌더와 PPR 재개.
4. [에러 화면 다시 렌더하기](04_error-recovery/README.md) — catch 280줄.

```text
 ★★ 소스가 스스로 구역에 이름을 붙여 놓았다 (`// MARK:`)

   L3271  renderToStream setup
   L3400  renderToStream errorHandlers
   L3713  nodeStreams RSC          L3756  webStreams RSC
   L3805  nodeStreams HTML         L3949  webStreams HTML
   L4086  renderToStream errorRecovery
   L4116  errorRecovery classification
   L4171  nodeStreams errorRecovery RSC + HTML
   L4269  webStreams errorRecovery RSC + HTML

 => 열 개의 MARK 중 여섯이 node/web 짝이다. 위에서 말한 그 스위치다
 ★ MARK 는 주석 줄이고 실제 if/else 는 그 앞뒤다 (L3713 주석 -> L3714 if 등)
```

```text
 ★ RSC 를 먼저 돌리고 한 틱 쉰다 (L3800-3803)

 주석 L3800-3802
   "React doesn't start rendering synchronously but we want the RSC render to
    have a chance to start before we begin SSR rendering because we want to
    capture any available preload headers so we tick one task before continuing"

 => React 는 동기로 렌더를 시작하지 않는다.
    RSC 렌더가 **시작될 기회**를 주려고 태스크 하나를 흘려보낸다.
    그 사이에 preload 헤더가 잡히기 때문이다
```

## 결과가 쓰이는 곳

```text
 반환한 AnyStream
      --> [App Router]의 L3086 이 new RenderResult(stream, options) 로 감싼다
      --> 그 뒤 라우트 모듈이 응답 캐시를 거쳐 소켓에 쓴다

 res 에 직접 붙인 헤더
      --> L3447-3448 이 setHeader / appendHeader 를 bind 해 두고
          렌더 도중 preload 헤더 등을 붙인다

 allCapturedErrors
      --> [03]의 makeGetServerInsertedHTML 만 쓴다 (L3846 · L3884 · L3989 · L4027)
      ★ [04]는 **읽지 않는다.** 에러 화면은 serverCapturedErrors: [] 를 넘긴다(L4249)

 reactServerErrorsByDigest
      --> [04]가 L4181 · L4279 에서 읽는다.
          이미 보고된 에러면 payload 에 **err 대신 null** 을 넘긴다
```

## 다루지 않는 것

`prerenderToStream`(L8229-10224, 1996줄)의 정적 갈래, `stream-ops.node.ts`(1104줄) / `stream-ops.web.ts`(314줄)의 `continueFizzStream` · `resumeToFizzStream` · `continueDynamicHTMLResumeNode` 구현, `App`(L2368) / `ErrorApp`(L2433) 컴포넌트의 본문과 `getRSCPayload`(L2047) / `getErrorRSCPayload`(L2234), `createReactServerErrorHandler` / `createHTMLErrorHandler` 의 분류 규칙, `makeGetServerInsertedHTML` 과 `ServerInsertedHTMLProvider`, `getRequiredScripts` 가 고르는 부트스트랩 스크립트, `use-flight-response.tsx` 의 인라인 데이터 스트림, PPR 의 `postponedState` 형식과 `DynamicState` / `DynamicHTMLPreludeState` 열거, React 의 Fizz·Flight 런타임 자체는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 준비와 에러 핸들러](01_setup/README.md)
- [02 RSC 페이로드](02_rsc/README.md)
- [03 HTML](03_html/README.md)
- [04 에러 화면 다시 렌더하기](04_error-recovery/README.md)
