# 컴파일 파이프라인 — 어휘 분석·AST·심벌 테이블·바이트코드/PVM (컴퓨터사이언스 부트캠프 with 파이썬 ch.10)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.
> `chapter10.py`는 프로세스·스레드 원고와 컴파일 계열 원고가 한 파일에 섞여 있어, 컴파일 부분만 이곳에 두고 프로세스·스레드 부분은 [process-thread](../process-thread/)로 분리했다. COMFILER.md는 원본 구조를 유지해 이관.

## 목차

| 원본 파일 | 절 |
|-----------|-----|
| `COMFILER.md` | 1. 컴파일 과정은 왜 필요할까? — 어휘 분석·BNF·파스 트리·AST |
| `SYMBOLTABLE.md` | 2. 심벌 테이블 |
| `chapter10.py` | 3. 컴파일 언어와 인터프리터 언어 |
| `chapter10.py` | 4. 컴파일 전체 흐름과 링커 |
| `chapter10.py` | 5. PVM(Python Virtual Machine) |
| `chapter10.py` | 6. 컴파일러 구성 — 렉서와 파서, 토큰 |
| `chapter10-1.py`, `test.py` | 7. 실습: 토큰화(tokenize) |
| `chapter10-2.py` | 8. 실습: AST 순회(ast.walk) |
| `TEST_AST.md` | 9. 실습: AST 덤프와 바이트코드 변환 |
| `chapter10-3.py` | 10. 실습: 심벌 테이블(symtable) |
| `chapter10-4.py` | 11. 실습: 바이트 코드와 PVM(dis) |
| `python_flow.md` | 12. 파이썬 실행 전체 흐름 — FastAPI의 경우 |

## 1. 컴파일 과정은 왜 필요할까?

출처: `computer_science/chapter/chapter10/COMFILER.md`

컴퓨터는 "x = 3 + 5 * 2" 같은 문자열을 그냥 이해하지 못한다.
그냥 문자열의 나열일 뿐이다.
컴퓨터가 실행할 수 있는 형태로 바꿔야 하는데 이러한 과정을 컴파일이라 한다.

한국어 문장에 빗대어보자.
"철수가 사과를 먹는다."

1. 먼저 단어를 구분: [철수가] [사과를] [먹는다]
2. 문법 구조 파악: 주어(철수가) + 목적어(사과를) + 동사(먹는다)
3. 의미 이해: 철수라는 사람이 사과를 먹는 행위

위와 같은 과정을 거치는데, 컴파일도 똑같은 과정을 거친다.

"x = 3 + 5"
1. 토큰 분리: [x] [=] [3] [+] [5]
2. 문법 구조 파악: 변수(x)에 수식(3+5)을 대입
3. 실행 또는 기계어 변환

위와 같은 구조를 가진다.
그렇다면 단계별로 보자.

### 1단계: 어휘 분석(Lexical Analysis)

가장 먼저 하는 일은 문자열을 **의미 있는 단위(토큰)**로 쪼개는 것이다.

```
소스 코드: "if (count >= 10)"
↓ 어휘 분석
토큰들:
    - IF    (키워드)
    - (     (왼쪽 괄호)
    - count (식별자/변수명)
    - >=    (연산자)
    - 10    (숫자)
    - )     (오른쪽 괄호)
```

이 단계에서는 문법이 맞는지 안 맞는지는 신경 안 쓴다.
그냥 단어를 찾아내는 것뿐이다.
이때 >=는 > 하나와 = 하나가 아니라, "크거나 같다"라는 토큰으로 인식해야 되고
이런 규칙을 정의하는 게 어휘 분석기의 역할이다.

### 2단계: 구문 분석 — 근데 "올바른 문장"이 뭔가?

토큰을 쪼갰으면, "이게 문법에 맞는 문장인가?"를 확인해야 된다.

```
x = 3 + 5 #(올바른 문장)
x = + 3 5 #(틀린 문장(문법 오류))
```

이때 문제는 "올바른 문장"이 뭔지 어떻게 정의할까?
한국어 문법을 보면 "주어 + 목적어 + 동사" 같은 규칙이 있다.
프로그래밍 언어도 이러한 규칙이 필요하며 그 규칙을 적는 방식이 바로 BNF이다.

