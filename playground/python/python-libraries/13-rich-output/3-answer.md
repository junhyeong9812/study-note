# python/python-libraries/13 — Rich 출력 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「에러:」는 굵은 빨강, 나머지는 굵게만

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
「에러:」는 bold + red 로, 「 파일을 찾을 수 없습니다.」는 bold 로만 찍힌다.

**왜 그런가**
`style="bold"` 는 줄 전체에 깔리는 바닥 스타일이다.
`[red]…[/red]` 태그는 그 위에서 「에러:」 구간에만 빨강을 더한다.
겹친 구간은 둘 다 적용된다 — 원본 주석의 「중첩 적용」이다(2-summary 「동작 방식 (2)」).

### 2. `pyproject.toml` 은 뿌리 바로 밑

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`pyproject.toml` 은 「프로젝트 구조」(뿌리) 바로 밑, `src/` 와 같은 높이에 놓인다.

**왜 그런가**
위치는 코드의 순서가 아니라 `add()` 를 어느 노드에 대고 불렀나로 정해진다.
`tree.add(...)` 는 뿌리 `tree` 에 대고 불렀으므로 바로 앞 줄이 `routes.add` 여도 `routes/` 밑으로 들어가지 않는다(2-summary 「동작 방식 (4)」, 「어디서 틀리나 3」).

### 3. 「설치」가 먼저 끝나고, 반복은 약 200번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
「설치」(`task2`)가 먼저 목표에 닿고, 반복은 「다운로드」가 끝나는 약 200번째에 멈춘다.

**왜 그런가**
`task1` 은 100 ÷ 0.5 = 200번, `task2` 는 50 ÷ 0.3 ≈ 167번 갱신해야 목표에 닿는다.
반복 조건 `progress.finished` 는 등록한 작업이 다 끝나야 참이 되므로 늦은 쪽(200번)에 맞춰 끝난다(2-summary 「어디서 틀리나 7」).
한 번에 0.02초를 쉬므로 대략 4초쯤 걸린다는 계산이 나온다(원본에 근거 없음 — 추론).
`task2` 가 끝난 뒤에도 계속 `advance` 되는데, 그때 진행판이 어떻게 보이는지는 원본으로 알 수 없다.

### 4. 진행 막대 대신 코드 텍스트

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
움직이는 진행 막대는 나오지 않고, `from rich.progress import …` 로 시작하는 코드가 글자 그대로 찍힌다.

**왜 그런가**
그 코드는 내장 `print("""…""")` 의 여러 줄 문자열 안에 있어 실행되지 않는다.
원본 주석도 「코드만 시연, 실행 시 애니메이션」이라 적는다(2-summary 「동작 방식 (6)」, 「어디서 틀리나 5」).

### 5. 시간 · 레벨이 두 번 찍히지 않게 하려고

`RichHandler` 는 로그 한 줄에 시간과 레벨을 스스로 붙인다.
`format` 에도 시간 · 레벨을 넣으면 같은 정보가 두 번 보인다.
그래서 `format` 에는 메시지만 둔다 — 원본 주석의 「함정」이다(2-summary 「동작 방식 (8)」, 「어디서 틀리나 4」).

### 6. 그 밑에 자식을 더 달아야 하는 노드만 받는다

`add()` 는 방금 만든 자식 노드를 돌려준다.
`src` · `models` · `routes` 밑에는 파일을 더 달아야 하므로 반환값을 변수에 받아 두어야 그 노드에 대고 `add()` 를 다시 부를 수 있다.
`user.py` 같은 잎은 밑에 달 것이 없어 받을 필요가 없다(2-summary 「동작 방식 (4)」).

### 7. 내장 `print` 는 대괄호까지 그대로, `console.print` 는 굵게

내장 `print` 는 태그를 해석하지 않아 `[bold]경고[/bold]` 가 글자 그대로 찍힌다.
`console.print` 는 태그를 해석해 「경고」만 굵게 찍는다.
태그를 해석하는 것은 `console.print` 와 `rich.print`(`rprint`)다(2-summary 「동작 방식 (1)」, 「어디서 틀리나 1」).

### 8. `console.print(객체)` 가 빠졌다

`Table` · `Tree` · `Panel` · `Markdown` · `Syntax` 는 만들기만 해서는 화면에 나오지 않는다.
만든 객체를 `console.print(...)` 로 넘겨야 그려진다(2-summary 「동작 방식 (5)」, 「어디서 틀리나 2」).

### 9. f-문자열의 서식 지정 — 폭 3칸 오른쪽 정렬, 소수점 없음

`{값:>3.0f}` 는 f-문자열 · `str.format` 의 서식 규칙과 같다.
`>3` 은 폭 3칸 오른쪽 정렬, `.0f` 는 소수점 아래 없이 실수를 적는다는 뜻이다.
그래서 퍼센트가 `  5%` · ` 50%` · `100%` 처럼 자리가 맞아 진행판 글자가 흔들리지 않는다(2-summary 「동작 방식 (6)」, 「구현 세부사항 대 언어 보장」).

