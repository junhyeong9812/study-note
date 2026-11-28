# python/python-advanced/04 — AST 조작 (코드 분석/변환) — 정리 (힌트)

> 출처 — study-site 항목 `python/ast-manipulation`(항목 데이터 `data/python/advanced-techniques.json`) · 정답 코드 study-practice `python/python-advanced/reference/ast-manipulation.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**AST 는 「국어 시간에 문장을 나무 그림으로 쪼개 그린 것」이다.**
「철수가 밥을 먹었다」를 주어 · 목적어 · 서술어 가지로 나누면, 글자 순서가 아니라 **문장의 짜임**이 보인다.
짜임이 보이면 「이 글에 서술어가 몇 개인가」를 셀 수 있고, 「모든 서술어 앞에 '빨리'를 끼워라」 같은 고치기도 기계적으로 할 수 있다.
Python 코드도 똑같은 구조다.
`ast.parse()` 가 소스 문자열을 나무로 쪼개고, `NodeVisitor` 가 그 나무를 돌며 세고, `NodeTransformer` 가 가지를 갈아 끼운다.

> **AST(추상 구문 트리)** — 소스 코드의 문법 구조를 노드와 가지로 나타낸 나무. 공백 · 주석 같은 겉모양은 버린다.\
> 예: `x = 1 + 2` 는 `Assign` 노드 아래에 대상 `Name(x)` 와 값 `BinOp(1, +, 2)` 가 달린 나무다.

| 비유 | 실체 |
|---|---|
| 문장 | 소스 코드 문자열 |
| 문장을 나무 그림으로 쪼개기 | `ast.parse()` |
| 주어 · 서술어 같은 가지 | `FunctionDef` · `Call` · `Name` 같은 노드 |
| 그림을 보며 서술어 세는 학생 | `NodeVisitor` (읽기만) |
| 그림의 가지를 바꿔 그리는 학생 | `NodeTransformer` (고쳐 쓰기) |
| 나무 그림을 다시 문장으로 읽기 | `ast.unparse()` |

```text
 소스 문자열 ──ast.parse()──▶  AST(나무) ──NodeVisitor────▶ 분석 결과(목록·통계)
                                   │
                                   └──NodeTransformer──▶ 고친 AST ──compile()──▶ 코드 객체 ──exec()──▶ 실행
                                                              │
                                                              └──ast.unparse()──▶ 다시 소스 문자열
```

## 이 주제가 답하려는 질문

1. 코드를 실행하지 않고 「어떤 함수 · 클래스 · import · 호출이 있나」를 어떻게 뽑아내나?
2. 코드를 손으로 고치지 않고 「모든 함수 맨 앞에 로그 한 줄」 같은 변환을 어떻게 자동으로 하나?
3. 코드를 기계가 만들어 실행하려면(코드 생성) 무엇을 거치나?
4. 바깥에서 들어온 문자열을 Python 값으로 바꿀 때 `eval()` 의 위험을 어떻게 피하나?

## 동작 방식

### (1) 파싱 — 문자열을 나무로

**언제 쓰나** — 모든 AST 작업의 첫걸음이다.
코드를 분석하든 변환하든 먼저 나무로 만든다.

```text
code = """
def greet(name):
    ...
x = greet("World")
"""
        │  ast.parse(code)
        ▼
Module
 ├─ body[0]: FunctionDef(name='greet', args=..., body=[...])
 └─ body[1]: Assign(targets=[Name('x')], value=Call(func=Name('greet'), args=[Constant('World')]))
        │  ast.dump(tree, indent=2)
        ▼
