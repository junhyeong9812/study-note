# js/syntax/12 — 옵셔널 체이닝·널 병합·논리 할당: 「안 부르는 것」이 전부다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제에는 두 판이 갈린 블록이 0개다.** 그래서 양쪽을 나란히 실은 자리가 없다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js12b-12a-shortcircuit.js
// js12b-12b-grid.js
// js12b-12c-assign.js
// js12b-12s-strict.js
// js12b-12x-forms.js
// js12b-12y-caret.js
// js12b-hb-browser.js
// js12b-versions.sh
// js12b-vdiff.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **호출 횟수**(특히 0회) |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외의 종류** · `SyntaxError` 가 가리키는 **열** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ 격자의 **SAME/SPLIT 판정** · 전역 오염 목록 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 사슬이 끊겼을 때 무엇이 안 불리나 — **인자도 첨자도 아예 평가되지 않는다** ★★★

**출력**

```text
===== node20 js12b-12a-shortcircuit.js (exit=0) =====
[1] argument of ?.[] and ?.() is never evaluated when the chain is cut
expression                        result      probe calls
o.a?.[f('k')]        a=null       undefined   0
o.a?.[f('k')]        a=obj        hit         1
o.fn?.(f(1))         no fn        undefined   0
o.fn?.(f(1))         has fn       got1        1

[2] was the right-hand side called?  ??  vs  ||  vs  &&
expression                        result      rhs calls
left=0            left ?? f('R')  0           0
left=0            left || f('R')  R           1
left=0            left && f('R')  0           0
left=null         left ?? f('R')  R           1
left=null         left || f('R')  R           1
left=null         left && f('R')  null        0
left=undefined    left ?? f('R')  R           1
left=undefined    left || f('R')  R           1
left=undefined    left && f('R')  undefined   0
left='x'          left ?? f('R')  x           0
left='x'          left || f('R')  x           0
left='x'          left && f('R')  R           1

[3] a?.b.c short-circuits the WHOLE chain; parentheses end it
nil.a?.b.c                -> undefined
nil.a?.b.c.d.e            -> undefined
(nil.a?.b).c              -> TypeError Cannot read properties of undefined (reading 'c')
nil.a.b.c                 -> TypeError Cannot read properties of null (reading 'b')
nil.a?.b?.c               -> undefined
deep.a?.b[f('c')].d       -> undefined   probe calls 0

[4] ?. stops at null and undefined ONLY
value                             v?.ctor     v?.nope
0                                 Number      undefined
-0                                Number      undefined
''                                String      undefined
NaN                               Number      undefined
false                             Boolean     undefined
0n                                BigInt      undefined
null                              undefined   undefined
undefined                         undefined   undefined

[5] delete a?.b
delete del.a?.b           -> true
delete del2.a?.b          -> true
keys of del2.a after delete -> []
```

**왜 그런가**

- `[1]` **탐침 호출은 `0 · 1 · 0 · 1`** 이다. 사슬이 끊기면 **대괄호 안 식과 괄호 안 인자가 아예 평가되지 않는다.**
  ★★★ **값으로는 안 갈린다** — 끊긴 두 줄의 결과는 둘 다 `undefined` 다. **0 이라는 숫자만이 근거다.**
- `[3]` **예외가 나는 줄은 두 줄**이다 — `(nil.a?.b).c` 와 `nil.a.b.c`.
  ★★★ `nil.a?.b.c.d.e` 는 **점이 넷 더 붙어도** 조용하다. `?.` 는 **한 칸이 아니라 사슬 전체**를 끊기 때문이다.
  ★★ **괄호가 사슬을 닫는다.** `(nil.a?.b)` 에서 사슬이 끝나고, 그 결과인 `undefined` 에 `.c` 를 **새로** 건 것이라 터진다.
- `deep.a?.b[f('c')].d` 의 **탐침 호출은 0회**다. 첨자 식조차 평가되지 않는다.
- `[4]` `?.` 가 **막는 것은 `null`·`undefined` 둘**이고, `0`·`-0`·`''`·`NaN`·`false`·`0n` 은 **전부 통과**한다.
  통과한 줄에서 `v?.ctor` 가 `Number`·`String`·`Boolean`·`BigInt` 로 나오는 것이 그 증거다 — **래퍼를 만들어 읽었다**는 뜻이다.
