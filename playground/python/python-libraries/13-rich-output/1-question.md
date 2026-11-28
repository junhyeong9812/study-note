# python/python-libraries/13 — Rich 출력 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `style=` 과 태그를 같이 주면 (예측)

```python
# 질문용 발췌
console.print("[red]에러:[/red] 파일을 찾을 수 없습니다.", style="bold")
```

- 「에러:」와 「파일을 찾을 수 없습니다.」는 각각 어떤 스타일로 찍히나?

### 2. 트리에 노드를 단 위치 (예측)

```python
# 질문용 발췌
tree = Tree("프로젝트 구조")
src = tree.add("src/")
models = src.add("models/")
models.add("user.py")
routes = src.add("routes/")
routes.add("api.py")
tree.add("pyproject.toml")
```

- `pyproject.toml` 은 트리의 어느 노드 바로 밑에 놓이나?

### 3. 작업 둘을 건 진행 막대 (예측)

```python
# 질문용 발췌
task1 = progress.add_task("다운로드", total=100)
task2 = progress.add_task("설치", total=50)
while not progress.finished:
    progress.update(task1, advance=0.5)
    progress.update(task2, advance=0.3)
    time.sleep(0.02)
```

- 어느 작업이 먼저 목표에 닿고, 반복은 대략 몇 번 돈 뒤 끝나나?

### 4. 원본 파일을 돌렸을 때 Progress 절 (예측)

- 정답 코드 파일을 그대로 실행하면 「Progress Bar (코드 구조)」 머리 아래에는 무엇이 나타나나?

### 5. `RichHandler` 를 쓸 때 `format` 을 메시지만 두는 까닭 (왜)

- `RichHandler` 와 함께 `format="%(message)s"` 로 두라는 까닭은 무엇인가?

### 6. `Tree.add()` 의 반환값을 변수에 받는 까닭 (왜)

- 원본이 `src` · `models` · `routes` 는 변수에 받고 `user.py` 같은 노드는 받지 않는 까닭은 무엇인가?

### 7. 태그가 해석되는 범위 (경계)

- `print("[bold]경고[/bold]")` 와 `console.print("[bold]경고[/bold]")` 는 화면에서 어떻게 다르나?

### 8. 구조물 객체만 만들고 끝내면 (경계)

- `Panel(...)` 이나 `Table(...)` 을 만들고 행까지 넣었는데 화면에 아무것도 없다면 무엇이 빠졌나?

### 9. 퍼센트 열과 파이썬 서식 문법 (연결)

- `TextColumn("{task.percentage:>3.0f}%")` 의 `>3.0f` 는 f-문자열의 어떤 규칙과 같고, 진행판에서 무슨 효과를 내나?

## 실습

### 실습 1. Rich 로 운영 대시보드 출력 만들기

**만들 것** — 메시지 · 표 · 트리 · 상자 · 마크다운 · 코드 강조를 차례로 찍고, 진행 막대와 로깅 연결 코드는 글자로 보여 주는 파이썬 스크립트.

**준비물** — 서드파티 라이브러리 `rich` 가 필요하다(`pip install rich`).

**요구 조건**

1단계 — 준비
1. `Console` · `Table` · `Tree` · `Panel` · `Columns` · `Text` 와 `rich` 의 `print`(`rprint` 이름으로)를 가져온다.
2. `Console` 객체를 하나 만들어 이후 출력에 쓴다.

2단계 — 기본 출력
3. 태그로 「성공!」만 굵은 초록으로 찍는다.
4. 「에러:」만 빨갛게 태그를 달고, 줄 전체에는 `style` 매개변수로 굵게를 깐다.
5. 「정보」를 기울인 cyan 으로 찍는다.
6. 밑줄 · 취소선 · 굵게를 한 줄에 각각 적용해 찍는다.

3단계 — 표
7. 제목이 「서버 상태」인 표를 만든다.
8. 열 넷(서버 · 상태 · CPU · 메모리)을 정의한다 — 서버 열은 줄바꿈 금지, CPU · 메모리 열은 오른쪽 정렬.
9. 서버 네 대의 행을 넣되, 상태 셀은 태그로 색을 단다.
10. 표를 출력한다.