### BNF(Backus-Naur Form) 이해하기

BNF는 1960년대에 만들어진, 문법 규칙을 적는 방식이다.
간단한 예시를 보자.
"숫자"를 정의해보자.

```
<숫자> ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
```

읽는 법
- <숫자>: 이건 "숫자"라는 개념을 정의하겠다는 뜻(비단말 기호)
- ::= '~로 정의된다'
- |: "또는"

즉, "숫자는 0 또는 1 또는 2 또는.. 또는 9로 정의된다."

이번엔 "양의 정수"를 정의해보자.

```
<숫자> ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
<양의정수> ::= <숫자> | <양의정수> <숫자>
```

두 번째 줄을 해석하면
- 양의 정수는 숫자 하나이거나 (예: 5)
- 양의 정수 뒤에 숫자가 붙은 것이다(예: 42 = 4라는 양의 정수 + 2라는 숫자)

이게 재귀적 정의이다.

```
42가 <양의정수>인가?

<양의정수>
→ <양의정수> <숫자>     (두 번째 규칙 적용)
→ <숫자> <숫자>         (첫 번째 규칙 적용)
→ 4 <숫자>              (4는 <숫자>)
→ 4 2                   (2는 <숫자>)

✓ 맞음!
```

### 수식 문법 정의하기

이제 3 + 5 * 2 같은 수식을 정의해보자.

```
<수식> ::= <숫자> | <수식> + <수식> | <수식> * <수식>

이게 문제가 어떤 게 있을까?
위와 같이 정의하면 '3 + 5 * 2'를 두 가지로 해석할 수 있다.
해석 1: (3 + 5) * 2 = 16
해석 2: 3 + (5 * 2) = 13
```

어떤 게 맞는지 문법이 정해주지 않았기 때문이다.
이걸 모호한 문법이라 한다.
수학에서는 곱셈이 덧셈보다 먼저이다.
이 우선순위를 문법에 반영해야 된다.

```
<수식>   ::= <항> | <수식> + <항> | <수식> - <항>
<항>     ::= <인수> | <항> * <인수> | <항> / <인수>
<인수>   ::= <숫자> | ( <수식> )
<숫자>   ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
```

왜 이렇게 하면 우선순위가 생길까?
- '<수식>'은 '<항>'들의 덧셈/뺄셈
- '<항>'은 '<인수>'들의 곱셈/나눗셈
- '<인수>'는 숫자 또는 괄호로 묶인 수식

'3 + 5 * 2'를 파싱하면

```
→ <수식> + <항>
→ <항> + <항>
→ <인수> + <항>
→ <숫자> + <항>
→ 3 + <항>
→ 3 + <항> * <인수>
→ 3 + <인수> * <인수>
→ 3 + <숫자> * <숫자>
→ 3 + 5 * 2
```

구조를 보면 '5 * 2'가 하나의 '<항>'으로 묶여 있고, 그래서 곱셈이 먼저 계산된다.

### 파스 트리 (Parse Tree)

위의 파싱 과정을 트리로 그린 게 *파스 트리*이다.
`3 + 5 * 2`의 파스 트리:

```
              <수식>
            /   |   \
       <수식>   +   <항>
          |        /  |  \
       <항>    <항>   *  <인수>
          |       |         |
      <인수>  <인수>     <숫자>
          |       |         |
      <숫자>  <숫자>        2
          |       |
          3       5
```

트리를 보면:
- 루트는 전체 '<수식>'
- '+'의 오른쪽에 '<항>'이 있고, 그 '<항>' 안에 '5 * 2'가 들어 있다.
- 즉, '5 * 2'가 하나의 단위로 묶여 있어서 먼저 계산된다.

### 왜 "트리"인가?

트리 구조의 장점은 *계산 순서가 명확해진다*는 것이다.
트리를 아래에서 위로 계산하면:

```
         +
        / \
       3   *
          / \
         5   2

1. 5 * 2 = 10  (먼저 아래쪽)
2. 3 + 10 = 13 (나중에 위쪽)
```

괄호가 있다면

```
         *
        / \
       +   2
      / \
     3   5

1. 3 + 5 = 8   (먼저 아래쪽)
2. 8 * 2 = 16  (나중에 위쪽)
```

