# issue1 — 스캐폴드: BFF의 뼈대를 세우고 "엣지 재활용" 가정을 실증하다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-front
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/2

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "봉투 해제를 한 곳에서"          ──▶      왜 페이지마다 검사하면 안 되는가,
>  결론만 제시                              무엇을 고민해 헬퍼 하나로 몰았나
> "가정을 실증했다"               ──▶      그 가정이 틀렸다면 무슨 일이 나는가까지
> BFF·standalone 용어 던짐         ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```
> 표현도 순화했다: "명세에 박아뒀다" → "명세에 기록해놨다".

---

## 1. 배경 — front는 두 개의 얼굴을 가진다

> 용어 — BFF(Backend For Frontend): 브라우저와 진짜 백엔드 사이에 두는 "전용 중간
> 서버". 브라우저는 이 중간 서버하고만 이야기하고, 진짜 백엔드는 바깥에 노출되지 않는다.

front는 성격이 둘로 갈린다.

- **사용자에게는** 위키 화면이다 — 노트를 트리로 보여주고 검색하게 해주는 웹페이지.
- **시스템에게는** 유일한 외부 노출 지점(BFF)이다 — 바깥 인터넷에서 집 안 서버로 들어오는
  요청은 전부 front를 거친다.

브라우저는 backend 서버(집 안 .158)의 존재를 아예 모른다. 브라우저가 아는 주소는
front(.9의 11000 포트) 하나뿐이고, 화면을 그릴 데이터는 front가 서버 안에서(SSR) backend에
대신 물어봐서 채운다.

이 첫 이슈에는 **미리 검증해야 할 가정**이 하나 있었다. 이 서버가 서는 자리(오라클 클라우드의
nginx 설정 = `www.junproject.xyz` → 집:11000 포워딩)는 이전 프로젝트(local-llm) 때 이미
만들어둔 것이다. 가정은 이랬다: **그 nginx 설정·인증서·포워딩을 한 글자도 안 고치고
그대로 재활용할 수 있는가.** 이게 틀렸다면 이후 이슈 전부가 재설계 대상이 된다.

---

## 2. 검토한 방식들

### 결정 (1) — create-next-app을 쓰지 않고 손으로 스캐폴드했다

**무엇이 문제였나:** Next.js 프로젝트를 시작하는 공식 도구 `create-next-app`은 예제
페이지·svg 로고·폰트 설정 같은 걸 잔뜩 만들어준다. 그런데 그 대부분이 시작하자마자
바로 지울 파일이다.

**무엇을 고민했나:** 지울 걸 만들었다가 지우는 것보다, 실제로 필요한 것만 손으로 쓰는
편이 무엇이 왜 있는지 명확하다. 필요한 건 다섯 덩어리뿐이었다.

**그래서 이렇게:** 아래 파일만 직접 작성했다.

```
package.json      의존성 8개 (next·react·react-markdown·remark-gfm·rehype-highlight·ioredis 등)
next.config.mjs   output: 'standalone'   ← 도커 이미지에 node_modules 전체 대신 필요분만 담기
tsconfig.json     paths: {"@/*": ["./src/*"]}   ← 절대경로 임포트의 뿌리
src/lib/          backend.ts(봉투 해제) · logger.ts(로그 규약)
src/app/          layout.tsx · page.tsx (홈)
```

> 용어 — standalone 출력: Next가 배포용으로 "필요한 파일만 추린 최소 묶음"을 만들어주는
> 모드. 도커 이미지에 무거운 `node_modules` 전체를 넣지 않아 이미지가 가벼워진다.

`next.config.mjs`는 이게 전부다 — `src/app` 밑이 아니라 리포 루트, 파일 경로 `next.config.mjs`:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',          // 도커 이미지 최소화
};
export default nextConfig;
```

### 결정 (2) — 봉투 해제를 페이지마다 하지 않고 헬퍼 하나로 강제했다

**무엇이 문제였나:** backend의 모든 응답은 `{success, data|error}`라는 **봉투(envelope)**로
싸여 온다. 즉 실제 데이터를 꺼내려면 매번 `success`가 참인지 먼저 검사하고, 참이면 `data`를,
거짓이면 `error`를 꺼내야 한다. 이걸 페이지마다 되풀이하면 어느 한 페이지에서 검사를
빠뜨리는 순간, 오류 응답을 정상 데이터인 척 화면에 그리게 된다.

**무엇을 고민했나:** 검사를 "잊을 수 없게" 만들 방법. 페이지가 backend를 부를 때 반드시
거쳐야 하는 창구를 하나 두고, 그 창구 안에서만 봉투를 열게 하면, 페이지는 봉투의 존재조차
몰라도 된다.

**그래서 이렇게:** `src/lib/backend.ts`에 `backendGet` 헬퍼 하나를 두고, 페이지는 항상
이걸로만 부른다. 파일 경로 `src/lib/backend.ts`:

