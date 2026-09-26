# go/syntax/42 — `fmt`: 포맷 동사·`Stringer`·`Errorf` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 격자의 출력 글자와 불린 횟수 · `18 / 78` · `vet` 의 문구와 `exit` · `exit=2` · `%!…` 표기.
> **흔들리는 칸** — `v03` 의 주소(`0x…`·십진) · 스택 넘침 리포트의 `sp=` 주소. **머신에 달린 칸** — 리포트의 줄 수·고루틴 수.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `{1 a}` · `{X:1 Name:a}` · `main.P{X:1, Name:"a"}` · `main.P` — 필드 안의 포인터는 **주소**, 맵은 **키 순서** · `%s` 는 `{%!s(int=1) a}` · `vet exit=0`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog > rows.txt; rc=$?; awk -F"\t" "/^v[0-9]/ && NF!=4{bad=1} END{exit bad}" rows.txt || echo "칸 수 어긋남"; cat rows.txt; echo "prog exit=$rc" =====
vet exit=0
칸 수 어긋남
v01 P{1,a}	%v	{1 a}	0
v01 P{1,a}	%+v	{X:1 Name:a}	0
v01 P{1,a}	%#v	main.P{X:1, Name:"a"}	0
v01 P{1,a}	%T	main.P	0
v01 P{1,a}	%s	{%!s(int=1) a}	0
v01 P{1,a}	%d	{1 %!d(string=a)}	0
v02 &P{1,a}	%v	&{1 a}	0
v02 &P{1,a}	%+v	&{X:1 Name:a}	0
v02 &P{1,a}	%#v	&main.P{X:1, Name:"a"}	0
v02 &P{1,a}	%T	*main.P	0
v02 &P{1,a}	%s	&{%!s(int=1) a}	0
v02 &P{1,a}	%d	&{1 %!d(string=a)}	0
v03 Outer	%v	{{1 a} 0x8ea900c8060}	0
v03 Outer	%+v	{In:{X:1 Name:a} Ptr:0x8ea900c8060}	0
v03 Outer	%#v	main.Outer{In:main.P{X:1, Name:"a"}, Ptr:(*main.P)(0x8ea900c8060)}	0
v03 Outer	%T	main.Outer	0
v03 Outer	%s	{{%!s(int=1) a} %!s(*main.P=&{2 b})}	0
v03 Outer	%d	{{1 %!d(string=a)} 9803532107872}	0
v04 (*P)(nil)	%v	<nil>	0
v04 (*P)(nil)	%+v	<nil>	0
v04 (*P)(nil)	%#v	(*main.P)(nil)	0
v04 (*P)(nil)	%T	*main.P	0
v04 (*P)(nil)	%s	%!s(*main.P=<nil>)	0
v04 (*P)(nil)	%d	0	0
v05 map	%v	map[a:1 b:2 c:3]	0
v05 map	%+v	map[a:1 b:2 c:3]	0
v05 map	%#v	map[string]int{"a":1, "b":2, "c":3}	0
v05 map	%T	map[string]int	0
v05 map	%s	map[a:%!s(int=1) b:%!s(int=2) c:%!s(int=3)]	0
v05 map	%d	map[%!d(string=a):1 %!d(string=b):2 %!d(string=c):3]	0
v06 []int	%v	[1 2]	0
v06 []int	%+v	[1 2]	0
v06 []int	%#v	[]int{1, 2}	0
v06 []int	%T	[]int	0
v06 []int	%s	[%!s(int=1) %!s(int=2)]	0
v06 []int	%d	[1 2]	0
v07 E	%v	E: boom	1
v07 E	%+v	E: boom	1
v07 E	%#v	main.E{Msg:"boom"}	0
v07 E	%T	main.E	0
v07 E	%s	E: boom	1
v07 E	%d	{%!d(string=boom)}	0
v08 V{7}	%v	V<7>	1
v08 V{7}	%+v	V<7>	1
v08 V{7}	%#v	main.V{N:7}	0
v08 V{7}	%T	main.V	0
v08 V{7}	%s	V<7>	1
v08 V{7}	%d	{7}	0
v09 &V{7}	%v	V<7>	1
v09 &V{7}	%+v	V<7>	1
v09 &V{7}	%#v	&main.V{N:7}	0
v09 &V{7}	%T	*main.V	0
v09 &V{7}	%s	V<7>	1
v09 &V{7}	%d	&{7}	0
v10 PR{7}	%v	{7}	0
v10 PR{7}	%+v	{N:7}	0
v10 PR{7}	%#v	main.PR{N:7}	0
v10 PR{7}	%T	main.PR	0
v10 PR{7}	%s	{%!s(int=7)}	0
v10 PR{7}	%d	{7}	0
v11 &PR{7}	%v	PR<7>	1
v11 &PR{7}	%+v	PR<7>	1
v11 &PR{7}	%#v	&main.PR{N:7}	0
v11 &PR{7}	%T	*main.PR	0
v11 &PR{7}	%s	PR<7>	1
v11 &PR{7}	%d	&{7}	0
v12 Emb	%v	V<7>	1
v12 Emb	%+v	V<7>	1
v12 Emb	%#v	main.Emb{V:main.V{N:7}, Extra:9}	0
v12 Emb	%T	main.Emb	0
v12 Emb	%s	V<7>	1
v12 Emb	%d	{{7} 9}	0
v13 Hold	%v	{V<1> {2}}	1
v13 Hold	%+v	{Pub:V<1> priv:{N:2}}	1
v13 Hold	%#v	main.Hold{Pub:main.V{N:1}, priv:main.V{N:2}}	0
v13 Hold	%T	main.Hold	0
v13 Hold	%s	{V<1> {%!s(int=2)}}	1
v13 Hold	%d	{{1} {2}}	0
── 칸마다 String()·Error() 가 불린 횟수 ──
v01 P{1,a}     %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v02 &P{1,a}    %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v03 Outer      %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v04 (*P)(nil)  %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v05 map        %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v06 []int      %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v07 E          %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
v08 V{7}       %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
v09 &V{7}      %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
v10 PR{7}      %v=0 %+v=0 %#v=0 %T=0 %s=0 %d=0
v11 &PR{7}     %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
v12 Emb        %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
v13 Hold       %v=1 %+v=1 %#v=0 %T=0 %s=1 %d=0
String()·Error() 가 불린 칸 18 / 78
prog exit=0
(exit 0)
```

**왜 그런가**

- ★★★ 동사는 **필드마다 재귀로** 적용된다(`go doc fmt` — 「the format applies to the elements of each operand, recursively」). 그래서 `%s` 는 `int` 필드에서, `%d` 는 `string` 필드에서 `%!` 가 난다.
- ★★ 포인터는 **겉 한 겹만** 따라간다 — `v02` 는 `&{1 a}`, `v03` 의 `Ptr` 필드는 주소다.
- ★★ `vet exit=0` — 동사를 **변수로** 넘겨서 `vet` 이 못 읽었다(8번).

### 2. `%v`·`%+v`·`%s` 셋에서만 — `v10 PR{7}` 은 한 칸도 안 불린다 · `Emb` 는 `V<7>`(`Extra` 안 보임) · `Hold` 는 `{V<1> {2}}` · `18 / 78`

**출력**

- 1번과 같은 블록이다 — 끝의 「칸마다 … 불린 횟수」 행렬과 마지막 줄을 본다.

**왜 그런가**

- ★★★ 규칙 4·5 는 「**문자열 동사(`%s %q %x %X`) 또는 `#` 없는 `%v`**」에서만 선다 — `%#v`·`%T`·`%d` 는 안 부른다. `%+v` 는 `%v` 의 플래그라 부른다.
- ★★★ `v10` 은 **포인터 리시버**라 값의 메서드 집합에 `String` 이 없다(3번). `v13` 은 **비공개 필드**라 안 불렸다(4번). `v12` 는 **승격된 `String()`** 이 바깥을 통째로 대신 찍었다.
- ★★ 18 = 불리는 값 여섯 × 동사 셋.