사람이 읽을 수 있는 나무 모양 문자열
```

- `ast.parse(code)` 는 소스 문자열을 받아 **`Module` 노드를 뿌리로 하는 나무**를 돌려준다.
- 소스의 맨 위 문장들은 `Module.body` 리스트에 차례대로 들어간다.
- 함수 정의는 `FunctionDef`, 호출은 `Call`, 이름은 `Name`, 상수는 `Constant` 같은 노드 종류로 갈린다.
- 각 노드는 자기 위치인 `lineno`(줄 번호) · `col_offset`(칸 위치)를 속성으로 갖는다.
- `ast.dump(tree, indent=2)` 는 나무를 들여쓴 문자열로 바꿔 보여 준다 — 원본 예제는 너무 길어서 앞 300자만 잘라 찍는다.

> **노드** — AST 의 한 마디. 종류(클래스 이름)와 필드(자식 노드 · 값)를 가진다.\
> 예: `Call` 노드는 `func`(부를 대상) · `args`(위치 인자) · `keywords`(키워드 인자) 필드를 가진다.

### (2) NodeVisitor — 나무를 돌며 읽기(분석)

**언제 쓰나** — 코드에 무엇이 있는지 **세거나 모으기만** 하고 나무는 그대로 둘 때.
린터 · 의존성 목록 뽑기 · 보안 검사가 여기에 해당한다.

```text
analyzer.visit(tree)
   │  노드 종류 이름으로 메서드를 찾는다
   ├─ FunctionDef 노드 → visit_FunctionDef(node) 호출
   ├─ ClassDef 노드    → visit_ClassDef(node) 호출
   ├─ Import 노드      → visit_Import(node)
   ├─ ImportFrom 노드  → visit_ImportFrom(node)
   ├─ Call 노드        → visit_Call(node)
   └─ 그 밖의 노드     → generic_visit(node) = 자식들에게 visit 을 차례로 넘김
                                  │
             visit_X 안에서 self.generic_visit(node) 를 부르면 X 의 자식으로 내려간다
             부르지 않으면 X 아래는 아무도 보지 않는다
```

- `visit(node)` 는 노드의 클래스 이름 `X` 를 보고 `visit_X` 메서드가 있으면 그것을, 없으면 `generic_visit` 을 부른다.
- `generic_visit(node)` 는 노드의 자식들을 필드 차례대로 돌며 각각 `visit` 을 부른다.
- 그래서 `visit_X` 를 직접 정의했다면 **그 안에서 `self.generic_visit(node)` 를 불러야** 아래로 계속 내려간다.
- 원본의 `CodeAnalyzer` 는 이렇게 모은다:
  - `visit_FunctionDef` — 이름 `node.name`, 위치 인자 이름 `[arg.arg for arg in node.args.args]`, 줄 번호 `node.lineno`, 데코레이터 이름, 반환 어노테이션 `node.returns`.
  - `visit_ClassDef` — 이름, 부모 클래스 `node.bases`, 본문 중 `FunctionDef` 만 추린 메서드 이름, 줄 번호.
  - `visit_Import` — `import json` 의 `alias.name` 을 그대로(`'json'`).
  - `visit_ImportFrom` — `from pathlib import Path` 를 `f"{node.module}.{alias.name}"` 로 묶는다(`'pathlib.Path'`).
  - `visit_Call` — 호출 대상 `node.func` 의 이름을 모은다.
- `visit_Call` 은 이름을 먼저 기록하고 **그다음** `generic_visit` 을 부른다.
  그래서 `print(len(x))` 처럼 겹친 호출은 바깥(`print`) → 안(`len`) 차례로 쌓인다.
- `_get_name` 은 이름 꺼내기 도우미다.
  `Name` 이면 `node.id`, `Attribute`(점 접근)면 왼쪽을 재귀로 풀어 `"왼쪽.attr"`, 그 밖의 노드면 `None` 을 돌려준다.
  예: `json.load` → `Attribute(value=Name('json'), attr='load')` → `'json.load'`.

> **디스패치** — 값의 종류를 보고 부를 함수를 골라 주는 일.\
> 예: `Call` 노드면 `visit_Call` 이 골라진다.

### (3) NodeTransformer — 나무를 고쳐 쓰기(변환)

**언제 쓰나** — 코드를 **바꾼 결과**가 필요할 때.
로그 주입 · 자동 리팩토링 · 코드 계측이 여기에 해당한다.

```text
DebugTransformer().visit(tree)
   │
   ▼ FunctionDef(add) 를 만남 → visit_FunctionDef(node)
   │   1. ast.parse('print("[DEBUG] add() 호출")').body[0] 로 print 문 노드를 만든다
   │   2. node.body.insert(0, log_stmt)  — 본문 맨 앞에 끼운다
   │   3. self.generic_visit(node)       — 안쪽(중첩 함수 등)도 변환
   │   4. ast.fix_missing_locations(node)
   │   5. return node                    — 돌려준 노드가 원래 자리에 들어간다
   ▼
