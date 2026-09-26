# go/syntax/18 — 임베딩과 필드·메서드 승격 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Struct types(Embedded field · Promoted) ·
> Selectors(depth) · Composite literals(Struct literals) · Method sets · Interface types 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 승격 규칙 자체는 **1.0부터 같다.** 이 주제에 판 경계가 **하나** 있다 —
> **승격된 필드 이름을 구조체 리터럴의 키로 쓰는 것이 1.27부터**다((8)절에서 `go.mod` 를 바꿔 증명한다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | 에러 문구 · 패닉 문구 · `reflect` 가 돌려주는 모양 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ 이 주제는 **거의 전부 명세 보장**이다. 「얕은 쪽이 이긴다」도 「같은 깊이면 모호하다」도
「승격된 메서드의 리시버가 안쪽 타입이다」도 **전부 명세의 문장**이다 — 컴파일러 사정이 아니다.
★★ 구현인 칸은 **에러·패닉 문구**와 **`encoding/json` 이 임베딩을 다루는 방식**뿐이다.
뒤엣것은 **명세가 아니라 패키지의 계약**이라는 점이 중요하다((7)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄의 `pc=0x…` · 스택의 `goroutine N` 과 `+0x…` | 빌드 산출물·런타임에 달렸다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 패닉 메시지 본문 · 종료 코드 `2` | 런타임이 정한 문장이다 |
| 안 흔들린다 | `reflect` 의 `NumField`·`FieldByName` 의 **`Index` 배열** | 타입 구조가 정한다 |
| 안 흔들린다 | `%T` 가 찍는 타입 이름 · `==` 의 참거짓 | 〃 |
| 안 흔들린다 | `json.Marshal` 이 낸 **키 순서** | ★ Go 의 JSON 은 **필드 선언 순서**로 낸다 — 맵이 아니라 구조체이기 때문이다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 찍지 않는다 |
| 해당 없음 | 포인터 값 | 주소는 한 번도 안 찍는다 — `==` 로 **같나 다르나**만 묻는다((1)절) |

★ **JSON 키 순서를 「안 흔들리는 칸」에 둔 것은 구조체를 마샬할 때만** 그렇다.
맵을 마샬하면 `encoding/json` 이 **키를 정렬**하므로 그것도 결정적이지만, 이 문서는 구조체만 던진다.

## 한눈에 — 쉽게 말하면

**임베딩은 「필드 이름을 안 적은 필드」다.** 그게 전부다.
그러면 **타입 이름이 곧 필드 이름**이 되고, 안쪽의 필드·메서드를 **바깥 이름으로도 부를 수 있게** 된다.
그것을 **승격(promotion)** 이라 부른다.

★★★ **상속이 아니다.** 상속이면 안쪽 메서드가 바깥의 재정의를 되불러야 하는데, **안 부른다.**

| 비유 | 실체 |
|---|---|
| 서랍 안에 상자를 넣고 **상자 이름을 안 적는다** | **임베딩** `struct{ Base }` — 필드 이름이 `Base` 가 된다 |
| 상자 속 물건을 서랍에서 바로 꺼낸다 | **승격** — `outer.Name` 이 `outer.Base.Name` 을 가리킨다 |
| 서랍에도 같은 이름의 물건이 있으면 | **얕은 쪽이 이긴다** — 서랍 것이 나온다 |
| 상자 둘에 같은 이름이 있으면 | **모호** — 컴파일 에러. 어느 상자인지 적어야 한다 |
| 상자가 제 일을 할 때 **서랍을 모른다** | ★★★ **승격 메서드의 리시버는 안쪽 타입**이다 |
| 상자를 **포인터로** 넣는다 | `*Base` 임베딩 — 안 채우면 `nil` 이라 승격 필드에서 패닉 |

```text
   type Dog struct { Animal; Age int }

   ┌──────────── Dog ────────────┐
   │ Animal ┌──────────────────┐ │   깊이 0 : Age
   │        │ Name string      │ │   깊이 1 : Animal.Name → d.Name  (승격)
   │        │ Speak() / Intro()│ │           Animal.Speak()          (승격)
   │        └──────────────────┘ │
   │ Age int                     │
   └─────────────────────────────┘

   d.Name  ==  d.Animal.Name      <- 같은 칸이다 (== 로 확인한다)
   d.Intro() 안의 a.Speak() 는 Animal.Speak() 다  <- Dog 를 못 본다
```

> **임베딩(embedding)** — 구조체 필드를 **이름 없이 타입만** 적는 것.\
> 예: `struct{ Base }` — 필드 이름은 `Base` 다.

> **승격(promotion)** — 임베딩한 타입의 필드·메서드를 **바깥 타입의 선택자로** 쓸 수 있게 되는 것.\
> 예: `d.Name` 이 `d.Animal.Name` 을 가리킨다.

> **깊이(depth)** — 그 이름에 닿기까지 지난 임베딩 필드의 수.\
> 예: `Dog` 자신의 `Age` 는 깊이 0, `Dog.Animal.Name` 은 깊이 1이다.

- Java 와 다른 점 — 자바의 `extends` 는 **재정의가 되불린다**(가상 디스패치).
  Go 의 승격은 **되불리지 않는다**((1)절이 출력으로 못 박는다).
  그래서 Go 에는 **`super` 가 없다** — 안쪽을 부르려면 **필드 이름을 적는다**(`d.Animal.Speak()`).
- Kotlin 과 다른 점 — 코틀린의 **`by` 위임**
  ([`../../../kotlin/syntax/21-class-delegation-by/`](../../../kotlin/syntax/21-class-delegation-by/))이
  가장 가까운데, 그쪽은 **인터페이스를 구현하고 컴파일러가 전달 메서드를 만든다.**
  Go 는 **필드 하나**이고 전달 메서드가 생기지 않는다 — **선택자 규칙**일 뿐이다.
- Rust 와 다른 점 — Rust 에는 임베딩이 **없다.** `Deref` 로 흉내 내는 관용이 있지만
  트레이트 구현은 여전히 **`impl Trait for T` 를 적어야** 한다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **임베딩은 무엇을 만드는가** — 필드 하나인가, 상속인가.
2. **이름이 겹치면 어느 쪽이 이기는가** — 그리고 안 이기면 무엇이 나오나.
3. **승격이 인터페이스 만족으로 이어지는가** — 바깥 타입이 안쪽의 인터페이스를 만족하나.

★ 「합성이냐 상속이냐」라는 설계 논의는 이 주제가 아니다 —
[`../../../../oop-basics/`](../../../../oop-basics/)가 정본이고, 여기는 **Go 의 승격 규칙**만 본다.
★ 메서드 집합의 정본은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/)다 —
여기는 **임베딩이 그 집합을 어떻게 키우나** 한 줄까지만 본다((5)절).

## 동작 방식

### (0) ★★ 이 주제가 쓰는 네 창 — `javap` 같은 것이 없다

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 어느 메서드가 불렸나 · 어느 필드가 바뀌었나 | **승격 자체는 안 보인다** — 그냥 필드처럼 보인다 |
| ★★★ **컴파일 에러** | **이름 충돌**. 모호하면 컴파일러가 말한다 | **일부러 충돌을 만들어야** 나온다 |
| ★★ **`reflect` 의 `Index`** | **평평해 보이는 이름의 실제 경로**(`[0 0 1]`) | 승격 메서드의 리시버까지는 안 말해 준다 |
| **런타임 패닉** | `*T` 임베딩을 안 채운 것 | 통과한 실행은 아무 말도 안 한다 |
| ★ **부적용인 창 — 바이트코드 덤프** | Go 에는 `javap -c` 에 해당하는 **교재용 덤프가 없다** | `go tool objdump` 는 기계어라 승격을 읽어 내기에 부적합하다 |

★★★ **그래서 이 주제의 증명은 「일부러 깨뜨리기」와 「리시버 타입 찍기」 둘이다.**
「승격됐다」를 직접 보여 주는 도구가 없으므로 —
**① 이름을 충돌시켜 컴파일러가 말하게 하고**((3)절),
**② 승격 메서드 안에서 `%T` 로 리시버를 찍고**((1)절),
**③ `reflect` 로 필드 경로를 뜬다**((4)절).

### (1) ★★★ 임베딩은 상속이 아니다 — 리시버를 찍어 본다

**언제 쓰나** — 임베딩을 처음 볼 때. **이 주제에서 가장 자주 틀리는 자리다.**

```text
===== 소스: t18a.go =====
package main

import "fmt"

type Animal struct {
	Name string
}

func (a Animal) Speak() string { return "..." }

func (a Animal) Intro() string {
	return fmt.Sprintf("%s 왈 %q  (이 메서드의 리시버 타입 = %T)", a.Name, a.Speak(), a)
}

type Dog struct {
	Animal // 임베딩 — 필드 이름이 없다. 타입 이름이 곧 필드 이름이다
	Age    int
}

func (d Dog) Speak() string { return "멍" }

func main() {
	d := Dog{Animal: Animal{Name: "바둑이"}, Age: 3}

	fmt.Println("── 필드 승격 ──")
	fmt.Println("  d.Name        =", d.Name)
	fmt.Println("  d.Animal.Name =", d.Animal.Name)
	fmt.Println("  같은 칸인가   :", &d.Name == &d.Animal.Name)

	fmt.Println("── 메서드 승격 ──")
	fmt.Println("  d.Speak()        =", d.Speak(), " ← Dog 자신의 것")
	fmt.Println("  d.Animal.Speak() =", d.Animal.Speak(), " ← 승격된 것은 이쪽")

	fmt.Println("── ★ 상속이 아니다 : 승격된 Intro 안의 a.Speak() 는 Dog 를 못 본다 ──")
	fmt.Println("  d.Intro() =", d.Intro())

	fmt.Println("── 이름 있는 필드로 두면 승격이 아예 없다 ──")
	type Cat struct {
		A   Animal // 이름이 붙었다 — 임베딩이 아니다
		Age int
	}
	c := Cat{A: Animal{Name: "나비"}, Age: 2}
	fmt.Println("  c.A.Name =", c.A.Name, " · c.A.Intro() =", c.A.Intro())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 필드 승격 ──
  d.Name        = 바둑이
  d.Animal.Name = 바둑이
  같은 칸인가   : true
── 메서드 승격 ──
  d.Speak()        = 멍  ← Dog 자신의 것
  d.Animal.Speak() = ...  ← 승격된 것은 이쪽
── ★ 상속이 아니다 : 승격된 Intro 안의 a.Speak() 는 Dog 를 못 본다 ──
  d.Intro() = 바둑이 왈 "..."  (이 메서드의 리시버 타입 = main.Animal)
── 이름 있는 필드로 두면 승격이 아예 없다 ──
  c.A.Name = 나비  · c.A.Intro() = 나비 왈 "..."  (이 메서드의 리시버 타입 = main.Animal)
(exit 0)
```

그림 해설 (한 단계씩):

- **필드 승격** — `d.Name` 과 `d.Animal.Name` 이 같고, **`&d.Name == &d.Animal.Name` 이 `true`** 다.
  **두 이름이 한 칸**이다. 명세:

  > A field declared with a type but no explicit field name is called an **embedded field**. …
  > **The unqualified type name acts as the field name.**

  > A field or method f of an embedded field in a struct x is called **promoted** if x.f is a legal
  > selector that denotes that field or method f. **Promoted fields act like ordinary fields of a struct.**

- **메서드 승격** — `d.Speak()` 는 `Dog` 자신의 것이라 `"멍"` 이고,
  승격된 것은 `d.Animal.Speak()` 쪽이라 `"..."` 다.
- ★★★ **그리고 `d.Intro()` 가 `바둑이 왈 "..."` 다.**
  `Intro` 는 `Animal` 의 메서드이고 그 안의 `a.Speak()` 는 **`Animal.Speak()`** 를 부른다 —
  `Dog.Speak()` 를 **안 부른다.** 리시버 타입을 같이 찍었다: **`main.Animal`**.
- ★★ **이것이 상속과 갈리는 자리 전부다.** 자바라면 `Dog` 가 `speak()` 를 재정의한 순간
  `intro()` 안의 호출이 `Dog.speak()` 로 간다. **Go 에는 그 되부름이 없다.**
  승격은 **선택자의 축약**이지 디스패치 표가 아니다.
- 마지막 줄 — **이름 있는 필드로 두면 승격이 아예 없다.** `c.Name` 은 컴파일도 안 되고
  `c.A.Name` 이라야 한다. **필드 이름을 안 적는 것 하나**가 전부를 가른다.

```text
   자바 (extends)                     Go (임베딩)

   Animal.intro()                      Animal.Intro()
        └ this.speak()                      └ a.Speak()
             ↓ 가상 디스패치                     ↓ 그냥 Animal 의 것
          Dog.speak()  "멍"                  Animal.Speak()  "..."
```

비용 — 없다. 승격은 컴파일 시점의 이름 해석이다.

### (2) 얕은 쪽이 이긴다 — 깊이 규칙

**언제 쓰나** — 바깥과 안쪽에 같은 이름이 있을 때.

```text
===== 소스: t18b.go =====
package main

import "fmt"

type Base struct {
	Name string
}

func (Base) Tag() string { return "Base" }

type Mid struct {
	Base        // 깊이 1 에 Base.Name 이 있다
	Name string // 깊이 0 — 얕은 쪽
}

func (Mid) Tag() string { return "Mid" }

type Deep struct {
	Mid // Mid.Name 은 깊이 1, Mid.Base.Name 은 깊이 2
}

func main() {
	m := Mid{Base: Base{Name: "밑"}, Name: "가운데"}

	fmt.Println("── 얕은 쪽이 이긴다 (깊이 0 대 깊이 1) ──")
	fmt.Println("  m.Name       =", m.Name)
	fmt.Println("  m.Base.Name  =", m.Base.Name)
	fmt.Println("  m.Tag()      =", m.Tag())
	fmt.Println("  m.Base.Tag() =", m.Base.Tag())

	d := Deep{Mid: m}
	fmt.Println("── 두 겹 밑에서도 규칙은 같다 (깊이 1 대 깊이 2) ──")
	fmt.Println("  d.Name          =", d.Name)
	fmt.Println("  d.Mid.Name      =", d.Mid.Name)
	fmt.Println("  d.Mid.Base.Name =", d.Mid.Base.Name)
	fmt.Println("  d.Tag()         =", d.Tag())

	fmt.Println("── 승격은 「이름이 하나뿐인 가장 얕은 깊이」에서만 일어난다 ──")
	d.Name = "바뀜"
	fmt.Println("  d.Name 에 쓰면 어디가 바뀌나 :",
		"d.Mid.Name =", d.Mid.Name, "· d.Mid.Base.Name =", d.Mid.Base.Name)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 얕은 쪽이 이긴다 (깊이 0 대 깊이 1) ──
  m.Name       = 가운데
  m.Base.Name  = 밑
  m.Tag()      = Mid
  m.Base.Tag() = Base
── 두 겹 밑에서도 규칙은 같다 (깊이 1 대 깊이 2) ──
  d.Name          = 가운데
  d.Mid.Name      = 가운데
  d.Mid.Base.Name = 밑
  d.Tag()         = Mid
── 승격은 「이름이 하나뿐인 가장 얕은 깊이」에서만 일어난다 ──
  d.Name 에 쓰면 어디가 바뀌나 : d.Mid.Name = 바뀜 · d.Mid.Base.Name = 밑
(exit 0)
```

그림 해설 (한 단계씩):

- `Mid` 에는 자기 `Name`(깊이 0)과 `Base.Name`(깊이 1)이 있다. **`m.Name` 은 `"가운데"`** 다.
  메서드도 같다 — **`m.Tag()` 가 `"Mid"`** 다.
- 명세가 깊이를 정의하고 규칙을 적는다.

  > The number of embedded fields traversed to reach f is called its **depth** in T.
  > The depth of a field or method f declared in T is **zero**.

  > For a value x of type T or \*T where T is not a pointer or interface type,
  > **x.f denotes the field or method at the shallowest depth in T where there is such an f.**
  > **If there is not exactly one f with shallowest depth, the selector expression is illegal.**

- `Deep` 에서도 같다 — `d.Name` 은 깊이 1의 `Mid.Name`(`"가운데"`)이고
  깊이 2의 `Mid.Base.Name`(`"밑"`)은 **가려진다.**
- ★★ 마지막 줄이 요점이다 — **`d.Name = "바뀜"` 이 고친 것은 `d.Mid.Name` 뿐**이고
  `d.Mid.Base.Name` 은 `"밑"` 그대로다. **가려진 칸은 그대로 살아 있다.**
  ★ 가려졌다고 사라진 것이 아니다 — **이름만 안 닿을 뿐**이다.
- ★ 「이긴다」는 낱말이 오해를 부른다 — **재정의가 아니다.**
  `Base.Tag()` 는 여전히 제 몸으로 살아 있고 `m.Base.Tag()` 로 부를 수 있다.

비용 — 없다.

### (3) ★★★ 같은 깊이면 모호하다 — 컴파일러가 말하게 하라

**언제 쓰나** — 임베딩 둘을 같은 타입에 넣을 때. **이 주제를 보이는 첫째 방법이다.**

```text
===== 소스: t18c.go =====
package main

import "fmt"

type L struct {
	Name string
}

func (L) Tag() string { return "L" }

type R struct {
	Name string
}

func (R) Tag() string { return "R" }

type Both struct {
	L // 깊이 1
	R // 깊이 1 — 같은 깊이에 Name 과 Tag 가 둘씩 있다
}

func main() {
	b := Both{L: L{Name: "왼"}, R: R{Name: "오"}}

	fmt.Println(b.L.Name, b.R.Name) // ① 이름을 밝히면 된다
	fmt.Println(b.L.Tag(), b.R.Tag())

	fmt.Println(b.Name)  // ② 모호하다
	fmt.Println(b.Tag()) // ③ 모호하다
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18c.go:28:16: ambiguous selector b.Name
./t18c.go:29:16: ambiguous selector b.Tag
(exit 1)
```

그림 해설 (한 단계씩):

- `Both` 는 `L` 과 `R` 을 둘 다 **깊이 1** 에 갖는다. 둘 다 `Name` 과 `Tag` 를 갖는다.
- **`b.L.Name`·`b.R.Name` 은 통과한다** — 어느 쪽인지 적었기 때문이다(에러가 25\~26번 줄에 없다).
- ★★★ **`b.Name` 과 `b.Tag()` 만 `ambiguous selector` 로 막힌다.**
  명세의 "**If there is not exactly one f with shallowest depth, the selector expression is illegal**"
  이 그대로 에러가 된 것이다.
- ★★ **주목할 것은 「타입 선언 자체는 통과했다」** 는 점이다.
  `type Both struct{ L; R }` 는 합법이고, **쓰는 자리에서만** 막힌다.
  ★ 그래서 **라이브러리를 업그레이드했더니 내 타입이 깨지는** 일이 생길 수 있다 —
  임베딩한 두 타입 중 한쪽에 메서드가 하나 늘면 그렇다.
- ★ 명세가 **타입 선언이 막히는 경우도** 따로 적는다 — 그것은 **필드 이름 자체가 겹칠 때**다.

  > The following declaration is illegal because field names must be unique in a struct type:
  > `struct { T; *T; *P.T }` — T conflicts with embedded field \*T and \*P.T

  즉 `struct{ L; L }` 나 `struct{ L; *L }` 은 **선언에서** 막히고,
  `struct{ L; R }` 는 **선언은 되고 선택자에서** 막힌다. **두 자리가 다르다.**

비용 — 없다. 전부 컴파일 시점이다.

### (4) ★★ `reflect` 로 필드 경로를 뜬다 — 평평해 보이지만 중첩이다

**언제 쓰나** — 「승격된 필드가 진짜 그 타입의 필드인가」를 물을 때.

```text
===== 소스: t18d.go =====
package main

import (
	"fmt"
	"reflect"
)

type Base struct {
	Name string
	Code int
}

type Mid struct {
	Base
	Name string
}

type Deep struct {
	Mid
	Extra bool
}

type L struct{ Dup string }
type R struct{ Dup string }

type Both struct {
	L
	R
}

func main() {
	t := reflect.TypeOf(Deep{})
	fmt.Println("── 평평해 보이지만 중첩이다 : 바깥 타입의 필드는 둘뿐 ──")
	fmt.Println("  Deep.NumField() =", t.NumField())
	for i := range t.NumField() {
		f := t.Field(i)
		fmt.Printf("    [%d] %-6s %-8v anonymous=%v\n", i, f.Name, f.Type, f.Anonymous)
	}

	fmt.Println("── FieldByName 은 경로를 Index 로 돌려준다 ──")
	for _, name := range []string{"Extra", "Name", "Code"} {
		f, ok := t.FieldByName(name)
		fmt.Printf("    %-6s ok=%-6v Index=%v  깊이=%d\n", name, ok, f.Index, len(f.Index))
	}

	fmt.Println("── 모호한 이름은 ok=false 로 돌아온다 (컴파일 에러와 같은 판정) ──")
	tb := reflect.TypeOf(Both{})
	f, ok := tb.FieldByName("Dup")
	fmt.Printf("    Both.Dup ok=%v Index=%v\n", ok, f.Index)
	fl, okl := tb.FieldByName("L")
	fmt.Printf("    Both.L   ok=%v Index=%v\n", okl, fl.Index)

	fmt.Println("── Index 로 실제 값을 꺼내 본다 ──")
	d := Deep{Mid: Mid{Base: Base{Name: "밑", Code: 7}, Name: "가운데"}, Extra: true}
	v := reflect.ValueOf(d)
	fn, _ := t.FieldByName("Name")
	fc, _ := t.FieldByName("Code")
	fmt.Printf("    Index=%v -> %q\n", fn.Index, v.FieldByIndex(fn.Index))
	fmt.Printf("    Index=%v -> %v\n", fc.Index, v.FieldByIndex(fc.Index))
	fmt.Printf("    d.Name=%q  d.Mid.Base.Name=%q\n", d.Name, d.Mid.Base.Name)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 평평해 보이지만 중첩이다 : 바깥 타입의 필드는 둘뿐 ──
  Deep.NumField() = 2
    [0] Mid    main.Mid anonymous=true
    [1] Extra  bool     anonymous=false
── FieldByName 은 경로를 Index 로 돌려준다 ──
    Extra  ok=true   Index=[1]  깊이=1
    Name   ok=true   Index=[0 1]  깊이=2
    Code   ok=true   Index=[0 0 1]  깊이=3
── 모호한 이름은 ok=false 로 돌아온다 (컴파일 에러와 같은 판정) ──
    Both.Dup ok=false Index=[]
    Both.L   ok=true Index=[0]
── Index 로 실제 값을 꺼내 본다 ──
    Index=[0 1] -> "가운데"
    Index=[0 0 1] -> 7
    d.Name="가운데"  d.Mid.Base.Name="밑"
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`Deep.NumField()` 가 2**다. `Mid` 와 `Extra` 둘뿐이다 —
  **승격된 `Name`·`Code` 는 `Deep` 의 필드가 아니다.** 선택자가 닿을 뿐이다.
- `FieldByName` 이 **경로를 `Index` 배열로** 돌려준다 —
  `Extra` 는 `[1]`, `Name` 은 `[0 1]`, `Code` 는 **`[0 0 1]`** 이다.
  ★ **`Code` 는 두 겹을 지나야 닿는다** — 그 사실이 선택자 `d.Code` 에는 안 보인다.
- ★★ **모호한 이름은 `ok=false` 로 돌아온다** — `Both.Dup` 이 `ok=false`, `Index=[]` 다.
  (3)절의 컴파일 에러와 **같은 판정**을 런타임 쪽 도구가 내놓는 것이다.
  ★ 「에러를 안 내고 조용히 `false`」이므로 **`reflect` 를 쓰는 코드에서는 이 자리가 조용해진다.**
- `v.FieldByIndex(fn.Index)` 로 **경로를 따라 실제 값**을 꺼낼 수 있다 — `"가운데"` 와 `7`.
  그리고 `d.Name` 과 `d.Mid.Base.Name` 이 여전히 갈라져 있는 것이 같이 찍힌다.

```text
   선택자가 보여 주는 것        reflect 가 보여 주는 것

   d.Extra                      Index=[1]
   d.Name                       Index=[0 1]
   d.Code                       Index=[0 0 1]   <- 두 겹 안쪽이다
        ↑ 셋이 똑같아 보인다          ↑ 깊이가 전부 다르다
```

비용 — `reflect` 호출이다. **이 문서는 그 비용을 재지 않았다.**

### (5) ★★ 인터페이스 임베딩과, 임베딩이 인터페이스를 만족시키는 것

**언제 쓰나** — 19·20번 주제로 넘어가기 직전.

```text
===== 소스: t18e.go =====
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

type Greeter interface{ Greet() string }
type Counter interface{ Count() int }

// ① 인터페이스 임베딩 — 메서드 집합의 합집합이다
type GreetCounter interface {
	Greeter
	Counter
}

type Core struct{ n int }

func (c Core) Greet() string { return "안녕" }
func (c Core) Count() int    { return c.n }

// ② 구조체 임베딩 — 바깥이 안쪽의 인터페이스를 그대로 만족한다
type Wrapper struct {
	Core
	Extra string
}

// ③ 인터페이스를 구조체에 임베딩 — 「일부만 바꿔 끼우기」 관용구
type OnlyGreet struct {
	Greeter // 필드 이름이 Greeter 다. 값은 넣지 않으면 nil
}

func main() {
	var gc GreetCounter = Wrapper{Core: Core{n: 3}, Extra: "ㄱ"}
	fmt.Println("① 바깥 타입이 두 인터페이스를 다 만족한다 :", gc.Greet(), gc.Count())
	fmt.Printf("   인터페이스에 담긴 동적 타입 : %T\n", gc)

	var g Greeter = Wrapper{}
	fmt.Println("② 임베딩한 타입의 인터페이스도 그대로 :", g.Greet())

	og := OnlyGreet{Greeter: Core{}}
	fmt.Println("③ 인터페이스 필드를 채우면 그리로 간다 :", og.Greet())

	fmt.Println("④ io.ReadWriter 도 두 인터페이스의 임베딩이다")
	var rw io.ReadWriter = struct {
		io.Reader
		io.Writer
	}{Reader: strings.NewReader("hi\n"), Writer: os.Stdout}
	n, _ := io.Copy(rw, rw)
	fmt.Println("   io.Copy 가 옮긴 바이트 :", n)

	fmt.Fprintln(os.Stderr, "-- ⑤ 인터페이스 필드를 안 채우면 nil 이다. 이제 부른다 --")
	var empty OnlyGreet
	fmt.Println(empty.Greet())
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
① 바깥 타입이 두 인터페이스를 다 만족한다 : 안녕 3
   인터페이스에 담긴 동적 타입 : main.Wrapper
② 임베딩한 타입의 인터페이스도 그대로 : 안녕
③ 인터페이스 필드를 채우면 그리로 간다 : 안녕
④ io.ReadWriter 도 두 인터페이스의 임베딩이다
hi
   io.Copy 가 옮긴 바이트 : 3
-- ⑤ 인터페이스 필드를 안 채우면 nil 이다. 이제 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4a11c9]

goroutine 1 [running]:
main.main()
	ex/t18e.go:56 +0x409
(exit 2)
```

그림 해설 (한 단계씩):

- ① **인터페이스 임베딩은 메서드 집합의 합집합**이다.
  `GreetCounter` 는 `Greeter` 와 `Counter` 를 담고, `Wrapper` 가 **둘 다** 만족한다.
  담긴 동적 타입은 **`main.Wrapper`** 다 — 안쪽 `Core` 가 아니다.
- ② ★★★ **바깥 타입이 안쪽의 인터페이스를 그대로 만족한다.**
  `Wrapper` 는 `Greet` 을 **안 적었는데** `Greeter` 다. 명세가 승격 메서드를 메서드 집합에 넣는다.

  > Given a struct type S and a type name T, promoted methods are included in the method set of the
  > struct as follows: **If S contains an embedded field T, the method sets of S and \*S both include
  > promoted methods with receiver T.** The method set of \*S also includes promoted methods with receiver \*T.

  ★ **이것이 이 주제가 19·20번으로 이어지는 다리다.**
- ③ **인터페이스를 구조체에 임베딩**할 수도 있다(`struct{ Greeter }`).
  그러면 **필드 이름이 `Greeter`** 이고, 넣은 값으로 호출이 간다.
- ④ **`io.ReadWriter` 도 인터페이스 임베딩**이다. 익명 구조체에 `io.Reader`·`io.Writer` 를
  임베딩해 **그 자리에서 `io.ReadWriter` 를 만들었다** — `io.Copy` 가 3바이트를 옮긴다.
- ★★ ⑤ **인터페이스 필드를 안 채우면 `nil`** 이고 부르면 패닉한다 —
  `panic: runtime error: invalid memory address or nil pointer dereference`, **종료 코드 2**.
  명세: "If x is of interface type and has the value nil, **calling or evaluating the method x.f
  causes a run-time panic.**"
  ★ 그래서 ③의 관용구(「일부만 바꿔 끼우기」)는 **안 바꾼 메서드를 부르면 죽는다**는 대가가 있다.

비용 — 인터페이스를 거치는 호출은 간접 호출이다. **이 문서는 재지 않았다.**

### (6) ★ 포인터 임베딩 — 메서드 집합이 달라진다

**언제 쓰나** — `*Base` 를 임베딩할지 고를 때.

```text
===== 소스: t18g.go =====
package main

import (
	"fmt"
	"os"
	"reflect"
)

type Base struct{ Name string }

func (b Base) Val() string  { return "Val:" + b.Name }
func (b *Base) Ptr() string { return "Ptr:" + b.Name }

type ByValue struct{ Base } // 값으로 임베딩
type ByPtr struct{ *Base }  // 포인터로 임베딩

func main() {
	fmt.Println("── 값 임베딩과 포인터 임베딩의 메서드 집합 (19번 주제로 이어진다) ──")
	for _, t := range []reflect.Type{
		reflect.TypeOf(ByValue{}), reflect.TypeOf(&ByValue{}),
		reflect.TypeOf(ByPtr{}), reflect.TypeOf(&ByPtr{}),
	} {
		names := make([]string, 0, t.NumMethod())
		for i := range t.NumMethod() {
			names = append(names, t.Method(i).Name)
		}
		fmt.Printf("  %-12v NumMethod=%d %v\n", t, t.NumMethod(), names)
	}

	bp := ByPtr{Base: &Base{Name: "ㄱ"}}
	fmt.Println("── 포인터 임베딩은 필드도 승격한다 ──")
	fmt.Println("  bp.Name =", bp.Name, " · bp.Val() =", bp.Val(), " · bp.Ptr() =", bp.Ptr())

	fmt.Fprintln(os.Stderr, "-- 임베딩한 포인터를 안 채우면 nil 이다. 이제 승격 필드를 읽는다 --")
	var empty ByPtr
	fmt.Println(empty.Name)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
── 값 임베딩과 포인터 임베딩의 메서드 집합 (19번 주제로 이어진다) ──
  main.ByValue NumMethod=1 [Val]
  *main.ByValue NumMethod=2 [Ptr Val]
  main.ByPtr   NumMethod=2 [Ptr Val]
  *main.ByPtr  NumMethod=2 [Ptr Val]
── 포인터 임베딩은 필드도 승격한다 ──
  bp.Name = ㄱ  · bp.Val() = Val:ㄱ  · bp.Ptr() = Ptr:ㄱ
-- 임베딩한 포인터를 안 채우면 nil 이다. 이제 승격 필드를 읽는다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4ef230]

goroutine 1 [running]:
main.main()
	ex/t18g.go:36 +0x570
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **첫 네 줄이 이 절의 본체다.**

| 타입 | `NumMethod` | 들어 있는 것 |
|---|---|---|
| `ByValue`(값 임베딩) | **1** | `Val` |
| `*ByValue` | **2** | `Ptr` · `Val` |
| `ByPtr`(포인터 임베딩) | **2** | `Ptr` · `Val` |
| `*ByPtr` | **2** | `Ptr` · `Val` |

- 명세의 두 조항이 그대로다.

  > **If S contains an embedded field T**, the method sets of S and \*S both include promoted methods
  > with receiver T. **The method set of \*S also includes promoted methods with receiver \*T.**

  > **If S contains an embedded field \*T**, the method sets of **S and \*S both** include promoted
  > methods with receiver **T or \*T**.

- ★★ 즉 **`*T` 로 임베딩하면 값 타입까지 포인터 리시버 메서드를 얻는다.**
  이것이 값 임베딩과 갈리는 유일한 자리이고, **정본은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/)** 다.
