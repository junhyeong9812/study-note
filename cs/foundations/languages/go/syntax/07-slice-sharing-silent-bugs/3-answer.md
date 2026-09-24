# go/syntax/07 — 슬라이스 공유로 조용히 틀리는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★ **이 파일의 답은 대부분 「반환값」이 아니라 「그 뒤 원본」에 있다.**
> ★ **근거로 읽을 칸** — 원본이 덮였나, 기반 배열이 같나, 각 도구의 **종료 코드**,
> 컴파일 에러 문장 본문.
> **근거로 읽지 않을 칸** — 기반 배열의 **주소 자체**, `cap` 의 **구체적 수치**(구현 — 06번 주제),
> `go test` 의 **경과 시간**(그래서 `sed` 로 `(초)` 로 바꿔 받았고, 자른 명령을 배너에 적었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ `all` 의 네 번째 칸이 **`4` 에서 `99` 로** 바뀐다

**출력**

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

**왜 그런가**

- `head := all[:3]` 은 `len` **3**, `cap` **6**이다. **뒤를 잘라도 `cap` 은 안 준다** —
  `cap` 은 `low` 만 보기 때문이다(06번 주제 (1)절).
- 여유가 3칸이나 있으니 `append(head, 99)` 는 **제자리에 쓴다.** 그 자리가 `all[3]` 이다.

  > **Otherwise, `append` re-uses the underlying array.**

- 그래서 `head` 는 `[1 2 3 99]`, **`all` 은 `[1 2 3 99 5 6]`** 이 된다.
- `tail := all[3:]` 은 **`[99 5 6]`** — 뒤를 보고 있던 쪽이 오염을 그대로 받는다.
- ★ **`go vet` 은 종료 코드 0** 이다. 한 줄도 안 말한다.

### 2. ★ 반환값은 같고 **원본만 갈린다**

**출력**

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

**왜 그런가**

| | `all` | `cap` | 반환값 | **부른 뒤 `all`** |
|---|---|---|---|---|
| ① | `[1 2 3 4]` | 4 | `[1 2 0]` | **`[1 2 0 4]`** — 덮였다 |
| ② | `[1 2]` | 2 | `[1 2 0]` | **`[1 2]`** — 그대로다 |

- 반환값은 **둘 다 `[1 2 0]`** 으로 같다. 갈린 것은 **원본**이다.
- 갈린 원인을 한 낱말로 — **`cap`**. ①은 `len(head)+1 = 3 <= cap 4` 라 제자리,
  ②는 `3 > 2` 라 재할당이다(06번 주제의 예측식).
- ★★ 테스트의 함정은 이것이다 — **작은 입력일수록 `cap` 이 딱 맞아 재할당이 일어난다.**
  즉 **테스트가 ② 쪽만 만들고 통과한다.** 버그는 `make([]T, n, n+k)` 로 미리 잡은 슬라이스나
  재사용 버퍼처럼 **`cap` 이 남는 실전 입력**에서만 터진다.
- 고치는 법 — 테스트 케이스에 **`cap` 이 남는 입력을 하나 넣는다.**

```text
   ① all = [1 2 3 4]  (cap 4)            ② all = [1 2]  (cap 2)

   head [1 2|3 4]                        head [1 2]
         ^~~~ len 2 · cap 4                    ^~~~ len 2 · cap 2
   append -> 3번 칸에 0 을 쓴다            append -> 새 배열을 잡는다
   all  [1 2 0 4]   ★ 덮였다              all  [1 2]      그대로다

   반환값은 둘 다 [1 2 0] — 같다.
```

### 3. 배열 꼬리에 「d」가 한 벌 더 남는다

**출력**

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

**왜 그런가**

- `out := append(s[:1], s[2:]...)` 는 `[a c d]` 로 **맞게 나온다.** `len` 3, `cap` 4다.
- 그런데 `out[:cap(out)]` 은 **`[a c d d]`** 다. 옮겨쓰기가 앞으로 밀었을 뿐
  **꼬리 칸은 옛 값 그대로**다.
- `s` 라는 이름으로 찍으면 **`[a c d d]`** 가 나온다 — `s` 의 `len` 이 여전히 **4**이기 때문이다.
  ★ **`s` 를 다시 쓰면 지운 것처럼 안 보인다.** 그래서 관용구는 `s = append(…)` 로 **다시 대입**한다.
- `&s[0] == &out[0]` 이 **true** — 같은 배열이다.
- ★ 원소가 **포인터**였다면 더 나쁘다. 꼬리에 남은 한 벌이 **그 객체의 회수를 막는다.**
  고치는 법은 `clear(s[n:])`(**1.21**) 이고 정본은 08번 주제다.

### 4. 돌려받은 것은 맞고 **`src` 는 짓이겨진다**

**출력**

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

**왜 그런가**

- `out := s[:0]` 은 **같은 배열의 길이 0짜리 창**이다. `cap` 은 6 그대로다.
- 거기에 `append` 하면 **앞에서부터 덮어쓴다** — `src[0]`·`src[1]`·`src[2]` 에 2·4·6 이 들어간다.
- 반환값 `[2 4 6]` 은 **맞다.** 그런데 **`src` 가 `[2 4 6 4 5 6]`** 이 됐다.
- `&src[0] == &even[0]` 이 **true**.
- ★ **이 관용구 자체는 틀린 것이 아니다.** Go 에서 「할당 없이 거르기」의 표준 꼴이고,
  **원본을 버려도 될 때** 쓰는 것이다. 틀리는 것은 **원본을 나중에 또 쓰는 코드**다.
- 원본을 살려야 하면 `out := make([]int, 0, len(s))` 로 시작한다.
  「할당을 아낀다」의 대가가 **원본**이라는 것을 알고 써야 한다.

### 5. ★★ **하나도 못 잡는다** — 넷 다 종료 코드 0

**출력**

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

**왜 그런가**

| 도구 | 종료 코드 | 무엇을 봤나 |
|---|---|---|
| `go build` | **0** | 타입·문법 |
| `go vet` | **0** | 의심스러운 꼴의 목록 — 여기 없다 |
| `go test` | **0**(`ok`) | **반환값만** 봤다 |
| `go test -race` | **0**(`ok`) | **고루틴 간** 접근 — 여기는 고루틴이 하나다 |

- `./prog` 는 `Prefix(data, 2) = [1 2 0]` 과 **`그 뒤 data = [1 2 0 4 5]`** 를 찍는다.
  **`3` 이 사라졌다.**
- 테스트가 통과한 이유를 계약으로 말하면 — 테스트가 적은 계약이
  「**`[1 2 0]` 을 돌려준다**」뿐이고 「**인자를 안 건드린다**」가 **계약에 없다.**
  없는 계약은 검사되지 않는다.
- ★★★ `-race` 가 통과하는 이유 — **이것은 데이터 레이스가 아니다.**
  레이스는 두 고루틴이 동기화 없이 같은 자리를 만질 때다.
  여기는 **한 고루틴이 언어가 약속한 대로 쓴 것**이라 검출기가 볼 대상이 아니다.
  (정본은 목록의 **35번 주제**다.)
- 고치는 법은 도구가 아니라 **계약**이다 — 테스트에
  「부른 뒤 인자가 그대로인가」를 한 줄 넣으면 이 버그는 **즉시 빨개진다.**

### 6. `Name` 은 갈리고 `Tags` 는 공유다 — 그리고 `append` 에서 갈린다

**출력**

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

**왜 그런가**

- `b := a` 는 구조체를 **한 겹만** 복사한다.
  - `b.Name = "복사본"` → **`a.Name` 은 그대로**(문자열은 값처럼 군다).
  - `b.Tags[0] = "바뀜"` → **`a.Tags[0]` 도 바뀐다**(헤더만 복사됐다).
- `b.Tags` 에 `append` 하니 `len` 2 `cap` 2 라 **재할당**이 일어난다.
  - `a.Tags` = `[바뀜 y]` (len 2, cap 2)
  - `b.Tags` = `[바뀜 y z]` (len 3, cap 4)
- ★★ 즉 **`append` 하는 그 순간부터 공유가 아니게 된다.**
  같은 필드가 **시점에 따라 공유이기도 아니기도 하다** — 이 주제에서 가장 헷갈리는 모양이다.
- 이 구조체는 `==` 로 비교할 수 **없다.**

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
- 고치는 법 — 필드마다 `slices.Equal`(**1.21**) 또는 `reflect.DeepEqual`.
  깊은 복사가 필요하면 `slices.Clone` 을 **직접** 쓴다(08번 주제).

### 7. 명세를 어긴 것이 없어서 — 도구가 볼 대상이 아니다

**출력** — 없음(왜 문항).

**왜 그런가**

- **이 버그는 명세를 어기지 않는다.** 명세가 이렇게 약속했고 그대로 동작했다.

  > If the capacity of `s` is not large enough … allocates a new …
  > **Otherwise, `append` re-uses the underlying array.**

  틀린 것은 **코드의 의도**지 **언어의 동작**이 아니다.
- `-race` 가 보는 것은 **두 고루틴이 동기화 없이 같은 메모리를 만지는 것**이다.
  이 버그는 **한 고루틴**이므로 원리상 범위 밖이다.
- `go vet` 에 넣기 어려운 이유를 하나 대면 — **`append(s[:i], …)` 는 정상적인 코드에서도 널리 쓰인다.**
  (3)·(4)절의 관용구가 바로 그것이다. 잡으면 **오탐이 쏟아진다.**
  ★ 다만 이것은 추정이고, **이 문서는 vet 의 소스를 읽어 확인하지 않았다.**
- 그러면 무엇으로 막나 — 셋이다.
  - **코드 모양을 아는 것**(이 주제).
  - **`s[:n:n]` 이나 복사로 막는 것**(08번 주제).
  - **테스트에 「인자가 그대로인가」를 계약으로 적는 것**(목록의 **49번 주제**).

### 8. 맵에서 꺼내 붙인 것은 **맵에 안 들어간다**

**출력**

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

**왜 그런가**

- `s := m["k"]` 가 준 것은 **헤더의 복사본**이다. 거기에 `append` 해서 `s` 가 `[1 2 3 4]` 가 돼도
  **`m["k"]` 는 `[1 2 3]`** 이다.
- `m["k"] = append(m["k"], 4)` 로 **다시 넣어야** 반영된다.
- 그런데 `m["k"][0] = 99` 는 **그냥 된다.** 원소 수정은 **기반 배열을 통해** 보이기 때문이다.
- ★ 즉 **원소는 고쳐지고 길이는 안 고쳐진다** — 목록의 **05번 주제** (3)절의
  함수 매개변수와 **똑같은 구조**다. 맵 값도, 매개변수도, 구조체 필드도 전부 **헤더가 복사되는 자리**다.
- ★ 키가 여럿이었다면 마지막 줄을 **정렬해서** 찍어야 한다 —
  Go 는 맵 순회를 **일부러 무작위화**하므로 순회 순서를 그대로 실으면 재현이 안 된다.
  이 프로그램은 **키가 하나뿐**이라 그 문제가 성립하지 않는다. 정본은 목록의 **09번 주제**다.

### 9. 명세는 ①·②·④, 도구·구현의 사정은 ③·⑤·⑥

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `cap` 이 남으면 재사용 | **명세 보장** | "Otherwise, `append` re-uses the underlying array." |
| ② | `s[:3]` 의 `cap` 이 6 | **명세 보장** | Slice expressions — `cap` 은 `low` 만 본다 |
| ③ | `go vet` 이 조용하다 | **도구의 사정** | vet 의 검사 목록에 없을 뿐이다. 판이 오르면 생길 수 있다 |
| ④ | 슬라이스 필드가 있으면 `==` 불가 | **명세 보장** | "Struct types are comparable if all their field types are comparable." |
| ⑤ | `append` 뒤 `cap` 이 2 → 4 | **구현(gc)** | 명세는 "sufficiently large" 까지만(06번 주제) |
| ⑥ | `-race` 가 통과한다 | **검출기의 설계** | 레이스 검출기는 고루틴 간 접근을 본다 |

- ★ ③과 ⑥을 「명세가 허락했다」로 읽으면 안 된다. **도구가 안 보는 것일 뿐**이고,
  ⑥은 **원리상 볼 수 없는 것**이라 성격이 또 다르다.
  ③은 언젠가 생길 수 있고 ⑥은 안 생긴다.

### 10. 셋이 같은 문제를 다른 방식으로 피했다

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Rust** | **파이썬** | **Go** |
|---|---|---|---|
| 같은 모양의 코드 | **컴파일이 거부**한다 | 그냥 된다 | **그냥 된다** |
| 무엇이 막나 | **빌림 규칙** — 가변 별칭이 금지다 | **슬라이스가 복사**라 별칭이 안 생긴다 | **아무것도 안 막는다** |
| `head = all[:3]` 뒤 `head` 를 늘리면 | 슬라이스로는 **길이를 못 늘린다** | `head` 는 **새 리스트**라 `all` 은 그대로 | **`all` 이 덮인다** |
| 사람이 외워야 하나 | 컴파일러가 가르쳐 준다 | 외울 것이 없다 | ★ **외워야 한다** |
| 그 대신 얻은 것 | — | — | **복사 없이 창을 내고 거기서 자란다** |

- Rust 쪽은 [`../../../rust/syntax/10-borrowing-and-aliasing-rules/`](../../../rust/syntax/10-borrowing-and-aliasing-rules/) 와
  [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)
  (「`&mut [T]` 로는 길이를 못 바꾼다」)에 있다.
- 파이썬 쪽은 [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) 5절 —
  `o[:] is o` 가 리스트에서 **`False`** 다(새 객체).
- ★ 세 언어가 **같은 위험을 서로 다른 값으로 샀다** — Rust 는 컴파일러의 복잡도로,
  파이썬은 복사 비용으로, Go 는 **사람의 주의**로 샀다.
  Go 가 얻은 것은 「**공유되는 창이 자란다**」는 편리함이고, 그 값이 이 주제다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **「`cap` 이 남으면 재사용한다」** — 목록의 **06번 주제** (2)절(계약)·(3)절(예측식).
  그 앞의 「헤더가 복사된다」는 목록의 **05번 주제** (3)·(4)절이다.
- **막는 법(`s[:n:n]`·`copy`·`clear`)** — 목록의 **08번 주제**.
- **조용한 실패의 총론** — [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/).
  **그쪽은 분류와 관측 설계까지**, 여기는 **Go 슬라이스 별칭 한 사례**부터다.
- **`-race` 가 실제로 무엇을 잡나** — 목록의 **35번 주제**.
- **「인자가 안 바뀌었나」를 표 기반 테스트로** — 목록의 **49번 주제**.
- **맵 인덱스 식과 순회 순서** — 목록의 **09번 주제**.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| ★ 부분 슬라이스에 `append` (`t07a`) | `go build && ./prog` · `go vet ./...` | 1 | `all` 이 `[1 2 3 99 5 6]` · **vet exit 0** |
| 입력에 따라 갈린다 (`t07b`) | `go build && ./prog` | 1 | 반환값 같고 원본만 갈림 |
| 삭제 관용구의 꼬리 (`t07c`) | 〃 | 1 | 배열이 `[a c d d]` · `&s[0] == &out[0]` 이 true |
| 제자리 필터 (`t07d`) | 〃 | 1 | `src` 가 `[2 4 6 4 5 6]` |
| ★★ 네 도구 (`t07e`) | `go build` · `go vet` · `go test -count=1` · `go test -race -count=1` · `./prog` | 각 1 | **넷 다 exit 0** · 데이터는 `[1 2 0 4 5]` |
| 구조체 얕은 복사 (`t07f`) | `go build && ./prog` | 1 | `Name` 갈림 · `Tags` 공유 · `append` 에서 갈림 |
| 구조체 비교 (`t07h`) | `go build` | 1 | `struct containing []string cannot be compared` |
| 맵 값 슬라이스 (`t07g`) | `go build && ./prog` | 1 | `append` 는 안 반영 · 원소 수정은 반영 |
| 위험한 꼴 넷 (`t07i`) | `go build && ./prog` · `go vet ./...` | 1 | 넷 다 원본이 바뀜 · **vet exit 0** |
| 막는 꼴 셋 (`t07form`) | `go build && ./prog` | 1 | `[1 2 3 0] [1 2 3 0] [1 2 3 0] [1 2 3 0 5 6]` |

**구현·도구에 달린 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| `cap` 의 구체적 수치(2 → 4 등) | **gc 의 성장 전략**(06번 주제) |
| `go vet` 이 **조용한 것** | **vet 의 검사 목록**. 판이 오르면 검사기가 생길 수 있다 |
| `go test` 의 **경과 시간** | 실행마다 다르다 — `sed` 로 `(초)` 로 바꿔 받았고 **자른 명령을 배너에 적었다** |
| `go test` 의 `ok  \tex` 라는 출력 형식 | **go 도구의 출력 형식** |
| 기반 배열의 **주소 자체** | 실행마다 다르다 — 그래서 `&a[0] == &b[0]` 만 찍었다 |
| `-race` 가 통과하는 것 | **검출기의 설계**. 이쪽은 판이 올라도 안 바뀐다(원리상 범위 밖) |
| 「vet 이 오탐 때문에 안 잡는다」는 설명 | **추정이다.** vet 의 소스를 읽어 확인하지 않았다 |
| 고루틴 둘이 같은 배열을 만질 때 | **안 던져 봤다.** 그때는 진짜 레이스이고 정본은 목록의 **35번 주제**다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