- `[5]` 둘 다 **`true`** 다. `delete` 의 반환값은 「지웠나」가 아니라 **「거부되지 않았나」** 이므로,
  `a` 가 `null` 이라 아무 일도 안 했을 때도 `true` 다. 실제로 지운 쪽은 `del2.a` 의 키가 비는 것으로 확인된다.

### 2. 같은 값을 두 연산자에 던지면 — **falsy 13종 중 6종에서 갈린다** ★★★

**출력**

```text
===== node20 js12b-12b-grid.js (exit=0) =====
[1] v ?? DEF   vs   v || DEF   vs   v && DEF
value       truthy   nullish  v ?? DEF    v || DEF    v && DEF    ?? vs ||
0           false    false    0           'DEF'       0           SPLIT
-0          false    false    -0          'DEF'       -0          SPLIT
''          false    false    ''          'DEF'       ''          SPLIT
NaN         false    false    NaN         'DEF'       NaN         SPLIT
false       false    false    false       'DEF'       false       SPLIT
0n          false    false    0n          'DEF'       0n          SPLIT
null        false    true     'DEF'       'DEF'       null        same
undefined   false    true     'DEF'       'DEF'       undefined   same
'0'         true     false    '0'         '0'         'DEF'       same
[]          true     false    []          []          'DEF'       same
{}          true     false    {}          {}          'DEF'       same
' '         true     false    ' '         ' '         'DEF'       same
1           true     false    1           1           'DEF'       same

split cells 6 / 13

[2] the same grid written as a default-value idiom
input       v ?? 8080   v || 8080
0           0           8080
''          ''          8080
false       false       8080
null        8080        8080
undefined   8080        8080
3000        3000        3000

[3] ?? is NOT the same as an isNullish() call: it also short-circuits
0 ?? expensive()      -> 0   calls 0
0 || expensive()      -> 8080   calls 1
ternary on isNullish  -> 0   calls 0
```

**왜 그런가**

- ★★★ **`SPLIT` 은 6 / 13** 이다 — `0`·`-0`·`''`·`NaN`·`false`·`0n`.
  공통점은 **falsy 인데 nullish 가 아닌 것**이다. `truthy` 칸이 `false` 이면서 `nullish` 칸도 `false` 인 줄이 정확히 그 여섯이다.
- ★★ `null`·`undefined` 줄에서는 **두 연산자가 같은 답**을 낸다. 두 값은 falsy 이면서 nullish 이기도 해서 **둘 다 오른쪽을 쓴다.**
  ★ 그래서 「`??` 로 바꿨더니 동작이 달라졌다」는 **`null` 때문일 수 없다.** 범인은 `0` 이나 `''` 다.
- `[3]` 의 `calls` 는 **`0 · 1 · 0`** 이다.
  ★★★ 가운데 줄만 1 이라는 것이 **`??` 가 「검사 함수」가 아니라 「연산자」** 라는 증거다 —
  손으로 쓴 삼항(`isNullish ? f() : x`)과 **호출 횟수가 같다.**

### 3. 로그가 둘로 갈리는 자리 — **값은 같고 setter 호출만 다르다** ★★★

**출력**

```text
===== node20 js12b-12c-assign.js (exit=0) =====
[1] b.x ||= R   vs   b.x = b.x || R      (same value, different writes)
start     form                  final     rhs calls  setter log
'keep'    b.x ||= R             'keep'    0          ["get"]
'keep'    b.x = b.x || R        'keep'    0          ["get","set:keep"]
0         b.x ||= R             'R'       1          ["get","set:R"]
0         b.x = b.x || R        'R'       1          ["get","set:R"]
''        b.x ||= R             'R'       1          ["get","set:R"]
''        b.x = b.x || R        'R'       1          ["get","set:R"]
null      b.x ||= R             'R'       1          ["get","set:R"]
null      b.x = b.x || R        'R'       1          ["get","set:R"]

[2] ??=  vs  ||=  vs  &&=      (setter log is the answer)
start     form        final     rhs calls  setter log
0         b.x ??= R   0         0          ["get"]
0         b.x ||= R   'R'       1          ["get","set:R"]
0         b.x &&= R   0         0          ["get"]
''        b.x ??= R   ''        0          ["get"]
''        b.x ||= R   'R'       1          ["get","set:R"]
''        b.x &&= R   ''        0          ["get"]
null      b.x ??= R   'R'       1          ["get","set:R"]
null      b.x ||= R   'R'       1          ["get","set:R"]
null      b.x &&= R   null      0          ["get"]
undefined b.x ??= R   'R'       1          ["get","set:R"]
undefined b.x ||= R   'R'       1          ["get","set:R"]
undefined b.x &&= R   undefined 0          ["get"]
'v'       b.x ??= R   'v'       0          ["get"]
'v'       b.x ||= R   'v'       0          ["get"]
'v'       b.x &&= R   'R'       1          ["get","set:R"]

[3] on a frozen object: ||= only fails when it actually tries to write (sloppy mode)
case                              result
frozen.keep ||= 'R'   (truthy)    no throw, value='kept'
frozen.keep ||= 'R'   (falsy)     no throw, value=''
frozen.keep ??= 'R'   (null)      no throw, value=null
frozen.keep = keep || 'R'         no throw, value=''
```

