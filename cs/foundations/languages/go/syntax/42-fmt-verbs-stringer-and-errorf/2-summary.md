# go/syntax/42 — `fmt`: 포맷 동사·`Stringer`·`Errorf` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`fmt`](https://pkg.go.dev/fmt) 패키지 문서(`go doc fmt` · `go doc fmt.Errorf`) · 툴체인 소스 `src/fmt/doc.go`·`print.go`·`internal/fmtsort/sort.go`. 전부 **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — 이 문서가 쓰는 동사·`Stringer`·`%!` 표기는 이 판(1.27.1)에서 잰 것이다. `%w` 는 1.13, `%w` 여러 개는 1.20 — [24번 주제](../24-error-wrapping-and-errors-is-as-join/) 머리말이 그 판 표기의 정본이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**동사 격자** — 값 13 가지 × 동사 6 개를 `Sprintf` 로 찍고, 칸마다 **`String()`·`Error()` 가 몇 번 불렸나**를 세는 로그」.
마지막 줄 「**String()·Error() 가 불린 칸 18 / 78**」((1)절). ★★★ **`String()` 을 가졌는데도 안 불린 칸이 세 종류** 있다 — 포인터 리시버를 값으로 넘김 · 비공개 필드 · `%#v`/`%d`((2)절).
★★ 짝이 되는 창은 「**`go vet` 의 `printf` 검사**」 — 재귀(`String` 안에서 자기 자신을 `%v`)와 잘못된 동사 **여섯 줄을 전부 잡는데**, 격자처럼 **동사가 변수면 한 줄도 못 본다**((3)·(5)절).

★★★ **이 주제의 경계** — `%w` 가 **무엇을 감싸고 `errors.Is`/`As` 가 어떻게 푸나**는 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)가 정본이다(`%w` 여러 개가 `Unwrap() []error` 가 되는 것까지 그 편 (6)절이 쟀다). 여기는 **`%w` 를 잘못 쓰면 무엇이 찍히나** 한 칸만 본다((5)절).
`nil` 포인터의 `String()` 이 터지면 `fmt` 가 **삼키고 `<nil>` 을 찍는 것**은 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)가 `catchPanic` 소스로 보였다 — 여기서는 되풀이하지 않는다.
**임베딩이 `String()` 을 승격하는 것**은 [18번 주제](../18-embedding-and-field-method-promotion/)가 「정본은 42번」이라며 **안 던졌다** — 여기서 던진다((2)절).
포인터 리시버 메서드가 **값의 메서드 집합에 없는 것**은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/)가 정본이다 — 여기는 그것이 **`fmt` 에서 어떻게 보이나**다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **메서드 집합**(포인터 리시버 메서드는 `*T` 에만) — 그것 말고 `fmt` 의 동작은 **명세에 없다** |
| **표준 라이브러리 계약** | `go doc fmt` 가 적은 것 | ★★★ **규칙 1\~5의 순서**(`Formatter` → `%#v` 면 `GoStringer` → 문자열 동사·`%v` 면 `Error` → `String`) · **비공개 필드에는 메서드를 안 부른다** · `%!verb(type=value)` 표기 |
| **구현** | 이 판의 소스가 한 것 | ★★ **맵을 키로 정렬해 찍는다** — 그 일은 `internal/fmtsort` 가 하고, **이 판의 `doc.go` 에는 `sort` 라는 낱말이 0 줄**이다((6)절) · 포인터 필드는 **주소**가 찍힌다 |
| **도구(`vet`)** | `printf` 분석기 | ★★ **서식 문자열이 상수일 때만** 본다 |

★★★ **선을 긋는다** — 「`String()` 이 있으면 부른다」는 **`fmt` 문서의 계약**이다. **언제 안 부르나**(포인터 리시버·비공개 필드·`%#v`)도 **같은 문서가 적은 계약**이다 — 격자는 그 문장들을 칸으로 센 것이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go doc fmt | sed -n "171,172p;180,192p;202,217p" =====
Except when printed using the verbs %T and %p, special formatting considerations
apply for operands that implement certain interfaces. In order of application:
3. If the %v verb is used with the # flag (%#v) and the operand implements the
GoStringer interface, that will be invoked.

If the format (which is implicitly %v for Println etc.) is valid for a string
(%s %q %x %X), or is %v but not %#v, the following two rules apply:

4. If an operand implements the error interface, the Error method will be
invoked to convert the object to a string, which will then be formatted as
required by the verb (if any).

5. If an operand implements method String() string, that method will be invoked
to convert the object to a string, which will then be formatted as required by
the verb (if any).
To avoid recursion in cases such as

    type X string
    func (x X) String() string { return Sprintf("<%s>", x) }

convert the value before recurring:

    func (x X) String() string { return Sprintf("<%s>", string(x)) }

Infinite recursion can also be triggered by self-referential data structures,
such as a slice that contains itself as an element, if that type has a String
method. Such pathologies are rare, however, and the package does not protect
against them.

