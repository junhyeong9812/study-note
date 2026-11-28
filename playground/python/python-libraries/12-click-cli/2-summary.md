# python/python-libraries/12 — Click CLI — 정리 (힌트)

> 출처 — study-site 항목 `python/click-cli`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/click-cli.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Click 은 「식당 주문서 양식」이다.**
손님은 양식의 칸에 맞춰 주문을 적는다.
직원은 빈칸이나 잘못 적은 칸을 먼저 걸러 낸다.
검사를 통과한 주문만 주방으로 넘어간다.
반드시 적어야 하는 칸은 정해진 차례대로 적는다(「메뉴 이름」).
골라 적는 칸은 이름표를 붙여 적는다(「맵기: 보통」).
아무것도 안 적으면 기본값이 들어간다.
푸드코트처럼 가게가 여럿이면 먼저 가게를 고르고, 그 가게의 주문서를 쓴다.
Click 으로 만든 명령줄 도구도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주문서 양식 | `@click.command()` 로 꾸민 함수 |
| 차례대로 꼭 적는 칸 | `@click.argument` (위치 인자) |
| 이름표 붙은 선택 칸 | `@click.option` (`--name` 꼴) |
| 보기 중에서 고르는 칸 | `type=click.Choice([...])` |
| 빈칸일 때 들어가는 값 | `default=` |
| 주문을 검사하는 직원 | Click 의 명령줄 해석 · 형 변환 · 검사 |
| 주방 | 명령 함수의 본문 |
| 푸드코트와 가게들 | `@click.group()` 과 하위 명령 |
| 푸드코트 공용 게시판 | `ctx.obj` (위·아래 명령이 함께 보는 상태) |

```text
터미널에 친 줄                         Click 이 하는 일                    함수가 받는 것
python cli.py --name Alice -c 3  ──▶  옵션 이름 찾기 → 형 변환 → 검사  ──▶  greet(name='Alice', count=3, greeting='hello')
                                       (어긋나면 여기서 멈춘다)
```

## 이 주제가 답하려는 질문

1. 터미널에 친 글자가 어떻게 파이썬 함수의 인자가 되나?
2. 이름 붙은 옵션과 위치 인자는 무엇이 다르고, 값 검사는 누가 언제 하나?
3. `git` 처럼 하위 명령이 여럿인 도구는 어떻게 짓고, 위 명령과 아래 명령은 값을 어떻게 나누나?
4. 색 출력 · 확인 질문 · 진행 표시 · 설치 후 명령 이름은 어떻게 다루나?

## 동작 방식

### (1) `@click.command` + `@click.option` — 함수를 명령으로 바꾸기

**언제 쓰나** — 파이썬 함수 하나를 터미널에서 `--이름 값` 꼴로 부르고 싶을 때 쓴다.
`sys.argv` 를 직접 쪼개는 대신 함수 위에 선언만 얹는다.

> **CLI** — 명령줄 인터페이스, 터미널에 글자를 쳐서 프로그램을 부리는 방식.\
> 예: `python cli.py --name Alice`.

> **데코레이터** — 함수 위에 `@이름` 으로 얹어 그 함수를 감싸거나 바꾸는 파이썬 문법.\
> 예: `@click.command()` 는 평범한 함수를 Click 명령으로 바꾼다.

```python
@click.command()
@click.option('--name', '-n', required=True, help='사용자 이름')
@click.option('--count', '-c', default=1, type=int, help='인사 횟수')
@click.option('--greeting', type=click.Choice(['hello', 'hi', 'hey']), default='hello')
def greet(name, count, greeting):
    """사용자에게 인사하는 CLI 도구"""
    for _ in range(count):
        click.echo(f'{greeting}, {name}!')
```

```text
입력: python cli.py --name Alice --count 3
  │
  ├─ '--name' 을 찾는다 → 다음 낱말 'Alice' 를 name 에
  ├─ '--count' 를 찾는다 → '3' (문자열) 을 type=int 로 바꿔 count=3
  ├─ '--greeting' 은 없다 → default 'hello'
  ├─ required=True 인 --name 이 빠졌는지 검사 → 통과
  ▼
greet(name='Alice', count=3, greeting='hello') 호출
  ▼
'hello, Alice!' 를 3번 echo
```

