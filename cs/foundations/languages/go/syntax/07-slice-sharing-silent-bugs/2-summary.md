# go/syntax/07 — 슬라이스 공유로 조용히 틀리는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Slice types ·
> Appending to and copying slices · Slice expressions · Comparison operators 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **이 주제의 버그는 전부 「컴파일도 되고 `go vet` 도 조용하고 테스트도 통과하는」 것**이다.
> (5)절에서 **`go build` · `go vet` · `go test` · `go test -race` 넷이 전부 통과하는데
> 데이터가 짓이겨진** 프로그램을 던진다.
> **버전** — 여기 나오는 모든 동작은 1.0부터 같다(3-인덱스 슬라이싱만 **1.2**부터).
> `clear` 는 **1.21**, `slices.Clone`·`slices.Equal` 도 **1.21**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)** | gc 가 그렇게 하는 것 | `cap` 의 수치 · 재할당 뒤의 크기 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · `go vet`·`go test` 의 침묵 |

★ 이 주제의 버그는 **명세대로 동작한 결과**다. 버그인데 **명세 위반이 아니다** —
그래서 도구가 잡아 줄 수 없다. 명세가 보장하는 것은 이 한 줄이다.

> **Otherwise, `append` re-uses the underlying array.**

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 기반 배열의 **주소 자체** | 그래서 `&a[0] == &b[0]` 같은 **동일성**만 찍는다 |
| **흔들린다** | `go test` 의 경과 시간 | 그래서 `sed` 로 `(초)` 로 바꿔 받는다 — 자르는 명령을 **배너에 그대로 적었다** |
| **판이 바뀌면 바뀐다** | `cap` 의 구체적 수치 | gc 의 성장 전략이다(06번 주제) |
| 안 흔들린다 | **덮였나 안 덮였나** — 원본 슬라이스의 값 | 명세가 정한다. 이 주제의 결론이 전부 여기 있다 |
| 안 흔들린다 | `go vet`·`go test`·`-race` 의 **종료 코드 0** | 넷 다 이 버그를 못 본다 |
| 안 흔들린다 | 컴파일 에러 문장 본문 · `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 해당 없음 | 맵 순회 순서 | (7)절에서 맵을 한 번 쓰는데 **키가 하나뿐**이라 순서가 성립하지 않는다 |

## 한눈에 — 쉽게 말하면

**「내 슬라이스에 하나 붙였을 뿐인데 남의 데이터가 바뀐다.」**

05번 주제가 말한 두 가지 중 무서운 쪽이 이것이다 —
**`cap` 이 남으면 `append` 가 제자리에 쓴다.** 그 「제자리」가 **남이 보고 있는 칸**일 수 있다.

| 비유 | 실체 |
|---|---|
| 공책 한 권을 여럿이 나눠 쓴다 | 한 배열을 여러 슬라이스가 공유 |
| 「나는 1\~3쪽만 쓴다」 | `head := all[:3]` |
| 3쪽 다음에 이어 적는다 | `append(head, x)` — **4쪽은 남의 것이었다** |
| 공책이 꽉 차서 새 공책을 산다 | 재할당 — **이때만 남이 안 다친다** |
| 「몇 쪽까지만 쓴다」고 못 박는다 | `all[:3:3]` — **cap 을 자른다**(08번 주제) |
| 아예 복사해 온다 | `copy` / `slices.Clone`(08번 주제) |

- ★ 이 버그의 특징은 **에러가 없다**는 것이다. 값이 틀릴 뿐이다.
- ★★ 게다가 **입력에 따라 났다 안 났다 한다** — `cap` 이 남는 입력에서만 난다((2)절).
  그래서 **테스트가 통과하는 쪽으로만 만들어지기 쉽다.**

```text
   all  [ 1 | 2 | 3 | 4 | 5 | 6 ]      len 6 · cap 6
   head [ 1 | 2 | 3 ]                  len 3 · cap 6   <- cap 이 배열 끝까지다

   append(head, 99)
                     v 여기에 쓴다
   all  [ 1 | 2 | 3 | 99| 5 | 6 ]      <- all[3] 이 4 에서 99 로 바뀌었다
   head [ 1 | 2 | 3 | 99]              len 4

   에러 없음 · 경고 없음 · 테스트 통과.
```

> **별칭(aliasing)** — 서로 다른 이름이 같은 저장소를 가리키는 것.\
> 예: `head` 와 `all` 은 다른 슬라이스지만 **같은 배열의 같은 칸**을 본다.

> **제자리 쓰기(in-place write)** — 새 배열을 안 잡고 기존 배열 칸에 쓰는 것.
> `cap` 이 남을 때 `append` 가 하는 일이다.

> **조용한 실패(silent failure)** — 에러·경고 없이 값만 틀리는 실패.
> 이 주제의 전부다. 총론은 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/)가 정본이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 어떤 코드 모양에서 **남의 데이터가 덮이나** — 코드만 보고 짚어낼 수 있나.
2. 왜 **에러가 안 나나** — 컴파일러·`go vet`·테스트·`-race` 가 각각 무엇을 보고 무엇을 못 보나.
3. 같은 코드가 **어떤 입력에서만 틀리나** — 그 조건을 한 줄로 적을 수 있나.

★ 조용한 실패 일반론은 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/)가 정본이다.
여기는 **Go 슬라이스 별칭이라는 한 사례**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창 — 앞의 셋이 전부 침묵한다

| 창 | 이 버그를 보나 | 왜 |
|---|---|---|
| `go build` | **못 본다** | 타입이 맞다. 문법도 맞다 |
| `go vet` | **못 본다** | 「뜻이 의심스러운 코드」 목록에 없다. 의심스럽지 않다 |
| `go test` | **대개 못 본다** | 테스트가 **반환값만** 보면 통과한다((5)절) |
| `go test -race` | **못 본다** | 경쟁이 아니다. **한 고루틴 안에서 일어나는 정상 동작**이다 |
| ★★ **기반 배열 동일성** | **본다** | `&a[i] == &b[j]` 또는 `unsafe.SliceData` 로 같은 배열인지 묻는다 |

★★★ **`-race` 가 안 잡는다는 것이 이 주제에서 가장 자주 틀리는 전제**다.
데이터 레이스는 **두 고루틴**이 동기화 없이 같은 자리를 만질 때다.
이 버그는 **한 고루틴**이 자기 코드대로 쓴 것이라 레이스가 아니다.

### (1) ★★★ 부분 슬라이스에 `append` — 원본이 덮인다

**언제 쓰나** — 「앞부분만 떼서 넘긴다」를 할 때마다.

```text
===== 소스: t07a.go =====
package main

