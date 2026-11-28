# python/python-libraries/13 — Rich 출력 — 정리 (힌트)

> 출처 — study-site 항목 `python/rich-output`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/rich-output.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `rich` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Rich 는 「터미널용 인쇄소」다.**
평범한 `print` 가 흑백 복사기라면, Rich 의 `Console` 은 원고에 붙은 교정 기호(`[bold]`, `[red]`)를 읽고 색 · 굵기 · 표 · 테두리를 입혀 찍어 주는 인쇄소다.
원고에 「여기는 빨갛게」라고 적어 두면 인쇄소가 알아서 빨갛게 찍는다.
표 · 나무 그림 · 액자(테두리 상자) · 진행 막대 같은 「완성품 틀」도 미리 갖춰 두었다.
Rich 도 똑같은 구조다 — 우리는 내용과 표시만 넘기고, 그리는 일은 `Console` 이 맡는다.

| 비유 | 실체 |
|---|---|
| 인쇄소 | `Console` 객체 |
| 원고에 적은 교정 기호 | 마크업 태그 `[bold green]…[/bold green]` |
| 완성품 틀(표 · 나무 · 액자) | `Table` · `Tree` · `Panel` |
| 인쇄 주문 | `console.print(...)` |
| 진행 상황판 | `Progress` |

```text
  원고(문자열 · 객체)          인쇄소(Console)              터미널
 "[red]에러[/red] ..."  ──▶  태그 해석 · 틀 그리기  ──▶  색 입힌 글자, 표, 상자
  Table / Tree / Panel  ──▶                         ──▶
```

## 이 주제가 답하려는 질문

1. 문자열에 색과 굵기를 어떻게 입히나 — 태그로? 매개변수로? 둘을 같이 쓰면?
2. 표 · 트리 · 테두리 상자 · 진행 막대 같은 구조물을 어떤 순서로 조립해 출력하나?
3. 마크다운 문서와 소스 코드를 터미널에서 어떻게 보기 좋게 찍나?
4. 표준 `logging` 의 출력을 Rich 로 바꾸려면 무엇을 연결하나, 그때 무엇을 조심하나?

## 동작 방식

### (1) `Console` 과 마크업 태그

**언제 쓰나** — 성공 · 에러 · 정보 메시지에 색과 굵기를 입혀 눈에 띄게 할 때.

```text
console.print("[bold green]성공![/bold green] 작업이 완료되었습니다.")
        │
        ▼  Console 이 문자열 안의 [ ... ] 를 태그로 읽는다
  "성공!"  ← bold + green 적용
  " 작업이 완료되었습니다."  ← 스타일 없음
        │
        ▼
  터미널: 굵은 초록 「성공!」 + 보통 글씨 나머지
```

- `Console()` 을 한 번 만들고, 출력은 모두 이 객체의 `print` 로 보낸다.
- `console.print()` 는 문자열 안의 `[태그]…[/태그]` 를 자동으로 마크업으로 해석한다.
- 여는 태그에는 스타일 이름을 공백으로 여럿 적을 수 있다(`[bold green]`, `[italic cyan]`).
- 닫는 태그는 `[/bold green]` 처럼 이름을 다 써도 되고, `[/]` 로 줄여도 된다(팁의 `[bold red]태그[/]`).
- 색 이름(`red`, `green`, `yellow`, `cyan`, `magenta`, `blue`)과 꾸밈(`bold`, `italic`, `underline`, `strike`)을 쓸 수 있다.

> **마크업** — 글자 사이에 끼워 넣어 「이 부분을 어떻게 보일지」 지시하는 표시.\
> 예: `[underline]밑줄[/underline]` 은 「밑줄」만 밑줄을 긋는다.

### (2) `style` 매개변수 — 전체에 깔리는 스타일

**언제 쓰나** — 한 줄 전체에 공통 스타일을 깔고, 일부에만 태그로 더 얹을 때.

```text
console.print("[red]에러:[/red] 파일을 찾을 수 없습니다.", style="bold")
        │
        ▼  style="bold" 가 줄 전체에 깔린다
        ▼  그 위에 [red] 가 「에러:」 부분에만 얹힌다
  "에러:"                    ← bold + red
  " 파일을 찾을 수 없습니다." ← bold
```

- 원본 주석은 이것을 「중첩 적용」이라 부른다.
- 바닥 스타일(`style=`)과 태그 스타일이 겹치는 구간은 둘 다 적용된다.

### (3) `Table` — 열을 먼저, 행을 나중에

**언제 쓰나** — 서버 상태처럼 같은 항목을 여러 개 나란히 비교해 보일 때.