```ts
/** 봉투를 해제해 data를 반환. success=false·비봉투·네트워크 오류는 BackendError로 정규화 */
export async function backendGet<T>(path: string, requestId: string): Promise<T> {
  const startedAt = Date.now();
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      headers: { "X-Request-Id": requestId },
      cache: "no-store",                       // 콘텐츠 최신성은 backend 캐시(트리)가 담당
      signal: AbortSignal.timeout(10_000),
    });
  } catch (error) {
    await log(requestId, `backend unreachable ${path}: ${String(error).slice(0, 120)}`, "error");
    throw new BackendError("backend_unreachable", 503);
  }
  const body = await response.json().catch(() => null);
  if (!body || typeof body.success !== "boolean") {        // 봉투가 아니면 거절
    await log(requestId, `backend non-envelope ${path} status=${response.status}`, "error");
    throw new BackendError("invalid_envelope", response.status);
  }
  if (!body.success) {                                     // 오류 봉투면 예외로 정규화
    await log(requestId, `backend error ${path}: ${body.error?.code}`, "warning");
    throw new BackendError(body.error?.code ?? "unknown", response.status, body.error?.detail);
  }
  await log(requestId, `${path.split("?")[0]} ok ${Date.now() - startedAt}ms`);
  return body.data as T;                                   // 페이지는 data만 본다
}
```

페이지 쪽 코드는 이렇게 깔끔해진다 — 봉투를 신경 쓰지 않는다. 파일 경로 `src/app/page.tsx`:

```tsx
export default async function HomePage() {
  const requestId = newRequestId();
  const treeData = await backendGet<TreeData>("/api/tree", requestId);   // data만 돌려받는다
  const buckets = treeData.tree.children;
  ...
}
```

### 결정 (3) — requestId 규약이 여기서 한 번 진화했다

> 용어 — requestId: 요청 하나마다 붙이는 추적용 꼬리표. 여러 서버 로그에 같은 id가 찍히면
> "이 로그들은 같은 요청이 만든 것"임을 나중에 꿰어 볼 수 있다.

**무엇이 문제였나:** 원래 규약은 "backend가 requestId를 발행한다"였다. 그런데 이제 요청의
**진입점이 front**로 바뀌었다 — 바깥에서 들어오는 첫 서버가 front다.

**무엇을 고민했나:** 꼬리표는 "요청이 처음 도착한 곳"에서 붙어야 그 뒤 모든 구간을 한
id로 꿸 수 있다. 진입점이 front라면 발행 주체도 front여야 한다.

**그래서 이렇게:** 규약을 v2로 갱신했다 — **진입 서버(front)가 발행 → `X-Request-Id`
헤더로 backend에 전파.** backend는 받은 id를 검증(형식이 틀리면 재발행 — acceptOrIssue)해서
그대로 쓴다. 위 `backendGet` 코드에서 `headers: { "X-Request-Id": requestId }`가 그 전파다.

로그는 `requestId:서버이름:메시지` 한 줄 형식이고, stdout과 Redis 스트림 양쪽에 남긴다.
중요한 건 **로그가 요청을 인질로 잡지 않게** 만든 것 — Redis가 죽어도 요청은 정상 진행한다.
파일 경로 `src/lib/logger.ts`:

```ts
  } catch {
    disabledUntil = Date.now() + BACKOFF_MS;   // 로그가 요청을 인질로 잡지 않는다
  }
```

---

## 3. 워크플로우 — 요청 한 건이 지나는 길

```
브라우저 ──HTTPS──▶ 오라클 nginx (www.junproject.xyz conf — 무수정 재활용) ──▶ .9:11000 front
                                                                                │ SSR: backendGet
                                                                                ▼ (집 안 LAN)
                                                                          .158:8090 backend
```

핵심은 "브라우저는 front까지만, backend는 LAN 안에서만"이다. 바깥에서 backend로 가는
직통로가 없다.

---

## 4. 실증 — 가정이 맞았나

배포 직후, 가장 먼저 확인한 것은 **엣지(오라클 nginx)를 통한 실호출**이다. 이 순서가
의도적이다 — 가정(nginx 설정 재활용)이 틀렸다면 나머지를 볼 이유가 없다.

```
$ curl -o /dev/null -w "edge:%{http_code} %{time_total}s" https://www.junproject.xyz/
edge:200 0.157142s
```

**오라클 nginx 설정·인증서·포워딩을 한 글자도 안 고치고 재활용하는 데 성공했다(200, 157ms).**
이어서 홈 화면 SSR도 즉시 검증됐다.

```
공부 노트 위키 · 커밋 4979164f
cs 주제 163개 · practice 주제 47개 · project 주제 14개 ...
```

front가 남긴 로그가 규약 포맷 그대로 backend의 Redis 로그 스트림에 합류한 것도 확인했다.

```
req-19df1abbb201:front:/api/tree ok 25ms
```

---

## 5. 구현 중 마주친 문제

이 이슈에서는 없었다. 대신 **배포 순서를 "가정 실증(엣지 200)이 가장 먼저 나오도록"
설계한 것**이 요점이다. 가정이 틀렸다면 이후 이슈 전부가 재설계였을 것이므로, 가장 위험한
가정을 맨 앞에서 깨뜨려 보는 순서를 택했다.

---

## 6. 결론

BFF 뼈대 + 봉투 해제 단일 창구(`backendGet`) + requestId 규약 v2(진입 서버 발행) +
**엣지 재활용 실증(200, 157ms)**. 가장 위험한 가정을 첫 커밋에서 통과시켜, 이후 이슈들이
안심하고 이 뼈대 위에 쌓일 수 있게 됐다. PR: #2
