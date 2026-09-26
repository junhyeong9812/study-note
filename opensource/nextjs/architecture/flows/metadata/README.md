# 메타데이터가 `<head>` 가 되기까지

상위: [Next.js 아키텍처 지도](../../README.md)

`export const metadata` 와 `export async function generateMetadata()` 는 **React 컴포넌트 셋으로 바뀌어** 렌더 트리에 들어간다. 그 셋을 만드는 함수가 `createMetadataComponents` 다. [App Router]가 RSC 페이로드를 만들 때 이 함수를 부르고, 받은 `Viewport` · `Metadata` 를 head 자리에, `MetadataOutlet` 을 페이지 옆에 꽂는다. [동적 판별]이 컴포넌트 스택에서 찾는 `__next_metadata_boundary__` 마커를 **실제로 트리에 심는 곳이 여기**다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `MDT` = `lib/metadata/metadata.tsx`(1913줄), `RMD` = `lib/metadata/resolve-metadata.ts`(1329줄), `BOUND` = `lib/framework/boundary-components.tsx`(52줄), `ICONMARK` = `lib/metadata/generate/icon-mark.tsx`(14줄), `SIMETA` = `server/app-render/metadata-insertion/create-server-inserted-metadata.tsx`(24줄).

## 위치

`packages/next` / `src/lib/metadata` / `metadata.tsx` L36-L182 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/lib/metadata/metadata.tsx#L36-L182))

## 실제 코드

마커 컴포넌트는 아무 일도 안 한다. **이름을 남기는 것**이 전부다.

```tsx
// boundary-components.tsx L11-L35
// We use a namespace object to allow us to recover the name of the function
// at runtime even when production bundling/minification is used.
const NameSpace = {
  [METADATA_BOUNDARY_NAME]: function ({ children }: { children: ReactNode }) {
    return children
  },
  [VIEWPORT_BOUNDARY_NAME]: function ({ children }: { children: ReactNode }) {
    return children
  },
  [OUTLET_BOUNDARY_NAME]: function ({ children }: { children: ReactNode }) {
    return children
  },
  [ROOT_LAYOUT_BOUNDARY_NAME]: function ({
    children,
  }: {
    children: ReactNode
  }) {
    return children
  },
}

export const MetadataBoundary =
  // We use slice(0) to trick the bundler into not inlining/minifying the function
  // so it retains the name inferred from the namespace object
  NameSpace[METADATA_BOUNDARY_NAME.slice(0) as typeof METADATA_BOUNDARY_NAME]
```

```text
 ★★★ 네 경계가 전부 `children` 을 그대로 돌려주는 함수다 (L14-29)
   METADATA · VIEWPORT · OUTLET · ROOT_LAYOUT
   이름은 boundary-constants.tsx 의 '__next_metadata_boundary__' 따위다

 ★★ 이름을 지키는 수법이 두 겹이다
   ① 객체 리터럴의 **계산된 키**로 함수를 만든다 — 함수 이름이 그 키로 추론된다
      주석 L11-12 - "We use a namespace object to allow us to recover the name
        of the function at runtime even when production bundling/minification is used."
   ② 꺼낼 때 `METADATA_BOUNDARY_NAME.slice(0)` 으로 꺼낸다
      주석 L33-34 - "We use slice(0) to trick the bundler into not inlining/minifying
        the function so it retains the name inferred from the namespace object"

 => [동적 판별] 03 의 `hasMetadataRegex`(DYNR L789-791)가
    `\n\s+at __next_metadata_boundary__` 를 스택 문자열에서 찾는다.
    **이름이 압축되면 그 정규식이 아무것도 못 찾는다.** 그래서 두 겹이다
 ★ 그리고 마커 파일은 **`'use client'`** 다 (BOUND L1). 정규식이 읽는 스택은 RSC 렌더가
   아니라 **클라이언트(Fizz) prerender** 의 onError 가 넘긴 componentStack 이다
   (app-render.tsx L9131-9165). 이름이 살아남아야 하는 곳이 SSR·클라이언트 번들이다
 ★★ 스트리밍으로 Metadata 가 Suspense 안에 들어가도 **"허용된 동적" 이 되지 않는다** —
   [동적 판별] [03]의 사다리에서 hasMetadataRegex(L877)가 hasSuspenseRegex(L894)보다
   **먼저** 걸리기 때문이다. 그래서 metadata 만 동적이면 [동적 판별] [04]의 ② 판정 대상이다
 ★ 저장소 전체 grep — `MetadataBoundary` · `ViewportBoundary` · `OutletBoundary` 를
   JSX 로 쓰는 곳은 **MDT 하나뿐**이다 (L90 · L134 · L141 · L167 · L170).
   `RootLayoutBoundary` 만 다른 곳(client/components/app-router.tsx L493)에서 쓴다
```