- `@click.option('--name', '-n', ...)` 은 긴 이름 `--name` 과 짧은 이름 `-n` 을 함께 단다.
- 함수 매개변수 이름은 긴 이름에서 `--` 를 뗀 것(`name`)이다.
- 터미널에서 들어온 값은 모두 문자열이라, `type=int` 가 정수로 바꿔 준다.
- `required=True` 인 옵션이 빠지면 함수가 불리기 전에 오류로 멈춘다.
- `click.Choice([...])` 는 보기 밖의 값을 막는다.
- 함수 docstring 은 `--help` 출력에 도구 설명으로 그대로 나온다.
- `help=` 문자열은 `--help` 에서 그 옵션의 설명이 된다.

> **옵션(option)** — `--이름` 꼴로 이름을 붙여 넘기는 선택적 인자.\
> 예: `--count 3`.

> **docstring** — 함수 본문 첫 줄에 둔 문자열, 그 함수의 설명문.\
> 예: `"""사용자에게 인사하는 CLI 도구"""`.

### (2) 옵션의 여러 꼴 — 형 · 검사 · 입력 받기

**언제 쓰나** — 켜고 끄는 스위치, 경로, 숫자 범위, 여러 번 받는 값, 파일, 비밀번호처럼 값의 성격이 다를 때 쓴다.

원본의 `serve` 명령이 한 번에 보여 준다.

| 선언 | 함수가 받는 것 | 하는 일 |
|---|---|---|
| `'--verbose', '-v', is_flag=True` | `True` / `False` | 값 없이 이름만 쓰면 켜진다(불리언 스위치) |
| `'--output', '-o', type=click.Path()` | 경로 문자열 | 경로로 다룬다 |
| `'--format', type=click.Choice(['json','csv','yaml'])` | 셋 중 하나 | 허용 값 제한 |
| `'--port', type=click.IntRange(1024, 65535), default=8080` | 정수 | 범위 밖이면 거부, 없으면 8080 |
| `'--tags', multiple=True` | 튜플 | 같은 옵션을 여러 번 받는다 |
| `'--config', type=click.File('r')` | 열린 파일 | 읽기 모드로 파일을 연다 |
| `'--password', prompt=True, hide_input=True` | 문자열 | 안 주면 입력을 물어보고, 치는 글자를 가린다 |

```text
입력: python cli.py -v --port 3000 --tags web --tags api
  │
  ├─ -v                → verbose=True
  ├─ --port 3000       → int 로 변환 → 1024~65535 안인지 검사 → port=3000
  ├─ --tags web        ┐
  ├─ --tags api        ┘→ 모아서 tags=('web', 'api')
  ├─ --password 없음   → prompt=True 라 비밀번호 입력을 요구(글자 가림)
  ▼
serve(verbose=True, port=3000, tags=('web','api'), password=<입력값>, 나머지는 기본값)
  ▼
Port: 3000 / Tags: ('web', 'api') / 상세 모드 활성화 를 echo
```

- `is_flag=True` 옵션은 뒤에 값을 붙이지 않는다.
- `multiple=True` 의 값은 리스트가 아니라 튜플로 들어온다(원본 주석 `# ('tag1', 'tag2')`).
- `IntRange` 와 `Choice` 의 검사는 함수 본문보다 먼저 일어난다.
- `prompt=True` 는 값이 명령줄에 없을 때 함수 본문 전에 사용자에게 묻는다.
- 원본 주석은 `prompt` 와 `required` 를 함께 쓰면 의도와 다르게 동작할 수 있다고 경고한다(「어디서 틀리나 5」).

> **플래그(flag)** — 값 없이 이름만으로 켜고 끄는 옵션.\
> 예: `-v`.

### (3) `@click.argument` — 위치로 받는 필수 값

