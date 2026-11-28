# python/python-advanced/04 — AST 조작 (코드 분석/변환) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 겹친 호출이 있는 코드를 `visit_Call` 로 훑으면 (예측)

```python
# 질문용 발췌 — CodeAnalyzer 의 visit_Call · _get_name 을 그대로 쓴다고 하자
src = """
data = json.load(open(path))
items = list(data.values())
print(len(items))
"""
analyzer = CodeAnalyzer()
analyzer.visit(ast.parse(src))
print(analyzer.function_calls)
```

- `function_calls` 에 어떤 이름들이 어떤 차례로 쌓이는가?

### 2. 분석기의 `visit_ClassDef` 끝에 있는 `generic_visit` (왜)

- `visit_ClassDef` 가 `self.generic_visit(node)` 를 부르지 않으면 `functions` 목록에서 무엇이 빠지고, 왜 그런가?

### 3. 디버그 변환기를 거친 함수를 하나만 부르면 (예측)

```python
# 질문용 발췌 — DebugTransformer 는 원본 그대로
source = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
tree = DebugTransformer().visit(ast.parse(source))
ast.fix_missing_locations(tree)
exec(compile(tree, '<string>', 'exec'))
result = add(3, 4)
print(f"add(3, 4) = {result}")
```

- 화면에 찍히는 줄은 무엇이고, `multiply` 쪽 로그는 찍히는가?

### 4. 변환기의 `visit_FunctionDef` 끝에 있는 `return node` (왜)

- `DebugTransformer.visit_FunctionDef` 에서 `return node` 를 지우면 변환된 나무의 함수 정의는 어떻게 되고, 왜 그런가?

### 5. 변환 뒤에 부르는 `fix_missing_locations` (왜)

- 나무를 고친 뒤 `compile()` 하기 전에 `ast.fix_missing_locations()` 를 부르는 까닭은 무엇인가?

### 6. `literal_eval` 에 두 문자열을 넣으면 (예측)

```python
# 질문용 발췌
a = ast.literal_eval("[1, 2, 3, (4, 5)]")
b = ast.literal_eval("__import__('os').system('ls')")
```

- `a` 에는 무엇이 들어가고, `b` 줄은 어떻게 끝나는가?

### 7. 문자열 필드가 하나도 없는 데이터클래스 생성 (경계)

- `generate_dataclass('Point', {'x': 'int', 'y': 'int'})` 가 만든 소스를 `exec` 하면 어디서 깨지는가?

### 8. `_get_name` 이 다루지 못하는 모양 (경계)

- `a().b()` 호출이나 `from . import x` 를 분석기에 넣으면 기록되는 이름은 어떻게 되는가?

### 9. `ast.unparse` 가 되살리지 못하는 것 (경계)

- 주석이 달린 코드를 `parse` 했다가 `unparse` 하면 무엇이 원본과 달라질 수 있고, 어느 버전부터 쓸 수 있는가?

### 10. 「쓰이지 않는 import」를 찾는 린터 (연결)

- `CodeAnalyzer` 를 넓혀 import 했지만 쓰지 않은 이름을 찾으려면 무엇을 더 모아 무엇과 비교하면 되는가?

## 실습

### 실습 1. AST 로 코드를 분석 · 변환 · 생성 · 평가 · 복원하기

**만들 것** — `ast` 모듈 하나로 코드 파싱, 분석기, 디버그 로그 주입 변환기, 데이터클래스 코드 생성기, 안전한 리터럴 평가, 소스 복원까지 여섯 단계를 차례로 보여 주는 스크립트.

**요구 조건**

1단계 — 파싱
1. `code` 문자열을 `ast.parse` 로 나무로 만들고, `ast.dump(..., indent=2)` 결과의 앞 300자를 찍은 뒤 `...` 을 찍는다.

2단계 — 분석(`CodeAnalyzer`, `ast.NodeVisitor` 상속)
2. 생성자에서 `functions` · `classes` · `imports` · `assignments` · `function_calls` 다섯 리스트를 만든다.
3. `visit_FunctionDef` 는 이름 · 위치 인자 이름 목록 · 줄 번호 · 데코레이터 이름 목록 · 반환 어노테이션을 딕셔너리로 `functions` 에 넣고 자식도 방문한다.
4. `visit_ClassDef` 는 이름 · 부모 클래스 이름 목록 · 본문의 메서드 이름 목록 · 줄 번호를 `classes` 에 넣고 자식도 방문한다.
5. `visit_Import` 는 모듈 이름을, `visit_ImportFrom` 은 `모듈.이름` 꼴을 `imports` 에 넣는다.
6. `visit_Call` 은 호출 대상의 이름을 얻을 수 있으면 `function_calls` 에 넣고 자식도 방문한다.
7. `_get_name` 은 `Name` 이면 이름, `Attribute` 면 왼쪽을 재귀로 풀어 `왼쪽.속성`, 그 밖에는 `None` 을 돌려준다.
8. `_get_annotation` 은 `None` 이면 `None`, 아니면 `_get_name` 결과를, 그것도 없으면 `ast.dump` 결과를 돌려준다.
9. `analysis_code` 를 분석해 함수 · 클래스 · 임포트 · 함수호출 네 목록을 찍는다.

3단계 — 변환(`DebugTransformer`, `ast.NodeTransformer` 상속)
10. `visit_FunctionDef` 는 `print("[DEBUG] 함수이름() 호출")` 문장 노드를 만들어 함수 본문 맨 앞에 끼우고, 자식을 변환하고, 위치를 보정한 뒤 노드를 돌려준다.
11. `source` 를 변환하고 위치를 보정한 뒤 `compile` · `exec` 로 실행하고, `add(3, 4)` 를 불러 결과를 찍는다.