## 동작 흐름

```text
 lib/metadata/ 6,828줄 (테스트 6개 1,448줄 제외, 23개 파일)

   metadata.tsx            1913   컴포넌트 셋 + 태그 만들기            [01][04]
   resolve-metadata.ts     1329   트리 수집 · 순서 · 합치기            [02][03]
   types/ (9개)            2158   Metadata 타입 정의
   resolvers/ (5개)         818   필드별 정규화 (opengraph · url · basics · title · icons)
   is-metadata-route.ts     263 · get-metadata-route.ts 214   파일 기반 메타데이터 라우트
   default-metadata.tsx      65   기본값 (대부분 null — alternates·pagination 은 객체, verification·other 는 {})
   generate/ (2개) 42 · constants.ts 15 · metadata-context.tsx 11
   (열거 합계 = 6,828)
```

```text
 두 파일을 줄 번호로 자르면 네 구획이다

 MDT L36-182     createMetadataComponents — 컴포넌트 셋과 경계        [01]
 MDT L184-281    React cache() 로 감싼 네 getter와 render*          [01]
 RMD L495-927    모듈을 읽어 항목 배열을 만든다 (layout → page 순)     [02]
 RMD L1278-1319  resolveMetadata / resolveViewport — [01]이 부르는 입구 [02]
 RMD L1025-1276  generateMetadata 를 (대부분) **먼저** 부르고 순서대로 합친다 [03]
 RMD L159-493    키 하나씩 덮어쓰는 규칙 (mergeMetadata · mergeViewport)   [03]
 RMD L929-1023   합친 뒤 openGraph → twitter 채우기와 favicon           [03]
 MDT L283-353    viewport 를 <meta> 로                                 [04]
 MDT L359-1913   metadata 를 <title>/<meta>/<link> 로 — 함수 하나 1555줄  [04]

 ★ 나눈 이유 — 데이터가 모양을 세 번 바꾼다
   모듈의 export (Metadata | 함수)  --[02]-->  MetadataItems 배열
   MetadataItems                   --[03]-->  ResolvedMetadata 객체 하나
   ResolvedMetadata                --[04]-->  React 엘리먼트 배열
   [01]은 그 전체를 **언제·어디서** 돌릴지를 정한다
```