When printing a struct, fmt cannot and therefore does not invoke formatting
methods such as Error or String on unexported fields.
(exit 0)
```

- ★★★ **규칙 4·5 는 「문자열 동사(`%s %q %x %X`) 또는 `#` 없는 `%v`」에서만** — 그래서 **`%d`·`%T`·`%#v` 에서는 `String()` 이 안 불린다**((1)절에서 칸으로 센다).
- ★★★ 마지막 문단 — 「**fmt cannot and therefore does not invoke formatting methods such as Error or String on unexported fields**」.
- ★★ 재귀를 피하는 처방도 문서에 있다 — 「**convert the value before recurring**」((4)절).

```text
===== 명령: go doc fmt | sed -n "255,260p" =====
    Wrong type or unknown verb: %!verb(type=value)
    	Printf("%d", "hi"):        %!d(string=hi)
    Too many arguments: %!(EXTRA type=value)
    	Printf("hi", "guys"):      hi%!(EXTRA string=guys)
    Too few arguments: %!verb(MISSING)
    	Printf("hi%d"):            hi%!d(MISSING)
(exit 0)
```

```text
===== 명령: go doc fmt.Errorf | sed -n "7,13p" =====
    If the format specifier includes a %w verb with an error operand,
    the returned error will implement an Unwrap method returning the operand.
    If there is more than one %w verb, the returned error will implement an
    Unwrap method returning a []error containing all the %w operands in the
    order they appear in the arguments. It is invalid to supply the %w verb
    with an operand that does not implement the error interface. The %w verb is
    otherwise a synonym for %v.
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 출력 글자 · 불린 횟수 · `18 / 78`** | 값과 동사가 같으면 같다 — **주소 칸만 빼고** |
| **흔들린다** | ★★ **`v03 Outer` 의 포인터 필드 주소** — `%v`·`%+v`·`%#v` 의 `0x…` 와 **`%d` 의 십진수** | 힙 주소다. `0x…` 는 기본 정규화 규칙이, **십진 주소는 `--rule` 하나**가 지운다 |
| **흔들린다** | 스택 넘침 리포트의 `sp=`·`stack=[…]` 주소 | 기본 규칙(주소) |
| **머신에 달린다** | ★ 리포트의 **`stderr 줄 수` · `goroutine 머리줄` 수** | 다른 고루틴(GC 일꾼)의 수가 **CPU 수**를 탄다 — 이 머신에서 재대조 두 판은 같았다. **근거로 쓰지 않는다** |
| 안 흔들린다 | `fatal error: stack overflow` · `1000000000-byte limit` · `exit=2` · `vet` 의 문구와 `exit` | |

## 한눈에 — 쉽게 말하면

**`fmt` 는 「통역사」, `String()` 은 값이 들고 다니는 「명함」이다.** 통역사는 소개할 때(`%v`·`%s`) **명함이 있으면 명함을 읽는다.**
그런데 명함을 **안 읽는 때가 셋** 있다 — ① **서류 전체를 원본 그대로**(`%#v`) 달라고 할 때 ② **숫자를 달라고**(`%d`) 할 때 ③ 명함이 **안주머니**(비공개 필드)에 있을 때.
그리고 명함이 **본인이 아니라 대리인(포인터)** 에게만 있으면, **본인(값)** 을 데려왔을 때 명함이 **없다**.
**명함에 「제 명함을 보세요」라고 적어 두면**(`String()` 안에서 자기 자신을 `%v`) 통역사는 **영원히 명함을 넘긴다** — 스택 넘침.

| 비유 | 실체 |
|---|---|
| 명함을 읽는다 | ★★★ **`%v`·`%+v`·`%s` 에서 `String()`/`Error()` 호출** — 18 칸((1)절) |
| 원본 서류를 달라 | ★★ **`%#v`** — 명함 대신 **Go 문법 꼴**(`main.V{N:7}`) |
| 숫자를 달라 | ★★ **`%d`** — 명함을 안 읽고 **필드를 숫자로**(`{7}`) |
| 안주머니의 명함 | ★★★ **비공개 필드 `priv V`** — `{V<1> {2}}` 에서 둘째가 명함을 안 읽혔다((2)절) |
| 대리인에게만 있는 명함 | ★★★ **포인터 리시버 `(*PR).String` 을 값 `PR{7}` 로** — `{7}`((2)절) |
| 윗사람 명함을 대신 내민다 | ★★ **임베딩 `Emb{V; Extra}`** — `V<7>` 만 찍히고 **`Extra` 가 사라진다**((2)절) |
| 「제 명함을 보세요」 | ★★★ **`Sprintf("%v", t)` 를 `String()` 안에서** — `fatal error: stack overflow`((3)절) |

