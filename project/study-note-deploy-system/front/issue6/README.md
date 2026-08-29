# issue6 — features 재편 + 3탭 고정 + 미사용 라우트 제거

- 이슈 #10 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/11

## 1. 배경 (사용자 결정 3개를 한 번에)

① app/은 **순수 라우팅만** — 참조 프로젝트(squatting front-server)와 동형으로
② 코테 서머리는 "의도된 부재"가 아니라 **추후 문제 분석으로 작성 예정** → 3탭 고정
③ 검색은 /search SSR만 쓰니 /api/search BFF 라우트는 미사용 → 제거

## 2. 구조 비교

```
[기존]                         [재편 (선택)]
src/app/  ← 페이지에 로직 혼재   src/app/        ← 라우팅만: 데이터 로드 → View 위임
src/components/ ← 전부 한 폴더   src/features/{home,wiki,search,sync,deploy}/{ui,lib}
src/lib/                        src/shared/{api,lib,ui}   ← 도메인 무소속만
```

페이지가 이렇게 얇아진다:

```tsx
// app/page.tsx — 이게 전부
export default async function HomePage() {
  const treeData = await backendGet<TreeData>("/api/tree", newRequestId());
  return <HomeView treeData={treeData} />;
}
```

### 3탭 고정 — 기각을 뒤집은 기록

리뷰가 "3탭 보장"을 지적했을 때 "코테는 2-summary가 의도된 부재"라며 기각했었다.
사용자 확정으로 근거가 무너짐 — 서머리는 쓸 예정이었다. 재채택:

```tsx
CHAPTER_KINDS.map((kind) => {
  const doc = docsByKind.get(kind);
  return doc ? <Markdown ... /> 
             : <p>아직 작성 전 — push하면 이 탭에 나타난다.</p>;
})
```

## 3. 구현 중 마주친 문제

### 이동 후 상대 임포트 잔재 — 빌드가 하나씩 알려줌

`git mv` 후 `@/lib/...` 치환을 일괄로 돌렸지만 **파일 내부의 상대 임포트**
(`from "./logger"`, `from "./backend"`)는 치환 대상 문자열이 아니라서 남았다:

```
Module not found: Can't resolve './logger'     (shared/api/backend.ts — logger가 다른 폴더로 감)
Type error: Cannot find module './backend'     (features/wiki/lib/tree.ts)
```

빌드가 한 개씩만 알려줘서 고치고-빌드 3회. **교훈**: 파일 이동 리팩토링의 치환은
절대 경로 임포트만 보면 안 되고 `from "\./` 패턴(상대 임포트)을 먼저 전수 grep해야
한 번에 끝난다.

## 4. 결론

app 얇아짐·feature 응집·3탭 고정·표면 축소. vitest 6·엣지 200. PR: #11