트리 구조가 달라지니까 계산 결과도 달라진다.

### AST (Abstract Syntax Tree)

파스 트리는 문법 규칙을 *그대로* 보여주다 보니 너무 장황하다.
`<수식>`, `<항>`, `<인수>` 같은 중간 노드들이 많아요.
그래서 AST라는 건 핵심만 남긴 트리인 것이다.

```
파스 트리:                    AST:
      <수식>                    +
    /   |   \                  / \
<수식>  +  <항>               3   *
   |      /  |  \                / \
 <항>  <항>  *  <인수>          5   2
   |     |        |
<인수> <인수>  <숫자>
   |     |        |
<숫자> <숫자>     2
   |     |
   3     5
```

실제 컴파일러는 AST를 사용한다.

## 2. 심벌 테이블(Symbol Table)

출처: `computer_science/chapter/chapter10/SYMBOLTABLE.md`

코드에 등장하는 변수, 함수 등의 정보를 저장하는 표이다.

```python
x = 10
y = "hello"
z = x + 5

def add(a, b):
    return a + b
```

이 코드를 분석하면 심벌 테이블이 아래와 같이 만들어진다.

```
이름      타입       스코프          값 위치
x        int        전역           10
y        str        전역           "hello"
z        int        전역           (x + 5의 결과)
add      function   전역           함수 정의 위치
a        parameter  add함수 내부    -
b        parameter  add함수 내부    -
```

그럼 이게 왜 필요할까?

```python
x = 10;
print(y)
```

컴파일러가 'y'를 만났을 때, 심벌 테이블을 뒤져서 "y라는 변수가 정의된 적이 있나?" 확인한다.

### 전체 흐름 정리

1. 소스코드 -> 파스 트리 (분석 트리)
   "x = 3 + 5" → 문법 구조 확인
2. 파스 트리 -> AST (추상 구문 트리)
   불필요한 노드 제거, 핵심만
3. 심벌 테이블 생성
   AST 순회하며 "x라는 변수가 있네" 기록
4. AST -> 바이트 코드
   심벌 테이블 참조하며 실행 가능한 코드로 변환

만약 심벌 테이블이 없다면?

```python
# 파일이 1000줄이라고 가정

x = 10          # 1번째 줄
# ... 중략 ...
y = x + 1       # 500번째 줄: x 어딨지? → 위로 500줄 탐색
# ... 중략 ...
z = x + y       # 999번째 줄: x 어딨지? → 또 탐색, y 어딨지? → 또 탐색
```

변수 참조할 때마다 매번 처음부터 뒤져야 합니다.

심벌 테이블이 있다면?

```
1단계: AST 한 번 순회하면서 테이블 구축

| 이름 | 타입 | 위치 |
|------|------|------|
| x    | int  | 0x01 |
| y    | int  | 0x02 |
| z    | int  | 0x03 |

2단계: 바이트코드 생성할 때 테이블에서 바로 조회 (O(1))

z = x + y
→ LOAD 0x01    # x는 0x01에 있다고 테이블이 알려줌
→ LOAD 0x02    # y는 0x02
→ ADD
→ STORE 0x03  # z는 0x03
```

## 3. 컴파일 언어와 인터프리터 언어

출처: `computer_science/chapter/chapter10/chapter10.py`

파이썬은 compile이라는 함수가 있어서 문자열을 컴파일할 수 있다.
여기서 중요한 점은 파이썬에 소스코드를 컴파일할 수 있는 컴파일러가 있다는 것.
컴파일 언어와 인터프리터 언어는 컴파일 타임이 있느냐 없느냐로 나뉘는데,
즉 소스코드를 분석하는 시점과 입력 데이터를 받는 시점이 언제냐에 따라 나뉜다.

C언어로 작성된 소스 코드가 실행 가능 파일이 되는 과정을 보면,
C로 소스코드를 작성한 다음 실제 데이터를 입력받아 그 결과를 출력하는 과정:

```
소스코드 -> 컴파일 타임(컴파일러 + 어셈블러) -> 목적파일 -> 링킹
런타임: 입력 데이터 -> 실행 -> 출력
```