def add(a, b):                       def multiply(a, b):
    print("[DEBUG] add() 호출")          print("[DEBUG] multiply() 호출")
    return a + b                         return a * b
   │
   ▼ ast.fix_missing_locations(transformed)
   ▼ compile(transformed, '<string>', 'exec')  → 코드 객체
   ▼ exec(코드 객체)                           → add, multiply 가 지금 이름공간에 생긴다
```

- `NodeTransformer` 는 `NodeVisitor` 와 같은 방식으로 돈다.
- 다른 점은 **`visit_X` 의 반환값이 그 자리를 차지한다**는 것이다.
  같은 노드를 돌려주면 유지, 새 노드를 돌려주면 교체, `None` 을 돌려주면 그 노드는 나무에서 빠진다.
- 그래서 변환기의 `visit_X` 는 끝에 반드시 `return node`(또는 새 노드)를 써야 한다.
- 새 문장 노드를 손으로 조립하는 대신 `ast.parse("한 줄 코드").body[0]` 로 얻는 것이 원본의 꾀다.
  `parse` 는 `Module` 을 주므로 `.body[0]` 으로 첫 문장 노드만 꺼낸다.
- `ast.fix_missing_locations()` 는 위치 정보(`lineno` · `col_offset`)가 **없는** 노드에 부모의 위치를 채워 준다.
  `compile()` 은 위치 정보가 없는 노드를 받지 못하므로, 변환 뒤 이 호출로 보정한다.
- `compile(tree, '<string>', 'exec')` 는 AST 를 코드 객체로 바꾸고, `exec()` 가 그것을 실행한다.
  모듈 맨 위에서 실행하면 `def add` 가 그 모듈 이름공간에 등록되어 바로 `add(3, 4)` 를 부를 수 있다.
- 변환은 함수 **정의**를 바꾼 것이라, 로그는 그 함수를 **부를 때마다** 찍힌다.
  부르지 않은 함수의 로그는 찍히지 않는다.

### (4) 코드 생성 — 문자열을 이어 붙여 실행

**언제 쓰나** — 틀이 정해진 코드(데이터클래스 · 설정 클래스)를 이름과 필드만 바꿔 찍어 낼 때.

```text
generate_dataclass('User', {'name': 'str', 'email': 'str', 'age': 'int'})
   │  줄 리스트를 만든다
   ▼
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int

    def __post_init__(self):
        self.name = self.name.strip()      ← 타입이 'str' 인 필드만
        self.email = self.email.strip()
   │  '\n'.join(lines) → exec(generated)
   ▼
User 클래스가 이름공간에 생김 → User(name='  Alice  ', ...) 의 name 은 앞뒤 공백이 깎인다
```

- 원본의 4절은 AST 를 만들지 않고 **소스 문자열을 줄 단위로 조립**한 뒤 `exec()` 로 실행한다.
- 필드 줄은 `f'    {field_name}: {field_type}'` 로 들여쓰기 4칸을 붙여 만든다.
- `__post_init__` 은 데이터클래스의 생성자가 필드를 채운 **뒤에** 불리는 메서드다.
  여기서는 타입이 `'str'` 인 필드에만 `.strip()` 줄을 넣는다.
- 문자열 조립은 쉽지만, 들여쓰기나 빈 본문 같은 **문법 실수를 `exec` 할 때에야** 알게 된다.

> **`__post_init__`** — `@dataclass` 가 만든 `__init__` 이 필드를 다 채운 다음 이어 부르는 메서드.\
> 예: 입력값 정리(공백 제거) · 검증을 여기서 한다.

### (5) `ast.literal_eval` — 리터럴만 받는 안전한 평가

**언제 쓰나** — 설정 파일 · 사용자 입력 같은 **믿을 수 없는 문자열**을 리스트 · 딕셔너리 값으로 바꿀 때.

```text
"{'a': 1, 'b': [2, 3]}"           ──literal_eval──▶ {'a': 1, 'b': [2, 3]}
"[1, 2, 3, (4, 5)]"               ──literal_eval──▶ [1, 2, 3, (4, 5)]
"__import__('os').system('ls')"   ──literal_eval──▶ 예외(호출이 섞여 거부)
                                   ──eval────────▶ 실제로 셸 명령이 실행된다(위험)