**왜 그런가**

- ★★★ `[1]` 의 첫 두 줄이 이 주제의 급소다.
  `b.x ||= R` 의 로그는 **`["get"]`**, `b.x = b.x || R` 의 로그는 **`["get","set:keep"]`** 이다.
  **`final` 칸은 둘 다 `'keep'` 으로 같다.** 값으로는 원리상 못 가르고, **로그 한 줄이 유일한 차이**다.
- 시작값이 falsy 인 나머지 여섯 줄에서는 **두 형태가 완전히 같다** — 그래서 평소에는 아무도 이 차이를 못 본다.
- `[2]` 시작값이 `0` 일 때 **쓰는 것은 `||=` 뿐**이다. `??=` 는 `0` 이 nullish 가 아니라서, `&&=` 는 `0` 이 truthy 가 아니라서 안 쓴다.
  ★★ 세 연산자의 조건을 한 줄로 — **`??=` 는 nullish 일 때, `||=` 는 falsy 일 때, `&&=` 는 truthy 일 때.**
- `[3]` 네 줄이 다 조용한 이유는 **둘로 갈린다.**
  첫 줄은 값이 truthy 라 **쓰기를 시도조차 안 했고**, 나머지 셋은 시도했지만 **비엄격이라 조용히 실패**했다.
  ★★★ **「안 터졌다」는 「막히지 않았다」가 아니다** — 값 칸이 전부 원래 값 그대로인 것이 실패의 증거다.

### 4. 두 모드에서 같은 줄을 돌리면 — **11칸 중 6칸이 모드에 달렸다** ★★

**출력**

```text
===== node20 js12b-12s-strict.js (exit=0) =====
[1] strict-first grid   (each probe owns a unique global name, printed back as <G>)
plain  G = 1                  SPLIT strict: ReferenceError <G> is not defined
                                    sloppy: OK 1
plain  var q; q = 1           SAME  strict: OK 1
                                    sloppy: OK 1
logical  G ??= 1              SAME  strict: ReferenceError <G> is not defined
                                    sloppy: ReferenceError <G> is not defined
logical  G ||= 1              SAME  strict: ReferenceError <G> is not defined
                                    sloppy: ReferenceError <G> is not defined
frozen.p ||= 'R'   p=''       SPLIT strict: TypeError Cannot assign to read only property 'p' of object '#<Object>'
                                    sloppy: OK ""
frozen.p ??= 'R'   p=null     SPLIT strict: TypeError Cannot assign to read only property 'p' of object '#<Object>'
                                    sloppy: OK null
getter-only ??= 'R'           SPLIT strict: TypeError Cannot set property p of #<Object> which has only a getter
                                    sloppy: OK null
getter-only ||= 'R'           SPLIT strict: TypeError Cannot set property p of #<Object> which has only a getter
                                    sloppy: OK 0
delete o?.p   configurable    SAME  strict: OK true keys=[]
                                    sloppy: OK true keys=[]
delete o?.p   non-config      SPLIT strict: TypeError Cannot delete property 'p' of #<Object>
                                    sloppy: OK false keys=["p"]
delete nul?.p  nul=null       SAME  strict: OK true
                                    sloppy: OK true

mode-dependent cells 6 / 11

[2] what the sloppy probes left behind on globalThis
globals starting with js12b -> ["js12bSloppyG0"]
any js12bStrictG* leaked?   -> false
if strict had run SECOND it would have read the sloppy leftover and reported SAME.
```