링커는 필요한 라이브러리를 가져오고 여러 개의 목적 파일을 함께 묶어 실행 파일을 생성한다.
중요한 점은 소스 코드를 분석하는 컴파일 타임과, 실제 데이터를 입력받아 결과를 출력하는 런타임이 분리되어 있다는 것.

인터프리터 언어인 파이썬이 소스코드와 데이터를 동시에 입력받아 결과를 출력하는 과정을 보자.

```
소스코드 ------> 컴파일러 -> 바이트코드 -> PVM -> 출력 데이터
입력 데이터 --->
```

컴파일과 바이트코드, PVM 과정이 런타임이다.
파이썬도 소스코드가 있으므로 이를 컴파일러가 분석한다.
목적 코드로 기계어를 생성하는 C언어와 달리 파이썬은 바이트 코드를 생성한다.
바이트 코드가 생성된 후에는 PVM(Python Virtual Machine, 파이썬 가상머신)에서 바이트 코드를 하나씩 해석하여 프로그램을 실행한다.
이러한 이유로 PVM을 파이썬 인터프리터라 부르기도 한다.
이때 중요한 점은 소스코드를 분석하는 컴파일 타임이 따로 없고 실행과 동시에 분석을 한다는 점이다.
즉 소스코드와 입력 데이터가 같은 시점에 삽입된다.

## 4. 컴파일 전체 흐름과 링커

출처: `computer_science/chapter/chapter10/chapter10.py`

컴파일 전체 흐름

```
소스코드 -전처리기-> 전처리된 코드 -컴파일러-> 어셈블리 -어셈블러-> 목적파일 -링커-> 실행파일
```

위와 같은 순서로 컴파일된다.
목적 파일이란 c파일을 개별적으로 기계어로 번역한 것이다.
하지만 아직 불완전하다.

```c
// main.c
#include <stdio.h>

int add(int a, int b);  // 선언만 있음

int main() {
    printf("%d", add(1, 2));  // add가 어딨는지 모름
    return 0;
}

// math.c
int add(int a, int b) {
    return a + b;  // 실제 구현
}
```

컴파일을 하면

```
main.c -> main.o (add 함수 주소: ???)
math.c -> math.o (add 함수 구현 포함)
```

링커가 하는 일

```
main.o  ─┐
         ├──→ 링커 ──→ program.exe
math.o  ─┘
         │
libc.a  ─┘  (printf 등 표준 라이브러리)
```

즉 링커란 각 객체의 심볼들을 해결하고 주소 재배치를 진행하며 라이브러리를 연결한다.

| 단계 | 입력 | 출력 | 역할 |
|------|------|------|------|
| 컴파일 | .c | .o | 개별 파일을 기계어로 |
| 링킹 | .o 여러 개 | 실행 파일 | 합쳐서 완성된 프로그램으로 |

## 5. PVM(Python Virtual Machine)

출처: `computer_science/chapter/chapter10/chapter10.py`

Python Virtual Machine의 약자로 파이썬 바이트 코드를 실행하는 인터프리터이다.

파이썬 실행 흐름

```
소스코드(.py) -컴파일러-> 바이트코드(.pyc) -PVM-> 실행
```

바이트 코드란?

```python
def add(a, b):
    return a + b
```

이게 내부적으로

```
LOAD_FAST a
LOAD_FAST b
BINARY_ADD
RETURN_VALUE
```

이런 바이트 코드로 변환되고, 이걸 PVM이 한 줄씩 해석해서 실행하는 구조이다.

C와 비교

| | C | Python |
|---|---|---|
| 변환 | 소스 → 기계어 | 소스 → 바이트코드 |
| 실행 | CPU가 직접 | PVM이 해석 |
| 속도 | 빠름 | 느림 |

JVM과 비슷

```
Java:   .java → .class (바이트코드) → JVM
Python: .py   → .pyc   (바이트코드) → PVM
```

즉 파이썬은 기계어로 직접 실행되는 게 아니라 PVM이라는 가상머신 위에서 돌아간다.

## 6. 컴파일러 구성 — 렉서와 파서, 토큰

출처: `computer_science/chapter/chapter10/chapter10.py`

우리가 작성한 파이썬 소스코드가 바이트 코드로 변환되어 실행되는 과정을 보자.
이 과정에서 컴파일러, AST, 심벌 테이블, 바이트 코드, 가상머신을 만나게 된다.