- **포인터 임베딩도 필드를 승격한다** — `bp.Name` 이 된다.
- ★ 대가는 마지막 줄이다 — **안 채우면 `nil`** 이고 승격 필드를 읽는 순간 패닉한다.
  값 임베딩에는 그 위험이 없다(제로값이 쓸 만하다).
- ★ 명세가 임베딩 필드의 꼴을 제한한다 —
  "An embedded field must be specified as a type name T or as a **pointer to a non-interface type name \*T**,
  and T itself **may not be a pointer type** or type parameter."
  즉 `**T` 는 안 되고, **인터페이스의 포인터**(`*io.Reader`)도 안 된다.

비용 — 포인터 임베딩은 8바이트 + 역참조 한 번이다. **이 문서는 재지 않았다.**

### (7) ★★ `json` 태그와 임베딩이 만나면 — 네 모양이 나온다

**언제 쓰나** — 임베딩한 구조체를 직렬화할 때.

```text
===== 소스: t18f.go =====
package main

import (
	"encoding/json"
	"fmt"
)

type Meta struct {
	ID   int    `json:"id"`
	Kind string `json:"kind"`
}

type FlatDoc struct { // ① 임베딩 — 평평해진다
	Meta
	Title string `json:"title"`
}

type NamedDoc struct { // ② 이름 있는 필드 — 중첩된다
	Meta  Meta   `json:"meta"`
	Title string `json:"title"`
}

type TaggedDoc struct { // ③ 임베딩에 태그를 주면 다시 중첩된다
	Meta  `json:"meta"`
	Title string `json:"title"`
}

type L struct {
	Dup string `json:"dup"`
}

type R struct {
	Dup string `json:"dup"`
}

type Clash struct { // ④ 같은 깊이에서 JSON 이름이 겹치면
	L
	R
	Title string `json:"title"`
}

type Shadow struct { // ⑤ 얕은 쪽이 있으면 그쪽이 이긴다
	Meta
	Kind string `json:"kind"`
}

func main() {
	m := Meta{ID: 1, Kind: "ㄱ"}
	p := func(tag string, v any) {
		b, err := json.Marshal(v)
		fmt.Printf("  %-10s %s   err=%v\n", tag, b, err)
	}
	fmt.Println("── 같은 데이터를 다섯 모양으로 ──")
	p("FlatDoc", FlatDoc{Meta: m, Title: "ㄷ"})
	p("NamedDoc", NamedDoc{Meta: m, Title: "ㄷ"})
	p("TaggedDoc", TaggedDoc{Meta: m, Title: "ㄷ"})
	p("Clash", Clash{L: L{Dup: "왼"}, R: R{Dup: "오"}, Title: "ㄷ"})
	p("Shadow", Shadow{Meta: m, Kind: "얕은쪽"})

	fmt.Println("── 되읽기 ──")
	var f FlatDoc
	err := json.Unmarshal([]byte(`{"id":9,"kind":"ㄴ","title":"ㄹ"}`), &f)
	fmt.Printf("  FlatDoc 되읽기 : %+v err=%v\n", f, err)

	fmt.Println("── ④ 는 에러가 아니다 : 겹친 두 필드가 조용히 빠졌을 뿐이다 ──")
	var c Clash
	err = json.Unmarshal([]byte(`{"dup":"들어갈까","title":"ㄹ"}`), &c)
	fmt.Printf("  Clash 되읽기 : L.Dup=%q R.Dup=%q Title=%q err=%v\n", c.L.Dup, c.R.Dup, c.Title, err)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 같은 데이터를 다섯 모양으로 ──
  FlatDoc    {"id":1,"kind":"ㄱ","title":"ㄷ"}   err=<nil>
  NamedDoc   {"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}   err=<nil>
  TaggedDoc  {"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}   err=<nil>
  Clash      {"title":"ㄷ"}   err=<nil>
  Shadow     {"id":1,"kind":"얕은쪽"}   err=<nil>
── 되읽기 ──
  FlatDoc 되읽기 : {Meta:{ID:9 Kind:ㄴ} Title:ㄹ} err=<nil>
── ④ 는 에러가 아니다 : 겹친 두 필드가 조용히 빠졌을 뿐이다 ──
  Clash 되읽기 : L.Dup="" R.Dup="" Title="ㄹ" err=<nil>
(exit 0)
```

