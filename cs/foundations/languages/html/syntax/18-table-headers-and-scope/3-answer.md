# html/syntax/18 — 표 머리 연결: `th`·`scope`·`headers`/`id`·`rowspan`/`colspan` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(`html17b-cdp.py`·`capture.sh`)는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/tables.html#table-processing-model) 의 표 처리 모델과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **명세 쪽 답은 모델 스크립트의 계산이고, Chrome 쪽 답은 트리의 좌표·역할이다.** 「이 칸의 머리」를 트리가 보고하지는 않는다(A7).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 갈린 칸 1 / 20 — 가운데 `th` 를 명세는 「아님」(cell), Chrome 은 `rowheader` 로 봤다

**출력**

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

**왜 그런가**

- ★★★ **N = 1** — 「가운데 `th`」(`#d1`). 그 `th` 가 걸친 **행에 `td` 가 있어** 열 머리가 아니고, 걸친 **열에도 `td` 가 있어** 행 머리도 아니다. HTML-AAM 의 `th` 첫 줄이 그런 `th` 에 **`cell`** 을 준다. **Chrome 은 `rowheader`** — 명세 ↔ 구현 불일치다.
- ★ **`th` 만 있는 표의 둘째 행 `th` 도 열 머리**다. 명세의 열 머리 조건(「걸친 행에 데이터 칸이 없다」)이 **행 머리 조건보다 먼저** 검사되고, 그 표에는 `td` 가 없다.
- **`scope="위"` 는 Auto** — `scope` 의 누락 기본값과 무효 기본값이 둘 다 Auto 다. 첫 열이라 행 머리가 됐다.
- **`scope` 를 명시한 칸은 전부 안 갈렸다** — 첫 행의 `scope=row` 는 `rowheader`, 첫 열의 `scope=col` 은 `columnheader`.

### 2. 좌표 2 / 100 · 역할 5 / 25 · 명세 6×6 대 트리 5×6 — 역할은 빈 모서리 `td` 에서, 좌표는 `rowspan=0` 에서 갈렸다

**출력**

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

**왜 그런가**

- ★★ **좌표가 갈린 칸은 `#c24`(높이 2 대 0)와 `#c34`(x 5 대 4)** — 명세의 `rowspan=0` 은 「자라는 칸」이라 y=3 까지 덮고, 그래서 `#c34` 가 x=5 로 밀려 **표가 6열**이 된다. 트리는 그 칸을 안 늘렸다.
- ★★★ **역할이 갈린 칸은 `1월`·`2월`·`7월`·`8월`·`부산`** — 전부 **빈 모서리 `<td>`** 때문이다. 모서리는 **데이터 칸**이라 y=0\~1 행과 x=0 열에 데이터 칸이 생긴다. 그래서 명세로는 그 넷이 열 머리가 아니고, `부산` 이 행 머리가 아니다 — 모두 「아님」→ `cell`. Chrome 은 `columnheader`·`rowheader`.
- **`scope` 를 명시한 `상반기`·`하반기`·`서울`·`인천` 은 안 갈렸다.**

### 3. 트리는 `tableCellRowSpan=0`, 화면은 두 행 높이 — `#c34` 는 화면에서 오른쪽, 트리에서 같은 열

**출력**

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

**왜 그런가**

- ★★ **트리의 `#c24` 는 `tableCellRowSpan=0`** — 속성 값을 그대로 적었다.
- ★★★ **화면의 `#c24` 는 두 행 높이**(height 54 — 이웃은 26), **`#c34` 는 `#c24` 의 오른쪽**(left 156 > 128)이다. **레이아웃은 명세 표 모델대로** 늘렸다.
- ★★★ **트리의 `#c34` 는 4번 열** — `#c24` 와 같은 열이다. 한 브라우저 안에서 **레이아웃과 접근성 트리가 다른 표 모델을 썼다.**

### 4. 첫 표는 1 / 15 가 같고, 그 한 칸(`#c22`)이 `headers` 를 가진 칸이다

**출력**

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

**왜 그런가**

