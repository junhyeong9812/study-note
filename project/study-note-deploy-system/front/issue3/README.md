# issue3 — 검색 화면: 시스템의 "성능 저하 모드"를 사용자에게도 보여준다

- 이슈 #5 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/6

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "봉투 그대로 중계"              ──▶      왜 프록시는 봉투를 열면 안 되나(서사)
>  결론만                                  → 무엇을 고민했나 → 그래서 이렇게
> "조용한 성공" 문제              ──▶      실제 에러 로그 + [기존]↔[변경] 진단 흐름
> 폴백·allowlist 용어 던짐         ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 검색은 "잘 되는 척"을 하면 안 된다

헤더에 상시 검색바를 두고(인터뷰 결정), 입력하면 `/search?q=` 결과 페이지로 간다.
브라우저는 backend를 직접 못 보므로, 그 사이를 잇는 `/api/search` BFF 프록시도 필요하다.

> 용어 — 프록시(proxy): 요청을 대신 받아 뒤 서버에 그대로 전달하고, 그 응답을 다시
> 그대로 돌려주는 중계 서버. 여기선 front가 브라우저의 검색 요청을 backend에 넘긴다.

backend 검색에는 특징이 있다 — llm(질의 확장)이나 임베딩(의미 검색)이 죽어도, 폴백으로
어쨌든 결과를 낸다.

> 용어 — 폴백(fallback): 원래 쓰려던 고급 기능이 실패했을 때 대신 돌리는 대비책. 여기선
> "질의 확장/의미 검색이 안 되면 단순 키워드 검색으로라도 답한다"를 뜻한다.

문제는, 폴백이 조용히 일어나면 사용자는 "지금 검색이 성능 저하 모드"임을 모른다는 것이다.
그래서 이걸 **화면에도 드러내기로** 했다 — "질의 확장 생략(폴백)" / "의미 검색 생략(폴백)"
뱃지를 붙여, 시스템이 지금 어떤 모드인지 사용자가 볼 수 있게 했다.

---

## 2. 검토한 방식들

### 결정 (1) — 프록시는 봉투를 "해제하지 않고" 그대로 중계한다

**무엇이 문제였나:** issue1에서 `backendGet` 헬퍼는 봉투를 열어 `data`만 돌려줬다. 그럼
검색 프록시도 봉투를 열어서 돌려줘야 할까?

**무엇을 고민했나:** 프록시가 봉투를 열었다가 다시 포장하면, 그 과정에서 오류 코드나
HTTP 상태가 한 단계 뭉개진다(예: backend가 준 422가 프록시에서 500으로 바뀌는 식). 반면
SSR로 화면을 그리는 페이지는 봉투를 열어 써야 한다. 즉 **용도가 다르다** — 페이지는 해제,
프록시는 원형 전달.

**그래서 이렇게:** `/search` 결과 페이지는 `backendGet`으로 해제해 쓰고, `/api/search`
프록시는 봉투도 status도 손대지 않고 그대로 중계했다. 파일 경로 `src/app/api/search/route.ts`:

```ts
try {
  const response = await fetch(`${BACKEND_URL}/api/search?${upstream}`, {
    headers: { "X-Request-Id": requestId },
    signal: AbortSignal.timeout(15_000),
  });
  const body = await response.json();
  await log(requestId, `search proxy q=${(search.get("q") ?? "").slice(0, 40)} -> ${response.status}`);
  return NextResponse.json(body, { status: response.status });   // 봉투·status 그대로
}
```

```
[페이지 /search (SSR)]  backendGet → 봉투 해제 → data로 화면 그림
[프록시 /api/search]    fetch → 봉투 손대지 않음 → status 그대로 반환
```

### 결정 (2) — 쿼리 파라미터를 allowlist로 거른다

> 용어 — allowlist: "허용 목록". 들어온 값 중 미리 정한 것만 통과시키고 나머지는 버리는
> 방식. 반대는 "차단 목록(denylist)".

