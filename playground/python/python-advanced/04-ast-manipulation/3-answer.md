# python/python-advanced/04 — AST 조작 (코드 분석/변환) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 바깥 호출이 먼저, 안쪽 호출이 나중 — `['json.load', 'open', 'list', 'data.values', 'print', 'len']`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
['json.load', 'open', 'list', 'data.values', 'print', 'len']
```

**왜 그런가**
- 나무는 위 문장부터 차례로 돌아간다.
- `visit_Call` 은 자기 이름을 **먼저** 넣고 `generic_visit` 으로 인자 속 호출을 **나중에** 방문한다.
- 그래서 `json.load(open(path))` 는 `json.load` → `open`, `print(len(items))` 는 `print` → `len` 차례다.
- `json.load` · `data.values` 는 `Attribute` 라 `_get_name` 이 왼쪽을 풀어 점으로 잇는다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. 클래스 안의 메서드(`__init__` · `load` · `process`)가 통째로 빠진다

- `visit_ClassDef` 를 정의하면 `ClassDef` 노드에서는 기본 `generic_visit` 대신 그 메서드만 불린다.
- 그 안에서 `generic_visit` 을 부르지 않으면 클래스 본문의 `FunctionDef` 노드로 아무도 내려가지 않아 `visit_FunctionDef` 가 불리지 않는다.
- 같은 까닭으로 메서드 안의 호출(`Path` · `open` · `json.load` 등)도 `function_calls` 에서 빠진다.
- `classes` 의 `methods` 목록은 `node.body` 를 직접 훑어 만드므로 그대로 채워진다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 3. `[DEBUG] add() 호출` 뒤에 `add(3, 4) = 7` — `multiply` 로그는 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[DEBUG] add() 호출
add(3, 4) = 7
```

**왜 그런가**
- 변환기는 두 함수 **정의** 모두의 본문 맨 앞에 `print` 문을 끼운다.
- `exec` 는 정의를 실행해 이름을 등록할 뿐이라, 이때는 아무것도 찍히지 않는다.
- `add(3, 4)` 를 부를 때 끼워 넣은 `print` 가 먼저 돌고, 원래 본문이 `7` 을 돌려준다.
- `multiply` 는 부르지 않았으므로 그 로그는 찍히지 않는다.
- 근거: 2-summary 「동작 방식 (3)」.

### 4. 함수 정의가 나무에서 사라진다 — `NodeTransformer` 는 반환값으로 자리를 채운다

- `return node` 가 없으면 메서드는 `None` 을 돌려준다.
- `NodeTransformer` 는 `visit_X` 의 반환값을 그 자리에 넣고, `None` 이면 그 노드를 지운다.
- 그래서 `def add` · `def multiply` 가 빠지고, 실행 뒤 `add(3, 4)` 는 이름을 찾지 못한다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 5. `compile()` 은 위치 정보가 빠진 노드를 받지 못하기 때문이다

- 모든 노드는 `lineno` · `col_offset` 을 가져야 `compile()` 을 통과한다.
- 변환하며 새로 끼운 노드에는 이 값이 없을 수 있으므로, `fix_missing_locations` 가 빠진 자리에 부모의 위치를 채운다.
- 원본의 `log_stmt` 는 `ast.parse` 로 얻어 이미 위치를 가지므로, 이 호출이 그 줄 번호를 원래 함수 위치로 고쳐 주지는 않는다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. `a` 는 `[1, 2, 3, (4, 5)]`, `b` 는 예외로 거부된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `a` 에는 리스트 `[1, 2, 3, (4, 5)]` 가 들어간다 — 안의 튜플까지 리터럴이다.
- `b` 줄은 셸 명령을 실행하지 않고 예외로 끝난다.
  문법은 맞고 리터럴이 아니므로 `ValueError` 쪽일 것이다(원본에 근거 없음 — 추론).
  원본은 이를 `except (ValueError, SyntaxError)` 로 잡아 `악성 코드 차단: <예외 이름>` 을 찍는다.

