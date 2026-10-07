# language/03-parsing-grammars-ast — BNF·CFG·재귀 하강·AST — 정리 (힌트)

## 해결하는 문제

렉서(02)는 토큰을 한 줄로 늘어놓는다. 하지만 `3 + 5 * 2`에서 **무엇이 무엇의 피연산자인지**는 줄에 안 보인다.

```text
  토큰:  [3] [+] [5] [*] [2]          ← 평평한 줄
  구조:      +                        ← 누가 누구 안에 들었나
            / \
           3   *
              / \
             5   2
```

- *파서(parser)*: 토큰 줄을 문법 규칙에 맞춰 구조를 알아내는 프로그램. 컴파일러의 파서는 보통 그 구조를 트리로 만든다. 규칙에 안 맞으면 문법 오류를 낸다.
    - 흔한 오해: 파서는 꼭 트리를 만든다 — JDK `javax.xml.parsers.SAXParser`처럼 트리 없이 "요소 시작·끝" 이벤트만 차례로 넘기는 스트리밍 파서도 있다.
- 이 트리가 있어야 의미 분석(04)·코드 생성(22)이 "곱셈 먼저"를 안다.

정규식(02)으로는 안 된다. 괄호 짝 맞추기가 대표 예다.

```text
  ((((1))))   여는 괄호가 몇 개였는지 끝까지 기억해야 한다.
  유한 오토마타는 상태가 유한하다 → 깊이가 상태 수를 넘으면 셀 수 없다.
  스택 하나를 더 주면 된다: 여는 괄호에 push, 닫는 괄호에 pop.
```

쉬운 예: 문장 성분 분석. "철수가 사과를 먹는다"를 주어·목적어·동사로 묶는 것이 파싱이다(원고 [compiler-pipeline](../../foundations/compiler-pipeline/README.md) §1).\
똑같은 구조다. JSON·HTTP 헤더·SQL·HTML·설정 파일을 읽는 모든 코드가 파서다.

실무 예:
- `[[[[…]]]]`를 수만 단계 중첩한 JSON 하나로 파서 스레드가 `StackOverflowError`로 죽는다(JSON bomb).
- 앞단 프록시와 뒷단 서버가 같은 HTTP 요청의 **본문 길이를 다르게 해석**해, 요청 하나 안에 다른 요청이 숨는다(request smuggling).

## 동작·원리

### 1. 문법을 적는 법 — BNF와 문맥 자유 문법

```text
  expr   ::= term   (('+' | '-') term)*
  term   ::= factor (('*' | '/') factor)*
  factor ::= NUMBER | '(' expr ')'
```

- *BNF*: "왼쪽 기호는 오른쪽으로 바꿀 수 있다"는 규칙(생성 규칙)을 적는 표기. 위처럼 `*`·`|`를 섞은 확장판을 EBNF라 한다.
- *단말 기호*: 토큰(`NUMBER`, `+`). *비단말 기호*: 규칙 이름(`expr`, `term`).
- *문맥 자유 문법(CFG)*: 왼쪽에 비단말 **하나**만 오는 규칙들. 앞뒤 문맥과 상관없이 바꿀 수 있다.
- BNF 읽는 법, `<양의정수>`의 재귀 정의, `42`의 유도 과정은 원고 §1 "BNF 이해하기"에 있다.

### 2. 우선순위와 결합성은 문법의 층으로 정한다

- `expr ::= expr '+' expr | expr '*' expr | NUMBER`는 **모호한 문법**이다. `3+5*2`가 두 트리를 가진다(원고 §1 "수식 문법 정의하기").
- 층을 나누면 해결된다. `expr`(덧셈) → `term`(곱셈) → `factor`(숫자·괄호). 아래층일수록 먼저 묶인다.
- *결합성*: 같은 우선순위 연산자가 이어질 때 어느 쪽부터 묶나. `8-3-2`는 `(8-3)-2`가 맞다(왼쪽 결합).

```text
  왼쪽 결합 (8-3)-2 = 3           오른쪽 결합 8-(3-2) = 7
        -                               -
       / \                             / \
      -   2                           8   -
     / \                                 / \
    8   3                               3   2
```

- Python 3.12 `ast.dump(ast.parse('8-3-2', mode='eval').body)`는 왼쪽 그림이다. `BinOp(left=BinOp(8 - 3), op=Sub(), right=2)`(실제 출력의 `Constant(value=…)`를 줄여 씀).
- 거듭제곱은 언어가 오른쪽 결합으로 정한다. Python `2**3**2`의 AST는 `2 ** (3 ** 2)`이고 값은 512다.

