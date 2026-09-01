# issue9 — 검색 자동완성: ES가 찾고, front는 이스케이프 후 강조만

- 이슈 #18 · PR: #21 (backend issue11과 쌍)

## 1. 배경

헤더 검색이 Enter 전용이었다. 요구: 돋보기 클릭으로도 검색 + **입력 중 자동완성** —
제목이든 내용이든 일치하면 리스트업, 내용 일치면 **일치 부분을 포함한 1문장**을
보여주고 일치 부분은 강조.

## 2. 방식 — 마커 프로토콜 (XSS를 구조로 차단)

backend(ES highlight)가 일치 부분을 HTML 태그가 아니라 **일반 문자로는 안 나올
마커**로 감싸 보낸다: `⟦m⟧정렬⟦/m⟧`. front는:

```tsx
// 텍스트는 React가 통째로 이스케이프 → 마커 위치만 <mark>로 재조립
text.split("⟦m⟧").flatMap(piece => {  const [marked, ...rest] = piece.split("⟦/m⟧"); … })
```

대안이었던 "backend가 `<mark>` HTML로 보내고 front가 dangerouslySetInnerHTML" 은
노트 본문에 악의적/우연한 HTML이 있으면 그대로 실행된다 — 탈락. 마커 방식은
이스케이프를 우회할 길 자체가 없다.

## 3. 흐름

```
입력 → 200ms 디바운스 → front /api/suggest(BFF) → backend ES(collapse·highlight)
리스트: 제목(강조) + 경로 + 스니펫(강조) · ↑↓ 선택 · Enter/돋보기 → /search · 클릭 → 해당 문서
```

상세: deploy-study-note `docs/workflow/search.md`.

## 4. 결론

자동완성이 portfolio 글까지 즉시 잡는다(재구조화 시너지). PR #21
