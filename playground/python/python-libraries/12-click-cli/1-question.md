# python/python-libraries/12 — Click CLI — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 예제 스크립트를 돌리면 처음 나오는 세 줄 (예측)

```python
# 질문용 발췌
print("=== 기본 명령어 ===")
print("""
import click

@click.command()
""")
```

- 출력의 첫 세 줄은 무엇인가?
- `click` 을 쓰는 코드인데도 이 스크립트가 명령을 실행하지 않는 까닭은 무엇인가?

### 2. `greet` 에 이름과 횟수를 주면 (예측)

```python
# 질문용 발췌
@click.option('--name', '-n', required=True, help='사용자 이름')
@click.option('--count', '-c', default=1, type=int, help='인사 횟수')
@click.option('--greeting', type=click.Choice(['hello', 'hi', 'hey']), default='hello')
def greet(name, count, greeting):
    for _ in range(count):
        click.echo(f'{greeting}, {name}!')
# 실행: python cli.py --name Alice --count 3
```

- 화면에 무엇이 몇 줄 나오는가?
- `--name` 을 빼고 `python cli.py --count 3` 으로 부르면 본문은 도는가?

### 3. `serve` 를 플래그 · 포트 · 태그 둘과 함께 부르면 (예측)

```python
# 질문용 발췌
@click.option('--verbose', '-v', is_flag=True)
@click.option('--port', type=click.IntRange(1024, 65535), default=8080)
@click.option('--tags', multiple=True)
@click.option('--password', prompt=True, hide_input=True)
def serve(verbose, port, tags, password):
    click.echo(f'Port: {port}')
    click.echo(f'Tags: {tags}')
    if verbose:
        click.echo('상세 모드 활성화')
# 실행: python cli.py -v --port 3000 --tags web --tags api
```

- 세 줄의 `echo` 가 나오기 전에 사용자는 무엇을 하게 되는가?
- `Tags:` 줄에는 어떤 꼴의 값이 찍히는가?

### 4. 함수 이름이 `list_projects` 인 하위 명령 (예측)

- 터미널에서 이 명령을 부를 때 치는 이름은 무엇인가?

### 5. `copy` 의 `src` 는 옵션이 아니라 인자로 받는다 (왜)

- 원본이 복사할 경로를 `--src` 옵션이 아니라 위치 인자로 받는 까닭은 무엇인가?
- `--all` 옵션에 `'show_all'` 이라는 이름을 하나 더 준 까닭은 무엇인가?

### 6. 출력을 `print()` 가 아니라 `click.echo()` 로 한다 (왜)

- 팁은 왜 CLI 출력에 `click.echo()` 를 권하는가?

### 7. `--debug` 를 놓는 자리 (경계)

- `python cli.py create --debug myproject` 처럼 하위 명령 뒤에 `--debug` 를 쓰면 어떻게 되는가?

### 8. 검사에 걸리는 값 (경계)

- `serve` 에 `--port 80` 을 주거나 `copy` 에 없는 파일 경로를 주면 함수 본문은 도는가?

### 9. `pyproject.toml` 등록과 `python cli.py` (연결)

- `mytool = "mypackage.cli:cli"` 를 등록하고 설치한 뒤의 `mytool create myproject` 는 원본의 어느 실행 줄과 같은 일을 하는가?

## 실습

### 실습 1. Click 구조를 여섯 절로 찍는 안내 스크립트

**만들 것** — Click CLI 의 여섯 가지 쓰임(기본 명령 · 옵션 타입 · 위치 인자 · 그룹 · 출력 도우미 · 진입점 등록)을 절 제목과 코드 조각 문자열로 차례로 찍는 스크립트를 만든다.

**준비물** — 파이썬만 있으면 된다. Click 코드는 문자열로 찍기만 하므로 `click` 을 설치하지 않아도 스크립트가 돈다(조각을 따로 돌려 보려면 `click` 이 필요하다).

**요구 조건**

1단계 — 틀
1. 절마다 `print("=== 절 이름 ===")` 한 줄과 `print("""…""")` 한 번을 쓴다.
2. 코드 조각 문자열은 여는 `"""` 바로 뒤에서 줄을 바꿔 시작한다.
3. 조각 안의 docstring 따옴표는 `\"\"\"` 로 이스케이프해 `"""` 로 찍히게 한다.