```

- `literal_eval` 은 숫자 · 문자열 · 튜플 · 리스트 · 딕셔너리 · 집합 · 불 · `None` **리터럴**만 받아들인다.
- 함수 호출 · 이름 참조 · 속성 접근처럼 **무언가를 실행해야 하는 것**이 섞이면 거부한다.
- 원본은 거부를 `except (ValueError, SyntaxError)` 로 잡는다.
  문법이 맞지만 리터럴이 아니면 `ValueError` 쪽, 문법부터 틀리면 `SyntaxError` 쪽이다.
- `eval()` 은 임의의 식을 실행하므로, 바깥 문자열에 쓰면 그 문자열을 만든 사람이 코드를 실행할 수 있다.

> **리터럴** — 코드에 값을 글자 그대로 적은 것.\
> 예: `42` · `'hi'` · `[1, 2]` · `{'a': 1}` · `None`.

### (6) `ast.unparse` — 나무를 다시 소스로

**언제 쓰나** — 변환한 AST 를 사람이 읽을 소스로 저장 · 확인할 때(Python 3.9+).

```text
"x = [i**2 for i in range(10) if i % 2 == 0]"
   │ ast.parse
   ▼
Module(body=[Assign(targets=[Name('x')], value=ListComp(...))])
   │ ast.unparse
   ▼
같은 뜻의 소스 문자열 (띄어쓰기 · 괄호 같은 겉모양은 원본과 다를 수 있다)
```

- `unparse` 는 AST 가 가진 정보만으로 소스를 다시 쓴다.
- AST 는 주석 · 원래 띄어쓰기 · 따옴표 종류 같은 겉모양을 버리므로, 복원본은 **뜻은 같고 모양은 다를 수 있다**.
- Python 3.9 이상에서만 쓸 수 있다.

## 문법 — 형태와 규칙

```python
import ast

class CallCounter(ast.NodeVisitor):        # 분석: 읽기만
    def __init__(self):
        self.count = 0
    def visit_Call(self, node):
        self.count += 1
        self.generic_visit(node)            # 안쪽 호출도 세려면 필수

class Doubler(ast.NodeTransformer):        # 변환: 반환값이 그 자리를 차지
    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return ast.Constant(node.value * 2)
        return node