```text
Table(title="서버 상태")
   │
   ├─ add_column("서버",  style="cyan", no_wrap=True)    ← 열 정의 1
   ├─ add_column("상태",  style="magenta")               ← 열 정의 2
   ├─ add_column("CPU",   justify="right", style="green")
   ├─ add_column("메모리", justify="right", style="yellow")
   │
   ├─ add_row("web-01", "[green]Running[/green]", "23%", "45%")
   ├─ ...
   ▼
console.print(table)  →  제목 + 테두리 + 열마다 색 · 정렬이 적용된 표
```

- `Table(title=...)` 로 표를 만들고 제목을 단다.
- `add_column` 으로 열을 정의한다 — 열 이름, 열 전체의 `style`, 정렬 `justify`, 줄바꿈 금지 `no_wrap`.
- `justify="right"` 는 숫자 열을 오른쪽 정렬해 자릿수를 맞춘다.
- `add_row` 로 행을 넣는다 — 값의 개수는 열의 개수와 맞춘다.
- 셀 문자열 안에도 마크업을 쓸 수 있다(`"[red]Down[/red]"`).
- 테두리와 색은 출력할 때 자동으로 적용된다.

### (4) `Tree` — `add()` 가 돌려주는 자식 노드

**언제 쓰나** — 디렉터리 구조처럼 부모-자식 관계를 들여쓰기와 선으로 보일 때.

```text
tree   = Tree("프로젝트 구조")       ← 뿌리
src    = tree.add("src/")            ← 뿌리의 자식. 반환값 = 그 자식 노드
src.add("main.py")                   ← src 의 자식
models = src.add("models/")          ← src 의 자식이자 새 부모
models.add("user.py")
tree.add("README.md")                ← 다시 뿌리의 자식

결과(모양만 — 선 문자는 Rich 가 정한다):
프로젝트 구조
├── src/
│   ├── main.py
│   └── models/
│       └── user.py
└── README.md
```

- `add()` 를 **어느 노드에 대고 부르느냐**가 위치를 정한다.
- `add()` 는 방금 만든 자식 노드를 돌려준다.
- 그 자식 밑에 또 무언가를 달려면 반환값을 변수(`src`, `models`)에 받아 둔다.
- 받아 두지 않은 노드(파일 같은 잎)는 그 뒤로 손댈 수 없으니 변수가 필요 없다.
- 노드 라벨에도 마크업을 쓸 수 있다.

### (5) `Panel` — 테두리 상자

**언제 쓰나** — 배포 완료 알림처럼 한 덩어리 메시지를 상자로 강조할 때.

```text
Panel("[bold]배포 완료[/bold]\n\n버전: ...", title="Deploy Status", border_style="green")
        │
        ▼
  초록 테두리 상자, 윗변에 「Deploy Status」, 안에 여러 줄 내용
```

- 첫 인자가 상자 안 내용이다 — `\n` 으로 줄을 나누고, 마크업도 쓸 수 있다.
- `title=` 은 상자 제목, `border_style=` 은 테두리 색이다.
- `Panel` 은 만들기만 해서는 아무것도 찍히지 않고 `console.print(Panel(...))` 로 넘겨야 나온다(`Table` · `Tree` 도 같다).

### (6) `Progress` — 진행 막대

**언제 쓰나** — 다운로드 · 설치처럼 시간이 걸리는 반복 작업의 진척을 보일 때.

```text
with Progress() as progress:                       ← 시작: 화면에 진행판을 띄운다
    task = progress.add_task("다운로드 중...", total=100)   ← 작업 등록(목표 100)
    while not progress.finished:                   ← 아직 안 끝났으면
        progress.update(task, advance=1)           ← 진척 +1
        time.sleep(0.02)
                                                   ← with 를 나오면 진행판 정리
```

- `Progress` 는 `with` 문(컨텍스트 매니저)으로 쓴다.
- `add_task(설명, total=목표)` 가 작업 하나를 등록하고 작업 id 를 돌려준다.
- `update(작업, advance=n)` 이 그 작업의 진척을 `n` 만큼 늘린다.
- `progress.finished` 를 반복 조건으로 쓴다 — 원본 루프는 등록한 작업이 다 끝날 때까지 돈다.
- 작업을 여럿 등록하면 한 진행판에 줄마다 따로 그려진다(`task1`, `task2`).
- `Progress(...)` 에 열(column)을 넘겨 모양을 고를 수 있다 — `SpinnerColumn()`(도는 표시), `TextColumn(...)`(글자), `BarColumn()`(막대).
- `TextColumn("{task.percentage:>3.0f}%")` 의 `{…}` 는 파이썬 서식 문법이다.
  `>3` 은 폭 3칸 오른쪽 정렬, `.0f` 는 소수점 없는 실수 표기다.
  그래서 퍼센트가 `  5%`, ` 50%`, `100%` 처럼 자리가 맞는다.

