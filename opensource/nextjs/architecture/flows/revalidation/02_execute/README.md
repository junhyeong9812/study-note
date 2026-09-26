# 02 실행

상위: [재검증이 쌓이고 실행되기까지](../README.md)

`executeRevalidates` 는 36줄이다. 쌓인 **세 통**을 모아 `Promise.all` 한다. 그 앞에 `withExecuteRevalidates` 라는 다른 진입점도 있는데, **새로 생긴 것만** 골라 돌린다.

## 위치

`packages/next` / `src/server` / `revalidation-utils.ts` L186-L221 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/revalidation-utils.ts#L186-L221))

`packages/next` / `src/server` / `revalidation-utils.ts` L6-L26 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/revalidation-utils.ts#L6-L26))

## 실제 코드

함수 전체가 이것이다.

```ts
// revalidation-utils.ts L186-L221
export function executeRevalidates(
  workStore: WorkStore,
  state?: RevalidationState
): false | Promise<void> {
  const promises: Promise<unknown>[] = []

  const pendingRevalidatedTags =
    state?.pendingRevalidatedTags ?? workStore.pendingRevalidatedTags ?? []

  if (pendingRevalidatedTags.length > 0) {
    promises.push(
      revalidateTags(
        pendingRevalidatedTags,
        workStore.incrementalCache,
        workStore
      )
    )
  }

  const pendingRevalidates = Object.values(
    state?.pendingRevalidates ?? workStore.pendingRevalidates ?? {}
  )

  promises.push(...pendingRevalidates)

  const pendingRevalidateWrites =
    state?.pendingRevalidateWrites ?? workStore.pendingRevalidateWrites ?? []

  promises.push(...pendingRevalidateWrites)

  if (promises.length === 0) {
    return false
  }

  return Promise.all(promises).then(() => undefined)
}
```

```text
 ★★ 통이 셋이다

 pendingRevalidatedTags   [01]이 쌓은 {tag, profile, revalidatedAt} 들
                          -> revalidateTags(...) 로 한 번에 넘긴다 (L197)
 pendingRevalidates       이미 Promise 인 것들 (Object.values 로 꺼낸다)
 pendingRevalidateWrites  이미 Promise 인 것들

 => 앞의 하나만 함수를 부르고, 뒤의 둘은 **이미 돌고 있는 약속**을 모은다
 ★ 할 일이 없으면 `false` 를 돌려준다 (L216-218).
   그래서 호출부가 `if (maybeRevalidatesPromise !== false)` 로 분기한다
   ([App Router] L2849 · L3072)
```

## 동작 흐름

```text
 executeRevalidates  REVUTIL L186-221

 L190  promises: Promise<unknown>[] = []
 L192  pendingRevalidatedTags = state?.… ?? workStore.… ?? []
 L195  비어 있지 않으면
 L196    promises.push(revalidateTags(pendingRevalidatedTags, workStore.incrementalCache, workStore))
 L205  pendingRevalidates = Object.values(state?.… ?? workStore.… ?? {})
 L209  promises.push(...pendingRevalidates)
 L211  pendingRevalidateWrites = state?.… ?? workStore.… ?? []
 L214  promises.push(...pendingRevalidateWrites)
 L216  promises 가 비었으면 => return false
 L220  => return Promise.all(promises).then(() => undefined)

 ★ `state` 인자가 있으면 workStore 대신 그것을 본다.
   그 인자를 주는 것이 아래 withExecuteRevalidates 다
```

```text
 withExecuteRevalidates  REVUTIL L6-26 — **새로 생긴 것만** 돌린다
   JSDoc L5 - "Run a callback, and execute any *new* revalidations added during its runtime."

 L6   withExecuteRevalidates(store, callback)
 L10    store 가 없으면 => return callback()
 L15    savedRevalidationState = cloneRevalidationState(store)
 L16    try { return await callback() }
 L18    finally {
 L20      newRevalidates = diffRevalidationState(saved, cloneRevalidationState(store))
 L24      await executeRevalidates(store, newRevalidates)
        }

 주석 L13-14
   "If we executed any revalidates during the request, then we don't want to execute
    them again. save the state so we can check if anything changed after we're done
    running callbacks."
 => 콜백 **전후를 비교**해 그 사이 늘어난 것만 실행한다.
    같은 요청에서 두 번 실행되는 것을 막는다
 ★ finally 라서 콜백이 던져도 새 재검증은 실행된다
```