tree = ast.parse("print(len([1, 2]))")
c = CallCounter(); c.visit(tree)            # c.count 는 2
new = ast.fix_missing_locations(Doubler().visit(tree))
src = ast.unparse(new)                      # 상수가 두 배가 된 소스
```

- `ast.parse(소스)` → `Module` 나무. 맨 위 문장들은 `.body` 리스트다.
- `ast.dump(나무, indent=2)` → 나무 구조를 문자열로.
- 분석 클래스는 `ast.NodeVisitor` 를 상속하고 `visit_<노드종류>` 메서드를 정의한다.
- 변환 클래스는 `ast.NodeTransformer` 를 상속하고 `visit_<노드종류>` 에서 **노드를 반환**한다.
- 자식으로 내려가려면 `visit_X` 안에서 `self.generic_visit(node)` 를 부른다.
- 순회 시작은 `인스턴스.visit(나무)` 다.
- 변환 뒤 실행하려면 `ast.fix_missing_locations(나무)` → `compile(나무, '<string>', 'exec')` → `exec(코드객체)`.
- 안전한 값 변환은 `ast.literal_eval(문자열)`.
- 소스 복원은 `ast.unparse(나무)` (3.9+).
- 자주 보는 노드 필드:

| 노드 | 주요 필드 | 뜻 |
|---|---|---|
| `FunctionDef` | `name` · `args.args` · `body` · `decorator_list` · `returns` · `lineno` | 함수 정의 |
| `ClassDef` | `name` · `bases` · `body` · `lineno` | 클래스 정의 |
| `Import` | `names`(각 `alias.name`) | `import x` |
| `ImportFrom` | `module` · `names` | `from x import y` |
| `Call` | `func` · `args` · `keywords` | 호출 |
| `Name` | `id` | 이름 하나 |
| `Attribute` | `value` · `attr` | 점 접근 `a.b` |

## 어디서 틀리나

### 1. `generic_visit` 을 빠뜨리면 아래가 통째로 안 보인다

`visit_ClassDef` 를 정의하고 `self.generic_visit(node)` 를 부르지 않으면, 클래스 안의 메서드 정의와 호출은 방문되지 않는다.
원본의 `CodeAnalyzer` 가 `visit_FunctionDef` · `visit_ClassDef` · `visit_Call` 끝마다 `generic_visit` 을 부르는 까닭이다.
반면 `visit_Import` · `visit_ImportFrom` 은 부르지 않는데, 그 아래에는 더 볼 것이 없어서 괜찮다.

### 2. NodeVisitor 는 분석용, NodeTransformer 는 변환용이다

원본 팁 그대로다.
`NodeVisitor` 의 `visit_X` 반환값은 버려지므로 나무를 바꾸려면 `NodeTransformer` 를 써야 한다.
거꾸로 `NodeTransformer` 에서 `return` 을 잊으면 `None` 이 반환되어 그 노드가 나무에서 **사라진다**.

### 3. 변환 뒤에는 `fix_missing_locations()` 로 위치를 보정한다

원본 팁 그대로다.
손으로 만든 노드(`ast.Constant(...)` 처럼)는 `lineno` 가 없어서 그대로 `compile()` 하면 실패한다.
원본 주석은 「새로 만든 노드의 lineno/col_offset 을 부모로부터 채움 (없으면 compile 시 에러 발생)」이라 적는다.
다만 원본의 `log_stmt` 는 `ast.parse(...)` 로 얻은 노드라 이미 `lineno` 를 가진다(그 짧은 문자열 안의 1번 줄).
`fix_missing_locations` 는 **없는** 위치만 채우므로, 이 노드의 줄 번호를 원래 함수 위치로 고쳐 주지는 않는다(원본에 근거 없음 — 추론).
→ 「위치를 맞춰 준다」기보다 「빠진 위치를 메워 compile 을 통과시킨다」로 이해하는 편이 정확하다.

### 4. `literal_eval` 은 `eval` 의 안전한 대안이지만, 리터럴만 된다

원본 팁 그대로다.
`"1 + 2"` 처럼 계산식이나 `"x"` 같은 이름은 기대한 대로 되지 않을 수 있다 — 리터럴 바깥이라 거부 대상이다(확인 필요).
값을 계산해야 하면 `literal_eval` 로 해결할 일이 아니다.

### 5. `ast.unparse()` 는 Python 3.9+ 에서만 있다

원본 팁 그대로다.
3.8 이하에서는 `AttributeError` 가 난다(원본에 근거 없음 — 추론).
또 주석과 원래 서식은 복원되지 않는다.

### 6. `_get_name` 이 모르는 노드를 만나면 `None` 이 섞인다

`_get_name` 은 `Name` · `Attribute` 만 다룬다.
`a().b()` 처럼 점 왼쪽이 호출이면 왼쪽이 `None` 이 되어 `f"{None}.b"` → `'None.b'` 라는 엉뚱한 이름이 기록된다.
`(lambda: 1)()` 처럼 호출 대상 자체가 `Name` · `Attribute` 가 아니면 `None` 이 나와 `if name:` 에서 걸러진다.
`from . import x` 같은 상대 import 는 `node.module` 이 `None` 이라 `'None.x'` 가 된다(원본에 근거 없음 — 추론).

### 7. 문자열로 조립한 코드는 실행해야 틀린 줄 안다

`generate_dataclass` 에 `str` 필드가 하나도 없으면 `def __post_init__(self):` 아래 본문이 비어 `exec` 때 문법 오류(들여쓰기 오류)가 난다.
문자열 조립은 문법 검사를 `exec` 시점으로 미룬다.

### 8. `exec` 로 생긴 이름은 코드에 보이지 않는다

`exec` 뒤에 부르는 `add` · `User` 는 소스 어디에도 `def` · `class` 로 적혀 있지 않다.
편집기 · 린터는 이 이름을 「정의되지 않은 이름」으로 볼 수 있다.

### 9. 원본에 쓰이지 않는 것이 있다

`inspect` · `textwrap` 은 import 만 하고 쓰지 않는다.
`self.assignments` 는 만들어 두고 채우지 않는다.
`DebugTransformer` 는 `visit_FunctionDef` 안에서 한 번, 바깥에서 한 번 `fix_missing_locations` 를 부른다 — 바깥 한 번이면 충분하다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `ast` 모듈의 노드 종류 · 필드 이름 | CPython 표준 라이브러리. 버전 사이에 바뀔 수 있다(확인 필요) |
| `ast.unparse()` 는 3.9 이상 | 원본 팁의 주장. CPython 표준 라이브러리의 버전 조건 |
| `unparse` 결과의 띄어쓰기 · 괄호 모양 | 구현 세부사항. 뜻은 같지만 글자 모양은 정해져 있지 않다 |
| `ast.dump()` 의 문자열 모양 | 구현 세부사항. 버전마다 다를 수 있다(확인 필요) |
| `literal_eval` 이 호출을 거부한다 | `ast` 모듈 문서의 약속(확인 필요) |
| 「`fix_missing_locations` 가 없으면 compile 에러」 | 원본 주석의 주장. 위치가 **없는** 노드가 있을 때만 맞다 — `ast.parse` 로 얻은 노드만 끼웠다면 위치가 이미 있다(원본에 근거 없음 — 추론) |
| 모듈 맨 위 `exec` 로 정의한 이름이 바로 보인다 | 인자 없는 `exec` 가 현재 전역 이름공간을 쓰는 동작. 함수 안에서는 다르게 동작한다(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 코드에 있는 함수 · import · 호출 목록 뽑기 | `NodeVisitor` | 정규식으로 소스 문자열 뒤지기 |
| 모든 함수에 로그 · 계측 끼우기 | `NodeTransformer` + `fix_missing_locations` | 소스 문자열 치환 |
| 바깥 문자열을 리스트 · 딕셔너리로 | `ast.literal_eval` | `eval` |
| 정형화된 클래스 코드 찍어 내기 | 문자열 조립 + `exec` (작을 때) | 사람이 읽고 고칠 일반 코드에 남발 |
| 변환 결과를 사람에게 보여 주기 | `ast.unparse` (3.9+) | 주석까지 살려야 할 때 — AST 는 주석을 버린다 |
| 린터 · 보안 검사 · 자동 리팩토링 | `ast` 전반 | 실행해 봐야 아는 동작(런타임 값) 분석 |

## 핵심 문장

1. **`ast.parse()` 는 코드를 `Module` 을 뿌리로 하는 나무로 바꾸고, 모든 분석 · 변환은 그 나무 위에서 한다.**
2. **`NodeVisitor` 는 읽기, `NodeTransformer` 는 고쳐 쓰기다** — 변환기의 `visit_X` 가 돌려준 노드가 그 자리를 차지한다.
3. **`visit_X` 를 정의했으면 `generic_visit` 을 불러야 아래로 내려간다.**
4. **변환한 나무는 `fix_missing_locations` → `compile` → `exec` 로 실행하고, `unparse` 로 소스로 되돌린다.**
5. **믿을 수 없는 문자열은 `eval` 이 아니라 리터럴만 받는 `literal_eval` 로 바꾼다.**

## 관련 자료

- `import-system` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `metaclass-advanced` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/advanced-techniques.json` 의 `ast-manipulation`