```text
 [App Router]가 부르는 자리 — 세 곳이다 (grep `createMetadataComponents(`)

 app-render.tsx L706    generateDynamicRSCPayload   RSC 요청(내비게이션)
 app-render.tsx L2102   getRSCPayload               첫 HTML 요청
 app-render.tsx L2253   getErrorRSCPayload          에러 화면 (shouldRenderMetadataAndViewport 일 때만)

 L2146  initialHead = <Fragment key=flightDataPathHeadKey>
          <NonIndex/> <Viewport/> <Metadata/> (next-size-adjust meta)
        </Fragment>
 L2190  f: [[initialTree, seedData, **initialHead**, isPossiblyPartialHead]]
 => head 는 트리와 **따로** 페이로드의 세 번째 칸에 실린다
 L2132  MetadataOutlet 은 createComponentTree 로 넘어가
        create-component-tree.tsx L912 에서 **페이지 엘리먼트 옆**에 놓인다

 ★ 에러 페이로드(L2249-2264)는 Viewport · Metadata 만 꺼내고 MetadataOutlet 은 버린다
```

1. [경계와 스트리밍](01_boundary/README.md) — 컴포넌트 셋이 같은 약속을 나눠 쥐고, 오류는 outlet 에서만 던진다.
2. [트리를 따라 모은다](02_collect/README.md) — 로더 트리를 깊이 우선으로 돌며 `[export, 파일 메타데이터]` 쌍을 쌓는다.
3. [부모를 약속으로 넘기며 합친다](03_accumulate/README.md) — `generateMetadata` 는 대부분 **먼저 불리고**(parent 를 쓰는 `'use cache'` 함수만 미뤄진다), 부모 값은 나중에 채워진다.
4. [태그로 내보낸다](04_tags/README.md) — 1555줄 함수 하나가 `tags.push` 를 182번 한다.

```text
 ★★★ `metadata` 와 `generateMetadata` 는 같은 칸에 들어간다 (RMD L522-547)

   typeof mod.generateMetadata === 'function' 이면 => 함수를 감싼 resolver 를 돌려준다
   아니면                                          => mod.metadata || null

 => 런타임 코드만 보면 둘 다 있을 때 **함수가 이긴다.** 정적 export 는 읽지도 않는다
 ★★★ 그런데 page · layout 에서는 그 상황이 **오지 않는다** — SWC RSC 변환이
   둘을 함께 내보내면 **빌드 오류**를 낸다
     crates/next-custom-transforms/src/transforms/react_server_components.rs
     L1061-1071 검사 · L361-364 문구
     ""metadata" and "generateMetadata" cannot be exported at the same time, please keep one of them."
   => 이 런타임 우선순위가 실제로 쓰이는 것은 그 검사가 안 걸리는 파일(에러 경계 등)이다
   ※ 검사 대상 정규식은 L912-916 (page · layout · route · 파일 기반 메타데이터 라우트)
 => 이후 [03]에서 "함수인가 객체인가" 만 보고 갈라진다.
    정적 `metadata` 는 **이미 풀린 결과**로 취급된다
 ★ viewport 도 런타임 규칙은 똑같다 — `generateViewport` 먼저, 없으면 `mod.viewport` (L495-520).
   그런데 viewport 에는 **컴파일 검사가 없다.** 그래서 런타임 우선순위가 실제로 작동하는 쪽은
   오히려 viewport 다
```

```text
 ★★ [`'use cache'`]와의 관계는 **표시 두 개**다

 RMD L66-69   import type { UseCacheLayoutProps, UseCachePageProps }
              from '../../server/use-cache/use-cache-wrapper'
   => **타입만** 가져온다. 런타임 의존은 없다

 RMD L554-563 createSegmentProps
   generateMetadata 가 'use cache' 함수면 props 에 표시를 붙인다
     page 쪽  { ...props, $$isPage: true }
     layout 쪽 { ...props, $$isLayout: true }
 UCW L2047-2121 이 그 표시를 읽고 **지운 뒤** 원래 함수에 넘긴다
   UCW L3571-3573 docstring - "Returns `true` if the `'use cache'` function is the
     page component itself, or `generateMetadata`/`generateViewport` in a page file."
 ★ create-component-tree.tsx L875 · L1051 이 페이지·레이아웃 컴포넌트에 같은 표시를 붙인다
   => 컴포넌트와 generateMetadata 가 **같은 규칙**으로 캐시 키를 만든다 ([`'use cache'`] 02)

 그리고 하나 더 — [03]의 getResult 가 'use cache' 함수의 **인자 사용 비트**를 읽는다
   (lib/client-and-server-references.ts L33-43 → server-reference-info.ts L33-60)
```

## 결과가 쓰이는 곳

```text
 Viewport · Metadata (컴포넌트)
      --> [App Router]의 initialHead 에 들어가 RSC 페이로드 `f` 의 세 번째 칸이 된다
          (app-render.tsx L2146-2165 · L2190-2197)
      --> RSC 요청이면 rscHead 로 (L715-732). 여기서는 요청마다 key 를 준다
          (getFlightViewportKey · getFlightMetadataKey)

 MetadataOutlet (컴포넌트)
      --> create-component-tree.tsx L912 에서 페이지 옆에 놓인다.
          `children` 슬롯에만 넘긴다 (L599-601)

 __next_metadata_boundary__ / __next_viewport_boundary__ / __next_outlet_boundary__ 스택 프레임
      --> [동적 판별] 03 의 정규식 셋이 찾는다 (DYNR L789-795)
      --> metadata 만 동적이면 빌드를 세우는 판정이 [동적 판별] 04 (DYNR L1356-1363)

 <meta name="«nxt-icon»"> 표지
      --> 스트림 변환(node-web-streams-helper.ts L351)이 지우거나 아이콘 이동 스크립트로 바꾼다 [04]
```

## 다루지 않는 것

`resolvers/`(818줄)의 필드별 정규화 — `resolveOpenGraph`(L161)의 og type 별 필드 표 · `resolveAlternates` · `resolveRobots` · `resolveUrl` 과 `metadataBase` 대체값(`getSocialImageMetadataBaseFallback`, `resolve-url.ts` L35) — 과 `types/`(2158줄)의 타입 정의, 파일 기반 메타데이터 라우트(`sitemap.xml` · `robots.txt` · `opengraph-image` 를 라우트로 만드는 `is-metadata-route.ts` · `get-metadata-route.ts`)와 빌드 로더가 `icon.png` 같은 파일을 `tree[2].metadata` 에 싣는 과정(`next-app-loader` 의 `createMetadataExportsCode`), `createServerParamsForMetadata` · `createServerSearchParamsForMetadata` · `createServerPathnameForMetadata` 가 만드는 약속과 `getMetadataVaryParamsAccumulator` 의 vary 추적, `NonIndex`(app-render.tsx L621)의 `noindex` 판단, 클라이언트 라우터가 head 를 받아 붙이는 쪽, `generateStaticParams` 와 메타데이터의 관계, 트레이싱 스팬 `ResolveMetadataSpan` 은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 경계와 스트리밍](01_boundary/README.md)
- [02 트리를 따라 모은다](02_collect/README.md)
- [03 부모를 약속으로 넘기며 합친다](03_accumulate/README.md)
- [04 태그로 내보낸다](04_tags/README.md)
