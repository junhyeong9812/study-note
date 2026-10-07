# language/04-semantic-analysis-and-scopes — 심벌 테이블·스코프·바인딩 — 정리 (힌트)

## 해결하는 문제

파서(03)를 통과한 AST는 **문법만** 맞다.

```text
  x = 10
  print(y)        ← 문법은 맞다. 그런데 y는 어디서 왔나?
  total = total + price   ← 이 total은 바깥 것인가, 안쪽 것인가?
```

- *의미 분석(semantic analysis)*: AST의 각 이름이 **어느 선언을 가리키는지** 정하고, 타입·사용 규칙을 확인하는 단계.
- *바인딩(binding)*: 이름과 그것이 가리키는 대상(변수·함수·타입)을 잇는 것.
- *스코프(scope)*: 한 선언이 그 이름으로 보이는 프로그램 범위.
- *심벌 테이블(symbol table)*: 이름 → 정보(종류·스코프·타입·위치)를 담는 표. 컴파일러가 이름을 만날 때마다 찾는다.

쉬운 예: 회사에서 "김 대리 불러 주세요".
- 먼저 우리 팀에서 찾는다. 없으면 본부, 그다음 회사 전체.
- 우리 팀에 김 대리가 있으면, 본부의 다른 김 대리는 **가려진다**.

똑같은 구조다. 이 "안에서 밖으로 찾기"가 스코프 체인이고, "가려짐"이 섀도잉이다.

실무 예:
- 세터의 매개변수 이름이 필드와 같아 `count = count + 1`이 필드를 안 바꾼다.
- JS에서 `for (var i …)` 안에 만든 콜백이 전부 마지막 값만 본다.
- Python 함수에 `count += 1` 한 줄을 추가했더니, 그 위에서 멀쩡하던 `count` 읽기가 `UnboundLocalError`가 됐다.

## 동작·원리

### 1. 의미 분석이 하는 일

```text
  AST ──▶ [이름 해석] ──▶ [타입 검사(05)] ──▶ [기타 규칙] ──▶ 주석 달린 AST + 심벌 테이블
           │                                   ├ 정의 전 사용
           │ 각 Name 노드 → 어느 선언?          ├ 같은 스코프 중복 선언
           └ 못 찾으면 "undefined" 오류         └ 람다가 바꾸는 지역 변수 캡처(Java) …
```

- 심벌 테이블의 기초(왜 필요한가, 매번 위로 탐색하는 비용, Python `symtable` 실습)는 원고 [compiler-pipeline](../../foundations/compiler-pipeline/README.md) §2·§10에 있다.
- 참고: 원고 §2의 표에는 Python 이름마다 타입 칸(`int`·`str`)이 있다. CPython의 `symtable`은 타입을 기록하지 않는다. 이름의 스코프(LOCAL·GLOBAL·FREE…)와 쓰임(정의·사용·매개변수)만 기록한다(아래 실험). 타입 칸은 정적 타입 언어 컴파일러(05)의 모습이다.
- 참고: 원고 §10의 `symtable` 출력에 `__annotate__` 자식 테이블이 있다. CPython 3.12.14에서 같은 모양의 코드는 그런 자식이 없었다(아래 실험). `symtable` 출력은 버전마다 다르니 자기 버전으로 확인한다.

### 2. 스코프 체인 = 해시 테이블의 스택

```text
  total = 0; rate = 0.1                 ← 전역
  fun price(price) {                    ← 함수
      let total = price * (1 + rate)
      for (let i …) { … i … total … }   ← 블록
  }

  블록 진입 시 표를 push, 나갈 때 pop. 찾기는 위에서 아래로.

   ┌────────────────────┐  top
   │ 블록   { i }        │   i     → 0칸 위에서 찾음
   ├────────────────────┤
   │ 함수   { price,     │   price → 1칸 위
   │         total }     │   total → 1칸 위 (전역 total을 가림 = 섀도잉)
   ├────────────────────┤
   │ 전역   { total,     │   rate  → 2칸 위
   │         rate }      │   ratee → 끝까지 없음 → "정의되지 않은 이름" 오류
   └────────────────────┘
```

- *렉시컬(정적) 스코프*: 이름이 **소스에 적힌 위치**의 바깥 블록을 따라 해석되는 규칙. Java·JS·Python·C·Go·Rust가 모두 이것이다.
- *동적 스코프*: 이름이 **호출한 쪽**을 따라 해석되는 규칙. 옛 Lisp 일부, 셸 변수 등에 있다. 이 노트의 언어들은 아니다.
- *렉시컬 주소*: "몇 칸 위 표의 몇 번째"라는 위치. 컴파일러가 이름을 이 주소로 바꿔 두면 실행 중에는 문자열로 찾지 않는다. 원고 §2의 "LOAD 0x01"이 이 생각이다.