- **명세** — `#c21` = 서울 · 상 / `#c24` = 서울 · 인천 · 하 / `#c31` = m1 · 인천 / `#c32` = m2 · 서울 / `#c33` = 없음 / `#c41` = 상 / `#c42` = 상.
  - `#c21`·`#c41` — 위로 훑다 만난 `1월` 은 **「아님」이라 막히고**, 열 묶음 단계가 `상` 을 더한다. `#c41` 은 왼쪽의 `부산` 도 **행 머리가 아니라 막힌다.**
  - `#c24` — 두 행을 덮으므로 왼쪽 훑기를 **두 번**(y=2·3) 해서 `서울`·`인천` 을 다 얻는다.
  - `#c31`·`#c32`·`#c33` — `headers` 가 있어 **목록만** 쓴다. `#c32` 는 **다른 행의 `서울`** 을 받고, `#c33` 은 없는 `id` 라 **빈 목록**이다.
  - `#c42` — 두 열에 걸쳤지만 열 묶음 단계는 **닻 내린 열 묶음(x=1\~2)의 `상`** 만 본다.
- **단순 규칙** — 트리 역할이 전부 머리이므로 **같은 열의 `columnheader` 둘(묶음 + 월) + 같은 행의 `rowheader`** 가 붙는다. `headers` 는 읽지 않는다.
- ★★★ **같은 칸 1 / 15, 그중 `headers` 있는 칸 1** — 그 칸 `#c22` 는 `headers="서울 m2 상"` 으로 **위·왼쪽 머리를 그대로** 적었다. 단순 규칙은 `headers` 를 무시하고도 같은 답을 냈다 — **우연이다.**

### 5. 역할 0 / 25 · 좌표 2 / 100 — 같은 칸 9 / 15, `headers` 칸은 여전히 하나

**출력**

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

**왜 그런가**

- ★★ **역할이 0 / 25** 로 떨어졌다 — 모서리가 **머리 칸**이 되자 y=0\~1 행과 x=0 열에서 데이터 칸이 사라졌다. `1월`\~`8월` 은 열 머리, `부산` 은 행 머리다. ★ **좌표 2 / 100 은 그대로** — `rowspan=0` 은 모서리와 무관하다.
- ★★ **같은 칸 9 / 15** — 머리가 바로 위·바로 왼쪽에 있는 평범한 칸 8개 + `#c22`. **`headers` 가 있는 칸은 여전히 `#c22` 하나**다.
- **다른 여섯 칸의 이유** — `#c24`(트리 높이 0 이 `인천` 을 못 덮는다) · `#c31`·`#c32`·`#c33`(`headers` 목록만 — 단순 규칙은 목록을 안 읽는다) · `#c34`(명세 x=5 에는 열 머리가 없다 · 트리 x=4 는 `8월` 아래) · `#c42`(명세는 닻 내린 열 묶음 하나만).

### 6. 6 / 10 이 `table` — 작은 `td` 전용 표 둘은 `LayoutTable`, `role="presentation"` 은 표 노드를 지운다

**출력**

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

**왜 그런가**

- ★★★ **N = 6** — `td` 만 1행 2칸·3행 3칸은 **`LayoutTable`/`LayoutTableCell`**, `role="presentation"` 둘은 **표 노드가 무시**되고 칸이 `generic` 이다.
- ★★ **표지 하나로 데이터 표가 된다** — `border=1` · CSS 테두리 · `th` · `caption` · `role=table`. 명세의 「아마 데이터 표」 표지 목록과 어긋나지 않는다. **25행**이 데이터 표가 된 것은 명세 목록에 없는 **구현 기준**이다.
- ★ **`role="presentation"` 은 `caption`·`th` 가 있어도 표를 지웠다.** 저자가 준 역할이 표지를 이긴다 — 그래서 **데이터 표에 주면 표가 트리에서 사라진다.**

### 7. 셀 노드에는 머리 관계가 없다 — HTML-AAM 이 `headers` 를 ARIA 층에 두지 않는다

**출력**

```text
$ python3 html17b-cdp.py page html17b-18-grid.html | sed -n '66,69p'
(라) 트리가 셀 노드에 단 속성 — #c31(headers 있음) · #c21(없음) · #m2(abbr 있음)
  #c31  CDP properties = [] · 내부 덤프 속성 중 이름에 header 가 든 것 = []
  #c21  CDP properties = [] · 내부 덤프 속성 중 이름에 header 가 든 것 = []
  #m2   abbr="이월" · CDP 이름 = "2월" · CDP 설명 = "" · 내부 덤프 속성 중 이름에 abbr 가 든 것 = []
(exit 0)
```

**왜 그런가**