## 용어 풀이

- **AST(추상 구문 트리)** — 소스 코드의 문법 구조를 노드 나무로 나타낸 것. 겉모양(공백 · 주석)은 버린다.
- **파싱** — 문자열을 문법 구조(나무)로 쪼개는 일.
- **노드** — AST 의 한 마디. 종류와 필드를 가진다.
- **`Module`** — `ast.parse` 결과의 뿌리 노드. 맨 위 문장들이 `.body` 에 들어 있다.
- **`NodeVisitor`** — 나무를 돌며 `visit_<종류>` 메서드를 불러 주는 분석용 바탕 클래스.
- **`NodeTransformer`** — `NodeVisitor` 처럼 돌되, 반환값으로 노드를 교체 · 삭제하는 변환용 바탕 클래스.
- **`generic_visit`** — 노드의 자식들을 차례로 방문하는 기본 동작.
- **디스패치** — 노드 종류를 보고 부를 메서드를 고르는 일.
- **`lineno` / `col_offset`** — 노드가 소스의 몇째 줄 · 몇째 칸에 있는지.
- **`fix_missing_locations`** — 위치 정보가 빠진 노드에 부모의 위치를 채워 주는 함수.
- **`compile`** — 소스나 AST 를 실행할 수 있는 코드 객체로 바꾸는 내장 함수.
- **`exec`** — 코드(문자열 또는 코드 객체)를 실행하는 내장 함수.
- **리터럴** — 값을 글자 그대로 적은 코드 조각.
- **`literal_eval`** — 리터럴로 된 문자열만 값으로 바꾸는 안전한 평가 함수.
- **`unparse`** — AST 를 소스 문자열로 되돌리는 함수(3.9+).
- **`__post_init__`** — 데이터클래스 생성자가 필드를 채운 뒤 부르는 메서드.
- **린터** — 코드를 실행하지 않고 문제를 찾아 주는 도구.

