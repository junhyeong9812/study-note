# API 역인덱스

상위: [Next.js 아키텍처 지도](README.md)

Next.js 를 쓸 때 실제로 만지는 것에서 소스로 거꾸로 찾는 표다. "이걸 부르면 어디로 가는가" 를 묻는다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 경로는 전부 `packages/next/src/` 기준이다.

```text
 ★ 흐름 칸이 "-" 인 것은 **아직 문서로 쓰지 않았다**는 뜻이다.
   이 표가 곧 남은 일의 목록이다
```

## 서버가 요청을 받는 자리

| 진입점 | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `getRequestHandler()` | `server/next-server.ts` L1269 | 노드 req/res 를 Next 래퍼로 감싼다. **진짜 진입점** | [요청→렌더](flows/request-to-render/01_entry/README.md) |
| `handleRequest` | `server/base-server.ts` L910 | OTEL 스팬을 열고 `prepare()` 를 기다린다 | [요청→렌더](flows/request-to-render/01_entry/README.md) |
| `handleRequestImpl` | `server/base-server.ts` L1026 | 670줄 정규화 파이프라인. 나가는 길이 스물 | [요청→렌더](flows/request-to-render/02_normalize/README.md) |
| `handleCatchallRenderRequest` | `server/next-server.ts` L1078 | 라우트를 고른다. 그리고 base 로 되돌아온다 | [요청→렌더](flows/request-to-render/04_handoff/README.md) |
| `renderToResponseImpl` | `server/base-server.ts` L2704 | 매치를 순차로 시도한다 | [요청→렌더](flows/request-to-render/05_render/README.md) |
| `renderToResponseWithComponentsImpl` | `server/base-server.ts` L2110 | 플래그 23개를 세우고 라우트 모듈에 넘긴다 | [응답 나가기](flows/response-out/01_decide/README.md) |
| `pipe` / `pipeImpl` | `server/base-server.ts` L1832 / L1846 | payload 가 null 이면 그냥 돌아선다 | [응답 나가기](flows/response-out/03_pipe/README.md) |
| `renderErrorToResponseImpl` | `server/base-server.ts` L2945 | 에러 페이지 폴백 사슬 | [응답 나가기](flows/response-out/04_error/README.md) |
| `renderToHTMLOrFlight` | `server/app-render/app-render.tsx` L3101 | App Router 렌더의 진입 | [App Router](flows/app-render/01_entry/README.md) |
| `renderToStream` | `server/app-render/app-render.tsx` L3258 | 동적 응답. RSC 렌더 -> HTML 렌더 | [동적 응답](flows/render-to-stream/README.md) |
| `prerenderToStream` | `server/app-render/app-render.tsx` L8229 | 정적 응답. 빌드와 ISR 재검증 | [정적 응답](flows/prerender-to-stream/README.md) |
| `handleUpgrade` | `server/base-server.ts` L1765 (abstract) | abstract 인데 NextNodeServer 구현은 **빈 본문**. 실제 업그레이드는 router-server upgradeHandler 가 한다 | [페이지 아닌 요청](flows/non-page/03_upgrade/README.md) |
| middleware | `server/lib/router-utils/resolve-routes.ts` L558 | router-server 가 render server 를 한 번 더 불러 실행하고 답을 헤더로 해석한다. Node 는 프로세스 안, Edge 는 sandbox | [페이지 아닌 요청](flows/non-page/01_middleware/README.md) |
| Route Handler (`GET`/`POST`…) | `server/route-modules/app-route/` | **기본이 동적** — 정적 생성은 옵트인. 켜졌을 때만 요청 객체 Proxy 가 무엇을 읽는지 지켜본다 | [페이지 아닌 요청](flows/non-page/02_route-handler/README.md) |
| Server Action (`'use server'`) | `server/app-render/action-handler.ts` L567 | 관문 여덟을 지나 사용자 함수를 부른다 | [서버 액션](flows/server-action/README.md) |