**왜 그런가**

- ★★★ **`SPLIT` 은 6 / 11** 이다. 나머지 다섯은 모드와 무관하다.
- ★★★ **`G ??= 1` 은 두 모드 모두 `ReferenceError`** 다. `G = 1` 과 **다르다.**
  논리 할당은 **먼저 읽기 때문**이다 — 선언되지 않은 이름을 읽는 순간 모드와 무관하게 터진다.
  ★★ **이것이 이 주제에서 뒤집힌 전제다.** 「비엄격이니 `??=` 도 전역을 만들겠지」가 틀렸다.
- `[2]` **globalThis 에 남은 이름은 하나** — `js12bSloppyG0`, 평범한 `G = 1` 탐침이 만든 것이다.
  ★★★ 만약 엄격 탐침과 **이름을 공유했다면** 뒤이어 도는 엄격 탐침이 그 값을 읽어 **`OK 1`** 을 답했을 것이고,
  두 모드가 「같다」는 거짓 결과가 나왔을 것이다. **값도 정상이고 에러도 없어 어떤 검사기에도 안 걸린다.**
- ★ 그래서 처방이 둘이다 — **엄격을 먼저 돌린다**(오염 전에 찍는다) · **이름을 다르게 준다**(공유 자체를 없앤다).
  이 블록은 둘을 다 쓰고, 마지막 두 줄이 **실제로 안 샜다**는 것을 출력으로 보인다.

### 5. 컴파일되는 것과 안 되는 것 — **문법은 모드를 안 탄다** ★★

**출력**

```text
===== node20 js12b-12x-forms.js (exit=0) =====
[1] does it even compile?   (strict run first, then sloppy)
a ?? b || c       SAME  SyntaxError Unexpected token '||'
a || b ?? c       SAME  SyntaxError Unexpected token '??'
a ?? b && c       SAME  SyntaxError Unexpected token '&&'
a && b ?? c       SAME  SyntaxError Unexpected token '??'
(a ?? b) || c     SAME  OK
a ?? (b || c)     SAME  OK
a ?? b ?? c       SAME  OK
a || b || c       SAME  OK
new a?.b()        SAME  SyntaxError Invalid optional chain from new expression
new (a?.b)()      SAME  OK
a?.b()            SAME  OK
a?.()             SAME  OK
new a?.()         SAME  SyntaxError Invalid optional chain from new expression
a?.b`tpl`         SAME  SyntaxError Invalid tagged template on optional chain
a?.b = 1          SAME  SyntaxError Invalid left-hand side in assignment
delete a?.b       SAME  OK
a?.b++            SAME  SyntaxError Invalid left-hand side expression in postfix operation
a ??= b           SAME  OK
a?.b ??= c        SAME  SyntaxError Invalid left-hand side in assignment
({}) ?? 1         SAME  OK

mode-dependent cells 0 / 20

[2] duplicate keys in an object literal -- ES5 strict forbade this, ES6+ does not
strict  { a: 1, a: 2, a: 3 }  -> OK {"a":3}
sloppy  { a: 1, a: 2, a: 3 }  -> OK {"a":3}
```

**왜 그런가**

- **컴파일되는 것은 10개**다 — `(a ?? b) || c` · `a ?? (b || c)` · `a ?? b ?? c` · `a || b || c` ·
  `new (a?.b)()` · `a?.b()` · `a?.()` · `delete a?.b` · `a ??= b` · `({}) ?? 1`.
  나머지 **10개가 `SyntaxError`** 다.
- ★★★ **`SPLIT` 은 0 / 20** 이다. 문법은 `"use strict"` 를 타지 않는다 — **파서가 보는 것은 모드가 아니라 문법 규칙**이기 때문이다.
- `[2]` **두 줄 모두 `OK {"a":3}`** 이다.
  ★★ 이것이 놀라운 이유는 **ES5 의 엄격 모드가 중복 키를 `SyntaxError` 로 막았기** 때문이다.
  ES6 에서 그 금지가 **사라졌고**, 지금은 두 모드 모두 **나중 것이 이긴다.** 13번 주제에서 다시 본다.