그림 해설 (한 단계씩):

- 같은 데이터가 **다섯 모양**으로 나온다.

| 타입 | 나온 JSON | 왜 |
|---|---|---|
| `FlatDoc`(임베딩) | `{"id":1,"kind":"ㄱ","title":"ㄷ"}` | **평평해진다** — 승격 규칙을 따라간다 |
| `NamedDoc`(이름 있는 필드) | `{"meta":{…},"title":"ㄷ"}` | 임베딩이 아니므로 **중첩** |
| `TaggedDoc`(임베딩 + 태그) | `{"meta":{…},"title":"ㄷ"}` | ★ **태그를 붙이면 다시 중첩된다** |
| `Clash`(같은 깊이 충돌) | `{"title":"ㄷ"}` | ★★★ **둘 다 조용히 빠진다** |
| `Shadow`(얕은 쪽이 있음) | `{"id":1,"kind":"얕은쪽"}` | 얕은 쪽이 이긴다 — 선택자 규칙과 같다 |

- ★★★ **`Clash` 가 이 절의 본체다.** `dup` 이라는 JSON 이름이 같은 깊이에 둘 있으니
  **양쪽 다 나가지 않는다.** 그리고 **`err` 는 `<nil>`** 이다 — 에러가 아니다.
- 되읽기도 같다 — `{"dup":"들어갈까"}` 를 넣어도 **`L.Dup` 과 `R.Dup` 이 둘 다 빈 문자열**이고
  `err` 는 여전히 `<nil>` 이다. **조용히 버려진다.**