## 페이지에서 쓰는 서버 API

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `cookies()` | `server/request/cookies.ts` L33 | **요청 데이터**. 정적 prerender 에서 런타임 기록을 남기며 매달리고, 캐시 스코프에서 던진다 | [동적 API](flows/request-apis/01_cookies-headers/README.md) |
| `headers()` | `server/request/headers.ts` L40 | cookies 와 결말표가 같다. 다만 switch 가 **둘**이라 관문 순서가 다르다 | [동적 API](flows/request-apis/01_cookies-headers/README.md) |
| `draftMode()` | `server/request/draft-mode.ts` L28 | 〃. `isDraftMode` 가 `isStaticGeneration` 을 끈다 | [App Router](flows/app-render/README.md) |
| `connection()` | `server/request/connection.ts` L26 | **실제 이동 요청**이 있어야만 풀린다. 런타임 prerender·private 캐시에서도 안 된다 | [동적 API](flows/request-apis/02_connection-io/README.md) |
| `after(task)` | `server/after/after.ts` L10 | 응답 뒤에 일을 미룬다. `waitUntil` 이 없으면 에러 | [요청→렌더](flows/request-to-render/05_render/README.md) |
| `params` / `searchParams` | `server/request/params.ts` · `search-params.ts` | 사용자가 부르지 않는다 — 프레임워크 팩토리 아홉이 만든다. `await searchParams` 는 `then` 덫으로 잡는다 | [동적 API](flows/request-apis/04_params/README.md) |
| `generateStaticParams` | `build/static-paths/app.ts` | 빌드가 경로를 미리 만든다 | [정적 응답](flows/prerender-to-stream/03_ppr/README.md) |
| `generateMetadata` | `lib/metadata/resolve-metadata.ts` L522 | 렌더 전에 **전부 한꺼번에** 불린다. `parent` 는 위까지 합친 값의 약속. 최상위 키 덮어쓰기(`other` 만 얕게 병합) | [메타데이터](flows/metadata/03_accumulate/README.md) |

## 캐시와 재검증

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `revalidateTag(tag, profile)` | `server/web/spec-extension/revalidate.ts` L35 | 태그를 쌓는다. 둘째 인자 없이 부르면 경고 | [재검증](flows/revalidation/01_collect/README.md) |
| `revalidatePath(path, type?)` | 〃 L100 | 경로를 **태그로 바꿔** 쌓는다. profile 을 안 넘기므로 의미상 `updateTag` 쪽 | [재검증](flows/revalidation/01_collect/README.md) |
| `updateTag(tag)` | 〃 L52 | profile 을 안 넘겨 **클라이언트 캐시까지** 버린다 | [재검증](flows/revalidation/03_notify/README.md) |
| `unstable_cache(cb, …)` | `server/web/spec-extension/unstable-cache.ts` L62 | Pages Router 는 `globalThis.__incrementalCache` 를 탄다 | [요청→렌더](flows/request-to-render/02_normalize/README.md) |
| `'use cache'` | `server/use-cache/use-cache-wrapper.ts` L1715 | 컴파일러가 `cache(kind, id, …)` 호출로 바꾼다. 그 함수가 **1855줄** | [`'use cache'`](flows/use-cache/README.md) |
| `'use cache: private'` | 〃 (`kind === 'private'`) | 정적 prerender 에서 살아남지 못한다. public 캐시 안에 중첩 불가 | [`'use cache'`](flows/use-cache/01_enter/README.md) |
| `refresh()` | `server/web/spec-extension/revalidate.ts` L73 | 서버 액션에서만. **클라이언트 동적 데이터만** 새로 받게 한다 | [재검증](flows/revalidation/01_collect/README.md) |
| `cacheLife(profile)` | `server/use-cache/cache-life.ts` L26 | 세 값을 각각 **최솟값으로만** 좁힌다. 캐시 함수 안에서만 | [`'use cache'`](flows/use-cache/04_life/README.md) |
| `cacheTag(...tags)` | `server/use-cache/cache-tag.ts` L4 | 렌더 중 아무 때나 부를 수 있어 **스트림을 다 버퍼링한 뒤** 모은다 | [`'use cache'`](flows/use-cache/04_life/README.md) |
| `markCurrentScopeAsDynamic` | `server/app-render/dynamic-rendering.ts` L172 | 같은 값으로 switch 를 **두 번** — 캐시 스코프면 무효, 아니면 렌더 모드별로 네 갈래 | [동적 판별](flows/dynamic-rendering/01_mark/README.md) |
| `postponeWithTracking` | 〃 L412 | `React.unstable_postpone`. 알아보는 방법이 **문자열 두 조각** | [동적 판별](flows/dynamic-rendering/02_interrupt/README.md) |
| `throwToInterruptStaticGeneration` | 〃 L249 | cacheComponents·PPR 없는 프리렌더용. `revalidate = 0` 으로 만들고 던진다 | [동적 판별](flows/dynamic-rendering/01_mark/README.md) |
| `throwIfDisallowedDynamic` | 〃 L1342 | 빌드를 세울지 정한다. **순서가 규칙의 전부** | [동적 판별](flows/dynamic-rendering/04_verdict/README.md) |
| `fetch` (확장된 것) | `ComponentMod.patchFetch()` | 요청마다 전역 fetch 를 갈아끼운다 | [App Router](flows/app-render/02_prepare/README.md) |

