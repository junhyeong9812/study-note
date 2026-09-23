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
| `handleUpgrade` | `server/base-server.ts` L1765 (abstract) | 웹소켓 업그레이드 | - |
| middleware | `server/next-server.ts` L1814 | `handleCatchallMiddlewareRequest` | - |
| Route Handler (`GET`/`POST`…) | `server/route-modules/app-route/` | `route.ts` 의 메서드 export | - |

## 페이지에서 쓰는 서버 API

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `cookies()` | `server/request/cookies.ts` L33 | Promise 를 돌려준다. 동적 표시가 선다 | - |
| `headers()` | `server/request/headers.ts` L40 | 〃 | - |
| `draftMode()` | `server/request/draft-mode.ts` L28 | 〃. `isDraftMode` 가 `isStaticGeneration` 을 끈다 | [App Router](flows/app-render/README.md) |
| `connection()` | `server/request/connection.ts` L26 | 요청이 실제로 올 때까지 기다린다 | - |
| `after(task)` | `server/after/after.ts` L10 | 응답 뒤에 일을 미룬다. `waitUntil` 이 없으면 에러 | [요청→렌더](flows/request-to-render/05_render/README.md) |
| `params` / `searchParams` | `server/request/params.ts` · `search-params.ts` | 페이지 props | - |
| `generateStaticParams` | `build/static-paths/app.ts` | 빌드가 경로를 미리 만든다 | - |
| `generateMetadata` | `lib/metadata/` | - | - |

## 캐시와 재검증

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `revalidateTag(tag, profile)` | `server/web/spec-extension/revalidate.ts` L35 | 태그를 무효화한다 | - |
| `revalidatePath(path, type?)` | 〃 L100 | 경로를 무효화한다 | - |
| `updateTag(tag)` | 〃 L52 | - | - |
| `unstable_cache(cb, …)` | `server/web/spec-extension/unstable-cache.ts` L62 | Pages Router 는 `globalThis.__incrementalCache` 를 탄다 | [요청→렌더](flows/request-to-render/02_normalize/README.md) |
| `'use cache'` | `server/use-cache/` | - | - |
| `cacheLife(profile)` | `server/use-cache/cache-life.ts` L26 | - | - |
| `cacheTag(...tags)` | `server/use-cache/cache-tag.ts` L4 | - | - |
| `fetch` (확장된 것) | `ComponentMod.patchFetch()` | 요청마다 전역 fetch 를 갈아끼운다 | [App Router](flows/app-render/02_prepare/README.md) |

```text
 ★ 위 셋이 실행되는 자리는 이미 문서에 있다
   executeRevalidates(workStore)  app-render.tsx L2848 / L3071
   => 렌더 중에 쌓아 두었다가 **렌더가 끝난 뒤** 한꺼번에 실행한다.
      다만 출구 일곱 중 하나만 그것을 지난다 ([App Router]의 03 참고)
```

## 흐름을 끊는 것

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `redirect(url, type?)` | `client/components/redirect.ts` L33 | 예외를 던져 위로 전파한다 | - |
| `permanentRedirect(...)` | 〃 L55 | 308 판 | - |
| `notFound()` | `client/components/not-found.ts` L23 | `never`. 예외를 던진다 | [응답 나가기](flows/response-out/04_error/README.md) |
| `forbidden()` | `client/components/forbidden.ts` L22 | 〃 403 | - |
| `unauthorized()` | `client/components/unauthorized.ts` L23 | 〃 401 | - |

## 클라이언트에서 쓰는 것

| API | 위치 | 하는 일 | 흐름 |
|---|---|---|---|
| `<Link>` | `client/app-dir/link.tsx` L340 | 프리페치 헤더 `1`/`2`/`3` 을 만든다 | [App Router](flows/app-render/01_entry/README.md) |
| `useRouter()` | `client/components/navigation.ts` L166 | `AppRouterInstance` | - |
| `usePathname()` | 〃 L112 | - | - |
| `useSearchParams()` | 〃 L55 | - | - |
| `useSelectedLayoutSegments()` | 〃 L267 | - | - |
| `<AppRouter>` | `client/components/app-router.tsx` | 내비게이션 상태 기계의 뿌리 | - |
| `<LayoutRouter>` | `client/components/layout-router.tsx` | - | - |
| 세그먼트 캐시 | `client/components/segment-cache/` 11,522줄 | - | - |

## Pages Router

| API | 위치 | 흐름 |
|---|---|---|
| `getServerSideProps` | `server/render.tsx` | - |
| `getStaticProps` | 〃 | - |
| `getStaticPaths` | `server/base-server.ts` L2033 (기본값은 `undefined` 고정) | [응답 나가기](flows/response-out/02_delegate/README.md) |
| API Route (`pages/api/`) | `server/next-server.ts` `handleApiRequest` | [요청→렌더](flows/request-to-render/04_handoff/README.md) |

## 아직 문서가 없는 큰 덩어리

```text
 A  app-render.tsx 의 나머지
      renderToStream          L3258-4369   1112줄   동적 응답을 흘린다
      prerenderToStream       L8229-10224  1996줄   정적 응답을 만든다
      검증 기계               L4418-8228   약 3800줄
      create-component-tree.tsx  1307줄    로더 트리 -> 컴포넌트
      dynamic-rendering.ts       1592줄    정적·동적 경계
      action-handler.ts          1580줄    서버 액션
      collect-segment-data.tsx   1528줄    세그먼트 캐시용 분해

 B  클라이언트 라우팅          client/components/   23,345줄
 E  Pages Router               server/render.tsx 외  약 4,000줄
 D  빌드 (webpack 경로)        build/               62,106줄
 F  Turbopack (Rust)           별도 문서 트리       294,455줄
```
