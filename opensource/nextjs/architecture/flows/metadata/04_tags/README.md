# 04 태그로 내보낸다

상위: [메타데이터가 `<head>` 가 되기까지](../README.md)

[03]이 만든 객체 하나를 React 엘리먼트 배열로 바꾼다. 메타데이터 쪽은 `createMetadataElements` **함수 하나가 1555줄**(L359-1913)이다. 추상화 없이 필드마다 `if` 와 `tags.push` 를 늘어놓는다. 끝에 붙는 아이콘 표지 하나가 스트림 변환까지 이어진다.

## 위치

`packages/next` / `src/lib/metadata` / `metadata.tsx` L283-L1913 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/lib/metadata/metadata.tsx#L283-L1913))

## 실제 코드

아이콘 태그 뒤에 붙는 표지다. **서버에서만** 그려진다.

```tsx
// icon-mark.tsx L1-L14
'use client'

// This is a client component that only renders during SSR,
// but will be replaced during streaming with an icon insertion script tag.
// We don't want it to be presented anywhere so it's only visible during streaming,
// right after the icon meta tags so that browser can pick it up as soon as it's rendered.
// Note: we don't just emit the script here because we only need the script if it's not in the head,
// and we need it to be hoistable alongside the other metadata but sync scripts are not hoistable.
export const IconMark = () => {
  if (typeof window !== 'undefined') {
    return null
  }
  return <meta name="«nxt-icon»" />
}
```

```text
 ★★★ 아이콘 `<link>` 를 head 로 되돌리는 장치의 절반이다

 주석 L3-8
   "This is a client component that only renders during SSR, but will be replaced
    during streaming with an icon insertion script tag. ...
    Note: we don't just emit the script here because we only need the script if
    it's not in the head, and we need it to be hoistable alongside the other
    metadata but sync scripts are not hoistable."

 => 스크립트를 직접 내면 안 되는 이유가 둘이다
    ① 아이콘이 이미 head 에 있으면 스크립트가 필요 없다
    ② 동기 script 는 **hoist 되지 않는다** — 다른 메타데이터와 같이 head 로 못 올라간다
 => 그래서 hoist 되는 `<meta>` 로 자리만 표시하고, 스트림에서 바꾼다
 ★ `'use client'` 이고 `typeof window !== 'undefined'` 면 null — 브라우저에서는 **아무것도 안 그린다**
 ★ 이름 `«nxt-icon»` 의 겹화살괄호는 사용자가 쓸 리 없는 문자다 ※ (의도 추정)
```

## 동작 흐름

```text
 renderMetadata(...)  MDT L249
 L257  resolvedMetadata = await resolveMetadata(...)        [02][03]
 L265  return <>{createMetadataElements(resolvedMetadata)}</>
 renderViewport(...)  MDT L268 — 같은 모양, createViewportElements

 createViewportElements(viewport)   L287-353 — tags.push 5곳
 L293  <meta charSet="utf-8" />            ← **언제나 첫 태그**
 L297-320  width · height · initial-scale · minimum-scale · maximum-scale ·
           user-scalable(yes/no) · viewport-fit · interactive-widget 를 ', ' 로 잇는다
 L321  하나라도 있으면 <meta name="viewport" content=...>
 L327  themeColor 배열 → <meta name="theme-color" [media]>
 L346  colorScheme → <meta name="color-scheme">
 ★ charset 이 **viewport 쪽**에 있다. metadata 쪽이 아니다
```

```text
 createMetadataElements(metadata)   L359-1913 — 절 18개, tags.push 182곳
   (명령: `// --- ` 머리 줄 수 · `tags.push` 줄 수를 L359-1913 에서 셌다)

 L365  Title            <title> — `title.absolute` 가 **빈 문자열이 아닐 때만**
 L370  Basic meta       description · application-name
 L386  Authors          url 이 있으면 <link rel="author">, name 이 있으면 <meta name="author">
 L398  Manifest
 L415  (절 머리 없음)   generator · keywords · referrer · creator · publisher ·
                        robots · googlebot · abstract
 L444  Link rel arrays  archives · assets · bookmarks
 L461  Pagination       prev · next  (+ L473 category · classification)
 L482  Other            임의 name/content — 배열이면 여러 개, null·'' 는 건너뛴다
 L499  Alternates       canonical · hrefLang · media · type 별 <link rel="alternate">
 L581  iTunes · L593 Facebook · L611 Pinterest · L622 Format Detection
 L645  Verification     google · yahoo(y_key) · yandex · me · other
 L700  Apple Web App
 L742  Open Graph       **698줄**(L742-1439) — tags.push 90곳
 L1440 Twitter · L1598 App Links
 L1847 Icons            shortcut · icon · apple · other → <link>, hasIcon 이면 끝에 <IconMark/> (L1850-1852 · L1906-1908)
 L1912 return tags
