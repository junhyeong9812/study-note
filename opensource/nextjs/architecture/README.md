# Next.js 아키텍처 지도

소스를 **직접 읽어서** 그린 탑다운 지도다. 지금까지 흐름 스물다섯 편, 120개 문서다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e) (2026-09-22). 모든 줄 번호는 이 태그 기준이다.

## 두 갈래로 읽는다

```text
 흐름  무엇이 일어나는가      25편, 120개 문서
       요청 하나가 지나는 길을 메서드 단위로 따라간다
       폴더 하나 = 메서드 하나

 구조  무엇이 있는가          **아직 없다**
       라우트 모듈 · 요청 메타 · 캐시 계층 · 매니페스트처럼 자리에 관한 것
```

API 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 아직 문서가 없는 것도 전부 적어 두었다 — 그 표가 곧 남은 일의 목록이다.

## 흐름 스물다섯 편

| 흐름 | 진입점 | 문서 |
|---|---|---|
| [요청이 들어와서 렌더로 가기까지](flows/request-to-render/README.md) | `NextNodeServer.getRequestHandler` L1269 | 6 |
| [응답이 만들어져 나가기까지](flows/response-out/README.md) | `renderToResponseWithComponentsImpl` L2110 | 5 |
| [App Router 가 페이지를 만드는 길](flows/app-render/README.md) | `renderToHTMLOrFlight` L3101 | 4 |
| [동적 응답을 스트림으로 내보내기](flows/render-to-stream/README.md) | `renderToStream` L3258 | 5 |
| [정적 응답을 미리 만들기](flows/prerender-to-stream/README.md) | `prerenderToStream` L8229 | 6 |
| [서버 액션이 실행되기까지](flows/server-action/README.md) | `handleAction` L567 | 4 |
| [재검증이 쌓이고 실행되기까지](flows/revalidation/README.md) | `revalidateTag` / `executeRevalidates` | 4 |
| [클라이언트가 화면을 바꾸기까지](flows/client-router/README.md) | `router-reducer` 의 액션 6종 | 4 |
| [프리페치가 쌓이고 내비게이션이 그것을 쓰기까지](flows/segment-cache/README.md) | `segment-cache/navigate` L68 | 4 |
| [세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지](flows/cache-entries/README.md) | `readOrCreateSegmentCacheEntry` L868 · `getFromCacheMap` (cache-map.ts) L229 | 5 |
| [프리페치 작업 하나가 태어나서 끝나기까지](flows/prefetch-tasks/README.md) | `schedulePrefetchTask` L317 | 5 |
| [가져온 적 없는 라우트 트리를 예측하기까지](flows/route-prediction/README.md) | `matchKnownRoute` L726 · `discoverKnownRoute` L220 | 5 |
| [`'use cache'` 가 값을 돌려주기까지](flows/use-cache/README.md) | `use-cache-wrapper.cache` L1715 | 5 |
| [무엇이 동적인지 가려내기](flows/dynamic-rendering/README.md) | `markCurrentScopeAsDynamic` L172 외 | 5 |
| [동적 API 가 값을 내주기까지](flows/request-apis/README.md) | `cookies()` · `headers()` · `connection()` 외 | 5 |
| [메타데이터가 `<head>` 가 되기까지](flows/metadata/README.md) | `createMetadataComponents` L36 | 5 |
| [클라이언트 트리가 라우터 상태를 읽기까지](flows/client-components/README.md) | `AppRouter` L579 | 5 |
| [트리를 조립하고 세그먼트로 자르기까지](flows/tree-assembly/README.md) | `createComponentTreeInternal` L84 · `collectSegmentData` L279 | 5 |
| [내비게이션 요청이 트리를 중간부터 그리기까지](flows/partial-tree/README.md) | `walkTreeWithFlightRouterState` L28 | 4 |
| [내비게이션이 서버 응답을 트리에 합치기까지](flows/ppr-navigation/README.md) | `startPPRNavigation` L222 · `spawnDynamicRequests` L1431 | 5 |
| [즉시 내비게이션을 개발 중에 검증하기까지](flows/instant-validation/README.md) | `anySegmentNeedsInstantValidation` L132 · `validateInstantConfigs` L7063 | 5 |
| [페이지가 아닌 요청이 처리되기까지](flows/non-page/README.md) | `resolveRoutes` 'middleware' L558 · `AppRouteRouteModule.handle` L757 | 4 |
| [Pages Router 가 페이지를 그리기까지](flows/pages-router/README.md) | `renderToHTMLImpl` L459 · `Router.change` L1207 | 5 |
| [`next build` 가 산출물을 만들기까지](flows/build/README.md) | `build` L1042 (3558줄) | 5 |
| [빌드가 번들러 설정과 배포 산출물을 만들기까지](flows/build-details/README.md) | `getBaseWebpackConfig` L327 · `collectBuildTraces` L94 · `handleBuildComplete` L557 · `copyTracedFiles` L1223 | 5 |