### 3. 언어마다 다른 규칙 — 같은 원리, 다른 경계

| | 새 스코프를 만드는 것 | 같은 이름 재선언 | 특이점 |
|---|---|---|---|
| Java 21 | 블록·메서드·클래스 | 지역 변수끼리 가리면 **컴파일 오류**(JLS §6.4) | 필드는 매개변수·지역 변수가 가릴 수 있다 |
| JS(ES2024) | `let`·`const`는 블록, `var`는 **함수** | `let` 블록마다 새로 | `for (let …)`은 반복마다 새 바인딩, `let`은 선언 전 접근 금지(TDZ) |
| Python 3.12 | 함수·클래스·모듈, 컴프리헨션(숨은 중첩 스코프), 3.12의 `type` 문·타입 매개변수(어노테이션 스코프). `if`·`for` 블록은 아님 | 대입이 있으면 그 함수의 지역 | `global`·`nonlocal` 문으로 바꿈. 클래스 본문의 이름은 메서드 안에서 단순 이름으로 안 보인다(`self.x`·`C.x`로) |
| C11 | 블록·함수·파일 | 안쪽 블록에서 가리기 허용 | 링크 범위(`static`·`extern`)는 [c/syntax/29](../../../languages/c/syntax/29-scope-and-linkage-static-extern/2-summary.md) |

- JLS 21 §6.4: "지역 변수 v의 이름을 v의 스코프 안에서 새 변수 선언에 쓰면 컴파일 오류다." 단 그 스코프 안의 클래스·인터페이스 선언(지역·익명 클래스) 안에서 선언하면 예외다. 반면 필드·매개변수 선언은 같은 이름의 다른 변수를 가린다.
- ECMAScript 2024 §14.7.4.4 `CreatePerIterationEnvironment`: `for (let …)`은 반복마다 새 환경을 만들어 변수를 복사한다.
- Python 3.12 실행 모델 §4.2.2: "코드 블록 안 어디에서든 이름 바인딩(대입 등)이 일어나면, 그 블록 안의 모든 사용은 현재 블록을 가리킨다. 그래서 바인딩 전에 쓰면 오류가 날 수 있다." 그 오류가 `UnboundLocalError`(`NameError` 하위)다.
- 참고: 원고 [variables-and-memory](../../foundations/variables-and-memory/README.md) §3은 `global`·`nonlocal`을 "메서드"라 부른다. 둘은 메서드가 아니라 **문(statement)** 이다. 컴파일러에게 "이 이름은 이 블록의 지역이 아니다"라고 알리는 선언이다.

### 4. 캡처 — 함수가 바깥 이름을 들고 나갈 때

안쪽 함수가 바깥 지역 변수를 쓰면, 바깥 함수가 끝나도 그 변수가 살아 있어야 한다.

```text
  def outer():                  outer의 프레임이 끝나도
      y = 2                        ┌───────────┐
      def inner():                 │ cell: y=2 │ ◀── inner.__closure__
          return x + y             └───────────┘
      return inner              x는 전역에서 LOAD_GLOBAL, y는 셀에서 LOAD_DEREF
```

- *자유 변수(free variable)*: 함수 안에서 쓰지만 그 함수에서 선언되지 않은 이름. 위 `inner`의 `y`.
- 그래서 원고 §3의 "지역 변수는 호출이 끝나면 사라진다"에는 예외가 있다. 캡처된 지역 변수는 셀·환경 레코드로 옮겨져 더 오래 산다.
- 언어마다 캡처 규칙이 다르다.
  - Java: 람다·내부 클래스가 쓰는 지역 변수는 `final`이거나 *effectively final*(한 번 대입 후 안 바뀜)이어야 한다(JLS 21 §15.27.2). 값을 복사해 가므로 바뀌면 안 된다.
  - JS·Python: 변수(바인딩) 자체를 공유한다. 나중에 바뀐 값이 보인다.
- 클로저의 수명·누수·경쟁은 [07-scope-closures-first-class-functions](../07-scope-closures-first-class-functions/2-summary.md)가 맡는다.

### 실험: 스코프 체인 모형과 네 런타임의 경계