- ★★★ **CDP `properties = []`, 내부 덤프에 `header`·`abbr` 가 든 속성 없음** — `headers` 를 단 칸도, `abbr` 을 단 머리도 같다.
- ★★ **HTML-AAM 의 `headers` 줄** — WAI-ARIA 층은 **「Not mapped」**. 플랫폼 층은 IAccessible2 `IAccessibleTableCell::rowHeaderCells`·`columnHeaderCells` · UIA `Table.ItemColumnHeaderItems`·`ItemRowHeaderItems` · ATK `atk_table_get_row_header`/`column_header` · AX `AXColumnHeaderUIElements`·`AXRowHeaderUIElements`. `abbr` 도 AX 의 `AXDescription`·IA2/ATK 객체 속성이다.
- ★★★ **그래서 창을 바꿨다 — 제5의 상태가 둘이다.** 명세 쪽은 **알고리즘을 페이지 스크립트로 옮겨** 계산했고, Chrome 쪽은 **트리가 주는 재료(좌표·역할)** 로 단순 규칙을 셌다. **Chrome 이 실제로 넘기는 머리 목록은 「못 잰 것」(제3의 상태)** 이다.

### 8. 모서리가 데이터 칸이냐 머리 칸이냐가 「그 행·그 열에 데이터 칸이 있나」를 바꾼다

- **명세의 열 머리** — 「`scope` 가 Col 이거나, Auto 이고 **그 칸이 걸친 행들의 어느 칸도 데이터 칸이 아닐 것**」. **행 머리** — 「`scope` 가 Row 이거나, Auto 이고 열 머리가 아니며 **걸친 열들의 어느 칸도 데이터 칸이 아닐 것**」. 모서리 `<td>` 는 y=0\~1 과 x=0 에 **데이터 칸을 하나 만든다** — 그래서 2번 표는 넷이 열 머리가 아니고 `부산` 이 행 머리가 아니다. 5번 표는 그 데이터 칸이 없어 **전부 머리**다.
- **빈 `th` 는 목록에 안 들어간다** — 배정 알고리즘의 끝 단계 「**빈 칸을 목록에서 뺀다**」(요소가 없고 글자가 공백뿐인 칸). ★ 다만 이 표에서는 **어느 데이터 칸의 훑기도 모서리 슬롯에 닿지 않아** 그 단계가 실제로 걸러 낸 칸은 없다 — 5번 출력에 `모서리_2` 가 없는 것은 그 단계의 증거가 아니다. 명세 문장으로만 적는다.
- **`scope` 를 명시한 칸은 영향을 안 받는다** — 명시 상태에서는 자동 판정의 「데이터 칸이 있나」 검사를 하지 않는다. `상반기`·`서울` 이 두 표에서 같았다.

### 9. 명세와 갈린 자리는 셋 — 「아님」 th 의 역할 · `rowspan=0` 의 트리 좌표 · 그 좌표에 딸린 표 크기

- ★★ **「어느 머리도 아닌 `th`」 → 명세(HTML-AAM) `cell` · Chrome `rowheader`** — A1 의 `#d1`, A2 의 다섯 칸. 모두 명세의 열·행 머리 정의 + HTML-AAM `th` 첫 줄과 갈렸다.
- ★★ **`rowspan=0` → 명세 「행 묶음 끝까지 자란다」 · Chrome 트리 `RowSpan 0` · 옆 칸 x 한 칸 어긋남 · 표 크기 5×6** — A2·A3. 레이아웃은 명세와 같았다.
- ★★★ **4·5번의 같은 칸은 `headers` 반영의 근거가 못 된다.** `#c22` 는 `headers` 가 위·왼쪽 머리와 **같아서** 무시해도 맞는 칸 — 우연이다. 나머지 같은 칸은 `headers` 가 없다. 반영 여부를 가를 수 있는 칸은 목록이 다른 `#c31`·`#c32`·`#c33` 인데, 그 칸들의 Chrome 쪽 답은 **플랫폼 층**에 있어 못 봤다.
- **레이아웃 표 판정은 명세가 정하지 않는다** — 「정확한 휴리스틱을 정의하지 않는다」·「제안은 틀릴 수 있다」고 적는다. 판정은 **구현**이다.

### 10. 둘 다 못 한다 — 둘 다 플랫폼 층의 일이다

- **못 쓴다.** 보조 기술이 없고, 칸의 머리 목록 자체가 트리에 없다. 「2월, 서울」은 명세 계산이 **배정한 머리**일 뿐 **읽힌 소리**가 아니다.
- **판정 못 한다.** `headers` 반영은 **IAccessibleTableCell·UIA·ATK·AX** 의 머리 목록을 봐야 한다. 이 판의 headless 에는 그 층이 없다 — **「못 잰 것」**. 그래서 이 문서는 「Chrome 이 `headers` 를 무시한다/존중한다」를 **한 줄도 적지 않는다.**