일반적인 컴파일러는 렉서(lexer)와 파서(parser)로 구성된다.

```
문자 --렉서--> 토큰 --파서--> 분석 트리
```

렉서로 입력되는 것이 소스코드이며 소스코드도 결국 문자에 불과하다.
이러한 문자들이 렉서를 거치면서 여러 개의 토큰으로 변경된다.

그럼 이때 토큰이란??
"나는 사과를 먹었다"는 문장이 있을 때
주어("나는"), 목적어("사과를"), 동사("먹었다")로 나눌 수 있다.
이렇게 문장의 종류별로 쪼갠 다음 문자를 함께 나타낸 것을 토큰이라 한다.
위 문장을 토큰 형태로 나타내면
<주어,"나는">, <목적어,"사과를">, <동사,"먹었다">
총 3개의 토큰으로 나타낼 수 있다.
프로그래밍 언어도 마찬가지다.
우리가 작성한 코드는 언어의 문법에 맞게 토큰으로 나눌 수 있다.

종류에는 변수나 함수 이름을 의미하는 식별자, for, while, if, elif 같은 키워드,
1, 2, 3, 'a', 'b' 같은 상수, +, - 같은 연산자가 존재한다.

파서는 토큰을 분석하여 분석 트리를 구성한다.
컴파일러마다 분석 트리를 생성하기도 하고 생성하지 않기도 한다.
분석 트리가 만들어지면 이를 이용해 목적 코드(C언어는 기계어, 파이썬은 바이트코드)를 생성한다.
이를 코드 생성(code generation)이라 한다.

분석 트리를 이해하려면 BNF 표기법 등 컴파일러 지식이 많이 필요하므로 이 책에서는 생략.

## 7. 실습: 토큰화(tokenize)

출처: `computer_science/chapter/chapter10/chapter10-1.py`, `computer_science/chapter/chapter10/test.py`

파이썬은 파이썬 컴파일러를 통해 다음과 같은 과정을 거쳐 바이트 코드를 생성한다.
1. 소스 코드 -> 분석 트리
2. 분석 트리 -> 추상 구문 트리
3. 심벌 테이블 생성
4. 추상 구문 트리 -> 바이트 코드

실습 대상 코드(test.py):

```python
if __name__ == '__main__':
    def func(a, b):
        return a + b


    a = 10
    b = 20

    c = func(a, b)
    print(c)
```

토큰화 코드:

```python
if __name__ == '__main__':
    from tokenize import tokenize
    from io import BytesIO
    s = open('test.py').read()
    g = tokenize(BytesIO(s.encode('utf-8')).readline)
    for token in g:
        print(token)
```

위 코드를 변환하면 (출력 발췌):

```
TokenInfo(type=68 (ENCODING), string='utf-8', start=(0, 0), end=(0, 0), line='')
TokenInfo(type=1 (NAME), string='if', start=(1, 0), end=(1, 2), line="if __name__ == '__main__':\n")
TokenInfo(type=1 (NAME), string='__name__', start=(1, 3), end=(1, 11), line="if __name__ == '__main__':\n")
TokenInfo(type=55 (OP), string='==', start=(1, 12), end=(1, 14), line="if __name__ == '__main__':\n")
TokenInfo(type=3 (STRING), string="'__main__'", start=(1, 15), end=(1, 25), line="if __name__ == '__main__':\n")
TokenInfo(type=55 (OP), string=':', start=(1, 25), end=(1, 26), line="if __name__ == '__main__':\n")
TokenInfo(type=4 (NEWLINE), string='\n', start=(1, 26), end=(1, 27), line="if __name__ == '__main__':\n")
TokenInfo(type=5 (INDENT), string='    ', start=(2, 0), end=(2, 4), line='    def func(a, b):\n')
TokenInfo(type=1 (NAME), string='def', start=(2, 4), end=(2, 7), line='    def func(a, b):\n')
TokenInfo(type=1 (NAME), string='func', start=(2, 8), end=(2, 12), line='    def func(a, b):\n')
... (이하 NAME/OP/NUMBER/NEWLINE/NL/DEDENT 토큰이 이어지고 ENDMARKER로 끝난다 — 전체 출력은 원본 chapter10-1.py 참고)
```