### 3. 재귀 하강 — 규칙 하나 = 함수 하나

```java
// expr ::= term (('+'|'-') term)*
Node expr() {
    Node n = term();
    while (peek() == '+' || peek() == '-') { char op = next(); n = new Bin(op, n, term()); }
    return n;        // 반복문이 왼쪽에 쌓는다 → 왼쪽 결합
}
// factor ::= NUMBER | '(' expr ')'
Node factor() {
    if (peek() == '(') { next(); Node n = expr(); expect(')'); return n; }   // 괄호 = 재귀
    return number();
}
```

- *재귀 하강(recursive descent)*: 비단말마다 함수를 하나 만들고, 규칙의 오른쪽을 그대로 함수 호출로 옮기는 파서. 위에서 아래로(top-down) 트리를 만든다.
- 괄호 한 겹 = `factor → expr → term → factor` 호출 한 바퀴다. **호출 스택이 1절의 "괄호를 세는 스택"** 이다.

```text
  입력 ((1)) 을 읽는 중의 호출 스택 (위가 최신)
   factor  ← '1'
   term
   expr
   factor  ← 두 번째 '('
   term
   expr
   factor  ← 첫 번째 '('
   term
   expr
  중첩 깊이 d → 프레임 약 3d개. d가 크면 스레드 스택(JDK 21 Linux/x64 기본 1024KB)을 넘는다.
```

- *왼쪽 재귀*: `expr ::= expr '-' term`처럼 규칙이 맨 왼쪽에서 자기 자신을 부르는 것. 그대로 함수로 옮기면 입력을 하나도 소비하지 않고 자기를 다시 부른다 → 무한 재귀. 재귀 하강에서는 반복문(`(…)*`)으로 바꿔 쓴다.

### 4. 파스 트리와 AST

- *파스 트리*: 문법 규칙을 그대로 보인 트리. `<수식>`·`<항>`·`<인수>` 같은 중간 노드가 다 있다.
- *AST(추상 구문 트리)*: 뜻에 필요한 것만 남긴 트리. 이 노트의 예제에서는 괄호·중간 노드가 사라지고 구조로만 남는다. 무엇을 남길지는 구현 목적에 따른다. Clang AST는 원문 위치·진단을 위해 괄호를 `ParenExpr` 노드로 남긴다(Clang "Introduction to the Clang AST").
- 두 트리의 그림, Python `ast.dump`·`ast.walk` 실습은 원고 §1 "파스 트리"·"AST", §8·§9에 있다.
- 실제 파서는 대개 파스 트리를 만들지 않고 바로 AST를 만든다. 위 코드도 `Bin`·`Num` 노드만 만든다.

### 5. 위에서 아래로 vs 아래에서 위로

| | 하향식(LL·재귀 하강) | 상향식(LR·LALR) |
|---|---|---|
| 방향 | 시작 기호에서 펼쳐 토큰에 맞춘다 | 토큰을 쌓아 규칙으로 줄인다(shift-reduce) |
| 스택 | 재귀 하강은 호출 스택, 표 기반 LL(1)은 명시적 스택 | 명시적 상태 스택 |
| 왼쪽 재귀 | LL·단순 재귀 하강은 못 씀 → 반복문으로 | 그대로 됨 |
| 흔한 형태 | 손으로 쓴 파서, ANTLR | yacc·bison 생성 파서 |

- 손으로 쓴 재귀 하강이 실무에서 많다. 오류 메시지를 다듬기 쉽고 코드가 문법과 닮아서다. javac·Go 컴파일러·V8 파서가 재귀 하강 계열이라는 말은 기억으로 쓴 것이다 `[?]`.
- PEG·packrat 파서는 대안을 순서대로 시도하고 되감는다. packrat은 메모이제이션으로 선형 시간에 묶는다. PEG는 보통 왼쪽 재귀를 못 쓰지만, CPython 3.9+의 PEG 파서는 메모이제이션 캐시를 써서 직접·간접 왼쪽 재귀를 허용한다(PEP 617 "Left recursion")([algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md) "쓰이는 곳").

### 실험: 재귀 하강 파서 — AST, 결합성, 깊은 중첩