### 11. 정본 경계

- **좌표·행 묶음** — [17번 주제](../17-table-structure/2-summary.md). 여기는 그 좌표 위에서 **머리를 배정하는 것**부터.
- **`role="presentation"` 으로 암묵 역할을 덮어쓰는 규칙** — 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나).
- **「우연히 맞는 칸」 격자의 원형** — [15번 주제](../15-lists/2-summary.md) (2) 의 `li.value` 가 표지 번호와 같은 칸 **4 / 27**(넷 다 우연).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★★ **보조 기술 없음.** NVDA·VoiceOver·Orca 가 설치돼 있지 않다.

**하네스** — [17번 주제](../17-table-structure/3-answer.md)의 `html17b-cdp.py` 를 그대로 쓴다. 이 주제는 **`page` 모드 + `window.__내부`** 로 CDP 역할과 **내부 덤프의 `tableCell*` 좌표**를 한 실행에 받고, **`int` 모드**로 덤프 원본을 찍는다.\
★★ **명세 모델**(`html17b-18-model.js`)은 [2-summary.md](2-summary.md) (3) 에 전문이 있다. **4.9.12.1 「표 만들기」**(열 묶음 · 행 처리 · 자라는 칸 · 미룬 `tfoot`)와 **4.9.12.2 「관계 맺기」**(`headers` 목록 · 두 방향 훑기와 불투명 머리 · 행 묶음·열 묶음 머리 · 빈 칸·중복·자기 자신 제거)를 옮겼다. ★ **근사가 한 곳 있다** — 「음이 아닌 정수 파싱 규칙」을 정규식 한 줄로 줄였다(이 주제의 속성 값은 전부 평범한 숫자다).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`th` 스무 개 격자** | 3 | 동작 방식 (2) · A1 |
| **복합 머리 표 격자**(좌표·역할·머리·속성·화면) | 3 | 동작 방식 (1)·(3)·(5)·(6) · A2\~A5·A7 |
| **내부 덤프 원본** | 3 | 동작 방식 (4) · A3 |
| **레이아웃 표 열 개** | 3 | 동작 방식 (7) · A6 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 「어느 머리도 아닌 `th`」의 역할 | **`rowheader`** | HTML-AAM 은 `cell` — 구현이 바뀔 수 있다 |
| 트리의 `rowspan=0` | **`tableCellRowSpan=0`**, 옆 칸 x 어긋남 | 레이아웃과 트리가 다른 모델 — 고쳐질 수 있다 |
| 레이아웃 표 판정 | 1행 2칸·3행 3칸 → `LayoutTable` · 25행 → `table` | 휴리스틱은 명세 밖이다 |
| 셀 노드의 머리 관계 | **없음** | CDP 가 속성을 늘리면 창 ⑦ 로 직접 물을 수 있게 된다 |

**안 돌려 본 것** — ① **Firefox·Safari 의 자동 판정·레이아웃 표 판정**(엔진이 없다). ② **불투명 머리가 갈리는 표**(머리 블록이 한 방향에 둘 이상) — 모델에는 옮겼으나 그 가지를 타는 표를 던지지 않았다. ③ **`th` 의 `headers`** — `td` 에만 줬다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **스크린리더의 표 읽기**(A10). ② **플랫폼 API 의 머리 목록 · `abbr`**(A7·A10) — 그 층이 이 판에 없다.

**부적용인 창** — **창 ①**(머리 연결 속성은 파서가 안 고친다 — 표 구조의 파서 동작은 17번) · **창 ③·④·⑤·⑥** — **잴 것이 없다.**

## 용어 풀이

- **열 머리 / 행 머리** — 명세가 `th` 를 나눈 종류. `scope` 또는 「걸친 행·열에 데이터 칸이 없나」로 정한다.
- **데이터 칸** — `td`. 비어 있어도 데이터 칸이다 — 이 주제의 급소.
- **머리 칸 배정** — 칸마다 머리 목록을 만드는 명세 알고리즘.
- **닻 내린 칸** — 칸이 덮는 슬롯 중 왼쪽 위. 열 묶음 단계는 이 슬롯의 열 묶음만 본다.
- **단순 규칙** — 이 문서가 트리 재료로 센 「같은 행의 `rowheader` + 같은 열의 `columnheader`」. **트리가 보고한 머리가 아니다.**
- **제5의 상태** — 같은 질문을 **다른 창으로 물은 것**. 이 주제는 명세 계산과 트리 재료, 둘로 물었다.