원본 예제에서 이 절의 코드는 **실행되지 않는다**.
`print("""…""")` 로 감싸 코드를 글자 그대로 찍을 뿐이다(원본 주석: 「코드만 시연, 실행 시 애니메이션」).
진행 막대 애니메이션을 보려면 그 코드를 따로 꺼내 실행해야 한다.
`logging` 절도 같은 방식이다.

### (7) `Markdown` 과 `Syntax`

**언제 쓰나** — 도움말 문서를 터미널에서 서식 있게 보이거나, 코드 조각을 색 강조해 보일 때.

```text
Markdown("# 제목\n**굵은 글씨** ...")   →  console.print(md)  →  제목 · 굵게 · 목록 · 코드블록이 서식대로
Syntax(code, "python", theme="monokai", line_numbers=True)
                                        →  console.print(syntax) → 줄 번호 + 색 강조된 코드
```

- `Markdown` 은 마크다운 문자열을 받아 제목 · 굵게 · 기울임 · 인라인 코드 · 목록(하위 목록 포함) · 코드블록을 렌더링한다.
- `Syntax(코드, 언어, theme=테마, line_numbers=True)` 는 코드를 색 강조하고 줄 번호를 붙인다.
- 원본 주석에 따르면 `Syntax` 는 Pygments 기반이라 여러 언어와 테마를 지원한다.

> **Pygments** — 파이썬으로 만든 코드 색 강조 라이브러리.\
> 예: 언어 이름 `"python"` 과 테마 `"monokai"` 를 받아 토큰마다 색을 정한다.

### (8) `RichHandler` — 표준 `logging` 에 연결

**언제 쓰나** — 기존 `logging` 코드는 그대로 두고 로그 출력만 보기 좋게 바꾸고 싶을 때.

```text
logging.basicConfig(level=logging.DEBUG,
                    format="%(message)s",
                    handlers=[RichHandler(rich_tracebacks=True)])
        │
        ▼  log.info / log.warning / log.error 호출
        ▼  메시지가 RichHandler 로 간다
        ▼  RichHandler 가 시간 · 레벨 · 색을 붙여 출력
  컬러 로그 + 예외 시 보기 좋은 traceback
```

- `RichHandler` 를 `basicConfig` 의 `handlers` 목록에 넣으면 로그가 Rich 로 찍힌다.
- `rich_tracebacks=True` 면 예외의 traceback 도 Rich 가 꾸며 보인다.
- `format` 에는 `"%(message)s"` 만 둔다 — 시간 · 레벨은 `RichHandler` 가 알아서 붙이기 때문이다.

> **핸들러(handler)** — `logging` 에서 로그 기록을 받아 실제로 어디에 어떻게 내보낼지 맡는 객체.\
> 예: `RichHandler` 는 기록을 색 입힌 터미널 출력으로 내보낸다.

## 문법 — 형태와 규칙

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
console.print("[bold]준비[/] 완료", style="italic")   # 바닥 italic + 「준비」만 bold 추가

t = Table(title="점수")
t.add_column("이름", style="cyan")
t.add_column("점수", justify="right")
t.add_row("가", "[green]90[/green]")
console.print(t)