```text
   ★★★ fmt 가 인자 하나를 찍을 때 고르는 길 (go doc fmt 규칙 1~5 · 이 판)

   동사가 %T · %p  ─────────────────────────────→ 메서드를 안 본다
   Formatter 인가? ──예──→ Format 을 부른다
   %#v 인가?  ──예──→ GoStringer 면 GoString, 아니면 Go 문법 꼴(main.V{N:7})
   %v · %s · %q · %x · %X 인가?
        ├─ error 인가?    ──예──→ Error()
        └─ Stringer 인가? ──예──→ String()
   그 밖(%d 등)      ─────────────────────────────→ 필드를 그 동사로 하나씩 ({7})

   ★ 「Stringer 인가」는 그 값의 **동적 타입의 메서드 집합**으로 묻는다
     PR{7} 의 메서드 집합에는 (*PR).String 이 없다 → 안 부른다
   ★ 구조체의 필드로 내려갈 때 **비공개 필드는 메서드를 안 부른다**
```

> **`Stringer`** — `String() string` 하나짜리 `fmt` 의 인터페이스. `fmt` 가 **값을 글자로 바꿀 때** 먼저 찾는다.

> **동사(verb)** — `%v`·`%d` 처럼 `%` 뒤의 글자. **값을 어떤 꼴로 찍을지** 고른다.

> **`%!d(string=hi)`** — 동사와 값의 타입이 안 맞을 때 `fmt` 가 **에러 대신 찍는 표기**. 패닉도 에러 반환도 없다.

## 이 주제가 답하려는 질문

1. **`%v`·`%+v`·`%#v`·`%T`·`%s`·`%d` 는 같은 값을 어떻게 다르게 찍나** — 그리고 **언제 `String()` 을 부르나.**
2. **`String()` 이 있는데도 안 불리는 자리와, 너무 불려서 끝나지 않는 자리는 어디인가.**
3. **동사를 잘못 쓰면 무엇이 찍히고, 누가 잡아 주나** — 런타임인가 `vet` 인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **동사 격자 — 값 13 × 동사 6 → 출력 · 불린 횟수** | 동사마다 **무엇을 찍고 메서드를 부르나** | ★ 본체 창 · 프로그램이 **탭 3개**를 세고 어긋나면 `exit 1` |
| ★★★ **`calls` 계수기** | `String()`/`Error()` 가 **실제로 불렸나** — 출력만 보고는 **안 가려지는 칸**을 가른다 | `V<7>` 이 찍혔으면 불린 것이지만, `{7}` 이 **안 불린 것인지 불렸는데 `{7}` 을 돌려준 것인지**는 계수기만 안다 |
| ★★ **`go vet`(printf)** | 정적으로 잡히나 | (3)·(5)절 |
| ★★ **스택 넘침 리포트의 수** | 재귀가 **어디서 끝났나** | (3)절 — 줄 수를 세고 첫 줄·생략 표시만 싣는다 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ `v10 PR{7}` 의 `%v` 는 `{7}` — **에러도 경고도 없고 모양도 그럴듯하다.** `String()` 을 **썼는데 안 불린 것**인데 출력만 보면 「원래 그렇게 찍히는 타입」과 구별이 안 된다. **기준이 「그 타입에 메서드가 있나」가 아니라 「넘긴 값의 메서드 집합에 있나」** 다 | (2)절 |
| **부적용 — 성능** | 이 문서는 `fmt` 의 속도를 **안 쟀고 주장하지 않는다** | — |
| **못 잰 것 — `Formatter`·`GoStringer`** | 규칙 2·3 의 인터페이스는 **구현해 보지 않았다** | 격자에 없다 |

### (1) ★★★ 동사 격자 — 값 13 × 동사 6

**언제 쓰나** — 로그·디버그 출력에서 **어느 동사가 무엇을 보여 줄지** 고를 때.