```text
 ★ 쌓기 -> 실행 -> 알리기 세 단계다 ([재검증] 흐름)
   쌓기    revalidate.ts L128   workStore.pendingRevalidatedTags 에 밀어 넣는다
   실행    revalidation-utils.ts L186  세 통을 모아 Promise.all (호출처 다섯)
   알리기  action-handler.ts L151      클라이언트에 0/1/2 중 하나를 헤더로
   => 대개 거기서 캐시가 지워지지 않는다. 배열에 쌓이고 끝난다
   => 그리고 **렌더 중에 부르면 던진다.** 통과하는 길은 둘뿐이다 —
      workUnitStore 가 없거나, type 이 'request' 일 때
```

## 흐름을 끊는 것

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `redirect(url, type?)` | `client/components/redirect.ts` L33 | 예외를 던져 위로 전파한다. 액션 안이면 fetch 는 200 + `x-action-redirect`, MPA 는 303 | [서버 액션](flows/server-action/03_control-flow/README.md) · [동적 응답](flows/render-to-stream/04_error-recovery/README.md) |
| `permanentRedirect(...)` | 〃 L55 | 308 판 | [동적 응답](flows/render-to-stream/04_error-recovery/README.md) |
| `notFound()` | `client/components/not-found.ts` L23 | `never`. 예외를 던진다 | [동적 응답](flows/render-to-stream/04_error-recovery/README.md) · [응답 나가기](flows/response-out/04_error/README.md) |
| `forbidden()` | `client/components/forbidden.ts` L22 | 〃 403 | [동적 응답](flows/render-to-stream/04_error-recovery/README.md) |
| `unauthorized()` | `client/components/unauthorized.ts` L23 | 〃 401 | [동적 응답](flows/render-to-stream/04_error-recovery/README.md) |