### 3. `Stringer` 인지를 **넘긴 값의 메서드 집합**으로 묻기 때문 — 에러도 경고도 없다

- ★★★ `(*PR).String` 은 `*PR` 의 메서드 집합에만 있다. `PR{7}` 을 `any` 에 담으면 동적 타입이 `PR` 이고 **`Stringer` 가 아니다** → 기본 꼴 `{7}`. `&PR{7}` 은 `*PR` 이라 `PR<7>`.
- ★★ 컴파일러도 `vet` 도 말하지 않는다 — **출력이 그럴듯해서** 눈으로도 잘 안 잡힌다.

### 4. `fmt` 는 비공개 필드에 메서드를 부를 수 없다 — `encoding/json` 이 비공개 필드를 **조용히 건너뛴 것**과 같은 뿌리(`reflect` 가 패키지 밖에서 그 값을 인터페이스로 못 꺼낸다)

- ★★★ `go doc fmt` — 「**fmt cannot and therefore does not invoke formatting methods such as Error or String on unexported fields**」. 그래서 `priv` 는 `{2}` 로(필드를 숫자로) 찍혔다.
- ★ 40번에서 `json.Marshal` 이 `email` 을 빼고도 `err` 가 `<nil>` 이었던 것처럼, 여기서도 **아무 표시가 없다.**

