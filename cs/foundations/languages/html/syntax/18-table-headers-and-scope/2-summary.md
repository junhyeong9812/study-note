# html/syntax/18 — 표 머리 연결: `th`·`scope`·`headers`/`id`·`rowspan`/`colspan` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [4.9.12 「표 처리 모델」](https://html.spec.whatwg.org/multipage/tables.html#table-processing-model)(4.9.12.1 「표 만들기」 · 4.9.12.2 「데이터 칸과 머리 칸의 관계 맺기」 — 열 머리·행 머리의 정의와 머리 칸 배정 알고리즘)과 [`th` 요소](https://html.spec.whatwg.org/multipage/tables.html#the-th-element)(`scope` 의 네 상태 · `abbr`), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/)(편집본 — `th` 의 네 줄 대응 · `headers`·`scope`·`abbr` 속성 대응). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다(캡처 조립기). 하네스는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다** — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — HTML 에는 언어 버전이 없다. `api.webstatus.dev` 조회로 **「Tables」 는 Baseline widely**(2018-01-29). `scope`·`headers`·`rowspan`·`colspan` 은 그 안의 오래된 속성이다. ★ `rowspan="0"` 은 따로 잡힌 기능 항목이 없어 **Baseline 으로 접지하지 못했다.**
> **선행** — [17번 주제](../17-table-structure/2-summary.md)(표 구조 — 이 주제가 쓰는 **표 처리 모델의 칸 좌표**가 거기서 나왔다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **본체는 창 ⑦ 이다 — 그런데 창 ⑦ 에는 「이 칸의 머리는 무엇인가」가 없다.** CDP 도 내부 덤프도 셀 노드에 머리 관계를 속성으로 달지 않는다((1)). 그래서 이 주제는 **두 개의 제5의 상태**로 선다 — **명세 알고리즘을 페이지 스크립트로 옮겨 「명세가 정한 머리」를 계산**하고, 트리에서는 **그 계산의 재료(칸 좌표·머리 역할)** 를 받아 **나란히** 놓았다. 「갈린 칸 N / M」은 스크립트가 센다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | CDP 가 쓰는 **포트 번호와 프로필 경로** | 실행마다 다르다 — **출력에는 안 들어간다** |
| **흔들린다(머신 사이)** | (5) 의 **top·height·left px** | 설치된 글꼴에 매인다. 근거는 **「같은가」 한 줄**(`false`)이다 |
| **안 흔들린다** | 트리의 역할 · 내부 덤프의 `tableCell*` 좌표 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 명세 계산 열 | 스크립트가 같은 DOM 에서 같은 답을 낸다 |
| **안 흔들린다** | 격자의 「**… = N / M**」 줄 | 스크립트가 센다 — 사람이 세지 않는다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다 |

실측 — 이 배치(17\~20)의 캡처 **61블록을 세 번 돌려 61블록 전부 한 글자도 같았다**(흔들린 칸 0 · 고칠 것 0).

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑦ 접근성 트리**(CDP + 내부 덤프) | ★★★ **쓴다 — 본체** | 「`th` 가 어떤 머리 역할을 받나」((2)) · 「칸 좌표를 어떻게 매겼나」((3)·(4)) · 「레이아웃 표로 봤나」((7)) — ★ **「이 칸의 머리」는 답하지 않는다**((1)) |
| **명세 계산**(페이지 스크립트) | ★★★ **쓴다 — 제5의 상태** | 「명세가 이 칸에 어느 머리를 배정하나」((6)) — 창이 아니라 **옮긴 알고리즘**이다 |
| **② 프로브**(`getBoundingClientRect`) | 쓴다 — 한 번 | 「`rowspan=0` 이 화면에서 늘어나나」((5)) |
| **① `--dump-dom`** | **부적용** | 머리 연결 속성은 파서가 **고치지도 옮기지도 않는다** — 표 구조의 파서 동작은 [17번](../17-table-structure/2-summary.md)이 잰다 |
| **③ `innerText` 대 `textContent`** | **부적용** | 머리 연결은 글자를 안 만든다 — **잴 것이 없다** |
| **④·⑤·⑥** | **부적용** | 문서 모드·요청·렌더 차단과 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 ① — 「머리 배정」을 스크립트로 물었다.** 트리에 없는 것을 **명세를 옮긴 계산**으로 얻었다. ★ **그 창이 못 보는 것** — **옮긴 스크립트가 명세를 잘못 읽었을 가능성**을 스크립트 자신은 못 잡는다. 그래서 (3) 에 모델 소스 전문을 실었다.
- ★★ **제5의 상태 ② — 「Chrome 이 쓰는 머리」를 재료로 물었다.** 트리가 주는 **좌표와 역할**로 「같은 행의 `rowheader` + 같은 열의 `columnheader`」라는 **단순 규칙**을 셌다((6)). ★ **이것은 트리가 보고한 머리가 아니다** — Chrome 이 플랫폼 API 로 무엇을 넘기는지는 이 판에서 **못 본다**(제3의 상태). 단순 규칙은 「트리를 읽은 사람이 흔히 짐작하는 답」의 대리다.

## 한눈에 — 쉽게 말하면

**★ 칸마다 「이 숫자는 무엇에 대한 숫자인가」를 알려 주는 꼬리표가 머리 칸이다. 꼬리표를 누가 붙이느냐는 명세가 정하고, 브라우저가 실제로 붙인 꼬리표는 이 판에서 안 보인다.**

**엑셀 표의 틀 고정**에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 스크롤해도 남는 **맨 윗줄의 제목** | **열 머리**(column header) — `th` + `scope=col` 또는 자동 판정 |
| 스크롤해도 남는 **맨 왼쪽 열의 이름** | **행 머리**(row header) — `th` + `scope=row` 또는 자동 판정 |
| 「상반기」처럼 **여러 열을 덮는 큰 제목** | **열 묶음 머리** — `scope=colgroup` + `<colgroup>` |
| 칸에 **손으로 적은 메모**(「이 칸은 2월·서울 기준」) | **`headers="id id"`** — 지정하면 **자동 판정을 통째로 대신한다** |
| 셀 하나를 가리키면 엑셀이 띄우는 **「B3 — 2월 / 서울」** 안내 | **머리 칸 배정 알고리즘**의 결과 — 명세에만 있다 |
| 그 안내를 **소리로 읽어 주는 사람** | 보조 기술 — **이 판에 없다** |

- **자동 판정은 「그 줄에 데이터 칸이 하나도 없나」로 한다.** 첫 행이 전부 `th` 면 열 머리다. ★ **빈 모서리를 `<td>` 로 쓰면 그 줄에 데이터 칸이 생겨 머리가 아니게 된다**((3)).
- **`headers` 를 쓰면 그 칸은 그 목록만 쓴다** — 위·왼쪽을 훑지 않는다((6)).
- **트리는 좌표와 역할까지만 준다.** 「이 칸의 머리」는 트리에 없다((1)).

```text
  한 칸의 머리를 정하는 두 길 — 명세의 배정 알고리즘

  <td headers="…"> 가 있나?
     │
     ├── 예 ──> 목록의 id 를 문서에서 찾아, 같은 표의 칸이면 그것만 쓴다
     │          (없는 id 는 조용히 빠진다)
     │
     └── 아니오 ─> 왼쪽으로 훑으며 「행 머리」를 모으고
                   위로 훑으며 「열 머리」를 모으고
                   같은 행 묶음의 scope=rowgroup · 같은 열 묶음의 scope=colgroup 을 더한다
                   (데이터 칸 뒤에 가려진 머리 · 종류가 안 맞는 머리는 막힌다)
```

> **머리 칸(header cell)** — `th` 가 만드는 칸. 명세는 그중 무엇이 **열 머리·행 머리·열 묶음 머리·행 묶음 머리**인지를 따로 정한다.\
> 예: `scope` 없는 `th` 가 첫 행에 있고 그 행에 `td` 가 없으면 **열 머리**다.

## 이 주제가 답하려는 질문

1. **「이 칸의 머리는 무엇인가」를 무엇으로 재나** — 트리에 있나. 없으면 무엇으로 대신 묻나.
2. **`scope` 없는 `th` 는 무슨 머리가 되나** — 명세의 자동 판정과 Chrome 의 역할이 같은가. 빈 모서리 칸 하나가 무엇을 바꾸나.
3. **`rowspan`/`colspan`·`headers`·`scope=colgroup` 이 섞인 표**에서 명세가 정한 좌표·머리와 Chrome 이 매긴 좌표·역할이 **몇 칸 갈리나** — 그리고 「맞아 보이는 칸」 중 몇이 우연인가.

## 동작 방식

### (1) 창 ⑦ 탐침 — 셀 노드에 「머리」가 속성으로 나오나

**언제 쓰나** — 이 주제의 첫 질문. **창 ⑦ 로 답할 수 있는가부터** 확인한다.

(3) 의 복합 머리 표에서 `headers` 를 단 칸(`#c31`), 안 단 칸(`#c21`), `abbr` 를 단 머리(`#m2`)를 골라 **CDP 의 속성 목록**과 **내부 덤프의 속성 이름**을 찍었다(소스는 (3)).

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '66,69p'
(라) 트리가 셀 노드에 단 속성 — #c31(headers 있음) · #c21(없음) · #m2(abbr 있음)
  #c31  CDP properties = [] · 내부 덤프 속성 중 이름에 header 가 든 것 = []
  #c21  CDP properties = [] · 내부 덤프 속성 중 이름에 header 가 든 것 = []
  #m2   abbr="이월" · CDP 이름 = "2월" · CDP 설명 = "" · 내부 덤프 속성 중 이름에 abbr 가 든 것 = []
(exit 0)
```

```text
  「이 칸의 머리」는 어느 층에 있나 — HTML-AAM 의 headers 속성 줄

  WAI-ARIA 층 (CDP · 내부 덤프가 보는 것)     Not mapped            <- 자리가 없다
  플랫폼 API 층                               IAccessibleTableCell::columnHeaderCells
                                              UIA Table.ItemColumnHeaderItems
                                              atk_table_get_column_header
                                              AXColumnHeaderUIElements
                                                                    <- 여기 산다. 이 판에서 못 본다
```

- ★★★ **셀 노드에 머리 관계가 없다.** CDP `properties` 는 **빈 배열**, 내부 덤프에도 이름에 `header` 가 든 속성이 **하나도 없다** — `headers` 를 단 칸도 마찬가지다.
- ★★ **이것은 누락이 아니라 명세 구조다.** HTML-AAM 은 `headers` 속성을 **WAI-ARIA 층에 「Not mapped」** 로 적고, **플랫폼 API**(IAccessible2 의 `columnHeaderCells` · UIA 의 `ItemColumnHeaderItems` · ATK · AX)로만 넘기라고 적는다. CDP 트리는 그 위 층이라 **자리가 없다.**
- ★ **`th abbr="이월"` 도 흔적이 없다** — CDP 이름은 `"2월"` 그대로, 설명은 빈 문자열. HTML-AAM 은 `abbr` 을 **AX 의 `AXDescription`·IA2/ATK 의 객체 속성**으로 적는다 — 역시 플랫폼 층이다.
- ★★★ **그래서 창 ⑦ 만으로는 이 주제에 답할 수 없다 — 창을 바꿨다.** 명세 쪽은 **알고리즘을 스크립트로 옮기고**, Chrome 쪽은 **트리가 주는 재료(좌표·역할)** 를 받는다. 머리 연결 그 자체는 **「못 잰 것」(제3의 상태)** 으로 남긴다.

### (2) 창 ⑦ × 명세 계산 — `scope` 없는 `th` 는 무슨 머리인가

**언제 쓰나** — `scope` 를 안 쓴 표를 받았을 때 · `scope` 를 틀리게 쓴 표를 받았을 때.

표 열 개에 `th` 를 스무 개 두고, `th` 마다 **명세의 머리 종류**(열·행·열묶음·행묶음·아님 — 스크립트 계산)와 **그 종류에 HTML-AAM 이 대응시키는 역할**, **트리의 역할**을 나란히 찍었다. 모델 스크립트는 (3) 에 있다.

```html
<!-- html17b-18-scope.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 th 는 무슨 머리인가</title>
<script src="html17b-18-model.js"></script>
</head>
<body>
<table data-k="첫 행이 th"><tr><th id="a1">이름</th><th id="a2">값</th></tr><tr><td>사과</td><td>1</td></tr></table>
<table data-k="첫 열이 th"><tr><th id="b1">사과</th><td>1</td></tr><tr><th id="b2">배</th><td>2</td></tr></table>
<table data-k="첫 행과 첫 열"><tr><th id="c1">과일</th><th id="c2">값</th></tr><tr><th id="c3">사과</th><td>1</td></tr></table>
<table data-k="가운데 th"><tr><td>가</td><th id="d1">나</th><td>다</td></tr><tr><td>1</td><td>2</td><td>3</td></tr></table>
<table data-k="th 만 있는 표"><tr><th id="e1">가</th><th id="e2">나</th></tr><tr><th id="e3">다</th><th id="e4">라</th></tr></table>
<table data-k="첫 행에 scope=row"><tr><th id="f1" scope="row">가</th><th id="f2" scope="row">나</th></tr><tr><td>1</td><td>2</td></tr></table>
<table data-k="첫 열에 scope=col"><tr><th id="g1" scope="col">사과</th><td>1</td></tr><tr><th id="g2" scope="col">배</th><td>2</td></tr></table>
<table data-k="모르는 scope 값"><tr><th id="h1" scope="위">사과</th><td>1</td></tr><tr><th id="h2" scope="위">배</th><td>2</td></tr></table>
<table data-k="scope=colgroup"><colgroup span="2"></colgroup><tr><th id="i1" scope="colgroup" colspan="2">묶음</th></tr><tr><td>1</td><td>2</td></tr></table>
<table data-k="scope=rowgroup"><tbody><tr><th id="j1" scope="rowgroup">묶음</th><td>1</td></tr><tr><td>2</td><td>3</td></tr></tbody></table>
<script>
window.__대상 = [...document.querySelectorAll("th")].map(e => [e.id, "#" + e.id]);
window.__끝 = () => {
  const O = ["th 마다 — 명세의 표 모델이 정한 머리 종류(스크립트 계산) · 그 종류에 HTML-AAM 이 대응시키는 역할 · 트리의 역할"];
  const AAM = { "열": "columnheader", "열묶음": "columnheader", "행": "rowheader", "행묶음": "rowheader", "아님": "cell" };
  let 갈림 = 0, 전체 = 0;
  for (const t of document.querySelectorAll("table[data-k]")) {
    const 표 = 표만들기(t);
    for (const c of 표.칸.filter(c => c.머리)) {
      const 종류 = 머리종류(표, c), 기대 = AAM[종류], 트리 = __AX[c.el.id].역할;
      전체++; if (기대 !== 트리) 갈림++;
      O.push("  " + t.dataset.k.padEnd(18) + ("#" + c.el.id).padEnd(4) + "(" + c.x + "," + c.y + ")  명세 = " + 종류.padEnd(4)
        + "-> " + 기대.padEnd(13) + "트리 = " + 트리.padEnd(13) + (기대 === 트리 ? "" : "<- 갈림"));
    }
  }
  O.push("");
  O.push("갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-18-scope.html
th 마다 — 명세의 표 모델이 정한 머리 종류(스크립트 계산) · 그 종류에 HTML-AAM 이 대응시키는 역할 · 트리의 역할
  첫 행이 th           #a1 (0,0)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 행이 th           #a2 (1,0)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 열이 th           #b1 (0,0)  명세 = 행   -> rowheader    트리 = rowheader    
  첫 열이 th           #b2 (0,1)  명세 = 행   -> rowheader    트리 = rowheader    
  첫 행과 첫 열          #c1 (0,0)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 행과 첫 열          #c2 (1,0)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 행과 첫 열          #c3 (0,1)  명세 = 행   -> rowheader    트리 = rowheader    
  가운데 th            #d1 (1,0)  명세 = 아님  -> cell         트리 = rowheader    <- 갈림
  th 만 있는 표         #e1 (0,0)  명세 = 열   -> columnheader 트리 = columnheader 
  th 만 있는 표         #e2 (1,0)  명세 = 열   -> columnheader 트리 = columnheader 
  th 만 있는 표         #e3 (0,1)  명세 = 열   -> columnheader 트리 = columnheader 
  th 만 있는 표         #e4 (1,1)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 행에 scope=row    #f1 (0,0)  명세 = 행   -> rowheader    트리 = rowheader    
  첫 행에 scope=row    #f2 (1,0)  명세 = 행   -> rowheader    트리 = rowheader    
  첫 열에 scope=col    #g1 (0,0)  명세 = 열   -> columnheader 트리 = columnheader 
  첫 열에 scope=col    #g2 (0,1)  명세 = 열   -> columnheader 트리 = columnheader 
  모르는 scope 값       #h1 (0,0)  명세 = 행   -> rowheader    트리 = rowheader    
  모르는 scope 값       #h2 (0,1)  명세 = 행   -> rowheader    트리 = rowheader    
  scope=colgroup    #i1 (0,0)  명세 = 열묶음 -> columnheader 트리 = columnheader 
  scope=rowgroup    #j1 (0,0)  명세 = 행묶음 -> rowheader    트리 = rowheader    

갈린 칸 = 1 / 20
(exit 0)
```

```text
  명세의 자동 판정 (scope 가 auto 일 때)

  열 머리   <- 그 th 가 걸친 「행」들에 데이터 칸(td)이 하나도 없다
  행 머리   <- 열 머리가 아니고, 그 th 가 걸친 「열」들에 데이터 칸이 하나도 없다
  아님      <- 둘 다 아니다  -> HTML-AAM: 역할 cell

  가운데 th   행에 td 있음 · 열에 td 있음   -> 명세 「아님」(cell)   트리 rowheader   <- 갈렸다
```

- ★★★ **갈린 칸은 20 중 1** 이다 — **「가운데 `th`」** 하나. 명세로는 그 `th` 의 행에도 열에도 `td` 가 있어 **어느 머리도 아니다** — HTML-AAM 의 `th` 첫 줄(「열·행·열묶음·행묶음 머리가 아닌 `th`」)이 **`cell` 역할**을 준다. **Chrome 은 `rowheader` 를 줬다.** 명세 ↔ 구현 불일치다.
- ★★ **`scope` 가 자동 판정을 이긴다.** 첫 **행**에 `scope=row` 를 주면 `rowheader`, 첫 **열**에 `scope=col` 을 주면 `columnheader` — 명세도 트리도 같다.
- ★ **모르는 값(`scope="위"`)은 `auto` 로 떨어진다** — 명세의 「누락 기본값과 무효 기본값이 둘 다 Auto」. 첫 열이라 행 머리가 됐다.
- ★ **`th` 만 있는 표는 전부 열 머리**다 — 어느 행에도 `td` 가 없으니 **열 머리 조건이 먼저 선다.** 둘째 행의 `th` 도 `columnheader` 다.
- **`scope=colgroup`·`rowgroup` 은 트리에서 `columnheader`·`rowheader`** — HTML-AAM 의 대응 그대로다.

### (3) 창 ⑦ × 명세 계산 — 복합 머리 표의 좌표와 역할

**언제 쓰나** — 이 주제의 본체. `rowspan`/`colspan`·`scope=colgroup`·`headers`·`rowspan=0` 이 한 표에 섞일 때.

「지역별 판매」 표 하나에 **이 주제의 표면을 전부** 넣었다. 둘째 표는 스크립트가 첫 표를 복제해 **모서리의 `<td>` 하나만 `<th>` 로** 바꾼 것이다((6) 이 쓴다).

```html
<!-- html17b-18-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 복합 머리 표</title>
<script src="html17b-18-model.js"></script>
</head>
<body>
<table id="판매">
<caption>지역별 판매</caption>
<colgroup><col></colgroup><colgroup span="2"></colgroup><colgroup span="2"></colgroup>
<thead>
<tr><td id="모서리" rowspan="2"></td><th id="상" colspan="2" scope="colgroup">상반기</th><th id="하" colspan="2" scope="colgroup">하반기</th></tr>
<tr><th id="m1">1월</th><th id="m2" abbr="이월">2월</th><th id="m7">7월</th><th id="m8">8월</th></tr>
</thead>
<tbody>
<tr><th id="서울" scope="row">서울</th><td id="c21">1</td><td id="c22" headers="서울 m2 상">2</td><td id="c23">3</td><td id="c24" rowspan="0">4</td></tr>
<tr><th id="인천" scope="row">인천</th><td id="c31" headers="m1 인천">5</td><td id="c32" headers="m2 서울">6</td><td id="c33" headers="없는아이디">7</td><td id="c34">8</td></tr>
</tbody>
<tbody>
<tr><th id="부산" rowspan="2">부산</th><td id="c41">9</td><td id="c42" colspan="2">10</td><td id="c44">11</td></tr>
<tr><td id="c51">12</td><td id="c52">13</td><td id="c53">14</td><td id="c54">15</td></tr>
</tbody>
</table>
<script>
// 둘째 표 — 첫 표를 복제해 모서리의 <td> 만 <th> 로 바꾼다. id 와 headers 에는 「_2」를 붙인다.
const 둘째 = document.getElementById("판매").cloneNode(true);
둘째.id = "판매_2";
for (const e of 둘째.querySelectorAll("[id]")) e.id += "_2";
for (const e of 둘째.querySelectorAll("[headers]"))
  e.setAttribute("headers", e.getAttribute("headers").split(" ").map(t => t + "_2").join(" "));
const 옛 = 둘째.querySelector("#모서리_2"), 새 = document.createElement("th");
for (const a of 옛.attributes) 새.setAttribute(a.name, a.value);
옛.replaceWith(새);
document.body.append(둘째);
window.__대상 = [...document.querySelectorAll("th, td")].map(e => [e.id, "#" + e.id]);
window.__내부 = true;
const AAM = { "열": "columnheader", "열묶음": "columnheader", "행": "rowheader", "행묶음": "rowheader", "아님": "cell" };
const 이름 = cs => cs.length ? cs.map(c => c.el.id).join(" ") : "—";
const 트리 = c => { const a = __INT[c.el.id].속성; return { x: +a.tableCellColumnIndex, y: +a.tableCellRowIndex,
  w: +a.tableCellColumnSpan, h: +a.tableCellRowSpan, 역할: __AX[c.el.id].역할 }; };
function 재기(id, O, 자세히) {
  const 표 = 표만들기(document.getElementById(id));
  let 좌갈 = 0, 좌전 = 0, 역갈 = 0, 역전 = 0;
  for (const c of 표.칸) {
    const t = 트리(c), 명 = [c.x, c.y, c.w, c.h], 트 = [t.x, t.y, t.w, t.h];
    const 갈린 = 명.filter((v, i) => v !== 트[i]).length;
    좌갈 += 갈린; 좌전 += 4;
    const 기대 = c.머리 ? AAM[머리종류(표, c)] : "cell";
    역전++; if (기대 !== t.역할) 역갈++;
    if (자세히 === "좌표") O.push("  " + ("#" + c.el.id).padEnd(6) + "명세 (" + 명.join(",") + ")  트리 (" + 트.join(",") + ")"
      + (갈린 ? "  <- 좌표 " + 갈린 + "칸" : "        ") + "   역할 명세->" + 기대.padEnd(13) + "트리 " + t.역할
      + (기대 !== t.역할 ? "  <- 역할" : ""));
  }
  const 요약1 = "  좌표 칸 갈림 = " + 좌갈 + " / " + 좌전 + " · 역할 칸 갈림 = " + 역갈 + " / " + 역전
    + " · 표 크기 명세 " + 표.폭 + "x" + 표.높이 + " / 트리 " + __INT[id].속성.tableColumnCount + "x" + __INT[id].속성.tableRowCount;
  const 머리칸 = 표.칸.map(c => ({ c, t: 트리(c) }));
  let 같음 = 0, 전체 = 0, 우연 = 0;
  for (const c of 표.칸.filter(c => !c.머리 && c.el.textContent.trim())) {
    const t = 트리(c);
    const 겹침 = (a, n, b, m) => a < b + Math.max(m, 1) && b < a + Math.max(n, 1);
    const 단순 = 머리칸.filter(({ t: h }) =>
      (h.역할 === "rowheader" && 겹침(h.y, h.h, t.y, t.h)) ||
      (h.역할 === "columnheader" && 겹침(h.x, h.w, t.x, t.w))).map(({ c }) => c);
    const 명세 = 머리찾기(표, c);
    const 정렬 = cs => cs.map(k => k.el.id).sort().join(" ");
    const 일치 = 정렬(명세) === 정렬(단순);
    전체++; if (일치) { 같음++; if (c.el.hasAttribute("headers")) 우연++; }
    if (자세히 === "머리") O.push("  " + ("#" + c.el.id).padEnd(8)
      + (c.el.hasAttribute("headers") ? "headers=" + JSON.stringify(c.el.getAttribute("headers")) : "").padEnd(26)
      + "명세 = " + 이름(명세).padEnd(24) + "단순 규칙 = " + 이름(단순).padEnd(24) + (일치 ? "같음" : "다름"));
  }
  const 요약2 = "  머리가 같은 칸 = " + 같음 + " / " + 전체 + " · 그중 headers 속성이 있는 칸 = " + 우연;
  return [요약1, 요약2];
}
window.__끝 = () => {
  const O = [];
  O.push("(가) 첫 표(모서리 td) — 칸마다 좌표 (x,y,w,h)와 역할: 명세 표 모델(스크립트) 대 트리(내부 덤프 tableCell* · CDP 역할)");
  const [a1, a2] = 재기("판매", O, "좌표");
  O.push(a1);
  O.push("");
  O.push("(나) 첫 표 — 글자가 있는 데이터 칸마다 머리: 명세 알고리즘(스크립트) 대 「트리 재료로 셈한 단순 규칙」(같은 행 rowheader + 같은 열 columnheader)");
  재기("판매", O, "머리");
  O.push(a2);
  O.push("");
  O.push("(다) 둘째 표(모서리 th) — 같은 머리 격자와 두 요약");
  const [b1, b2] = 재기("판매_2", O, "머리");
  O.push(b2);
  O.push(b1);
  O.push("");
  O.push("(라) 트리가 셀 노드에 단 속성 — #c31(headers 있음) · #c21(없음) · #m2(abbr 있음)");
  for (const id of ["c31", "c21"]) O.push("  #" + id + "  CDP properties = " + JSON.stringify(Object.keys(__AX[id].속성))
    + " · 내부 덤프 속성 중 이름에 header 가 든 것 = " + JSON.stringify(Object.keys(__INT[id].속성).filter(k => /header/i.test(k))));
  O.push("  #m2   abbr=" + JSON.stringify(document.getElementById("m2").getAttribute("abbr")) + " · CDP 이름 = " + JSON.stringify(__AX.m2.이름)
    + " · CDP 설명 = " + JSON.stringify(__AX.m2.설명) + " · 내부 덤프 속성 중 이름에 abbr 가 든 것 = "
    + JSON.stringify(Object.keys(__INT.m2.속성).filter(k => /abbr/i.test(k))));
  O.push("");
  O.push("(마) 창 ② — rowspan=0 인 #c24 와 이웃의 화면 상자(위·높이 px), 그리고 #c34 의 가로 순서");
  const R = id => document.getElementById(id).getBoundingClientRect();
  for (const id of ["c23", "c24", "c33", "c34"]) O.push("  #" + id + "  top = " + R(id).top.toFixed(0) + " · height = " + R(id).height.toFixed(0)
    + " · left = " + R(id).left.toFixed(0));
  O.push("  #c34 의 left 가 #c24 의 left 와 같은가 = " + (R("c34").left === R("c24").left));
  return O.join("\n");
};
</script>
</body>
</html>
```

**명세 모델** — 4.9.12 「표 처리 모델」을 옮긴 스크립트다. `표만들기` 가 칸마다 (x, y, 폭, 높이)를 매기고, `머리종류` 가 `th` 의 종류를, `머리찾기` 가 머리 칸 배정 알고리즘을 돈다.

```js
// html17b-18-model.js
// WHATWG HTML 4.9.12 「표 처리 모델」을 페이지 스크립트로 옮긴 것.
//   표만들기(table)  -> { 칸: [{ el, x, y, w, h, 머리 }], 폭, 높이, 행묶음: [...], 열묶음: [...] }
//   머리종류(표, 칸)  -> "열" | "행" | "열묶음" | "행묶음" | "아님"  (th 만. td 는 null)
//   머리찾기(표, 칸)  -> 명세가 그 칸에 배정하는 머리 칸들의 배열
// ★ 이것은 명세를 옮긴 「계산」이지 브라우저가 보고한 값이 아니다.
function 음이아닌정수(v) {                       // rules for parsing non-negative integers (근사)
  const m = /^[\t\n\f\r ]*(\d+)/.exec(v ?? "");
  return m ? Number(m[1]) : null;
}
function 표만들기(table) {
  const 표 = { 칸: [], 폭: 0, 높이: 0, 행묶음: [], 열묶음: [] };
  const 슬롯 = new Map();                          // "x,y" -> [칸 ...]
  const 덮기 = (c, x, y) => { const k = x + "," + y; if (!슬롯.has(k)) 슬롯.set(k, []); 슬롯.get(k).push(c); };
  let y현재 = 0, 자라는 = [];
  const 자라기 = () => { for (const g of 자라는) { for (let x = g.x; x < g.x + g.w; x++) 덮기(g.c, x, y현재); g.c.h = y현재 - g.c.y + 1; } };
  const 행 = tr => {
    if (표.높이 === y현재) 표.높이++;
    let x = 0;
    자라기();
    for (const el of [...tr.children].filter(e => e.localName === "td" || e.localName === "th")) {
      while (x < 표.폭 && 슬롯.has(x + "," + y현재)) x++;
      if (x === 표.폭) 표.폭++;
      let cs = 음이아닌정수(el.getAttribute("colspan")); if (!cs) cs = 1; if (cs > 1000) cs = 1000;
      let rs = 음이아닌정수(el.getAttribute("rowspan")); if (rs === null) rs = 1; if (rs > 65534) rs = 65534;
      let 자람 = false; if (rs === 0) { 자람 = true; rs = 1; }
      if (표.폭 < x + cs) 표.폭 = x + cs;
      if (표.높이 < y현재 + rs) 표.높이 = y현재 + rs;
      const c = { el, x, y: y현재, w: cs, h: rs, 머리: el.localName === "th" };
      for (let yy = y현재; yy < y현재 + rs; yy++) for (let xx = x; xx < x + cs; xx++) 덮기(c, xx, yy);
      표.칸.push(c);
      if (자람) 자라는.push({ c, x, w: cs });
      x += cs;
    }
    y현재++;
  };
  const 묶음끝 = () => { while (y현재 < 표.높이) { 자라기(); y현재++; } 자라는 = []; };
  const 행묶음 = g => {
    const 시작 = 표.높이;
    for (const tr of [...g.children].filter(e => e.localName === "tr")) 행(tr);
    if (표.높이 > 시작) 표.행묶음.push({ el: g, y: 시작, h: 표.높이 - 시작 });
    묶음끝();
  };
  const 미룬tfoot = [];
  let 행시작 = false;                              // 행이 시작된 뒤의 colgroup 은 명세가 건너뛴다
  for (const e of table.children) {
    if (["tr", "thead", "tbody", "tfoot"].includes(e.localName)) 행시작 = true;
    if (e.localName === "colgroup" && !행시작) {
      const cols = [...e.children].filter(c => c.localName === "col");
      const 시작 = 표.폭;
      if (cols.length) for (const col of cols) { let s = 음이아닌정수(col.getAttribute("span")); if (!s) s = 1; 표.폭 += Math.min(s, 1000); }
      else { let s = 음이아닌정수(e.getAttribute("span")); if (!s) s = 1; 표.폭 += Math.min(s, 1000); }
      표.열묶음.push({ el: e, x: 시작, w: 표.폭 - 시작 });
    } else if (e.localName === "tr") 행(e);
    else if (e.localName === "tfoot") { 묶음끝(); 미룬tfoot.push(e); }
    else if (e.localName === "thead" || e.localName === "tbody") { 묶음끝(); 행묶음(e); }
  }
  묶음끝();
  for (const f of 미룬tfoot) 행묶음(f);
  표.슬롯 = 슬롯;
  return 표;
}
function 범위(v) { const s = (v || "").toLowerCase(); return ["row", "col", "rowgroup", "colgroup"].includes(s) ? s : "auto"; }
function 머리종류(표, c) {
  if (!c.머리) return null;
  const s = 범위(c.el.getAttribute("scope"));
  const 데이터있음 = pred => 표.칸.some(d => !d.머리 && pred(d));
  const 겹침 = (a, n, b, m) => a < b + m && b < a + n;
  const 열머리 = s === "col" || (s === "auto" && !데이터있음(d => 겹침(d.y, d.h, c.y, c.h)));
  if (열머리) return "열";
  if (s === "row" || (s === "auto" && !데이터있음(d => 겹침(d.x, d.w, c.x, c.w)))) return "행";
  if (s === "colgroup") return "열묶음";
  if (s === "rowgroup") return "행묶음";
  return "아님";
}
function 머리찾기(표, p) {
  let 목록 = [];
  const 종류 = c => 머리종류(표, c);
  if (p.el.hasAttribute("headers")) {
    for (const id of p.el.getAttribute("headers").split(/[\t\n\f\r ]+/).filter(Boolean)) {
      const e = document.getElementById(id);
      const c = 표.칸.find(k => k.el === e);
      if (c && c !== p) 목록.push(c);
    }
  } else {
    const 훑기 = (x0, y0, dx, dy) => {
      let x = x0, y = y0; const 불투명 = [];
      let 블록안 = p.머리, 블록 = p.머리 ? [p] : [];
      for (;;) {
        x += dx; y += dy;
        if (x < 0 || y < 0) return;
        const 덮은 = 표.슬롯.get(x + "," + y) || [];
        if (덮은.length !== 1) continue;
        const c = 덮은[0];
        if (c.머리) {
          블록안 = true; 블록.push(c);
          let 막힘 = false;
          if (dx === 0) { if (불투명.some(o => o.x === c.x && o.w === c.w)) 막힘 = true; if (종류(c) !== "열") 막힘 = true; }
          if (dy === 0) { if (불투명.some(o => o.y === c.y && o.h === c.h)) 막힘 = true; if (종류(c) !== "행") 막힘 = true; }
          if (!막힘) 목록.push(c);
        } else if (블록안) { 블록안 = false; 불투명.push(...블록); 블록 = []; }
      }
    };
    for (let y = p.y; y < p.y + p.h; y++) 훑기(p.x, y, -1, 0);
    for (let x = p.x; x < p.x + p.w; x++) 훑기(x, p.y, 0, -1);
    const 행g = 표.행묶음.find(g => p.y >= g.y && p.y < g.y + g.h);
    if (행g) 목록.push(...표.칸.filter(c => 종류(c) === "행묶음" && c.y >= 행g.y && c.y < 행g.y + 행g.h
      && c.x <= p.x + p.w - 1 && c.y <= p.y + p.h - 1));
    const 열g = 표.열묶음.find(g => p.x >= g.x && p.x < g.x + g.w);
    if (열g) 목록.push(...표.칸.filter(c => 종류(c) === "열묶음" && c.x >= 열g.x && c.x < 열g.x + 열g.w
      && c.x <= p.x + p.w - 1 && c.y <= p.y + p.h - 1));
  }
  const 빈칸 = c => c.el.children.length === 0 && /^[\t\n\f\r ]*$/.test(c.el.textContent);
  목록 = 목록.filter(c => !빈칸(c));
  return [...new Set(목록)].filter(c => c !== p);
}
```

```text
  첫 표의 격자 — 명세 표 모델이 매긴 좌표 (x →, y ↓)

         x=0          x=1     x=2     x=3     x=4     x=5
       +-----------+---------------+---------------+
  y=0  | (모서리 td)|    상반기      |    하반기      |      colgroup: x0 | x1-2 | x3-4
       |  rowspan=2 +-------+-------+-------+-------+
  y=1  |            |  1월  |  2월  |  7월  |  8월  |      thead
       +-----------+-------+-------+-------+-------+
  y=2  | 서울 row   |  c21  |  c22  |  c23  |  c24  |      tbody 1
       +-----------+-------+-------+-------+ rowspan=0
  y=3  | 인천 row   |  c31  |  c32  |  c33  |  (c24)|  c34   <- 명세: c24 가 x=4 를 덮어 x=5 로 밀린다
       +-----------+-------+-------+-------+-------+-------
  y=4  | 부산      |  c41  |    c42 (2칸)  |  c44  |      tbody 2
       | rowspan=2 +-------+-------+-------+-------+
  y=5  |            |  c51  |  c52  |  c53  |  c54  |
       +-----------+-------+-------+-------+-------+

  트리(내부 덤프)의 좌표:  c24 = (4,2,1,0)   c34 = (4,3)   표 크기 5 x 6
```

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '1,27p'
(가) 첫 표(모서리 td) — 칸마다 좌표 (x,y,w,h)와 역할: 명세 표 모델(스크립트) 대 트리(내부 덤프 tableCell* · CDP 역할)
  #모서리  명세 (0,0,1,2)  트리 (0,0,1,2)           역할 명세->cell         트리 cell
  #상    명세 (1,0,2,1)  트리 (1,0,2,1)           역할 명세->columnheader 트리 columnheader
  #하    명세 (3,0,2,1)  트리 (3,0,2,1)           역할 명세->columnheader 트리 columnheader
  #m1   명세 (1,1,1,1)  트리 (1,1,1,1)           역할 명세->cell         트리 columnheader  <- 역할
  #m2   명세 (2,1,1,1)  트리 (2,1,1,1)           역할 명세->cell         트리 columnheader  <- 역할
  #m7   명세 (3,1,1,1)  트리 (3,1,1,1)           역할 명세->cell         트리 columnheader  <- 역할
  #m8   명세 (4,1,1,1)  트리 (4,1,1,1)           역할 명세->cell         트리 columnheader  <- 역할
  #서울   명세 (0,2,1,1)  트리 (0,2,1,1)           역할 명세->rowheader    트리 rowheader
  #c21  명세 (1,2,1,1)  트리 (1,2,1,1)           역할 명세->cell         트리 cell
  #c22  명세 (2,2,1,1)  트리 (2,2,1,1)           역할 명세->cell         트리 cell
  #c23  명세 (3,2,1,1)  트리 (3,2,1,1)           역할 명세->cell         트리 cell
  #c24  명세 (4,2,1,2)  트리 (4,2,1,0)  <- 좌표 1칸   역할 명세->cell         트리 cell
  #인천   명세 (0,3,1,1)  트리 (0,3,1,1)           역할 명세->rowheader    트리 rowheader
  #c31  명세 (1,3,1,1)  트리 (1,3,1,1)           역할 명세->cell         트리 cell
  #c32  명세 (2,3,1,1)  트리 (2,3,1,1)           역할 명세->cell         트리 cell
  #c33  명세 (3,3,1,1)  트리 (3,3,1,1)           역할 명세->cell         트리 cell
  #c34  명세 (5,3,1,1)  트리 (4,3,1,1)  <- 좌표 1칸   역할 명세->cell         트리 cell
  #부산   명세 (0,4,1,2)  트리 (0,4,1,2)           역할 명세->cell         트리 rowheader  <- 역할
  #c41  명세 (1,4,1,1)  트리 (1,4,1,1)           역할 명세->cell         트리 cell
  #c42  명세 (2,4,2,1)  트리 (2,4,2,1)           역할 명세->cell         트리 cell
  #c44  명세 (4,4,1,1)  트리 (4,4,1,1)           역할 명세->cell         트리 cell
  #c51  명세 (1,5,1,1)  트리 (1,5,1,1)           역할 명세->cell         트리 cell
  #c52  명세 (2,5,1,1)  트리 (2,5,1,1)           역할 명세->cell         트리 cell
  #c53  명세 (3,5,1,1)  트리 (3,5,1,1)           역할 명세->cell         트리 cell
  #c54  명세 (4,5,1,1)  트리 (4,5,1,1)           역할 명세->cell         트리 cell
  좌표 칸 갈림 = 2 / 100 · 역할 칸 갈림 = 5 / 25 · 표 크기 명세 6x6 / 트리 5x6
(exit 0)
```

- ★★★ **좌표 칸 갈림 2 / 100 · 역할 칸 갈림 5 / 25 · 표 크기 명세 6x6 / 트리 5x6.**
- ★★ **좌표가 갈린 두 칸은 `rowspan="0"` 한 곳에서 나왔다.** 명세는 `rowspan=0` 을 「**행 묶음 끝까지 자란다**」로 적는다 — `#c24` 가 y=2\~3 을 덮고, 그래서 `#c34` 가 **x=5** 로 밀린다. **트리는 `#c24` 의 높이를 0 으로, `#c34` 를 x=4 로** 매겼다((4) 가 원본).
- ★★★ **역할이 갈린 다섯 칸은 전부 「빈 모서리 `<td>`」 하나에서 나왔다.** `#모서리` 는 **데이터 칸**이다(빈 `td` 여도). 그래서 명세로는 —
  - `1월`·`2월`·`7월`·`8월`(y=1) 은 **그 행에 데이터 칸(모서리)이 있어 열 머리가 아니고**, 열에도 데이터가 있어 행 머리도 아니다 → **「아님」** → `cell`.
  - `부산`(x=0, `scope` 없음) 은 **그 열에 데이터 칸(모서리)이 있어 행 머리가 아니다** → `cell`.
  - Chrome 은 다섯 다 **`columnheader`·`rowheader`** 를 줬다.
- ★ **`scope` 를 쓴 칸은 안 갈렸다** — `상반기`·`하반기`(`colgroup`)·`서울`·`인천`(`row`). **명시한 `scope` 는 모서리 칸의 영향을 안 받는다.**

> **데이터 칸(data cell)** — `td` 가 만드는 칸. **글자가 없어도 데이터 칸이다.** 명세의 자동 판정은 「데이터 칸이 있나」를 본다.\
> 예: 빈 `<td>` 모서리 하나가 같은 행의 `th` 넷을 머리에서 떨어뜨렸다.

### (4) 창 ⑦ 원본 — 내부 덤프의 `tableCell*`

**언제 쓰나** — (3) 의 「트리」 열이 **스크립트의 가공이 아니라 덤프 그대로**라는 것을 확인하는 자리.

```text
$ python3 html17b-cdp.py int html17b-18-grid.html tableCellColumnIndex,tableCellRowIndex,tableCellColumnSpan,tableCellRowSpan | sed -n '1,35p'
rootWebArea
      table          #판매
        caption
        rowGroup
          row
            cell           #모서리     tableCellColumnIndex=0 tableCellRowIndex=0 tableCellColumnSpan=1 tableCellRowSpan=2
            columnHeader   #상       tableCellColumnIndex=1 tableCellRowIndex=0 tableCellColumnSpan=2 tableCellRowSpan=1
            columnHeader   #하       tableCellColumnIndex=3 tableCellRowIndex=0 tableCellColumnSpan=2 tableCellRowSpan=1
          row
            columnHeader   #m1      tableCellColumnIndex=1 tableCellRowIndex=1 tableCellColumnSpan=1 tableCellRowSpan=1
            columnHeader   #m2      tableCellColumnIndex=2 tableCellRowIndex=1 tableCellColumnSpan=1 tableCellRowSpan=1
            columnHeader   #m7      tableCellColumnIndex=3 tableCellRowIndex=1 tableCellColumnSpan=1 tableCellRowSpan=1
            columnHeader   #m8      tableCellColumnIndex=4 tableCellRowIndex=1 tableCellColumnSpan=1 tableCellRowSpan=1
          row
            rowHeader      #서울      tableCellColumnIndex=0 tableCellRowIndex=2 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c21     tableCellColumnIndex=1 tableCellRowIndex=2 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c22     tableCellColumnIndex=2 tableCellRowIndex=2 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c23     tableCellColumnIndex=3 tableCellRowIndex=2 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c24     tableCellColumnIndex=4 tableCellRowIndex=2 tableCellColumnSpan=1 tableCellRowSpan=0
          row
            rowHeader      #인천      tableCellColumnIndex=0 tableCellRowIndex=3 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c31     tableCellColumnIndex=1 tableCellRowIndex=3 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c32     tableCellColumnIndex=2 tableCellRowIndex=3 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c33     tableCellColumnIndex=3 tableCellRowIndex=3 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c34     tableCellColumnIndex=4 tableCellRowIndex=3 tableCellColumnSpan=1 tableCellRowSpan=1
          row
            rowHeader      #부산      tableCellColumnIndex=0 tableCellRowIndex=4 tableCellColumnSpan=1 tableCellRowSpan=2
            cell           #c41     tableCellColumnIndex=1 tableCellRowIndex=4 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c42     tableCellColumnIndex=2 tableCellRowIndex=4 tableCellColumnSpan=2 tableCellRowSpan=1
            cell           #c44     tableCellColumnIndex=4 tableCellRowIndex=4 tableCellColumnSpan=1 tableCellRowSpan=1
          row
            cell           #c51     tableCellColumnIndex=1 tableCellRowIndex=5 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c52     tableCellColumnIndex=2 tableCellRowIndex=5 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c53     tableCellColumnIndex=3 tableCellRowIndex=5 tableCellColumnSpan=1 tableCellRowSpan=1
            cell           #c54     tableCellColumnIndex=4 tableCellRowIndex=5 tableCellColumnSpan=1 tableCellRowSpan=1
(exit 0)
```

- ★★ **`#c24` 가 `tableCellRowSpan=0`** 이다 — 속성 값 `0` 을 **그대로** 높이로 적었다. 명세의 「0 이면 자라는 칸, 높이는 1 로 두고 행마다 늘린다」가 **트리 좌표에는 반영되지 않았다.**
- ★ **`#c34` 가 `tableCellColumnIndex=4`** — `#c24` 와 **같은 열**이다. 화면에서는 어떤지 (5) 가 잰다.
- **행이 `rowGroup` 없이 표에 붙어 있다** — 속성 없는 `tbody` 는 트리에서 빠진다([17번 주제](../17-table-structure/2-summary.md) (6)). `thead` 의 `rowGroup` 은 남았다.

### (5) 창 ② — `rowspan=0` 은 화면에서 늘어나는데 트리는 안 늘었다

**언제 쓰나** — 「`rowspan=0` 은 끝까지 늘어난다」를 믿기 전에.

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '71,76p'
(마) 창 ② — rowspan=0 인 #c24 와 이웃의 화면 상자(위·높이 px), 그리고 #c34 의 가로 순서
  #c23  top = 90 · height = 26 · left = 100
  #c24  top = 90 · height = 54 · left = 128
  #c33  top = 118 · height = 26 · left = 100
  #c34  top = 118 · height = 26 · left = 156
  #c34 의 left 가 #c24 의 left 와 같은가 = false
(exit 0)
```

```text
  같은 칸, 두 창

                 화면 (창 ②)                         트리 (내부 덤프)
  #c24           top 90 · height 54 (두 행)           RowSpan = 0
  #c34           left 156  (c24 의 오른쪽)            ColumnIndex = 4  (c24 와 같은 열)

  화면은 명세대로 늘렸고, 트리는 늘리지 않았다 — 한 브라우저 안에서 두 모델이 갈렸다.
```

- ★★★ **화면에서는 늘어났다** — `#c24` 의 높이가 이웃(26)의 두 배 남짓(54)이고, `#c34` 는 `#c24` **오른쪽**(left 156 > 128)으로 밀렸다. **레이아웃은 명세 표 모델과 같다.**
- ★★★ **트리는 안 늘렸다**((4)). 그래서 트리의 `#c34` 는 **화면에서 오른쪽에 있는데 같은 열 번호**를 받았다 — **Chrome 안에서 레이아웃과 접근성 트리가 다른 모델을 쓴 것**이다.
- ★ px 는 글꼴에 매인다. 근거는 마지막 줄의 **`false`**(같은 left 가 아니다)다.

### (6) 명세 계산 × 트리 재료 — 머리 배정과 「우연히 맞는 칸」

**언제 쓰나** — 「트리에 좌표와 역할이 있으니 머리는 거기서 셀 수 있다」고 생각할 때.

(3) 의 두 표에서 글자가 있는 데이터 칸 열다섯마다 — **명세 알고리즘이 배정한 머리**와 **트리의 좌표·역할로 센 단순 규칙**(같은 행에 걸친 `rowheader` + 같은 열에 걸친 `columnheader`)을 나란히 두고 **같은 칸**을 셌다.

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '29,45p'
(나) 첫 표 — 글자가 있는 데이터 칸마다 머리: 명세 알고리즘(스크립트) 대 「트리 재료로 셈한 단순 규칙」(같은 행 rowheader + 같은 열 columnheader)
  #c21                              명세 = 서울 상                    단순 규칙 = 상 m1 서울                 다름
  #c22    headers="서울 m2 상"         명세 = 서울 m2 상                 단순 규칙 = 상 m2 서울                 같음
  #c23                              명세 = 서울 하                    단순 규칙 = 하 m7 서울                 다름
  #c24                              명세 = 서울 인천 하                 단순 규칙 = 하 m8 서울                 다름
  #c31    headers="m1 인천"           명세 = m1 인천                   단순 규칙 = 상 m1 인천                 다름
  #c32    headers="m2 서울"           명세 = m2 서울                   단순 규칙 = 상 m2 인천                 다름
  #c33    headers="없는아이디"           명세 = —                       단순 규칙 = 하 m7 인천                 다름
  #c34                              명세 = 인천                      단순 규칙 = 하 m8 인천                 다름
  #c41                              명세 = 상                       단순 규칙 = 상 m1 부산                 다름
  #c42                              명세 = 상                       단순 규칙 = 상 하 m2 m7 부산            다름
  #c44                              명세 = 하                       단순 규칙 = 하 m8 부산                 다름
  #c51                              명세 = 상                       단순 규칙 = 상 m1 부산                 다름
  #c52                              명세 = 상                       단순 규칙 = 상 m2 부산                 다름
  #c53                              명세 = 하                       단순 규칙 = 하 m7 부산                 다름
  #c54                              명세 = 하                       단순 규칙 = 하 m8 부산                 다름
  머리가 같은 칸 = 1 / 15 · 그중 headers 속성이 있는 칸 = 1
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '47,64p'
(다) 둘째 표(모서리 th) — 같은 머리 격자와 두 요약
  #c21_2                            명세 = 서울_2 m1_2 상_2           단순 규칙 = 상_2 m1_2 서울_2           같음
  #c22_2  headers="서울_2 m2_2 상_2"   명세 = 서울_2 m2_2 상_2           단순 규칙 = 상_2 m2_2 서울_2           같음
  #c23_2                            명세 = 서울_2 m7_2 하_2           단순 규칙 = 하_2 m7_2 서울_2           같음
  #c24_2                            명세 = 서울_2 인천_2 m8_2 하_2      단순 규칙 = 하_2 m8_2 서울_2           다름
  #c31_2  headers="m1_2 인천_2"       명세 = m1_2 인천_2               단순 규칙 = 상_2 m1_2 인천_2           다름
  #c32_2  headers="m2_2 서울_2"       명세 = m2_2 서울_2               단순 규칙 = 상_2 m2_2 인천_2           다름
  #c33_2  headers="없는아이디_2"         명세 = —                       단순 규칙 = 하_2 m7_2 인천_2           다름
  #c34_2                            명세 = 인천_2                    단순 규칙 = 하_2 m8_2 인천_2           다름
  #c41_2                            명세 = 부산_2 m1_2 상_2           단순 규칙 = 상_2 m1_2 부산_2           같음
  #c42_2                            명세 = 부산_2 m2_2 m7_2 상_2      단순 규칙 = 상_2 하_2 m2_2 m7_2 부산_2  다름
  #c44_2                            명세 = 부산_2 m8_2 하_2           단순 규칙 = 하_2 m8_2 부산_2           같음
  #c51_2                            명세 = 부산_2 m1_2 상_2           단순 규칙 = 상_2 m1_2 부산_2           같음
  #c52_2                            명세 = 부산_2 m2_2 상_2           단순 규칙 = 상_2 m2_2 부산_2           같음
  #c53_2                            명세 = 부산_2 m7_2 하_2           단순 규칙 = 하_2 m7_2 부산_2           같음
  #c54_2                            명세 = 부산_2 m8_2 하_2           단순 규칙 = 하_2 m8_2 부산_2           같음
  머리가 같은 칸 = 9 / 15 · 그중 headers 속성이 있는 칸 = 1
  좌표 칸 갈림 = 2 / 100 · 역할 칸 갈림 = 0 / 25 · 표 크기 명세 6x6 / 트리 5x6
(exit 0)
```

```text
  「머리가 같은 칸」을 셀 때 빠지는 함정 — 첫 표 1 / 15, 둘째 표 9 / 15

  같은 칸                               왜 같은가
  #c22 (headers="서울 m2 상")           ★ 우연 — 단순 규칙은 headers 를 읽지 않는다.
                                           손으로 적은 목록이 마침 위·왼쪽 머리와 같았을 뿐이다
  둘째 표의 나머지 8칸                   명세의 훑기와 단순 규칙이 같은 길을 간다
                                           (헤더가 칸의 바로 위·바로 왼쪽에 있고 정직하게 th 다)

  다른 칸                               왜 다른가
  #c31 #c32 #c33 (headers 있음)          명세는 목록만 쓴다 — 없는 id 는 빠져 「—」
  #c24                                   트리의 RowSpan 0 이 인천을 못 덮는다
  #c34                                   명세 x=5 위에는 열 머리가 없다(인천만) — 트리 x=4 는 m8·하 아래
  #c42 (colspan 2)                       명세: 칸이 「걸친」 열 묶음이 아니라 「닻 내린」 열 묶음만 본다
  첫 표의 나머지                         모서리 td 때문에 명세 쪽 1월~8월·부산이 머리가 아니다
```

- ★★★ **첫 표는 1 / 15 가 같고, 그 한 칸이 우연이다.** `#c22` 는 `headers` 로 **위·왼쪽 머리를 그대로 적어 둔 칸**이라, `headers` 를 **아예 읽지 않는** 단순 규칙과 우연히 같았다. **이 칸으로 「`headers` 가 반영됐다」를 확인하면 틀린다.**
- ★★ **둘째 표(모서리 `th`)는 9 / 15 가 같다 — 그중 `headers` 가 있는 칸은 역시 `#c22` 하나다.** 모서리를 `th` 로 바꾸자 1월\~8월·부산이 명세로도 머리가 되어, **머리가 바로 위·바로 왼쪽에 있는 평범한 칸 8개**가 같아졌다.
- ★★ **`headers` 를 쓴 칸은 명세가 목록만 쓴다.** `#c31`(`m1 인천`)은 열 묶음 머리 `상` 이 **빠진다** — 자동 판정이 통째로 꺼지기 때문이다. `#c32`(`m2 서울`)는 **다른 행의 `서울`** 을 머리로 받는다 — 명세는 위치를 따지지 않는다. `#c33`(`없는아이디`)은 **머리가 하나도 없다** — 경고도 없다.
- ★ **`#c42` 가 드러낸 명세의 결** — 두 열(x=2\~3)에 걸친 칸인데, 명세의 열 묶음 단계는 **「닻 내린(anchored) 열 묶음」** 하나(x=1\~2, `상`)만 본다. 위로 훑기는 두 열을 다 훑어 `m2`·`m7` 을 얻는다. 그래서 **`상` 은 있고 `하` 는 없다.**
- ★★★ **어느 칸도 「트리가 보고한 머리」가 아니다.** 단순 규칙 열은 **트리의 재료로 사람이 센 것**이다. Chrome 이 보조 기술에 실제로 넘기는 머리 목록은 **플랫폼 API 층**이라 이 판에서 못 본다((1)).

### (7) 창 ⑦ — Chrome 은 「레이아웃 표」를 따로 판정한다

**언제 쓰나** — 배치용으로 쓴 옛 표를 만났을 때 · `role="presentation"` 을 줄지 말지 정할 때.

표 열 개에 **데이터 표의 표지**를 하나씩 더하거나 빼고 트리의 역할을 찍었다.

```html
<!-- html17b-18-layout.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 레이아웃 표 판정</title>
<style>.선 td { border: 1px solid black; }</style>
</head>
<body>
<table id="t1"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t2"><tr><td>1</td><td>2</td><td>3</td></tr><tr><td>4</td><td>5</td><td>6</td></tr><tr><td>7</td><td>8</td><td>9</td></tr></table>
<table id="t3" border="1"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t4" class="선"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t5"><tr><th>머리</th><td>오른쪽</td></tr></table>
<table id="t6"><caption>캡션</caption><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t7" role="table"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t8" role="presentation"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t9" role="presentation"><caption>캡션</caption><tr><th>머리</th><td>오른쪽</td></tr></table>
<table id="t10"></table>
<script>
const 설명 = { t1: "td 만 1행 2칸", t2: "td 만 3행 3칸", t3: "td 만 + border=1", t4: "td 만 + CSS 테두리",
  t5: "th 하나", t6: "caption 하나", t7: "td 만 + role=table", t8: "td 만 + role=presentation",
  t9: "caption·th + role=presentation", t10: "td 만 25행 2칸" };
for (let i = 0; i < 25; i++) document.getElementById("t10").insertRow().append(
  Object.assign(document.createElement("td"), { textContent: "가" }), Object.assign(document.createElement("td"), { textContent: "나" }));
const 표 = Object.keys(설명);
for (const k of 표) document.querySelector("#" + k + " td").id = k + "셀";
window.__대상 = 표.flatMap(k => [[k, "#" + k], [k + "셀", "#" + k + "셀"]]);
window.__내부 = true;
window.__끝 = () => {
  const O = ["표마다 — CDP 역할(표 · 첫 td) · 내부 덤프 역할(표 · 첫 td) · 무시 여부"];
  let 데이터 = 0;
  for (const k of 표) {
    const a = __AX[k], c = __AX[k + "셀"];
    const 내 = n => !n ? "(덤프에 없음)" : n.속성.ignored ? "(무시)" : n.역할, i = 내(__INT[k]), ic = 내(__INT[k + "셀"]);
    if (i === "table") 데이터++;
    O.push("  " + 설명[k].padEnd(32) + "CDP 표 = " + (a.무시 ? "(무시)" : a.역할).padEnd(13) + "첫 td = " + (c.무시 ? "(무시)" : c.역할).padEnd(17)
      + "내부 표 = " + i.padEnd(12) + "첫 td = " + ic);
  }
  O.push("");
  O.push("내부 덤프가 table 로 판정한 표 = " + 데이터 + " / " + 표.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-18-layout.html
표마다 — CDP 역할(표 · 첫 td) · 내부 덤프 역할(표 · 첫 td) · 무시 여부
  td 만 1행 2칸                      CDP 표 = LayoutTable  첫 td = LayoutTableCell  내부 표 = layoutTable 첫 td = layoutTableCell
  td 만 3행 3칸                      CDP 표 = LayoutTable  첫 td = LayoutTableCell  내부 표 = layoutTable 첫 td = layoutTableCell
  td 만 + border=1                 CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell
  td 만 + CSS 테두리                  CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell
  th 하나                           CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell
  caption 하나                      CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell
  td 만 + role=table               CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell
  td 만 + role=presentation        CDP 표 = (무시)         첫 td = generic          내부 표 = (덤프에 없음)    첫 td = genericContainer
  caption·th + role=presentation  CDP 표 = (무시)         첫 td = generic          내부 표 = (덤프에 없음)    첫 td = genericContainer
  td 만 25행 2칸                     CDP 표 = table        첫 td = cell             내부 표 = table       첫 td = cell

내부 덤프가 table 로 판정한 표 = 6 / 10
(exit 0)
```

```text
  세 갈래

  Chrome 이 스스로 「레이아웃 표」로 본 것      LayoutTable / LayoutTableCell
     td 만 1행 2칸 · td 만 3행 3칸
  표지 하나로 「데이터 표」가 된 것             table / cell
     border=1 · CSS 테두리 · th · caption · role=table · 25행
  role=presentation                            표 노드가 사라지고 칸은 generic
     caption·th 가 있어도 그렇다
```

- ★★★ **`th` 도 `caption` 도 없는 작은 표는 `LayoutTable` 이 됐다** — 저자가 아무것도 안 했는데 **Chrome 이 휴리스틱으로 판정**했다. 칸은 `cell` 이 아니라 `LayoutTableCell` 이다.
- ★★ **명세는 휴리스틱을 정하지 않는다.** 「이 명세는 정확한 휴리스틱을 정의하지 않는다」고 적고 **표지 목록**만 준다 — `role=presentation`·`border="0"` 은 「아마 레이아웃」, `caption`·`thead`·`th`·`headers`·`scope`·**0 이 아닌 `border`**·**CSS 로 보이는 테두리**는 「아마 데이터」. 이 판의 판정이 그 표지와 **어긋나지 않았다.** ★ **25행이면 데이터 표**가 된 것은 목록에 없는 **구현의 기준**이다.
- ★★ **`role="presentation"` 은 표 노드를 트리에서 지운다** — 칸은 `generic` 이 된다. ★ **`caption`·`th` 가 있어도 지운다**(`caption·th + role=presentation`). 저자가 명시한 역할이 표지를 이긴다.
- ★ **`role="table"` 은 휴리스틱을 이긴다** — `td` 만 1행 2칸이어도 `table` 이다.
- ★★ **「레이아웃 표는 접근성에 나쁘다」를 이 판이 보인 만큼만 적는다** — 트리에서 **표·칸의 역할이 바뀌거나 사라진다**까지다. 보조 기술이 그 표를 어떻게 읽는지는 못 본다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 위 소스가 전부 실제로 던진 형태다.

| 속성 | 요소 | 값 | 명세가 하는 일 |
|---|---|---|---|
| `scope` | `th` | `row`·`col`·`rowgroup`·`colgroup` · 그 밖은 **auto** | 머리 **종류**를 정한다((2)) |
| `headers` | `td`·`th` | 공백으로 가른 **`id` 목록** | 지정하면 **자동 배정을 통째로 대신한다**((6)) |
| `abbr` | `th` | 글자 | 「다른 맥락에서 이 머리를 부를 때」의 짧은 이름 — 트리에는 흔적이 없다((1)) |
| `colspan` | `td`·`th` | 1\~1000(0·무효는 1) | 칸의 폭 |
| `rowspan` | `td`·`th` | 0\~65534 · **0 = 행 묶음 끝까지** | 칸의 높이 — 트리는 0 을 늘리지 않았다((4)·(5)) |
| `span` | `col`·`colgroup` | 1\~1000 | 열 묶음의 폭 — `scope=colgroup` 이 이것을 본다 |

### 어디서 헷갈리나

- **`headers` 는 `scope` 의 보충이 아니라 대체다.** 쓰면 그 칸은 **위·왼쪽을 안 본다.** 열 묶음 머리도 빠진다(`#c31`).
- **`scope=colgroup` 은 `<colgroup>` 이 있어야 뜻이 있다.** 명세의 열 묶음 단계는 **칸이 닻 내린 열 묶음** 안의 열 묶음 머리만 더한다.
- **빈 모서리는 `<td>` 가 아니라 `<th>` 로** — 비어 있는 머리 칸은 명세의 「빈 칸 제거」 단계가 머리 목록에서 **빼 준다**(명세 문장 — 이 판의 표에서는 그 단계가 걸러 낸 칸이 없었다). `<td>` 로 쓰면 **같은 행·열의 자동 머리를 깨뜨린다**((3)).

## 어디서 틀리나

### 1. 빈 모서리를 `<td>` 로 쓴다

**명세로는 그 행의 `th` 넷과 그 열의 `th` 하나가 머리가 아니게 된다**((3) — 역할 5칸 갈림).\
Chrome 의 트리는 그래도 `columnheader`·`rowheader` 를 줘서 **화면에서도 트리에서도 안 보인다.**

```text
  <thead><tr><td></td><th>1월</th>…            <- 명세: 1월은 「아님」(cell)
  <thead><tr><th></th><th>1월</th>…            <- 명세: 1월은 열 머리
```

★ 처방은 **`<th>` 로 쓰거나 `scope=col`/`row` 를 명시**하는 것이다 — 명시한 칸은 모서리의 영향을 안 받았다.

### 2. `headers` 를 부분적으로 쓴다

**그 칸만 자동 배정이 꺼진다**((6) — `#c31` 에서 `상` 이 빠졌다). 섞어 쓰면 **칸마다 규칙이 다른 표**가 된다.\
★ `headers` 는 **복합 표 전체를 손으로 설계할 때** 쓰고, 그때는 **모든 머리를 목록에 넣는다.**

### 3. `headers` 의 `id` 오타

**경고 없이 머리가 사라진다**((6) — `#c33` 은 「—」). 명세가 「같은 표의 칸이면 더한다」라서 **없으면 조용히 건너뛴다.**

### 4. 트리의 좌표·역할을 보고 머리를 짐작한다

**우연히 맞는 칸이 있다**((6) — `#c22`). `headers` 를 옳게 쓴 칸은 **그 속성을 무시해도 같은 답**이 나온다.\
★ `headers` 가 반영되는지를 확인하려면 **위·왼쪽 머리와 다른 목록**을 적은 칸(`#c32`)을 봐야 한다 — 그리고 그 답은 **플랫폼 API 층**에 있어 이 판에서는 못 본다.

### 5. `rowspan="0"` 으로 「끝까지」를 맡긴다

**화면은 늘어나고 트리는 안 늘어난다**((5)). 트리의 옆 칸 좌표가 **한 열씩 어긋난다.**\
★ 행 수가 정해져 있으면 **숫자로** 쓴다.

### 6. `th` 없이 `td` 만으로 표를 만든다

**Chrome 이 레이아웃 표로 판정할 수 있다**((7) — `LayoutTable`). `th`·`caption` 하나면 데이터 표가 된다.

## 구현 세부사항 대 언어 보장

★ 세 층으로 갈라 적는다 — **명세(WHATWG HTML · HTML-AAM)가 보장하는 것 / Chrome 151 이 구현한 것 / 이 판에서 관찰한 것.**

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML 표 처리 모델)** | 칸 좌표 · `rowspan=0` 의 자람 · 열·행 머리의 자동 판정 · 머리 칸 배정 알고리즘 | (2)·(3)·(6) — **스크립트로 옮긴 계산** |
| **명세(HTML-AAM)** | `th` → `columnheader`/`rowheader`/**`cell`**(어느 머리도 아니면) · `headers`·`abbr` → **플랫폼 API 만**(ARIA 층 Not mapped) | (1)·(2) |
| **명세(HTML)** | 레이아웃 표 휴리스틱은 **정의하지 않는다** — 표지 목록만 | (7) |
| **구현(Chrome)** | 「어느 머리도 아닌 `th`」에 **`rowheader`** | (2)·(3) — ★ 명세와 갈렸다(6칸) |
| **구현(Chrome)** | 트리 좌표에서 **`rowspan=0` 을 0 그대로** — 레이아웃은 늘린다 | (4)·(5) — ★ 명세와 갈렸다 · 브라우저 안에서도 갈렸다 |
| **구현(Chrome)** | 레이아웃 표 판정 — `th`·`caption`·테두리 없는 작은 표 → `LayoutTable` · 25행 → `table` | (7) |
| **이 판의 관찰** | (5) 의 px | 글꼴이 바뀌면 절댓값은 바뀐다 |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 칸을 어떻게 읽는지**(「3행 2열, 2월, 서울, 6」) | 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 트리는 보조 기술의 **입력**이지 출력이 아니다 |
| ★★★ **Chrome 이 칸마다 넘기는 머리 목록**(`columnHeaderCells` 류) | **플랫폼 API 층**이다. CDP·내부 덤프는 그 위 층이라 **자리가 없다**((1)) — **「못 잰 것」(제3의 상태)**. 그래서 Chrome 이 `headers` 를 존중하는지 **이 문서는 판정하지 않는다** |
| **`abbr` 이 실제로 쓰이는지** | 같은 층이다 |
| **다른 엔진의 자동 판정·레이아웃 표 판정** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **단순한 표(머리 한 줄·한 열)는 `th` 만** — 자동 판정으로 충분하고 이 판의 트리도 그대로 따랐다.
- **모서리는 `<th>`**, 머리 방향이 애매하면 **`scope` 를 명시** — 명시한 칸은 명세·트리 어디서도 안 갈렸다.
- **두 줄 머리(상반기/1월)는 `<colgroup>` + `scope=colgroup`** — `span` 을 칸과 맞춘다.
- **`headers` 는 자동 배정으로 안 되는 표에만, 쓸 거면 전부** — 부분 사용은 칸마다 규칙을 바꾼다.
- **`rowspan=0` 은 쓰지 않는다** — 트리 좌표가 어긋난다.
- **배치에 표를 쓰지 않는다** — 불가피하면 `role="presentation"` 으로 표 역할을 걷어 낸다. 데이터 표에는 절대 주지 않는다(`caption`·`th` 가 있어도 지운다).

## 핵심 문장

1. **「이 칸의 머리」는 CDP 트리에도 내부 덤프에도 없다 — HTML-AAM 이 `headers` 를 ARIA 층에 「Not mapped」로 두고 플랫폼 API 로만 넘기기 때문이다.**
2. **`scope` 없는 `th` 20개 중 명세와 트리의 역할이 갈린 것은 1개 — 행에도 열에도 `td` 가 있는 가운데 `th` 를 Chrome 은 `rowheader` 로 봤다.**
3. **빈 모서리 `<td>` 하나가 명세로는 같은 행·열의 `th` 다섯을 머리에서 떨어뜨린다 — 트리는 그대로 머리로 둔다.**
4. **`rowspan=0` 은 화면에서는 끝까지 늘어나고 트리 좌표에서는 0 그대로다 — 한 브라우저 안에서 두 모델이 갈렸다.**
5. **`headers` 는 자동 배정을 대체한다 — 쓰면 열 묶음 머리도 빠지고, 없는 `id` 는 조용히 사라진다.**
6. **트리 재료로 센 머리가 명세와 맞는 칸에는 우연이 섞인다 — `headers` 를 위·왼쪽 그대로 적은 칸은 그 속성을 무시해도 맞는다.**
7. **Chrome 은 `th`·`caption`·테두리 없는 작은 표를 `LayoutTable` 로 판정하고, `role="presentation"` 은 표 노드를 지운다.**

## 관련 자료

- [17번 주제 — 표 구조](../17-table-structure/2-summary.md) — **표 처리 모델의 좌표**와 행 묶음·열 묶음이 거기서 나왔다. `tbody` 가 트리에서 빠지는 것도 그쪽 (6).
- [13번 주제 — 구절 시맨틱](../13-phrasing-semantics/2-summary.md) — `Abbr` 처럼 **명세의 빈자리를 Chrome 이 채운 역할**을 처음 잡은 편. 여기의 「어느 머리도 아닌 `th` → `rowheader`」가 같은 집안이다.
- [15번 주제 — 목록](../15-lists/2-summary.md) — **「우연히 맞는 칸을 세는 격자」**(`li.value` 4 / 27)의 원형. 여기 (6) 이 같은 기법이다.
- 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) — `role="presentation"`·`role="table"` 로 **암묵 역할을 덮어쓰는 규칙 전체**는 그쪽이 정본이다. 여기는 **표 노드가 사라진다**는 결과까지.
- 목록의 **43번 주제**(접근 가능한 이름 계산) — 칸의 이름이 **내용에서 오는 규칙**은 그쪽이 정본이다.

## 용어 풀이

- **열 머리 / 행 머리(column / row header)** — 명세가 `th` 를 분류한 이름. `scope` 또는 자동 판정이 정한다.
- **열 묶음 머리 / 행 묶음 머리** — `scope=colgroup`/`rowgroup` 인 `th`.
- **데이터 칸(data cell)** — `td`. 비어 있어도 데이터 칸이다.
- **머리 칸 배정(assigning header cells)** — 칸마다 머리 목록을 만드는 명세 알고리즘. `headers` 가 있으면 목록, 없으면 위·왼쪽 훑기 + 묶음 머리.
- **닻 내린 칸(anchored)** — 칸의 왼쪽 위 슬롯. 여러 슬롯을 덮는 칸도 **닻은 하나**다.
- **자라는 칸(downward-growing cell)** — `rowspan=0` 인 칸. 행 묶음이 끝날 때까지 늘어난다.
- **레이아웃 표(layout table)** — 배치용으로 쓴 표. 명세는 판정 기준을 정하지 않고, Chrome 은 `LayoutTable` 역할로 표시한다.
- **플랫폼 API** — 운영체제의 접근성 인터페이스(IAccessible2·UIA·ATK·AX). 보조 기술이 실제로 읽는 층이다.

## 더 들어가면

- **왜 명세는 「어느 머리도 아닌 `th`」를 허용하나** — 표 처리 모델은 **오류를 거부하지 않고 해석한다.** 파서가 태그 수프를 트리로 만들 듯, 표 모델도 어떤 표든 칸마다 답을 낸다. 그 답이 「머리 없음」일 수 있을 뿐이다.
- **불투명 머리(opaque headers)** — 배정 알고리즘의 훑기는 **데이터 칸을 지나면 그 앞의 머리 덩어리를 「불투명」으로** 적어 두고, 같은 폭·높이의 머리를 막는다. 머리 블록이 여러 번 나오는 표에서 **가까운 블록만** 머리가 되게 하는 장치다. 이 판에서 따로 재지 않았다.
- **`summary` 와 `abbr` 의 운명** — 둘 다 「표를 소리로 읽을 때」를 위해 생긴 속성이다. `summary` 는 비준수가 됐고 `abbr` 은 남았다. 둘 다 트리에 흔적이 없다는 것까지가 이 판의 관찰이다(`abbr` — (1)).