```

```text
 ★★ 줄 수의 절반 가까이가 Open Graph 다

 L938  if ('type' in og) { const ogType = og.type; switch (ogType) …   (L938-940)
         case 12개 — website · article · book · profile ·
           music.song · music.album · music.playlist · music.radio_station ·
           video.movie · video.episode · video.tv_show · video.other
 L1433   default:
 L1434     const _exhaustiveCheck: never = ogType
 L1435     throw new Error(`Invalid OpenGraph type: ${_exhaustiveCheck}`)
 => 타입이 모든 경우를 덮었는지 **컴파일 시** 검사하고, 그래도 오면 런타임에 던진다
 ★ og:type 태그는 이 switch 안에서만 나온다 — `type` 이 없으면 og:type 이 없다
```

```text
 ★★ 필드마다 작은 규칙이 박혀 있다 (전부 이 함수 안)

 keywords          join(',') — 쉼표 뒤 공백 없음 (L420)
 formatDetection   값이 **false 인 키만** `telephone=no` 식으로 모은다 (L632-637).
                   true 는 아무 태그도 안 만든다
 appleWebApp       capable 이면 name="**mobile-web-app-capable**" (L706) —
                   `apple-` 접두사가 없다
 manifest          상대 URL(getOrigin 이 undefined)이고 VERCEL_ENV === 'preview' 면
                   crossOrigin="use-credentials" (L400-410)
 iTunes            `app-id=${appId}` 에 appArgument 가 있으면 `, app-argument=...` (L584-587)
 icons             rel 이 없으면 칸마다 기본값 — shortcut 'shortcut icon' · icon 'icon' ·
                   apple 'apple-touch-icon' · other 'icon' (L1860 · L1873 · L1886 · L1899)
```

```tsx
// create-server-inserted-metadata.tsx L3-L24
/**
 * For chromium based browsers (Chrome, Edge, etc.) and Safari,
 * icons need to stay under <head> to be picked up by the browser.
 *
 */
const REINSERT_ICON_SCRIPT = `\
document.querySelectorAll('body link[rel="icon"], body link[rel="apple-touch-icon"]').forEach(el => document.head.appendChild(el))`

export function createServerInsertedMetadata(nonce: string | undefined) {
  let inserted = false

  return async function getServerInsertedMetadata(): Promise<string> {
    if (inserted) {
      return ''
    }

    inserted = true
    return `<script${
      nonce ? ` nonce="${htmlEscapeAttributeString(nonce)}"` : ''
    }>${REINSERT_ICON_SCRIPT}</script>`
  }
}
```

```text
 ★★★ 표지를 **첫 청크의 `</head>` 위치로 판정**한다
     (server/stream-utils/node-web-streams-helper.ts L351 createMetadataTransformStream)

 표지 바이트 = `<meta name="«nxt-icon»"` 까지만 (encoded-tags.ts L23-30)
   주석 - "Only the match the prefix cause the suffix can be different wether it's
     xml compatible or not ">" or "/>"   (원문 그대로 — "wether" 도 원문이다)
   다음 바이트가 '/' 면 2바이트, 아니면 1바이트를 더 지운다 (L377-383)

 첫 청크에서 찾았고 `</head>` 보다 **앞**이면  => 표지만 지운다 (아이콘이 이미 head 에 있다)
 첫 청크에서 찾았고 `</head>` 보다 **뒤**면    => 표지 자리에 insert() 결과를 끼운다
 한 번 처리하면 isMarkRemoved = true — 이후 청크는 그대로 흘린다

 insert() = createServerInsertedMetadata(nonce) 가 만든 함수 (위 실제 코드)
   `inserted` 플래그로 **요청당 한 번만** 스크립트를 돌려준다
   document.querySelectorAll('body link[rel="icon"], body link[rel="apple-touch-icon"]')
     .forEach(el => document.head.appendChild(el))
   docstring L3-7 - "For chromium based browsers (Chrome, Edge, etc.) and Safari,
     icons need to stay under <head> to be picked up by the browser."

 => [01]의 스트리밍 갈래에서 Metadata 는 `<div hidden>` 안의 Suspense 뒤에 있다.
    늦게 풀리면 아이콘 `<link>` 가 body 쪽에서 나올 수 있고, 브라우저가 못 줍는다
 ※ "늦게 풀리면 body 로 간다" 는 React 의 hoist 동작에서 온 추론이다.
   소스가 적는 것은 셀렉터가 `body link[...]` 를 찾는다는 사실까지다
 ★ 옮기는 것은 rel="icon" · "apple-touch-icon" **둘뿐**이다. 'shortcut icon' 은 셀렉터에 없다
 ★ nonce 가 있으면 `nonce="..."` 를 붙인다 — CSP 를 쓰는 앱에서도 돈다
```

## 결과가 쓰이는 곳

```text
 React.ReactElement[] (태그 배열)
      --> <>...</> 로 감싸져 Metadata / Viewport 컴포넌트의 반환값이 된다 [01]
      --> [App Router]의 initialHead 를 거쳐 RSC 페이로드로 직렬화된다

 key={i++}
      --> 배열 안 순번이다. 필드가 빠지면 뒤의 key 가 당겨진다 ※ (재조정에 미치는 영향은 확인 안 함)

 <meta name="«nxt-icon»">
      --> [동적 응답] · [정적 응답]의 HTML 스트림 변환이 지우거나 스크립트로 바꾼다
          (stream-ops.node.ts L735 · L849, node-web-streams-helper.ts L956 외 넷)
```

## 다루지 않는 것

Open Graph 절의 이미지 · 비디오 · 오디오 하위 태그(L785-935)와 og type 별 태그(L938-1437)의 필드 하나하나, Twitter 절(L1440-1597)의 player · app 카드, App Links 절(L1598-1846)의 플랫폼 여덟 갈래, Alternates 의 `languages` · `media` · `types` 세 갈래의 세부, `getOrigin`(`generate/utils.ts` L17)의 판정, `createMetadataTransformStream` 의 첫 청크 이후 갈래(L424 이후)와 `indexOfUint8Array`, `ENCODED_TAGS` 의 다른 표지들, React 가 `<title>` · `<meta>` · `<link>` 를 head 로 올리는(hoist) 규칙 자체, `next-size-adjust` meta 와 `NonIndex` 는 이 문서의 범위 밖이다.