```ts
// revalidation-utils.ts L6-L26
export async function withExecuteRevalidates<T>(
  store: WorkStore | undefined,
  callback: () => Promise<T>
): Promise<T> {
  if (!store) {
    return callback()
  }
  // If we executed any revalidates during the request, then we don't want to execute them again.
  // save the state so we can check if anything changed after we're done running callbacks.
  const savedRevalidationState = cloneRevalidationState(store)
  try {
    return await callback()
  } finally {
    // Check if we have any new revalidates, and if so, wait until they are all resolved.
    const newRevalidates = diffRevalidationState(
      savedRevalidationState,
      cloneRevalidationState(store)
    )
    await executeRevalidates(store, newRevalidates)
  }
}
```

```text
 ★★ diff 를 태그 이름만으로 하지 않는다 (L47-78)

 L51  prevTagsWithProfile = new Set(prev.pendingRevalidatedTags.map((item) => {
 L53    profileKey = typeof item.profile === 'object'
                      ? JSON.stringify(item.profile)
                      : item.profile || ''
 L57    return `${item.tag}:${profileKey}`
      }))

 => 키가 `태그:프로필` 이다. **같은 태그를 다른 프로필로 재검증하면 다른 것**으로 센다
 ★★ 다만 [01]의 중복 합치기(REVAL L219-226)와 **규칙이 다르다**
     여기(diff)  `item.profile || ''` 이므로 undefined 와 '' 가 **같은 키**가 된다
     거기(dedup) typeof 기반 `===` 이므로 그 둘을 **구분한다**
```

```text
 revalidateTags  REVUTIL L80-184 — 프로필별로 묶어서 핸들러에 넘긴다

 L88   비어 있으면 return
 L92   handlers = getCacheHandlers()
 L96   tagsByProfile = new Map<프로필, 태그[]>()
 L103  각 항목에 대해
 L107    이미 있는 프로필 키를 **값 비교**로 찾는다
 L109      둘 다 문자열이면 ===
 L116      둘 다 객체면 (JSON 비교로 이어진다)
 ...   (L130-184)

 => 프로필이 같은 태그들을 한 묶음으로 만들어 **배치로** 처리한다
    주석 L95 - "Group tags by profile for batch processing"
 ★ Map 의 키가 객체일 수 있어서 `Map.get` 을 못 쓴다.
   그래서 L107 의 선형 탐색이 있다

 ★★ 접어 둔 L130-184 에 계약 수준인 것이 넷 있다
   L154  문자열 profile 이 store.cacheLifeProfiles 에 없으면 **throw**
         => executeRevalidates 가 돌려준 Promise 의 reject 가 여기서 난다
   L161  핸들러에 넘기는 durations 는 `{expire}` **하나뿐**.
         profile 의 stale·revalidate 는 버려진다
   L167  profile 이 없으면 updateTags(tags) 를 **인자 하나로** 불러 즉시 만료시킨다
   L172  `handler.updateTags?.(...)` — 그 메서드가 없는 핸들러면 undefined 가 섞인다
```

## 결과가 쓰이는 곳

```text
 반환한 false | Promise<void>
      --> 호출처 다섯
            app-render.tsx L2848 · L3071
            action-handler.ts L1246 (skipPageRendering 이면) · L1433 (에러 경로)
            route-modules/app-route/module.ts L397
          => 호출부가 이것을 waitUntil 에 넘기거나 await 한다

 revalidateTags 가 보내는 곳이 **둘**이다
      --> handler.updateTags?.(...)                     REVUTIL L170-176
      --> incrementalCache.revalidateTag(tags, durations)  REVUTIL L178-180
      ★ `?.` 라서 updateTags 가 없는 핸들러면 promises 에 undefined 가 들어간다

 (반환 없음 — Promise<void>)
      --> Promise.all 이라 하나만 reject 해도 전체가 reject 한다.
          실제 reject 원인 하나는 REVUTIL L154 의 "모르는 프로필" throw 다
```

## 다루지 않는 것

`revalidateTags`(L80-184)의 L130-184 본문과 프로필별 배치 처리의 세부, `getCacheHandlers`(`use-cache/handlers.ts` 352줄)가 돌려주는 핸들러의 종류와 `expireTags` 류 메서드, `IncrementalCache` 가 태그로 항목을 찾아 무효화하는 방식, `pendingRevalidates` / `pendingRevalidateWrites` 에 Promise 를 넣는 쪽(패치된 `fetch` 등), `cloneRevalidationState`(L35) / `diffRevalidationState`(L47)의 L58 이후 본문, `withExecuteRevalidates` 를 부르는 곳, `Promise.all` 이 하나라도 reject 했을 때의 전파 경로는 이 문서의 범위 밖이다.
