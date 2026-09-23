# react — React(렌더링·CSS 박스모델·출력 안전) 패턴

React로 화면을 그리며 **CSS 박스모델·출력 이스케이프·관심사 경계**에 부딪혀 터진 패턴.

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [css-negative-margin-overflow](css-negative-margin-overflow/) | 부모 패딩 상쇄용 음수 마진이 overflow 컨테이너와 만나 콘텐츠 폭 초과 → 가로 스크롤. 여백 소유권을 자식에게 옮겨 음수마진 자체를 제거 | front8 |
| [xss-escape-then-assemble](xss-escape-then-assemble/) | 백엔드 HTML을 `dangerouslySetInnerHTML`로 꽂으면 본문 HTML 실행(XSS) → 텍스트 전체 이스케이프 후 마커(`⟦m⟧`)만 `<mark>`로 조립. 디바운스 | front9 · backend11 |
| [separation-structure-vs-style](separation-structure-vs-style/) | 마크다운 렌더러는 구조(`<table>`)만 만들고 표시는 소비자(CSS) 몫인데 그 절반을 안 채움 → 관심사 분리, `border-collapse`. "렌더러 버그가 아니라 스타일 부재" | front10 |