4단계 — 트리 · 상자
11. 뿌리 아래 `src/`, 그 아래 `main.py` · `models/`(`user.py`, `product.py`) · `routes/`(`api.py`), 뿌리 바로 아래 `pyproject.toml` · `README.md` 가 오는 트리를 만들어 출력한다.
12. 배포 정보를 내용으로, 제목과 테두리 스타일을 지정한 상자를 출력한다.

5단계 — 글자로 보여 줄 코드
13. 기본 진행 막대와 열을 고른 진행 막대(작업 둘) 코드를 실행하지 않고 여러 줄 문자열로 찍는다.

6단계 — 마크다운 · 코드 강조
14. 제목 · 굵게 · 기울임 · 인라인 코드 · 하위 목록 · 코드블록을 담은 마크다운을 렌더링해 출력한다.
15. 피보나치 함수 코드를 python 으로, 테마와 줄 번호를 지정해 강조 출력한다.

7단계 — 로깅
16. `RichHandler` 를 `basicConfig` 에 연결하는 코드를 실행하지 않고 여러 줄 문자열로 찍는다.

**시작 코드**

```python
# TODO: rich 에서 Console, Table, Tree, Panel, Columns, Text 와 print(rprint 로)를 가져온다

# TODO: Console 객체 만들기
console = None

print("=== Rich 기본 출력 ===")
# TODO: "성공!" 은 bold green, 뒤에 " 작업이 완료되었습니다."
# TODO: "에러:" 는 red 태그, 뒤에 " 파일을 찾을 수 없습니다.", 줄 전체 style 은 bold
# TODO: "정보" 는 italic cyan, 뒤에 ": 처리 중..."
# TODO: "밑줄"(underline), "취소선"(strike), "굵게"(bold)

print("\n=== Table ===")
# TODO: 제목 "서버 상태" 인 표
# 열: 서버(cyan, 줄바꿈 금지) / 상태(magenta) / CPU(오른쪽, green) / 메모리(오른쪽, yellow)
# 행:
#   web-01   [green]Running[/green]   23%  45%
#   web-02   [green]Running[/green]   67%  72%
#   db-01    [yellow]Warning[/yellow] 89%  91%
#   cache-01 [red]Down[/red]           0%   0%
# TODO: 표 출력

print("\n=== Tree ===")
# 라벨: "[bold]프로젝트 구조[/bold]", "[bold blue]src/[/bold blue]", "[green]main.py[/green]",
#       "[bold blue]models/[/bold blue]", "user.py", "product.py",
#       "[bold blue]routes/[/bold blue]", "api.py",
#       "[yellow]pyproject.toml[/yellow]", "[yellow]README.md[/yellow]"
# TODO: 트리 조립 후 출력

print("\n=== Panel ===")
PANEL_BODY = (
    "[bold]배포 완료[/bold]\n\n"
    "버전: v2.1.0\n"
    "환경: production\n"
    "시간: 2024-01-15 14:30:00"
)
# TODO: 제목 "Deploy Status", 테두리 green 인 상자로 PANEL_BODY 출력

print("\n=== Progress Bar (코드 구조) ===")
# TODO: 기본 Progress(작업 하나, total=100, advance=1)와
#       SpinnerColumn · TextColumn · BarColumn · 퍼센트 TextColumn 을 고른 Progress
#       (작업 "다운로드" total=100 advance=0.5, "설치" total=50 advance=0.3)
#       코드를 실행하지 말고 여러 줄 문자열로 print

print("\n=== Markdown ===")
# TODO: Markdown 가져오기, 마크다운 문자열 렌더링 출력

print("\n=== Syntax Highlighting ===")
code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
# TODO: Syntax 가져오기, python · theme="monokai" · 줄 번호로 출력

print("\n=== Rich Logging ===")
# TODO: logging.basicConfig(level=DEBUG, format=메시지만, handlers=[RichHandler(rich_tracebacks=True)])
#       와 info · warning · error 로그 세 줄 코드를 여러 줄 문자열로 print
```

**확인 방법** — `python rich-output.py` 로 돌려 섹션마다 색 메시지 · 표 · 트리 · 상자 · 렌더링된 마크다운 · 줄 번호 붙은 코드가 나오고, Progress · Logging 섹션에는 코드 텍스트가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