**무엇이 문제였나:** 브라우저가 보낸 쿼리 문자열을 그대로 backend URL에 이어붙이면, 예상치
못한 파라미터까지 backend로 흘러 들어간다(파라미터 주입 면적이 넓어진다).

**무엇을 고민했나:** 넘겨야 할 파라미터는 사실 정해져 있다 — `q`, `topic`, `size`,
그리고 복수 허용인 `doc_kind`. 그 밖은 넘길 이유가 없다.

**그래서 이렇게:** 정해둔 키만 골라 새 쿼리를 다시 만들었다. 파일 경로
`src/app/api/search/route.ts`:

```ts
const upstream = new URLSearchParams();
for (const key of ["q", "topic", "size"]) {              // 이 셋만 단수 전달
  const value = search.get(key);
  if (value) upstream.set(key, value);
}
for (const kind of search.getAll("doc_kind")) upstream.append("doc_kind", kind);   // 복수 허용
```

브라우저 입력을 upstream에 그대로 잇지 않고, 통과할 것만 새로 조립한다.

---

## 3. 실증

```
$ curl "/search?q=kafka가 빠른 이유"     뱃지: ['질의 확장 사용', '의미 검색 사용']  kafka-why-fast 히트
$ curl "/api/search?q=lsm"              {"success":true,...,"path":"cs/systems/lsm-tree/3-answer.md"...
edge-search:200
```

뱃지가 폴백 여부를 그대로 드러내고(위 예는 둘 다 정상 모드), 프록시는 봉투 원형을
반환한다. 엣지를 통한 검색도 200.

---

## 4. 구현 중 마주친 문제

### 파일을 "썼다고 생각했는데" 빌드가 조용히 성공했다

**증상:** route 파일을 만드는 명령이 실제로는 실패해 있었는데, 빌드는 성공으로 나왔다.

```
/bin/bash: 줄 136: src/app/api/search/route.ts: 그런 파일이나 디렉터리가 없습니다
...
 ✓ Compiled successfully in 17.6s          ← 그런데 빌드는 성공
├ ƒ /search   630 B   107 kB               ← 그런데 /api/search 행이 없다
```

**진단:** 두 가지가 겹쳤다.

```
[무엇이 일어났나]
브랜치를 새로 checkout  ──▶  빈 디렉토리 src/app/api 가 사라짐
                              (git은 빈 디렉토리를 추적하지 않는다)
파일 리다이렉션 `> 경로`  ──▶  없는 디렉토리는 만들어주지 않음 → 쓰기 실패
Next 빌드                 ──▶  "없는 라우트"를 오류로 보지 않음 → 통과
                              결과: 파일이 안 생겼는데 빌드는 초록불
```

> 용어 — 리다이렉션(`> 경로`): 셸에서 명령 출력을 파일로 보내는 것. 대상 디렉토리가
> 없으면 파일을 만들지 못하고 그냥 실패한다.

**수정:**

```
[기존]  > src/app/api/search/route.ts        (디렉토리 없음 → 실패, 그래도 빌드 초록)
[변경]  mkdir -p src/app/api/search           (디렉토리 먼저 만들고)
        > src/app/api/search/route.ts        (그다음 쓰기)
        + 빌드 출력에서 grep "api/search"      (라우트 표에 정말 있는지 확인)
```

빌드 출력의 **라우트 목록에 기대한 경로가 있는지**를 확인 항목으로 삼았다.

**배경:** 실패가 조용한 조합(리다이렉션 실패 + 관대한 빌드)에서는 "성공 로그"가 아니라
**산출물 목록**을 봐야 한다. Next 빌드 출력의 라우트 표가 바로 그 산출물 목록이다.

---

## 5. 결론

검색바 → 결과 페이지(위키 링크·스니펫·종류) + 폴백 가시화(뱃지). 프록시는 봉투 원형
중계 + 파라미터 allowlist. 그리고 "조용한 실패"를 산출물 목록으로 잡는 확인 습관을 얻었다.
PR: #6