### 5. `vet exit=1`(`causes recursive (ex.T).String method call`) · 실행은 `exit=2` · stdout 은 `시작` 한 줄 · `recover:` 는 **안 찍힌다**

**출력**

```text
===== 소스: t42rec.go =====
package main

import "fmt"

type T struct{ N int }

// String 이 자기 자신을 %v 로 찍는다.
func (t T) String() string { return fmt.Sprintf("T(%v)", t) }

func main() {
	fmt.Println("시작")
	fmt.Println(T{1})
	fmt.Println("끝")
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog >out.txt 2>err.txt; echo "prog exit=$?"; echo "stdout: $(tr "\n" "|" < out.txt)"; echo "stderr 줄 수 $(wc -l < err.txt) · goroutine 머리줄 $(grep -c "^goroutine " err.txt) · main.T.String 프레임 $(grep -c "^main.T.String" err.txt)"; echo "── stderr 첫 세 줄 ──"; sed -n 1,3p err.txt; echo "── 생략 표시 ──"; grep "frames elided" err.txt; echo "── 위에서부터 main·fmt 프레임 이름 열 넷(인자 뗌) ──"; grep -m14 -E "^(main|fmt)\\." err.txt | sed -E "s/\\([^()]*\\)\$//" =====
t42rec.go:8:52: fmt.Sprintf format %v with arg t causes recursive (ex.T).String method call
vet exit=1
prog exit=2
stdout: 시작|
stderr 줄 수 566 · goroutine 머리줄 30 · main.T.String 프레임 15
── stderr 첫 세 줄 ──
runtime: goroutine stack exceeds 1000000000-byte limit
runtime: sp=0x1f4b6e8e0330 stack=[0x1f4b6e8e0000, 0x1f4b8e8e0000]
fatal error: stack overflow
── 생략 표시 ──
...3050303 frames elided...
── 위에서부터 main·fmt 프레임 이름 열 넷(인자 뗌) ──
fmt.(*buffer).writeString
fmt.(*pp).doPrintf
fmt.Sprintf
main.T.String
main.(*T).String
fmt.(*pp).handleMethods
fmt.(*pp).printArg
fmt.(*pp).doPrintf
fmt.Sprintf
main.T.String
main.(*T).String
fmt.(*pp).handleMethods
fmt.(*pp).printArg
fmt.(*pp).doPrintf
(exit 0)
```

```text
===== 명령: go build -trimpath -o prog . && ./prog >out.txt 2>err.txt; echo "prog exit=$?"; echo "stdout 줄 수 $(wc -l < out.txt)"; sed -n 3p err.txt =====
prog exit=2
stdout 줄 수 0
fatal error: stack overflow
(exit 0)
```

**왜 그런가**

- ★★★ `t` 는 `Stringer` 라 `%v` 가 `t.String()` 을 부르고, 그 안에서 또 `%v` 로 `t` 를 찍는다 — 프레임 이름 열넷이 **`main.T.String` → `main.(*T).String` → `fmt.(*pp).handleMethods` → … → `fmt.Sprintf` → `main.T.String`** 으로 돈다.
- ★★★ **컴파일러는 안 막는다** — `vet` 만 잡는다. 1 GB 스택을 다 쓰고 **`fatal error: stack overflow`**.
- ★★ `fatal error` 는 **`recover` 가 못 받고 `defer` 도 안 돈다** — `stdout 줄 수 0`.