**언제 쓰나** — 「무엇을」 처리하는지가 명령의 핵심이라 이름표 없이 차례로 받고 싶을 때 쓴다.

> **인자(argument)** — `--` 이름표 없이 놓인 차례로 받는 위치 기반 필수 값.\
> 예: `python cli.py a.txt b.txt` 에서 `a.txt` 와 `b.txt`.

```python
@click.command()
@click.argument('src', type=click.Path(exists=True))
@click.argument('dst', type=click.Path())
def copy(src, dst):
    """SRC 파일을 DST로 복사"""
```

```text
입력: python cli.py /path/to/source /path/to/dest
  │
  ├─ 첫째 낱말 → src   → exists=True 라 실제로 있는 경로인지 검사
  ├─ 둘째 낱말 → dst   → 존재 검사 없음
  ▼
copy(src='/path/to/source', dst='/path/to/dest')
  ▼
'Copying /path/to/source -> /path/to/dest'
```

- 선언한 차례가 곧 받는 차례다.
- `click.Path(exists=True)` 는 없는 경로를 자동으로 거부한다.
- 검사에 걸리면 함수 본문은 돌지 않는다.

### (4) `@click.group` — 하위 명령과 `ctx.obj`

**언제 쓰나** — `cli create …`, `cli delete …` 처럼 한 도구 아래 명령을 여럿 두는 `git` 꼴 도구를 만들 때 쓴다.

> **그룹(group)** — 하위 명령을 담는 부모 명령.\
> 예: `@click.group() def cli(...)` 아래 `@cli.command() def create(...)`.

> **컨텍스트(context)** — 한 번의 명령 실행 동안 Click 이 들고 다니는 상태 묶음.\
> 예: `@click.pass_context` 로 받는 `ctx`, 그 안의 `ctx.obj`.

```text
입력: python cli.py --debug create myproject
                    ───────  ──────  ─────────
                    cli 의    하위    create 의
                    옵션      명령    argument
  │
  ├─ cli(ctx, debug=True) 먼저 실행
  │     ctx.ensure_object(dict)  → ctx.obj 가 없으면 빈 dict 로 만든다
  │     ctx.obj['DEBUG'] = True
  ├─ create(ctx, name='myproject') 실행
  │     ctx.obj['DEBUG'] 를 읽어 True
  ▼
'Creating project: myproject' → '[DEBUG] 디버그 모드'
```

- `@cli.command()` 의 `cli` 는 위에서 만든 그룹 함수다 — 그 그룹에 하위 명령으로 등록된다.
- `--debug/--no-debug` 는 켜는 이름과 끄는 이름 한 쌍을 한 번에 만든다.
- `--debug` 는 `cli` 에 선언된 옵션이라, 그룹 이름과 하위 명령 이름 **사이**에 쓴다.
- `create` 는 자기 옵션 · 인자만 안다 — 부모의 값은 `ctx.obj` 로 받는다.
- `@click.option('--all', 'show_all', is_flag=True)` 처럼 두 번째에 이름을 주면 함수 매개변수 이름이 그것(`show_all`)이 된다.
- 함수 이름 `list_projects` 인 명령을 원본은 `python cli.py list-projects --all` 로 부른다 — 밑줄이 하이픈으로 바뀐 이름이다.
- `@click.confirmation_option(prompt='정말 삭제하시겠습니까?')` 은 본문 전에 확인을 받는 안전장치다.

### (5) 출력 · 대화 도우미

**언제 쓰나** — 결과를 보기 좋게 찍거나, 오래 걸리는 일을 보여 주거나, 사용자에게 묻고 싶을 때 쓴다.

