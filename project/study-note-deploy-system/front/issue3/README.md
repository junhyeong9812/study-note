# issue3 — 검색 화면: 폴백을 사용자에게도 보여준다

- 이슈 #5 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/6

## 1. 배경

헤더 상시 검색바(인터뷰 결정) → `/search?q=` 결과 페이지. 브라우저가 backend를 직접
못 보므로 `/api/search` BFF 프록시도 필요하다. backend 검색의 특징 — llm·임베딩이
죽어도 폴백으로 응답한다 — 를 **화면에도 드러내기로 했다**: "질의 확장 생략(폴백)"
"의미 검색 생략(폴백)" 뱃지. 시스템이 성능 저하 모드임을 사용자가 알 수 있게.

## 2. 검토한 방식들

### 선택 — 프록시는 봉투를 "해제하지 않고" 그대로 중계

```ts
// /api/search route handler — 봉투 그대로, status 그대로
const response = await fetch(`${BACKEND_URL}/api/search?${upstream}`, {
  headers: { "X-Request-Id": requestId } });
return NextResponse.json(await response.json(), { status: response.status });
```

페이지(SSR)는 `backendGet`으로 해제해 쓰고, 프록시는 원형 전달 — 프록시가 봉투를
해제·재포장하면 오류 코드가 한 단계 뭉개진다.

### 선택 — 쿼리 파라미터 allowlist

```ts
for (const key of ["q", "topic", "size"]) { ... }        // 이 셋만 전달
for (const kind of search.getAll("doc_kind")) ...        // 복수 허용
```
브라우저 입력을 그대로 upstream에 잇지 않는다 — 파라미터 주입 면적 축소.

## 3. 실증

```
$ curl "/search?q=kafka가 빠른 이유"     뱃지: ['질의 확장 사용', '의미 검색 사용']  kafka-why-fast 히트
$ curl "/api/search?q=lsm"              {"success":true,...,"path":"cs/systems/lsm-tree/3-answer.md"...
edge-search:200
```

## 4. 구현 중 마주친 문제

### 파일을 "썼다고 생각했는데" 빌드가 조용히 성공

**증상**: route 파일 생성 명령이 실패해 있었다:

```
/bin/bash: 줄 136: src/app/api/search/route.ts: 그런 파일이나 디렉터리가 없습니다
...
 ✓ Compiled successfully in 17.6s          ← 그런데 빌드는 성공
├ ƒ /search   630 B   107 kB               ← /api/search 행이 없다
```

**진단**: 브랜치를 새로 checkout하면서 빈 디렉토리(`src/app/api`)가 사라졌다 — git은
**빈 디렉토리를 추적하지 않는다.** 파일 리다이렉션(`> 경로`)은 디렉토리를 만들어주지
않으니 쓰기가 실패했고, Next는 "없는 라우트"를 오류로 보지 않으니 빌드가 통과했다.

**수정**: `mkdir -p src/app/api/search` 후 재작성. 그리고 빌드 출력에서 **라우트 목록에
기대한 경로가 있는지**를 확인 항목으로 삼음(`grep "api/search"`).

**배경**: 실패가 조용한 조합(리다이렉션 실패 + 관대한 빌드)에서는 "성공 로그"가 아니라
**산출물 목록**을 봐야 한다. Next 빌드 출력의 라우트 표가 그 산출물 목록이다.

## 5. 결론

검색바 → 결과(위키 링크·스니펫·종류) + 폴백 가시화. 프록시는 봉투 원형 중계 + allowlist. PR: #6