**왜 그런가**
- `literal_eval` 은 숫자 · 문자열 · 튜플 · 리스트 · 딕셔너리 · 집합 · 불 · `None` 리터럴만 받는다.
- `__import__(...)` 는 함수 호출이라 받아들일 수 없는 노드다.
- `eval` 이었다면 실제로 `os.system('ls')` 가 실행된다.
- 근거: 2-summary 「동작 방식 (5)」.

### 7. `__post_init__` 본문이 비어 `exec` 때 문법 오류가 난다

- `str` 필드가 없으면 `for` 안의 `if field_type == 'str'` 이 한 번도 참이 아니다.
- 그래서 소스는 `    def __post_init__(self):` 로 끝나고 그 아래 본문 줄이 없다.
- Python 은 본문 없는 `def` 를 허용하지 않으므로 `exec(generated)` 에서 들여쓰기 오류(`SyntaxError` 계열)가 난다(원본에 근거 없음 — 추론).
- 문자열 조립 방식은 문법 검사를 `exec` 시점까지 미루기 때문에 생기는 일이다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 7」.

### 8. 엉뚱하게 `'None.b'` · `'None.x'` 가 기록된다

- `a().b()` 의 호출 대상은 `Attribute(value=Call(...), attr='b')` 다.
- `_get_name` 은 왼쪽 `Call` 을 모르므로 `None` 을 돌려주고, f-문자열이 그것을 `'None'` 으로 이어 `'None.b'` 가 된다.
- 안쪽 `a()` 는 `generic_visit` 으로 방문되어 `'a'` 로 따로 기록된다.
- `from . import x` 는 `node.module` 이 `None` 이라 `'None.x'` 가 된다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 6」.

### 9. 주석과 원래 서식이 사라질 수 있고, 3.9 이상에서만 쓸 수 있다

- AST 는 주석 · 원래 띄어쓰기 · 따옴표 종류 같은 겉모양을 버린다.
- `unparse` 는 나무에 남은 정보로만 소스를 쓰므로 뜻은 같고 모양은 다를 수 있다.
- `ast.unparse()` 는 Python 3.9+ 에서만 있다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 10. 코드에서 쓰인 이름을 더 모아 `imports` 와 비교한다

- 지금 분석기는 `visit_Import` · `visit_ImportFrom` 으로 들여온 이름만 모은다.
- `visit_Name`(또는 `_get_name` 이 푸는 `Attribute` 의 맨 왼쪽 이름)으로 코드에서 **실제 쓰인 이름**을 모은다.
- 들여온 이름(`json` · `Path`) 가운데 쓰인 이름 집합에 없는 것이 「쓰이지 않는 import」다.
- 이것이 2-summary 「언제 쓰고 언제 안 쓰나」 의 린터 · 보안 검사 용도이고, 원본 정리 줄의 「활용: 린터」와 이어진다.
- `visit_Name` 을 정의한다는 세부는 정리 본문의 디스패치 규칙(`visit_<종류>`)에서 끌어낸 것이다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. AST 로 코드를 분석 · 변환 · 생성 · 평가 · 복원하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 파싱 · dump 앞 300자 | `tree = ast.parse(code)` · `ast.dump(tree, indent=2)[:300]` |
| 2. 결과 리스트 다섯 개 | `CodeAnalyzer.__init__` 의 `self.functions` … `self.function_calls` |
| 3. 함수 정보 수집 · 자식 방문 | `visit_FunctionDef` 의 `self.functions.append({...})` · `self.generic_visit(node)` |
| 4. 클래스 정보 수집 | `visit_ClassDef` 의 `bases` · `methods` · `self.classes.append` |
| 5. import 수집 | `visit_Import` 의 `alias.name` · `visit_ImportFrom` 의 `f"{node.module}.{alias.name}"` |
| 6. 호출 이름 수집 | `visit_Call` 의 `self._get_name(node.func)` · `if name:` |
| 7. 이름 풀기 | `_get_name` 의 `ast.Name` → `node.id`, `ast.Attribute` → 재귀 |
| 8. 어노테이션 풀기 | `_get_annotation` 의 `self._get_name(node) or ast.dump(node)` |
| 9. 분석 실행 · 출력 | `analyzer.visit(ast.parse(analysis_code))` · `print(f"함수: ...")` 네 줄 |
| 10. 디버그 문 주입 | `DebugTransformer.visit_FunctionDef` 의 `ast.parse(...).body[0]` · `node.body.insert(0, log_stmt)` · `ast.fix_missing_locations(node)` · `return node` |
| 11. 변환 · 실행 | `DebugTransformer().visit(tree)` · `exec(compile(transformed, '<string>', 'exec'))` · `add(3, 4)` |
| 12. 소스 조립 | `generate_dataclass` 의 `lines` · `if field_type == 'str'` · `'\n'.join(lines)` |
| 13. 생성 · 실행 · 사용 | `print(generated)` · `exec(generated)` · `User(name='  Alice  ', ...)` |
| 14. 리터럴 평가 | `ast.literal_eval("{'a': 1, 'b': [2, 3]}")` · `ast.literal_eval("[1, 2, 3, (4, 5)]")` |
| 15. 악성 문자열 차단 | `try` / `except (ValueError, SyntaxError) as e` · `type(e).__name__` |
| 16. 소스 복원 | `reconstructed = ast.unparse(tree)` · `print(f"복원: ...")` |
| 17. 정리 출력 | 끝의 `print("ast.parse(): ...")` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-advanced/reference/ast-manipulation.py`

```python
# [고급 기법] AST 조작 (코드 분석/변환)
# 설명: ast 모듈로 Python 코드 분석, 변환, 자동 코드 생성
# 팁: ast.literal_eval()은 eval()의 안전한 대안으로 리터럴만 평가한다. NodeVisitor는 분석용, NodeTransformer는 변환용이다. fix_missing_locations()로 변환 후 라인 번호를 보정해야 한다. ast.unparse()(Python 3.9+)로 AST를 소스 코드로 복원할 수 있다.