| 함수 | 하는 일 |
|---|---|
| `click.echo(x)` | 출력. 팁: `print()` 보다 유니코드 · 파이프 처리가 안전하다 |
| `click.secho('성공!', fg='green', bold=True)` | `echo` + 스타일(글자색 `fg`, 배경색 `bg`, 굵게 `bold`) |
| `with click.progressbar(range(100), label='처리 중') as bar:` | 컨텍스트 매니저 꼴의 진행 바, `bar` 를 돌면 진행이 찬다 |
| `click.confirm('계속하시겠습니까?')` | 예/아니오를 묻고 참/거짓을 돌려준다 |
| `click.edit('기본 텍스트')` | `$EDITOR` 편집기를 열어 텍스트를 받는다 |

```text
for item in bar:          ← 한 바퀴 돌 때마다
    time.sleep(0.01)      ← 일을 하고
                          ← 진행 바가 한 칸씩 찬다 (100개면 끝에서 가득)
```

> **컨텍스트 매니저** — `with` 문으로 열고 닫는 일을 묶는 객체.\
> 예: `with click.progressbar(...) as bar:`.

### (6) `pyproject.toml` — 명령 이름 붙이기

**언제 쓰나** — `python cli.py …` 대신 `mytool …` 처럼 이름 하나로 부르고 싶을 때 쓴다.

```text
[project.scripts]
mytool = "mypackage.cli:cli"
          ─────────────  ───
          모듈 경로       그 모듈 안의 함수(그룹)

pip install  ──▶  'mytool' 콘솔 스크립트 생성  ──▶  mytool create myproject
                                                    = cli 그룹에 'create myproject' 를 넘긴 것
```

- `[project.scripts]` 에 등록하면 설치할 때 콘솔 스크립트가 생긴다.
- 오른쪽 `"모듈:함수"` 가 그 스크립트가 부를 Click 명령(여기서는 그룹 `cli`)이다.

### (7) 원본 예제 스크립트가 실제로 하는 일

원본 예제는 Click 코드를 **문자열로 찍기만** 한다.
`import click` 도, 데코레이터도 전부 `print("""…""")` 안의 글자다.
그래서 스크립트를 돌리면 절 제목과 코드 조각이 화면에 나올 뿐, 명령은 정의되지도 실행되지도 않는다.

```text
print("=== 기본 명령어 ===")     → 절 제목 한 줄
print("""                        → 따옴표 바로 뒤가 줄바꿈이라
import click                       출력은 빈 줄로 시작한다
...""")
\"\"\"…\"\"\"                     → 문자열 안에서 이스케이프한 것이라 """…""" 로 찍힌다
```

## 문법 — 형태와 규칙

```python
import click

@click.group()
def app():
    """할 일 도구"""

@app.command()
@click.argument('title')
@click.option('--times', '-t', default=1, type=int, help='반복 횟수')
def add(title, times):
    """할 일 추가"""
    for _ in range(times):
        click.echo(f'추가: {title}')

if __name__ == '__main__':
    app()
```

- `@click.command()` · `@click.group()` 은 괄호까지 붙여 쓴다.
- 옵션 · 인자 데코레이터는 명령 데코레이터 아래, 함수 바로 위에 쌓는다.
- 옵션: `@click.option('--긴이름', '-짧은이름', type=…, default=…, required=…, help=…)`.
- 옵션 선언에 `--` 없는 이름을 하나 더 주면 그것이 매개변수 이름이 된다(`'--all', 'show_all'`).
- 켜기/끄기 쌍: `'--debug/--no-debug'`.
- 인자: `@click.argument('이름', type=…)` — 이름표 없이 차례로 받는다.
- 하위 명령: `@그룹함수.command()`.
- 상태 공유: `@click.pass_context` 로 `ctx` 를 받고, `ctx.ensure_object(dict)` 후 `ctx.obj[...]` 에 넣고 읽는다.
- 원본 조각에는 마지막 호출 줄(`app()` 같은 것)이 없다 — 위 최소 예제처럼 진입점을 불러야 돈다(원본에 근거 없음 — 추론).
- 테스트는 `click.testing.CliRunner` 로 한다(팁).

## 어디서 틀리나

### 1. option 과 argument 를 뒤바꿔 생각한다