### 6. `T{1}` · `Q{2}` · `vet exit=0` — `*q` 는 값 `Q` 이고 값의 메서드 집합에 `String` 이 없어서

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
T{1}
Q{2}
(exit 0)
```

- ★★★ `type raw T` — 필드는 같고 **메서드가 없는** 새 타입이라 `%v` 가 필드를 찍는다(`go doc fmt` 의 「convert the value before recurring」).
- ★★ `(*Q).String` 안의 `*q` 는 **값 `Q`** — 3번과 같은 규칙으로 `String()` 이 **안 불린다.** 그래서 재귀가 없다. ★ 리시버 종류에 기대는 처방이다.

### 7. `vet` 은 `6 / 6` · 실행은 여섯 줄이지만 `%!(EXTRA int=2)` 가 **`b4` 줄 머리**에 붙는다 · 끝은 `true`

**출력**

```text
===== 소스: t42bad.go =====
package main

import (
	"errors"
	"fmt"
)

func main() {
	fmt.Printf("b1 %d\n", "hi")
	fmt.Printf("b2 %v %v\n", 1)
	fmt.Printf("b3 %v\n", 1, 2)
	fmt.Printf("b4 %z\n", 1)
	fmt.Printf("b5 %w\n", errors.New("x"))
	err := fmt.Errorf("b6 감쌈: %w", "문자열")
	fmt.Println(err, errors.Unwrap(err) == nil)
}
===== 명령: go vet . 2>vet.txt; echo "vet exit=$?"; cat vet.txt; echo "vet 이 짚은 줄 $(grep -c "t42bad.go:" vet.txt) / 6"; go build -trimpath -o prog . && ./prog =====
vet exit=1
t42bad.go:9:17: fmt.Printf format %d has arg "hi" of wrong type string
t42bad.go:10:20: fmt.Printf format %v reads arg #2, but call has 1 arg
t42bad.go:11:2: fmt.Printf call needs 1 arg but has 2 args
t42bad.go:12:17: fmt.Printf format %z has unknown verb z
t42bad.go:13:17: fmt.Printf does not support error-wrapping directive %w
t42bad.go:14:32: fmt.Errorf format %w has arg "문자열" of wrong type string
vet 이 짚은 줄 6 / 6
b1 %!d(string=hi)
b2 1 %!v(MISSING)
b3 1
%!(EXTRA int=2)b4 %!z(int=1)
b5 %!w(*errors.errorString=&{x})
b6 감쌈: %!w(string=문자열) true
(exit 0)
```

**왜 그런가**

- ★★★ 런타임은 **멈추지 않고 글자로 적는다**(`exit 0`) — `%!d(string=hi)` · `%!v(MISSING)` · `%!z(int=1)`.
- ★★★ 남는 인자는 **서식 문자열이 끝난 뒤** — 즉 `\n` 뒤에 붙는다. 그래서 `b3 1` 다음 줄 머리가 `%!(EXTRA int=2)` 이고 **`b4` 가 거기 이어진다.**
- ★★ `Printf` 의 `%w` 는 뜻이 없다(`%!w(…)`). `Errorf` 에 `error` 가 아닌 것을 `%w` 로 넣으면 **감싸지지 않아** `errors.Unwrap(err) == nil` 이 `true`.

### 8. 서식 문자열이 **상수가 아니라 변수**였기 때문 — `printf` 검사는 **상수 서식 문자열과 인자**를 맞춘다

- ★★★ 격자는 `fmt.Sprintf(verb, v.arg)` 로 **동사를 변수**에서 가져왔다. `vet` 은 그 값을 **실행 전에 알 수 없다.** 같은 `%s`/`%d` 실수가 7번에서는 전부 잡히고 1번에서는 **0 줄**이다.
- ★ 그래서 서식을 조립하는 코드는 **`vet` 대신 테스트로** 확인해야 한다.

### 9. `*fmt.wrapErrors` · `errors.Unwrap(multi)` 은 `<nil>` — `%w` 둘은 **`Unwrap() []error`** 가 되고, `b6` 은 **아무것도 안 감쌌다**

- ★★ 24번 (6)절의 출력 — `%T` 가 **`*fmt.wrapErrors`**, `errors.Unwrap(multi)` 이 **`<nil>`**(`Unwrap() error` 가 없고 `Unwrap() []error` 만 있다), `errors.Is` 는 둘 다 찾는다.
- ★★★ `b6` 은 `%w` 에 **`string`** 을 넣어 감쌀 것이 없었다 — `Unwrap` 이 `nil` 인 까닭이 **다르다**(24번은 「사슬이 아니라 트리」, 여기는 「감싼 것이 없음」).

### 10. `String()` 을 **부르고**, 그 안에서 `nil` 역참조로 터지면 **패닉을 삼켜 `<nil>`** 을 찍는다

- ★★★ 21번이 `fmt/print.go` 의 `catchPanic` 을 떴다 — `recover()` 아래에서 「**If it's a nil pointer, just say "<nil>"**」. 그래서 `<nil>` 이 찍힌 로그는 **「값이 없었다」가 아니라 「`String()`/`Error()` 가 터졌다」** 일 수 있다.
- ★ 1번의 `v04` 는 **`String()` 이 없는** 타입이라 그 길을 안 탄다 — 같은 `<nil>` 이 **다른 이유**로 나온다.

### 11. 이 판에서는 **구현**(`internal/fmtsort`) — `fmt/doc.go` 에 `sort` 가 0 줄 · 09번은 **1.12 릴리스 노트를 근거로 「계약」** 이라 적었다

**출력**

```text
===== 명령: grep -n -i "sort" "$(go env GOROOT)/src/fmt/doc.go"; echo "doc.go 의 sort 줄 수: $(grep -c -i "sort" "$(go env GOROOT)/src/fmt/doc.go")"; grep -n "fmtsort" "$(go env GOROOT)/src/fmt/print.go"; sed -n "7,8p" "$(go env GOROOT)/src/internal/fmtsort/sort.go" =====
doc.go 의 sort 줄 수: 0
8:	"internal/fmtsort"
804:		sorted := fmtsort.Sort(f)
// It is not guaranteed to be efficient and works only for types
// that are valid map keys.
(exit 0)
```

- ★★ 명세에는 없다(`fmt` 는 라이브러리다). 패키지 문서(`go doc fmt`)에도 이 판에서는 **그 문장이 없다.** 정렬은 `print.go` 가 부르는 `internal/fmtsort` 가 한다.
- ★ 이 문서는 릴리스 노트를 **열지 않았다** — 09번의 「계약」을 뒤집지 않고 **「패키지 문서에서는 못 찾았다」** 만 적는다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 동사 격자 (`t42grid`) | 값 13 × 동사 6 · `calls` 계수기 · 탭 3개 검사 | 캡처마다 | **`18 / 78`** · 주소 칸만 흔들림 |
| ★★★ 재귀 (`t42rec`·`t42recov`) | `vet` · stdout/stderr 분리 · 줄 수만 셈 | 캡처마다 | `vet exit=1` · `exit=2` · `recover` 안 옴 |
| ★★ 잘못된 동사 (`t42bad`) | `vet` 짚은 줄 셈 · 실행 | 캡처마다 | **`6 / 6`** · `EXTRA` 줄 넘김 |
| ★ 고치는 형태 (`t42fix`) · 맵 정렬 출처 (`t42sort`) | 실행 · 소스 `grep` | 캡처마다 | `T{1}`·`Q{2}` · `doc.go` 에 `sort` 0 줄 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `String()` 을 부르는 동사·비공개 필드 규칙 | **`fmt` 문서의 계약** |
| 맵 키 정렬 | **구현**(`internal/fmtsort`) — 이 판 패키지 문서에 문장 없음 |
| 스택 한도·`fatal error` 리포트 모양 | **런타임 구현** · 리포트 줄 수는 CPU 수를 탄다 |
| `vet` 이 잡는 범위 | **이 판 `vet` 의 `printf` 분석기** — 상수 서식 문자열만 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(`--rule` 하나 — `v03` 의 `%d` 십진 주소: `'(%!d\(string\x3da\)\} )[0-9]{6,}=\1<십진주소>'` · 패턴 안의 `=` 를 `\x3d` 로 쓴 것은 도구가 **첫 `=`** 에서 패턴과 대체를 가르기 때문이다).
