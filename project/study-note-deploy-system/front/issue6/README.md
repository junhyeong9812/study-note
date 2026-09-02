# issue6 — features 재편 + 3탭 고정 + 미사용 라우트 제거

- 이슈 #10 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/11

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "app=순수 라우팅"               ──▶      왜 폴더 구조를 바꿨나(서사)
>  결정 3개 나열                            각 결정을 문제→고민→선택으로
> "빌드가 하나씩 알려줌"          ──▶      실제 에러 로그 + [기존]↔[변경] 구조도
> features·응집 용어 던짐          ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 사용자 결정 3개를 한 번에 반영

이 이슈는 사용자가 확정한 결정 세 개를 한꺼번에 반영한다.

1. `app/`은 **순수 라우팅만** 담게 한다 — 다른 프로젝트들과 같은 구조로.
2. 코테 정리 문서는 "의도된 부재"가 아니라 **추후 문제 분석으로 작성 예정** → 3탭 고정.
3. 검색은 `/search` SSR만 쓰므로, 안 쓰이는 `/api/search` BFF 라우트는 제거.

---

## 2. 결정 (1) — app은 라우팅만, 로직은 features로

**무엇이 문제였나:** 지금까지 페이지(`src/app/**`)에 데이터 로드·화면 조립·비즈니스
로직이 뒤섞여 있었다. 컴포넌트도 `src/components/` 한 폴더에 도메인 구분 없이 다 있었다.

**무엇을 고민했나:** 페이지가 "이 URL은 어떤 데이터를 어떤 화면에 넘긴다"만 담당하고,
실제 화면과 로직은 도메인별 폴더로 모으면(응집), 어디를 고쳐야 할지가 폴더 이름으로 드러난다.

> 용어 — 응집(cohesion): 관련된 코드를 한곳에 모으는 것. wiki 관련은 `features/wiki/`
> 안에 다 있게 하는 식.

**그래서 이렇게:** `app/`은 라우팅만 남기고, 도메인별 `features/<도메인>/{ui,lib}`와
도메인 무소속인 `shared/{api,lib,ui}`로 재편했다.

```
[기존]                              [재편 (변경)]
src/app/          ← 페이지에 로직 혼재   src/app/        ← 라우팅만: 데이터 로드 → View 위임
src/components/   ← 전부 한 폴더        src/features/{home,wiki,search,sync,deploy}/{ui,lib}
src/lib/                               src/shared/{api,lib,ui}   ← 도메인 무소속만
```

페이지가 이렇게 얇아진다. 파일 경로 `src/app/page.tsx`:

```tsx
// app/page.tsx — 이게 전부 (데이터 로드 → View 위임)
export default async function HomePage() {
  const treeData = await backendGet<TreeData>("/api/tree", newRequestId());
  return <HomeView treeData={treeData} />;
}
```

이 커밋에서 실제로 옮겨간 것(파일 이동 stat 발췌):

```
src/{components => features/wiki/ui}/Markdown.tsx
src/{components => features/wiki/ui}/Sidebar.tsx
src/{components => features/wiki/ui}/Tabs.tsx
src/{ => features/wiki}/lib/links.ts
src/{ => features/wiki}/lib/tree.ts
src/{lib => shared/api}/backend.ts
src/{ => shared}/lib/logger.ts
src/{components => shared/ui}/Header.tsx / SearchBar.tsx
```

---

## 3. 결정 (2) — 3탭 고정: 기각을 뒤집은 기록

**무엇이 문제였나:** issue5에서 리뷰가 "1/2/3 탭을 항상 3개로 보장하라"고 지적했을 때,
나는 "코테는 2-summary가 의도된 부재"라며 기각했었다.

**무엇을 고민했나:** 사용자 확정으로 그 기각의 근거가 무너졌다 — 코테 정리 문서는 쓸
예정이었다. 근거가 바뀌었으니 판정도 바뀌어야 한다. 없는 탭을 감추면, 사용자는 "이
주제엔 정리가 원래 없다"로 오해한다. 반대로 3탭을 항상 두고 없는 것을 "작성 전"으로
표시하면, "아직 안 썼다"가 드러난다.