- 환경: Temurin 21.0.12, `--cpus=2 --network none`. 위 문법의 재귀 하강 파서(`Rd.java`, JDK만)와 결합성 비교(`Assoc.java`).

```text
  3+5*2    AST=(+ 3 (* 5 2))   =13
  (3+5)*2  AST=(* (+ 3 5) 2)   =16
  8-3-2    AST=(- (- 8 3) 2)   =3

  (A) expr ::= term ('-' term)*      → 3     (반복문, 왼쪽 결합)
  (B) expr ::= term '-' expr | term  → 7     (오른쪽 재귀 = 틀린 뜻)
  (C) expr ::= expr '-' term | term  → StackOverflowError  (왼쪽 재귀를 그대로)
```

`(`ᵈ `1` `)`ᵈ 입력, 깊이별:

| 깊이 d | 기본 스택(1024KB) | `-Xss8m` | 깊이 상한 256 |
|---|---|---|---|
| 1,000 | ok | ok | 거부(`nesting > 256 at pos 256`) |
| 5,000 | `StackOverflowError` | ok | 거부 |
| 10,000 | `StackOverflowError` | ok | 거부 |
| 50,000 | `StackOverflowError` | `StackOverflowError` | 거부 |

- 축소판 파서로 이분 탐색한 한계: 약 1,660단계(집필 3회 + 점검 2회, 모두 같은 값). 프레임 크기와 JIT 상태에 따라 바뀐다.
- 관찰 — 스택을 8배로 키우면 한계가 옮겨갈 뿐 사라지지 않는다. **깊이 상한**을 두면 입력 크기와 무관하게 같은 위치(pos 256)에서 예외로 거부한다.

같은 입력 모양을 다른 런타임의 JSON 파서에(`[`ᵈ `]`ᵈ):

```text
  CPython 3.12.14 json.loads   d=5,000 ok · d=100,000 RecursionError: maximum recursion depth
                               exceeded while decoding a JSON array from a unicode string
                               (이분 탐색: 9,997까지 ok — sys.getrecursionlimit()은 1000)
  node 22.23.2 JSON.parse      d=1,000,000 까지 ok
                               (같은 node에서 직접 짠 재귀 함수는 1e6 깊이에 RangeError: Maximum call stack size exceeded)
```

- 관찰 — CPython의 C 파서는 파이썬 재귀 한도(1000)가 아닌 다른 한도에서 멈췄다. CPython 3.12 소스에서 `_json.c`는 중첩마다 `_Py_EnterRecursiveCall(" while decoding a JSON array …")`을 부르고, 이 카운터는 `sys.getrecursionlimit()`과 별개인 `C_RECURSION_LIMIT`(Linux 비디버그 빌드 10000, `Include/cpython/pystate.h`)를 쓴다. 9,997은 그 10000에서 이미 쓰인 몇 단계를 뺀 값으로 **해석**한다. V8 `JSON.parse`는 이 깊이에서 스택을 넘지 않았다. 반복문(명시적 스택) 구현으로 **해석**한다.
- 해석 — "어느 깊이에서 죽나"는 런타임·버전마다 다르다. 그래서 파서 앞에 **명시적 깊이 상한**을 두는 쪽이 이식성이 있다.

### 6. 파서 불일치 — 같은 바이트, 다른 해석

```text
  요청 바이트 ──▶ [프록시: 파서 P] ──▶ [앱 서버: 파서 Q]
                  "본문은 여기까지"        "아니, 여기까지"
                  → 남은 바이트를 Q는 "다음 요청"으로 읽는다
```

- HTTP/1.1에서 본문 길이는 `Content-Length`나 `Transfer-Encoding: chunked`로 정한다. 둘 다 오면 RFC 9112 §6.3은 "Transfer-Encoding이 Content-Length를 이긴다", "요청 밀반입 시도일 수 있으니 오류로 처리하는 게 좋다"고 적는다.
  - *request smuggling*: 수신자들 사이의 파싱 차이를 이용해 무해해 보이는 요청 안에 다른 요청을 숨기는 기법(RFC 9112 §11.2).
- 본문 길이 규칙 자체는 [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md), 공격·방어 쪽은 [security/23-deserialization-and-parser-attacks](../../security/23-deserialization-and-parser-attacks/2-summary.md)가 맡는다. 여기서는 공격을 재현하지 않고, **무해한 불일치**로 원리만 본다.