## 실습 정답

### 실습 1. Rich 로 운영 대시보드 출력 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 부품 가져오기 | `from rich.console import Console` … `from rich import print as rprint` |
| 2. `Console` 객체 | `console = Console()` |
| 3. 「성공!」 굵은 초록 | `console.print("[bold green]성공![/bold green] …")` |
| 4. 태그 + `style` 바닥 | `console.print("[red]에러:[/red] …", style="bold")` |
| 5. 기울인 cyan | `"[italic cyan]정보[/italic cyan]: 처리 중..."` |
| 6. 밑줄 · 취소선 · 굵게 | `"[underline]…[/underline], [strike]…[/strike], [bold]…[/bold]"` |
| 7. 제목 있는 표 | `Table(title="서버 상태")` |
| 8. 열 넷 정의 | `table.add_column(…, no_wrap=True)` · `justify="right"` |
| 9. 행 넷 + 셀 태그 | `table.add_row("web-01", "[green]Running[/green]", …)` 등 |
| 10. 표 출력 | `console.print(table)` |
| 11. 트리 조립 · 출력 | `Tree(…)`, `src = tree.add(…)`, `models = src.add(…)`, `routes = src.add(…)`, `console.print(tree)` |
| 12. 상자 출력 | `console.print(Panel(…, title="Deploy Status", border_style="green"))` |
| 13. 진행 막대 코드를 글자로 | `print("""from rich.progress import …""")` |
| 14. 마크다운 렌더링 | `from rich.markdown import Markdown`, `md = Markdown(…)`, `console.print(md)` |
| 15. 코드 강조 | `Syntax(code, "python", theme="monokai", line_numbers=True)`, `console.print(syntax)` |
| 16. 로깅 연결 코드를 글자로 | `print("""import logging … RichHandler(rich_tracebacks=True) …""")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/rich-output.py`

````python
# [주요 라이브러리] Rich 출력
# 설명: Rich console, table, progress bar, 트리, 마크다운 출력
# 팁: Rich는 [bold red]태그[/]로 스타일을 적용한다. console.print()는 자동으로 마크업을 해석한다. RichHandler를 logging에 연결하면 아름다운 로그 출력이 가능하다. Jupyter Notebook에서도 잘 동작한다.

# Console: Rich 출력의 메인 진입점
from rich.console import Console
# Table: 표 형태 렌더링
from rich.table import Table
# Tree: 트리 구조 렌더링
from rich.tree import Tree
# Panel: 박스 테두리 출력
from rich.panel import Panel
# Columns: 여러 열로 정렬 출력
from rich.columns import Columns
# Text: 스타일 가능한 텍스트 객체
from rich.text import Text
# rich.print: 내장 print를 대체하는 마크업 처리 print
from rich import print as rprint

# Console 인스턴스 생성: 모든 출력은 이 객체를 통해(stdout 자동 감지)
console = Console()

# === 기본 출력 ===
# 섹션 헤더 출력: 마크업 태그로 색상/스타일 적용
print("=== Rich 기본 출력 ===")
# [tag]...[/tag] 형식으로 인라인 스타일 지정
# 닫는 태그 [/] 단축 사용 가능
console.print("[bold green]성공![/bold green] 작업이 완료되었습니다.")
# style 파라미터로도 스타일 지정 가능(중첩 적용)
console.print("[red]에러:[/red] 파일을 찾을 수 없습니다.", style="bold")
# italic, cyan 등 다양한 색상 키워드 지원
console.print("[italic cyan]정보[/italic cyan]: 처리 중...")
# 밑줄/취소선/굵게 등 텍스트 데코레이션
console.print("[underline]밑줄[/underline], [strike]취소선[/strike], [bold]굵게[/bold]")

# === Table ===
# 섹션 헤더 출력: 표 렌더링
print("\n=== Table ===")
# Table 객체 생성(제목 지정)
table = Table(title="서버 상태")
# add_column으로 컬럼 정의(스타일/정렬/줄바꿈 옵션)
table.add_column("서버", style="cyan", no_wrap=True)
# 두 번째 컬럼
table.add_column("상태", style="magenta")
# 숫자 정렬 right + 색상
table.add_column("CPU", justify="right", style="green")
# 메모리 컬럼
table.add_column("메모리", justify="right", style="yellow")

# add_row로 행 추가(셀 단위에도 마크업 가능)
table.add_row("web-01", "[green]Running[/green]", "23%", "45%")
# 두 번째 행
table.add_row("web-02", "[green]Running[/green]", "67%", "72%")
# 경고 행: 노란색 스타일
table.add_row("db-01", "[yellow]Warning[/yellow]", "89%", "91%")
# 다운된 서버: 빨간색 스타일
table.add_row("cache-01", "[red]Down[/red]", "0%", "0%")

