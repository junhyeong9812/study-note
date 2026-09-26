# go/syntax/21 — `nil` 인터페이스와 `nil` 포인터를 담은 인터페이스 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Comparison operators · Interface types ·
> Type switches 절. 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했고,
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> `errors.Is` 의 근거는 `$(go env GOROOT)/src/errors/wrap.go` 를 직접 떠 왔다.\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 이 주제에는 **판 경계가 없다.** 인터페이스 값이 (타입, 값) 두 칸인 것은 **1.0부터 같다.**
> ★★★ 그리고 이것은 **명세가 못 박은 자리**다 — 비교 규칙이 「dynamic types」·「dynamic values」라고
> **두 칸을 직접 부른다.** gc 가 그렇게 구현한 것이 아니다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★ **본체는 셋째 창이다** — 「`x == nil` 과 `reflect.ValueOf(x).IsNil()` 을 같은 줄에 나란히 찍는 창」.
이 주제의 전부가 **그 둘의 답이 갈리는 칸** 하나다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)·표준 라이브러리** | 이 컴파일러·런타임·`fmt`·`errors` 가 그렇게 하는 것 | 패닉 문구 · `%v` 가 찍는 글자 · `errors` 의 소스 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ **「인터페이스 값은 두 칸이고 두 칸이 다 비어야 `nil` 이다」는 명세 보장**이다.
★★ 반면 **`%v` 가 `nil` 포인터를 `<nil>` 로 찍는 것은 `fmt` 의 계약**이고,
**`go vet` 이 이 함정을 안 보는 것은 도구의 사정**이다. 셋을 갈라 읽어라.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 블록의 `pc=0x…` 와 스택 프레임의 힙 주소 | 실행마다 다르다 |
| 안 흔들린다 | ★★★ `x == nil` 의 참거짓 · `%T` · `%v` · `IsValid` · `IsNil` | 타입 구조가 정한다 — **이 주제의 근거 칸 전부**가 여기다 |
| 안 흔들린다 | 패닉 **메시지 본문**과 `goroutine 1 [running]:` · `파일:줄` · 종료 코드 `2` | 런타임이 정한 문장이다 |
| 안 흔들린다 | 스택의 `+0x…` **프레임 오프셋** | `-trimpath` 로 같은 소스를 같은 판으로 빌드하면 고정이다(2판 대조) |
| 안 흔들린다 | `go vet` 의 **출력 줄 수**(0)와 종료 코드 | 도구가 이 검사를 안 들고 있다 |
| 안 흔들린다 | `errors/wrap.go` 의 **줄 번호와 본문** | 이 툴체인 판에 든 파일이다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 순회해 찍지 않는다 |

★ 정규화 규칙은 **주소 하나**만 썼다. 나머지 블록은 재실행에서 한 글자도 같았다.

## 한눈에 — 쉽게 말하면

**`nil` 인터페이스는 「아무것도 안 들었다」이고, `nil` 을 담은 인터페이스는 「빈 상자가 들었다」다.**
상자가 들어 있으면 **인터페이스는 비어 있지 않다.** `err != nil` 이 참이 되는 이유가 이것뿐이다.

| 비유 | 실체 |
|---|---|
| 택배 봉투에 「운송장」과 「내용물」이 따로 있다 | **인터페이스 값의 두 칸** — 동적 타입 · 동적 값 |
| 운송장도 없고 내용물도 없다 | `var e error` — `e == nil` 이 **참** |
| 운송장은 붙었는데 내용물이 없다 | `var e error = (*MyErr)(nil)` — `e == nil` 이 ★ **거짓** |
| 봉투 겉면에는 「내용물 없음」이라 찍힌다 | `%v` 가 `<nil>` 을 찍는다 — **로그만 보면 똑같다** |
| 「빈 봉투냐」를 물으면 창구가 「아니오」라 한다 | `err != nil` 이 참이라 에러 처리로 들어간다 |
| 운송장 붙이는 사람이 따로 있다 | ★★★ **함수의 반환 타입** — 구체 타입을 `error` 로 넓히는 그 자리 |
| 검사대가 이 봉투를 안 본다 | ★★ **`go vet` 이 침묵한다** — 탐침 8개 중 0개가 답했다 |

```text
   ★★★ 두 칸 — 이 주제의 전부

   ① nil 인터페이스                     ② nil 을 담은 인터페이스
      var e error                          var p *MyErr = nil
                                           var e error = p
   ┌──────────┬──────────┐              ┌──────────┬──────────┐
   │ 타입 칸  │ 값 칸    │              │ 타입 칸  │ 값 칸    │
   │  (비었음)│ (비었음) │              │ *MyErr   │ (비었음) │
   └──────────┴──────────┘              └──────────┴──────────┘

      e == nil      -> true                e == nil      -> ★ false
      %T            -> <nil>               %T            -> *main.MyErr
      %v            -> <nil>               %v            -> <nil>   ← 여기가 같다
      IsValid()     -> false               IsValid()     -> true
      IsNil()       -> (물을 수 없음)      IsNil()       -> ★ true

   ★ 로그에 남는 글자(%v)만 같고 나머지가 전부 다르다.
```

```text
   타입 칸을 채우는 것은 「대입」이다 — 그 한 줄을 찾아라

     func f() error {
         var p *MyErr          ← ① 여기서 p 의 정적 타입이 *MyErr 로 굳는다
         if bad { p = … }
         return p              ← ② 여기서 (타입=*MyErr, 값=nil) 로 담긴다
     }                            반환 타입이 error 라서 넓혀지는 것이다

     고치면 —

     func f() error {
         if bad { return &MyErr{…} }
         return nil            ← ★ 리터럴 nil 은 두 칸이 다 빈 채로 담긴다
     }
```

> **동적 타입 / 동적 값(dynamic type / dynamic value)** — 인터페이스 값이 지금 들고 있는 타입과 값.\
> 예: `var e error = (*MyErr)(nil)` 이면 동적 타입이 `*MyErr`, 동적 값이 `nil` 이다((1)절).