## 클라이언트에서 쓰는 것

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `<Link>` | `client/app-dir/link.tsx` L340 | hover 하면 Intent 우선순위 프리페치가 걸린다 | [세그먼트 캐시](flows/segment-cache/02_scheduler/README.md) |
| 프리페치 헤더 `1`/`2`/`3` | `segment-cache/cache.ts` L3063-3078 | FetchStrategy 를 헤더 값으로 바꾼다 | [세그먼트 캐시](flows/segment-cache/README.md) · [App Router](flows/app-render/01_entry/README.md) |
| `useRouter()` | `client/components/navigation.ts` L166 | `AppRouterInstance`. `.push()` 가 ACTION_NAVIGATE 를 디스패치한다 | [클라이언트](flows/client-router/02_navigate/README.md) |
| `usePathname()` | 〃 L112 | `canonicalUrl` 에서 basePath 를 뗀 값을 `PathnameContext` 로 받는다 | [클라이언트 트리](flows/client-components/04_hooks/README.md) |
| `useSearchParams()` | 〃 L55 | `SearchParamsContext` 를 감싼다. prerender 에서는 동적 — `prerender-client` 는 매달리고 옛 경로는 `BailoutToCSRError` | [클라이언트 트리](flows/client-components/04_hooks/README.md) |
| `useSelectedLayoutSegments()` | 〃 L267 | 가장 가까운 `LayoutRouterContext` 의 트리를 아래로 걷는다. `__PAGE__` 에서 멈춘다 | [클라이언트 트리](flows/client-components/04_hooks/README.md) |
| `<AppRouter>` | `client/components/app-router.tsx` L579 | `useActionQueue` 로 구독해 Context **일곱**을 공급한다 | [클라이언트 트리](flows/client-components/02_provide/README.md) |
| `router-reducer` | `client/components/router-reducer/router-reducer.ts` L23 | 액션 6종. 서버에서는 noop 이 된다 | [클라이언트](flows/client-router/01_dispatch/README.md) |
| `<LayoutRouter>` | `client/components/layout-router.tsx` L706 | 서버는 경계 props 만 준다. 내용은 부모 `CacheNode.slots` 에서 꺼낸다 | [클라이언트 트리](flows/client-components/03_layout-router/README.md) |
| 세그먼트 캐시 | `client/components/segment-cache/` 11,522줄 | 캐시 둘 · 완성도 6단계 · 프리페치 큐 | [세그먼트 캐시](flows/segment-cache/README.md) |
| `router.refresh()` (클라이언트) | `router-reducer/reducers/refresh-reducer.ts` L22 | `RefreshAll` 로 내비게이션한다. 세그먼트 캐시(`invalidateSegmentCacheEntries`, L39)와 BFCache(`invalidateBfCache`) 버전을 모두 올리고 겹치는 레이아웃까지 다시 채운다 | [PPR 내비게이션](flows/ppr-navigation/02_fill-segment/README.md) |
| `router.back()` / `forward()` | `router-reducer/reducers/restore-reducer.ts` L23 | `HistoryTraversal`. BFCache 를 신선도 검사 없이 읽는다. 버전이 올라갔으면 못 찾는다 | [PPR 내비게이션](flows/ppr-navigation/02_fill-segment/README.md) |
| `fetchServerResponse` | `router-reducer/fetch-server-response.ts` L149 | 내비게이션의 RSC 요청. 실패는 네 갈래 모두 URL 문자열(MPA)로 돌아온다 | [PPR 내비게이션](flows/ppr-navigation/03_fetch/README.md) |
| `router.prefetch(href, { onInvalidate })` | `client/components/segment-cache/prefetch.ts` · `cache.ts` L458 | Default 우선순위 작업 하나를 만든다(개발 서버에서는 만들지 않는다). onInvalidate 는 전역 Set 에 모였다가 무효화 때 한 번 불린다 | [프리페치 작업](flows/prefetch-tasks/README.md) · [캐시 항목](flows/cache-entries/04_stale-evict/README.md) |
| `<Link prefetch>` | `client/components/links.ts` | 뷰포트에 들어오면 Default, hover 하면 Intent. `true` 는 Full 전략 | [프리페치 작업](flows/prefetch-tasks/02_one-pass/README.md) |
| `experimental.optimisticRouting` | `server/config-shared.ts` L2175 (기본 true) | 라우트 캐시 미스일 때 배운 패턴으로 트리를 예측한다(`matchKnownRoute`). 꺼지면 서버가 staticSiblings 도 안 보낸다 | [라우트 예측](flows/route-prediction/README.md) |
| `experimental.varyParams` | `server/config-shared.ts` L2174 (기본 true) | 세그먼트 항목을 실제로 읽은 params 기준의 더 일반적인 키로 다시 건다. 서버가 값을 싣는 것은 cacheComponents 렌더뿐 | [캐시 항목](flows/cache-entries/02_fill/README.md) |
| `staleTimes.static` | `segment-cache/cache.ts` L122 `getStaleTimeMs` | 서버 · 설정의 stale 값에 30초 하한을 씌운다 | [캐시 항목](flows/cache-entries/04_stale-evict/README.md) |
| Instant Navigation Testing 쿠키 | `segment-cache/navigation-testing-lock.ts` · `build/define-env.ts` L396 | 개발에서는 늘 켜져 있고 프로덕션 번들에서는 `.disabled` 모듈로 바뀐다. 잠긴 동안 서버는 셸만, 클라이언트는 동적 데이터 쓰기를 미룬다 | [라우트 예측](flows/route-prediction/04_testing-lock/README.md) |

## Pages Router

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `getServerSideProps` | `server/render.tsx` (renderToHTMLImpl L459) | 요청마다 `_app` 의 getInitialProps 다음에 불린다. data 요청이면 HTML 없이 JSON 만 나간다 | [Pages Router](flows/pages-router/01_render/README.md) |
| `getStaticProps` | 〃 | `_app` gIP 다음에 불린다. HTML 과 JSON 이 한 응답 캐시 항목에 들어간다 | [Pages Router](flows/pages-router/01_render/README.md) |
| `getStaticPaths` | `server/base-server.ts` L2033 · `build/static-paths/pages.ts` | fallback false 면 NoFallbackError, 문자열이면 fallback 셸을 꺼낸다 | [Pages Router](flows/pages-router/README.md) |
| `getInitialProps` | `server/render.tsx` · `shared/lib/router/router.ts` | 서버에서는 `_app` 경유로 가장 먼저, 클라이언트 이동 때는 req/res 없이 불린다 | [Pages Router](flows/pages-router/01_render/README.md) |
| `_document` | `pages/_document.tsx` | 페이지를 먼저 문자열로 만든 뒤 `<Main/>` 자리표시로 잘라 끼운다 | [Pages Router](flows/pages-router/01_render/README.md) |
| API Route (`pages/api/`) | `server/next-server.ts` `handleApiRequest` → `api-resolver.ts` | 응답 캐시가 없고 res 에 편의 메서드 여덟을 직접 붙인다 | [Pages Router](flows/pages-router/04_api/README.md) |
| `useRouter` (`next/router`) | `client/router.ts` | 렌더마다 만드는 복사본. coreMethodFields 여섯만 옮겨 `forward` 가 없다 | [Pages Router](flows/pages-router/02_hydrate/README.md) |

