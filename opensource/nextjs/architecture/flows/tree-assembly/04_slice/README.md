# 04 세그먼트로 자르기

상위: [트리를 조립하고 세그먼트로 자르기까지](../README.md)

[01]~[03]이 만든 트리는 prerender 되어 RSC 버퍼 하나가 된다. 이 구획은 그 버퍼를 **다시 디코드해서 세그먼트마다 따로 인코드**한다. 새로 렌더하는 것이 아니다 — 이미 끝난 결과를 쪼갠다. [프리페치]의 클라이언트가 `/_tree` 와 세그먼트 키로 요청하는 응답을 **미리** 만들어 두는 곳이다. 정적 생성(빌드 · ISR) 때 생기고 — PPR 갈래와 평범한 정적 생성 갈래 모두다(app-render L9624-9634) — 요청 때는 캐시에서 주거나 **404** 다(app-page-runtime.ts L1763-1810 — 주석 "should never reach the application layer"). 정적 생성되지 않는 동적 라우트(PPR 꺼짐)의 `/_tree` 는 이것과 **별개로** [중간부터 그리기] 가 요청 시점에 만든다 — 캐시 미스를 대신하는 관계가 아니다.

## 위치

`packages/next` / `src/server/app-render` / `collect-segment-data.tsx` L279-L469 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/collect-segment-data.tsx#L279-L469))

## 실제 코드

결과 Map 의 키 셋이 이 함수의 산출물을 요약한다.

```tsx
// collect-segment-data.tsx L435-L466
  // Write the route tree to a special `/_tree` segment.
  const treeBuffer = await streamToBuffer(treeStream)
  resultMap.set('/_tree' as SegmentRequestKey, treeBuffer)

  // Also output the entire full page data response
  resultMap.set('/_full' as SegmentRequestKey, fullPageDataBuffer)

  // Await the segment tasks in parallel and write the segment prefetches to
  // the result map.
  let hasPageSegment = false
  for (const [segmentPath, buffer] of await Promise.all(segmentTasks)) {
    resultMap.set(segmentPath, buffer)
    if (segmentPath.endsWith('__PAGE__')) {
      hasPageSegment = true
    }
  }

  if (!hasPageSegment) {
    // The build requires at least one segment path ending with __PAGE__ to
    // register the catch-all segment data route. When all page segments are
    // disabled (e.g. every leaf has runtime prefetching), no __PAGE__ entry
    // is emitted. Write a dummy entry with a path that doesn't match any
    // real route segment so the client will never request it.
    //
    // TODO: Remove the __PAGE__ requirement from the build instead of
    // working around it here. The invariant is outdated now that segments
    // can be disabled.
    resultMap.set(
      '/todo-remove-fake-segment/__PAGE__' as SegmentRequestKey,
      Buffer.alloc(0)
    )
  }
```

```text
 ★★★ 키가 세 종류다

   '/_tree'   라우트 트리 — [프리페치]의 클라이언트가 가장 먼저 받는 것
   '/_full'   페이지 전체 버퍼 그대로 (다시 인코드하지 않는다)
   세그먼트마다 하나 — '…/__PAGE__' 같은 SegmentRequestKey

 => [프리페치] [README]가 "서버가 세그먼트 캐시 프로토콜을 알아보는 것은
    `NEXT_ROUTER_SEGMENT_PREFETCH_HEADER === '/_tree'`" 라고 한 그 '/_tree' 가
    **여기서 만들어진다** (L437)

 ★★★ 그리고 `__PAGE__` 가 하나도 없으면 **가짜 세그먼트**를 넣는다 (L447-466, `!hasPageSegment` 일 때만)
   '/todo-remove-fake-segment/__PAGE__' → Buffer.alloc(0)
   주석 L453-458 - "The build requires at least one segment path ending with __PAGE__ to
     register the catch-all segment data route. When all page segments are disabled (e.g.
     every leaf has runtime prefetching), no __PAGE__ entry is emitted. Write a dummy entry
     with a path that doesn't match any real route segment so the client will never request it."
   주석 L459-461 - "TODO: Remove the __PAGE__ requirement from the build instead of working
     around it here. The invariant is outdated now that segments can be disabled."
 => 키 이름 자체가 `todo-remove` 다. 빌드의 낡은 불변식을 맞추려는 **자리표**다
```

## 동작 흐름