- 환경: Temurin 21.0.12 · node 22.23.2(`node:22-alpine`) · CPython 3.12.14(`python:3.12-slim`), 모두 `--cpus=2 --network none`.

(1) 해시 테이블 스택 모형(`Scopes.java`, 위 그림의 선언을 그대로 넣음):

```text
  i     -> Sym[name=i, kind=local, depth=2] (0 hops up)
  price -> Sym[name=price, kind=param, depth=1] (1 hop up)
  total -> Sym[name=total, kind=local, depth=1] (1 hop up)
  rate  -> Sym[name=rate, kind=global, depth=0] (2 hops up)
  ratee -> UNDEFINED (compile error)
  after block: i -> UNDEFINED (compile error)
  WARN 'total' shadows Sym[name=total, kind=global, depth=0]
```

(2) JS — `var`와 `let`의 루프 캡처, TDZ, 호이스팅:

```text
  var: [ 3, 3, 3 ]  let: [ 0, 1, 2 ]
  typeof i after loop: number 3  typeof j: undefined
  TDZ: ReferenceError Cannot access 'tdz' before initialization
  console.log(typeof hoisted, hoisted); var hoisted = 1;  → undefined undefined
```

(3) Java — 캡처 규칙과 섀도잉:

```text
  for (int i = 0; i < 3; i++) fs.add(() -> i);
  → Capture.java:6: error: local variables referenced from a lambda expression must be final or effectively final

  for (...) { int k = i; fs.add(() -> k); }  +  for (int x : List.of(10, 20)) fs.add(() -> x);
  → [0, 1, 2, 10, 20]

  int x = 1; { int x = 2; }
  → error: variable x is already defined in method main(String[])

  int count = 0;  void add(int count) { count = count + 1; }   →  s.add(5) 뒤 field count = 0
```

(4) Python — 대입 하나가 스코프를 바꾼다, 늦은 바인딩:

```text
  count = 0
  def inc(): count += 1
  inc() → UnboundLocalError: cannot access local variable 'count' where it is not associated with a value

  symtable(3.12.14):  top    [('x','global'), ('outer','global')]
                      outer  [('y','local'), ('inner','local')]
                      inner  [('x','global'), ('y','free')]
  dis(inner):  COPY_FREE_VARS 1 · LOAD_GLOBAL 0 (x) · LOAD_DEREF 0 (y) · BINARY_OP 0 (+)

  [lambda: i for i in range(3)]        → [2, 2, 2]
  [lambda i=i: i for i in range(3)]    → [0, 1, 2]
```

- 관찰 1 — JS `var`·Python 리스트 컴프리헨션 람다는 **바인딩 하나**를 공유해 마지막 값을 본다. JS `let`과 Java(값 복사 + effectively final)는 반복마다 다른 값을 본다.
- 관찰 2 — Java는 지역 변수끼리의 섀도잉을 컴파일 오류로 막지만, **필드**를 가리는 매개변수는 허용한다. 그래서 필드 버그는 컴파일러가 못 잡았다(`field count = 0`).
- 관찰 3 — Python의 이름 해석은 컴파일 시점에 정해진다. `dis`에서 `x`는 `LOAD_GLOBAL`, `y`는 `LOAD_DEREF`(셀)로 이미 갈려 있다.

## 쓰이는 자료구조·알고리즘

- **스코프 체인 = 해시 테이블의 스택** — 블록 진입 push, 탈출 pop, 조회는 위에서 아래로. 깊이 d면 최악 d번의 해시 조회([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)).
- **다른 구현** — 이름마다 선언 스택을 두는 해시 테이블 하나 + 블록을 나갈 때 그 블록에서 넣은 이름만 되돌리는 기록. 조회가 O(1)이다. 함수형 컴파일러는 영속 맵을 쓰기도 한다([data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)).
- **AST 순회** — 선언을 표에 넣고 사용을 찾으며 깊이 우선으로 내려간다([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)). Python처럼 "블록 어디서든 대입하면 지역"인 언어는 블록을 한 번 다 훑은 뒤에 결정한다.
- **렉시컬 주소** — (몇 칸 위, 몇 번째). 실행 중 조회를 배열 접근으로 바꾼다.

## 적용 — 풀어나가는 법

