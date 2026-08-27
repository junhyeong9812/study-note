# issue7 — /api/tree: "트리는 sync 때만 변한다"로 기각을 뒤집다

- 이슈 #12 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/14

## 1. 배경 — 결정 번복의 기록

issue5에서 "트리 API"를 기각했었다(평면 목록 주고 front가 조립). 게이트 리뷰 중 사용자가
재검토: **트리는 문서가 바뀔 때(=sync 때)만 변한다. 그럼 backend가 sync 시점에 한 번
만들어 두면 되지 않나** — 매 요청 조립도, front 조립도 필요 없다. 맞는 관찰이라 채택.
기각을 뒤집을 땐 이유를 남긴다: 이전 기각의 근거("화면 구조가 바뀔 때마다 backend 수정")는
**네비게이션 모양**을 backend가 만들 때 얘기고, 이번에 만드는 건 모양이 아니라
**폴더 구조 그 자체**(리프 폴더=주제, 안에 단일 문서 or 1/2/3)라 화면과 무관하다.

> 곁가지 — "flyway로 추적하면 되지 않나"는 부적합: flyway는 **DB 스키마 마이그레이션**
> 도구다. 트리는 DB에 없고 git의 파생물이라, 트리에 sync된 commit_sha를 태깅하면
> "이 트리 = 이 커밋"이 되고 이력 추적은 git이 공짜로 해준다.

## 2. 구현 워크플로우

```
sync 성공 → TreeBuilder.build(전체 md 경로) → 캐시에 {commit_sha, tree} 저장
                                                (실패한 sync는 트리를 못 바꾼다)
재시작 직후 캐시 없음 → 첫 GET /api/tree 때 clone 기준으로 lazy 생성

GET /api/tree → {"success":true,"data":{"commit_sha":"ecf910e1...","tree":{
  "name":"", "children":[ {"name":"cs", "docs":[...index.md...], "children":[
      {"name":"systems","children":[{"name":"lsm-tree","is_subject":true,
        "docs":[{"path":"...","doc_kind":"question"},{"doc_kind":"summary"},{"doc_kind":"answer"}]}...]}]}...]}}}
```

TreeBuilder는 domain의 **순수 함수**(경로 목록 → 트리) — git도 ES도 모른다. 그래서
테스트가 문자열 목록만으로 끝난다.

## 3. 구현 중 마주친 문제

### 문제 — 트리 JSON만 camelCase(docKind)로 나감
- **원인**: 다른 API는 응답을 손으로 조립(snake_case)했는데 트리는 Kotlin data class를
  그대로 직렬화 — 필드명이 코드 관례(camelCase)로 나갔다.
- **수정**: `@JsonProperty("doc_kind")`·`("is_subject")`로 계약 통일.
- **배경**: "자동 직렬화"는 편하지만 계약을 코드 내부 관례에 결합시킨다. 봉투 규약처럼
  **외부 계약은 명시적으로** 선언해야 리팩토링(필드명 변경)이 계약을 못 깨뜨린다.

## 4. 결론

실기동: 루트 자식 = 재구조화한 버킷 8개(cs·practice·project·lab·portfolio·reference·
templates·세미나), lsm-tree가 is_subject=true로 [question, summary, answer]를 담음.
front는 이 트리를 그대로 그리면 된다. 24건 green. PR: #14