## 흐름이 이어지는 자리

```text
 요청 하나가 지나는 길

 [요청 -> 렌더]   base-server.ts 3195줄
      getRequestHandler -> handleRequest -> handleRequestImpl
      | run -> runImpl
      v
      NEXTSRV handleCatchallRenderRequest   라우트를 고른다
      | this.render(...)  ← **base 로 되돌아온다**
      v
 [응답 나가기]    같은 파일의 뒷 절반
      renderToResponseWithComponentsImpl  플래그 23개를 세운다
      | ComponentMod.handler(req, res, {waitUntil})
      |   ★ 이 사이에 층이 다섯 이상 있고 **응답 캐시가 렌더 여부를 정한다**
      v
 [App Router]     app-render.tsx 10598줄
      renderToHTMLOrFlight -> workAsyncStorage.run -> Impl
      | if (isStaticGeneration)
      +-------------------+
      v                   v
   [정적 응답]          [동적 응답 스트림]
   prerenderToStream    renderToStream L3258
   L8229  1996줄        L3258  1112줄
   세 갈래 894/245/100  RSC 렌더 -> HTML 렌더
   catch 559줄          catch 280줄
```

```text
 ★ 세 흐름을 꿰는 한 가지 — 반환값이 계약이다

   handleRSCRequest        return 다섯이 **전부 false**  (계약을 안 지킨다)
   handleCatchallRender…   return 일곱이 **전부 true**   ("내가 끝냈다")
   renderPageComponent     false = "내 것이 아니다"      / null = "Edge 로 이미 썼다"
   renderToResponse*       null  = "응답은 이미 나갔다"

 => base-server 가 ResponsePayload 를 실제로 만드는 자리는 **넷뿐**이고
    넷 다 정적이거나 에러다. 평범한 페이지는 라우트 모듈이 직접 쓴다
```

## 읽는 법

```text
 위치          그 코드가 실제로 어디 있는가 (파일·줄·퍼머링크)
 실제 코드     인용. 줄 번호를 붙였다
 동작 흐름     아스키 그림. 왼쪽 숫자가 소스 줄 번호다
 결과가 쓰이는 곳  이 코드가 만든 것을 누가 받는가
 다루지 않는 것    일부러 뺀 것. 다음에 뭘 읽을지의 목록이기도 하다

 표기
   +--   직접 호출
   ~~>   태스크·콜백 경계 (지금 프레임에서 이어지지 않는다)
   =>    갈래의 끝 (return / throw 가 적힌 줄에만 쓴다)
   ★     읽다가 놀란 것
   ※     내 해석이다. 소스가 그렇게 말한 것이 아니다
```

## 아직 안 쓴 것

```text
 API 역인덱스의 모든 행에 흐름 문서가 붙었고, 클라이언트 라우팅은 세그먼트 캐시 항목 ·
 프리페치 작업 · 라우트 예측까지 내려갔다. JS/TS 쪽에서 남긴 것은 일부러 뺀 것이다

 D  빌드의 나머지 (webpack 을 명시적으로 고른 앱에서만 돈다)
      build/webpack/config/**(buildConfiguration) · 개별 플러그인 · 로더 본문 · @vercel/nft 알고리즘

 Turbopack(Rust, crates/ 294,455줄)은 언어도 도구도 달라 **별도 문서 트리**로 간다
```