import token 후 token.tok_name을 통해 얼마나 토큰이 많은지 볼 수 있다.

## 8. 실습: AST 순회(ast.walk)

출처: `computer_science/chapter/chapter10/chapter10-2.py`

추상 구문 트리(Abstract Syntax Tree)란 소스 코드의 구조를 나타내는 자료구조이다.
추상 구문 트리를 바탕으로 심벌 테이블을 만들고 바이트 코드를 생성할 수 있다.

```python
import ast
node = ast.parse(s, 'test.py', 'exec')
g = ast.walk(node)
print(next(g))
print(next(g))
print(next(g))
```

노드를 생성하고 walk 함수를 사용하면 트리의 모든 노드를 순회할 수 있는 발생자 객체를 얻을 수 있다.

```
Module(body=[If(test=Compare(left=Name(...), ops=[Eq(...)], comparators=[Constant(...)]),
body=[FunctionDef(name='func', args=arguments(...), body=[Return(...)], ...), ..., Expr(value=Call(...))], orelse=[])], type_ignores=[])
If(test=Compare(left=Name(id='__name__', ctx=Load(...)), ops=[Eq()], comparators=[Constant(value='__main__', kind=None)]), ...)
Compare(left=Name(id='__name__', ctx=Load()), ops=[Eq()], comparators=[Constant(value='__main__', kind=None)])
```

위와 같이 발생자 객체를 얻을 수 있고, 발생자는 함수를 실행 도중에 멈췄다가 원하는 시점에 다시 시작할 수 있도록 하는 함수이다.
여기서 walk 함수를 통해 만들어진 발생자 객체가 next 함수를 호출할 때마다 노드를 하나씩 넘겨준다는 점만 기억하자.
발생자를 만든 다음 next() 함수를 통해 노드를 하나씩 획득하고 있다.

## 9. 실습: AST 덤프와 바이트코드 변환

출처: `computer_science/chapter/chapter10/TEST_AST.md`

```python
import ast

code = """
def func(a, b):
    return a + b

a = 10
b = 20

c = func(a, b)
print(c)
"""

tree = ast.parse(code)
print(ast.dump(tree, indent=2))
```

위 코드를 실행하면

```
Module(
  body=[
    FunctionDef(
      name='func',
      args=arguments(
        args=[
          arg(arg='a'),
          arg(arg='b')
        ]
      ),
      body=[
        Return(
          value=BinOp(
            left=Name(id='a'),
            op=Add(),
            right=Name(id='b')
          )
        )
      ]
    ),
    Assign(
      targets=[Name(id='a')],
      value=Constant(value=10)
    ),
    Assign(
      targets=[Name(id='b')],
      value=Constant(value=20)
    ),
    Assign(
      targets=[Name(id='c')],
      value=Call(
        func=Name(id='func'),
        args=[
          Name(id='a'),
          Name(id='b')
        ]
      )
    ),
    Expr(
      value=Call(
        func=Name(id='print'),
        args=[Name(id='c')]
      )
    )
  ]
)
```

이러한 결과가 나오고 이걸 트리로 시각화한다면

```
                        Module
                           |
    ┌──────────┬───────────┼───────────┬────────────┐
    │          │           │           │            │
FunctionDef  Assign      Assign      Assign        Expr
 (func)      (a=10)      (b=20)      (c=...)       (print)
    │                                    │            │
    │                                  Call         Call
    │                                 /    \          |
  Return                          func    args      Name(c)
    │                            (func)   /   \
  BinOp                               Name  Name
  / | \                               (a)   (b)
 a  +  b
```

각 노드를 보면

```
노드                  의미
Module               파일 전체
FunctionDef          함수 정의 (def func)
Assign               대입문(a = 10)
BinOp                이항 연산 (a + b)
Call                 함수 호출 (func(a, b))
Name                 변수 참조(a, b, c)
Constant             상수값(10, 20)
Return               반환문
```

순서를 정리하면

```python
def func(a, b):    # 1번째
    return a + b

a = 10             # 2번째
b = 20             # 3번째
c = func(a, b)     # 4번째
print(c)           # 5번째
```