### 6. 캐럿은 어디를 가리키나 — **네 조합이 같은 열에서 거부된다** ★

**출력**

```text
===== node20 js12b-12y-caret.js (exit=0) =====
=== a ?? b || c
ex.js:1
a ?? b || c
       ^^
SyntaxError Unexpected token '||'

=== a || b ?? c
ex.js:1
a || b ?? c
       ^^
SyntaxError Unexpected token '??'

=== a ?? b && c
ex.js:1
a ?? b && c
       ^^
SyntaxError Unexpected token '&&'

=== a && b ?? c
ex.js:1
a && b ?? c
       ^^
SyntaxError Unexpected token '??'

=== (a ?? b) || c
compiles.

=== a ?? (b || c)
compiles.

=== a ?? b ?? c
compiles.

=== new a?.b()
ex.js:1
new a?.b()
     ^^
SyntaxError Invalid optional chain from new expression

=== a?.b`t`
ex.js:1
a?.b`t`
    ^^^
SyntaxError Invalid tagged template on optional chain

=== a?.b ??= c
ex.js:1
a?.b ??= c
^^^^
SyntaxError Invalid left-hand side in assignment
```

**왜 그런가**

- ★★ **첫 네 식의 캐럿이 전부 8열**이다 — `a ?? b ` 까지 읽고 **세 번째 연산자를 만나는 자리**다.
  네 식의 **문구는 서로 다르지만**(`'||'`·`'??'`·`'&&'`), **멈추는 위치는 같다.**
- ★★★ 그 열이 말하는 것은 **「우선순위가 없다」** 이다. 우선순위가 낮거나 높다면 파서가 **묶어서 받아들였을** 것이다.
  받아들이지 않고 **그 자리에서 멈춘다**는 것은 **두 연산자의 결합 방식을 문법이 정의하지 않았다**는 뜻이다.
  ★ 값으로는 이것을 원리상 못 가른다 — 어느 쪽으로 묶든 컴파일이 안 되므로 비교할 값이 없다.
- ★ `a?.b ??= c` 의 캐럿은 **`^^^^`(1\~4열)**, 즉 **왼쪽 식 전체**를 덮는다.
  「연산자가 문제」가 아니라 **「이 식은 대입 대상이 될 수 없다」** 는 진단이다.

### 7. `?.` 는 정확히 무엇을 막는가 ★★★

- ★★★ **두 종류뿐이다 — `null` 과 `undefined`.**
  falsy 는 여덟 종(`false`·`0`·`-0`·`0n`·`''`·`null`·`undefined`·`NaN`)이고, `?.` 는 **그 중 둘만** 본다.
  1번 답의 `[4]` 가 나머지 여섯이 전부 통과하는 것을 전수로 보인다.
- ★★★ **`a.b` 가 `null` 이면 `a?.b.c` 는 그대로 터진다.** `?.` 는 **자기 왼쪽만** 검사한다.
  그 자리에는 `a?.b?.c` 가 필요하다. 1번 답에서 `nil.a?.b?.c` 가 조용한 것이 그 확인이다.
- ★★ `a?.b.c` 는 **사슬 하나**이고 `(a?.b).c` 는 **사슬 + 새 식**이다.
  괄호가 사슬을 닫으므로 보호가 괄호 밖까지 이어지지 않는다.
- ★ 5번 답의 문법 격자가 확인한다 — `a?.b = 1`·`a?.b ??= c`·`a?.b++` 는 전부 `SyntaxError` 이고
  **`delete a?.b` 만 `OK`** 다. `delete` 는 대입이 아니라 **삭제 연산자**라서 예외로 허용된다.

### 8. 왜 `??` 를 `||` 와 못 섞는가 ★★

- ★★★ **파싱 오류다.** 실무에서 이 차이가 큰 이유는, 런타임 오류는 **그 줄을 지날 때만** 나지만
  파싱 오류는 **파일 전체가 로드되지 않아** 전혀 다른 곳에서 실패로 보이기 때문이다.
  6번 답의 캐럿이 **컴파일 시점**에 찍힌다는 것이 그 증거다.
- ★★ 괄호를 치면 **묶는 방법이 소스에 적혀 있어** 파서가 고를 필요가 없다.
- ★ `a ?? b ?? c` 는 **같은 연산자끼리**라 결합 방향이 정의돼 있다. 정의되지 않은 것은 **서로 다른 두 연산자의 조합**뿐이다.