## 더 들어가면

- `ast.dump` 의 `indent` 인자는 3.9 에서 들어왔다(확인 필요).
- `ast.parse` 에 `type_comments=True` · `feature_version` 같은 선택 인자가 있다(확인 필요).
- `ast.walk(tree)` 는 순서를 따지지 않고 모든 노드를 한 번씩 내놓는 생성기라, 단순 집계에는 클래스 없이도 쓸 수 있다(확인 필요).
- `ast.copy_location(new, old)` 는 옛 노드의 위치를 새 노드에 옮겨 줘서, 변환 뒤 오류 줄 번호를 원래 코드에 맞추는 데 쓴다(확인 필요).
- `async def` 는 `FunctionDef` 가 아니라 `AsyncFunctionDef` 노드라, 원본의 `visit_FunctionDef` 만으로는 비동기 함수를 놓친다(확인 필요).
- 위치 인자 이름만 `node.args.args` 에 있고, `*args` · 키워드 전용 인자 · 위치 전용 인자는 다른 필드(`vararg` · `kwonlyargs` · `posonlyargs`)에 있다(확인 필요).
- `literal_eval` 도 아주 깊게 중첩된 입력에서는 인터프리터를 멈추게 할 수 있다는 경고가 문서에 있다 — 완전한 샌드박스는 아니다(확인 필요).
- `literal_eval` 은 bytes 리터럴과 `...`(Ellipsis)도 받는다고 알려져 있다(확인 필요).
- 주석 · 서식까지 보존하며 고쳐 쓰려면 표준 `ast` 대신 구체 구문 트리(CST)를 다루는 외부 도구를 쓰기도 한다(확인 필요).