옵션은 `--이름` 이 붙은 **선택적** 값이다.
인자는 이름표 없이 **위치로** 받는 **필수** 값이다.
「`--src a.txt` 라고 쳐야지」나 「`name` 은 빼도 되겠지」가 둘을 헷갈린 꼴이다.
단, 옵션도 `required=True` 를 주면 필수가 된다(`greet` 의 `--name`).

### 2. 그룹 옵션을 하위 명령 뒤에 쓴다

`--debug` 는 그룹 `cli` 의 옵션이라 `python cli.py --debug create myproject` 처럼 그룹과 하위 명령 사이에 쓴다.
`create` 뒤에 쓰면 `create` 가 받게 되는데, `create` 에는 그런 옵션이 없다.

### 3. 매개변수 이름이 내장 이름을 가린다

`serve` 의 `--format` 은 매개변수 `format` 이 되어 함수 안에서 내장 `format()` 을 가린다.
`--all` 은 그대로면 `all` 이 되어 내장 `all()` 을 가린다 — 원본은 `'show_all'` 을 따로 주어 피했다.

### 4. `multiple=True` 값을 리스트로 착각한다

`--tags web --tags api` 는 `('web', 'api')` 튜플로 들어온다.
`append` 같은 리스트 메서드를 부르면 안 된다.

### 5. `prompt` 와 `required` 를 함께 쓴다

원본 주석의 주장: 「`prompt` 와 `required` 를 함께 쓰면 의도와 다르게 동작할 수 있다」.
왜 의심스러운가: 어떤 상황에서 어떻게 다르게 동작하는지 원본은 밝히지 않는다(확인 필요).
안전한 길은 둘 중 하나만 써서 「안 주면 묻는다」와 「안 주면 오류」 중 하나로 정하는 것이다.

### 6. `print()` 로 찍는다

팁: `click.echo()` 는 `print()` 보다 유니코드 · 파이프 처리가 안전하다.
CLI 출력은 다른 프로그램으로 파이프될 때가 많으니 `echo` · `secho` 를 쓴다.

### 7. 함수 이름 그대로 부른다

`list_projects` 함수는 원본에서 `list-projects` 로 불린다.
`python cli.py list_projects` 로 치면 그런 명령이 없다고 나온다(확인 필요 — 이름 변환 규칙은 「구현 세부사항 대 언어 보장」).

### 8. 검사를 함수 본문에서 다시 짠다

`Choice` · `IntRange` · `Path(exists=True)` · `required=True` 는 본문 전에 걸러 준다.
본문에서 `if port < 1024:` 를 또 짤 필요가 없다.

### 9. CLI 를 손으로만 시험한다

팁: `click.testing.CliRunner` 로 CLI 를 테스트할 수 있다.
터미널을 열지 않고 명령을 부르고 출력을 검사한다.

### 10. 확인 질문을 무시한다

`@click.confirmation_option` 은 사용자가 거절하면 `delete` 본문을 돌리지 않는다.
지우기 같은 되돌릴 수 없는 명령에 단다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 데코레이터를 함수 위에 쌓을 수 있다, docstring 이 `__doc__` 이 된다 | 파이썬 언어 |
| docstring 이 `--help` 에 나온다, 옵션 검사가 본문 전에 일어난다 | Click 라이브러리 |
| `multiple=True` 값이 튜플이다 | Click 라이브러리 |
| `list_projects` → `list-projects` 이름 변환 | Click 라이브러리 — 버전에 따라 다를 수 있다(확인 필요) |
| `echo` 가 `print` 보다 유니코드 · 파이프에 안전하다 | Click 구현의 주장 — 플랫폼 · 터미널에 따라 차이(확인 필요) |
| `secho` 색이 보인다 | 터미널이 색을 지원하는지에 달림 |
| `click.edit` 가 여는 편집기 | 사용자 환경 변수 `$EDITOR` |
| `[project.scripts]` 로 `mytool` 명령이 생긴다 | 패키징 표준(`pyproject.toml`)과 설치 도구(`pip`) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 꼭 필요한 대상 1~2개 | `@click.argument` | `--src` 꼴의 옵션 |
| 있어도 되고 없어도 되는 설정 | `@click.option` + `default` | 위치 인자 |
| 켜기/끄기 | `is_flag=True` 또는 `'--x/--no-x'` | 문자열 `'true'` 를 받아 비교 |
| 허용 값이 정해짐 | `click.Choice` · `click.IntRange` | 본문의 `if` 검사 |
| 하위 명령 여러 개 | `@click.group()` + `@cli.command()` | 첫 인자로 분기하는 큰 `if` |
| 위 명령의 값을 아래로 | `@click.pass_context` + `ctx.obj` | 전역 변수 |
| 비밀번호 | `prompt=True, hide_input=True` | 명령줄에 그대로 치게 하기 |
| 지우기 같은 위험한 명령 | `@click.confirmation_option` | 확인 없이 바로 실행 |
| 출력 | `click.echo` · `click.secho` | `print` |