### 9. 어디서 조용히 틀리나 ★★★

넷을 대면 이렇다.

1. ★★★ **`||` 로 기본값을 줘서 `0`·`''` 를 삼킨다.** 2번 답의 6칸이 전부 이 사고다.
2. ★★★ **`||=` 를 `= x || y` 로 바꿔 적어 쓰기가 한 번 더 일어난다.** 값이 같아 테스트가 통과한다.
3. ★★ **동결·getter-only 객체에 비엄격으로 쓰기를 시도해 조용히 실패한다.**
4. ★★ **`(a?.b).c` 로 괄호를 쳐 보호를 잃는다.** 이쪽은 조용하지 않고 터지지만, **왜 터지는지가 안 보인다.**

- ★★★ **11번에서 본 것과 같은 모양은 2번**이다. 11번의 핵심 문장 하나가
  「**스프레드는 정의하고 `Object.assign` 은 대입한다 — 대상의 setter 한 자리에서 갈린다**」였고,
  여기서는 「`||=` 와 `= x || y` 는 **값이 같은데 쓰기 횟수가 다르다**」이다.
  **둘 다 값으로는 안 보이고 setter 로그로만 갈린다** — 같은 집안이다.
- ★★ **아니다.** 3번 답의 `[3]` 첫 줄은 **값이 truthy 라 쓰기를 시도조차 안 한 것**이고, 동결은 그대로다.
  falsy 로 바꾸면 시도하고, 비엄격이라 조용히 실패한다.
- ★ 발견하는 법은 셋이다 — **엄격 모드로 돌려 본다**(4번 답의 격자) · **쓴 뒤 값을 다시 읽는다** ·
  **setter 에 로그를 심는다**(3번 답의 방법).

### 10. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

**왜 그런가**

- ★★★ **이 주제에서 두 판이 갈린 칸은 0개다.** 위 대조기가 19블록을 두 판에서 돌려 **갈린 것은 한 블록**뿐이라고 세는데,
  그 한 블록은 **14번 주제의 `toSorted`**(ES2024, v18 에 없음)이고 **12번 주제의 블록은 전부 동일**하다.
- ★★★ **명세의 몫은 「종류」이고 「문구」는 엔진의 사정**이다.
  어떻게 아는가 — 11번 주제에서 **같은 줄의 문구가 v18 과 v20 에서 실제로 갈렸고 종류는 같았다.**
  한 번이라도 갈린 것은 보장이 아니다.
- ★★ **호스트가 정하는 칸은 0개**다. Chrome 151 의 열아홉 줄이 Node 쪽과 전부 같다.
  ★ 다만 **문구까지 같은 것은 둘 다 V8 이기 때문**이지 명세가 정한 것이 아니다.
- ★ **부적용인 창은 ③ 브랜드 태그**(`Object.prototype.toString.call`)다.
  `?.`·`??` 는 값의 **종류**를 묻지 않으므로 브랜드로 가를 칸이 아예 없다 —
  **「재 봤더니 같았다」가 아니라 「잴 것이 없다」** 이다. 「안 쟀다」와 다른 제4의 상태다.

### 11. 경계 — 어디까지가 이 주제인가 ★★

- **falsy 목록** → [02번](../02-coercion-and-loose-equality/2-summary.md) ·
  **엄격 모드 규칙 전부** → 목록의 **35번 주제** ·
  **동결이 왜 쓰기를 막나** → [14번](../14-property-descriptors-and-freezing/2-summary.md) ·
  **`Object.is`·SameValueZero** → 목록의 **33번 주제**.
- ★★★ **10번의 기본값은 `undefined` 만 「비었다」로 세고, `??` 는 `null` 까지 센다.**
  구조 분해의 `const { a = 1 } = { a: null }` 은 `a` 가 **`null`** 이고, `obj.a ?? 1` 은 **`1`** 이다.
  **같은 「기본값」이라는 말이 두 문법에서 서로 다른 집합을 가리킨다** — 이것이 10번에서 이어받은 매듭이다.
