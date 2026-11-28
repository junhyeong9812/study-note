# python/python-libraries/12 — Click CLI — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 절 제목 · 빈 줄 · `import click` — 코드는 문자열로 찍힐 뿐이다

**출력**

```text
=== 기본 명령어 ===

import click
```

**왜 그런가**
첫 `print` 가 절 제목을 찍는다.
둘째 `print` 의 문자열은 여는 `"""` 바로 뒤가 줄바꿈이라 빈 줄로 시작하고, 그다음 줄이 `import click` 이다.
`import click` 과 데코레이터는 전부 문자열 안의 글자라 파이썬이 실행하지 않는다.
명령은 정의되지도 불리지도 않는다.
근거: 2-summary 「동작 방식 (7)」.

### 2. `hello, Alice!` 세 줄 — `--name` 이 빠지면 본문 전에 멈춘다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
hello, Alice!
hello, Alice!
hello, Alice!
```

**왜 그런가**
`--name Alice` 가 `name='Alice'` 가 된다.
`--count 3` 의 `'3'` 은 `type=int` 로 정수 3 이 된다.
`--greeting` 은 주지 않았으니 기본값 `hello` 다.
`range(3)` 만큼 돌며 `echo` 한다.
`--name` 은 `required=True` 라 빠지면 Click 이 함수를 부르기 전에 오류로 멈추고, 본문은 돌지 않는다.
근거: 2-summary 「동작 방식 (1)」.

### 3. 먼저 비밀번호를 입력하고, 태그는 튜플로 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
명령줄에 `--password` 가 없으므로 `prompt=True` 때문에 비밀번호 입력을 요구받는다.
`hide_input=True` 라 치는 글자는 화면에 보이지 않는다.
입력을 마치면 아래 세 줄이 나온다.

```text
Port: 3000
Tags: ('web', 'api')
상세 모드 활성화
```

**왜 그런가**
`3000` 은 `IntRange(1024, 65535)` 안이라 통과한다.
`multiple=True` 인 `--tags` 를 두 번 주었으니 두 값이 튜플로 모인다.
`-v` 는 `is_flag=True` 라 `verbose=True` 가 되어 마지막 줄이 찍힌다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 4」.

### 4. `list-projects`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`python cli.py list-projects --all` 처럼 밑줄을 하이픈으로 바꾼 이름으로 부른다.

**왜 그런가**
원본의 실행 예가 `list-projects` 로 부른다.
함수 이름의 밑줄이 명령 이름에서는 하이픈이 된다 — 이 변환은 파이썬이 아니라 Click 이 하는 일이다(버전에 따라 다를 수 있다 — 확인 필요).
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 7」, 「구현 세부사항 대 언어 보장」.

### 5. 복사할 대상은 꼭 필요한 값이고, `all` 은 내장 이름이다

복사 명령에서 원본 경로는 없으면 아무 일도 못 하는 필수 값이다.
argument 는 위치로 받는 필수 값이라 이름표 없이 `copy a b` 로 짧게 부를 수 있다.
`--all` 을 그대로 두면 매개변수 이름이 `all` 이 되어 내장 `all()` 을 가린다.
`'show_all'` 을 주면 매개변수 이름이 `show_all` 이 되어 그것을 피한다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 1 · 3」, 「문법」.

### 6. 유니코드와 파이프 처리가 더 안전하기 때문이다

팁에 따르면 `click.echo()` 는 `print()` 보다 유니코드 · 파이프 처리가 안전하다.
CLI 출력은 다른 프로그램으로 파이프되거나 한글 같은 유니코드를 담는 일이 잦다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 6」.

### 7. `create` 는 `--debug` 를 모르므로 오류가 난다

`--debug` 는 그룹 `cli` 에 선언된 옵션이다.
하위 명령 뒤에 쓰면 `create` 가 그 옵션을 받게 되는데, `create` 는 자기 인자 `name` 만 안다.
그래서 알 수 없는 옵션이라는 오류로 멈춘다(오류 문구는 확인 필요).
올바른 자리는 `python cli.py --debug create myproject` 처럼 그룹과 하위 명령 사이다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 2」.

### 8. 돌지 않는다 — 검사는 본문보다 먼저다

`80` 은 `IntRange(1024, 65535)` 밖이라 거부된다.
`click.Path(exists=True)` 는 없는 경로를 거부한다.
두 검사 모두 Click 이 함수를 부르기 전에 하므로 본문은 돌지 않는다.
근거: 2-summary 「동작 방식 (2) · (3)」, 「어디서 틀리나 8」.

### 9. `python cli.py create myproject` 와 같다

`[project.scripts]` 에 등록하면 설치할 때 `mytool` 콘솔 스크립트가 생긴다.
그 스크립트는 `mypackage.cli` 모듈의 그룹 `cli` 를 부른다.
그래서 `mytool create myproject` 는 `cli` 그룹에 `create myproject` 를 넘기는 것이고, 원본의 `python cli.py create myproject` 꼴(디버그 옵션 없이)과 같은 일을 한다.
근거: 2-summary 「동작 방식 (6)」.

## 실습 정답

### 실습 1. Click 구조를 여섯 절로 찍는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 절마다 제목 · 조각 출력 | `print("=== … ===")` 여섯 개와 각 `print("""…""")` |
| 2. 조각이 줄바꿈으로 시작 | `print("""` 다음 줄부터 내용 |
| 3. docstring 이스케이프 | `\"\"\"사용자에게 인사하는 CLI 도구\"\"\"` 등 |
| 4. `greet` 의 세 옵션 | `@click.option('--name', '-n', required=True, …)` · `'--count', '-c', default=1, type=int` · `type=click.Choice(['hello', 'hi', 'hey']), default='hello'` |
| 5. docstring · `count` 번 인사 | `for _ in range(count): click.echo(f'{greeting}, {name}!')` |
| 6. 실행 예 주석 | `# 실행: python cli.py --name Alice --count 3` |
| 7. `serve` 의 일곱 옵션 | `is_flag=True` · `click.Path()` · `click.Choice(['json', 'csv', 'yaml'])` · `click.IntRange(1024, 65535), default=8080` · `multiple=True` · `click.File('r')` · `prompt=True, hide_input=True` |
| 8. `serve` 본문 · 주석 | `click.echo(f'Port: {port}')` · `click.echo(f'Tags: {tags}')` · `if verbose:` · `# 실행: python cli.py -v --port 3000 --tags web --tags api` |
| 9. `copy` 인자 둘 | `@click.argument('src', type=click.Path(exists=True))` · `@click.argument('dst', type=click.Path())` · `Copying {src} -> {dst}` |
| 10. 그룹 `cli` | `@click.group()` · `'--debug/--no-debug', default=False` · `@click.pass_context` · `ctx.ensure_object(dict)` · `ctx.obj['DEBUG'] = debug` |
| 11. 하위 명령 셋 | `create(ctx, name)` 의 `ctx.obj['DEBUG']` · `@click.option('--all', 'show_all', is_flag=True)` · `@click.confirmation_option(prompt='정말 삭제하시겠습니까?')` |
| 12. 하위 명령 실행 예 | `# python cli.py --debug create myproject` 외 두 줄 |
| 13. 출력 도우미 | `click.secho` 세 줄 · `click.progressbar(range(100), label='처리 중')` · `click.confirm('계속하시겠습니까?')` · `click.edit('기본 텍스트')` |
| 14. 진입점 등록 | `[project.scripts]` · `mytool = "mypackage.cli:cli"` · `# 설치 후: mytool create myproject` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/click-cli.py`

```python
# [주요 라이브러리] Click CLI
# 설명: @click.command, @click.option, @click.argument, 그룹 명령어
# 팁: option은 --flag 형태의 선택적 인자, argument는 위치 기반 필수 인자다. @click.group()으로 서브커맨드 구조를 만든다. click.echo()는 print()보다 유니코드/파이프 처리가 안전하다. click.testing.CliRunner로 CLI 테스트가 가능하다.

# Click CLI 프레임워크 시연
# 실행 가능한 코드 + 구조 설명

# 섹션 헤더 출력: 가장 단순한 단일 명령어 예시
print("=== 기본 명령어 ===")
# @click.command로 함수를 CLI 명령으로 변환
# @click.option은 --name 같은 플래그 인자, required=True는 필수
# type=click.Choice는 허용값 제한, default는 기본값
# 함수 docstring은 --help 출력에 그대로 표시됨
print("""
import click

@click.command()
@click.option('--name', '-n', required=True, help='사용자 이름')
@click.option('--count', '-c', default=1, type=int, help='인사 횟수')
@click.option('--greeting', type=click.Choice(['hello', 'hi', 'hey']), default='hello')
def greet(name, count, greeting):
    \"\"\"사용자에게 인사하는 CLI 도구\"\"\"  # --help에 표시
    for _ in range(count):
        click.echo(f'{greeting}, {name}!')

# 실행: python cli.py --name Alice --count 3
""")

# 섹션 헤더 출력: 다양한 Option 타입 시연
print("=== Option 다양한 타입 ===")
# is_flag=True는 boolean 토글, click.Path()는 경로, click.IntRange는 범위 검증
# multiple=True는 같은 옵션 여러 번 받을 수 있음(튜플로 전달됨)
# prompt=True는 미입력 시 사용자에게 입력 요구, hide_input은 비밀번호 가림
# 함정: prompt와 required를 함께 쓰면 의도와 다르게 동작할 수 있음
print("""
@click.command()
@click.option('--verbose', '-v', is_flag=True, help='상세 출력')
@click.option('--output', '-o', type=click.Path(), help='출력 파일 경로')
@click.option('--format', type=click.Choice(['json', 'csv', 'yaml']))
@click.option('--port', type=click.IntRange(1024, 65535), default=8080)
@click.option('--tags', multiple=True, help='태그 (여러 번 지정 가능)')
@click.option('--config', type=click.File('r'), help='설정 파일')
@click.option('--password', prompt=True, hide_input=True, help='비밀번호')
def serve(verbose, output, format, port, tags, config, password):
    click.echo(f'Port: {port}')
    click.echo(f'Tags: {tags}')  # ('tag1', 'tag2')
    if verbose:
        click.echo('상세 모드 활성화')

# 실행: python cli.py -v --port 3000 --tags web --tags api
""")

# 섹션 헤더 출력: 위치 인자(argument) 사용법
print("=== Argument (위치 인자) ===")
# argument는 옵션과 달리 -- 플래그 없이 위치로 전달
# exists=True를 주면 존재하는 경로만 허용(자동 검증)
print("""
@click.command()
@click.argument('src', type=click.Path(exists=True))  # 필수 위치 인자
@click.argument('dst', type=click.Path())
def copy(src, dst):
    \"\"\"SRC 파일을 DST로 복사\"\"\"
    click.echo(f'Copying {src} -> {dst}')

# 실행: python cli.py /path/to/source /path/to/dest
""")

# 섹션 헤더 출력: 서브커맨드 그룹 패턴(git 스타일 CLI)
print("=== 그룹 명령어 ===")
# @click.group으로 부모 명령 정의 후 @cli.command로 서브 등록
# @click.pass_context와 ctx.obj로 부모-자식 간 상태 공유
# --debug/--no-debug 형태는 boolean 플래그 한 쌍을 자동 생성
# @click.confirmation_option은 실행 전 사용자에게 확인을 받는 안전장치
print("""
@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    \"\"\"프로젝트 관리 도구\"\"\"
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

@cli.command()
@click.argument('name')
@click.pass_context
def create(ctx, name):
    \"\"\"새 프로젝트 생성\"\"\"
    debug = ctx.obj['DEBUG']
    click.echo(f'Creating project: {name}')
    if debug:
        click.echo('[DEBUG] 디버그 모드')

@cli.command()
@click.option('--all', 'show_all', is_flag=True)
def list_projects(show_all):
    \"\"\"프로젝트 목록 조회\"\"\"
    click.echo('Projects: myapp, webapp, api')

@cli.command()
@click.argument('name')
@click.confirmation_option(prompt='정말 삭제하시겠습니까?')
def delete(name):
    \"\"\"프로젝트 삭제\"\"\"
    click.echo(f'Deleted: {name}')

# 실행:
# python cli.py --debug create myproject
# python cli.py list-projects --all
# python cli.py delete myproject
""")

# 섹션 헤더 출력: Click이 제공하는 출력/대화 도우미
print("=== 출력 도우미 ===")
# click.secho는 echo + 스타일(fg, bg, bold)
# click.progressbar는 컨텍스트 매니저 형태의 진행바
# click.confirm은 yes/no 확인, click.edit는 $EDITOR로 텍스트 편집
print("""
# 색상 출력
click.secho('성공!', fg='green', bold=True)
click.secho('경고!', fg='yellow')
click.secho('에러!', fg='red', bg='white')

# 진행 바
import time
with click.progressbar(range(100), label='처리 중') as bar:
    for item in bar:
        time.sleep(0.01)

# 사용자 확인
if click.confirm('계속하시겠습니까?'):
    click.echo('진행합니다')

# 에디터 열기
message = click.edit('기본 텍스트')  # $EDITOR 실행
""")

# 섹션 헤더 출력: 패키지 진입점으로 등록하는 방법
print("=== setup.py / pyproject.toml 등록 ===")
# [project.scripts] 항목에 등록하면 pip install 시 콘솔 스크립트 생성
print("""
# pyproject.toml
[project.scripts]
mytool = "mypackage.cli:cli"

# 설치 후: mytool create myproject
""")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 기본 명령어 ===

import click

@click.command()
@click.option('--name', '-n', required=True, help='사용자 이름')
@click.option('--count', '-c', default=1, type=int, help='인사 횟수')
@click.option('--greeting', type=click.Choice(['hello', 'hi', 'hey']), default='hello')
def greet(name, count, greeting):
    """사용자에게 인사하는 CLI 도구"""  # --help에 표시
    for _ in range(count):
        click.echo(f'{greeting}, {name}!')

# 실행: python cli.py --name Alice --count 3

=== Option 다양한 타입 ===

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='상세 출력')
@click.option('--output', '-o', type=click.Path(), help='출력 파일 경로')
@click.option('--format', type=click.Choice(['json', 'csv', 'yaml']))
@click.option('--port', type=click.IntRange(1024, 65535), default=8080)
@click.option('--tags', multiple=True, help='태그 (여러 번 지정 가능)')
@click.option('--config', type=click.File('r'), help='설정 파일')
@click.option('--password', prompt=True, hide_input=True, help='비밀번호')
def serve(verbose, output, format, port, tags, config, password):
    click.echo(f'Port: {port}')
    click.echo(f'Tags: {tags}')  # ('tag1', 'tag2')
    if verbose:
        click.echo('상세 모드 활성화')

# 실행: python cli.py -v --port 3000 --tags web --tags api

=== Argument (위치 인자) ===

@click.command()
@click.argument('src', type=click.Path(exists=True))  # 필수 위치 인자
@click.argument('dst', type=click.Path())
def copy(src, dst):
    """SRC 파일을 DST로 복사"""  
    click.echo(f'Copying {src} -> {dst}')

# 실행: python cli.py /path/to/source /path/to/dest

=== 그룹 명령어 ===

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    """프로젝트 관리 도구"""  
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

@cli.command()
@click.argument('name')
@click.pass_context
def create(ctx, name):
    """새 프로젝트 생성"""  
    debug = ctx.obj['DEBUG']
    click.echo(f'Creating project: {name}')
    if debug:
        click.echo('[DEBUG] 디버그 모드')

@cli.command()
@click.option('--all', 'show_all', is_flag=True)
def list_projects(show_all):
    """프로젝트 목록 조회"""  
    click.echo('Projects: myapp, webapp, api')

@cli.command()
@click.argument('name')
@click.confirmation_option(prompt='정말 삭제하시겠습니까?')
def delete(name):
    """프로젝트 삭제"""  
    click.echo(f'Deleted: {name}')

# 실행:
# python cli.py --debug create myproject
# python cli.py list-projects --all
# python cli.py delete myproject

=== 출력 도우미 ===

# 색상 출력
click.secho('성공!', fg='green', bold=True)
click.secho('경고!', fg='yellow')
click.secho('에러!', fg='red', bg='white')

# 진행 바
import time
with click.progressbar(range(100), label='처리 중') as bar:
    for item in bar:
        time.sleep(0.01)

# 사용자 확인
if click.confirm('계속하시겠습니까?'):
    click.echo('진행합니다')

# 에디터 열기
message = click.edit('기본 텍스트')  # $EDITOR 실행

=== setup.py / pyproject.toml 등록 ===

# pyproject.toml
[project.scripts]
mytool = "mypackage.cli:cli"

# 설치 후: mytool create myproject
````

**풀이 요점**
- 스크립트 자체는 문자열을 찍을 뿐이고, 배울 내용은 문자열 안의 Click 선언이다.
- 옵션은 `--이름` 꼴 선택 값, 인자는 위치 기반 필수 값이라는 구분이 `greet`·`serve` 와 `copy` 에서 갈린다.
- 값 검사(`required` · `Choice` · `IntRange` · `Path(exists=True)`)는 선언에 맡기고 본문에는 넣지 않는다.
- 그룹 패턴의 핵심은 `@click.group()` → `@cli.command()` 등록과 `pass_context` + `ctx.obj` 로 나누는 상태다.
- `'show_all'` 처럼 매개변수 이름을 따로 주면 내장 이름을 가리지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