import "fmt"

func main() {
	all := []int{1, 2, 3, 4, 5, 6}
	head := all[:3]
	fmt.Printf("all  = %v\n", all)
	fmt.Printf("head = all[:3] = %v  len=%d cap=%d\n", head, len(head), cap(head))

	head = append(head, 99)

	fmt.Println()
	fmt.Println("head = append(head, 99) 한 뒤")
	fmt.Printf("head = %v\n", head)
	fmt.Printf("all  = %v   ← 4 가 99 로 덮였다\n", all)

	tail := all[3:]
	fmt.Printf("tail = all[3:] = %v\n", tail)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
all  = [1 2 3 4 5 6]
head = all[:3] = [1 2 3]  len=3 cap=6

head = append(head, 99) 한 뒤
head = [1 2 3 99]
all  = [1 2 3 99 5 6]   ← 4 가 99 로 덮였다
tail = all[3:] = [99 5 6]
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
```

그림 해설 (한 단계씩):

- `head := all[:3]` 은 `len` 3 **`cap` 6**이다. **뒤를 잘라도 `cap` 은 안 준다**(06번 주제 (1)절).
- `append(head, 99)` 는 여유가 있으니 **제자리에 쓴다.** 그 자리가 `all[3]` 이다.
- 결과 — `all` 이 `[1 2 3 99 5 6]` 이 됐다. **`4` 가 사라졌다.**
- `tail := all[3:]` 로 보면 `[99 5 6]` — **뒤를 보고 있던 쪽이 오염을 그대로 받는다.**
- ★ **`go vet` 이 종료 코드 0** 이다. 한 줄도 안 말한다.

비용 — 없다. **그래서 문제다.** 비용이 있으면 눈에 띄었을 것이다.

### (2) ★★ 같은 코드가 입력에 따라 갈린다

**언제 쓰나** — 「우리 테스트는 통과하는데 운영에서 깨진다」를 설명해야 할 때.

```text
===== 소스: t07b.go =====
package main

import "fmt"

// addTag 는 받은 슬라이스 뒤에 0 을 하나 붙여 돌려준다.
func addTag(s []int) []int { return append(s, 0) }

func run(name string, all []int) {
	head := all[:2]
	fmt.Printf("%s\n", name)
	fmt.Printf("  부르기 전 all = %v  len=%d cap=%d   head = all[:2] = %v\n",
		all, len(all), cap(all), head)
	got := addTag(head)
	fmt.Printf("  addTag(head)  = %v\n", got)
	fmt.Printf("  부른 뒤   all = %v\n", all)
}

func main() {
	run("① head 뒤에 여유가 있는 경우 (cap 4)", []int{1, 2, 3, 4})
	fmt.Println()
	run("② head 뒤에 여유가 없는 경우 (cap 2)", []int{1, 2})
	fmt.Println()
	fmt.Println("같은 함수 · 같은 관용구인데 원본이 한쪽만 바뀐다. 갈린 것은 cap 하나다.")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① head 뒤에 여유가 있는 경우 (cap 4)
  부르기 전 all = [1 2 3 4]  len=4 cap=4   head = all[:2] = [1 2]
  addTag(head)  = [1 2 0]
  부른 뒤   all = [1 2 0 4]

② head 뒤에 여유가 없는 경우 (cap 2)
  부르기 전 all = [1 2]  len=2 cap=2   head = all[:2] = [1 2]
  addTag(head)  = [1 2 0]
  부른 뒤   all = [1 2]

같은 함수 · 같은 관용구인데 원본이 한쪽만 바뀐다. 갈린 것은 cap 하나다.
(exit 0)
```

그림 해설 (한 단계씩):

- `addTag` 는 **단 한 줄**짜리 함수다(`return append(s, 0)`). 두 경우 모두 **반환값은 `[1 2 0]` 으로 같다.**
- 그런데 **원본은 갈린다.**
  - `cap` 4짜리에서는 `all` 이 `[1 2 0 4]` 로 **덮였다.**
  - `cap` 2짜리에서는 `all` 이 `[1 2]` 로 **그대로다.**
- ★★ 갈린 것은 **`cap` 하나**다. 코드는 한 글자도 안 다르다.
- ★★★ 실무에서 이것이 왜 나쁜가 — **테스트는 보통 작은 입력으로 쓴다.**
  작은 입력은 `cap` 이 딱 맞아 재할당이 일어나고, **그래서 버그가 안 난다.**
  큰 입력·재사용 버퍼·`make` 로 미리 잡은 슬라이스에서만 터진다.
- 06번 주제의 예측식이 그대로 판정식이다 — **`len(s) + 붙일 개수 <= cap(s)` 면 남이 다친다.**

비용 — 없다.

### (3) ★★ 삭제 관용구의 꼬리

**언제 쓰나** — `append(s[:i], s[i+1:]...)` 로 원소를 지울 때. 아주 흔한 관용구다.

```text
===== 소스: t07c.go =====
package main

import "fmt"

func main() {
	s := []string{"a", "b", "c", "d"}
	i := 1
	fmt.Printf("지우기 전 s = %v  len=%d cap=%d\n", s, len(s), cap(s))

	out := append(s[:i], s[i+1:]...)

	fmt.Printf("append(s[:1], s[2:]...) = %v  len=%d cap=%d\n", out, len(out), cap(out))
	fmt.Printf("원본 배열을 cap 까지 펴 보면 %v   ← 끝에 \"d\" 가 남아 있다\n", out[:cap(out)])
	fmt.Printf("s 라는 이름으로는 %v  (s 의 len 은 그대로 4 다)\n", s)
	fmt.Println()
	fmt.Println("s 와 out 의 첫 칸이 같은 자리인가 :", &s[0] == &out[0])
}
===== 명령: go build -trimpath -o prog . && ./prog =====
지우기 전 s = [a b c d]  len=4 cap=4
append(s[:1], s[2:]...) = [a c d]  len=3 cap=4
원본 배열을 cap 까지 펴 보면 [a c d d]   ← 끝에 "d" 가 남아 있다
s 라는 이름으로는 [a c d d]  (s 의 len 은 그대로 4 다)

s 와 out 의 첫 칸이 같은 자리인가 : true
(exit 0)
```

그림 해설 (한 단계씩):

- 관용구는 제대로 동작한다 — `[a c d]` 가 나온다. **반환값은 맞다.**
- 그런데 **기반 배열은 `[a c d d]`** 다. **마지막 칸에 `"d"` 가 한 벌 더 남아 있다.**
- 게다가 `s` 라는 이름으로 찍으면 **`[a c d d]`** 다 — `s` 의 `len` 은 여전히 4이기 때문이다.
  **`s` 를 계속 쓰면 지워지지 않은 것처럼 보인다.**
- `&s[0] == &out[0]` 이 **true** 다. 둘은 같은 배열이다.
- ★ 두 가지가 따로 위험하다.
  - ① **`s = append(s[:i], s[i+1:]...)` 로 받지 않으면** 지운 게 아니다.
  - ② 원소가 **포인터**면 꼬리에 남은 한 벌이 **회수를 막는다**(08번 주제에서 `clear` 로 지운다).

비용 — 옮기는 만큼. 꼬리 정리는 **공짜가 아니라 한 줄 더 쓰는 일**이다.

### (4) ★★ 제자리 필터가 원본을 짓이긴다

**언제 쓰나** — 「할당 없이 거른다」는 관용구를 쓸 때.

```text
===== 소스: t07d.go =====
package main

import "fmt"

// keepEven 은 짝수만 남긴다 — 널리 쓰이는 「할당 없는 필터」 관용구다.
func keepEven(s []int) []int {
	out := s[:0]
	for _, v := range s {
		if v%2 == 0 {
			out = append(out, v)
		}
	}
	return out
}

func main() {
	src := []int{1, 2, 3, 4, 5, 6}
	fmt.Printf("거르기 전 src = %v\n", src)

	even := keepEven(src)

	fmt.Printf("돌려받은 것    = %v\n", even)
	fmt.Printf("거른 뒤 src    = %v   ← 원본이 짓이겨졌다\n", src)
	fmt.Printf("배열 전체      = %v\n", even[:cap(even)])
	fmt.Println("같은 배열인가  :", &src[0] == &even[0])
}
===== 명령: go build -trimpath -o prog . && ./prog =====
거르기 전 src = [1 2 3 4 5 6]
돌려받은 것    = [2 4 6]
거른 뒤 src    = [2 4 6 4 5 6]   ← 원본이 짓이겨졌다
배열 전체      = [2 4 6 4 5 6]
같은 배열인가  : true
(exit 0)
```

그림 해설 (한 단계씩):

- `out := s[:0]` 은 **같은 배열의 길이 0짜리 창**이다. 거기에 `append` 하면 **앞에서부터 덮어쓴다.**
- 돌려받은 것은 `[2 4 6]` 으로 **맞다.** 그런데 **`src` 가 `[2 4 6 4 5 6]`** 이 됐다.
- `&src[0] == &even[0]` 이 **true** — 같은 배열이다.
- ★ 이 관용구 자체는 **틀린 것이 아니다.** Go 위키가 권하는 꼴이고, **원본을 버려도 될 때** 쓰는 것이다.
  틀리는 것은 **원본을 나중에 또 쓰는 코드**다.
- 고치는 법 — 원본을 살려야 하면 **`out := make([]int, 0, len(s))`** 로 새 배열을 잡는다.
  「할당을 아낀다」의 대가가 **원본**이라는 것을 알고 써야 한다.

비용 — 할당 0. 그 대가가 원본이다.

### (5) ★★★ 왜 에러가 안 나나 — 네 도구가 전부 통과한다

**언제 쓰나** — 「우리는 테스트가 있으니 괜찮다」를 반증해야 할 때.

```text
===== 소스: t07e.go =====
package main

import "fmt"

// Prefix 는 앞 n 개만 남기고 뒤에 표식 0 을 하나 붙여 돌려준다.
func Prefix(s []int, n int) []int {
	return append(s[:n], 0)
}

func main() {
	data := []int{1, 2, 3, 4, 5}
	got := Prefix(data, 2)
	fmt.Println("Prefix(data, 2) =", got)
	fmt.Println("그 뒤 data      =", data)
}
===== 소스: t07e_test.go =====
package main

import "testing"

func TestPrefix(t *testing.T) {
	got := Prefix([]int{1, 2, 3, 4, 5}, 2)
	want := []int{1, 2, 0}
	if len(got) != len(want) {
		t.Fatalf("len(got) = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("got[%d] = %d, want %d", i, got[i], want[i])
		}
	}
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
===== 명령: go test -count=1 ./... 2>&1 | sed -E 's/[0-9]+\.[0-9]+s/(초)/' =====
ok  	ex	(초)
(exit 0)
===== 명령: go test -race -count=1 ./... 2>&1 | sed -E 's/[0-9]+\.[0-9]+s/(초)/' =====
ok  	ex	(초)
(exit 0)
===== 명령: ./prog =====
Prefix(data, 2) = [1 2 0]
그 뒤 data      = [1 2 0 4 5]
(exit 0)
```

그림 해설 (한 단계씩):

- `Prefix` 는 (1)절의 그 한 줄이다 — `return append(s[:n], 0)`.
- **`go build` 통과**(exit 0) · **`go vet` 통과**(exit 0) ·
  **`go test` 통과**(`ok`) · **`go test -race` 통과**(`ok`).
- 그런데 실행해 보면 **`data` 가 `[1 2 0 4 5]`** 다. **`3` 이 사라졌다.**
- ★★ 테스트가 통과한 이유는 하나다 — **반환값만 검사했기 때문**이다.
  `Prefix` 의 계약을 「`[1 2 0]` 을 돌려준다」로만 적었고, **「인자를 안 건드린다」를 안 적었다.**
- ★★★ **`-race` 가 통과하는 것이 핵심**이다. 이것은 레이스가 아니다 —
  **한 고루틴이 언어가 약속한 대로 한 일**이다. 도구가 잡을 수 있는 종류의 버그가 아니다.
- 고치는 법은 **도구가 아니라 계약**이다 — 테스트에 「**부른 뒤 인자가 그대로인가**」를 한 줄 넣는다.
  (그 한 줄이 이 문서의 `./prog` 출력과 같은 일을 한다.)

```text
   go build   ->  통과      타입이 맞다
   go vet     ->  통과      의심스러운 꼴이 아니다
   go test    ->  통과      반환값만 봤다
   -race      ->  통과      고루틴이 하나다
   ------------------------------------------
   기반 배열   ->  ★ 여기서만 보인다
```

비용 — 「테스트 한 줄」이 전부다.

### (6) 구조체 값 복사는 얕다

**언제 쓰나** — 구조체를 값으로 넘기며 「복사했으니 안전하겠지」 할 때.

```text
===== 소스: t07f.go =====
package main

import "fmt"

// Doc 은 문자열 하나와 슬라이스 하나를 가진 평범한 구조체다.
type Doc struct {
	Name string
	Tags []string
}

func main() {
	a := Doc{Name: "원본", Tags: []string{"x", "y"}}
	b := a

	b.Name = "복사본"
	b.Tags[0] = "바뀜"

	fmt.Printf("a = %+v\n", a)
	fmt.Printf("b = %+v\n", b)
	fmt.Println("Name 은 갈렸고 Tags 는 같이 바뀌었다 :", a.Name != b.Name, "/", a.Tags[0] == b.Tags[0])

	b.Tags = append(b.Tags, "z")
	fmt.Println()
	fmt.Println("b.Tags 에 append 한 뒤")
	fmt.Printf("a.Tags = %v (len=%d cap=%d)\n", a.Tags, len(a.Tags), cap(a.Tags))
	fmt.Printf("b.Tags = %v (len=%d cap=%d)\n", b.Tags, len(b.Tags), cap(b.Tags))
	fmt.Println("append 는 b.Tags 만 새 배열로 옮겼다 — 공유가 거기서 끊겼다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
a = {Name:원본 Tags:[바뀜 y]}
b = {Name:복사본 Tags:[바뀜 y]}
Name 은 갈렸고 Tags 는 같이 바뀌었다 : true / true

b.Tags 에 append 한 뒤
a.Tags = [바뀜 y] (len=2 cap=2)
b.Tags = [바뀜 y z] (len=3 cap=4)
append 는 b.Tags 만 새 배열로 옮겼다 — 공유가 거기서 끊겼다
(exit 0)
```

그림 해설 (한 단계씩):

- `b := a` 로 구조체를 복사했다. **`Name` 은 갈렸다** — 문자열은 값처럼 군다.
- 그런데 **`Tags` 는 같이 바뀐다.** 복사된 것은 **슬라이스 헤더**이지 배열이 아니다(05번 주제 (3)절).
- ★ 그다음 `b.Tags` 에 `append` 하니 `cap` 2 → 4 로 **재할당**이 일어나고, **거기서 공유가 끊긴다.**
  `a.Tags` 는 `len` 2 `cap` 2 그대로다.
- ★★ 즉 **한 구조체 안에서 「공유하다가 어느 순간 안 하게」** 된다. 이것이 가장 헷갈리는 모양이다.
- 고치는 법 — 깊은 복사가 필요하면 **필드마다 `slices.Clone`** 해야 한다(08번 주제).
  「복사 생성자」가 없는 언어라 **직접 쓰는 수밖에 없다.**

슬라이스 필드가 있으면 그 구조체는 **`==` 로 비교할 수도 없다.**

```text
===== 소스: t07h.go =====
package main

import "fmt"

// Doc 은 슬라이스 필드를 가진 구조체다.
type Doc struct {
	Name string
	Tags []string
}

func main() {
	a := Doc{Name: "원본", Tags: []string{"x"}}
	b := Doc{Name: "원본", Tags: []string{"x"}}
	fmt.Println(a == b)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t07h.go:14:14: invalid operation: a == b (struct containing []string cannot be compared)
(exit 1)
```

- `invalid operation: a == b (struct containing []string cannot be compared)`.
- 명세: "**Struct types are comparable if all their field types are comparable.**"
  슬라이스는 비교 불가이므로 그 구조체도 비교 불가가 된다.
- 고치는 법 — `slices.Equal`(**1.21**) 로 필드마다, 또는 `reflect.DeepEqual`.

비용 — 얕은 복사는 헤더만큼. 깊은 복사는 원소만큼.

### (7) 맵 값에 `append` 하면 사라진다

**언제 쓰나** — `map[string][]T` 를 쓸 때. 흔한 모양이다.

```text
===== 소스: t07g.go =====
package main

import "fmt"

func main() {
	m := map[string][]int{"k": {1, 2, 3}}

	s := m["k"]
	s = append(s, 4)
	fmt.Println("s = append(m[\"k\"], 4) 한 뒤 m[\"k\"] =", m["k"], " s =", s)

	m["k"] = append(m["k"], 4)
	fmt.Println("m[\"k\"] = append(...) 로 다시 넣으면 m[\"k\"] =", m["k"])

	m["k"][0] = 99
	fmt.Println("m[\"k\"][0] = 99 는 그냥 된다        m[\"k\"] =", m["k"])

	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	fmt.Println("맵의 키(정렬하지 않아도 하나뿐이다) :", keys)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
s = append(m["k"], 4) 한 뒤 m["k"] = [1 2 3]  s = [1 2 3 4]
m["k"] = append(...) 로 다시 넣으면 m["k"] = [1 2 3 4]
m["k"][0] = 99 는 그냥 된다        m["k"] = [99 2 3 4]
맵의 키(정렬하지 않아도 하나뿐이다) : [k]
(exit 0)
```

그림 해설 (한 단계씩):

- `s := m["k"]; s = append(s, 4)` 는 **맵에 안 반영된다.** 맵이 준 것은 **헤더의 복사본**이다.
- `m["k"] = append(m["k"], 4)` 로 **다시 넣어야** 반영된다.
- 그런데 `m["k"][0] = 99` 는 **그냥 된다** — 원소 수정은 기반 배열을 통해 보이기 때문이다.
- ★ 즉 **원소는 고쳐지고 길이는 안 고쳐진다.** 05번 주제 (3)절의 함수 인자와 **똑같은 구조**다.
  맵 값도, 함수 매개변수도, 구조체 필드도 전부 **헤더가 복사되는 자리**다.
- ★ 이 주제에서 맵을 쓰는 곳은 여기뿐이고 **키가 하나뿐**이라 순회 순서 문제가 없다.
  키가 여럿이면 **정렬해서 찍어야 한다** — Go 는 맵 순회를 일부러 무작위화한다(목록의 **09번 주제**).

비용 — 없음. `m[k] = append(m[k], v)` 는 맵 조회가 두 번이다.

### (8) ★ 네 번째 창과 고치는 법

앞의 일곱 절이 전부 같은 한 가지를 말한다 — **「이 둘이 같은 배열을 보나」**.
그것만이 이 버그를 보는 창이다. 창을 만드는 법은 셋이다.

| 창 | 쓰는 법 | 한계 |
|---|---|---|
| 원소 주소 비교 | `&a[0] == &b[0]` | **빈 슬라이스에서 못 쓴다**(인덱스가 패닉) |
| 기반 배열 포인터 | `unsafe.SliceData(a) == unsafe.SliceData(b)` | **1.20+**. `unsafe` 를 들여와야 한다 |
| `cap` 으로 **예측** | `len(s)+k <= cap(s)` | 실무용. **명세가 떠받쳐 준다**(06번 주제 (3)절) |

고치는 법은 두 가지뿐이다. 형태는 아래 (문법) 절에 있고 **정본은 08번 주제**다.

```text
===== 소스: t07form.go =====
package main

import "fmt"

func main() {
	all := []int{1, 2, 3, 4, 5, 6}

	bad := append(all[:3], 0)        // ① 원본을 덮을 수 있다
	safe := append(all[:3:3], 0)     // ② cap 을 잘라 새 배열을 강제한다
	own := make([]int, 3, 4)         //
	copy(own, all[:3])               // ③ 아예 베껴 놓고 시작한다
	own = append(own, 0)             //
	fmt.Println(bad, safe, own, all) // ④ all 은 ① 때문에 이미 바뀌어 있다
}
===== 명령: go build -trimpath -o prog . && ./prog =====
[1 2 3 0] [1 2 3 0] [1 2 3 0] [1 2 3 0 5 6]
(exit 0)
```

- ① `append(all[:3], 0)` — **원본을 덮는다.** 출력 마지막의 `all` 이 `[1 2 3 0 5 6]` 인 것이 그 증거다.
- ② `append(all[:3:3], 0)` — **`cap` 을 잘라** 재할당을 강제한다. 남이 안 다친다.
- ③ `make` + `copy` — **아예 새 배열**에서 시작한다.
- ★ ②와 ③은 결과가 같다(`[1 2 3 0]`). 다른 것은 **비용과 의도**다 —
  ②는 「한 번 더 붙일 때만 복사」이고 ③은 「무조건 복사」다.

**언제 어느 것을 쓰나** — 판단 규칙 한 줄: **남의 슬라이스를 받아 `append` 하면 ②를 붙여라.**
내 것이면 아무것도 안 해도 된다.

## 문법 — 형태와 규칙

### 형태 — 위험한 꼴 넷

```go
// t07i.go
package main

import "fmt"

// remove 는 i번째를 지운다 — 삭제 관용구.
func remove(s []int, i int) []int { return append(s[:i], s[i+1:]...) }

// filter 는 짝수만 제자리에서 거른다.
func filter(s []int) []int {
	out := s[:0]
	for _, v := range s {
		if v%2 == 0 {
			out = append(out, v)
		}
	}
	return out
}

// addTag 는 남의 슬라이스를 받아 붙인다.
func addTag(s []int) []int { return append(s, 0) }

func main() {
	a := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("① append(a[:3], 99) =", append(a[:3], 99))
	b := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("② remove(b, 1)      =", remove(b, 1))
	c := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("③ filter(c)         =", filter(c))
	d := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("④ addTag(d[:2])     =", addTag(d[:2]))
	fmt.Println()
	fmt.Println("넷 다 원본이 바뀌어 있다")
	fmt.Println("  a =", a)
	fmt.Println("  b =", b)
	fmt.Println("  c =", c)
	fmt.Println("  d =", d)
}
```

```text
===== 소스: t07i.go =====
package main

import "fmt"

// remove 는 i번째를 지운다 — 삭제 관용구.
func remove(s []int, i int) []int { return append(s[:i], s[i+1:]...) }

// filter 는 짝수만 제자리에서 거른다.
func filter(s []int) []int {
	out := s[:0]
	for _, v := range s {
		if v%2 == 0 {
			out = append(out, v)
		}
	}
	return out
}

// addTag 는 남의 슬라이스를 받아 붙인다.
func addTag(s []int) []int { return append(s, 0) }

func main() {
	a := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("① append(a[:3], 99) =", append(a[:3], 99))
	b := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("② remove(b, 1)      =", remove(b, 1))
	c := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("③ filter(c)         =", filter(c))
	d := []int{1, 2, 3, 4, 5, 6}
	fmt.Println("④ addTag(d[:2])     =", addTag(d[:2]))
	fmt.Println()
	fmt.Println("넷 다 원본이 바뀌어 있다")
	fmt.Println("  a =", a)
	fmt.Println("  b =", b)
	fmt.Println("  c =", c)
	fmt.Println("  d =", d)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① append(a[:3], 99) = [1 2 3 99]
② remove(b, 1)      = [1 3 4 5 6]
③ filter(c)         = [2 4 6]
④ addTag(d[:2])     = [1 2 0]

넷 다 원본이 바뀌어 있다
  a = [1 2 3 99 5 6]
  b = [1 3 4 5 6 6]
  c = [2 4 6 4 5 6]
  d = [1 2 0 4 5 6]
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
```

- 네 꼴이 한 프로그램에 모여 있다. **반환값은 넷 다 그럴듯하다.**
- 마지막 네 줄이 값이다 — **`a`·`b`·`c`·`d` 가 전부 바뀌어 있다.**
- `go vet` 은 여기서도 **종료 코드 0** 이다.

### 형태 — 막는 꼴 셋

```go
// t07form.go
package main

import "fmt"

func main() {
	all := []int{1, 2, 3, 4, 5, 6}

	bad := append(all[:3], 0)        // ① 원본을 덮을 수 있다
	safe := append(all[:3:3], 0)     // ② cap 을 잘라 새 배열을 강제한다
	own := make([]int, 3, 4)         //
	copy(own, all[:3])               // ③ 아예 베껴 놓고 시작한다
	own = append(own, 0)             //
	fmt.Println(bad, safe, own, all) // ④ all 은 ① 때문에 이미 바뀌어 있다
}
```

규칙 불릿.

- **남의 슬라이스를 받아 `append` 하는 함수는 `s[:n:n]` 을 붙인다.** 이것 하나가 ①·④를 다 막는다.
- **원본을 살려야 하면 제자리 필터를 쓰지 않는다.** `make` 로 새 배열을 잡는다.
- **삭제 관용구는 결과를 다시 대입한다.** 포인터 슬라이스면 꼬리를 `clear` 한다(08번 주제).
- **구조체를 복사해도 슬라이스 필드는 공유다.** 깊은 복사는 직접 쓴다.
- **맵 값 슬라이스는 `m[k] = append(m[k], v)`** 로 다시 넣는다.
- **테스트에 「인자가 안 바뀌었나」를 한 줄 넣는다.** 도구는 안 잡아 준다.

## 어디서 틀리나

### 1. ★★★ 「`-race` 를 켰으니 이런 건 잡힌다」

- (5)절 실측 — **`go test -race` 가 `ok`** 다. 데이터가 짓이겨졌는데도 통과한다.
- 레이스는 **두 고루틴**의 문제다. 이 버그는 **한 고루틴이 언어대로 한 일**이다.
- 고치는 법 — 도구를 늘리지 말고 **계약을 테스트에 적는다.**

### 2. ★★★ 「테스트가 통과하니 괜찮다」

- (5)절 실측 — 반환값만 검사하는 테스트는 **반드시 통과한다.**
- (2)절 실측 — 게다가 **작은 입력에서는 버그가 안 난다.** 테스트가 보통 작은 입력을 쓴다.
- 고치는 법 — 테스트 케이스에 **`cap` 이 남는 입력**을 하나 넣는다(`make([]T, n, n+k)`).

### 3. ★★ 「`s[:3]` 은 3개짜리니까 3개만 건드린다」

- (1)절 실측 — `cap` 이 **6**이다. 뒤를 잘라도 `cap` 은 안 준다.
- 「몇 개를 보나」는 `len` 이고 「몇 개를 건드릴 수 있나」는 `cap` 이다. **둘을 섞어 읽는 것이 뿌리다.**
- 고치는 법 — `s[:3:3]` 으로 **둘을 같게 만든다.**

### 4. ★★ 「`append` 결과를 새 변수로 받았으니 원본은 안전하다」

- (1)·(3)절 실측 — **새 변수로 받아도 배열은 같다.** 변수 이름은 헤더의 이름일 뿐이다.
- 고치는 법 — 안전을 원하면 **배열을 갈라야** 한다(`s[:n:n]` 또는 `copy`).

### 5. ★★ 「구조체를 값으로 넘겼으니 복사됐다」

- (6)절 실측 — `Name` 은 갈리고 **`Tags` 는 공유**다. 복사는 **한 겹**만 일어난다.
- 게다가 `append` 하면 **거기서부터 갈린다** — 같은 필드가 시점에 따라 공유이기도 아니기도 하다.
- 고치는 법 — 깊은 복사를 **손으로** 쓴다. `slices.Clone` 을 필드마다.

### 6. ★ 「맵에서 꺼내 `append` 했으니 맵도 바뀐다」

- (7)절 실측 — **안 바뀐다.** `m[k] = append(m[k], v)` 로 다시 넣어야 한다.
- 헷갈리는 이유는 **원소 수정(`m[k][0] = 99`)은 되기 때문**이다.
- 고치는 법 — 「길이를 바꾸면 다시 넣는다」를 규칙으로 외운다.

### 7. ★ 「삭제 관용구를 썼으니 지워졌다」

- (3)절 실측 — 기반 배열의 꼬리에 **한 벌이 남는다.** 포인터면 **회수도 안 된다.**
- 고치는 법 — 결과를 다시 대입하고, 포인터 슬라이스면 `clear(s[n:])`(**1.21**).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `cap` 이 남으면 `append` 가 **기반 배열을 재사용** | **명세 보장** | "Otherwise, `append` re-uses the underlying array." |
| 그래서 **이웃 슬라이스가 덮인다** | **명세 보장의 결과** | 공유 자체가 명세다 — "A slice therefore shares storage …" |
| `s[:n]` 의 `cap` 이 **안 주는** 것 | **명세 보장** | Slice expressions — `cap` 은 `low` 만 본다 |
| 슬라이스 필드가 있는 구조체가 **비교 불가** | **명세 보장** | "Struct types are comparable if all their field types are comparable." |
| 맵 값 슬라이스가 **복사본**인 것 | **명세 보장** | 맵 인덱스 식의 결과는 값이다 |
| `copy`·`append` 가 **겹쳐도 결과가 정해진** 것 | **명세 보장** | "the result is independent of whether the memory referenced by the arguments overlaps" |
| **어느 입력에서 터지는가** | **명세 보장 + 구현** | 갈림은 명세(`cap`), **`cap` 의 수치**는 구현 |
| `go vet` 이 **한 줄도 안 말하는** 것 | **도구(go vet)의 관찰** | 판이 오르면 검사기가 생길 수 있다 |
| `go test -race` 가 **통과하는** 것 | **검출기의 설계** | 레이스 검출기는 **고루틴 간** 접근을 본다 |
| `cap` 2 → 4 같은 수치 | **구현(gc)** | 06번 주제 |

★ 이 주제의 사고는 전부 「**명세대로 동작한 결과**」다. 명세를 어긴 것이 없으므로
**도구가 잡아 줄 여지가 원리상 없다.** 남는 것은 **코드 모양을 아는 것**뿐이다 —
그래서 이 주제가 「관용구」로 분류돼 있다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 남의 슬라이스를 받아 붙인다 | **`append(s[:n:n], …)`** | 재할당을 강제해 남을 안 다친다 |
| 내가 만든 슬라이스에 붙인다 | 그냥 `append` | 공유하는 쪽이 없다 |
| 원본을 살리며 거른다 | `make([]T, 0, len(s))` | 제자리 필터는 원본을 먹는다 |
| 원본을 버려도 된다 | `out := s[:0]` | 할당 0. **의도를 주석으로 적는다** |
| 원소를 지운다 | `s = append(s[:i], s[i+1:]...)` + 꼬리 정리 | 결과를 **다시 대입**한다 |
| 포인터·큰 값의 슬라이스를 줄인다 | `clear(s[n:])` 뒤 `s = s[:n]` | 꼬리가 회수를 막는다(**1.21**) |
| 구조체를 진짜로 복사한다 | 필드마다 `slices.Clone` | 값 복사는 한 겹만이다 |
| 맵 값 슬라이스에 붙인다 | `m[k] = append(m[k], v)` | 다시 넣어야 반영된다 |
| 슬라이스를 비교한다 | `slices.Equal` | `==` 는 컴파일 에러다 |
| 이 버그를 테스트로 막는다 | **「부른 뒤 인자가 그대로인가」** | 도구는 못 잡는다 |

판단 규칙 두 줄.

- **「이 슬라이스는 내 것인가」를 먼저 물어라.** 남의 것이면 `[:n:n]` 을 붙인다.
- **「에러가 안 났다」는 근거가 아니다.** 이 주제에서는 에러가 원리상 안 난다.

## 핵심 문장

- ★★★ **`cap` 이 남으면 `append` 는 제자리에 쓴다** — 그 자리가 남의 칸일 수 있다.
  `all[:3]` 에 하나 붙였더니 `all[3]` 이 덮였다.
- ★★★ **`go build`·`go vet`·`go test`·`go test -race` 넷이 전부 통과하는데 데이터가 짓이겨진다.**
  명세를 어긴 것이 없으니 도구가 잡을 수 없다.
- ★★ **같은 코드가 입력에 따라 났다 안 났다 한다.** `cap` 이 남는 입력에서만 난다 —
  **작은 테스트 입력에서는 안 난다.**
- `s[:3]` 의 `cap` 은 3이 아니라 **배열 끝까지**다. 「몇 개를 보나」와 「몇 개를 건드릴 수 있나」가 다르다.
- 삭제 관용구는 **꼬리에 한 벌을 남긴다.** 포인터면 회수도 막는다.
- 제자리 필터(`s[:0]`)는 **원본을 먹는 대가로** 할당을 아끼는 것이다.
- **구조체 값 복사는 한 겹**이다. 슬라이스 필드는 공유이고, `append` 하는 순간 갈린다.
- 맵 값 슬라이스는 **원소 수정은 되고 길이 변경은 안 된다** — 함수 매개변수와 같은 구조다.
- 막는 법은 둘뿐이다 — **`s[:n:n]`** 또는 **복사**. 정본은 08번 주제다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 07번)
- 목록의 **05번 주제**(배열과 슬라이스) — **그쪽은 「헤더가 복사된다」는 사실까지**,
  여기는 **그 사실이 버그가 되는 모양**부터
- 목록의 **06번 주제**(`len`/`cap`과 `append`) — **그쪽은 예측식과 성장 전략까지**,
  여기는 **예측을 안 한 코드가 어떻게 되는지**부터
- 목록의 **08번 주제**(`copy`·3-인덱스·메모리 유지) — **막는 법의 정본**
- 목록의 **09번 주제**(맵) — (7)절의 맵 인덱스 식과 순회 순서의 정본
- 목록의 **35번 주제**(데이터 레이스와 `-race`) — **그쪽은 검출기가 무엇을 보는지까지**,
  여기는 **이 버그가 왜 그 범위 밖인지**만
- 목록의 **49번 주제**(`testing`) — 「인자가 안 바뀌었나」를 표 기반 테스트로 쓰는 법
- [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) —
  **그쪽은 조용한 실패의 총론(분류·관측 설계)까지**, 여기는 **Go 슬라이스 별칭이라는 한 사례**부터
- [`../../../rust/syntax/10-borrowing-and-aliasing-rules/`](../../../rust/syntax/10-borrowing-and-aliasing-rules/) —
  **그쪽은 별칭을 컴파일러가 거부해서 이 버그가 성립하지 않는다**,
  여기는 **별칭이 합법이라 사람이 막아야 한다**

## 용어 풀이

- **별칭(aliasing)** — 다른 이름이 같은 저장소를 가리키는 것.
- **제자리 쓰기(in-place write)** — 새 배열 없이 기존 칸에 쓰는 것.
- **삭제 관용구** — `append(s[:i], s[i+1:]...)`. 원소 하나를 빼는 Go 의 관용구.
- **제자리 필터** — `out := s[:0]` 뒤 `append`. 할당 없이 거르는 관용구.
- **깊은 복사(deep copy)** — 안쪽까지 베끼는 것. Go 에는 자동으로 해 주는 장치가 없다.
- **데이터 레이스(data race)** — 두 고루틴이 동기화 없이 같은 자리를 만지는 것.
  **이 주제의 버그는 레이스가 아니다.**
- **조용한 실패(silent failure)** — 에러·경고 없이 값만 틀리는 실패.

---

## 더 들어가면

- 표준 라이브러리도 이 함정을 안다. `append` 로 받은 슬라이스를 오래 들고 있어야 하는 API 는
  대개 **복사해서 보관**한다. 남의 슬라이스를 저장하는 라이브러리를 쓸 때
  **「이게 복사하나」를 문서에서 확인**하는 습관이 필요하다.
- `bytes.Buffer`·`strings.Builder` 는 내부 슬라이스를 **밖에 안 내준다.**
  `Bytes()` 가 내부 배열을 주는 것은 알려진 예외라 문서가 경고한다. 정본은 목록의 **11번 주제**다.
- 「함수가 인자를 안 건드린다」를 타입으로 강제할 방법이 Go 에는 **없다.**
  Rust 는 `&` 와 `&mut` 로 그것을 타입에 적는다
  ([`../../../rust/syntax/10-borrowing-and-aliasing-rules/`](../../../rust/syntax/10-borrowing-and-aliasing-rules/)).
  Go 는 **주석과 테스트로** 적는 수밖에 없다.
- `go vet` 에 이런 검사가 **없는 이유**는 오탐이 너무 많기 때문으로 보인다 —
  `append(s[:i], …)` 는 **정상적인 코드에서도 널리 쓰인다.**
  다만 이것은 추정이고, **이 문서는 vet 의 소스를 읽어 확인하지 않았다.**
- 이 주제의 모든 예제는 **한 고루틴**이다. 고루틴 둘이 같은 배열을 만지면 그때는 **진짜 레이스**이고
  `-race` 가 잡는다. 정본은 목록의 **35번 주제**다.