- ★★ 02번에서 그대로 받아 쓰는 것은 **`ToBoolean` 의 falsy 여덟 종 목록**이다. 여기서 그 목록을 다시 증명하지 않는다.
- ★ 이 주제가 끝까지 책임지는 것 셋 —
  ① **`?.` 가 사슬 단위로 끊는다는 것**(괄호가 닫는다는 것 포함)
  ② **`??` 와 `||` 가 갈리는 칸의 정확한 목록**
  ③ **논리 할당이 대입 자체를 건너뛴다는 것**(setter 로그로).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js12b-12a-shortcircuit.js` | ★★★ **호출 횟수 0** · 사슬 전체 단축 · 괄호가 사슬을 닫는 것 · `?.` 가 막는 값 8종 격자 | node20 1벌 + node18 대조 1벌 |
| `js12b-12b-grid.js` | ★★★ **`??` 대 `\|\|` 갈린 칸 6 / 13** · 오른쪽 호출 횟수 | node20 1벌 + node18 대조 1벌 |
| `js12b-12c-assign.js` | ★★★ **setter 로그가 둘로 갈리는 것** · 세 연산자 × 다섯 시작값 격자 | node20 1벌 + node18 대조 1벌 |
| `js12b-12s-strict.js` | ★★★ **모드에 달린 칸 6 / 11** · 전역 오염 실측(1개) | node20 1벌 + node18 대조 1벌 |
| `js12b-12x-forms.js` | **문법 20형태 × 두 모드 — SPLIT 0** · 중복 키가 엄격에서도 통과 | node20 1벌 + node18 대조 1벌 |
| `js12b-12y-caret.js` | ★★ **캐럿 열**(18-C) — 값으로 못 가르는 것 | node20 1벌 + node18 대조 1벌 |
| `js12b-hb-browser.js` · `js12b-page.html` | ★★★ **호스트가 정하는 칸 0개** | Chrome 151 1벌 |
| `js12b-vdiff.sh` | **19블록 중 갈린 것 1개**(그 하나는 14번 주제) | 1벌 |
| `js12b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `Cannot read properties of undefined (reading 'c')` ·
  `Unexpected token '\|\|'` · `Invalid optional chain from new expression` ·
  `Invalid tagged template on optional chain` · `Invalid left-hand side in assignment` ·
  `Cannot assign to read only property 'p' of object '#<Object>'` ·
  `Cannot set property p of #<Object> which has only a getter`.
  **종류(`TypeError`·`SyntaxError`·`ReferenceError`)만 명세가 정한다.**
- ★★ **캐럿이 가리키는 열** — 이 판에서 안정적이었지만 **파서의 사정**이다. 판이 오르면 다시 찍어야 한다.
- ★ **브라우저와 Node 20 의 문구가 같은 것** — **같은 계열의 V8 이기 때문**이다.

**`?.` 가 사슬 전체를 끊는 것 · 대괄호 안 식과 인자가 평가되지 않는 것 · `??` 가 `null`/`undefined` 둘만 보는 것 · `??` 를 `\|\|`/`&&` 와 괄호 없이 못 섞는 것 · 옵셔널 체인이 대입 대상이 못 되는 것 · `delete a?.b` 가 허용되는 것 · 논리 할당이 조건이 맞을 때만 대입하는 것 · 엄격 모드에서 실패한 쓰기가 `TypeError` 인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 **문구** ·
  `?.` 를 프라이빗 필드(`a?.#x`)와 섞은 형태 · `super?.()` · 모듈(`.mjs`)에서의 같은 격자
  (모듈은 항상 엄격이라 **엄격 열과 같을 것으로 예상하지만 안 돌려 봤다**) · Node 18 보다 낮은 판.
- ★ **못 잰 것** — **`?.`·`??`·`??=` 의 비용.** 쓰기 횟수가 다르다는 것은 **관찰했지만**
  그것이 얼마나 드는지는 **재지 않았다.** 그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **부적용인 창** — ③ 브랜드 태그. 「안 쟀다」가 아니라 「**이 주제에는 그 칸이 없다**」이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 11번 주제에서 **실제로 한 번 바뀐 전례**가 있다.
- ★★ **캐럿 열** — 파서가 바뀌면 움직인다.
- **`??`/`?.`/논리 할당의 규칙 자체는 다시 돌릴 필요가 없다** — ES2020·ES2021 이후 바뀐 적이 없다.
