# language/03-parsing-grammars-ast — 정답

## 정답

### 1. 괄호 짝과 스택

- 유한 오토마타는 상태가 유한하다. 여는 괄호가 몇 개 쌓였는지를 상태로 기억해야 하는데, 깊이가 상태 수를 넘으면 구분할 수 없다.
- 스택 하나를 더 주면 된다. 여는 괄호에 push, 닫는 괄호에 pop, 끝에서 스택이 비었는지 본다. 유한 상태 + 스택 = 푸시다운 기계이고, 문맥 자유 문법을 알아본다.

### 2. AST와 층

```text
  3+5*2              (3+5)*2
     +                  *
    / \                / \
   3   *              +   2
      / \            / \
     5   2          3   5
```

- `expr`는 `term`들을 `+`로 잇고, `term`은 `factor`들을 `*`로 잇는다. `5*2`는 `term` 하나 안에서 이미 묶여 `expr` 단계에 하나의 피연산자로 올라온다. 아래층(term)이 먼저 묶이니 곱셈이 먼저다.
- 괄호는 `factor ::= '(' expr ')'`로 맨 아래층에서 `expr` 전체를 한 덩어리로 만든다. 그래서 `3+5`가 먼저 묶인다.
- 실험(`Rd.java`): `(+ 3 (* 5 2))`=13, `(* (+ 3 5) 2)`=16.

### 3. 세 문법의 `8-3-2`

- (A) 반복문으로 왼쪽에 쌓는다 → `(8-3)-2` = **3**.
- (B) 오른쪽 재귀 → `8-(3-2)` = **7**. 문법이 틀렸다(오른쪽 결합).
- (C) 왼쪽 재귀를 그대로 함수로 → `expr()`이 입력을 하나도 소비하지 않고 `expr()`을 부른다 → **`StackOverflowError`**.
- 실험(`Assoc.java`, JDK 21.0.12) 출력이 그대로 3, 7, `StackOverflowError`였다.

### 4. `((1))`의 호출 스택

```text
  (위가 최신)
  factor  ← 1
  term
  expr
  factor  ← 두 번째 (
  term
  expr
  factor  ← 첫 번째 (
  term
  expr
```

- 괄호 한 겹마다 `factor → expr → term → factor`를 한 바퀴 돈다. 프레임 수는 약 3d다. 호출 스택이 괄호 스택 역할을 한다.

### 5. 깊이별 결과

| d | 기본(1024KB) | `-Xss8m` | 상한 256 |
|---|---|---|---|
| 1,000 | ok | ok | `nesting > 256 at pos 256`으로 거부 |
| 5,000 | `StackOverflowError` | ok | 거부 |
| 50,000 | `StackOverflowError` | `StackOverflowError` | 거부 |

- 실험(Temurin 21.0.12, `Rd.java`). 축소판의 한계는 약 1,660단계였다(5회 같은 값, 프레임 크기·JIT 상태에 따라 다름).
- 스택을 키우면 한계가 옮겨갈 뿐이다. 상한은 입력 길이와 무관하게 같은 위치에서 막는다.

### 6. CPython `json` vs V8 `JSON.parse`

- CPython 3.12.14: d=5,000은 ok. d=100,000은 `RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string`. 이분 탐색 한계 9,997(파이썬 `sys.getrecursionlimit()` 1000과 다름). CPython 3.12의 `_json.c`는 `_Py_EnterRecursiveCall`로 C 쪽 카운터 `C_RECURSION_LIMIT`(Linux 비디버그 10000, `Include/cpython/pystate.h`)를 쓴다. 9,997은 이미 쓰인 몇 단계를 뺀 값으로 해석한다.
- node 22.23.2: d=1,000,000도 ok. 같은 node에서 직접 짠 재귀 함수는 깊이 1e6에 `RangeError: Maximum call stack size exceeded`였다. `JSON.parse`는 재귀가 아닌 구현으로 해석한다.
- 교훈: 한계는 런타임·버전·구현마다 다르다. 런타임 한계에 기대지 말고 파서 앞에 **명시적 깊이·크기 상한**을 둔다.

### 7. 파스 트리 vs AST

- 파스 트리: 문법 규칙의 전개를 그대로 보인다. `<수식>`·`<항>`·`<인수>` 같은 중간 노드와 괄호가 다 남는다.
- AST: 뜻에 필요한 연산자·피연산자만 남긴다. 이 예제에서 괄호는 트리 모양으로 바뀌어 사라진다. 다만 Clang AST의 `ParenExpr`처럼 괄호를 노드로 남기는 구현도 있다.
- 실제 파서는 대개 파스 트리를 만들지 않고 바로 AST를 만든다(원고 §1 "AST": "실제 컴파일러는 AST를 사용한다"). 실험 파서도 `Bin`·`Num` 노드만 만든다.

### 8. `StackOverflowError`가 안 잡힌 이유

- `StackOverflowError`는 `java.lang.Error` 하위다. `Exception`이 아니라 `catch (Exception e)`에 안 걸린다.
- 잡더라도 스택이 바닥난 직후라 복구 코드가 또 넘칠 수 있다. 상태가 어중간할 수 있어 계속 쓰는 것을 권하지 않는다.
- 근본 대처: 파서에 깊이 상한(Jackson 2.15+ `StreamReadConstraints`, 2.15·2.17 소스 기본 1000 / 직접 쓴 파서는 `depth` 카운터), 요청 크기 상한. `-Xss` 확대는 한계를 옮길 뿐이다.

### 9. 두 파서의 불일치

- Python `dict(parse_qsl("role=user&role=admin"))` → `{'role': 'admin'}`(마지막 값). node `URLSearchParams.get('role')` → `'user'`(첫 값). 실험에서 그대로 나왔다.
- 앞단은 `admin`을 검사하고 뒷단은 `user`를 쓴다. 순서가 반대인 조합이면 `user`로 검사를 통과하고 `admin`으로 처리된다.
- 같은 구조: request smuggling도 **같은 바이트를 두 수신자가 다르게 해석**하는 문제다. 앞단은 `Content-Length`로, 뒷단은 `Transfer-Encoding`으로 경계를 정하면 남은 바이트가 다음 요청이 된다(RFC 9112 §11.2). RFC 9112 §6.3은 둘 다 있으면 TE가 이기고, 밀반입 시도일 수 있으니 오류로 처리하는 게 좋다고 적는다.
- 대처: 애매한 입력(중복 파라미터, CL+TE 동시)은 거부한다. 한 번 파싱한 결과를 검사와 사용에 같이 쓴다.

### 10. RFC 8259와 Jackson

- §4: 객체 안 이름이 고유하지 않으면 받는 소프트웨어의 동작은 예측할 수 없다. 마지막 쌍만 보고하는 구현, 오류를 내는 구현, 전부 보고하는 구현이 있다.
- §9: 구현은 텍스트 크기·최대 중첩 깊이·숫자 범위 등에 상한을 둘 수 있다.
- Jackson: 깊이는 `StreamReadConstraints`(`maxNestingDepth`, 2.15·2.17 소스 기본 1000, 초과 시 `StreamConstraintsException`). 중복 키는 `JsonParser.Feature.STRICT_DUPLICATE_DETECTION`(2.3부터, 기본 꺼짐)을 켜면 `JsonParseException`. 소스 주석은 파싱 시간이 보통 20~30% 늘어난다고 적는다.