## 핵심 문장

1. **Click 은 함수 위의 선언을 보고 명령줄을 해석해 함수 인자로 넘긴다** — 형 변환과 검사는 본문 전에 끝난다.
2. **option 은 `--이름` 꼴의 선택 값, argument 는 위치로 받는 필수 값이다.**
3. **`@click.group()` 으로 하위 명령 구조를 만들고, `ctx.obj` 로 부모와 자식이 상태를 나눈다.**
4. **출력은 `click.echo`, 꾸밈은 `secho`, 사용자 대화는 `confirm` · `prompt` · `edit` 로 한다.**
5. **`[project.scripts]` 에 `"모듈:함수"` 를 적으면 설치 후 이름 하나로 부를 수 있다.**

## 관련 자료

- [rich-output](../13-rich-output/2-summary.md)
- `packaging` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `click-cli`

## 용어 풀이

- **CLI** — 터미널에 글자를 쳐서 프로그램을 부리는 방식.
- **데코레이터** — 함수 위 `@이름` 으로 함수를 감싸거나 바꾸는 문법.
- **명령(command)** — `@click.command()` 로 바뀐, 터미널에서 부를 수 있는 함수.
- **옵션(option)** — `--이름` 꼴의 선택적 인자.
- **플래그(flag)** — 값 없이 이름만으로 켜는 불리언 옵션.
- **인자(argument)** — 이름표 없이 위치로 받는 필수 값.
- **그룹(group)** — 하위 명령을 담는 부모 명령.
- **하위 명령(서브커맨드)** — 그룹 아래 등록된 명령.
- **컨텍스트(`ctx`)** — 한 번의 실행 동안 Click 이 들고 다니는 상태, `ctx.obj` 에 사용자 값을 둔다.
- **docstring** — 함수 첫 줄의 설명 문자열.
- **컨텍스트 매니저** — `with` 로 열고 닫는 일을 묶는 객체.
- **콘솔 스크립트** — 설치 때 만들어져 이름만으로 부를 수 있는 실행 진입점.
- **`$EDITOR`** — 사용자가 쓸 편집기를 가리키는 환경 변수.

## 더 들어가면

- `click.echo` 는 출력이 터미널이 아닐 때(파이프 · 파일) 색 코드를 떼어 낸다고 알려져 있다(확인 필요).
- `@click.confirmation_option` 은 확인을 건너뛰는 `--yes` 옵션을 함께 만든다고 알려져 있다(확인 필요).
- `CliRunner().invoke(cli, ['create', 'x'])` 꼴로 부르고, 돌아온 결과의 `output` · `exit_code` 를 검사한다(확인 필요).
- `multiple=True` 옵션을 한 번도 안 주면 빈 튜플이 들어온다(확인 필요).
- `IntRange` 의 양 끝 값이 포함되는지, 범위 밖을 막는 대신 끝값으로 자르는 설정이 있는지는 문서를 볼 것(확인 필요).
- 검사에 걸리면 Click 은 사용법 안내와 오류 문구를 찍고 0 이 아닌 종료 코드로 끝난다(확인 필요).