**그래서 이렇게:** 3탭 고정 + "작성 전" 패널로 재채택했다. 파일 경로
`src/features/wiki/ui/WikiView.tsx`:

```tsx
/** 주제(리프) — 챕터면 1/2/3 3탭 고정: 없는 문서는 "작성 전" 패널.
 * (2026-08-28 결정: 코테 2-summary는 의도된 부재가 아니라 추후 문제 분석으로 작성 예정) */
<Tabs
  labels={CHAPTER_KINDS.map((kind) => KIND_LABEL[kind])}
  panels={CHAPTER_KINDS.map((kind) => {
    const doc = docsByKind.get(kind);
    return doc
      ? <Markdown key={kind} markdown={doc.markdown || "*아직 작성 전*"} docPath={doc.path} />
      : <p key={kind} style={{ color: "var(--muted)" }}>아직 작성 전 — push하면 이 탭에 나타난다.</p>;
  })}
/>
```

```
[기존]  탭 = 있는 문서만  →  코테는 [1·질문][3·정답]  (2·정리가 아예 안 보임)
[변경]  탭 = 항상 3개     →  코테는 [1·질문][2·정리 "작성 전"][3·정답]
```

---

## 4. 결정 (3) — 미사용 /api/search 제거

**무엇이 문제였나:** `/search` 결과 페이지는 SSR로 `backendGet`을 직접 부르므로, 브라우저용
프록시 `/api/search`를 실제로 아무도 쓰지 않았다. 그런데도 공개 경로로 열려 있었다.

**무엇을 고민했나:** 쓰지 않는 공개 경로는 공격 면적일 뿐이다.

**그래서 이렇게:** `/api/search` 라우트(30줄)를 삭제했다. 검색 프록시가 다시 필요해지는
것은 issue9의 자동완성(`/api/suggest`)에서다.

---

## 5. 구현 중 마주친 문제

### 이동 후 상대 임포트 잔재 — 빌드가 하나씩만 알려줬다

**무엇이 문제였나:** `git mv`로 파일을 옮긴 뒤 `@/lib/...` 같은 **절대 경로 임포트**는
일괄 치환으로 고쳤지만, 파일 내부의 **상대 임포트**(`from "./logger"`, `from "./backend"`)는
치환 대상 문자열이 아니어서 그대로 남았다. 파일이 다른 폴더로 이사했으니 이 상대 경로들이
전부 깨졌다.

```
Module not found: Can't resolve './logger'     (shared/api/backend.ts — logger가 다른 폴더로 감)
Type error: Cannot find module './backend'     (features/wiki/lib/tree.ts)
```

**무엇을 고민했나:** 빌드가 오류를 **한 번에 하나씩만** 알려줘서 고치고-빌드-고치고를 3회
반복했다. 근본 원인은 개별 실수가 아니라 **정책 부재**였다 — 상대 임포트와 절대 임포트가
정책 없이 섞여 있었던 것. 치환 도구는 절대 경로만 바꿨고, 상대 경로는 파일이 이사하면 깨진다.

```
[기존]  상대·절대 임포트 혼용
        예: import { log } from "./logger"        ← 파일 이동하면 깨짐
[변경]  절대경로(@/...)로 고정
        예: import { log } from "@/shared/lib/logger"   ← 파일이 어디로 가든 안 깨짐
```

**그래서 이렇게(정책 확정, 2026-08-29):** 이 프로젝트는 **절대경로 임포트(`@/...`)로
고정**한다. 같은 폴더 안이라도 상대 임포트를 쓰지 않는다 — 파일 이동이 임포트를 못
깨뜨리게. 이 정책의 전수 적용과 도구별 alias 설정은 issue7에서 마무리한다.

---

## 6. 결론

app이 얇아지고(라우팅만), feature별로 응집됐고, 3탭이 고정됐고, 공개 표면이 줄었다.
vitest 6건 통과·엣지 200 유지. PR: #11