```text
 누가 부르는가 — app-render.tsx

 prerenderToStream (L8229, [정적 응답])
   L9076 · L9414 · L9627 · L10175  await collectSegmentData(...)   ← app-render 쪽 **감싸는 함수**
     app-render.tsx L10417  async function collectSegmentData(...)
       L10569  metadata.segmentData = await ComponentMod.collectSegmentData(...)   ← **이 파일의 것**

 주석 L10427-10436
   "All of the segments for a page are generated simultaneously, including during
    revalidations. This is to ensure consistency, because it's possible for a mismatch
    between a layout and page segment can cause the client to error during rendering. ...
    For performance, we reuse the Flight output that was created when generating the
    initial page HTML. The Flight stream for the whole page is decomposed into a separate
    stream per segment."

 => 자르기는 **prerender 때**(빌드 · 재검증) 일어난다. 요청마다가 아니다 — 대체로.
    네 호출처 모두 shouldGenerateStaticFlightData 로 거른다 (app-render L2787)
 ★ 예외를 소스가 인정한다 — 루트 세그먼트에 `instant = false` 가 있으면 prerender 가
   요청마다 돈다 (TODO #91407 — create-flight-router-state-from-loader-tree.ts L69-75 ·
   app-render L10532-10536)
 => 한 페이지의 세그먼트를 **한꺼번에** 자른다 — 레이아웃과 페이지가 어긋나면
    클라이언트가 렌더 중 오류를 낼 수 있어서다
 ★ 이름이 같은 함수가 두 파일에 있다. 바깥 것은 매니페스트·힌트를 모으고
   ComponentMod(번들된 entry-base) 를 거쳐 안쪽 것을 부른다
```

```text
 collectSegmentData   CSEG L279-469

 L279  (isCacheComponentsEnabled, fullPageDataBuffer, staleTime, clientModules,
        serverConsumerManifest, prefetchInlining, hints, isUpgradeableISRFallback)
        => Promise<Map<SegmentRequestKey, Buffer>>

 ① 워밍업 디코드            L294-329
 ② 두 단계 디코드 준비       L331-366
 ③ 시간 제한                L368-376
 ④ 트리 prerender           L384-433   <PrefetchTreeData …/> — 세그먼트 작업을 뿌린다
 ⑤ 결과 모으기              L436-466   '/_tree' · '/_full' · 세그먼트 · 가짜
```

```text
 ★★★ ① 워밍업 — 한 번 디코드해서 **세 가지**를 얻는다 (주석 L294-307)

   "warm up the module cache by decoding the page data once. Then we can assume that
    any remaining async tasks that occur the next time are due to hanging promises
    caused by dynamic data access."

   얻는 것
     모듈 캐시         두 번째 디코드부터는 모듈 로드로 기다리지 않는다
     `a` 필드          셸 단계가 끝나는 **바이트 위치** (L324)
     `u` 필드          렌더가 런타임 데이터를 읽었는가 (L327)

 L327  runtimeDataAccessed = readRuntimeDataAccessed(pagePayload.u)
 ★★ 그런데 이 boolean 은 **대부분 쓰이지 않는다.** 세그먼트 응답마다
   `needsRuntimeRequest = initialRSCPayload.u ?? Promise.resolve(runtimeDataAccessed)` (L997-998)
   — `u` 가 있으면 **약속을 그대로** 넘기고, 이 값은 `u` 가 없을 때의 대체값일 뿐이다
 => [동적 API] 가 남긴 기록(`u`)은 여기서 풀리는 것이 아니라 **세그먼트 응답에 실려
    클라이언트까지 간다.** `u` 를 true 로 푸는 쪽은 trackRuntimeDataAccessed 말고도
    trackFallbackParamsAccessed · makeStageHangingPromise 가 있고, prerender 가 끝나면
    false 로 푼다 (app-render L8930 · L9020)
 ★ L309 기본값이 **true** 다 — 주석 "Conservatively true when the page carries no flag
   (legacy render paths) or the decode fails"
 ★★ L329 `} catch {}` — 워밍업 디코드가 실패해도 **조용히 넘어간다.**
   그러면 기본값 true 가 남고 `a` 는 undefined 다. 실패가 "보수적인 값" 으로 흡수된다
```