```
Module.body = [
    FunctionDef,   # [0]
    Assign(a),     # [1]
    Assign(b),     # [2]
    Assign(c),     # [3]
    Expr(print)    # [4]
]
```

소스코드 위에서 아래 순서 그대로 리스트에 저장된다.

AST -> 바이트 코드

```python
import dis

def func(a, b):
    return a + b

a = 10
b = 20
c = func(a, b)

dis.dis(func)
```

```
  2           LOAD_FAST                0 (a)
              LOAD_FAST                1 (b)
              BINARY_ADD
              RETURN_VALUE
```

AST의 `BinOp(left=a, op=Add, right=b)`가 이 바이트코드로 변환된 겁니다.

전체 흐름

```
소스코드
    ↓ 파싱
AST (트리 구조, 순서 보존)
    ↓ 컴파일
바이트코드 (.pyc)
    ↓ 실행
PVM이 바이트코드 순차 실행
```

## 10. 실습: 심벌 테이블(symtable)

출처: `computer_science/chapter/chapter10/chapter10-3.py`

```python
import symtable
sym = symtable.symtable(s, 'test.py', 'exec')
print(sym.get_name())
# top
print(sym.get_symbols())
# [<symbol '__name__': GLOBAL_IMPLICIT, USE>,
# <symbol 'func': LOCAL, USE|DEF_LOCAL>,
# <symbol 'a': LOCAL, USE|DEF_LOCAL>,
# <symbol 'b': LOCAL, USE|DEF_LOCAL>,
# <symbol 'c': LOCAL, USE|DEF_LOCAL>,
# <symbol 'print': GLOBAL_IMPLICIT, USE>]
```

이처럼 글로벌 테이블을 가져와서 확인할 수 있다.
이제 func의 심벌 테이블을 보자.

```python
print(sym.get_children())
# [<SymbolTable for __annotate__ in test.py>,
# <Function SymbolTable for func in test.py>]
func_sym = sym.get_children()[1]
print(func_sym.get_name())
# func
print(func_sym.get_symbols())
# [<symbol 'a': LOCAL, USE|DEF_PARAM>,
# <symbol 'b': LOCAL, USE|DEF_PARAM>]
```

## 11. 실습: 바이트 코드와 PVM(dis)

출처: `computer_science/chapter/chapter10/chapter10-4.py`

```python
import dis
g = dis.get_instructions(s)
for inst in g:
    print(inst.opname.ljust(20), end=" ")
    # ljust는 문자열 메서드로 문자열에 붙여 써야 된다.
    # 왼쪽 정렬하고 나머지를 공백으로 채운다.
    print(inst.argval)
```

```
RESUME               0
LOAD_NAME            __name__
LOAD_CONST           __main__
COMPARE_OP           ==
POP_JUMP_IF_FALSE    68
NOT_TAKEN            None
LOAD_CONST           <code object func at 0x0000024C87FF6D30, file "<disassembly>", line 2>
MAKE_FUNCTION        None
STORE_NAME           func
LOAD_SMALL_INT       10
STORE_NAME           a
LOAD_SMALL_INT       20
STORE_NAME           b
LOAD_NAME            func
PUSH_NULL            None
LOAD_NAME            a
LOAD_NAME            b
CALL                 2
STORE_NAME           c
LOAD_NAME            print
PUSH_NULL            None
LOAD_NAME            c
CALL                 1
POP_TOP              None
LOAD_CONST           None
RETURN_VALUE         None
LOAD_CONST           None
RETURN_VALUE         None
```

위와 같이 나오는 걸 볼 수 있다.
모듈 dis를 불러와서 get_instructions라는 함수를 통해 바이트 코드를 제공하는 발생자를 만든다.
`print(inst.opname.ljust(20), end=" ")` — 즉 앞쪽은 바이트 코드 이름이며
`print(inst.argval)` — 여기는 인자값이다.
어셈블러와 다른 파이썬 바이트 코드 인스트럭션을 확인할 수 있다.
이러한 바이트 코드는 파이썬의 가상 머신 위에서 실행된다.
파이썬의 가상 머신인 PVM은 그저 굉장히 큰 무한 루프일 뿐이며,
다음 코드는 CPython 소스 코드 중 ceval.c 파일에 있는 PVM 코드를 알아보기 쉽게 재구성한 것.