```text
===== 소스: t42grid.go =====
package main

import (
	"fmt"
	"os"
	"strings"
)

// calls 는 String()·Error() 가 불린 횟수다.
var calls int

type P struct {
	X    int
	Name string
}

type Outer struct {
	In  P
	Ptr *P
}

// V 는 값 리시버로 String 을 가진다.
type V struct{ N int }

func (v V) String() string { calls++; return fmt.Sprintf("V<%d>", v.N) }

// PR 은 포인터 리시버로 String 을 가진다.
type PR struct{ N int }

func (p *PR) String() string { calls++; return fmt.Sprintf("PR<%d>", p.N) }

// E 는 Error 를 가진다.
type E struct{ Msg string }

func (e E) Error() string { calls++; return "E: " + e.Msg }

// Emb 는 V 를 임베딩한다.
type Emb struct {
	V
	Extra int
}

// Hold 는 같은 타입의 필드를 공개·비공개로 하나씩 가진다.
type Hold struct {
	Pub  V
	priv V
}

func main() {
	vals := []struct {
		id  string
		arg any
	}{
		{"v01 P{1,a}", P{1, "a"}},
		{"v02 &P{1,a}", &P{1, "a"}},
		{"v03 Outer", Outer{P{1, "a"}, &P{2, "b"}}},
		{"v04 (*P)(nil)", (*P)(nil)},
		{"v05 map", map[string]int{"b": 2, "a": 1, "c": 3}},
		{"v06 []int", []int{1, 2}},
		{"v07 E", E{"boom"}},
		{"v08 V{7}", V{7}},
		{"v09 &V{7}", &V{7}},
		{"v10 PR{7}", PR{7}},
		{"v11 &PR{7}", &PR{7}},
		{"v12 Emb", Emb{V{7}, 9}},
		{"v13 Hold", Hold{V{1}, V{2}}},
	}
	verbs := []string{"%v", "%+v", "%#v", "%T", "%s", "%d"}
	hit, all := 0, 0
	matrix := []string{}
	for _, v := range vals {
		line := fmt.Sprintf("%-14s", v.id)
		for _, verb := range verbs {
			before := calls
			out := fmt.Sprintf(verb, v.arg)
			n := calls - before
			all++
			if n > 0 {
				hit++
			}
			row := strings.Join([]string{v.id, verb, out, fmt.Sprint(n)}, "\t")
			if strings.Count(row, "\t") != 3 {
				fmt.Fprintln(os.Stderr, "칸 수 어긋남:", row)
				os.Exit(1)
			}
			fmt.Println(row)
			line += fmt.Sprintf(" %s=%d", verb, n)
		}
		matrix = append(matrix, line)
	}
	fmt.Println("── 칸마다 String()·Error() 가 불린 횟수 ──")
	for _, l := range matrix {
		fmt.Println(l)
	}
	fmt.Printf("String()·Error() 가 불린 칸 %d / %d\n", hit, all)
}
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

그림 해설 (한 단계씩):

- ★★★ **보통 구조체(`v01`)** — `%v` `{1 a}` · `%+v` `{X:1 Name:a}`(필드 이름) · `%#v` `main.P{X:1, Name:"a"}`(**Go 문법** — 문자열에 따옴표, 타입 이름) · `%T` `main.P`.
  ★ **`%s` 는 `{%!s(int=1) a}`** — 동사가 **필드마다** 적용되어 `int` 필드에서 틀렸다. `%d` 는 거꾸로 **문자열 필드**에서 `%!d(string=a)`. 문서의 「**the format applies to the elements of each operand, recursively**」 그대로다.
- ★★ **포인터(`v02`)는 `&{1 a}`** — 겉 한 겹은 `&` 로 따라 들어간다. ★★★ **그런데 필드 안의 포인터(`v03 Ptr`)는 주소**(`0x…`)다 — 한 겹만 따라간다. `%s` 만 예외로 `%!s(*main.P=&{2 b})` 에서 **내용이 보인다.** `%d` 는 주소를 **십진수**로 찍었다(흔들리는 칸).
- ★★ **`nil` 포인터(`v04`)** — `%v` `<nil>` · `%#v` `(*main.P)(nil)` · **`%d` 는 `0`**.
- ★★ **맵(`v05`)은 키 순서** — `map[a:1 b:2 c:3]`(넣은 순서는 `b a c`). (6)절.
- ★★★ **`Stringer`·`error`(`v07`\~`v13`)** — 불린 칸은 **`%v`·`%+v`·`%s` 셋뿐**이고 **`%#v`·`%T`·`%d` 는 한 번도 안 불렸다.** `%+v` 도 `String()` 을 부른다(필드 이름이 안 나온다 — `V<7>`).
- ★★★ **마지막 줄 `18 / 78`** — 불린 18 칸 = 불리는 값 **여섯**(`v07`·`v08`·`v09`·`v11`·`v12`·`v13`) × 동사 **셋**. **`v10 PR{7}` 은 한 칸도 없다**((2)절).

```text
   ★★ 위 행렬에서 1 이 선 칸만 — 동사 셋 × 값 여섯 = 18

                 %v   %+v   %#v   %T   %s   %d
   v07 E          1    1     .     .    1    .      Error()
   v08 V{7}       1    1     .     .    1    .      값 리시버 · 값
   v09 &V{7}      1    1     .     .    1    .      값 리시버 · 포인터
   v10 PR{7}      .    .     .     .    .    .      ★ 포인터 리시버 · 값
   v11 &PR{7}     1    1     .     .    1    .      포인터 리시버 · 포인터
   v12 Emb        1    1     .     .    1    .      임베딩으로 승격된 V.String
   v13 Hold       1    1     .     .    1    .      ★ Pub 만 — priv 는 안 불렸다
```

비용 — 이 문서는 재지 않았다.

### (2) ★★★ `String()` 이 있는데 안 불리는 셋, 대신 불려서 필드를 가리는 하나

같은 격자의 네 줄을 떼어 본다(출력은 (1)절 블록 그대로다):