2단계 — 기본 명령어 절
4. `import click` 과 `greet` 명령을 적는다: `--name`/`-n` 필수 옵션, `--count`/`-c` 정수 옵션(기본 1), `--greeting` 은 `hello`·`hi`·`hey` 중 하나(기본 `hello`).
5. `greet` 는 docstring(도구 설명)을 갖고, `count` 번 `click.echo` 로 `{greeting}, {name}!` 을 찍는다.
6. 실행 예 주석 `python cli.py --name Alice --count 3` 을 단다.

3단계 — Option 다양한 타입 절
7. `serve` 명령에 일곱 옵션을 단다: 플래그 `--verbose`/`-v`, 경로 `--output`/`-o`, 셋 중 하나인 `--format`(`json`·`csv`·`yaml`), 1024~65535 범위의 `--port`(기본 8080), 여러 번 받는 `--tags`, 읽기용 파일 `--config`, 묻고 가리는 `--password`.
8. 본문은 포트와 태그를 `echo` 하고, `verbose` 이면 `상세 모드 활성화` 를 찍는다. 실행 예 주석을 단다.

4단계 — Argument 절
9. `copy` 명령에 존재 검사를 하는 `src` 인자와 검사 없는 `dst` 인자를 단다. 본문은 `Copying {src} -> {dst}` 를 찍는다. 실행 예 주석을 단다.

5단계 — 그룹 명령어 절
10. `--debug/--no-debug`(기본 꺼짐) 옵션과 컨텍스트를 받는 그룹 `cli` 를 만들고, `ctx.obj` 를 dict 로 보장한 뒤 `DEBUG` 를 넣는다.
11. 하위 명령 셋을 단다: 컨텍스트에서 `DEBUG` 를 읽어 디버그 줄을 더 찍는 `create(name)`, `--all` 플래그를 `show_all` 로 받는 `list_projects`, 삭제 전 확인을 받는 `delete(name)`.
12. 세 하위 명령의 실행 예 주석을 단다.

6단계 — 출력 도우미 · 등록 절
13. 출력 도우미 절에 색 출력 세 줄, 100칸 진행 바, 예/아니오 확인, 편집기 열기를 적는다.
14. 마지막 절(`setup.py / pyproject.toml 등록`)에 `[project.scripts]` 와 `mytool` 등록 줄, 설치 후 실행 예 주석을 적는다.

**시작 코드**

```python
# Click CLI 프레임워크 시연
# 실행 가능한 코드 + 구조 설명

print("=== 기본 명령어 ===")
print("""
import click

# TODO: greet 명령 — 옵션 셋(--name/-n 필수, --count/-c 정수 기본 1, --greeting Choice)
# TODO: docstring 을 \"\"\" 로 이스케이프해 적고, count 번 echo

# 실행: python cli.py --name Alice --count 3
""")

print("=== Option 다양한 타입 ===")
print("""
# TODO: @click.command() 와 일곱 옵션(verbose · output · format · port · tags · config · password)
def serve(verbose, output, format, port, tags, config, password):
    # TODO: Port / Tags 를 echo, verbose 면 '상세 모드 활성화'
    pass

# 실행: python cli.py -v --port 3000 --tags web --tags api
""")

print("=== Argument (위치 인자) ===")
print("""
# TODO: copy 명령 — src(존재 검사) · dst 인자, 'Copying {src} -> {dst}'

# 실행: python cli.py /path/to/source /path/to/dest
""")

print("=== 그룹 명령어 ===")
print("""
# TODO: 그룹 cli (--debug/--no-debug, pass_context, ctx.obj['DEBUG'])
# TODO: create · list_projects · delete 하위 명령

# 실행:
# python cli.py --debug create myproject
# python cli.py list-projects --all
# python cli.py delete myproject
""")

print("=== 출력 도우미 ===")
print("""
# 색상 출력
click.secho('성공!', fg='green', bold=True)
click.secho('경고!', fg='yellow')
click.secho('에러!', fg='red', bg='white')

# 진행 바
import time
# TODO: range(100) 을 '처리 중' 진행 바로 돌며 0.01초씩 쉬기

# 사용자 확인
# TODO: '계속하시겠습니까?' 를 묻고 예면 '진행합니다'

# 에디터 열기
# TODO: '기본 텍스트' 로 편집기 열기  # $EDITOR 실행
""")

print("=== setup.py / pyproject.toml 등록 ===")
print("""
# pyproject.toml
# TODO: [project.scripts] 에 mytool 을 mypackage.cli 의 cli 로 등록

# 설치 후: mytool create myproject
""")
```

**확인 방법** — `python click-cli.py` 로 돌려 여섯 절 제목이 차례로 나오고, 절마다 빈 줄 뒤에 코드 조각이 찍히며, docstring 이 `"""…"""` 로 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