console.print(Panel("끝", title="알림", border_style="blue"))
```

- 태그 꼴: `[스타일 스타일 …]글자[/스타일 스타일 …]`, 닫기는 `[/]` 로 줄일 수 있다.
- `console.print(문자열, style=...)` — `style` 은 줄 전체의 바닥 스타일이다.
- 구조물(`Table` · `Tree` · `Panel` · `Markdown` · `Syntax`)은 객체를 만든 뒤 `console.print(객체)` 로 출력한다.
- `from rich import print as rprint` — 내장 `print` 대신 쓸 수 있는, 마크업을 해석하는 `print` 다.
  이름을 `rprint` 로 바꿔 받으면 내장 `print` 와 함께 쓸 수 있다.
- 원본이 가져오는 것: `Console` · `Table` · `Tree` · `Panel` · `Columns`(여러 열로 정렬 출력) · `Text`(스타일 가능한 텍스트 객체) · `rprint`, 그리고 쓰는 자리에서 `Markdown` · `Syntax` · `Progress` 계열 · `RichHandler`.

| 부품 | 모듈 | 핵심 인자 |
|---|---|---|
| `Console` | `rich.console` | (없음) |
| `Table` | `rich.table` | `title`; `add_column(이름, style, justify, no_wrap)`; `add_row(셀…)` |
| `Tree` | `rich.tree` | 뿌리 라벨; `add(라벨)` → 자식 노드 |
| `Panel` | `rich.panel` | 내용, `title`, `border_style` |
| `Progress` | `rich.progress` | 열들; `add_task(설명, total)`; `update(작업, advance)`; `finished` |
| `Markdown` | `rich.markdown` | 마크다운 문자열 |
| `Syntax` | `rich.syntax` | 코드, 언어, `theme`, `line_numbers` |
| `RichHandler` | `rich.logging` | `rich_tracebacks` |

## 어디서 틀리나

### 1. 내장 `print` 는 태그를 해석하지 않는다
태그를 해석하는 것은 `console.print()` 와 `rich.print`(`rprint`)다.
내장 `print("[bold]x[/bold]")` 는 대괄호까지 글자 그대로 찍는다.
원본은 섹션 머리(`print("=== Table ===")`)를 내장 `print` 로 찍는데, 머리에 태그가 없어서 문제가 드러나지 않을 뿐이다.
**원본의 주장 → 왜 의심스러운가**: 정답 코드 주석은 `print("=== Rich 기본 출력 ===")` 줄에 「마크업 태그로 색상/스타일 적용」이라 적는다.
그 줄은 내장 `print` 이고 태그도 없으므로 색이 입혀지지 않는다고 보는 것이 맞다(원본에 근거 없음 — 추론).

### 2. 만들기만 하고 `console.print` 를 빠뜨린다
`Table` · `Tree` · `Panel` · `Markdown` · `Syntax` 는 객체를 만들어도 화면에 아무것도 나오지 않는다.
반드시 `console.print(객체)` 로 넘긴다.

### 3. `Tree.add()` 의 반환값을 버린다
`tree.add("src/")` 만 하고 반환값을 받지 않으면 `src/` 밑에 자식을 달 길이 없다.
하위 항목을 달 노드는 변수에 받아 둔다.
반대로 `tree.add(...)` 로 다는 것은 언제나 뿌리 바로 밑이다 — 코드의 위치가 아니라 **어느 노드에 대고 불렀나**가 위치를 정한다.

### 4. `RichHandler` 와 함께 `format` 에 시간 · 레벨을 넣는다
원본 주석의 함정이다.
`RichHandler` 가 시간 · 레벨을 이미 붙이므로 `format` 에도 넣으면 같은 정보가 두 번 보인다.
`format="%(message)s"` 로 둔다.

### 5. 문자열로 감싼 코드를 실행된 것으로 착각한다
원본의 Progress 절과 logging 절은 `print("""…""")` 안에 든 **글자**다.
파일을 돌려도 진행 막대는 움직이지 않고 로그도 Rich 로 찍히지 않는다 — 코드 텍스트가 찍힐 뿐이다.

### 6. 가져오고 쓰지 않는 이름
원본은 `Columns` · `Text` · `rprint` 를 가져오지만 본문에서 쓰지 않는다.
틀린 것은 아니지만, 이 셋의 동작은 원본 예제로 확인할 수 없다.

### 7. 작업이 여럿일 때 `finished`
`task1`(목표 100, 한 번에 0.5)과 `task2`(목표 50, 한 번에 0.3)는 끝나는 시점이 다르다.
반복은 `progress.finished` 가 참이 될 때까지, 곧 늦게 끝나는 작업까지 다 끝날 때까지 돈다.

### 8. 팁 모음
- Rich 는 `[bold red]태그[/]` 로 스타일을 적용한다.
- `console.print()` 는 마크업을 자동으로 해석한다.
- `RichHandler` 를 `logging` 에 연결하면 보기 좋은 로그 출력이 된다.
- Jupyter Notebook 에서도 잘 동작한다(원본 팁).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `console.print` 가 `[…]` 태그를 해석한다 | Rich 라이브러리(파이썬 언어가 아니다) |
| 내장 `print` 는 태그를 해석하지 않는다 | 파이썬 내장 함수의 동작(문자열을 그대로 쓴다) |
| `Tree.add()` 가 자식 노드를 돌려준다 | Rich 라이브러리의 API |
| `Syntax` 가 Pygments 기반이다 | Rich 의 구현(원본 주석의 주장) |
| `{task.percentage:>3.0f}` 의 `>3.0f` 뜻 | 파이썬 서식 문법(언어 · 표준 라이브러리) |
| `basicConfig(handlers=[…])` 로 핸들러를 다는 것 | 파이썬 표준 라이브러리 `logging` |
| 색이 실제로 보이는가 | 터미널(또는 Jupyter)의 표시 능력 |
| Jupyter 에서 잘 동작한다 | Rich 의 지원(원본 팁) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 에러 · 성공 메시지를 눈에 띄게 | `console.print("[red]…[/red]")` | 내장 `print` 에 태그 |
| 여러 서버 상태를 나란히 비교 | `Table` | 공백으로 맞춘 문자열 |
| 디렉터리 구조 보이기 | `Tree` 와 반환값 변수 | 직접 그린 `├──` 문자열 |
| 한 덩어리 알림 강조 | `Panel` | 줄마다 `=` 를 찍은 경계선 |
| 오래 걸리는 반복 | `with Progress()` + `update` | 매 반복 `print` 로 퍼센트 찍기 |
| 기존 `logging` 출력을 꾸미기 | `RichHandler` + `format="%(message)s"` | `format` 에 시간 · 레벨 중복 |
| 코드 조각 보여 주기 | `Syntax(…, line_numbers=True)` | 색 없는 `print(code)` |

## 핵심 문장

1. **`Console` 이 인쇄소다** — 문자열의 태그와 구조물 객체를 받아 색 · 테두리를 입혀 찍는다.
2. **태그는 `console.print` · `rprint` 만 해석한다** — `style=` 은 줄 전체 바닥, 태그는 그 위에 얹힌다.
3. **구조물은 만들고 나서 `console.print` 로 넘긴다** — `Table` 은 열 먼저 행 나중, `Tree` 는 `add()` 반환값으로 깊이를 판다.
4. **`Progress` 는 `with` · `add_task` · `update(advance)` · `finished` 의 고리다.**
5. **`RichHandler` 는 시간 · 레벨을 스스로 붙인다** — `format` 은 메시지만.

## 관련 자료

- [click-cli](../12-click-cli/2-summary.md)
- `logging-patterns` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `rich-output`

## 용어 풀이

- **Rich** — 터미널 출력에 색 · 표 · 트리 · 진행 막대 등을 입히는 파이썬 서드파티 라이브러리.
- **`Console`** — Rich 출력의 중심 객체, 모든 출력이 이것을 거친다.
- **마크업 태그** — `[bold]…[/bold]` 처럼 글자에 스타일을 지시하는 표시.
- **`style` 매개변수** — `console.print` 에서 줄 전체에 까는 스타일.
- **`justify`** — 표 열의 정렬 방향(`"right"` 등).
- **`no_wrap`** — 표 열에서 줄바꿈을 막는 옵션.
- **노드** — 트리의 한 마디(뿌리 · 디렉터리 · 파일).
- **`border_style`** — `Panel` 테두리의 스타일.
- **컨텍스트 매니저** — `with` 문으로 시작과 정리를 묶는 객체.
- **`add_task` / `update` / `advance`** — 진행 작업 등록 / 진척 갱신 / 늘릴 양.
- **열(column, Progress)** — 진행판 한 줄을 이루는 부품(스피너 · 글자 · 막대).
- **서식 문법** — `{값:>3.0f}` 처럼 폭 · 정렬 · 자릿수를 정하는 파이썬 문법.
- **Pygments** — 코드 색 강조 라이브러리.
- **핸들러** — `logging` 에서 기록을 실제로 내보내는 객체.
- **traceback** — 예외가 났을 때 호출 경로를 보여 주는 출력.

## 더 들어가면

- `[/]` 는 가장 최근에 연 스타일을 닫는다고 알려져 있다(확인 필요).
- 대괄호를 글자 그대로 찍고 싶으면 `rich.markup.escape` 나 `\[` 로 이스케이프한다(확인 필요).
- `Console` 은 출력 대상이 터미널이 아니면(파일로 넘기기 등) 색 코드를 빼고 찍는다고 알려져 있다(확인 필요).
- `Progress` 의 작업은 `total` 을 넘겨 `advance` 해도 오류 없이 끝난 것으로 본다고 알려져 있다(확인 필요).
- `Columns` 는 여러 렌더 대상을 화면 폭에 맞춰 여러 열로 늘어놓고, `Text` 는 `stylize` 등으로 구간 스타일을 코드로 다는 객체다(확인 필요).
- `rich.traceback.install()` 로 로깅 없이도 예외 traceback 을 꾸밀 수 있다(확인 필요).
- `track(iterable)` 은 `Progress` 를 간단히 쓰는 지름길이다(확인 필요).