## 즉시 내비게이션 검증

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `export const instant` | `build/segment-config/app/app-segment-config.ts` L133 | 값은 넷(없음 · true · false · 객체). cacheComponents 없이 쓰면 빌드 오류. 기본 수준에서는 설정이 없어도 개발 서버가 page 를 암묵 검증한다 | [instant 검증](flows/instant-validation/01_gate/README.md) |
| `experimental.instantInsights.validationLevel` | `server/config.ts` L1671 | 기본 'warning' 은 개발만 검증한다. 빌드 검증은 'experimental-*' 나 세그먼트 `level: 'experimental-error'` 로 라우트가 켜질 때 | [instant 검증](flows/instant-validation/01_gate/README.md) |
| `validateInstantConfigsInBuild` | `server/app-render/app-render.tsx` L7726 | prerender 뒤 샘플마다 다시 렌더해 검증한다. 샘플이 없으면 요청 API 를 읽는 순간 실패하고, 실패하면 StaticGenBailoutError | [instant 검증](flows/instant-validation/04_verdict/README.md) |

## 빌드

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `next build` | `build/index.ts` `build` L1042 | CLI 가 부르는 입구. **3558줄** 함수 하나이고 `// #region` 다섯이 단계의 뼈대다 | [빌드](flows/build/README.md) |
| `generateStaticParams` (빌드 쪽) | `build/static-paths/app.ts` | 빌드의 Collect data 단계에서 `'generate-static-params'` 스토어 안에서 불린다 (그 스토어를 만드는 곳은 L628 하나) | [빌드](flows/build/03_collect/README.md) |
| `next.config` 의 `webpack` 훅 | `build/webpack-config.ts` L2587 | 기본 설정 조립 뒤에 불린다. falsy 를 돌려주면 throw, 사용자 CSS 규칙이 있으면 내장 CSS 를 걷어낸다. webpack · Rspack 전용 | [빌드 세부](flows/build-details/01_config/README.md) |
| `serverExternalPackages` / `transpilePackages` | `build/webpack-config.ts` L892-922 · `build/handle-externals.ts` L293-298 | node 서버에서 App 레이어는 기본으로 번들하고 Pages 레이어는 node_modules 를 밖에 둔다. 기본 opt-out 79개. 둘이 겹치면 throw | [빌드 세부](flows/build-details/01_config/README.md) |
| `outputFileTracingIncludes` / `Excludes` | `build/collect-build-traces.ts` L94 · `crates/next-api/src/nft.rs` | webpack 이면 NFT 가 두 번(컴파일 중 · 뒤) 돌아 같은 `.nft.json` 에 합친다. Turbopack 은 Rust 가 따로 적용한다 | [빌드 세부](flows/build-details/02_trace/README.md) |
| `output: 'standalone'` | `build/utils.ts` `copyTracedFiles` L1223 | 번들러와 무관하게 `.nft.json` 목록대로 복사하고 설정을 박은 server.js 를 쓴다. `.next/static` · `public` 은 복사하지 않는다 | [빌드 세부](flows/build-details/04_standalone/README.md) |
| `adapterPath` (`modifyConfig` / `onBuildComplete`) | `build/adapter/build-complete.ts` L557 · `server/config.ts` L1721 | 빌드 끝에 `.next` 를 outputs · routing 으로 번역해 한 번 넘긴다. modifyConfig 는 loadConfig 마다 돈다. 해시는 Turbopack 일 때만 | [빌드 세부](flows/build-details/03_adapter/README.md) |

## 아직 문서가 없는 큰 덩어리

```text
 F  Turbopack (Rust)           별도 문서 트리 예정    crates/ 294,455줄
```