4단계 — 코드 생성
12. `generate_dataclass(name, fields)` 는 `dataclass` import · `@dataclass` · 클래스 선언 · 필드 줄 · `__post_init__`(타입이 `'str'` 인 필드만 `.strip()`)을 줄 리스트로 만들어 `'\n'` 으로 이어 돌려준다.
13. `User` 클래스 소스를 만들어 찍고, `exec` 한 뒤 공백 섞인 값으로 `User` 를 만들어 찍는다.

5단계 — 안전한 평가
14. 딕셔너리 문자열과 리스트 문자열을 `ast.literal_eval` 로 바꿔 찍는다.
15. `__import__('os').system('ls')` 를 `literal_eval` 에 넣어 `ValueError` · `SyntaxError` 를 잡고 예외 이름을 찍는다.

6단계 — 복원과 정리
16. 리스트 컴프리헨션 한 줄을 `parse` 한 뒤 `ast.unparse` 로 되돌려 원본과 복원본을 나란히 찍는다.
17. 마지막에 AST 핵심 정리 여섯 줄을 찍는다.

**시작 코드**

```python
# AST (Abstract Syntax Tree) - 코드 분석과 변환
import ast
import inspect
import textwrap

# === 1. 코드 파싱 ===
print("=== AST 파싱 ===")
code = """
def greet(name):
    message = f"Hello, {name}!"
    print(message)
    return message

x = greet("World")
"""
tree = None  # TODO: code 를 AST 로
# TODO: dump(indent=2) 의 앞 300자 출력
print("...\n")


# === 2. NodeVisitor (코드 분석) ===
class CodeAnalyzer:  # TODO: 무엇을 상속하나
    """코드 분석기: 함수, 클래스, 변수 사용 추출"""

    def __init__(self):
        # TODO: 결과 리스트 다섯 개
        pass

    def visit_FunctionDef(self, node):
        # TODO: name / args / line / decorators / returns 수집
        # TODO: 자식 방문
        pass

    def visit_ClassDef(self, node):
        # TODO: name / bases / methods / line 수집, 자식 방문
        pass

    def visit_Import(self, node):
        pass  # TODO

    def visit_ImportFrom(self, node):
        pass  # TODO

    def visit_Call(self, node):
        pass  # TODO

    def _get_name(self, node):
        pass  # TODO: Name / Attribute / 그 밖

    def _get_annotation(self, node):
        pass  # TODO


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
analyzer = CodeAnalyzer()
# TODO: analysis_code 를 파싱해 순회
print(f"함수: {analyzer.functions}")
print(f"클래스: {analyzer.classes}")
print(f"임포트: {analyzer.imports}")
print(f"함수호출: {analyzer.function_calls}")


# === 3. NodeTransformer (코드 변환) ===
class DebugTransformer:  # TODO: 무엇을 상속하나
    """모든 함수에 디버그 로깅 추가"""

    def visit_FunctionDef(self, node):
        # TODO: print 문 노드 만들기 → 본문 맨 앞에 삽입 → 자식 변환 → 위치 보정 → 반환
        pass


print("\n=== 코드 변환 (디버그 주입) ===")
source = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
# TODO: 파싱 → 변환 → 위치 보정 → compile → exec
result = add(3, 4)
print(f"add(3, 4) = {result}")


# === 4. 코드 생성 ===
print("\n=== 코드 생성 ===")

def generate_dataclass(name, fields):
    """데이터클래스 코드 자동 생성"""
    # TODO: 헤더 줄 · 필드 줄 · __post_init__ (str 필드만 strip)
    pass

generated = generate_dataclass('User', {
    'name': 'str',
    'email': 'str',
    'age': 'int',
})
print(generated)
print()
# TODO: generated 실행
user = User(name='  Alice  ', email='  alice@test.com  ', age=30)
print(f"생성된 클래스 사용: {user}")


# === 5. ast.literal_eval (안전한 평가) ===
print("\n=== 안전한 리터럴 평가 ===")
# TODO: "{'a': 1, 'b': [2, 3]}" 평가 → "literal_eval dict: ..." 출력
# TODO: "[1, 2, 3, (4, 5)]" 평가 → "literal_eval list: ..." 출력
# TODO: "__import__('os').system('ls')" 를 막고 "악성 코드 차단: 예외이름" 출력


# === 6. 소스 코드로 역변환 (unparse) ===
print("\n=== AST -> 소스 코드 (Python 3.9+) ===")
code = "x = [i**2 for i in range(10) if i % 2 == 0]"
# TODO: parse → unparse
print(f"원본: {code}")
# TODO: print(f"복원: ...")


print("\nAST 핵심 정리")
print("="*50)
print("ast.parse(): 코드 -> AST 트리")
print("NodeVisitor: 읽기 전용 트리 순회 (분석)")
print("NodeTransformer: 트리 수정 (변환)")
print("ast.unparse(): AST -> 소스 코드 (3.9+)")
print("ast.literal_eval(): 안전한 리터럴 평가")
print("활용: 린터, 코드 생성, 자동 리팩토링, 보안 검사")
```

**확인 방법** — Python 3.9 이상에서 `python ast_manipulation.py` 로 돌려, 함수호출 목록에 `Path` · `open` · `json.load` 같은 이름이 있는지, `[DEBUG] add() 호출` 줄 뒤에 `add(3, 4) = 7` 이 나오는지, `User` 의 이름 · 이메일 공백이 깎였는지, `악성 코드 차단:` 줄이 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