1. **"이 이름이 어느 선언인가"를 도구로 확인한다.**
   - Python: `dis.dis(f)`에서 `LOAD_FAST`(지역)·`LOAD_FAST_CHECK`(초기화 전일 수 있는 지역 — 3.12)·`LOAD_GLOBAL`·`LOAD_DEREF`(캡처)·`LOAD_NAME`을 본다. `symtable.symtable(src, name, "exec")`로 스코프를 본다.
   - Java: IDE의 "선언으로 이동". 컴파일 오류 문구(`must be final or effectively final`, `is already defined`)는 의미 분석 단계의 오류다.
   - JS: `var`를 `let`/`const`로 바꾸면 블록 스코프·TDZ가 숨은 버그를 오류로 드러낸다.
2. **필드와 같은 이름의 매개변수는 `this.`로만 쓴다.** 생성자·세터에서 `this.count = count`. 정적 분석기의 섀도잉 경고를 켠다(도구별 규칙 이름은 `[?]` — 팀 도구 문서에서 확인).
3. **반복문 안에서 만드는 콜백은 무엇을 캡처하는지 본다.**
   - JS: `let`으로 선언하면 반복마다 새 바인딩.
   - Python: 기본 인자(`lambda i=i:`)나 `functools.partial`로 그 시점 값을 묶는다.
   - Java: 반복마다 새 지역 변수(`int k = i`)를 만든다. 향상된 `for`의 변수는 이미 반복마다 새로다.
4. **Python에서 바깥 변수를 바꿔야 하면 `nonlocal`·`global`을 쓰되**, 보통은 값을 반환하거나 객체 필드로 옮기는 편이 읽기 쉽다.

## 장애 시나리오와 대처

### 1. 섀도잉 — 고쳤다고 생각한 값이 그대로 (⚠)

- **현상**: 세터·생성자를 불렀는데 필드가 안 바뀐다. 예외는 없다.
- **보이는 형태**: `void add(int count) { count = count + 1; }` — 실험에서 `field count = 0`. JS에서는 함수 안 `let total`이 바깥 `total`을 가려 바깥 값이 그대로(`outer total still 10`).
- **원인**: 안쪽 선언이 바깥 선언을 가렸다. 이름 해석은 스코프 체인의 **가장 가까운** 표에서 멈춘다. Java는 지역끼리의 가리기는 막지만 필드 가리기는 허용한다(JLS §6.4).
- **대처**: `this.count`로 명시한다. 섀도잉 경고를 켠다. 같은 이름을 쓰지 않는 이름 규칙을 둔다.

### 2. 루프 클로저가 마지막 값만 캡처 (⚠)

- **현상**: 반복문에서 등록한 콜백·비동기 작업이 전부 같은 값(마지막 값)으로 실행된다.
- **보이는 형태**: JS `for (var i…) setTimeout(() => use(i))` → 모두 3. Python `[lambda: i for i in range(3)]` → `[2, 2, 2]`.
- **원인**: JS `var`는 함수 스코프라 바인딩이 하나다. Python 클로저는 값이 아니라 변수를 캡처하고, 호출 시점에 읽는다(늦은 바인딩). 반복이 끝난 뒤 호출하면 마지막 값이다.
- **대처**: JS는 `let`(반복마다 새 바인딩 — ECMAScript §14.7.4.4). Python은 기본 인자 `lambda i=i:`(실험 `[0, 1, 2]`)나 `functools.partial`. 상세는 [languages/js/syntax/05](../../../languages/js/syntax/05-var-let-const-and-tdz/2-summary.md)·[python/syntax/22](../../../languages/python/syntax/22-closures-and-late-binding/2-summary.md).

### 3. 한 줄 추가로 `UnboundLocalError`

- **현상**: 잘 돌던 Python 함수에 카운트 증가 한 줄을 넣었더니, 그 줄보다 **위의** 읽기에서 예외가 난다.
- **보이는 형태**: `UnboundLocalError: cannot access local variable 'count' where it is not associated with a value`(CPython 3.12.14).
- **원인**: 함수 안 어디든 대입이 있으면 그 이름은 함수 전체에서 지역이다(실행 모델 §4.2.2). 컴파일 시점에 정해지므로, 대입 앞의 읽기도 지역을 읽으려다 실패한다.
- **대처**: 정말 바깥 변수를 바꿀 거면 `global`/`nonlocal`을 선언한다. 보통은 값을 인자로 받고 반환하도록 고친다.

### 4. Java 람다 캡처 오류를 피하려다 공유 가변 상태