# AST (Abstract Syntax Tree) - 코드 분석과 변환

# ast: Python 소스 코드를 추상 구문 트리로 파싱/변환하는 표준 라이브러리
import ast
# inspect: 살아있는 객체의 소스/시그니처 조사 모듈
import inspect
# textwrap: 들여쓰기 조작용 (dedent 등)
import textwrap


# === 1. 코드 파싱 ===
print("=== AST 파싱 ===")
# 분석 대상 소스 코드 (문자열 형태)
code = """
def greet(name):
    message = f"Hello, {name}!"
    print(message)
    return message

x = greet("World")
"""

# ast.parse: 소스 문자열을 Module 노드를 루트로 갖는 AST 트리로 변환
tree = ast.parse(code)
# ast.dump: AST 노드를 사람이 읽기 쉬운 문자열로 직렬화 (indent로 들여쓰기)
print(ast.dump(tree, indent=2)[:300])  # AST 구조 출력
print("...\n")


# === 2. NodeVisitor (코드 분석) ===
# NodeVisitor: 트리를 순회하면서 visit_<NodeType> 메서드로 분석 (트리 변경 X)
class CodeAnalyzer(ast.NodeVisitor):
    """코드 분석기: 함수, 클래스, 변수 사용 추출"""

    # 분석 결과를 저장할 리스트들 초기화
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.assignments = []
        self.function_calls = []

    # FunctionDef 노드(함수 정의) 방문 시 호출되는 메서드
    def visit_FunctionDef(self, node):
        # 함수 메타데이터 수집
        self.functions.append({
            'name': node.name,
            # 위치 인자명 추출
            'args': [arg.arg for arg in node.args.args],
            # 노드 위치 (라인 번호)
            'line': node.lineno,
            # 데코레이터 식 -> 이름 변환
            'decorators': [self._get_name(d) for d in node.decorator_list],
            # 반환 타입 어노테이션
            'returns': self._get_annotation(node.returns),
        })
        # generic_visit: 자식 노드들도 자동 방문 (생략하면 트리 탐색이 멈춤)
        self.generic_visit(node)  # 자식 노드도 방문

    # ClassDef 노드(클래스 정의) 방문
    def visit_ClassDef(self, node):
        # 부모 클래스(베이스) 이름 목록
        bases = [self._get_name(b) for b in node.bases]
        # 클래스 본문에서 함수 정의만 추려 메서드명 수집
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        self.classes.append({
            'name': node.name,
            'bases': bases,
            'methods': methods,
            'line': node.lineno,
        })
        self.generic_visit(node)

    # Import 노드 방문 (import x, import y 형태)
    def visit_Import(self, node):
        # node.names는 alias 리스트 (각각 .name이 모듈명)
        for alias in node.names:
            self.imports.append(alias.name)

    # ImportFrom 노드 방문 (from x import y 형태)
    def visit_ImportFrom(self, node):
        for alias in node.names:
            # module.attr 형식으로 결합
            self.imports.append(f"{node.module}.{alias.name}")

    # Call 노드 방문 (함수/메서드 호출)
    def visit_Call(self, node):
        # node.func은 호출 대상 표현식 (Name 또는 Attribute)
        name = self._get_name(node.func)
        if name:
            self.function_calls.append(name)
        self.generic_visit(node)

    # 노드에서 식별자 이름 추출 (재귀로 점 표기 처리)
    def _get_name(self, node):
        # 단순 이름 노드 (예: foo)
        if isinstance(node, ast.Name):
            return node.id
        # 속성 접근 노드 (예: a.b.c)
        if isinstance(node, ast.Attribute):
            # 좌측 표현식을 재귀적으로 풀고 .attr 결합
            return f"{self._get_name(node.value)}.{node.attr}"
        return None

    # 어노테이션 노드를 사람이 읽기 쉬운 문자열로 변환
    def _get_annotation(self, node):
        if node is None:
            return None
        # 이름이면 이름 사용, 아니면 ast.dump로 원시 구조 노출
        return self._get_name(node) or ast.dump(node)