- ★★ **(3)절과 견주면 성질이 갈린다** —
  선택자에서는 **컴파일 에러**로 시끄럽게 막히는데, JSON 에서는 **아무 말 없이 빠진다.**
  같은 「같은 깊이 충돌」인데 **한쪽은 컴파일러가, 한쪽은 라이브러리가** 처리하기 때문이다.
- ★★★ **그리고 이것은 명세가 아니라 `encoding/json` 의 계약**이다.
  다른 직렬화 라이브러리는 다르게 굴 수 있다. **층을 갈라 적어야 하는 자리다.**

비용 — 없다(반사 비용은 안 쟀다).

### (8) ★ 승격된 필드를 리터럴의 키로 — 1.27부터

**언제 쓰나** — 임베딩한 타입의 필드를 리터럴에서 채울 때.

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: t18h.go =====
package main

import "fmt"

type Object struct{ Name, Color string }

type Point3D struct {
	Object
	X, Y, Z float64
}

type Line struct {
	Object
	P, Q Point3D
}

func main() {
	// ★ 1.27 부터 — 승격된 필드 이름을 리터럴의 키로 쓸 수 있다
	l := Line{Name: "대각", Q: Point3D{X: 1, Y: 1, Z: 1}}
	fmt.Printf("  l.Name=%q  l.Object.Name=%q  l.Q.Z=%v\n", l.Name, l.Object.Name, l.Q.Z)
	fmt.Printf("  l = %+v\n", l)

	// 1.26 이하의 적는 법 — 임베딩한 타입 이름을 키로 쓴다
	old := Line{Object: Object{Name: "대각"}, Q: Point3D{X: 1, Y: 1, Z: 1}}
	fmt.Println("  두 꼴이 같은가 :", l == old)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  l.Name="대각"  l.Object.Name="대각"  l.Q.Z=1
  l = {Object:{Name:대각 Color:} P:{Object:{Name: Color:} X:0 Y:0 Z:0} Q:{Object:{Name: Color:} X:1 Y:1 Z:1}}
  두 꼴이 같은가 : true
(exit 0)
```

**같은 소스를 `go.mod` 한 줄만 바꿔 던지면 갈린다.**

```text
===== 소스: go.mod =====
module ex

go 1.26
===== 소스: t18i.go =====
package main

import "fmt"

type Object struct{ Name, Color string }

type Line struct {
	Object
	P int
}

func main() {
	l := Line{Name: "대각", P: 1} // 승격된 필드를 키로
	fmt.Println(l)
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18i.go:13:12: use of promoted field Object.Name in struct literal of type Line requires go1.27 or later (-lang was set to go1.26; check go.mod)
(exit 1)
```

그림 해설 (한 단계씩):

- ★★ **`Line{Name: "대각", …}` 이 된다** — `Name` 은 `Line` 의 필드가 아니라 `Object.Name` 이다.
  명세가 그 규칙에 판 표시를 달고 있다.

  > Each key must be a valid field selector **[Go 1.27]** for a (possibly promoted) field of the struct;
  > the key selects that field.

- ★★★ **`go.mod` 의 `go` 한 줄을 `go 1.26` 으로 내리면 컴파일이 막힌다** —
  `use of promoted field Object.Name in struct literal of type Line requires go1.27 or later
  (-lang was set to go1.26; check go.mod)`.
  ★ **소스는 한 글자도 안 바뀌었다.** 갈린 것은 **언어 판 그 자체**다.
  그래서 이 블록은 **`go.mod` 를 소스로 함께 싣는다** — 없으면 재현이 안 된다.
- 1.26 이하의 적는 법은 **임베딩한 타입 이름을 키로** 쓰는 것이다(`Object: Object{Name: "대각"}`).
  두 꼴이 **`==` 로 같다**(`true`).

**그런데 승격 키에는 제약이 둘 있다.**

```text
===== 소스: t18j.go =====
package main

import "fmt"

type Object struct{ Name, Color string }

type ByPtr struct {
	*Object // 포인터로 임베딩
	N       int
}

type Line struct {
	Object
	P int
}

func main() {
	// ① 포인터 임베딩을 지나는 승격 키는 안 된다
	a := ByPtr{Name: "ㄱ", N: 1}
	fmt.Println(a)

	// ② 임베딩한 타입과 그 안의 승격 필드를 같이 적을 수 없다
	b := Line{Object: Object{Color: "검정"}, Name: "대각"}
	fmt.Println(b)
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18j.go:19:13: invalid implicit pointer indirection to reach Name
./t18j.go:23:45: cannot specify promoted field Name and enclosing embedded field Object
(exit 1)
```

- ① **포인터 임베딩을 지나는 승격 키는 안 된다** — `invalid implicit pointer indirection to reach Name`.
  명세: "**The types of the embedded fields (if any) traversed to reach a selected field must not be
  pointer types.**"
  ★ (6)절에서 **선택자로는 `bp.Name` 이 됐다** — **리터럴 키에서만** 막힌다. 두 자리의 규칙이 다르다.
- ② **임베딩한 타입과 그 안의 승격 필드를 같이 적을 수 없다** —
  `cannot specify promoted field Name and enclosing embedded field Object`.
  명세: "A key must not denote a promoted field inside an embedded struct **if that struct is also
  specified by another key.**"
  둘 다 적으면 **어느 쪽이 나중인지**가 뜻을 정하게 되므로 아예 막는다.

비용 — 없다. 전부 컴파일 시점이다.

## 문법 — 형태와 규칙

### 형태

```go
// t18form.go
package main

import "fmt"

type Base struct{ N int }

func (b Base) Hello() string { return "base" }

type Named interface{ Hello() string }

// ① 임베딩 = 필드 이름을 안 적은 필드. 타입 이름이 곧 필드 이름이다
type Outer struct {
	Base       // ② 필드 이름은 Base
	*Extra     // ③ 포인터도 임베딩된다. 필드 이름은 Extra
	Named      // ④ 인터페이스도 임베딩된다. 필드 이름은 Named
	M      int // ⑤ 보통 필드
}

type Extra struct{ E string }

// ⑥ 인터페이스 임베딩 — 메서드 집합의 합집합
type Greeter interface {
	Named
	fmt.Stringer
}

type G struct{ Base }

func (G) String() string { return "G" }

func main() {
	o := Outer{Base: Base{N: 1}, Extra: &Extra{E: "ㄱ"}, Named: Base{N: 2}, M: 3}
	fmt.Println(o.N, o.E, o.M)       // ⑦ 승격된 필드
	fmt.Println(o.Base.N, o.Extra.E) // ⑧ 필드 이름으로도 닿는다
	fmt.Println(o.Named.Hello())     // ⑨ 임베딩한 인터페이스로 간다

	var g Greeter = G{} // ⑩ 바깥이 임베딩한 타입의 메서드로 만족된다
	fmt.Println(g.Hello(), g.String())
}
```

```text
===== 소스: t18form.go =====
package main

import "fmt"

type Base struct{ N int }

func (b Base) Hello() string { return "base" }

type Named interface{ Hello() string }

// ① 임베딩 = 필드 이름을 안 적은 필드. 타입 이름이 곧 필드 이름이다
type Outer struct {
	Base       // ② 필드 이름은 Base
	*Extra     // ③ 포인터도 임베딩된다. 필드 이름은 Extra
	Named      // ④ 인터페이스도 임베딩된다. 필드 이름은 Named
	M      int // ⑤ 보통 필드
}

type Extra struct{ E string }

// ⑥ 인터페이스 임베딩 — 메서드 집합의 합집합
type Greeter interface {
	Named
	fmt.Stringer
}

type G struct{ Base }

func (G) String() string { return "G" }

func main() {
	o := Outer{Base: Base{N: 1}, Extra: &Extra{E: "ㄱ"}, Named: Base{N: 2}, M: 3}
	fmt.Println(o.N, o.E, o.M)       // ⑦ 승격된 필드
	fmt.Println(o.Base.N, o.Extra.E) // ⑧ 필드 이름으로도 닿는다
	fmt.Println(o.Named.Hello())     // ⑨ 임베딩한 인터페이스로 간다

	var g Greeter = G{} // ⑩ 바깥이 임베딩한 타입의 메서드로 만족된다
	fmt.Println(g.Hello(), g.String())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1 ㄱ 3
1 ㄱ
base
base G
(exit 0)
```

규칙 불릿.

- **임베딩은 필드 이름을 안 적은 필드**다. **타입 이름이 곧 필드 이름**이다.
- 꼴은 **`T`** 또는 **`*T`**(T 는 포인터가 아니어야 한다). **인터페이스도 임베딩된다.**
- **승격된 필드·메서드는 보통 필드·메서드처럼 쓴다.** 원래 자리로도 닿는다(`o.Base.N`).
- **선택자는 가장 얕은 깊이 하나**를 고른다. **같은 깊이에 둘이면 컴파일 에러**다.
- **타입 선언이 막히는 것은 필드 이름이 겹칠 때뿐**이다(`struct{ T; *T }`).
- **승격 메서드의 리시버는 안쪽 타입**이다. **되부름이 없다 — 상속이 아니다.**
- **인터페이스 임베딩은 메서드 집합의 합집합**이다.
- **`*T` 임베딩은 값 타입에도 `*T` 의 메서드를 준다.** 대신 `nil` 위험이 붙는다.
- **승격 필드를 리터럴 키로 쓰는 것은 1.27부터**다. 포인터 임베딩을 지나면 안 되고, 겹쳐 적을 수 없다.

### 금지 사례 — 컴파일러가 거부하는 것

(3)·(8)절의 블록이 정본이다. 한 표로 묶으면 이렇다.

| 쓴 것 | 메시지 | 왜 막나 |
|---|---|---|
| `b.Name`(같은 깊이에 둘) | `ambiguous selector b.Name` | 가장 얕은 깊이에 하나여야 한다 |
| `b.Tag()`(같은 깊이에 둘) | `ambiguous selector b.Tag` | 〃 |
| `ByPtr{Name: …}`(`*Object` 임베딩) | `invalid implicit pointer indirection to reach Name` | 지나는 임베딩이 포인터면 안 된다 |
| `Line{Object: …, Name: …}` | `cannot specify promoted field Name and enclosing embedded field Object` | 겹쳐 적을 수 없다 |
| `Line{Name: …}` (go.mod 가 `go 1.26`) | `use of promoted field Object.Name … requires go1.27 or later` | 판 경계 |

★ **거부하지 않는 것**도 함께 봐야 한다 — **`type Both struct{ L; R }` 선언 자체**는 통과하고((3)절),
**JSON 의 같은 깊이 충돌**은 에러 없이 **조용히 필드가 빠진다**((7)절).

## 어디서 틀리나

### 1. ★★★ 「임베딩은 상속이다」

- (1)절 실측 — `Dog` 가 `Speak()` 를 새로 썼는데도 `d.Intro()` 가 **`"..."`** 를 냈다.
  승격 메서드의 리시버가 **`main.Animal`** 로 찍혔다.
- **되부름이 없다.** 자바의 `super` 에 해당하는 것도 없다 — 안쪽은 **필드 이름**으로 부른다.
- 고치는 법 — 되부름이 필요하면 **인터페이스 필드를 임베딩**해 넣어 준다((5)절 ③).
  그 대가는 **안 채우면 패닉**이다.

### 2. ★★ 「같은 깊이에 같은 이름이 있어도 알아서 고르겠지」

- (3)절 실측 — `ambiguous selector b.Name` · `ambiguous selector b.Tag`.
- ★ **타입 선언은 통과한다.** 쓰는 자리에서만 막히므로 **나중에 깨진다.**
- 고치는 법 — **어느 쪽인지 적거나**(`b.L.Name`), 바깥에 같은 이름을 **하나 더 선언**해 얕은 쪽을 만든다.

### 3. ★★ 「승격된 필드는 그 타입의 필드다」

- (4)절 실측 — `Deep.NumField()` 가 **2**다. `Name`·`Code` 는 목록에 없다.
  `FieldByName("Code").Index` 가 **`[0 0 1]`** 이다.
- 고치는 법 — `reflect` 를 쓰는 코드는 **`Index` 경로**를 따라가야 한다. `Field(i)` 순회만으로는 못 본다.

### 4. ★★★ 「JSON 도 컴파일러처럼 충돌을 막아 주겠지」

- (7)절 실측 — `Clash` 가 **`{"title":"ㄷ"}`** 을 냈다. `dup` 이 **양쪽 다 빠졌고 `err` 는 `<nil>`** 이다.
  되읽기도 조용히 빈 문자열이다.
- 고치는 법 — 임베딩 둘을 쓸 때는 **JSON 이름이 겹치는지 먼저 본다.**
  겹치면 한쪽에 **태그로 다른 이름**을 주거나 **이름 있는 필드**로 바꾼다.

### 5. ★★ 「`*T` 임베딩이 더 좋다 — 메서드가 더 많으니까」

- (6)절 실측 — 맞다(`ByPtr` 의 `NumMethod` 가 **2**). 그런데 **안 채우면 패닉**이다.
- 고치는 법 — **생성자에서 반드시 채운다.** 아니면 값 임베딩 + `*Outer` 로 쓴다.

### 6. ★ 「인터페이스를 임베딩해 두면 일부만 구현하면 된다」

- (5)절 실측 — 맞다. 그리고 **안 바꾼 메서드를 부르면 죽는다**(`nil pointer dereference`).
- 고치는 법 — **그 관용구는 테스트 대역에만** 쓰고, 운영 코드에서는 전부 채운다.

### 7. ★ 「승격 필드를 리터럴 키로 쓰면 되지」

- (8)절 실측 — **1.27부터**다. 그 아래에서는 `requires go1.27 or later` 다.
  포인터 임베딩을 지나면 **판에 상관없이** 막힌다.
- 고치는 법 — `go.mod` 의 `go` 줄을 확인한다. 라이브러리라면 **옛 꼴**(`Object: Object{…}`)로 적는다.

### 8. ★ 「가려진 필드는 사라진 것이다」

- (2)절 실측 — `d.Name = "바뀜"` 뒤에도 `d.Mid.Base.Name` 이 **`"밑"`** 그대로다.
- 고치는 법 — 가려진 칸도 **메모리에 있고 JSON 에도 영향**을 준다. 필요 없으면 아예 임베딩하지 않는다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **임베딩 필드의 이름이 타입 이름인 것** | **명세 보장** | "The unqualified type name acts as the field name" |
| **승격된 필드가 보통 필드처럼 구는 것** | **명세 보장** | "Promoted fields act like ordinary fields of a struct" |
| **선택자가 가장 얕은 깊이 하나를 고르는 것** | **명세 보장** | "x.f denotes the field or method at the shallowest depth" |
| **같은 깊이에 둘이면 illegal 인 것** | **명세 보장** | "If there is not exactly one f with shallowest depth, the selector expression is illegal" |
| **필드 이름이 겹치면 선언 자체가 illegal 인 것** | **명세 보장** | "field names must be unique in a struct type" |
| **승격 메서드가 메서드 집합에 드는 것** | **명세 보장** | "promoted methods are included in the method set of the struct" |
| **`*T` 임베딩이 값 타입에도 `*T` 메서드를 주는 것** | **명세 보장** | "If S contains an embedded field *T, the method sets of S and *S both include …" |
| **임베딩 꼴이 `T` 또는 `*T` 인 것** | **명세 보장** | "must be specified as a type name T or as a pointer to a non-interface type name *T" |
| **`nil` 인터페이스 메서드 호출이 패닉인 것** | **명세 보장** | "calling or evaluating the method x.f causes a run-time panic" |
| **승격 필드를 리터럴 키로 쓰는 것이 1.27부터** | **명세 보장 + 판 경계** | "Each key must be a valid field selector [Go 1.27] for a (possibly promoted) field" |
| **포인터 임베딩을 지나는 승격 키가 막히는 것** | **명세 보장** | "The types of the embedded fields … must not be pointer types" |
| **승격 메서드의 리시버가 안쪽 타입인 것** | **명세 보장** | 메서드는 그 리시버 타입에 묶인다. 디스패치 표가 없다 |
| `json` 이 임베딩을 **평평하게** 내는 것 | **패키지 계약** | `encoding/json` 의 규칙. **명세가 아니다** |
| `json` 이 **충돌한 두 필드를 조용히 버리는 것** | **패키지 계약** | 〃. 다른 라이브러리는 다를 수 있다 |
| 컴파일 에러·패닉의 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 gc 의 것 |
| `reflect` 의 `Index` 표현 | **패키지 계약** | `reflect` 의 API 이지 명세의 낱말은 아니다 |
| 승격 호출의 **실행 비용** | **안 쟀다** | 벤치마크가 없다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |

★ 이 주제의 결론은 「**승격은 전부 명세가 정하고, 그 이름을 읽는 라이브러리만 제 규칙을 갖는다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 공통 필드 묶음을 여러 타입에 | **값 임베딩** | 제로값이 쓸 만하고 `nil` 위험이 없다 |
| 안쪽을 **갈아 끼워야** 함 | **인터페이스 임베딩** | 테스트 대역·부분 구현의 관용구 |
| 안쪽이 크고 공유해야 함 | **`*T` 임베딩** | 메서드 집합도 넓어진다. 대신 채워야 한다 |
| 안쪽 메서드를 **되불러야** 함 | ★ **임베딩이 아니다** | Go 에 가상 디스패치가 없다. 인터페이스로 설계한다 |
| 이름이 겹칠 것 같음 | **이름 있는 필드** | 모호 에러는 나중에 터진다 |
| 임베딩 둘 + JSON | **태그로 이름을 갈라 둔다** | 겹치면 **조용히 빠진다** |
| 안쪽 API 를 그대로 노출하기 싫음 | **이름 있는 필드 + 전달 메서드** | 승격은 **전부** 노출한다 — 고를 수 없다 |
| 라이브러리를 임베딩 | 신중히 | 그쪽에 메서드가 늘면 **내 타입이 모호해질 수 있다** |
| `sync.Mutex` 를 임베딩 | 되도록 **이름 있는 필드**(`mu sync.Mutex`) | 임베딩하면 `Lock`/`Unlock` 이 **공개 API 가 된다** |

판단 규칙 두 줄.

- **「이 이름을 밖에 그대로 내보내도 되나」를 먼저 묻는다.** 승격은 고를 수 없는 전부 공개다.
- **되부름이 필요하면 임베딩이 아니라 인터페이스다.** 그것이 (1)절의 결론 전부다.

## 핵심 문장

- **임베딩은 「필드 이름을 안 적은 필드」** 이고, 그러면 **타입 이름이 곧 필드 이름**이 된다.
- ★★★ **상속이 아니다.** 승격된 `Intro()` 안의 `a.Speak()` 가 `Dog.Speak()` 를 **안 부른다** —
  리시버 타입이 **`main.Animal`** 로 찍힌다. **되부름도 `super` 도 없다.**
- ★★ **선택자는 가장 얕은 깊이 하나**를 고른다. 가려진 칸은 **사라지지 않고 그대로 살아 있다.**
- ★★★ **같은 깊이에 둘이면 `ambiguous selector` 다** — 그런데 **타입 선언은 통과한다.**
  그래서 **나중에 깨진다.**
- ★★ **`reflect` 로 보면 평평하지 않다** — `Deep.NumField()` 는 **2**이고 `Code` 의 `Index` 는 **`[0 0 1]`** 이다.
  모호한 이름은 **`ok=false`** 로 조용히 돌아온다.
- ★★ **승격 메서드는 메서드 집합에 든다** — 그래서 **바깥 타입이 안쪽의 인터페이스를 그대로 만족한다.**
  이것이 19·20번으로 이어지는 다리다.
- ★★ **`*T` 임베딩은 값 타입에도 `*T` 의 메서드를 준다**(`ByValue` 1개 대 `ByPtr` 2개).
  대신 **안 채우면 패닉**이다.
- ★★★ **JSON 은 컴파일러와 다르게 군다** — 같은 깊이 충돌을 **에러 없이 조용히 버린다**(`err` 가 `<nil>`).
  그리고 그것은 **명세가 아니라 `encoding/json` 의 계약**이다.
- ★ **승격 필드를 리터럴 키로 쓰는 것은 1.27부터**다. `go.mod` 한 줄로 갈린다 —
  소스는 한 글자도 안 바뀌는데 **언어 판이 답을 바꾼다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 18번)
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체) —
  **이 주제의 직접 선행.** **그쪽은 「이름을 적은 필드」까지**, 여기는 **「안 적은 필드」** 부터
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) — **이 주제의 직접 후행.**
  여기는 **승격이 집합을 키운다**까지, 그쪽은 **「그래서 인터페이스를 만족하나」** 부터
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스) —
  (5)절의 「바깥이 안쪽의 인터페이스를 만족하는 것」이 거기서 본론이 된다
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(포인터) —
  (6)절의 `*T` 임베딩이 `nil` 이면 패닉하는 것의 기계는 거기 (6)절이 정본
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(타입 스위치) —
  인터페이스에 담긴 것을 되꺼내는 법
- [목록의 **45번 주제**](../45-encoding-json-tags-omitempty-pointers-numbers-and-streaming/)(`encoding/json`) — **(7)절의 정본.**
  여기는 **임베딩이 만드는 네 모양**까지, 그쪽은 **태그 전체 규칙**부터
- [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — `sync.Mutex` 를 임베딩할지 말지의 판단
- [`../../../../oop-basics/`](../../../../oop-basics/) —
  **그쪽은 상속·합성 설계 논의까지**, 여기는 **Go 의 승격 규칙**부터
- [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) —
  **그쪽은 `implements` 를 적고 충돌을 `X.super.m()` 으로 푼다**,
  여기는 **적는 것이 없고 충돌을 필드 이름으로 푼다**
- [`../../../kotlin/syntax/21-class-delegation-by/`](../../../kotlin/syntax/21-class-delegation-by/) —
  **그쪽은 컴파일러가 전달 메서드를 만든다**, 여기는 **선택자 규칙일 뿐 전달 메서드가 없다**
- [`../../../kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/) —
  **그쪽은 충돌 시 `override` + `super<T>` 로 사람이 적는다**, 여기는 **선택자를 길게 적는다**

## 용어 풀이

- **임베딩(embedding)** — 구조체에 **필드 이름 없이 타입만** 적는 것. 명세의 낱말은 embedded field.
- **승격(promotion)** — 임베딩한 타입의 필드·메서드가 **바깥 선택자로 닿게** 되는 것.
- **깊이(depth)** — 그 이름에 닿기까지 지난 임베딩 필드의 수. 자기 것은 0이다.
- **모호한 선택자(ambiguous selector)** — 가장 얕은 깊이에 같은 이름이 둘 이상인 것. 컴파일 에러다.
- **가림(shadowing)** — 얕은 쪽이 이겨 깊은 쪽 이름이 안 닿는 것. **지워지는 것이 아니다.**
- **인터페이스 임베딩** — 인터페이스 안에 다른 인터페이스를 적는 것. 메서드 집합의 합집합이 된다.
- **포인터 임베딩** — `*T` 를 임베딩하는 것. 값 타입의 메서드 집합까지 넓어진다.
- **전달 메서드(forwarding method)** — 안쪽 것을 그대로 부르는 껍데기 메서드.
  Go 는 **만들지 않는다** — 코틀린의 `by` 가 만드는 것이 이것이다.

---

## 더 들어가면

- **임베딩한 타입의 메서드를 「가리려면」 바깥에 같은 이름을 선언**하면 된다((1)절의 `Dog.Speak`).
  그런데 그것이 **되부름을 만들지 않는다**는 것이 이 주제의 핵심이다.
  「가리기」와 「재정의」를 같은 것으로 읽으면 (1)절에서 틀린다.
- 명세는 **`P.T3`·`*P.T4` 처럼 다른 패키지의 타입도 임베딩**할 수 있다고 적는다.
  그때 필드 이름은 **패키지 한정자를 뗀 `T3`·`T4`** 다. 이 문서는 **안 던졌다.**
- **제네릭 타입도 임베딩된다**(`TypeArgs` 가 문법에 있다). 다만 **타입 파라미터 자체는 안 된다.**
  이 문서는 **안 던졌다** — 정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다.
- `go vet` 에는 임베딩 전용 검사가 없다. (7)절의 JSON 충돌도 **`vet` 이 안 본다** —
  이 문서는 그 침묵을 **안 던졌다**(17번 주제에서 같은 성질의 침묵을 블록으로 잡았다).
- **`sync.Mutex` 를 임베딩하면 `Lock`/`Unlock` 이 공개 API 가 된다.**
  값 리시버로 그 타입을 복사하면 `go vet` 의 `copylocks` 가 잡는다 —
  실측은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (6)절에 있다.
- 임베딩한 타입이 `String()` 을 가지면 **`fmt` 가 바깥 타입에도 그것을 쓴다** —
  승격이 `fmt.Stringer` 만족으로 이어지기 때문이다. 무한 재귀의 씨앗이 되는 자리이고,
  정본은 [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)다. 이 문서는 **안 던졌다.**