| 값 | `%v` 출력 | 불린 횟수 | 무엇이 일어났나 |
|---|---|---|---|
| `v10 PR{7}` | `{7}` | 0 | ★★★ **`String` 이 `*PR` 에만 있다** — 값 `PR{7}` 의 메서드 집합에 없어 `Stringer` 가 **아니다** |
| `v11 &PR{7}` | `PR<7>` | 1 | 포인터로 넘기면 불린다 |
| `v13 Hold` | `{V<1> {2}}` | 1 | ★★★ **`Pub` 만 불렸다** — 비공개 필드 `priv` 는 **같은 타입 `V` 인데** `{2}` |
| `v12 Emb` | `V<7>` | 1 | ★★ **승격된 `V.String` 이 `Emb` 전체를 대신 찍었다** — **`Extra:9` 가 안 보인다** |

- ★★★ **포인터 리시버** — [19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 규칙(**값의 메서드 집합에는 포인터 리시버 메서드가 없다**)이 `fmt` 에서는 **에러가 아니라 「조용히 기본 꼴」** 로 나타난다. `fmt.Println(pr)` 과 `fmt.Println(&pr)` 이 **다른 것을 찍는다.**
- ★★★ **비공개 필드** — 문서 문장 그대로다(머리말 `t42doc`). `fmt` 는 `reflect` 로 필드를 보는데 **비공개 필드의 값은 패키지 밖에서 인터페이스로 꺼낼 수 없다** — [40번 주제](../40-package-visibility-naming-and-internal/) (4)절에서 `encoding/json` 이 비공개 필드를 **조용히 건너뛴 것**과 같은 뿌리다.
- ★★ **임베딩** — [18번 주제](../18-embedding-and-field-method-promotion/)가 「무한 재귀의 씨앗이 되는 자리」라 적고 안 던진 곳이다. 여기서 본 것은 재귀가 아니라 **필드가 가려지는 것**이다 — `%+v` 도 `V<7>` 이고, **`%#v` 만** `main.Emb{V:main.V{N:7}, Extra:9}` 로 전부 보인다.

비용 — 없다.

### (3) ★★★ `String()` 안에서 자기 자신을 `%v` — 스택 넘침

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

그림 해설 (한 단계씩):

- ★★★ **`vet exit=1`** — `fmt.Sprintf format %v with arg t causes recursive (ex.T).String method call`. **빌드 전에 잡힌다.** 그런데 `go build` 는 `vet` 을 안 돌린다 — **그대로 빌드되고 돈다.**
- ★★★ **`prog exit=2`** · **`stdout: 시작|`** — 첫 줄만 찍히고 `끝` 은 **안 찍혔다.** `fatal error: stack overflow` · `goroutine stack exceeds 1000000000-byte limit`.
  ★★ **`fatal error` 는 `panic` 이 아니다** — `main` 에 `defer func(){ … recover() … }()` 를 걸어도 **그 `defer` 가 한 줄도 못 찍고** 죽는다:

```text
===== 소스: t42recov.go =====
package main

import "fmt"

type T struct{ N int }

// String 이 자기 자신을 %v 로 찍는다.
func (t T) String() string { return fmt.Sprintf("T(%v)", t) }

func main() {
	defer func() {
		fmt.Println("recover:", recover())
	}()
	fmt.Println(T{1})
}
===== 명령: go build -trimpath -o prog . && ./prog >out.txt 2>err.txt; echo "prog exit=$?"; echo "stdout 줄 수 $(wc -l < out.txt)"; sed -n 3p err.txt =====
prog exit=2
stdout 줄 수 0
fatal error: stack overflow
(exit 0)
```

  `stdout 줄 수 0` · `prog exit=2` — `recover:` 줄이 **안 나왔다.**
- ★★ **`...3050303 frames elided...`** — 트레이스백이 **가운데 300만 프레임을 생략**했다. `main.T.String` 프레임은 **15 개만** 찍혔다 — 리포트의 줄 수(566)는 **머신에 달린 칸**이라 근거로 안 쓴다.
- ★★ **왜 도나** — `Sprintf("T(%v)", t)` 의 `t` 는 `T` 이고 `T` 는 `Stringer` 다 → `fmt` 가 `t.String()` 을 부른다 → 그 안에서 또 `Sprintf("%v", t)` → ….

```text
   ★★ 재귀 한 바퀴 (리포트의 프레임 이름으로)

   main.T.String(...)          ex/t42rec.go:8
     fmt.Sprintf("T(%v)", t)
       fmt.(*pp).doPrintf
         fmt.(*pp).printArg
           fmt.(*pp).handleMethods     ← t 가 Stringer 인지 묻는다 → 예
             main.(*T).String          ← <autogenerated> 감싸개를 지나
               main.T.String(...)      ← 다시 처음으로
```

비용 — 1 GB 스택을 다 쓰고 죽는다.

### (4) ★★ 고치는 두 길 — 메서드 없는 타입으로 바꾸기 · 포인터 리시버 안의 값

```text
===== 소스: t42fix.go =====
package main

import "fmt"

type T struct{ N int }

// 메서드가 없는 새 타입으로 바꿔 찍는다.
func (t T) String() string {
	type raw T
	return fmt.Sprintf("T%v", raw(t))
}

type Q struct{ N int }

// 포인터 리시버 안에서 값(*q)을 찍는다.
func (q *Q) String() string { return fmt.Sprintf("Q%v", *q) }

func main() {
	fmt.Println(T{1})
	fmt.Println(&Q{2})
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
T{1}
Q{2}
(exit 0)
```

- ★★★ **`type raw T` → `raw(t)`** — `raw` 는 `T` 와 **필드가 같고 메서드가 없는** 새 타입이다. `%v` 가 `String()` 을 못 찾아 **필드를 찍는다** → `T{1}`. 문서 처방(「convert the value before recurring」)의 구조체 판이다.
- ★★ **포인터 리시버 `(*Q).String` 안에서 `*q`** — `*q` 는 **값 `Q`** 이고 값의 메서드 집합에는 `String` 이 없어 `{2}` 로 찍힌다 → `Q{2}`. (2)절의 「안 불리는 칸」을 **일부러 쓴** 것이다. ★ 이 처방은 **리시버 종류에 기댄다** — (3)절의 `T` 는 **값 리시버라서** `t` 를 넘기자 `String()` 이 다시 불렸다. 같은 규칙의 반대편이다(값 리시버로 바꾼 판은 **따로 던지지 않았다**).
- `vet exit=0` — 둘 다 조용하다.

비용 — 없다.

### (5) ★★★ 잘못된 동사 — 런타임은 조용히 적고, `vet` 은 여섯 줄을 다 짚는다

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

그림 해설 (한 단계씩):

- ★★★ **런타임은 한 번도 안 멈췄다**(`exit 0`) — 전부 **글자로** 적는다: `%!d(string=hi)` · `%!v(MISSING)` · `%!z(int=1)`.
- ★★★ **`b3` — `%!(EXTRA int=2)` 가 다음 줄 머리에 붙었다** — 남는 인자는 **서식 문자열이 다 끝난 뒤**(그러니까 `\n` **뒤**)에 덧붙는다. 그래서 `b4` 가 **그 줄에 이어 찍혔다.** 로그 한 줄이 **두 줄로 번지는** 자리다.
- ★★ **`b5` — `Printf` 의 `%w` 는 `%!w(*errors.errorString=&{x})`** — `%w` 는 **`Errorf` 에서만** 뜻이 있다. `vet` 문구 「**does not support error-wrapping directive %w**」.
- ★★★ **`b6` — `Errorf` 에 `error` 아닌 인자로 `%w`** — 메시지에 `%!w(string=문자열)` 이 박히고 **`errors.Unwrap(err) == nil` 이 `true`** — **감싼 것이 없다.** 문서 「**It is invalid to supply the %w verb with an operand that does not implement the error interface**」(머리말 `t42errorf`).
  ★ `%w` 를 여러 개 쓰면 `Unwrap() []error` 가 되는 것은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (6)절이 쟀다.
- ★★★ **`vet 이 짚은 줄 6 / 6`** — 여섯 줄 전부. ★★★ **그런데 (1)절 격자는 `vet exit=0`** 이었다 — 격자의 `%s`·`%d` 칸도 **같은 종류의 실수**인데, **동사를 변수(`verb`)로 넘겨서** `vet` 이 서식 문자열을 **읽을 수 없었다.** `vet` 은 **상수 서식 문자열만** 본다.

비용 — 없다.

### (6) ★★ 맵이 키 순서로 찍히는 것 — 문서인가 구현인가

```text
===== 명령: grep -n -i "sort" "$(go env GOROOT)/src/fmt/doc.go"; echo "doc.go 의 sort 줄 수: $(grep -c -i "sort" "$(go env GOROOT)/src/fmt/doc.go")"; grep -n "fmtsort" "$(go env GOROOT)/src/fmt/print.go"; sed -n "7,8p" "$(go env GOROOT)/src/internal/fmtsort/sort.go" =====
doc.go 의 sort 줄 수: 0
8:	"internal/fmtsort"
804:		sorted := fmtsort.Sort(f)
// It is not guaranteed to be efficient and works only for types
// that are valid map keys.
(exit 0)
```

- ★★★ **이 판의 `fmt/doc.go` 에 `sort` 는 0 줄** — 정렬은 `print.go` 가 **`internal/fmtsort`** 를 불러 한다. 그 패키지 주석은 「**a general stable ordering mechanism for maps, on behalf of the fmt and text/template packages**」(윗줄)이라 적는다.
- ★★ [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)는 이것을 「**표준 라이브러리의 계약 — 1.12 릴리스부터 문서화됨**」이라 적었다(릴리스 노트가 근거다). **이 판의 패키지 문서(`go doc fmt`)에는 그 문장이 없다** — 이 문서는 **릴리스 노트를 열지 않았으므로** 09편을 뒤집지 않고, **「패키지 문서에서는 못 찾았다」** 만 적는다.
- ★ 실용 결론은 같다 — **`fmt` 가 찍은 맵은 재현되고, `range` 는 재현되지 않는다**(09편).

비용 — 정렬 비용이 있다. **재지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t42fix.go
package main

import "fmt"

type T struct{ N int }

// 메서드가 없는 새 타입으로 바꿔 찍는다.
func (t T) String() string {
	type raw T
	return fmt.Sprintf("T%v", raw(t))
}

type Q struct{ N int }

// 포인터 리시버 안에서 값(*q)을 찍는다.
func (q *Q) String() string { return fmt.Sprintf("Q%v", *q) }

func main() {
	fmt.Println(T{1})
	fmt.Println(&Q{2})
}
```

규칙 불릿.

- ★★★ **`String()`·`Error()` 는 `%v`·`%+v`·`%s`(과 `%q %x %X`)에서만** 불린다. `%#v`·`%T`·`%d` 는 안 부른다.
- ★★★ **`Stringer` 인지는 넘긴 값의 메서드 집합**으로 정한다 — 포인터 리시버 `String` 은 **포인터로 넘겨야** 불린다.
- ★★★ **`String()` 안에서 자기 자신을 `%v`/`%s` 로 찍지 마라** — 메서드 없는 타입으로 바꾸거나(`type raw T`) 필드를 직접 찍는다.
- ★★ **비공개 필드의 `String()` 은 안 불린다** · 임베딩한 `String()` 은 **바깥 타입 전체를 대신 찍는다.**
- ★★ 틀린 동사·인자 수는 **`%!…` 글자**로 남는다 — **`go vet` 을 돌려라**(상수 서식 문자열만 본다).
- ★ `%w` 는 **`Errorf` 에서 `error` 인자에만.**

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 런타임 | `vet` | 어디서 |
|---|---|---|---|
| `func (t T) String() string { return Sprintf("%v", t) }` | ★★★ `fatal error: stack overflow` · `exit 2` | 잡는다 — `causes recursive … String method call` | (3)절 |
| `Printf("%d", "hi")` | `%!d(string=hi)` | 잡는다 | (5)절 |
| `Printf("%v\n", 1, 2)` | `%!(EXTRA int=2)` 가 **다음 줄**에 | 잡는다 | (5)절 |
| `Printf("%w", err)` | `%!w(…)` | 잡는다 | (5)절 |
| `Errorf("%w", "문자열")` | `%!w(string=…)` · **`Unwrap` 이 `nil`** | 잡는다 | (5)절 |
| 동사를 **변수**로 넘김 | 위와 같은 `%!` | ★★★ **못 본다** | (1)절 |
| 포인터 리시버 `String` 을 값으로 찍음 | ★★★ **조용히 기본 꼴** | 말 없음 | (2)절 |

## 어디서 틀리나

### 1. ★★★ 「`String()` 을 만들었으니 `Println` 이 쓴다」

- (2)절 — **포인터 리시버면 값으로 넘길 때 안 쓴다**(`{7}`). **비공개 필드도 안 쓴다**(`{2}`).

### 2. ★★★ 「`%+v` 면 필드 이름까지 다 보인다」

- (1)절 — **`Stringer` 면 `%+v` 도 `String()` 을 부른다**(`V<7>`). 전부 보려면 **`%#v`**.

### 3. ★★ 「`%v` 는 포인터를 따라가 내용을 보여 준다」

- (1)절 `v03` — **겉 한 겹만.** 필드 안의 포인터는 **주소**다.

### 4. ★★★ 「`String()` 안에서 `%v` 로 자신을 찍어도 컴파일러가 막는다」

- (3)절 — **컴파일러는 안 막는다.** `vet` 만 잡는다. 안 돌리면 **스택 넘침**이다.

### 5. ★★ 「틀린 동사는 패닉이나 에러를 낸다」

- (5)절 — **`exit 0`**. 글자로만 남는다. **`%!(EXTRA …)` 는 줄을 넘어간다.**

### 6. ★★ 「`vet` 이 `Printf` 실수를 다 잡는다」

- (1)·(5)절 — **상수 서식 문자열만.** 변수로 넘긴 동사는 `vet exit=0`.

### 7. ★ 「임베딩하면 바깥 구조체의 필드도 같이 찍힌다」

- (2)절 `v12` — **승격된 `String()` 이 전부 가린다**(`Extra` 가 안 보인다).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 포인터 리시버 메서드는 값의 메서드 집합에 없다 | **명세** | [19번 주제](../19-method-sets-value-vs-pointer-receiver/) · (2)절 |
| ★★★ `String()` 은 `%v %s %q %x %X` 에서만 · `%#v` 는 `GoStringer` | **표준 라이브러리 계약**(`go doc fmt`) | `t42doc` · (1)절 |
| ★★★ 비공개 필드엔 메서드를 안 부른다 | **표준 라이브러리 계약** | `t42doc` · (2)절 |
| `%!verb(type=value)` · `MISSING` · `EXTRA` | **표준 라이브러리 계약** | `t42docbad` · (5)절 |
| ★★ 맵을 키로 정렬 | **구현**(`internal/fmtsort`) — 이 판 패키지 문서에 문장 없음 · 09편은 릴리스 노트로 계약이라 적음 | (6)절 |
| 스택 한도 1 GB · `fatal error` | **런타임 구현** | (3)절 |
| 재귀·잘못된 동사를 잡는 것 | **도구(`vet` printf)** — 상수 서식 문자열만 | (3)·(5)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 사람이 읽는 로그 | `%v`(+ `String()`) | (1)절 |
| 디버깅 — **숨은 필드까지** | ★★★ **`%#v`** | `String()`·임베딩이 가리는 것을 연다((2)절) |
| 필드 이름만 붙여서 | `%+v` — ★ `Stringer` 가 아닐 때만 뜻이 있다 | (1)절 |
| 타입 확인 | `%T` | (1)절 |
| `String()` 구현 | **값 리시버** + 필드를 직접 찍거나 `type raw T` | (2)·(4)절 |
| 오류 감싸기 | `Errorf("…: %w", err)` — **`err` 가 `error` 일 때만** | (5)절 · [24번 주제](../24-error-wrapping-and-errors-is-as-join/) |
| 서식 문자열을 변수로 만들어야 할 때 | ★ `vet` 이 못 본다는 것을 알고 **테스트로** 확인 | (1)절 |

## 핵심 문장

- ★★★ **`String()`·`Error()` 는 `%v`·`%+v`·`%s` 에서만 불린다 — `18 / 78`.** `%#v`·`%T`·`%d` 는 안 부른다.
- ★★★ **포인터 리시버 `String()` 은 값으로 넘기면 안 불린다** — 에러 없이 `{7}`. 비공개 필드도 안 불린다.
- ★★★ **`String()` 안에서 자기 자신을 `%v` 로 찍으면 `fatal error: stack overflow`** — 컴파일러는 안 막고 `vet` 만 잡는다. `type raw T` 로 끊는다.
- ★★ **틀린 동사는 `%!d(string=hi)` 같은 글자로만 남는다** — `EXTRA` 는 줄을 넘어간다. `vet` 은 **상수 서식 문자열**만 본다.
- ★★ **`Errorf` 의 `%w` 에 `error` 가 아닌 것을 넣으면 감싸지지 않는다**(`Unwrap` 이 `nil`).
- ★ **맵은 키 순서로 찍힌다** — 이 판의 패키지 문서가 아니라 `internal/fmtsort` 가 한다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 42번)
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스·암묵 구현) — ★ 목록상 선행 · `Stringer` 도 **선언 없이 만족**한다
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) — (2)절의 규칙 정본 · [18번 주제](../18-embedding-and-field-method-promotion/)(임베딩) — 승격 정본
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 포인터의 `String()` 이 터지면 `<nil>`) · [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`%w`·`Is`/`As`·`%w` 여러 개) · [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵 순서)
- [Python 08번](../../../python/syntax/08-fstrings-and-format-spec/)(f-string·서식 명세) · [Python 30번](../../../python/syntax/30-repr-eq-hash-contracts/)(`__repr__` 계약 — Go 의 `%#v`·`String()` 과 자리가 같다) · Rust 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **48번**(`Display`/`Debug`)