# 분석 대상 코드 (실제 사용 예)
analysis_code = """
import json
from pathlib import Path

class DataProcessor:
    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> dict:
        with open(self.path) as f:
            return json.load(f)

    def process(self, data: dict) -> list:
        return list(data.values())

processor = DataProcessor('data.json')
result = processor.load()
print(len(result))
"""

print("=== 코드 분석 ===")
# Analyzer 인스턴스 생성 및 트리 순회 시작
analyzer = CodeAnalyzer()
analyzer.visit(ast.parse(analysis_code))
print(f"함수: {analyzer.functions}")
print(f"클래스: {analyzer.classes}")
print(f"임포트: {analyzer.imports}")
print(f"함수호출: {analyzer.function_calls}")


# === 3. NodeTransformer (코드 변환) ===
# NodeTransformer: visit_*가 새 노드를 반환하면 그 자리에 교체됨 (트리 변경)
class DebugTransformer(ast.NodeTransformer):
    """모든 함수에 디버그 로깅 추가"""

    # 함수 정의를 만나면 print 문을 본문 맨 앞에 삽입
    def visit_FunctionDef(self, node):
        # 새 print 문을 파싱해서 첫 번째 statement 노드 추출
        log_stmt = ast.parse(
            f'print("[DEBUG] {node.name}() 호출")'
        ).body[0]

        # 기존 본문 리스트의 0번 인덱스에 삽입 (앞에 prepend)
        node.body.insert(0, log_stmt)

        # 자식 노드들도 변환 적용 (중첩 함수 대응)
        self.generic_visit(node)

        # fix_missing_locations: 새로 만든 노드의 lineno/col_offset을 부모로부터 채움
        # (없으면 compile 시 에러 발생)
        ast.fix_missing_locations(node)
        return node


print("\n=== 코드 변환 (디버그 주입) ===")
# 변환 대상 소스
source = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""

# 파싱 -> 변환 -> 라인 번호 보정
tree = ast.parse(source)
transformed = DebugTransformer().visit(tree)
ast.fix_missing_locations(transformed)