# 표 출력(테두리/색상 자동 적용)
console.print(table)

# === Tree ===
# 섹션 헤더 출력: 디렉토리 같은 트리 구조 표시
print("\n=== Tree ===")
# 루트 노드 생성(라벨에 마크업 가능)
tree = Tree("[bold]프로젝트 구조[/bold]")
# 자식 노드 추가는 add() 호출, 리턴 값은 그 자식 노드(체이닝 가능)
src = tree.add("[bold blue]src/[/bold blue]")
# src 하위 파일
src.add("[green]main.py[/green]")
# models 서브디렉토리 노드
models = src.add("[bold blue]models/[/bold blue]")
# models 하위 파일들
models.add("user.py")
# product.py도 모델 디렉토리에
models.add("product.py")
# routes 노드
routes = src.add("[bold blue]routes/[/bold blue]")
# routes 하위 파일
routes.add("api.py")
# 루트 옆 파일들
tree.add("[yellow]pyproject.toml[/yellow]")
# README 파일
tree.add("[yellow]README.md[/yellow]")

# 트리 렌더링
console.print(tree)

# === Panel ===
# 섹션 헤더 출력: 박스 테두리로 강조
print("\n=== Panel ===")
# Panel(content, title=..., border_style=...)로 박스 출력
console.print(Panel(
    "[bold]배포 완료[/bold]\n\n"
    "버전: v2.1.0\n"
    "환경: production\n"
    "시간: 2024-01-15 14:30:00",
    title="Deploy Status",
    border_style="green"
))

# === Progress Bar ===
# 섹션 헤더 출력: 진행률 표시(코드만 시연, 실행 시 애니메이션)
print("\n=== Progress Bar (코드 구조) ===")
# Progress 컨텍스트 매니저 안에서 add_task → update로 진행
# 컬럼을 커스터마이즈하면 스피너/바/퍼센트 등 조합 가능
print("""
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import time

# 기본 프로그레스바
with Progress() as progress:
    task = progress.add_task("[green]다운로드 중...", total=100)
    while not progress.finished:
        progress.update(task, advance=1)
        time.sleep(0.02)

# 커스텀 프로그레스바
with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("{task.percentage:>3.0f}%"),
) as progress:
    task1 = progress.add_task("다운로드", total=100)
    task2 = progress.add_task("설치", total=50)
    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        time.sleep(0.02)
""")

# === Markdown ===
# 섹션 헤더 출력: 마크다운 문자열을 그대로 렌더링
print("\n=== Markdown ===")
# Markdown 클래스는 # 제목, **굵게**, 코드블록 등 거의 모든 마크다운 지원
from rich.markdown import Markdown

# 멀티라인 마크다운 문자열
md = Markdown("""
# 제목

**굵은 글씨**와 *기울임*, `인라인 코드`

- 항목 1
- 항목 2
  - 하위 항목

```python
def hello():
    print("Hello, Rich!")
```
""")
# 마크다운 렌더링 출력
console.print(md)

# === Syntax Highlighting ===
# 섹션 헤더 출력: 소스 코드를 색상 강조하여 출력
print("\n=== Syntax Highlighting ===")
# Syntax 클래스는 Pygments 기반으로 다양한 언어/테마 지원
from rich.syntax import Syntax

# 강조 표시할 파이썬 코드(여기선 멀티라인 문자열)
code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
# Syntax(code, lang, theme, line_numbers)로 객체 생성
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
# 코드 강조 출력
console.print(syntax)

# === 로깅 ===
# 섹션 헤더 출력: logging과 RichHandler 통합
print("\n=== Rich Logging ===")
# RichHandler를 logging.basicConfig의 handlers에 넣으면 컬러풀한 로그 + 예쁜 traceback 출력
# 함정: format에 시간/레벨을 직접 넣지 말 것(RichHandler가 알아서 처리)
print("""
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")
log.info("서버가 시작되었습니다")
log.warning("디스크 사용량 80% 초과")
log.error("데이터베이스 연결 실패")
""")
````

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `rich` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 출력은 모두 하나의 `console` 을 거친다 — 섹션 머리만 내장 `print` 로 찍는다.
- 태그는 구간 스타일, `style=` 은 줄 전체 바닥 스타일이다.
- `Table` 은 `add_column` 으로 열을 정한 뒤 `add_row` 로 채우고, 셀에도 태그를 쓸 수 있다.
- `Tree` 는 하위 항목을 달 노드만 `add()` 반환값을 변수에 받는다.
- Progress · Logging 절은 실행되는 코드가 아니라 `print` 로 찍는 문자열이다.
- `RichHandler` 를 쓸 때 `format` 은 `"%(message)s"` 만 둔다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `rich` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
