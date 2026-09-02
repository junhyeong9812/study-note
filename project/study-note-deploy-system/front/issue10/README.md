# issue10 — 마크다운 표 분할선: 렌더러는 구조만, 표시는 CSS 몫

- 이슈 #19 · PR: #22

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> 상황·원인·수정 한 줄씩          ──▶      무엇이 문제였나 → 무엇을 고민했나 → 그래서 이렇게
> "CSS 추가"                     ──▶      실제 globals.css diff + 파일 경로
> border-collapse 용어 던짐        ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 무엇이 문제였나

내 노트에는 비교표가 많다(무엇이든 표로 정리하는 버릇). 그런데 위키에서 보면 표의
**구조만 잡히고 경계선이 없어서**, 셀들이 어디서 나뉘는지 눈으로 구분되지 않았다.

---

## 2. 무엇을 고민했나 — 원인은 렌더러가 아니라 CSS 부재

**원인:** react-markdown(remark-gfm)은 마크다운 표를 `<table>`·`<th>`·`<td>` 같은 **HTML
구조로만** 바꿔준다. 그 이상은 하지 않는다. 그리고 브라우저의 기본 `<table>`은 테두리가
없다. 즉 렌더러는 자기 일(구조 생성)을 다 했고, 빠진 것은 **표시(스타일)**였다.

> 용어 — remark-gfm: 마크다운에 GitHub식 표·체크박스 등을 더해주는 플러그인. 표를
> `<table>` 구조로 바꿔주지만 색·선 같은 스타일은 손대지 않는다.
> 용어 — border-collapse: 인접한 셀의 테두리를 겹쳐 하나의 선으로 합치는 CSS 속성.
> 없으면 셀마다 따로 테두리가 생겨 선이 이중으로 보인다.

**고민:** 표시는 소비자(우리 CSS)의 몫이다. 전역 스타일에 `.markdown table` 규칙을 한 번
넣으면 모든 표에 일괄 적용된다. 넘치는 표(폭이 화면보다 넓은 표)는 페이지 전체를 가로로
밀지 않도록, 표만 가로 스크롤되게 한다.

---

## 3. 그래서 이렇게

전역 `.markdown table` CSS를 추가했다. 파일 경로 `src/app/globals.css`:

```diff
 pre code { background: none; padding: 0; }
+
+/* 마크다운 표 — 분할선이 보이도록 (이슈: 표 구조는 잡히나 경계선 없음) */
+.markdown table { border-collapse: collapse; margin: 1rem 0; display: block; overflow-x: auto; }
+.markdown th, .markdown td { border: 1px solid var(--line); padding: 0.45rem 0.8rem; font-size: 0.92rem; }
+.markdown th { background: var(--code-bg); font-weight: 700; }
+.markdown tr:nth-child(even) td { background: color-mix(in srgb, var(--code-bg) 40%, transparent); }
+.markdown blockquote { border-left: 3px solid var(--line); padding-left: 1rem; color: var(--muted); margin: 0.8rem 0; }
+.markdown h1, .markdown h2, .markdown h3 { margin: 1.4rem 0 0.6rem; }
+.markdown p, .markdown ul, .markdown ol { margin: 0.55rem 0; }
+.markdown ul, .markdown ol { padding-left: 1.4rem; }
```

각 규칙이 하는 일:

```
border-collapse: collapse       셀 경계를 하나의 선으로 합침
th/td border 1px var(--line)    모든 셀에 분할선
th background                   헤더 행에 배경색으로 구분
tr:nth-child(even) 줄무늬        짝수 행 옅은 배경 (행 추적 쉽게)
table display:block + overflow-x 넘치는 표만 가로 스크롤 (페이지는 안 밀림)
blockquote / 목록 여백           겸사겸사 기본 타이포도 정리
```

```
[기존]  | a | b |     ← 구조는 있으나 선이 없어 셀 경계가 안 보임
        | 1 | 2 |
[변경]  ┌───┬───┐     ← border-collapse + 셀 border + 헤더 배경 + 짝수 줄무늬
        │ a │ b │
        ├───┼───┤
        │ 1 │ 2 │
        └───┴───┘
```

---

## 4. 결론

**배경(원칙):** 마크다운 렌더러는 "구조"만 책임진다 — 표시는 전부 소비자(CSS)의 몫이라는
경계. 표 하나 안 보이던 문제의 진짜 원인은 렌더러 버그가 아니라, 그 경계에서 우리가 채워야
할 절반(스타일)을 안 채운 것이었다. PR: #22