실험: 같은 쿼리 문자열 `role=user&role=admin`을 두 라이브러리로(같은 컨테이너 이미지):

```text
  Python 3.12.14  parse_qs        → {'role': ['user', 'admin']}
                  dict(parse_qsl) → {'role': 'admin'}       ← 마지막 값
  node 22.23.2    URLSearchParams.get('role') → 'user'      ← 첫 값
                  getAll('role')               → ['user', 'admin']
```

- 관찰 — 앞단이 Python 방식으로 `role`을 검사하고 뒷단이 node 방식으로 읽으면, 검사한 값(`admin`)과 쓰는 값(`user`)이 다르다. 반대 순서면 권한 상승이다. 각 라이브러리는 자기 규칙대로 맞게 동작했다.
- JSON의 중복 키도 같은 종류다. RFC 8259 §4는 "이름이 고유하지 않으면 받는 소프트웨어의 동작은 예측할 수 없다"고 적는다. 마지막 값만 보고하는 구현, 오류를 내는 구현, 전부 보고하는 구현이 있다. 이 실험의 Python `json`과 node `JSON.parse`는 둘 다 마지막 값(`admin`)이었다.

## 쓰이는 자료구조·알고리즘

- **재귀 하강** — 비단말 = 함수. 재귀 호출 구조는 [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md).
- **푸시다운(스택)** — 괄호 깊이를 세는 장치. 재귀 하강에서는 호출 스택이, LR 파서와 연산자 우선순위 파서(shunting-yard)에서는 명시적 스택이 맡는다([data-structure/03-stack](../../data-structure/03-stack/2-summary.md) — 수식 파서 문제).
- **트리(AST)** — 산술식의 평가·코드 생성은 후위 순회다. 자식을 먼저 계산하고 부모 연산을 한다. `&&`·`if`처럼 왼쪽(조건) 결과에 따라 오른쪽 자식을 평가할지 고르는 노드는 순서가 다르다(JLS §15.23: `&&`의 오른쪽은 왼쪽이 true일 때만 평가)([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)).
- **문법 = 생성 규칙 그래프** — 왼쪽 재귀 찾기는 "규칙 A가 입력 소비 없이 A에 닿는가"의 그래프 도달성 문제다([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).

## 적용 — 풀어나가는 법

1. **신뢰 못 할 입력을 받는 파서마다 세 가지 상한을 확인한다.** 크기(바이트), 깊이(중첩), 개수(원소·키). RFC 8259 §9도 "구현은 텍스트 크기·최대 중첩 깊이에 상한을 둘 수 있다"고 적는다.
   - Jackson은 2.15부터 `StreamReadConstraints`가 있다(클래스 `@since 2.15`). jackson-core 2.15·2.17 소스 모두 기본 최대 깊이는 `DEFAULT_MAX_DEPTH = 1000`이다. 넘으면 `StreamConstraintsException`이다. 메시지는 버전마다 다르다(2.17: `Document nesting depth (…) exceeds the maximum allowed (1000, …)`, 2.15 브랜치: `Depth (…) exceeds the maximum allowed nesting depth (1000)`).
   - 직접 쓴 재귀 하강이면 `depth` 카운터를 둔다(실험의 `maxDepth`).
2. **`StackOverflowError`는 `Exception`이 아니다.** `catch (Exception e)`로는 안 잡힌다. 깊이 상한으로 막는 게 맞고, 잡아서 계속 쓰는 것은 권하지 않는다(상태가 어중간할 수 있다).
3. **한 메시지는 한 파서로 한 번만 해석한다.** 검사(앞단)와 사용(뒷단)이 다른 라이브러리를 쓰면 중복 키·중복 헤더·인코딩 해석이 갈린다.
   - 애매한 입력은 **거부**한다. 중복 쿼리 파라미터·중복 JSON 키·`Content-Length`와 `Transfer-Encoding` 동시 존재.
   - 프록시와 서버의 HTTP 파서 설정(엄격 모드)을 맞추고, 가능하면 끝단까지 HTTP/2를 쓴다(방어 세부는 security/23).
4. **손으로 쓴 파서는 문법부터 적는다.** 층(우선순위)과 반복문(왼쪽 결합)을 문법에서 정하고 함수로 옮긴다. `8-3-2`, `2-3+4`, `((1))`, 빈 입력, 짝 안 맞는 괄호를 테스트에 넣는다.
5. **AST를 보며 디버깅한다.** Python `ast.dump(ast.parse(src), indent=2)`. 직접 쓴 파서는 AST를 `(+ 3 (* 5 2))`처럼 찍는 함수를 둔다(실험의 `show`). 예상과 다른 우선순위는 트리 모양에서 바로 보인다.

## 장애 시나리오와 대처

### 1. 깊은 중첩 JSON 하나로 파서 스레드가 죽음 — JSON bomb (⚠)

- **현상**: 특정 요청에서 500이 나거나, 작업자 스레드·워커가 죽는다. 요청 크기는 크지 않다(수십 KB).
- **보이는 형태**: Java `java.lang.StackOverflowError`, 스택 트레이스에 같은 파서 메서드가 반복된다(트레이스는 `MaxJavaStackTraceDepth` 기본 1024프레임에서 잘린다). Python `RecursionError: maximum recursion depth exceeded while decoding a JSON array`. Jackson 2.15+면 `StreamConstraintsException`(2.17 메시지: `Document nesting depth …`).
- **원인**: 재귀 하강 파서는 중첩 한 겹마다 스택 프레임을 쓴다. 실험에서 기본 스택의 Java 재귀 하강은 5,000단계에서 죽었다. `[`만 5,000개면 5KB다.
- **대처**: 파서에 깊이 상한(예: 수백~1,000)을 둔다. 요청 크기 상한을 앞단에 둔다. `-Xss`로 스택을 키우는 것은 한계를 옮길 뿐이다.

### 2. 프록시와 서버가 본문 경계를 다르게 읽음 — request smuggling (⚠)

- **현상**: 다른 사용자의 요청에 엉뚱한 응답이 붙는다. 앞단 WAF·인증을 거치지 않은 요청이 뒷단 로그에 보인다.
- **보이는 형태**: 뒷단 접근 로그에 앞단 로그에 없는 요청이 있다. 요청에 `Content-Length`와 `Transfer-Encoding`이 함께 있거나, `Transfer-Encoding` 값이 이상하게 쓰여 있다.
- **원인**: 두 HTTP 파서가 메시지 길이 규칙(RFC 9112 §6.3)을 다르게 구현했다. 한쪽 끝이 다른 쪽에게는 다음 요청의 시작이 된다.
- **대처**: 둘 다 있는 요청은 거부한다(§6.3이 "오류로 처리하는 게 좋다"고 적는다). 프록시가 정규화한 뒤 넘기거나, 앞단과 뒷단을 같은 파서·같은 엄격 설정으로 맞춘다. 끝단까지 HTTP/2로 간다. 세부는 [security/23](../../security/23-deserialization-and-parser-attacks/2-summary.md)·[network/40](../../network/40-chunked-and-streaming-responses/2-summary.md).

### 3. 검사한 값과 쓰는 값이 다름 — 중복 파라미터·키

- **현상**: 권한 검사를 통과한 요청이 다른 권한으로 처리된다.
- **보이는 형태**: 요청에 같은 이름의 파라미터(`role=…&role=…`)나 같은 JSON 키가 두 번 있다.
- **원인**: 라이브러리마다 중복을 다르게 고른다. 실험에서 Python `dict(parse_qsl)`는 마지막 값, node `URLSearchParams.get`은 첫 값이었다. RFC 8259 §4도 JSON 중복 키 동작은 예측할 수 없다고 적는다.
- **대처**: 중복을 거부하는 엄격 파싱. Jackson은 `JsonParser.Feature.STRICT_DUPLICATE_DETECTION`(2.3부터, 기본 꺼짐)을 켜면 중복 키에서 `JsonParseException`을 던진다. 소스 주석은 기본 파싱 시간이 보통 20~30% 늘어난다고 적는다. 한 번 파싱한 결과 객체를 검사와 사용에 같이 쓴다.

### 4. 손으로 쓴 파서의 결합성·우선순위 버그

- **현상**: 계산식·필터식 기능에서 `8-3-2`가 7로 나온다. 또는 어떤 입력을 넣어도 시작하자마자 `StackOverflowError`다.
- **보이는 형태**: 값이 틀린 경우는 예외 없이 결과만 다르다. 무한 재귀는 첫 호출부터 같은 함수가 반복된 트레이스다.
- **원인**: `expr ::= term '-' expr`(오른쪽 재귀 → 오른쪽 결합, 실험 7). `expr ::= expr '-' term`을 그대로 옮김(왼쪽 재귀 → 입력 소비 없이 자기 호출, 실험 `StackOverflowError`).
- **대처**: `term ('-' term)*` 반복문으로 바꾼다. 결합성 테스트(`8-3-2 == 3`, `2**3**2 == 512`처럼 언어가 정한 값)를 넣는다.

## 핵심 문장

- 파서는 토큰 줄의 구조를 알아낸다(컴파일러에서는 보통 트리로 만든다). 괄호 깊이를 세야 하므로 유한 오토마타가 아니라 스택이 필요하다.
- 우선순위는 문법의 층으로, 결합성은 재귀 방향(또는 반복문)으로 정한다. 재귀 하강에서 왼쪽 재귀는 무한 재귀다.
- 재귀 하강의 호출 스택이 곧 괄호 스택이다. 중첩 깊이에 비례해 스택을 쓰므로, 신뢰 못 할 입력에는 깊이 상한이 필요하다.
- 이 실험에서 Java 기본 스택의 재귀 하강은 1,000단계는 통과하고 5,000단계에서 넘쳤다. CPython `json`은 약 1만 단계에서, V8 `JSON.parse`는 100만 단계에서도 버텼다. 한계는 런타임마다 다르다.
- 같은 바이트를 두 파서가 다르게 읽으면 보안 문제다(request smuggling, 중복 키). 애매한 입력은 거부하고 한 번만 파싱한다.

## 관련 주제·근거

- 선행
  - [02-lexing-and-regular-languages](../02-lexing-and-regular-languages/2-summary.md) — 토큰과 정규 언어의 한계
  - [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) — 괄호·수식 파싱
- 후속·연결
  - [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md) — AST 위에서 이름·타입 확인
  - [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md) — AST에서 IR로
  - [architecture/10-calling-convention-and-stack-frame](../../architecture/10-calling-convention-and-stack-frame/2-summary.md) — 재귀 깊이가 스택을 쓰는 방식
  - [security/23-deserialization-and-parser-attacks](../../security/23-deserialization-and-parser-attacks/2-summary.md) · [security/18-injection](../../security/18-injection/2-summary.md)(해석기가 데이터를 코드로 파싱) · [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md)
  - [web-platform/02-rendering-pipeline](../../web-platform/02-rendering-pipeline/2-summary.md) — HTML 토큰화·트리 구성
  - 원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) §1(BNF·수식 문법·파스 트리·AST) · §8(`ast.walk`) · §9(`ast.dump`)
