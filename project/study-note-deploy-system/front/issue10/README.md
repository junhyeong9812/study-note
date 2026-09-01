# issue10 — 마크다운 표 분할선

- 이슈 #19 · PR: #22

**상황**: 노트에 표가 많은데(비교표 문화) 위키에선 표 구조만 잡히고 경계선이 없음.
**원인**: react-markdown(remark-gfm)은 `<table>`을 만들 뿐 스타일은 안 준다 — 브라우저
기본 `<table>`은 테두리가 없다.
**수정**: 전역 `.markdown table` CSS — `border-collapse: collapse`, 셀 경계 `1px var(--line)`,
헤더 배경, 짝수행 줄무늬, 넘치는 표는 `overflow-x: auto`(표만 가로 스크롤 — 페이지는 불변).
겸사겸사 인용(blockquote)·목록 여백도 기본 타이포로 정리.
**배경**: 마크다운 렌더러는 "구조"만 책임진다 — 표시는 전부 소비자(CSS) 몫이라는 경계.