## 용어 풀이

- **동사(verb)** — `%v`·`%d` 등. 값을 어떤 꼴로 찍을지.
- **`%v` / `%+v` / `%#v`** — 기본 꼴 / 필드 이름을 붙인 꼴 / Go 문법 꼴.
- **`Stringer`** — `String() string`. `fmt` 가 문자열 동사와 `%v` 에서 부른다.
- **`GoStringer`** — `GoString() string`. `%#v` 에서 부른다(이 문서는 구현해 보지 않았다).
- **메서드 집합** — 그 타입의 값으로 부를 수 있는 메서드들. `T` 에는 값 리시버만, `*T` 에는 둘 다.
- **`%!verb(type=value)`** — 동사와 값이 안 맞을 때의 표기. `MISSING`(인자 부족) · `EXTRA`(남음).
- **`printf` 분석기** — `go vet` 의 한 검사. 상수 서식 문자열과 인자를 맞춰 본다.
- **`fatal error`** — 런타임이 복구 불가로 죽는 것. `panic` 과 달리 **`recover` 가 받지 못하고 `defer` 도 안 돈다**((3)절 `t42recov`).

---

## 더 들어가면

- ★ **`Formatter`·`GoStringer`·폭·정밀도·플래그(`%6.2f`·`%-10s`·`%q`·`%x`)** — 이 문서는 격자에 넣지 않았다.
- ★ **자기 자신을 담는 슬라이스**(문서가 「the package does not protect against them」이라 적은 경우) — 안 던졌다.
- ★ **다른 `fatal error`**(동시 맵 쓰기 등)도 같은 성질인지 — 안 던졌다. 이 문서가 잰 것은 **스택 넘침 하나**다.