- **현상**: `effectively final` 컴파일 오류를 피하려 `int[] counter = {0}`이나 `AtomicInteger`를 캡처했다. 병렬 스트림·여러 스레드에서 값이 틀리거나 경합이 생긴다.
- **보이는 형태**: 실행마다 합계가 다르다(배열 한 칸). 또는 `AtomicInteger` 경합으로 느리다.
- **원인**: JLS §15.27.2는 "동적으로 바뀌는 지역 변수의 캡처는 동시성 문제를 부를 수 있어" 막는다고 적는다. 배열 한 칸 우회는 그 보호를 끈다.
- **대처**: 캡처 대신 `reduce`·`collect`·`sum`처럼 결과를 반환하는 연산을 쓴다. 공유 상태가 필요하면 동시성 규칙([13-language-memory-model](../13-language-memory-model/2-summary.md))을 따른다.

## 핵심 문장

- 의미 분석은 AST의 이름마다 어느 선언인지 정한다. 그 표가 심벌 테이블이다.
- 렉시컬 스코프의 이름 해석은 "해시 테이블의 스택을 위에서 아래로 찾기"다. 가장 가까운 선언이 바깥 선언을 가린다(섀도잉).
- 같은 원리라도 경계는 언어마다 다르다. Java는 블록·지역 재선언 금지, JS `var`는 함수 스코프, Python은 "대입하면 지역"이다.
- 바깥 지역 변수를 캡처한 함수는 그 변수를 더 오래 살린다. Java는 값을 복사하므로 effectively final을 요구하고, JS·Python은 변수를 공유해 늦게 바뀐 값을 본다.
- 루프 클로저의 "마지막 값만 보임"은 반복마다 새 바인딩이 생기느냐의 문제다.

## 관련 주제·근거

- 선행
  - [03-parsing-grammars-ast](../03-parsing-grammars-ast/2-summary.md) — 의미 분석의 입력인 AST
- 후속·연결
  - [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md) — 이름이 정해진 AST를 IR로
  - [05-type-systems](../05-type-systems/2-summary.md) · [07-scope-closures-first-class-functions](../07-scope-closures-first-class-functions/2-summary.md) · [13-language-memory-model](../13-language-memory-model/2-summary.md)
  - [software-design/05-connascence](../../software-design/05-connascence/2-summary.md) — 이름 커너선스와 심벌 테이블
  - 문법: [js/syntax/05 var·let·const·TDZ](../../../languages/js/syntax/05-var-let-const-and-tdz/2-summary.md) · [js/syntax/06 스코프·클로저](../../../languages/js/syntax/06-scope-and-closures/2-summary.md) · [python/syntax/21 LEGB·global·nonlocal](../../../languages/python/syntax/21-scope-legb-global-nonlocal/2-summary.md) · [python/syntax/22 늦은 바인딩](../../../languages/python/syntax/22-closures-and-late-binding/2-summary.md) · [java/syntax/29 람다](../../../languages/java/syntax/29-lambda-expressions/2-summary.md) · [c/syntax/29 스코프·링크](../../../languages/c/syntax/29-scope-and-linkage-static-extern/2-summary.md)
  - 원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) §2(심벌 테이블) · §10(`symtable`) · 원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md) §3(전역·지역·`global`·`nonlocal`)
- 문서
  - JLS SE21 §6.4 Shadowing and Obscuring(지역 재선언 오류, 필드·매개변수 가리기) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html> · §15.27.2 Lambda Body(effectively final, 이유) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - ECMAScript 2024 §14.7.4.4 CreatePerIterationEnvironment <https://tc39.es/ecma262/2024/>
  - Python 3.12 언어 레퍼런스 4장 Execution model §4.2.2 Resolution of names <https://docs.python.org/3.12/reference/executionmodel.html>
  - Aho 외 『Compilers』(Dragon Book) 2.7절·6장 `[?]`
- 실험 목록
  - 해시 테이블 스택 스코프 모형(`Scopes.java`) · 람다 캡처 컴파일 오류와 우회(`Capture.java`·`Capture2.java`) · 필드 섀도잉(`Shadow.java`) · 지역 재선언 오류(`Shadow2.java`) — Temurin 21.0.12
  - `var`/`let` 루프 캡처·TDZ·호이스팅·블록 섀도잉(`closure.js`·`tdz2.js`) — node 22.23.2
  - `UnboundLocalError`, `symtable`, `dis`(`LOAD_GLOBAL`·`LOAD_DEREF`), 늦은 바인딩과 기본 인자(`scope.py`·`late.py`) — CPython 3.12.14
  - 초기화 전 읽기의 `LOAD_FAST_CHECK`(`dis`), 메서드에서 클래스 변수 단순 이름 → `NameError` — CPython 3.12.14(`python:3.12-slim`, `python -c`)