- 문서·소스
  - RFC 9112 HTTP/1.1 — §6.3 Message Body Length(TE와 CL 동시 존재), §11.2 Request Smuggling <https://www.rfc-editor.org/rfc/rfc9112>
  - RFC 8259 JSON — §4 이름 중복 시 동작 예측 불가, §9 Parsers(크기·중첩 깊이 상한 허용) <https://www.rfc-editor.org/rfc/rfc8259>
  - `java` 도구 문서(JDK 21) `-Xss` — Linux/x64 기본 1024KB <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - jackson-core 2.15·2.17 `StreamReadConstraints.java` — `@since 2.15`, `DEFAULT_MAX_DEPTH = 1000`, 깊이 초과 메시지(버전별) · `JsonParser.java` — `STRICT_DUPLICATE_DETECTION(false)`, `@since 2.3` <https://github.com/FasterXML/jackson-core>
  - Aho 외 『Compilers』(Dragon Book) 4장 `[?]`
- 실험 목록
  - 재귀 하강 파서 AST·평가·깊이별 `StackOverflowError`·`-Xss8m`·깊이 상한(`Rd.java`), 한계 이분 탐색 3회(`Probe.java`), 결합성 세 문법(`Assoc.java`) — Temurin 21.0.12, `--cpus=2 --network none`
  - CPython 3.12.14 `json.loads` 깊이(이분 탐색, 2회 모두 9,997), `ast.dump`(`8-3-2`, `2**3**2`) — `python:3.12-slim` · 한도 근거: CPython 3.12 `Modules/_json.c`·`Include/cpython/pystate.h`(`C_RECURSION_LIMIT`)
  - node 22.23.2 `JSON.parse` 깊이, 직접 재귀 1e6 — `node:22-alpine`
  - 쿼리 문자열 중복(`parse_qs`·`parse_qsl` vs `URLSearchParams`)과 JSON 중복 키(두 런타임)