```text
 ★★ ③ 트리 prerender 를 **한 태스크 뒤 무조건** 끊는다 (L369-376)

   const onCompletedProcessingRouteTree = async () => {
     // Since all we're doing is decoding and re-encoding a cached prerender, if
     // serializing the stream takes longer than a microtask, it must because of
     // hanging promises caused by dynamic data.
     await waitAtLeastOneReactRenderTask()
     abortController.abort()
   }

 => 트리 순회가 끝나면(L1058 에서 부른다) 한 태스크를 기다린 뒤 **조건 없이** abort 한다.
    이것이 멈추는 것은 **`/_tree` prerender 하나**다 (L407 의 signal)
 => 주석의 논리 — 이미 끝난 prerender 를 다시 인코드할 뿐이니 한 태스크면 충분하고,
    그래도 남은 것은 매달린 약속뿐이다
 ★ 세그먼트 버퍼의 구멍은 **여기서 정하지 않는다** — renderSegmentPrefetch 가 따로
   release 를 기다린 뒤 한 태스크(L1407), 다시 둘(L1439-1440)을 기다리고 자기 abort 를
   부른다(L1443). 중단 뒤 나온 오류 행은 버린다(L1360-1362 · L1383-1387)
 ★ ①의 워밍업이 이 판단의 전제다 — 모듈 로드 대기를 미리 치워 놓아야
   "한 태스크면 충분" 이 성립한다
 ★ 스트림도 **일부러 닫지 않는다** — createUnclosingPrefetchStream (L312-313 주석
   "Use a stream that never closes so pending references (dynamic holes) can't error
    the decode.")
```

```text
 ★★ ④ React **컴포넌트**를 부작용 운반용으로 쓴다 (L386-389)

   // RootTreePrefetch is not a valid return type for a React component, but
   // we need to use a component so that when we decode the original stream
   // inside of it, the side effects are transferred to the new stream.
   // @ts-expect-error
   <PrefetchTreeData ... segmentTasks={segmentTasks} ... />

 => 원래 스트림을 **컴포넌트 안에서** 디코드해야 그 부작용(클라이언트 참조 등)이
    새 스트림으로 옮겨진다
 => 반환형이 컴포넌트로 맞지 않아 `@ts-expect-error` 로 타입 검사를 **일부러 끈다**
 ★ PrefetchTreeData 는 트리를 돌며 세그먼트마다 renderSegmentPrefetch 작업을
   `segmentTasks` 배열에 **밀어 넣는다**. 트리 렌더가 끝난 뒤 L445 Promise.all 로 모은다
```

```text
 ② 두 단계 디코드 — 셸 경계를 재기 위해 (주석 L331-343)

 L344  release = createPromiseWithResolvers<boolean>()
 셸 경계(`a`)가 숫자면
   먼저 셸 바이트까지만 넣고 → release 를 기다렸다가 → 나머지를 넣는다
   (스트림은 역시 닫지 않는다)
 셸 경계가 없으면
   한 번에 넣고 release 를 바로 푼다 (`a === null` 이면 true)

 => 세그먼트마다 **자기 셸이 어디서 끝나는지**를 잰다. 페이지의 셸 경계 순간에 멈춰 두고
    각 세그먼트 렌더가 거기까지 흘린 바이트를 센다
 ★ finally(L424-433)에서 **실패해도** release 를 푼다 — 주석 "so a tree-render error can't
   strand the spawned tasks on a release that never comes". 그런데 바로 아래 TODO 가
   "I don't think it's really necessary to unblock the spawned tasks" 라고 적는다
```

## 결과가 쓰이는 곳

```text
 metadata.segmentData (Map)
      --> prerender 결과에 실려 빌드 산출물·ISR 캐시로 저장된다

 '/_tree'
      --> [프리페치]의 라우트 트리 프리페치 응답 (NEXT_ROUTER_SEGMENT_PREFETCH_HEADER: '/_tree')

 세그먼트 키마다의 Buffer
      --> [프리페치]의 세그먼트 요청 응답. 클라이언트가 세그먼트 캐시에 넣는다

 needsRuntimeRequest (`u` 약속, 없으면 L327 의 값)
      --> **세그먼트 응답마다** 실린다 (L997-998 → L1029 · L1048 · L1349).
          트리 프리페치(`{tree, staleTime, buildId}`, L1062-1068)에는 **없다.**
          클라이언트가 런타임 프리페치를 시도할지 판단하는 근거 ([프리페치]의 PPRRuntime)
```

## 다루지 않는 것

`PrefetchTreeData`(L931-1069)의 트리 순회 본문과 `TreePrefetch` · `SegmentPrefetchResponse` 타입의 필드, `renderSegmentPrefetch`(L1273-1445)가 세그먼트 하나를 렌더하고 셸 경계를 재는 방식, `collectSegmentDataImpl`(L1071), `collectPrefetchHints`(L493-889)와 prefetch inlining, `createUniformHintTree`(L898), gzip 크기 측정(L923), `readRuntimeDataAccessed`(L1462)의 해석, `waitAtLeastOneReactRenderTask` 의 구현, `onSegmentPrerenderError`(L229)가 무시하는 오류의 종류, app-render 쪽 감싸는 함수(L10417-10579)가 힌트·매니페스트를 준비하는 부분, 빌드가 이 Map 을 파일로 쓰는 쪽은 이 문서의 범위 밖이다.