> **`nil` 인터페이스** — 두 칸이 다 빈 것. `== nil` 이 참이고 `reflect` 가 **값을 아예 못 만든다**\
> (`IsValid()` 가 `false`). 메서드를 부르면 호출 자체가 패닉이다([20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절).

> **`nil` 을 담은 인터페이스** — 타입 칸만 찬 것. `== nil` 이 **거짓**이고 `IsNil()` 이 참이다.\
> 메서드는 **불린다** — 리시버가 `nil` 일 뿐이라 그 메서드가 리시버를 읽으면 그때 패닉한다((4)절).

> **삼켜진 패닉** — `fmt` 가 `Error()`/`String()` 을 부른 뒤 패닉을 받아 `<nil>` 로 바꿔 찍는 것.\
> 예: `fmt.Println(err)` 이 `<nil>` 을 찍었는데 실제로는 `Error()` 가 터진 것이다((4)절).

> **넓힘(widening)** — 구체 타입 값을 인터페이스 타입 변수·반환값·인자에 넣는 것.\
> 예: `return p` 에서 `p` 가 `*MyErr` 이고 반환 타입이 `error` 면 그 자리에서 넓혀진다((2)절).

- [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절이 **이 함정을 한 번 던져 보고 넘겼다.**
  거기서 결론난 것은 세 가지다 — ① 인터페이스 값이 (타입, 값) 두 칸인 것은 **명세 보장**이고
  ② `trap()` 의 `err == nil` 이 `false` 이며 ③ `reflect` 의 `IsNil`/`IsValid` 가 두 상태를 가른다.
  **여기서는 그것을 전제로 두고** 「**그래서 어떤 코드가 이 함정에 빠지나**」와
  「**어떻게 막나**」로 간다.
- Rust 와 다른 점 — ★ Rust 에는 이 함정이 **원리상 없다.** `Option<Box<dyn Error>>` 의 `None` 은
  타입 칸이라는 것이 따로 없고, `Box<dyn Error>` 는 **`None` 이 될 수가 없다.**
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **21번**·**24번**.)
- 자바와 다른 점 — 자바의 `null` 은 **참조 하나**라 두 칸이 없다.
  「`null` 인데 `!= null` 이 참」이 될 수가 없다
  ([`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/)).
  ★ 대신 자바에는 **`NullPointerException` 이 나중에 터지는** 다른 문제가 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 코드가 이 함정에 빠지나** — 「`nil` 포인터를 돌려줬는데 `err != nil`」이 되는 **실제 코드 모양**은 몇 가지인가.
2. **어떻게 막나** — 반환 타입·성공 경로·변수 선언 중 **어디를 고치면** 막히나.
3. **포인터만 걸리나** — 맵·슬라이스·함수·채널·인터페이스는 어떤가. 그리고 **도구가 이것을 잡아 주나**.

★ 「인터페이스 값이 두 칸이다」 자체의 정본은 [20번 주제](../20-interface-declaration-and-implicit-implementation/)다.
★ 「담긴 것을 되꺼내는 법」은 [22번 주제](../22-type-assertion-any-and-comparable/), 「오류 값 설계」는 [23번 주제](../23-error-interface-and-errors-as-values/)와 목록의 **25번 주제**다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`%T` 와 `%v` 를 나란히 찍기** | 타입 칸이 찼는데 **찍히는 글자는 같다**는 것 | [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절에서 쓰던 창 |
| ★★★ **`x == nil` 과 `reflect…IsNil()` 을 같은 줄에** | **답이 갈리는 칸** — 이 주제의 전부 | ★ 본체 창 |
| ★★ **`IsValid()` 로 「값 칸이 있기는 한가」를 따로 묻기** | `nil` 인터페이스와 `nil` 담은 인터페이스를 **도구에서** 가르는 유일한 자리 | 〃 |
| ★ **타입 스위치의 `case nil` 로 물어보기** | 같은 질문을 **문법으로** 물은 것 — 답이 `reflect` 와 일치한다 | [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)에서 쓰던 창 |
| ★★ **`go vet` 을 탐침 8개로 던지기** | **아무 말도 안 한다** — 그 침묵이 재료다 | ★ 이 주제의 고유 창 |
| **부적용 — 컴파일 에러** | ★★★ **잴 것이 없다.** 이 함정은 **컴파일이 통과한다** — 타입은 맞기 때문이다 | — |
| **부적용 — 벤치마크** | 두 칸을 채우는 일뿐이라 **잴 것이 없다.** 이 문서는 **안 쟀다** | — |

★★★ **「부적용 — 컴파일 에러」 칸이 이 주제의 성격이다.**
[19번 주제](../19-method-sets-value-vs-pointer-receiver/)와 [20번 주제](../20-interface-declaration-and-implicit-implementation/)에서는
**틀리면 컴파일러가 문장으로 말해 줬다.** 여기서는 **말해 줄 컴파일러가 없다** —
`*MyErr` 을 `error` 로 넓히는 것은 **옳은 코드**이기 때문이다.
그래서 이 주제의 도구는 전부 **런타임 쪽**(`%T`·`reflect`·타입 스위치)이다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「이 인터페이스의 값 칸이 비었나」를 **언어 문법으로는 물을 수 없다**(`==` 는 두 칸을 함께 본다).
그래서 **`reflect.Value.IsNil()`** 로 물었다. ★ 바꾼 창의 한계도 적는다 —
`reflect` 는 **`IsNil()` 을 물을 수 없는 종류가 있다**(`int`·`string`·구조체는 부르면 패닉이다).
그래서 (1)절의 프로그램은 `Kind()` 로 먼저 걸러 놓고 묻는다.

### (1) ★★★ 두 칸을 글자로 — 답이 갈리는 칸 하나

**언제 쓰나** — 「이 인터페이스가 정말 비었나」를 확인할 때.

```text
===== 소스: t21a.go =====
package main

import (
	"fmt"
	"reflect"
)

type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// 인터페이스의 두 칸을 한 줄로 찍는다.
// x == nil 은 두 칸이 모두 비었을 때만 참이고, IsNil() 은 값 칸만 본다.
func slots(label string, x any) {
	rv := reflect.ValueOf(x)
	isNil := "cannot-ask" // 값 칸이 nil 을 가질 수 없는 종류
	switch {
	case !rv.IsValid():
		isNil = "no-value-slot"
	case rv.Kind() == reflect.Pointer || rv.Kind() == reflect.Map ||
		rv.Kind() == reflect.Slice || rv.Kind() == reflect.Func ||
		rv.Kind() == reflect.Chan || rv.Kind() == reflect.Interface:
		isNil = fmt.Sprintf("%v", rv.IsNil())
	}
	fmt.Printf("  %-22s x==nil:%-6v %%T=%-16T IsValid:%-6v IsNil:%s\n",
		label, x == nil, x, rv.IsValid(), isNil)
}

func main() {
	fmt.Println("-- (1) 두 칸이 다 빈 것 --")
	var pureIface error
	slots("var e error", pureIface)
	slots("untyped nil", nil)

	fmt.Println("-- (2) 타입 칸만 찬 것 : x == nil 이 false 인데 IsNil() 은 true 다 --")
	slots("(*MyErr)(nil)", (*MyErr)(nil))
	slots("(*int)(nil)", (*int)(nil))
	slots("map[string]int(nil)", map[string]int(nil))
	slots("[]int(nil)", []int(nil))
	slots("(func())(nil)", (func())(nil))
	slots("(chan int)(nil)", (chan int)(nil))

	fmt.Println("-- (3) 값 칸이 비지 않은 것 --")
	slots("&MyErr{}", &MyErr{Msg: "x"})
	slots("map[string]int{}", map[string]int{})
	slots("[]int{}", []int{})

	fmt.Println("-- (4) IsNil() 을 물을 수 없는 종류 --")
	slots("int(0)", 0)
	slots("string(\"\")", "")
	slots("struct{}{}", struct{}{})

	fmt.Println("-- (5) 인터페이스를 인터페이스에 담으면 두 칸이 그대로 복사된다 --")
	var e1 error                 // 두 칸 다 빔
	var a1 any = e1              // 담아도 여전히 두 칸 다 빔
	var e2 error = (*MyErr)(nil) // 타입 칸이 찬 것
	var a2 any = e2              // 담으면 그 두 칸이 그대로 온다
	fmt.Printf("  var a any = (빈 error)       -> a == nil : %v\n", a1 == nil)
	fmt.Printf("  var a any = (nil 담은 error) -> a == nil : %v  (%%T=%T)\n", a2 == nil, a2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- (1) 두 칸이 다 빈 것 --
  var e error            x==nil:true   %T=<nil>            IsValid:false  IsNil:no-value-slot
  untyped nil            x==nil:true   %T=<nil>            IsValid:false  IsNil:no-value-slot
-- (2) 타입 칸만 찬 것 : x == nil 이 false 인데 IsNil() 은 true 다 --
  (*MyErr)(nil)          x==nil:false  %T=*main.MyErr      IsValid:true   IsNil:true
  (*int)(nil)            x==nil:false  %T=*int             IsValid:true   IsNil:true
  map[string]int(nil)    x==nil:false  %T=map[string]int   IsValid:true   IsNil:true
  []int(nil)             x==nil:false  %T=[]int            IsValid:true   IsNil:true
  (func())(nil)          x==nil:false  %T=func()           IsValid:true   IsNil:true
  (chan int)(nil)        x==nil:false  %T=chan int         IsValid:true   IsNil:true
-- (3) 값 칸이 비지 않은 것 --
  &MyErr{}               x==nil:false  %T=*main.MyErr      IsValid:true   IsNil:false
  map[string]int{}       x==nil:false  %T=map[string]int   IsValid:true   IsNil:false
  []int{}                x==nil:false  %T=[]int            IsValid:true   IsNil:false
-- (4) IsNil() 을 물을 수 없는 종류 --
  int(0)                 x==nil:false  %T=int              IsValid:true   IsNil:cannot-ask
  string("")             x==nil:false  %T=string           IsValid:true   IsNil:cannot-ask
  struct{}{}             x==nil:false  %T=struct {}        IsValid:true   IsNil:cannot-ask
-- (5) 인터페이스를 인터페이스에 담으면 두 칸이 그대로 복사된다 --
  var a any = (빈 error)       -> a == nil : true
  var a any = (nil 담은 error) -> a == nil : false  (%T=*main.MyErr)
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **둘째 덩어리의 여섯 줄이 이 주제의 전부다** — `x == nil` 은 `false` 인데 `IsNil()` 은 `true` 다.
  「**값은 비었는데 인터페이스는 안 비었다**」가 그 두 칸으로 글자가 됐다.
- 명세가 그 규칙을 그대로 적는다.

```text
===== 명령: sed -n "5204,5210p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

	
	Interface types that are not type parameters are comparable.
	Two interface values are equal if they have identical dynamic types
	and equal dynamic values or if both have value nil.
	
(exit 0)
```

  ★ **「둘 다 `nil`」은 두 칸이 다 비었다는 뜻**이다. 타입 칸에 `*MyErr` 이 있으면 그 조건이 깨진다.
- ★★ **`%v` 만 같다.** 표로 보면 이렇다.

| | `x == nil` | `%T` | `%v` | `IsValid` | `IsNil` |
|---|---|---|---|---|---|
| `var e error` | **`true`** | `<nil>` | `<nil>` | `false` | 물을 수 없음 |
| `(*MyErr)(nil)` | ★ **`false`** | `*main.MyErr` | `<nil>` | `true` | ★ **`true`** |
| `&MyErr{}` | `false` | `*main.MyErr` | (메시지) | `true` | `false` |

  **가운데 줄과 윗줄이 `%v` 에서만 같다.** 로그는 그 칸만 보여 준다.
- ★★ **`IsValid()` 가 두 상태를 가른다.** 진짜 `nil` 인터페이스는 `reflect` 가
  **값을 아예 못 만든다**(`false`). 타입 칸이 차 있으면 만든다(`true`).
  ★ 그래서 `IsNil()` 을 바로 부르면 안 되고 **`IsValid()` 로 먼저 물어야** 한다.
- ★★★ **다섯째 덩어리가 중요하다** — **인터페이스를 인터페이스에 담으면 두 칸이 그대로 복사된다.**
  빈 `error` 를 `any` 에 넣으면 `any` 도 비어 있고, `nil` 담은 `error` 를 `any` 에 넣으면
  **그 `*MyErr` 표가 따라온다.** 「`any` 로 한 번 감싸면 풀리겠지」가 안 통한다.
- 넷째 덩어리 — `int`·`string`·구조체는 **`IsNil()` 을 물을 수 없다**(부르면 패닉이다).
  ★ **그것도 답이다** — 이 종류들은 애초에 「빈 값」이라는 상태가 없어 함정에 안 빠진다.

비용 — 두 칸을 채우는 일뿐이다. **이 문서는 재지 않았다.**

### (2) ★★★ 함정에 빠지는 네 가지 코드 모양

**언제 쓰나** — 코드 리뷰에서 이 함정을 찾을 때. **찾을 것은 「구체 타입 변수를 `error` 로 넓히는 한 줄」이다.**

```text
===== 소스: t21b.go =====
package main

import "fmt"

type ValidationErr struct{ Field string }

func (e *ValidationErr) Error() string { return "invalid field: " + e.Field }

// (가) 미리 선언해 두고 분기에서만 채운다 — 가장 흔한 꼴
func validate(name string) error {
	var e *ValidationErr // 이 한 줄이 타입 칸을 정한다
	if name == "" {
		e = &ValidationErr{Field: "name"}
	}
	return e // name 이 비지 않아도 nil 이 아닌 error 가 나온다
}

// (나) 도우미가 구체 타입을 돌려주고 호출부가 그대로 넘긴다
func check(n int) *ValidationErr {
	if n < 0 {
		return &ValidationErr{Field: "n"}
	}
	return nil // 여기서는 진짜 nil 포인터다
}

func run(n int) error { return check(n) } // 담기면서 타입 칸이 찬다

// (다) 구조체 필드가 구체 타입이다
type Result struct{ Err *ValidationErr }

func (r Result) Fail() error { return r.Err }

// (라) defer 로 명명 반환값을 채운다
func withDefer(fail bool) (err error) {
	var e *ValidationErr
	defer func() { err = e }() // 성공해도 e 의 타입 칸이 실린다
	if fail {
		e = &ValidationErr{Field: "d"}
	}
	return
}

func report(label string, err error) {
	taken := "아니오"
	if err != nil {
		taken = "예"
	}
	fmt.Printf("  %-26s err==nil:%-6v %%T=%-20T %%v=%-22v if err != nil 로 들어가나:%s\n",
		label, err == nil, err, err, taken)
}

func main() {
	fmt.Println("-- 성공 경로인데 전부 함정에 빠진다 --")
	report("(가) validate(\"go\")", validate("go"))
	report("(나) run(1)", run(1))
	report("(다) Result{}.Fail()", Result{}.Fail())
	report("(라) withDefer(false)", withDefer(false))

	fmt.Println("-- 실패 경로는 정상이다 (원래 의도대로) --")
	report("(가) validate(\"\")", validate(""))
	report("(나) run(-1)", run(-1))

	fmt.Println("-- (나) 의 도우미를 구체 타입 그대로 받으면 제대로 nil 이다 --")
	p := check(1)
	fmt.Printf("  check(1) 의 정적 타입은 *ValidationErr -> p == nil : %v\n", p == nil)
	fmt.Printf("  같은 값을 error 에 담으면          -> err == nil : %v\n", error(p) == nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 성공 경로인데 전부 함정에 빠진다 --
  (가) validate("go")         err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (나) run(1)                 err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (다) Result{}.Fail()        err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (라) withDefer(false)       err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
-- 실패 경로는 정상이다 (원래 의도대로) --
  (가) validate("")           err==nil:false  %T=*main.ValidationErr  %v=invalid field: name    if err != nil 로 들어가나:예
  (나) run(-1)                err==nil:false  %T=*main.ValidationErr  %v=invalid field: n       if err != nil 로 들어가나:예
-- (나) 의 도우미를 구체 타입 그대로 받으면 제대로 nil 이다 --
  check(1) 의 정적 타입은 *ValidationErr -> p == nil : true
  같은 값을 error 에 담으면          -> err == nil : false
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **네 줄이 전부 성공 경로인데 `err != nil` 로 들어갔다.**
  `%v` 는 넷 다 `<nil>` 이고 `%T` 는 넷 다 `*main.ValidationErr` 이다.
- 네 모양을 갈라 보면 이렇다.

| 모양 | 타입 칸을 채우는 줄 | 왜 흔한가 |
|---|---|---|
| **(가) 미리 선언하고 분기에서만 채운다** | `var e *ValidationErr` | 「초기화는 위에서」라는 습관 |
| **(나) 도우미가 구체 타입을 돌려준다** | `func check(n int) *ValidationErr` | 도우미 쪽이 그 타입을 쓰고 싶어서 |
| **(다) 구조체 필드가 구체 타입이다** | `type Result struct{ Err *ValidationErr }` | 필드에 타입을 적어 두면 편해서 |
| **(라) `defer` 로 명명 반환값을 채운다** | `defer func() { err = e }()` | 정리 코드에서 한 번에 넘기려고 |

- ★★ **(나) 가 가장 안 보인다.** 마지막 두 줄이 그것을 보인다 —
  **같은 값인데 받는 변수의 정적 타입에 따라 답이 갈린다.**
  `p := check(1)` 로 받으면 `p == nil` 이 **`true`**, 그것을 `error` 에 담으면 **`false`** 다.
  ★ **`check` 함수 안에서는 아무 문제가 없다.** 문제는 `run` 의 `return check(n)` **한 줄**이다.
- ★ 실패 경로(둘째 덩어리)는 **원래 의도대로 동작한다.** 그래서 테스트가 실패 경로만 보면 통과한다 —
  **성공 경로를 테스트해야** 잡힌다.

비용 — 없다. 잘못 도는 것일 뿐이다.

```text
   ★★ 네 모양 — 타입 칸을 채우는 줄은 하나뿐이다

   (가) 미리 선언             (나) 도우미의 반환 타입
     var e *ValidationErr       func check(n int) *ValidationErr
     if bad { e = … }                                ▲
     return e                   func run(n) error { return check(n) }
          ▲                                  ▲
          └─ 여기                            └─ 여기서 넓혀진다

   (다) 구조체 필드           (라) defer 가 명명 반환값에
     type Result struct {       func f() (err error) {
         Err *ValidationErr         var e *ValidationErr
     }         ▲                    defer func() { err = e }()
     func (r Result) Fail() error {           ▲
         return r.Err  ◀─ 여기                └─ 성공 경로에서도 실린다
     }

   ★ 넷 다 「구체 타입 이름이 적힌 줄」이 있고, 그 값이 error 로 넓혀진다.
```

### (3) ★★ 막는 규칙 셋 — 각각 던져 본다

**언제 쓰나** — (2)절의 네 모양 중 하나를 고칠 때.

```text
===== 소스: t21c.go =====
package main

import "fmt"

type ValidationErr struct{ Field string }

func (e *ValidationErr) Error() string { return "invalid field: " + e.Field }

// 규칙 (1) 도우미의 반환 타입도 error 로 적는다 — 구체 타입을 밖으로 내보내지 않는다
func checkA(n int) error {
	if n < 0 {
		return &ValidationErr{Field: "n"}
	}
	return nil
}
func runA(n int) error { return checkA(n) }

// 규칙 (2) 성공 경로에서 nil 을 명시로 돌려준다 — 구체 변수를 쓸 수밖에 없을 때
func validateB(name string) error {
	var e *ValidationErr
	if name == "" {
		e = &ValidationErr{Field: "name"}
	}
	if e == nil { // 두 줄이 함정을 막는다
		return nil
	}
	return e
}

// 규칙 (3) 구체 타입 변수를 아예 만들지 않는다 — 분기에서 바로 돌려준다
func validateC(name string) error {
	if name == "" {
		return &ValidationErr{Field: "name"}
	}
	return nil
}

// 규칙 (2)의 defer 판 — 명명 반환값에 쓸 때
func withDeferFixed(fail bool) (err error) {
	var e *ValidationErr
	defer func() {
		if e != nil { // 조건을 씌운다
			err = e
		}
	}()
	if fail {
		e = &ValidationErr{Field: "d"}
	}
	return
}

func report(label string, err error) {
	fmt.Printf("  %-28s err==nil:%-6v %%T=%-20T %%v=%v\n", label, err == nil, err, err)
}

func main() {
	fmt.Println("-- 성공 경로 : 세 규칙이 전부 제대로 nil 을 낸다 --")
	report("규칙(1) runA(1)", runA(1))
	report("규칙(2) validateB(\"go\")", validateB("go"))
	report("규칙(3) validateC(\"go\")", validateC("go"))
	report("규칙(2) withDeferFixed(false)", withDeferFixed(false))

	fmt.Println("-- 실패 경로 : 네 판 모두 원래대로 동작한다 --")
	report("규칙(1) runA(-1)", runA(-1))
	report("규칙(2) validateB(\"\")", validateB(""))
	report("규칙(3) validateC(\"\")", validateC(""))
	report("규칙(2) withDeferFixed(true)", withDeferFixed(true))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 성공 경로 : 세 규칙이 전부 제대로 nil 을 낸다 --
  규칙(1) runA(1)                err==nil:true   %T=<nil>                %v=<nil>
  규칙(2) validateB("go")        err==nil:true   %T=<nil>                %v=<nil>
  규칙(3) validateC("go")        err==nil:true   %T=<nil>                %v=<nil>
  규칙(2) withDeferFixed(false)  err==nil:true   %T=<nil>                %v=<nil>
-- 실패 경로 : 네 판 모두 원래대로 동작한다 --
  규칙(1) runA(-1)               err==nil:false  %T=*main.ValidationErr  %v=invalid field: n
  규칙(2) validateB("")          err==nil:false  %T=*main.ValidationErr  %v=invalid field: name
  규칙(3) validateC("")          err==nil:false  %T=*main.ValidationErr  %v=invalid field: name
  규칙(2) withDeferFixed(true)   err==nil:false  %T=*main.ValidationErr  %v=invalid field: d
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **세 규칙이 전부 `err == nil : true` 를 낸다.** 그리고 실패 경로도 그대로 돈다.

| 규칙 | 무엇을 고치나 | 언제 고르나 |
|---|---|---|
| ★★★ **(1) 반환 타입을 `error` 로** | **도우미까지** 구체 타입을 안 내보낸다 | 기본값. 고칠 자리가 하나다 |
| ★★ **(2) 성공 경로에서 `nil` 을 명시** | `if e == nil { return nil }` 두 줄 | 구체 변수를 꼭 써야 할 때(`defer` 판 포함) |
| ★ **(3) 구체 타입 변수를 안 만든다** | 분기에서 바로 `return &Err{…}` | 함수가 짧을 때. 가장 읽기 쉽다 |

- ★★ **규칙 (1)이 가장 세다.** (2)와 (3)은 **그 함수 하나**를 고치는 것이고,
  (1)은 **그 타입이 밖으로 새는 것을 막는다.** (2)절의 (나) 모양이 그래서 생겼다.
- ★ `defer` 판은 규칙 (2)의 변형이다 — `defer func() { if e != nil { err = e } }()`.
  **조건 한 줄**이 타입 칸이 실리는 것을 막는다.
- ★★ **규칙 (3)만으로는 (다) 모양이 안 고쳐진다** — 구조체 필드는 변수가 아니다.
  필드 타입을 `error` 로 바꾸는 것이 규칙 (1)의 필드 판이다.

비용 — 규칙 (2)가 두 줄 는다. 나머지는 없다.

### (4) ★★ 로그에는 `<nil>` 이 찍히는데 `err != nil` 이다

**언제 쓰나** — 장애 로그에 「에러: `<nil>`」이 찍혀 있을 때.

```text
===== 소스: t21d.go =====
package main

import (
	"errors"
	"fmt"
	"os"
)

// Error() 안에서 리시버를 읽는 흔한 판
type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// nil 리시버를 스스로 막는 판 — 로그가 더 그럴듯해진다
type SafeErr struct{ Msg string }

func (e *SafeErr) Error() string {
	if e == nil {
		return "SafeErr(비어 있음)"
	}
	return "SafeErr:" + e.Msg
}

func main() {
	var bad error = (*MyErr)(nil)
	var safe error = (*SafeErr)(nil)
	var pure error

	fmt.Println("-- 로그에 찍히는 글자와 err != nil 의 답이 어긋난다 --")
	fmt.Printf("  bad  : fmt.Println -> ")
	fmt.Println(bad)
	fmt.Printf("  safe : fmt.Println -> ")
	fmt.Println(safe)
	fmt.Printf("  pure : fmt.Println -> ")
	fmt.Println(pure)

	fmt.Println("-- 그런데 세 값의 err != nil 은 이렇다 --")
	fmt.Printf("  bad  != nil : %v\n", bad != nil)
	fmt.Printf("  safe != nil : %v\n", safe != nil)
	fmt.Printf("  pure != nil : %v\n", pure != nil)

	fmt.Println("-- %v 가 <nil> 을 찍는 것은 fmt 의 계약이다 (Error() 를 안 부른다) --")
	fmt.Printf("  bad  : %%v=%v  %%s=%s  %%T=%T\n", bad, bad, bad)
	fmt.Printf("  safe : %%v=%v  %%s=%s  %%T=%T\n", safe, safe, safe)

	fmt.Println("-- errors.Is(err, nil) 은 == 와 같은 답을 준다 --")
	fmt.Printf("  errors.Is(bad,  nil) = %v   (bad == nil  은 %v)\n", errors.Is(bad, nil), bad == nil)
	fmt.Printf("  errors.Is(pure, nil) = %v   (pure == nil 은 %v)\n", errors.Is(pure, nil), pure == nil)
	fmt.Printf("  errors.Is(nil,  nil) = %v\n", errors.Is(nil, nil))
	fmt.Printf("  errors.As(bad, new(*MyErr)) = %v  <- 타입 칸이 있으니 찾아진다\n",
		errors.As(bad, new(*MyErr)))

	fmt.Fprintln(os.Stderr, "-- 이제 bad.Error() 를 직접 부른다 --")
	_ = bad.Error()
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 로그에 찍히는 글자와 err != nil 의 답이 어긋난다 --
  bad  : fmt.Println -> <nil>
  safe : fmt.Println -> SafeErr(비어 있음)
  pure : fmt.Println -> <nil>
-- 그런데 세 값의 err != nil 은 이렇다 --
  bad  != nil : true
  safe != nil : true
  pure != nil : false
-- %v 가 <nil> 을 찍는 것은 fmt 의 계약이다 (Error() 를 안 부른다) --
  bad  : %v=<nil>  %s=<nil>  %T=*main.MyErr
  safe : %v=SafeErr(비어 있음)  %s=SafeErr(비어 있음)  %T=*main.SafeErr
-- errors.Is(err, nil) 은 == 와 같은 답을 준다 --
  errors.Is(bad,  nil) = false   (bad == nil  은 false)
  errors.Is(pure, nil) = true   (pure == nil 은 true)
  errors.Is(nil,  nil) = true
  errors.As(bad, new(*MyErr)) = true  <- 타입 칸이 있으니 찾아진다
-- 이제 bad.Error() 를 직접 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x49e954]

goroutine 1 [running]:
main.(*MyErr).Error(...)
	ex/t21d.go:12
main.main()
	ex/t21d.go:54 +0x5f4
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **세 줄이 전부 `<nil>` 로 찍히는데 `err != nil` 은 둘이 참이다.**
  로그만 보면 **셋을 구별할 방법이 없다.**
- ★★★ **`%v` 가 찍은 `<nil>` 은 사실 「삼켜진 패닉」이다.** 이 문서를 쓰면서 뒤집힌 전제다 —
  「`fmt` 는 `nil` 포인터면 메서드를 안 부른다」가 아니라 **부르고, 터지면 `<nil>` 로 바꿔 찍는다.**
  두 줄이 갈린 것이 그 증거다(`bad` 는 `<nil>`, `safe` 는 메시지). 소스가 그렇게 적혀 있다.

```text
===== 명령: grep -n -A 8 "func (p \*pp) catchPanic" "$(go env GOROOT)/src/fmt/print.go" =====
580:func (p *pp) catchPanic(arg any, verb rune, method string) {
581-	if err := recover(); err != nil {
582-		// If it's a nil pointer, just say "<nil>". The likeliest causes are a
583-		// Stringer that fails to guard against nil or a nil pointer for a
584-		// value receiver, and in either case, "<nil>" is a nice result.
585-		if v := reflect.ValueOf(arg); v.Kind() == reflect.Pointer && v.IsNil() {
586-			p.buf.writeString(nilAngleString)
587-			return
588-		}
(exit 0)
```

  ★★ **`if err := recover(); err != nil` 아래에 있다** — 메서드를 부른 뒤 **패닉을 받아** 검사한다.
  주석까지 그 사정을 적어 둔다(「a Stringer that fails to guard against nil」).
  ★★★ **그래서 `<nil>` 이 찍힌 로그는 「값이 없었다」가 아니라 「`Error()` 가 터졌다」일 수 있다.**
- ★★★ **`SafeErr` 줄이 더 나쁘다.** `Error()` 가 `nil` 리시버를 스스로 막아 정상 반환하면
  `fmt` 가 **그 문자열을 그대로 찍는다** — 여기서는 `SafeErr(비어 있음)` 이 찍혔다.
  사람이 보기에 **정상적인 오류 메시지**인데 실제로는 아무 일도 안 일어난 것이다.
  ★ 「`nil` 포인터면 무조건 `<nil>`」로 외우면 이 줄에서 틀린다.
- ★ **`errors.Is(err, nil)` 은 `==` 와 같은 답을 준다.** 표준 라이브러리 소스가 그것을 말한다.

```text
===== 명령: grep -n -A 8 "^func Is(err, target error) bool" "$(go env GOROOT)/src/errors/wrap.go" =====
45:func Is(err, target error) bool {
46-	if err == nil || target == nil {
47-		return err == target
48-	}
49-
50-	isComparable := reflectlite.TypeOf(target).Comparable()
51-	return is(err, target, isComparable)
52-}
53-
(exit 0)
```

  ★★ **첫 두 줄이 답이다** — `target` 이 `nil` 이면 사슬을 타지 않고 **`err == target` 을 그대로 돌려준다.**
  그러니 **`errors.Is(err, nil)` 로 이 함정을 못 막는다.** `== nil` 과 똑같이 속는다.
- ★ **`errors.As(bad, new(*MyErr))` 는 `true`** 다 — 타입 칸이 있으니 그 타입으로 찾아진다.
  ★★ **찾아진 값이 `nil` 포인터**라는 것이 더 나쁘다. 그것을 쓰면 그때 터진다.
- 마지막 — **`bad.Error()` 를 직접 부르면 그제야 패닉**이다.
  **호출 자체는 성공했다**(리시버가 `nil` 일 뿐이다) — `Error()` 안에서 `e.Msg` 를 읽다 터졌다.
  스택에 **`main.(*MyErr).Error(...)` 프레임이 찍혀** 있는 것이 그 증거다.

비용 — 없다.

### (5) ★★ 포인터만 걸리는 것이 아니다 — 전수

**언제 쓰나** — 「내 함수는 포인터를 안 돌려주니 괜찮겠지」라고 생각할 때.

```text
===== 소스: t21e.go =====
package main

import (
	"fmt"
	"io"
	"os"
)

type Cache interface{ Get(k string) int }

type mapCache struct{ m map[string]int }

func (c *mapCache) Get(k string) int { return c.m[k] }

// 포인터가 아닌 것들도 같은 함정에 빠진다.
func newWriter(enable bool) io.Writer {
	var f *os.File // 포인터
	if enable {
		f = os.Stdout
	}
	return f
}

func newCache(enable bool) Cache {
	var c *mapCache
	if enable {
		c = &mapCache{m: map[string]int{"a": 1}}
	}
	return c
}

func tags(enable bool) any {
	var m map[string]int // 맵
	if enable {
		m = map[string]int{"a": 1}
	}
	return m
}

func rows(enable bool) any {
	var s []int // 슬라이스
	if enable {
		s = []int{1}
	}
	return s
}

func hook(enable bool) any {
	var f func() // 함수
	if enable {
		f = func() {}
	}
	return f
}

func events(enable bool) any {
	var ch chan int // 채널
	if enable {
		ch = make(chan int, 1)
	}
	return ch
}

// 타입 스위치는 무엇을 고르나 — case nil 로 안 간다
func which(x any) string {
	switch x.(type) {
	case nil:
		return "case nil"
	case map[string]int:
		return "case map[string]int"
	case []int:
		return "case []int"
	case func():
		return "case func()"
	case chan int:
		return "case chan int"
	case io.Writer:
		return "case io.Writer"
	case Cache:
		return "case Cache"
	default:
		return "default"
	}
}

func line(label string, x any) {
	fmt.Printf("  %-22s x==nil:%-6v %%T=%-18T 타입스위치:%s\n", label, x == nil, x, which(x))
}

func main() {
	fmt.Println("-- 포인터만 걸리는 것이 아니다 : 맵·슬라이스·함수·채널도 같다 --")
	line("newWriter(false)", newWriter(false))
	line("newCache(false)", newCache(false))
	line("tags(false)", tags(false))
	line("rows(false)", rows(false))
	line("hook(false)", hook(false))
	line("events(false)", events(false))

	fmt.Println("-- 진짜 nil 인터페이스만 case nil 로 간다 --")
	var pure any
	line("var x any", pure)
	line("untyped nil", nil)

	fmt.Println("-- 채워 넣은 판 --")
	line("tags(true)", tags(true))
	line("events(true)", events(true))

	fmt.Println("-- 그런데 쓰임새는 종류마다 다르다 --")
	var m map[string]int
	fmt.Printf("  nil 맵 읽기      : m[\"a\"] = %d (패닉 없음)\n", m["a"])
	var s []int
	fmt.Printf("  nil 슬라이스 append : %v (패닉 없음)\n", append(s, 1))
	fmt.Fprintln(os.Stderr, "-- 이제 nil 함수를 부른다 --")
	var f func()
	f()
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 포인터만 걸리는 것이 아니다 : 맵·슬라이스·함수·채널도 같다 --
  newWriter(false)       x==nil:false  %T=*os.File           타입스위치:case io.Writer
  newCache(false)        x==nil:false  %T=*main.mapCache     타입스위치:case Cache
  tags(false)            x==nil:false  %T=map[string]int     타입스위치:case map[string]int
  rows(false)            x==nil:false  %T=[]int              타입스위치:case []int
  hook(false)            x==nil:false  %T=func()             타입스위치:case func()
  events(false)          x==nil:false  %T=chan int           타입스위치:case chan int
-- 진짜 nil 인터페이스만 case nil 로 간다 --
  var x any              x==nil:true   %T=<nil>              타입스위치:case nil
  untyped nil            x==nil:true   %T=<nil>              타입스위치:case nil
-- 채워 넣은 판 --
  tags(true)             x==nil:false  %T=map[string]int     타입스위치:case map[string]int
  events(true)           x==nil:false  %T=chan int           타입스위치:case chan int
-- 그런데 쓰임새는 종류마다 다르다 --
  nil 맵 읽기      : m["a"] = 0 (패닉 없음)
  nil 슬라이스 append : [1] (패닉 없음)
-- 이제 nil 함수를 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x49bd33]

goroutine 1 [running]:
main.main()
	ex/t21e.go:115 +0x373
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **여섯 종류가 전부 같은 함정에 빠진다** — 포인터·맵·슬라이스·함수·채널, 그리고 그 위의 인터페이스.
  **「`nil` 이 될 수 있는 종류」면 전부 대상**이다.
- ★★ **그런데 타입 스위치의 답이 그 사실을 그대로 말한다** —
  여섯 줄이 **`case nil` 로 안 가고** 각자의 구체 타입 가지로 간다.
  ★ 「`case nil` 이 잡아 주겠지」가 안 통한다. 명세가 `case nil` 을
  **인터페이스 값 자체가 `nil` 일 때**로 정의하기 때문이다([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절).
- ★★ **그런데 쓰임새는 종류마다 다르다** — 이것이 이 절의 둘째 결론이다.

| 종류 | `nil` 인 채로 무엇이 되나 | 그래서 |
|---|---|---|
| **맵** | 읽기는 된다(제로값) · **쓰기는 패닉** | 읽기만 하면 **끝까지 안 터진다** |
| **슬라이스** | `len`·`append`·`range` 가 **전부 된다** | ★ **영원히 안 터진다** |
| **함수** | 부르면 **패닉** | 바로 터진다 |
| **채널** | 송수신이 **영원히 막힌다** | ★★ 터지지도 않고 **멈춘다** |
| **포인터** | 필드를 읽으면 **패닉** | 메서드가 리시버를 안 쓰면 안 터진다 |

  ★★★ **슬라이스와 채널이 가장 나쁘다.** 슬라이스는 아무 일도 안 나고,
  채널은 **조용히 멈춘다**(그쪽 정본은 목록의 **29번 주제**다).
- ★ 마지막 — `nil` 함수를 부르자 **`panic: runtime error: invalid memory address or nil pointer dereference`**,
  종료 코드 2다. (4)절의 `nil` 포인터 역참조와 **같은 문구**다.

비용 — 없다.

### (6) ★★ 도구가 못 보는 것 — 탐침 8개를 던진다

**언제 쓰나** — 「린터가 잡아 주겠지」라고 생각할 때.

★★★ **탐침 8개를 한 패키지에 넣고 `go vet` 에게 물었다. 답한 것은 0개다.**
(2)절의 네 모양에 `io.Writer` 판·`any` 판·호출부 판을 더한 것이다.

```text
===== 소스: t21probe.go =====
// go vet 에게 같은 함정을 여덟 가지 모양으로 던진다.
package main

import (
	"fmt"
	"io"
	"os"
)

type E struct{ M string }

func (e *E) Error() string { return "E:" + e.M }

// 탐침 1 — 미리 선언하고 그대로 반환
func p1() error {
	var e *E
	return e
}

// 탐침 2 — 도우미가 구체 타입, 호출부가 error 로 넓힌다
func helper() *E { return nil }
func p2() error  { return helper() }

// 탐침 3 — nil 포인터 리터럴을 바로 반환
func p3() error { return (*E)(nil) }

// 탐침 4 — 명명 반환값을 defer 로 채운다
func p4() (err error) {
	var e *E
	defer func() { err = e }()
	return
}

// 탐침 5 — 구조체 필드가 구체 타입
type R struct{ Err *E }

func p5() error { return R{}.Err }

// 탐침 6 — nil *os.File 을 io.Writer 로
func p6() io.Writer {
	var f *os.File
	return f
}

// 탐침 7 — nil 맵을 any 로
func p7() any {
	var m map[string]int
	return m
}

// 탐침 8 — 호출부가 그 결과를 nil 과 비교한다 (함정이 실제로 터지는 자리)
func caller() string {
	if err := p1(); err != nil {
		return "에러 처리로 들어갔다"
	}
	return "정상"
}

func main() {
	fmt.Println(p1() == nil, p2() == nil, p3() == nil, p4() == nil,
		p5() == nil, p6() == nil, p7() == nil, caller())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
false false false false false false false 에러 처리로 들어갔다
(exit 0)
```

- 여덟 개가 **전부 `false`** 다. 마지막 칸은 **호출부가 실제로 에러 처리로 들어갔다**는 뜻이다.

```text
===== 소스: t21probe.go =====
// go vet 에게 같은 함정을 여덟 가지 모양으로 던진다.
package main

import (
	"fmt"
	"io"
	"os"
)

type E struct{ M string }

func (e *E) Error() string { return "E:" + e.M }

// 탐침 1 — 미리 선언하고 그대로 반환
func p1() error {
	var e *E
	return e
}

// 탐침 2 — 도우미가 구체 타입, 호출부가 error 로 넓힌다
func helper() *E { return nil }
func p2() error  { return helper() }

// 탐침 3 — nil 포인터 리터럴을 바로 반환
func p3() error { return (*E)(nil) }

// 탐침 4 — 명명 반환값을 defer 로 채운다
func p4() (err error) {
	var e *E
	defer func() { err = e }()
	return
}

// 탐침 5 — 구조체 필드가 구체 타입
type R struct{ Err *E }

func p5() error { return R{}.Err }

// 탐침 6 — nil *os.File 을 io.Writer 로
func p6() io.Writer {
	var f *os.File
	return f
}

// 탐침 7 — nil 맵을 any 로
func p7() any {
	var m map[string]int
	return m
}

// 탐침 8 — 호출부가 그 결과를 nil 과 비교한다 (함정이 실제로 터지는 자리)
func caller() string {
	if err := p1(); err != nil {
		return "에러 처리로 들어갔다"
	}
	return "정상"
}

func main() {
	fmt.Println(p1() == nil, p2() == nil, p3() == nil, p4() == nil,
		p5() == nil, p6() == nil, p7() == nil, caller())
}
===== 명령: go vet ./... =====
(exit 0)
```

- ★★★ **출력 0줄에 종료 코드 0.** 「안 물어본 것」이 아니라 **「물었는데 조용한 것」이다** —
  탐침 8개가 같은 패키지 안에 있고 빌드가 통과했다.
- 분석기 목록에 그런 검사가 아예 없다.

```text
===== 명령: go tool vet help | sed -n "/^Registered analyzers:/,/^By default/p" =====
Registered analyzers:

    appends      check for missing values after append
    asmdecl      report mismatches between assembly files and Go declarations
    assign       check for useless assignments
    atomic       check for common mistakes using the sync/atomic package
    bools        check for common mistakes involving boolean operators
    buildtag     check //go:build and // +build directives
    cgocall      detect some violations of the cgo pointer passing rules
    composites   check for unkeyed composite literals
    copylocks    check for locks erroneously passed by value
    defers       report common mistakes in defer statements
    directive    check Go toolchain directives such as //go:debug
    errorsas     report passing non-pointer or non-error values to errors.As
    framepointer report assembly that clobbers the frame pointer before saving it
    hostport     check format of addresses passed to net.Dial
    httpresponse check for mistakes using HTTP responses
    ifaceassert  detect impossible interface-to-interface type assertions
    loopclosure  check references to loop variables from within nested functions
    lostcancel   check cancel func returned by context.WithCancel is called
    nilfunc      check for useless comparisons between functions and nil
    printf       check consistency of Printf format strings and arguments
    shift        check for shifts that equal or exceed the width of the integer
    sigchanyzer  check for unbuffered channel of os.Signal
    slog         check for invalid structured logging calls
    stdmethods   check signature of methods of well-known interfaces
    stdversion   report uses of too-new standard library symbols
    stringintconv check for string(int) conversions
    structtag    check that struct field tags conform to reflect.StructTag.Get
    testinggoroutine report calls to (*testing.T).Fatal from goroutines started by a test
    tests        check for common mistaken usages of tests and examples
    timeformat   check for calls of (time.Time).Format or time.Parse with 2006-02-01
    unmarshal    report passing non-pointer or non-interface values to unmarshal
    unreachable  check for unreachable code
    unsafeptr    check for invalid conversions of uintptr to unsafe.Pointer
    unusedresult check for unused results of calls to some functions
    waitgroup    check for misuses of sync.WaitGroup

By default all analyzers are run.
(exit 0)
```

```text
===== 명령: echo "이름에 nil 이 든 분석기 : $(go tool vet help | sed -n "/^Registered analyzers:/,/^By default/p" | grep -c "^    .*nil")" =====
이름에 nil 이 든 분석기 : 1
(exit 0)
```

- ★★ **이름에 `nil` 이 든 분석기는 하나**(`nilfunc`)이고, 그것은
  「**함수를 `nil` 과 견주는 쓸모없는 비교**」를 보는 다른 검사다.
  ★ 목록에 `errorsas` 가 있는 것이 대비다 — **`errors.As` 의 인자 실수는 잡는다**([24번 주제](../24-error-wrapping-and-errors-is-as-join/)).
  **같은 도구가 어떤 실수는 잡고 이 실수는 안 잡는다.**
- 밖의 도구도 이 머신에는 없다.

```text
===== 명령: for t in staticcheck errcheck nilaway golangci-lint; do printf "%s : %s\n" "$t" "$(command -v $t || echo "PATH 에 없음")"; done =====
staticcheck : PATH 에 없음
errcheck : PATH 에 없음
nilaway : PATH 에 없음
golangci-lint : PATH 에 없음
(exit 0)
```

  ★ **「도구가 없다」고 적기 전에 `PATH` 를 확인한 블록**이다. 네 이름 모두 이 머신에 없다 —
  그래서 **이 문서는 그 도구들이 이 함정을 잡는지 안 잡는지 모른다.** 모르는 것은 모른다고 적는다.

★★★ **정리 — 탐침 8개 중 답한 것 0개.** 이 주제의 결론은 **목록의 공백**이다.
컴파일러도 안 막고(타입이 맞다) `go vet` 도 안 보고 밖의 도구는 이 머신에 없다.
**막는 것은 (3)절의 규칙 셋뿐**이고, 그 셋은 전부 **사람이 코드를 쓰는 방식**이다.

```text
   ★★ 도구 지도 — 이 주제만 아무도 안 말해 준다

   19번 메서드 집합   ──▶ 컴파일러  「method Speak has pointer receiver」
   20번 만족 단언     ──▶ 컴파일러  「missing method Name」  (적었을 때만)
   22번 comparable    ──▶ 컴파일러  「does not satisfy comparable」
   22번 인터페이스 단언 ─▶ go vet    「impossible type assertion …」
   24번 errors.As 인자 ─▶ go vet    「second argument to errors.As …」
   ★ 21번 (이 주제)  ──▶ (없음)     컴파일 exit 0 · vet 출력 0줄 exit 0

       ▲ 탐침 8개 중 답한 것 0개
```

비용 — `go vet` 한 번 더 도는 것뿐이다. **이 문서는 재지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t21form.go
package main

import "fmt"

type NotFound struct{ Key string }

func (e *NotFound) Error() string { return "not found: " + e.Key }

// (1) 함정 — 구체 포인터 타입 변수를 error 로 넓혀 돌려준다
func trap(k string) error {
	var e *NotFound
	if k == "" {
		e = &NotFound{Key: k}
	}
	return e
}

// (2) 막는 규칙 셋
func ruleA(k string) error { // 반환 타입을 error 로 (도우미까지)
	if k == "" {
		return &NotFound{Key: k}
	}
	return nil
}

func ruleB(k string) error { // 성공 경로에서 nil 을 명시
	var e *NotFound
	if k == "" {
		e = &NotFound{Key: k}
	}
	if e == nil {
		return nil
	}
	return e
}

func ruleC(k string) error { // 구체 타입 변수를 만들지 않는다
	if k == "" {
		return &NotFound{Key: k}
	}
	return nil
}

func main() {
	fmt.Println("trap :", trap("a") == nil)  // (3) 두 칸 중 타입 칸이 찼다
	fmt.Println("ruleA:", ruleA("a") == nil) // (4) 두 칸이 다 비었다
	fmt.Println("ruleB:", ruleB("a") == nil)
	fmt.Println("ruleC:", ruleC("a") == nil)

	var e error = trap("a")
	fmt.Printf("%%T=%T %%v=%v e==nil=%v\n", e, e, e == nil) // (5) 세 칸을 나란히
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
trap : false
ruleA: true
ruleB: true
ruleC: true
%T=*main.NotFound %v=<nil> e==nil=false
(exit 0)
```

규칙 불릿.

- **인터페이스 값은 (동적 타입, 동적 값) 두 칸**이고 **두 칸이 다 비어야 `nil`** 이다(명세).
- **구체 타입 값을 인터페이스에 넣으면 타입 칸이 찬다.** 그 값이 `nil` 이어도 찬다.
- **리터럴 `nil` 을 인터페이스에 넣으면 두 칸이 다 빈다.** 그래서 `return nil` 이 안전하다.
- **인터페이스를 인터페이스에 넣으면 두 칸이 그대로 복사된다.** 감싸도 안 풀린다.
- **`%v` 는 `<nil>` 을 찍을 수 있다** — 그것은 `fmt` 의 계약이지 `== nil` 의 답이 아니다.
- **`errors.Is(err, nil)` 은 `err == nil` 과 같다.** 이 함정을 못 막는다.
- **타입 스위치의 `case nil` 은 인터페이스 값 자체가 `nil` 일 때만** 골라진다.
- **포인터·맵·슬라이스·함수·채널·인터페이스**가 전부 대상이다.
- **컴파일러는 아무 말도 안 한다.** 타입이 맞기 때문이다.

### 금지 사례 — 컴파일러가 거부하는 것

★★★ **없다. 그것이 이 주제의 성격이다.**
(2)절의 네 모양은 **전부 컴파일이 통과하고**(종료 코드 0) `go vet` 도 침묵한다((6)절).
비교해 보면 이렇다.

| 주제 | 틀리면 누가 말해 주나 |
|---|---|
| [19번](../19-method-sets-value-vs-pointer-receiver/) 메서드 집합 | **컴파일러** — `method Speak has pointer receiver` |
| [20번](../20-interface-declaration-and-implicit-implementation/) 만족 단언 | **컴파일러**(단언을 적었을 때만) — `missing method Name` |
| **21번 (이 주제)** | ★ **아무도** — 컴파일 통과 · `vet` 0줄 · 런타임도 안 터진다 |
| [24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 `errors.As` 인자 | **`go vet`** — `errorsas` 분석기가 잡는다 |

## 어디서 틀리나

### 1. ★★★ 「`nil` 포인터를 돌려줬으니 `err == nil` 이겠지」

- (1)·(2)절 실측 — **`err == nil` 이 `false`** 이고 `%T` 는 `*main.ValidationErr`, `%v` 는 `<nil>` 이다.
- 고치는 법 — (3)절의 규칙 셋. **반환 타입을 `error` 로** 적는 것이 가장 세다.

### 2. ★★★ 「도우미가 구체 타입을 돌려주는 건 괜찮겠지」

- (2)절 실측 — `check(1)` 을 `p := check(1)` 로 받으면 `p == nil` 이 **`true`** 인데
  `return check(n)` 으로 `error` 에 담으면 **`false`** 다.
  ★ **`check` 함수 안에는 버그가 없다.** 버그는 넓히는 한 줄에 있다.
- 고치는 법 — 도우미의 반환 타입도 **`error`** 로 적는다.

### 3. ★★ 「로그에 `<nil>` 이 찍혔으니 에러가 없었던 거겠지」

- (4)절 실측 — **`<nil>` 이 찍히는데 `err != nil` 이 참**이다.
  `Error()` 가 `nil` 리시버를 막아 두면 **더 그럴듯한 메시지**가 찍힌다.
- 고치는 법 — 로그를 근거로 삼지 말고 **`%T` 를 같이 찍는다.**
  `fmt.Printf("err=%v (%T)", err, err)` 한 줄이면 타입 칸이 보인다.

### 4. ★★ 「포인터만 조심하면 되겠지」

- (5)절 실측 — **맵·슬라이스·함수·채널·인터페이스가 전부 같다.**
  그리고 **슬라이스는 그 뒤로도 안 터지고** 채널은 **조용히 멈춘다.**
- 고치는 법 — 인터페이스로 넓히는 **모든 반환값**에 같은 규칙을 적용한다.

### 5. ★★ 「`any` 로 한 번 감싸면 풀리겠지」

- (1)절 다섯째 덩어리 실측 — **두 칸이 그대로 복사된다.**
  `nil` 담은 `error` 를 `any` 에 넣어도 `a == nil` 이 **`false`** 다.
- 고치는 법 — 감싸기로는 못 푼다. **만드는 자리**에서 막는다.

### 6. ★★ 「`errors.Is(err, nil)` 이 제대로 봐 주겠지」

- (4)절 실측 + `errors/wrap.go` 소스 — `target` 이 `nil` 이면 **`err == target` 을 그대로 돌려준다.**
- 고치는 법 — 이 함정에는 안 쓴다. **`err == nil` 과 똑같이 속는다.**

### 7. ★★ 「`case nil` 이 잡아 주겠지」

- (5)절 실측 — 여섯 종류가 **전부 각자의 구체 타입 가지**로 갔다.
- 고치는 법 — `case nil` 은 **인터페이스 값 자체**가 비었는지만 본다.
  값 칸을 물으려면 **`reflect` 의 `IsNil()`** 이다.

### 8. ★ 「린터가 잡아 주겠지」

- (6)절 실측 — 탐침 **8개 중 0개**. `go vet` 출력 **0줄에 종료 코드 0**.
- 고치는 법 — 도구를 기다리지 말고 **코드 규칙**으로 막는다((3)절).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **인터페이스 값이 (동적 타입, 동적 값)인 것** | **명세 보장** | "identical dynamic types and equal dynamic values or if both have value nil" |
| **두 칸이 다 비어야 `nil` 인 것** | **명세 보장** | 〃 |
| **구체 값을 넓히면 타입 칸이 차는 것** | **명세 보장** | 대입 가능성 규칙 — 그 값이 `nil` 이어도 같다 |
| **인터페이스를 인터페이스에 넣으면 두 칸이 복사되는 것** | **명세 보장** | 〃 |
| **`case nil` 이 인터페이스 값 자체가 `nil` 일 때 골라지는 것** | **명세 보장** | Type switches 절([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)) |
| **`nil` 담은 인터페이스의 메서드가 불리는 것** | **명세 보장** | 메서드 호출은 동적 타입이 정한다 |
| **`nil` 슬라이스에 `append`·`len`·`range` 가 되는 것** | **명세 보장** | 그쪽 정본은 [05번](../05-arrays-vs-slices-value-and-header/)·[06번 주제](../06-len-cap-and-append-reallocation/) |
| **`nil` 맵 읽기가 제로값인 것** | **명세 보장** | 그쪽 정본은 [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) |
| **`%v` 가 `nil` 포인터를 `<nil>` 로 찍는 것** | ★★★ **`fmt` 의 계약 — 그것도 「패닉을 받아서」다** | `fmt/print.go` 의 `catchPanic`. 명세가 아니다 |
| **`Error()` 가 `nil` 리시버를 막으면 그 메시지가 찍히는 것** | ★★ **`fmt` 의 계약** | (4)절 실측. 「`nil` 포인터면 무조건 `<nil>`」이 아니다 |
| **`errors.Is(err, nil)` 이 `==` 와 같은 것** | **표준 라이브러리 계약** | `errors/wrap.go` 의 첫 두 줄 |
| **`reflect` 의 `IsValid`/`IsNil` 이 두 칸을 가르는 것** | **표준 라이브러리 계약** | `reflect` 의 문서 |
| **`IsNil()` 을 못 부르는 종류가 있는 것** | **표준 라이브러리 계약** | 부르면 패닉이다 — `Kind()` 로 먼저 거른다 |
| 패닉 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 런타임의 것 |
| 패닉 블록의 `pc=0x…` · 스택의 힙 주소 | **빌드 산출물·런타임** | 흔들린다 |
| **`go vet` 이 이 함정을 안 보는 것** | ★ **도구(구현)** | 분석기 목록에 없다. 판이 오르면 달라질 수 있다 |
| **밖의 린터가 잡는지** | ★ **모른다** | 이 머신에 없다((6)절) |
| 인터페이스 넓힘의 **실제 비용** | ★ **안 쟀다** | 벤치마크가 없다(목록의 **50번 주제**) |

★ 이 주제의 결론은 「**규칙은 전부 명세인데 어기는 것을 아무도 안 막는다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 오류를 돌려주는 함수를 쓴다 | **반환 타입을 `error` 로**(도우미까지) | 구체 타입이 밖으로 안 샌다 |
| 구체 타입 변수를 꼭 써야 한다 | **성공 경로에서 `return nil`** | 두 줄이 타입 칸을 막는다 |
| `defer` 로 명명 반환값을 채운다 | **`if e != nil` 조건을 씌운다** | 성공 경로에서 안 실린다 |
| 구조체가 오류를 들고 다닌다 | **필드 타입을 `error` 로** | 필드는 변수가 아니라 규칙 (3)이 안 먹는다 |
| 「이 인터페이스가 정말 비었나」 | **`%T` 를 같이 찍는다** | `%v` 만으로는 안 갈린다 |
| 두 종류의 `nil` 을 갈라야 한다 | **`reflect` 의 `IsValid`/`IsNil`** | `== nil` 은 두 칸을 함께 본다 |
| 담긴 타입으로 분기한다 | **타입 스위치**([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)) | 단 `case nil` 은 값 칸을 안 본다 |
| 린터에 기대고 싶다 | **기대지 않는다** | 탐침 8개 중 0개 |
| 오류를 감싼다 | [24번 주제](../24-error-wrapping-and-errors-is-as-join/) | `%w`·`Is`/`As` 는 **이 함정을 못 막는다** |

판단 규칙 두 줄.

- ★★★ **`error` 를 돌려줄 때 구체 타입 변수를 그대로 `return` 하지 마라.** 이 주제의 전부가 그 한 줄이다.
- ★★ **로그에 `<nil>` 이 찍혀 있어도 그것이 「에러가 없었다」는 증거가 아니다.** `%T` 를 같이 찍어라.

## 핵심 문장

- ★★★ **인터페이스 값은 두 칸(동적 타입, 동적 값)이고 두 칸이 다 비어야 `nil` 이다.**
  이것은 **명세가 못 박은 것**이지 gc 의 사정이 아니다 —
  비교 규칙이 「dynamic types」·「dynamic values」라고 두 칸을 직접 부른다.
- ★★★ **`x == nil` 이 `false` 인데 `reflect.ValueOf(x).IsNil()` 이 `true` 인 칸**이 이 주제의 전부다.
  「값은 비었는데 인터페이스는 안 비었다」가 그 두 글자로 갈린다.
- ★★★ **`%v` 만 같다.** `nil` 인터페이스도 `nil` 담은 인터페이스도 `<nil>` 을 찍는다 —
  **로그로는 구별이 안 된다.** `%T` 를 같이 찍어야 보인다.
- ★★★ **그 `<nil>` 은 「삼켜진 패닉」일 수 있다.** `fmt` 는 `Error()` 를 부르고,
  터졌는데 인자가 `nil` 포인터면 **`<nil>` 로 바꿔 찍는다**(`fmt/print.go` 의 `catchPanic`).
  「메서드를 안 부른다」가 아니다 — 이 문서를 쓰면서 뒤집힌 전제다.
- ★★★ **함정에 빠지는 코드 모양은 넷**이다 — 미리 선언 · 도우미의 구체 타입 반환 ·
  구조체 필드 · `defer` 로 명명 반환값 채우기. **전부 성공 경로에서만 틀린다.**
- ★★ **막는 규칙은 셋**이고 **반환 타입을 `error` 로 적는 것**이 가장 세다 —
  나머지 둘은 함수 하나를 고치는 것이고 이것은 **타입이 새는 것**을 막는다.
- ★★★ **포인터만이 아니다** — 맵·슬라이스·함수·채널·인터페이스가 전부 같다.
  그리고 **슬라이스는 그 뒤로도 안 터지고 채널은 조용히 멈춘다.**
- ★★ **`any` 로 감싸도 안 풀린다.** 인터페이스를 인터페이스에 넣으면 **두 칸이 그대로 복사된다.**
- ★★ **`errors.Is(err, nil)` 로 못 막는다.** 표준 라이브러리 소스가
  `if err == nil || target == nil { return err == target }` 이라고 적혀 있다.
- ★★ **`case nil` 도 못 막는다.** 그것은 인터페이스 값 자체가 비었는지만 본다.
- ★★★ **아무도 안 막는다** — 컴파일러는 타입이 맞으니 통과시키고
  `go vet` 은 **탐침 8개 중 0개**에 출력 0줄·종료 코드 0이다.
  **막는 것은 코드를 쓰는 규칙뿐**이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 21번)
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스 선언과 암묵 구현) —
  ★★★ **이 주제의 직접 선행.** **그쪽은 「두 칸이 있다」를 명세로 세우고 한 번 던져 보는 데까지**,
  여기는 **「그래서 어떤 코드가 빠지고 어떻게 막나」부터**
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) —
  **그쪽은** 「**무엇이 인터페이스에 담기나**」, 여기는 **「담긴 뒤 그 값이 비었나」**
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(타입 스위치) —
  **`case nil` 의 정본.** 여기는 **그것이 이 함정을 못 막는다**는 데까지
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(포인터) —
  `nil` 포인터 역참조가 패닉인 것 자체는 거기
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) ·
  [05번](../05-arrays-vs-slices-value-and-header/)·[06번 주제](../06-len-cap-and-append-reallocation/)(슬라이스) —
  `nil` 맵·`nil` 슬라이스가 무엇을 허락하는지의 정본. 여기는 **그것들이 인터페이스에 담길 때**만
- [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언·`any`·`comparable`) — **담긴 것을 되꺼내는 법의 정본**
- [23번 주제](../23-error-interface-and-errors-as-values/)(`error` 인터페이스) — **이 함정이 왜 `error` 에서 유명한가.**
  거기가 「오류가 값이다」의 정본이다
- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`%w`·`Is`/`As`) — ★ **`errors.Is`/`As` 가 이 함정을 못 막는 것**의 정본
- 목록의 **29번 주제**(채널) — `nil` 채널이 **조용히 멈추는** 것의 정본
- 목록의 **52번 주제**(도구) — `go vet` 이 무엇을 보고 무엇을 안 보는지의 정본
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **21번**
  ([`../../../rust/syntax/21-option-and-combinators/`](../../../rust/syntax/21-option-and-combinators/)) —
  ★ **그쪽은 「없음」이 `Option` 이라는 값**이라 두 칸이 갈릴 자리가 없다
- [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/) —
  **그쪽의 `null` 은 참조 하나**라 「`null` 인데 `!= null`」이 될 수 없다

## 용어 풀이

- **인터페이스 값의 두 칸** — 동적 타입과 동적 값. 명세의 비교 규칙이 그 이름을 직접 쓴다.
- **`nil` 인터페이스** — 두 칸이 다 빈 것. `== nil` 이 참. `reflect` 가 값을 못 만든다.
- **`nil` 을 담은 인터페이스** — 타입 칸만 찬 것. `== nil` 이 거짓. `IsNil()` 이 참.
- **넓힘** — 구체 타입 값을 인터페이스 타입 자리에 넣는 것. 타입 칸이 여기서 찬다.
- **동적 타입 / 동적 값** — 인터페이스가 지금 들고 있는 타입과 값.
- **`reflect.Value.IsValid()`** — `reflect` 가 값을 만들 수 있었나. `nil` 인터페이스면 `false`.
- **`reflect.Value.IsNil()`** — 값 칸이 `nil` 인가. 포인터·맵·슬라이스·함수·채널·인터페이스에만 물을 수 있다.
- **탐침(probe)** — 도구에게 같은 질문을 여러 모양으로 던져 **답하는 수를 세는** 방식.
  이 주제는 8개를 던져 0개가 답했다.

---

## 더 들어가면

- ★ **`fmt` 가 `nil` 포인터를 어떻게 다루는지**는 이 문서가 **두 판만 던졌다**
  (`Error()` 가 리시버를 읽는 판 · 안 읽는 판). 그 밖의 동사(`%+v`·`%#v`)는 **안 던졌다** —
  정본은 목록의 **42번 주제**다.
- ★ **인터페이스에 담을 때 할당이 생기나**는 **안 쟀다.** `(*T)(nil)` 을 담는 것은
  포인터 한 칸을 복사하는 일이지만 **그 주장은 이 문서가 측정한 것이 아니다**(목록의 **50번 주제**).
- **제네릭에서 `*T` 의 제로값**은 같은 성질을 다른 자리에서 만난다 —
  `var zero T` 가 `T` 가 인터페이스일 때와 포인터일 때 다르다. 이 문서는 **안 던졌다**(목록의 **37번 주제**).
- ★ **`errors.As` 로 찾아진 값이 `nil` 포인터**인 경우를 이 문서는 (4)절에서 한 줄만 보였다.
  그 뒤에 무엇이 되는지는 **안 던졌다** — [24번 주제](../24-error-wrapping-and-errors-is-as-join/)가 정본이다.
- **에디터·언어 서버**가 이 함정을 경고해 주는지는 **근거로 안 썼다.**
  그것은 도구의 기능이지 언어의 것이 아니고, 이 문서는 에디터를 안 열었다.