# compile: AST -> 코드 객체 / exec: 코드 객체 실행 (현재 모듈 네임스페이스에 등록)
exec(compile(transformed, '<string>', 'exec'))
# 변환된(디버그 print 삽입된) add 함수 호출
result = add(3, 4)
print(f"add(3, 4) = {result}")


# === 4. 코드 생성 ===
print("\n=== 코드 생성 ===")

# 데이터클래스 소스를 문자열로 동적 조립
def generate_dataclass(name, fields):
    """데이터클래스 코드 자동 생성"""
    # 헤더와 데코레이터, 클래스 선언 라인 준비
    lines = [
        'from dataclasses import dataclass',
        '',
        '@dataclass',
        f'class {name}:',
    ]
    # 필드 라인 추가 (name: type)
    for field_name, field_type in fields.items():
        lines.append(f'    {field_name}: {field_type}')

    # __post_init__ 메서드 추가 (str 필드만 strip 적용)
    lines.append('')
    lines.append('    def __post_init__(self):')
    for field_name, field_type in fields.items():
        if field_type == 'str':
            lines.append(f'        self.{field_name} = self.{field_name}.strip()')

    # 줄 단위 리스트를 하나의 소스로 결합
    return '\n'.join(lines)

# User 클래스 코드를 동적 생성
generated = generate_dataclass('User', {
    'name': 'str',
    'email': 'str',
    'age': 'int',
})
print(generated)
print()

# 생성된 소스를 exec로 실행 -> User 클래스가 현재 네임스페이스에 등록됨
exec(generated)
user = User(name='  Alice  ', email='  alice@test.com  ', age=30)
print(f"생성된 클래스 사용: {user}")


# === 5. ast.literal_eval (안전한 평가) ===
print("\n=== 안전한 리터럴 평가 ===")

# literal_eval은 숫자/문자열/튜플/리스트/딕셔너리/집합/불/None 리터럴만 허용 (코드 실행 X)
result = ast.literal_eval("{'a': 1, 'b': [2, 3]}")
print(f"literal_eval dict: {result}")

result = ast.literal_eval("[1, 2, 3, (4, 5)]")
print(f"literal_eval list: {result}")

# 함수 호출이 포함되면 거부됨 (eval과의 결정적 차이)
try:
    ast.literal_eval("__import__('os').system('ls')")
except (ValueError, SyntaxError) as e:
    print(f"악성 코드 차단: {type(e).__name__}")


# === 6. 소스 코드로 역변환 (unparse) ===
print("\n=== AST -> 소스 코드 (Python 3.9+) ===")
code = "x = [i**2 for i in range(10) if i % 2 == 0]"
tree = ast.parse(code)
# ast.unparse: AST 트리를 다시 Python 소스 문자열로 복원 (3.9+)
reconstructed = ast.unparse(tree)
print(f"원본: {code}")
print(f"복원: {reconstructed}")


print("\nAST 핵심 정리")
print("="*50)
print("ast.parse(): 코드 -> AST 트리")
print("NodeVisitor: 읽기 전용 트리 순회 (분석)")
print("NodeTransformer: 트리 수정 (변환)")
print("ast.unparse(): AST -> 소스 코드 (3.9+)")
print("ast.literal_eval(): 안전한 리터럴 평가")
print("활용: 린터, 코드 생성, 자동 리팩토링, 보안 검사")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 분석기와 변환기는 같은 디스패치 규칙(`visit_<종류>`)을 쓰고, 차이는 반환값이 쓰이느냐 하나다.
- `visit_X` 를 정의한 곳마다 자식을 볼 필요가 있으면 `generic_visit` 을 부른다 — 함수 · 클래스 · 호출에서는 부르고, import 에서는 부르지 않는다.
- 새 문장 노드는 `ast.parse("한 줄").body[0]` 로 얻는 것이 가장 짧다.
- 변환한 나무는 `fix_missing_locations` → `compile` → `exec` 차례를 지켜야 실행된다.
- 바깥 문자열은 `literal_eval` 로만 값으로 바꾸고, 예외 두 종류를 함께 잡는다.
- `unparse` 는 3.9+ 이고, 결과는 뜻만 같고 모양은 다를 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