```c
PyObject *
_PyEval_EvalFrameDefault(PyFrameObject *f, int throwflag)
{
    int opcode;
    int oparg;
    int word;

    opcode = _Py_OPCODE(word);
    oparg = _Py_OPARG(word);

    for (;;) {
        switch (opcode) {
            case NOP:
                //things
                break;
            case LOAD_FAST:
                //things
                break;
            case STORE_FAST:
                //things
                break;
        }
    }
}
```

이 코드를 보면 디폴트 함수는 바이트 코드의 실제 실행을 담당하는 함수로, 이 함수 안에 opcode라는 변수가 바이트 코드를 받아온다.
그리고 무한 루프문을 통해 — 파이썬의 while True문처럼 — 도는 이 무한 루프가 PVM이다.
무한 루프 안에는 실제 바이트 코드를 분석하고 실행하는 스위치문이 있으며,
파이썬에서는 스위치 대신 if-elif를 많이 사용.
즉 스위치문에서 로드와 스토어 같은 바이트코드를 처리하고,
opcode가 NOP이라면 break문을 만날 때까지 case NOP을 실행한다.

## 12. 파이썬 실행 전체 흐름 — FastAPI의 경우

출처: `computer_science/chapter/chapter10/python_flow.md`

전체 흐름

```
python test.py 실행
        │
        ▼
┌───────────────────┐
│  1. 컴파일 단계    │  ← PVM 아님
│  소스코드 → 바이트코드 │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  2. 실행 단계      │  ← PVM (무한 루프)
│  바이트코드 해석/실행 │
└───────────────────┘
```

1단계: 컴파일 (PVM 아님)

```
소스코드 "x = 10"
    ↓ 어휘 분석
토큰 [x, =, 10]
    ↓ 구문 분석
AST
    ↓ 바이트코드 생성
LOAD_CONST 10
STORE_NAME x
```

여기까지는 컴파일러가 하는 일.

2단계: 실행(PVM)

```c
// ceval.c - 여기가 PVM
for (;;) {  // 무한 루프
    switch (opcode) {
        case LOAD_CONST:
            // 상수를 스택에 push
            break;
        case STORE_NAME:
            // 스택에서 pop해서 변수에 저장
            break;
        // ...
    }
}
```

이와 같이 PVM은 이미 만들어진 바이트코드를 실행만 한다.

FastAPI 같은 웹서버일 경우에는 어떻게 동작할까?

```
uvicorn main:app 실행
        │
        ▼
┌─────────────────────────────┐
│  서버 시작 시 (1회)          │
│  모든 import된 파일 컴파일    │
│  → 바이트코드 생성 (.pyc)    │
│  → 라우터, 의존성 등록        │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  대기 상태 (이벤트 루프)      │
│  바이트코드는 이미 메모리에    │
└─────────────────────────────┘
        │
        ▼ 요청 들어옴
┌─────────────────────────────┐
│  PVM이 바이트코드 실행만      │
│  컴파일 안 함 (이미 됐으니까)  │
└─────────────────────────────┘
```

서버가 구동하면 모든 import된 파일을 컴파일한다.
바이트코드를 생성하고 라우터, 의존성을 등록한다.
이후 대기 상태가 되며 바이트 코드는 이미 메모리에 적재되어 있다.
요청이 들어오면 PVM이 바이트코드 실행만 한다.

```python
# main.py
from fastapi import FastAPI

print("컴파일 시점에 실행됨!")  # 서버 시작할 때 출력

app = FastAPI()

@app.get("/")
def home():
    print("요청 시 실행됨!")  # 요청 들어올 때 출력
    return {"msg": "hello"}
```

```
$ uvicorn main:app
컴파일 시점에 실행됨!   ← 서버 시작할 때
INFO: Started server process
INFO: Waiting for application startup

# 이후 요청 보내면
요청 시 실행됨!         ← 요청마다
```

왜 이렇게?

매 요청마다 컴파일하면 너무 느립니다.

```
요청마다 컴파일하면:
요청 → 컴파일(수십ms) → 실행 → 응답

미리 컴파일하면:
요청 → 실행(즉시) → 응답
```
