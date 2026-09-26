# go/syntax/45 — `encoding/json`: 태그·`omitempty`·포인터·숫자·스트리밍 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`encoding/json`](https://pkg.go.dev/encoding/json) · [`encoding/json/v2`](https://pkg.go.dev/encoding/json/v2) 패키지 문서(`go doc encoding/json` · `json.Unmarshal` · `json.Marshal`). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> JS 대비는 **`node v18.19.1`** 이다(머리말 `tools`).\
> **버전** — `omitzero` 는 **1.24** 부터다(이보다 옛 판은 이 머신에 없어 **안 돌렸다**). ★★ **이 판(`go1.27.1`)은 `encoding/json/v2` 가 기본으로 켜져 있고, v1 패키지가 v2 위에서 돈다**((6)절).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**빠진 필드 대 `null` 격자** — 입력 4(`{}` · `{"A":null}` · `{"A":0}` · `{"A":1}`) × 필드 타입 6(`int` · `*int` · `json.RawMessage` · `any` · 사용자 타입 `Opt` · `sql.NullInt64`)으로 디코드한 값」.
마지막 줄 「**네 입력을 서로 다른 값으로 받은 행 2 / 6**」((2)절). ★★★ **`*int` 도 `any` 도 「키가 없음」과 「`null`」을 못 가른다.** 가르는 것은 **`json.RawMessage` 와 `UnmarshalJSON` 을 가진 사용자 타입**뿐이었다.
★★ 짝이 되는 창은 「**`omitempty` 대 `omitzero` 격자**」 — 값 10가지 중 **빠진 칸이 둘 다 `7 / 10` 인데 빠진 칸의 모양이 다르다**((4)절).

★★★ **이 주제의 경계** — 태그가 **`reflect` 로만 보이고 오타가 조용하다**는 것은 [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (6)절이 정본이다 — 여기서는 되풀이하지 않고 **`encoding/json` 이 그 태그를 읽어 무엇을 하나**를 잰다.
`UnmarshalJSON` 을 **포인터 수신자**로 다는 이유(메서드 집합)는 [19번 주제](../19-method-sets-value-vs-pointer-receiver/), 에러를 `errors.As` 로 꺼내는 것은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/), `Decoder` 가 받는 `io.Reader` 는 [43번 주제](../43-io-reader-writer-and-composition/)다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **함수 인자는 값으로 복사된다** — `Unmarshal(data, t)` 가 `t` 를 못 바꾸는 근거((1)절). 태그가 「otherwise ignored」인 것(17번) |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ 「**If v is nil or not a pointer, Unmarshal returns an InvalidUnmarshalError**」 · `any` 에는 **`float64`** · `null` 은 포인터·인터페이스·맵·슬라이스만 `nil` 로, **나머지에는 효과 없음** · 이름 매칭은 **대소문자 무시** · `omitempty`/`omitzero` 의 정의 · **v1 이 v2 위에서 구현된다** |
| **구현** | 이 판에서 찍힌 것 | ★★ 같은 키가 두 번 오면 **뒤의 것이 이긴다**(문서에 없다 — (5)절) · 에러 문구 전부 · `go vet` 의 `non-pointer` 경고 |

★★★ **선을 긋는다** — 「`any` 로 받으면 `float64`」는 **문서의 계약**이다. 「`9007199254740993` 이 `…992` 가 된다」는 **IEEE 754 배정밀도의 성질**이고 JS 와 **같은 손실**이다((3)절). 「중복 키는 뒤의 것」은 **이 판의 관찰**이고, **v2 는 같은 입력을 에러로 막는다**((6)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go version; "$GO125" version; node --version =====
go version go1.27.1 linux/amd64
go version go1.25.12 linux/amd64
v18.19.1
(exit 0)
```

```text
===== 명령: go doc encoding/json.Unmarshal | sed -n "4,6p;12,16p;35,39p;41,49p;81,84p" =====
    Unmarshal parses the JSON-encoded data and stores the result in the
    value pointed to by v. If v is nil or not a pointer, Unmarshal returns an
    InvalidUnmarshalError.
    To unmarshal JSON into a pointer, Unmarshal first handles the case of the
    JSON being the JSON literal null. In that case, Unmarshal sets the pointer
    to nil. Otherwise, Unmarshal unmarshals the JSON into the value pointed at
    by the pointer. If the pointer is nil, Unmarshal allocates a new value for
    it to point to.
    To unmarshal JSON into a struct, Unmarshal matches incoming object keys
    to the keys used by Marshal (either the struct field name or its tag),
    preferring an exact match but also accepting a case-insensitive match.
    By default, object keys which don't have a corresponding struct field are
    ignored (see Decoder.DisallowUnknownFields for an alternative).
    To unmarshal JSON into an interface value, Unmarshal stores one of these in
    the interface value:

      - bool, for JSON booleans
      - float64, for JSON numbers
      - string, for JSON strings
      - []any, for JSON arrays
      - map[string]any, for JSON objects
      - nil for JSON null
    The JSON null value unmarshals into an interface, map, pointer, or slice
    by setting that Go value to nil. Because null is often used in JSON to mean
    “not present,” unmarshaling a JSON null into any other Go type has no effect
    on the value and produces no error.
(exit 0)
```

```text
===== 명령: go doc encoding/json.Marshal | sed -n "53,56p;85,94p" =====
    The "omitempty" option specifies that the field should be omitted from
    the encoding if the field has an empty value, defined as false, 0,
    a nil pointer, a nil interface value, and any array, slice, map, or string
    of length zero.
    The "omitzero" option specifies that the field should be omitted from the
    encoding if the field has a zero value, according to rules:

    1) If the field type has an "IsZero() bool" method, that will be used to
    determine whether the value is zero.

    2) Otherwise, the value is zero if it is the zero value for its type.

    If both "omitempty" and "omitzero" are specified, the field will be omitted
    if the value is either empty or zero (or both).
(exit 0)
```

```text
===== 명령: go doc encoding/json | sed -n "19,23p;33,36p" =====
This package (i.e., encoding/json) is now formally known as the v1 package since
a v2 package now exists at encoding/json/v2. All the behavior of the v1 package
is implemented in terms of the v2 package with the appropriate set of options
specified that preserve the historical behavior of v1.

  - In v1, JSON object members are unmarshaled into a Go struct using
    a case-insensitive name match with the JSON name of the fields.
    In contrast, v2 matches fields using an exact, case-sensitive match.
    The jsonv2.MatchCaseInsensitiveNames and MatchCaseSensitiveDelimiter options
(exit 0)
```

- ★★★ **「All the behavior of the v1 package is implemented in terms of the v2 package」** — 이 판에서 `encoding/json` 을 쓰는 코드는 **이미 v2 엔진 위에서** 돈다. 그래서 이 문서의 v1 블록은 전부 **`GOEXPERIMENT=nojsonv2` 로 옛 엔진을 한 번 더 빌드해 견준다**(블록 마지막 줄 「다른 줄 0」).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 디코드 값 · `2 / 6` · `7 / 10`** | 입력과 타입이 정한다 — 재대조 두 판에서 한 글자도 같았다 |
| 안 흔들린다 | 에러 문구 · `InputOffset` · `float64` 값 | |
| 안 흔들린다 | ★★ **「`nojsonv2` 판과 다른 줄 0」** | 두 엔진의 출력을 `diff` 한 줄 수다 |
| **판에 달릴 수 있다** | ★★ **v2 의 에러 문구**(`jsontext: …`) | v1 과 **다른 패키지의 문구**다 — 다른 판에서 같은지는 **확인하지 않았다** |

★ 정규화 규칙은 **기본 넷**만 썼다. 시각·주소가 찍히는 블록이 없다.

## 한눈에 — 쉽게 말하면

**`json.Unmarshal` 은 「택배 기사」다.** 상자(JSON)를 풀어 **내 집 서랍(Go 값)** 에 넣어 준다.
그런데 **주소(포인터)** 를 안 주고 **서랍 사진(값의 사본)** 을 건네면 — 기사는 사진에는 물건을 넣을 수 없으니 **「주소가 아니다」** 라며 돌아간다(`InvalidUnmarshalError`).
서랍에 **「비었음」 딱지**가 붙어 있을 때 그것이 **택배가 안 온 것**인지 **「비었음」이라고 적힌 쪽지가 온 것**인지(빠진 키 대 `null`)는 — **서랍 종류에 따라** 구분되기도 하고 안 되기도 한다.

| 비유 | 실체 |
|---|---|
| 서랍 주소를 줌 | ★★★ **`Unmarshal(data, &t)`** — 포인터라야 채운다((1)절) |
| 서랍 사진을 줌 | ★★★ **`Unmarshal(data, t)`** — `json: Unmarshal(non-pointer main.T)` |
| 「안 옴」과 「비었음 쪽지」 | ★★★ **빠진 키** 대 **`null`** — `int`·`*int`·`any` 는 **같게** 받는다((2)절) |
| 받은 쪽지를 봉투째 보관 | ★★ **`json.RawMessage`** — `null` 이면 **글자 `"null"`**, 안 왔으면 **`nil`** |
| 도장 찍는 서랍 | ★★ **`UnmarshalJSON` 을 가진 사용자 타입** — 불렸다는 사실이 「왔다」의 증거 |
| 숫자를 저울로 잼 | ★★★ **`any` 에 숫자 = `float64`** — `2^53` 을 넘는 정수는 **눈금이 모자라** 뭉개진다((3)절) |
| 이름표를 대충 읽는 기사 | ★★ **대소문자 무시 매칭** — `"NAME"` 이 `Name` 에 들어간다((5)절) |

```text
   ★★★ 빠진 키 대 null — 서랍마다 남는 흔적

   입력            int     *int     RawMessage     any          Opt(UnmarshalJSON)
   {}               0      nil      nil            nil          Set=false
   {"A":null}       0      nil      "null"         nil          Set=true  Null=true
   {"A":0}          0      &0       "0"            float64(0)   Set=true  V=0
                  └─ 셋 다 같음 ─┘  └ 셋이 다름 ┘   └ 위 둘 같음 ┘  └ 셋이 다름 ┘
```

> **`json.RawMessage`** — `[]byte` 의 다른 이름. 디코더가 그 자리의 **JSON 글자를 해석하지 않고 그대로** 담는다.

> **`UnmarshalJSON`** — `json.Unmarshaler` 인터페이스의 메서드. 디코더가 그 필드의 JSON 글자를 **이 메서드에 넘긴다.**

## 이 주제가 답하려는 질문

1. **왜 포인터를 줘야 하나** — 값을 주면 무슨 일이 일어나고 누가 잡나.
2. **빠진 키와 `null` 과 0 을 가를 수 있나** — 필드 타입마다.
3. **숫자는 어떤 타입으로 들어오나** — 큰 정수·소수·문자열 숫자.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **빠진 키 대 `null` 격자 — 입력 4 × 타입 6 → 디코드 값** | 타입마다 **무엇이 남나** | ★ 본체 창 · 스크립트가 「**서로 다른 값으로 받은 행**」을 센다 |
| ★★★ **`omitempty` 대 `omitzero` 격자 — 값 10 × 태그 2 → 빠졌나** | 나가는 쪽에서 **무엇이 사라지나** | (4)절 |
| ★★ **에러 창** — `InvalidUnmarshalError` · `cannot unmarshal …` · `go vet` | 막히는 자리 | (1)·(3)절 |
| ★★ **판 창** — `GOEXPERIMENT=nojsonv2` 로 옛 v1 엔진을 따로 빌드 | v1 결과가 **엔진을 타나** | 모든 v1 블록 마지막 줄 · (6)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`sql.NullInt64` 의 「Null」은 SQL 의 NULL 이다** — 이름만 보고 JSON `null` 을 가르는 도구로 고르면, **`{}` 와 `null` 이 똑같이 `{Int64:0 Valid:false}`** 이고 **숫자 `0`·`1` 은 에러**다. 타입도 이름도 그럴듯한데 **그 「Null」이 가리키는 층이 다르다** | (2)절 |
| **부적용 — 속도** | ★★★ **「`json` 이 느리다」·「v2 가 빠르다」는 이 문서에서 주장하지 않는다** — 한 번도 재지 않았다 | 규칙 4 |
| **못 잰 것 — `omitzero` 이전 판** | `omitzero` 가 없는 판(1.23 이하)에서 그 태그가 **조용히 무시되는지**는 그 툴체인이 이 머신에 없어 **안 돌렸다** | 규칙 3 |

### (1) ★★★ 포인터가 아니면 — `InvalidUnmarshalError`

**언제 쓰나** — `json.Unmarshal(b, x)` 의 둘째 인자를 적을 때.

```text
===== 소스: t45ptr.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
)

type T struct{ A int }

func main() {
	in := []byte(`{"A":1}`)
	var t T
	var p *T

	err := json.Unmarshal(in, t)
	fmt.Printf("[1] Unmarshal(in, t)   err=%v · t=%+v\n", err, t)
	var ie *json.InvalidUnmarshalError
	fmt.Printf("    errors.As(InvalidUnmarshalError)=%v · Type=%v\n", errors.As(err, &ie), ie.Type)

	err = json.Unmarshal(in, nil)
	fmt.Printf("[2] Unmarshal(in, nil) err=%v\n", err)

	err = json.Unmarshal(in, p)
	fmt.Printf("[3] Unmarshal(in, p)   err=%v · p=%v\n", err, p)

	err = json.Unmarshal(in, &t)
	fmt.Printf("[4] Unmarshal(in, &t)  err=%v · t=%+v\n", err, t)

	err = json.Unmarshal(in, &p)
	fmt.Printf("[5] Unmarshal(in, &p)  err=%v · p=%+v\n", err, *p)

	fmt.Println("── reflect 가 보는 것 ──")
	fmt.Printf("    ValueOf(t).CanSet()        = %v\n", reflect.ValueOf(t).CanSet())
	fmt.Printf("    ValueOf(&t).Elem().CanSet() = %v\n", reflect.ValueOf(&t).Elem().CanSet())
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
t45ptr.go:17:23: call of Unmarshal passes non-pointer as second argument
t45ptr.go:22:22: call of Unmarshal passes non-pointer as second argument
vet exit=1
[1] Unmarshal(in, t)   err=json: Unmarshal(non-pointer main.T) · t={A:0}
    errors.As(InvalidUnmarshalError)=true · Type=main.T
[2] Unmarshal(in, nil) err=json: Unmarshal(nil)
[3] Unmarshal(in, p)   err=json: Unmarshal(nil *main.T) · p=<nil>
[4] Unmarshal(in, &t)  err=<nil> · t={A:1}
[5] Unmarshal(in, &p)  err=<nil> · p={A:1}
── reflect 가 보는 것 ──
    ValueOf(t).CanSet()        = false
    ValueOf(&t).Elem().CanSet() = true
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`go vet` 이 먼저 잡았다** — `call of Unmarshal passes non-pointer as second argument` 두 줄(`[1]`·`[2]`). **컴파일러는 안 잡는다** — 둘째 인자의 타입이 `any` 라 무엇이든 들어간다. `vet exit=1` 인데도 빌드와 실행은 됐다.
- ★★★ **`[1]` 값을 주면 `json: Unmarshal(non-pointer main.T)`** — 그리고 `t` 는 `{A:0}` 그대로다. 에러는 `*json.InvalidUnmarshalError` 이고 `errors.As` 로 꺼내면 **`Type=main.T`** 가 들어 있다(24번의 `As`).
- ★★ **`[2]` `nil` 은 `json: Unmarshal(nil)`**, **`[3]` `nil` 인 `*T` 는 `json: Unmarshal(nil *main.T)`** — 포인터여도 **가리키는 곳이 없으면** 같은 에러 타입이다. ★ `vet` 은 `[3]` 을 **못 잡았다** — 타입은 포인터라서다.
- ★★★ **`[5]` 포인터의 포인터 `&p` 는 된다** — `p` 가 `nil` 이어도 디코더가 **새 `T` 를 만들어 `p` 에 달았다**(문서 「If the pointer is nil, Unmarshal allocates a new value for it to point to」).
- ★★★ **왜 그런가 — 마지막 두 줄** — `reflect.ValueOf(t).CanSet()` 이 **`false`**, `reflect.ValueOf(&t).Elem().CanSet()` 이 **`true`**. `Unmarshal` 은 `reflect` 로 값을 채우는데, **값으로 받은 인자는 호출한 쪽 `t` 의 사본**이라 채워 봐야 **호출한 쪽에는 안 보인다.** 그래서 라이브러리가 **채우기 전에 거절**한다.

```text
   ★★ 사본에는 써 봐야 소용이 없다

   main 의 t ─┐
              │ Unmarshal(in, t)     ─ 값 복사 ─▶  [ 사본 ]  ← 채워도 main 은 못 본다 → 그래서 거절
              │ Unmarshal(in, &t)    ─ 주소 ───▶  [ &t ]  ─▶ main 의 t 를 직접 채운다
```

비용 — 없다.

### (2) ★★★ 빠진 키 대 `null` — 입력 4 × 필드 타입 6

**언제 쓰나** — PATCH 요청처럼 **「안 보냄」과 「지워라(`null`)」가 뜻이 다른** 입력을 받을 때.

```text
===== 소스: t45null.go =====
package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
)

// Opt 는 UnmarshalJSON 이 불렸는지와 받은 글자를 적는다.
type Opt struct {
	Set  bool
	Null bool
	V    int
}

func (o *Opt) UnmarshalJSON(b []byte) error {
	o.Set = true
	if string(b) == "null" {
		o.Null = true
		return nil
	}
	return json.Unmarshal(b, &o.V)
}

type RInt struct{ A int }
type RPtr struct{ A *int }
type RRaw struct{ A json.RawMessage }
type RAny struct{ A any }
type ROpt struct{ A Opt }
type RSql struct{ A sql.NullInt64 }

func show(v any) string {
	switch x := v.(type) {
	case *int:
		if x == nil {
			return "nil"
		}
		return fmt.Sprintf("&%d", *x)
	case json.RawMessage:
		if x == nil {
			return "nil"
		}
		return fmt.Sprintf("%q", string(x))
	case nil:
		return "nil"
	case float64:
		return fmt.Sprintf("float64(%v)", x)
	default:
		return fmt.Sprintf("%+v", x)
	}
}

func main() {
	inputs := []string{`{}`, `{"A":null}`, `{"A":0}`, `{"A":1}`}
	rows := []struct {
		name string
		dec  func(string) (string, error)
	}{
		{"int", func(s string) (string, error) { var r RInt; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"*int", func(s string) (string, error) { var r RPtr; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"json.RawMessage", func(s string) (string, error) { var r RRaw; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"any", func(s string) (string, error) { var r RAny; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"Opt(사용자 타입)", func(s string) (string, error) { var r ROpt; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"sql.NullInt64", func(s string) (string, error) { var r RSql; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
	}
	fmt.Println("필드 타입\t" + strings.Join(inputs, "\t") + "\t넷이 서로 다른가")
	n := 0
	for _, r := range rows {
		cells := []string{r.name}
		seen := map[string]bool{}
		for _, in := range inputs {
			got, err := r.dec(in)
			if err != nil {
				got = "에러: " + err.Error()
			}
			seen[got] = true
			cells = append(cells, got)
		}
		all := len(seen) == len(inputs)
		if all {
			n++
		}
		fmt.Println(strings.Join(cells, "\t") + "\t" + fmt.Sprint(all))
	}
	fmt.Printf("네 입력을 서로 다른 값으로 받은 행 %d / %d\n", n, len(rows))

	fmt.Println("── 이미 값이 든 필드에 null 을 풀면 ──")
	ri := RInt{A: 5}
	json.Unmarshal([]byte(`{"A":null}`), &ri)
	seven := 7
	rp := RPtr{A: &seven}
	json.Unmarshal([]byte(`{"A":null}`), &rp)
	fmt.Printf("    int 5 → %s · *int &7 → %s\n", show(ri.A), show(rp.A))
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
vet exit=0
필드 타입	{}	{"A":null}	{"A":0}	{"A":1}	넷이 서로 다른가
int	0	0	0	1	false
*int	nil	nil	&0	&1	false
json.RawMessage	nil	"null"	"0"	"1"	true
any	nil	nil	float64(0)	float64(1)	false
Opt(사용자 타입)	{Set:false Null:false V:0}	{Set:true Null:true V:0}	{Set:true Null:false V:0}	{Set:true Null:false V:1}	true
sql.NullInt64	{Int64:0 Valid:false}	{Int64:0 Valid:false}	에러: json: cannot unmarshal number into Go struct field RSql.A of type sql.NullInt64	에러: json: cannot unmarshal number into Go struct field RSql.A of type sql.NullInt64	false
네 입력을 서로 다른 값으로 받은 행 2 / 6
── 이미 값이 든 필드에 null 을 풀면 ──
    int 5 → 5 · *int &7 → nil
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`int` 는 `0 0 0 1`** — 빠짐·`null`·`0` 이 **전부 0** 이다. 문서 「unmarshaling a JSON null into any other Go type **has no effect**」 그대로다.
- ★★★ **`*int` 는 `nil nil &0 &1`** — `0` 은 가른다. 그러나 **빠짐과 `null` 은 둘 다 `nil`** 이다. 흔히 「포인터로 받으면 빠진 것과 `null` 을 가른다」고 하는데 **이 격자에서는 안 갈렸다.** 포인터가 가르는 것은 **「값이 있었나(0 포함)」** 까지다.
- ★★★ **`json.RawMessage` 는 `nil "null" "0" "1"`** — **넷이 다 다르다.** `null` 은 **글자 네 개**로 남고, 키가 없으면 **아예 안 채워져 `nil`** 이다.
- ★★ **`any` 는 `nil nil float64(0) float64(1)`** — `*int` 와 같은 구멍이다. 숫자는 **`float64`** 로 들어왔다((3)절).
- ★★★ **`Opt`(사용자 타입)는 넷이 다 다르다** — 디코더가 **키가 있을 때만** `UnmarshalJSON` 을 부르고, **`null` 일 때도 부른다**(글자 `null` 을 넘긴다). 그래서 `Set` 이 「왔나」를, `Null` 이 「`null` 이었나」를 적는다.
- ★★★ **`sql.NullInt64` 는 `{}`·`null` 이 둘 다 `{Int64:0 Valid:false}`, 숫자는 에러** — `cannot unmarshal number into Go struct field RSql.A of type sql.NullInt64`. **이 타입은 `UnmarshalJSON` 이 없다** — `database/sql` 의 `Scan` 용이다. 이름에 `Null` 이 있어도 **JSON 과는 무관하다**(제5의 상태 — (0)절).
- ★★★ **마지막 줄 `네 입력을 서로 다른 값으로 받은 행 2 / 6`** — `RawMessage` 와 `Opt` 둘.
- ★★ **아래 두 줄 — 이미 값이 든 필드** — `int 5` 에 `null` 을 풀면 **5 가 그대로**, `*int &7` 은 **`nil` 로 지워진다.** 「`null` 을 보내면 지운다」가 **타입마다 다르다**(문서의 「pointer … by setting that Go value to nil」).

```text
   ★★★ 가를 수 있나 — 이 격자의 결론

   필요한 구분                    고를 타입
   0 대 「값 없음」              *int · any                 (빠짐 = null)
   빠짐 대 null 대 0             json.RawMessage · UnmarshalJSON 을 단 타입
   (쓰지 말 것)                  sql.NullInt64 — JSON 을 모른다
```

비용 — 없다.

### (3) ★★★ 숫자 — `any` 에는 `float64`, 큰 정수는 뭉개진다

```text
===== 소스: t45num.go =====
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

func main() {
	const in = `9007199254740993`

	var a any
	err := json.Unmarshal([]byte(in), &a)
	f := a.(float64)
	fmt.Printf("[1] any      : %T · %%v=%v · %%.0f=%.0f · err=%v\n", a, a, f, err)
	fmt.Printf("    int64(받은 값) = %d\n", int64(f))

	var i64 int64
	err = json.Unmarshal([]byte(in), &i64)
	fmt.Printf("[2] int64    : %d · err=%v\n", i64, err)

	dec := json.NewDecoder(strings.NewReader(in))
	dec.UseNumber()
	var b any
	err = dec.Decode(&b)
	n := b.(json.Number)
	iv, ierr := n.Int64()
	fmt.Printf("[3] UseNumber: %T · String()=%s · Int64()=%d,%v · err=%v\n", b, n.String(), iv, ierr, err)

	fmt.Println("── int 필드에 여러 글자 ──")
	for _, s := range []string{`1`, `1.0`, `1.5`, `1e3`, `"1"`, `99999999999999999999`} {
		var r struct{ A int }
		err := json.Unmarshal([]byte(`{"A":`+s+`}`), &r)
		fmt.Printf("    %-22s → A=%d · err=%v\n", s, r.A, err)
	}
	var q struct {
		A int `json:",string"`
	}
	err = json.Unmarshal([]byte(`{"A":"1"}`), &q)
	fmt.Printf("    `json:\",string\"` 태그로 \"1\" → A=%d · err=%v\n", q.A, err)
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
vet exit=0
[1] any      : float64 · %v=9.007199254740992e+15 · %.0f=9007199254740992 · err=<nil>
    int64(받은 값) = 9007199254740992
[2] int64    : 9007199254740993 · err=<nil>
[3] UseNumber: json.Number · String()=9007199254740993 · Int64()=9007199254740993,<nil> · err=<nil>
── int 필드에 여러 글자 ──
    1                      → A=1 · err=<nil>
    1.0                    → A=0 · err=json: cannot unmarshal number 1.0 into Go struct field .A of type int
    1.5                    → A=0 · err=json: cannot unmarshal number 1.5 into Go struct field .A of type int
    1e3                    → A=0 · err=json: cannot unmarshal number 1e3 into Go struct field .A of type int
    "1"                    → A=0 · err=json: cannot unmarshal string into Go struct field .A of type int
    99999999999999999999   → A=0 · err=json: cannot unmarshal number 99999999999999999999 into Go struct field .A of type int
    `json:",string"` 태그로 "1" → A=1 · err=<nil>
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

```text
===== 소스: t45num.js =====
const v = JSON.parse("9007199254740993");
console.log("typeof:", typeof v, "· 값:", v, "· === 9007199254740992:", v === 9007199254740992);
console.log("Number.MAX_SAFE_INTEGER:", Number.MAX_SAFE_INTEGER);
===== 명령: node t45num.js =====
typeof: number · 값: 9007199254740992 · === 9007199254740992: true
Number.MAX_SAFE_INTEGER: 9007199254740991
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[1]` `any` 로 받은 `9007199254740993` 은 `float64` · `9007199254740992`** — **에러 없이 1 이 사라졌다** — `int64(받은 값) = 9007199254740992`. `2^53 + 1` 은 배정밀도로 **표현할 수 없는 첫 정수**다.
- ★★★ **JS 도 한 글자도 같은 값** — `JSON.parse("9007199254740993")` 가 `9007199254740992`(`MAX_SAFE_INTEGER` 는 `…991`). **Go 의 `any` 경로와 JS 는 같은 손실**이다. [JS 31번](../../../js/syntax/31-json/) (6)절에서 20자리 id 가 뭉개진 것과 같은 집안이다.
  ★ **파이썬은 다르다** — [Python 47번](../../../python/syntax/47-json/)에서 같은 글자가 **`int` 로 정확히** 돌아왔다(점이 붙으면 `float`). **세 언어 중 둘이 같은 손실을 낸다.**
- ★★★ **`[2]` 필드 타입이 `int64` 면 정확하다** — 손실은 「JSON 숫자」의 성질이 아니라 「**`any` 에 `float64` 를 고른 것**」의 결과다.
- ★★★ **`[3]` `Decoder.UseNumber()` 는 `json.Number`** — **글자 그대로**(`String()=9007199254740993`) 들고 있다가 `Int64()` 로 정확히 꺼낸다. 모르는 모양의 JSON 을 `any` 로 받아야 할 때의 처방이다.
- ★★ **`int` 필드에 여러 글자** — `1` 만 통과다. ★★ **`1.0`·`1e3` 도 에러**다(값은 정수인데 **글자에 점·지수가 있다**). `"1"`(문자열)은 `cannot unmarshal string` · 20자리는 **범위 밖 에러** — **조용히 자르지 않는다.**
- ★★ **`` `json:",string"` `` 태그면 `"1"` 을 받는다** — 문자열 안의 숫자를 푸는 옵션이다.

비용 — 없다.

### (4) ★★★ `omitempty` 대 `omitzero` — 값 10 × 태그 2

```text
===== 소스: t45omit.go =====
package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

type E struct {
	Int    int             `json:"int,omitempty"`
	Bool   bool            `json:"bool,omitempty"`
	Str    string          `json:"str,omitempty"`
	NilPtr *int            `json:"nilptr,omitempty"`
	PtrTo0 *int            `json:"ptrto0,omitempty"`
	NilSl  []int           `json:"nilsl,omitempty"`
	EmpSl  []int           `json:"empsl,omitempty"`
	EmpMap map[string]int  `json:"empmap,omitempty"`
	Struct struct{ X int } `json:"struct,omitempty"`
	Time   time.Time       `json:"time,omitempty"`
}

type Z struct {
	Int    int             `json:"int,omitzero"`
	Bool   bool            `json:"bool,omitzero"`
	Str    string          `json:"str,omitzero"`
	NilPtr *int            `json:"nilptr,omitzero"`
	PtrTo0 *int            `json:"ptrto0,omitzero"`
	NilSl  []int           `json:"nilsl,omitzero"`
	EmpSl  []int           `json:"empsl,omitzero"`
	EmpMap map[string]int  `json:"empmap,omitzero"`
	Struct struct{ X int } `json:"struct,omitzero"`
	Time   time.Time       `json:"time,omitzero"`
}

func main() {
	zero := 0
	e, _ := json.Marshal(E{PtrTo0: &zero, EmpSl: []int{}, EmpMap: map[string]int{}})
	z, _ := json.Marshal(Z{PtrTo0: &zero, EmpSl: []int{}, EmpMap: map[string]int{}})
	fmt.Printf("omitempty: %s\n", e)
	fmt.Printf("omitzero : %s\n", z)
	keys := []string{"int", "bool", "str", "nilptr", "ptrto0", "nilsl", "empsl", "empmap", "struct", "time"}
	ne, nz := 0, 0
	fmt.Println("키\tomitempty 로 빠졌나\tomitzero 로 빠졌나")
	for _, k := range keys {
		ge := !strings.Contains(string(e), `"`+k+`":`)
		gz := !strings.Contains(string(z), `"`+k+`":`)
		if ge {
			ne++
		}
		if gz {
			nz++
		}
		fmt.Printf("%s\t%v\t%v\n", k, ge, gz)
	}
	fmt.Printf("빠진 칸 — omitempty %d / %d · omitzero %d / %d\n", ne, len(keys), nz, len(keys))
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
vet exit=0
omitempty: {"ptrto0":0,"struct":{"X":0},"time":"0001-01-01T00:00:00Z"}
omitzero : {"ptrto0":0,"empsl":[],"empmap":{}}
키	omitempty 로 빠졌나	omitzero 로 빠졌나
int	true	true
bool	true	true
str	true	true
nilptr	true	true
ptrto0	false	false
nilsl	true	true
empsl	true	false
empmap	true	false
struct	false	true
time	false	true
빠진 칸 — omitempty 7 / 10 · omitzero 7 / 10
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **둘 다 `7 / 10` 인데 빠진 칸이 다르다** — `omitempty` 만 뺀 것은 **빈 슬라이스·빈 맵**, `omitzero` 만 뺀 것은 **빈 구조체·`time.Time{}`**.
- ★★★ **`omitempty` 는 빈 구조체와 `time.Time{}` 을 못 뺀다** — `"struct":{"X":0}` · `"time":"0001-01-01T00:00:00Z"`. 문서의 정의가 **「false, 0, a nil pointer, a nil interface value, and any array, slice, map, or string of length zero」** 뿐이라 **구조체가 목록에 없다.** `time.Time` 은 구조체다.
- ★★★ **`omitzero` 는 빈(길이 0) 슬라이스·맵을 못 뺀다** — `"empsl":[]` · `"empmap":{}`. **`nil` 이 아니면 제로값이 아니기** 때문이다(`nilsl` 은 둘 다 뺐다).
- ★★ **`time.Time{}` 이 `omitzero` 로 빠진 것은 `IsZero()` 메서드 덕** — 문서 「If the field type has an "IsZero() bool" method, that will be used」.
- ★★ **`ptrto0`(0 을 가리키는 포인터)는 둘 다 남는다** — 포인터가 `nil` 이 아니다. 「값이 0 이어도 보냈다」를 표현하는 길이다((2)절의 거울).
- ★ **둘을 같이 쓰면 합집합**이다(문서 「omitted if the value is either empty or zero」). 이 격자는 **따로** 쟀다.

```text
   ★★★ 빠진 칸의 모양

                 int bool str nilptr ptrto0 nilsl empsl empmap struct time
   omitempty      ✗   ✗    ✗    ✗      ·      ✗     ✗     ✗      ·      ·
   omitzero       ✗   ✗    ✗    ✗      ·      ✗     ·     ·      ✗      ✗
                                                    └ 길이 0 ┘    └ 구조체 ┘
   ✗ = 빠짐 · = 남음
```

비용 — 없다.

### (5) ★★ 이름 매칭 — 대소문자를 안 가린다

```text
===== 소스: t45case.go =====
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type U struct {
	Name string
	ID   int `json:"id"`
}

func main() {
	for _, in := range []string{
		`{"Name":"a"}`,
		`{"NAME":"a"}`,
		`{"nAmE":"a"}`,
		`{"ID":7}`,
		`{"id":7,"ID":8}`,
		`{"ID":8,"id":7}`,
	} {
		var u U
		err := json.Unmarshal([]byte(in), &u)
		fmt.Printf("%-20s → %+v · err=%v\n", in, u, err)
	}
	fmt.Println("── 필드 둘이 한 키에 맞을 때 ──")
	for _, in := range []string{`{"NAME":"x"}`, `{"Name":"x"}`, `{"name":"x"}`} {
		var v struct {
			Name string
			NAME string
		}
		err := json.Unmarshal([]byte(in), &v)
		fmt.Printf("%-20s → %+v · err=%v\n", in, v, err)
	}
	fmt.Println("── Decoder.DisallowUnknownFields ──")
	for _, in := range []string{`{"NAME":"a"}`, `{"Name":"a","Nmae":"b"}`} {
		var u U
		dec := json.NewDecoder(strings.NewReader(in))
		dec.DisallowUnknownFields()
		err := dec.Decode(&u)
		fmt.Printf("%-24s → %+v · err=%v\n", in, u, err)
	}
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
vet exit=0
{"Name":"a"}         → {Name:a ID:0} · err=<nil>
{"NAME":"a"}         → {Name:a ID:0} · err=<nil>
{"nAmE":"a"}         → {Name:a ID:0} · err=<nil>
{"ID":7}             → {Name: ID:7} · err=<nil>
{"id":7,"ID":8}      → {Name: ID:8} · err=<nil>
{"ID":8,"id":7}      → {Name: ID:7} · err=<nil>
── 필드 둘이 한 키에 맞을 때 ──
{"NAME":"x"}         → {Name: NAME:x} · err=<nil>
{"Name":"x"}         → {Name:x NAME:} · err=<nil>
{"name":"x"}         → {Name:x NAME:} · err=<nil>
── Decoder.DisallowUnknownFields ──
{"NAME":"a"}             → {Name:a ID:0} · err=<nil>
{"Name":"a","Nmae":"b"}  → {Name:a ID:0} · err=json: unknown field "Nmae"
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`{"NAME":"a"}`·`{"nAmE":"a"}` 도 `Name` 에 들어간다** — 태그가 `json:"id"` 인 필드도 `"ID"` 로 채워진다. 문서 「preferring an exact match but also accepting a case-insensitive match」.
- ★★★ **같은 필드에 맞는 키가 둘이면 뒤의 것이 이긴다** — `{"id":7,"ID":8}` 은 **8**, 순서를 뒤집으면 **7**. **정확히 맞는 `"id"` 가 앞에 있어도 진다.** 문서의 「preferring an exact match」는 **키 둘 사이가 아니라 필드 둘 사이**의 규칙이다 — 아래 세 줄이 그것이다.
- ★★ **필드 `Name`·`NAME` 이 둘 다 있으면** — `"NAME"` 은 `NAME`, `"Name"` 은 `Name`(정확히 맞는 쪽), `"name"` 은 **`Name`**(둘 다 대소문자 무시로 맞는데 앞의 필드).
- ★★★ **`DisallowUnknownFields` 도 `"NAME"` 을 모르는 필드로 안 친다** — 대소문자만 다르면 **아는 필드**다. `"Nmae"` 같은 오타만 `json: unknown field "Nmae"` 로 막힌다.
- ★★ **이것이 조용한 구멍인 이유** — 외부 입력이 `"ADMIN":true` 처럼 대소문자만 바꿔 **다른 뜻으로 보낸 키**를 코드가 `Admin` 으로 받는다. 에러도 경고도 없다. ★ v2 는 이 매칭을 **기본으로 끈다**((6)절).

비용 — 없다.

### (6) ★★ 스트리밍 — `Token`·`More`·`Decode`, 그리고 v2

```text
===== 소스: t45stream.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
)

type Item struct{ N int }

func main() {
	fmt.Println("── [1] 배열 원소를 하나씩 ──")
	dec := json.NewDecoder(strings.NewReader(`[{"N":1},{"N":2},{"N":3}]`))
	tok, err := dec.Token()
	fmt.Printf("    Token() = %v (%T) · err=%v\n", tok, tok, err)
	for dec.More() {
		var it Item
		err := dec.Decode(&it)
		fmt.Printf("    Decode  = %+v · err=%v · InputOffset=%d\n", it, err, dec.InputOffset())
	}
	tok, err = dec.Token()
	fmt.Printf("    Token() = %v (%T) · err=%v\n", tok, tok, err)

	fmt.Println("── [2] 값이 여럿 이어진 입력 ──")
	dec = json.NewDecoder(strings.NewReader("{\"N\":1}\n{\"N\":2}\n"))
	for {
		var it Item
		err := dec.Decode(&it)
		if errors.Is(err, io.EOF) {
			fmt.Println("    io.EOF")
			break
		}
		fmt.Printf("    Decode = %+v · err=%v\n", it, err)
	}

	fmt.Println("── [3] 뒤따르는 글자 ──")
	const in = `{"N":1} x`
	var a Item
	fmt.Printf("    Unmarshal        : err=%v · %+v\n", json.Unmarshal([]byte(in), &a), a)
	dec = json.NewDecoder(strings.NewReader(in))
	var b, c Item
	fmt.Printf("    Decode 첫 번째   : err=%v · %+v\n", dec.Decode(&b), b)
	fmt.Printf("    Decode 두 번째   : err=%v · %+v\n", dec.Decode(&c), c)
	fmt.Printf("    dec.More()       : %v\n", json.NewDecoder(strings.NewReader(in)).More())
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && GOEXPERIMENT=nojsonv2 go build -trimpath -o prog.v1 . || exit 1; ./prog > on.txt; rc=$?; ./prog.v1 > off.txt; cat on.txt; echo "prog exit=$rc · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 $(diff on.txt off.txt | grep -c "^<")" =====
vet exit=0
── [1] 배열 원소를 하나씩 ──
    Token() = [ (json.Delim) · err=<nil>
    Decode  = {N:1} · err=<nil> · InputOffset=8
    Decode  = {N:2} · err=<nil> · InputOffset=16
    Decode  = {N:3} · err=<nil> · InputOffset=24
    Token() = ] (json.Delim) · err=<nil>
── [2] 값이 여럿 이어진 입력 ──
    Decode = {N:1} · err=<nil>
    Decode = {N:2} · err=<nil>
    io.EOF
── [3] 뒤따르는 글자 ──
    Unmarshal        : err=invalid character 'x' after top-level value · {N:0}
    Decode 첫 번째   : err=<nil> · {N:1}
    Decode 두 번째   : err=invalid character 'x' looking for beginning of value · {N:0}
    dec.More()       : true
prog exit=0 · GOEXPERIMENT=nojsonv2 로 빌드한 판과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[1]` 배열을 원소 하나씩** — `Token()` 이 **`[`**(`json.Delim`)을 먹고, `More()` 가 참인 동안 `Decode` 가 **원소 하나씩** 풀고, 마지막 `Token()` 이 **`]`**. `InputOffset` 이 `8 → 16 → 24` 로 **원소 하나만큼씩** 전진한다 — 배열 전체를 한 번에 메모리에 올리지 않는 길이다.
- ★★ **`[2]` 줄마다 값 하나(NDJSON 류)** — `Decode` 를 되풀이하면 **`io.EOF`** 에서 끝난다(43번의 `io.EOF` 계약).
- ★★★ **`[3]` 뒤따르는 쓰레기 `{"N":1} x`** — **`Unmarshal` 은 에러**(`invalid character 'x' after top-level value`)이고 **값도 안 채운다**(`{N:0}`). **`Decoder.Decode` 는 첫 값을 멀쩡히 돌려준다**(`err=<nil>` · `{N:1}`). 쓰레기는 **두 번째 `Decode` 에서야** 에러가 된다.
  ★★ **그래서 「한 번만 `Decode` 하고 끝」인 HTTP 핸들러는 뒤의 쓰레기를 모른다** — 「입력 전체가 JSON 하나인가」를 보려면 `Unmarshal` 을 쓰거나, `Decode` 뒤에 **`dec.More()`**(여기서 `true`)나 두 번째 `Decode` 의 `io.EOF` 를 확인한다.

```text
===== 소스: t45v2.go =====
package main

import (
	jsonv1 "encoding/json"
	"encoding/json/v2"
	"fmt"
)

type U struct {
	Name string
	S    []int
}

func main() {
	for _, in := range []string{`{"NAME":"a"}`, `{"Name":"a","Name":"b"}`, `{"Name":"a"} x`} {
		var u1, u2 U
		e1 := jsonv1.Unmarshal([]byte(in), &u1)
		e2 := json.Unmarshal([]byte(in), &u2)
		fmt.Printf("%-24s v1: %+v err=%v\n%-24s v2: %+v err=%v\n", in, u1, e1, "", u2, e2)
	}
	b1, _ := jsonv1.Marshal(U{})
	b2, _ := json.Marshal(U{})
	fmt.Printf("Marshal(U{})             v1: %s\n%-24s v2: %s\n", b1, "", b2)
	var a any
	e := json.Unmarshal([]byte(`9007199254740993`), &a)
	fmt.Printf("9007199254740993 → any   v2: %T %v err=%v\n", a, a, e)
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . ; echo "[기본] build exit=$?"; GOEXPERIMENT=nojsonv2 go build -trimpath -o /dev/null . 2>err.txt; echo "[GOEXPERIMENT=nojsonv2] build exit=$?"; sed "s/^/  (stderr) /; s|in .*/src/encoding|in <GOROOT>/src/encoding|" err.txt; ./prog =====
vet exit=0
[기본] build exit=0
[GOEXPERIMENT=nojsonv2] build exit=1
  (stderr) package ex
  (stderr) 	imports encoding/json/v2: build constraints exclude all Go files in <GOROOT>/src/encoding/json/v2
{"NAME":"a"}             v1: {Name:a S:[]} err=<nil>
                         v2: {Name: S:[]} err=<nil>
{"Name":"a","Name":"b"}  v1: {Name:b S:[]} err=<nil>
                         v2: {Name:a S:[]} err=jsontext: duplicate object member name "Name"
{"Name":"a"} x           v1: {Name: S:[]} err=invalid character 'x' after top-level value
                         v2: {Name:a S:[]} err=jsontext: invalid character 'x' after top-level value after offset 13
Marshal(U{})             v1: {"Name":"","S":null}
                         v2: {"Name":"","S":[]}
9007199254740993 → any   v2: float64 9.007199254740992e+15 err=<nil>
(exit 0)
```

- ★★★ **`[기본] build exit=0` · `[GOEXPERIMENT=nojsonv2] build exit=1`** — 이 판은 `encoding/json/v2` 가 **기본으로 빌드된다.** 끄면 `build constraints exclude all Go files`. ★★ **브리핑의 전제 「v2 는 `GOEXPERIMENT=jsonv2` 를 켜야 한다」가 이 판에서는 뒤집혔다** — 켜는 스위치가 아니라 **끄는 스위치**(`nojsonv2`)가 있다.
- ★★★ **v2 는 대소문자를 안 무시한다**(`{"NAME":"a"}` → `Name:` 빈 채) · **중복 키를 에러로 막는다**(`duplicate object member name "Name"`) · **`nil` 슬라이스를 `[]` 로 낸다**(v1 은 `null`).
- ★★ **v2 의 뒤따르는 쓰레기** — 에러는 내지만 **`Name:a` 가 이미 채워져 있다.** v1 `Unmarshal` 은 **먼저 전체를 검사하고** 채운다(`Name:` 빈 채). 에러를 보고도 값을 쓰면 v2 쪽이 **반쯤 채운 값**을 쓰게 된다.
- ★★ **큰 정수는 v2 도 `float64`** — `9.007199254740992e+15`. **손실은 v1 만의 것이 아니다.**

비용 — 없다. 두 엔진의 속도는 **재지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t45null.go
package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
)

// Opt 는 UnmarshalJSON 이 불렸는지와 받은 글자를 적는다.
type Opt struct {
	Set  bool
	Null bool
	V    int
}

func (o *Opt) UnmarshalJSON(b []byte) error {
	o.Set = true
	if string(b) == "null" {
		o.Null = true
		return nil
	}
	return json.Unmarshal(b, &o.V)
}

type RInt struct{ A int }
type RPtr struct{ A *int }
type RRaw struct{ A json.RawMessage }
type RAny struct{ A any }
type ROpt struct{ A Opt }
type RSql struct{ A sql.NullInt64 }

func show(v any) string {
	switch x := v.(type) {
	case *int:
		if x == nil {
			return "nil"
		}
		return fmt.Sprintf("&%d", *x)
	case json.RawMessage:
		if x == nil {
			return "nil"
		}
		return fmt.Sprintf("%q", string(x))
	case nil:
		return "nil"
	case float64:
		return fmt.Sprintf("float64(%v)", x)
	default:
		return fmt.Sprintf("%+v", x)
	}
}

func main() {
	inputs := []string{`{}`, `{"A":null}`, `{"A":0}`, `{"A":1}`}
	rows := []struct {
		name string
		dec  func(string) (string, error)
	}{
		{"int", func(s string) (string, error) { var r RInt; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"*int", func(s string) (string, error) { var r RPtr; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"json.RawMessage", func(s string) (string, error) { var r RRaw; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"any", func(s string) (string, error) { var r RAny; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"Opt(사용자 타입)", func(s string) (string, error) { var r ROpt; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
		{"sql.NullInt64", func(s string) (string, error) { var r RSql; e := json.Unmarshal([]byte(s), &r); return show(r.A), e }},
	}
	fmt.Println("필드 타입\t" + strings.Join(inputs, "\t") + "\t넷이 서로 다른가")
	n := 0
	for _, r := range rows {
		cells := []string{r.name}
		seen := map[string]bool{}
		for _, in := range inputs {
			got, err := r.dec(in)
			if err != nil {
				got = "에러: " + err.Error()
			}
			seen[got] = true
			cells = append(cells, got)
		}
		all := len(seen) == len(inputs)
		if all {
			n++
		}
		fmt.Println(strings.Join(cells, "\t") + "\t" + fmt.Sprint(all))
	}
	fmt.Printf("네 입력을 서로 다른 값으로 받은 행 %d / %d\n", n, len(rows))

	fmt.Println("── 이미 값이 든 필드에 null 을 풀면 ──")
	ri := RInt{A: 5}
	json.Unmarshal([]byte(`{"A":null}`), &ri)
	seven := 7
	rp := RPtr{A: &seven}
	json.Unmarshal([]byte(`{"A":null}`), &rp)
	fmt.Printf("    int 5 → %s · *int &7 → %s\n", show(ri.A), show(rp.A))
}
```

규칙 불릿.

- ★★★ **`Unmarshal`·`Decode` 에는 포인터를 준다** — 값을 주면 `InvalidUnmarshalError`. `go vet` 이 흔한 꼴을 잡지만 **`nil` 인 포인터 변수는 못 잡는다.**
- ★★★ **빠짐·`null`·0 을 가르려면 `json.RawMessage` 나 `UnmarshalJSON` 을 단 타입** — `*T` 는 빠짐과 `null` 을 **같게** 받는다.
- ★★★ **모르는 JSON 을 `any` 로 받으면 숫자는 `float64`** — 정수 id 가 있으면 `Decoder.UseNumber()` 나 **구체 타입**(`int64`).
- ★★ **`omitempty` 는 구조체를 못 뺀다 · `omitzero` 는 빈 슬라이스를 못 뺀다** — 둘을 같이 쓰면 합집합(1.24+).
- ★★ **이름 매칭은 대소문자 무시** — 같은 필드에 맞는 키가 둘이면 **뒤의 것**(이 판의 관찰).
- ★★ **`Decoder.Decode` 한 번은 뒤따르는 글자를 안 본다** — 입력 끝까지 보려면 `More()`/두 번째 `Decode`.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `json.Unmarshal(b, t)`(값) | ★★ **`go vet`** + 실행 시 `InvalidUnmarshalError` | (1)절 |
| `var p *T; json.Unmarshal(b, p)` | ★★ **실행 시에만** `Unmarshal(nil *main.T)` — `vet` 은 조용 | (1)절 `[3]` |
| PATCH 입력을 `*int` 로 받아 「`null` 이면 지움」 | ★★★ **아무도 안 잡는다** — 빠짐도 `nil` | (2)절 |
| `sql.NullInt64` 로 JSON 숫자 받기 | 실행 시 `cannot unmarshal number` | (2)절 |
| 큰 정수 id 를 `map[string]any` 로 받기 | ★★★ **아무도 안 잡는다** — 1 이 사라진다 | (3)절 |
| `time.Time` 필드에 `omitempty` | ★★ **아무도 안 잡는다** — `"0001-01-01T00:00:00Z"` 가 나간다 | (4)절 |
| 대소문자만 다른 키 | ★★ **아무도 안 잡는다** — `DisallowUnknownFields` 도 통과 | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「`Unmarshal` 에 값을 넘겨도 채워진다」

- (1)절 — **`non-pointer main.T`**. 값은 사본이라 채워도 호출한 쪽이 못 본다(`CanSet() = false`).

### 2. ★★★ 「포인터 필드면 빠진 키와 `null` 을 가를 수 있다」

- (2)절 — **둘 다 `nil`**. 가르는 것은 `RawMessage`·`UnmarshalJSON` 뿐(`2 / 6`).

### 3. ★★★ 「`sql.NullInt64` 로 JSON `null` 을 받는다」

- (2)절 — **숫자가 에러**. 이름의 「Null」은 SQL 층이다.

### 4. ★★★ 「JSON 숫자는 정확히 들어온다」

- (3)절 — **`any` 경로는 `float64`** — `9007199254740993` → `…992`. JS 와 같은 손실. `int64`·`UseNumber` 는 정확.

### 5. ★★ 「`omitempty` 면 제로값은 다 빠진다」

- (4)절 — **구조체·`time.Time{}` 은 안 빠진다.** 그 자리가 `omitzero` 다. 거꾸로 `omitzero` 는 빈 슬라이스를 안 뺀다.

### 6. ★★ 「키 이름은 정확히 맞아야 들어간다」

- (5)절 — **v1 은 대소문자 무시** · 중복 키는 뒤의 것. v2 는 둘 다 반대다.

### 7. ★ 「`Decode` 가 에러 없이 끝났으니 입력 전체가 올바르다」

- (6)절 — **`{"N":1} x` 의 첫 `Decode` 는 `<nil>`.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 인자는 값으로 복사된다 | **명세** | (1)절 · [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) |
| ★★★ 포인터 아니면 `InvalidUnmarshalError` | **표준 라이브러리 계약** | `t45udoc` · (1)절 |
| `null` 은 포인터 등만 `nil`, 나머지는 효과 없음 | **표준 라이브러리 계약** | `t45udoc` · (2)절 |
| ★★★ `any` 의 숫자는 `float64` | **표준 라이브러리 계약** | `t45udoc` · (3)절 |
| `2^53 + 1` 이 `…992` 로 | **IEEE 754 배정밀도의 성질** — JS 와 같다 | (3)절 |
| 대소문자 무시 매칭 | **표준 라이브러리 계약** | `t45udoc` · (5)절 |
| ★★ 중복 키는 뒤의 것이 이긴다 | **이 판의 관찰** — v1 문서에 없다 · v2 는 에러 | (5)·(6)절 |
| `omitempty`·`omitzero` 의 정의 | **표준 라이브러리 계약** | `t45mdoc` · (4)절 |
| v1 이 v2 위에서 돈다 · v2 가 기본 빌드 | **이 판의 계약**(`go doc encoding/json`) + **빌드 관찰** | `t45v2doc` · (6)절 |
| 에러 문구 | **구현** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 모양을 아는 입력 | **구체 구조체 + 포인터로 `Unmarshal`** | (1)절 |
| 「안 보냄」과 「지움」이 다른 PATCH | ★★★ **`json.RawMessage` 나 `UnmarshalJSON` 을 단 타입** | (2)절 `2 / 6` |
| 모양을 모르는데 정수 id 가 있다 | **`Decoder.UseNumber()`** | (3)절 |
| 선택 필드를 응답에서 빼기 | 슬라이스·맵·문자열은 `omitempty` · **구조체·`time.Time` 은 `omitzero`** | (4)절 |
| 외부 입력을 엄격히 | `DisallowUnknownFields` — ★ **대소문자 변형은 못 막는다** · 또는 v2 | (5)·(6)절 |
| 큰 배열·연속 값 | **`Decoder` + `Token`/`More`** | (6)절 — ★ 메모리 이득은 **재지 않았다** |

## 핵심 문장

- ★★★ **`Unmarshal` 에는 포인터를 준다** — 값은 사본이라 `json: Unmarshal(non-pointer main.T)`. `vet` 이 흔한 꼴을 잡는다.
- ★★★ **빠진 키와 `null` 은 `int`·`*int`·`any` 에서 같다** — 가르는 것은 `json.RawMessage` 와 `UnmarshalJSON` 을 단 타입(`2 / 6`). `sql.NullInt64` 는 JSON 을 모른다.
- ★★★ **`any` 로 받은 숫자는 `float64`** — `9007199254740993` 이 조용히 `…992`. JS 와 같은 손실. `int64`·`UseNumber` 는 정확.
- ★★ **`omitempty` 는 구조체·`time.Time` 을 못 빼고 `omitzero` 는 빈 슬라이스·맵을 못 뺀다**(둘 다 `7 / 10`).
- ★★ **v1 은 대소문자를 무시하고 중복 키는 뒤의 것이 이긴다** — 이 판에서 v1 은 v2 엔진 위에서 돌고, 옛 엔진과 출력이 **한 줄도 안 갈렸다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 45번)
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) — ★ 목록상 선행 · **필드 태그는 `reflect` 로만 보인다 · 태그 오타가 조용하다**(그 절의 `json.Marshal` 한 줄이 이 주제의 입구)
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(값 복사) · [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(`UnmarshalJSON` 의 포인터 수신자) · [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`errors.As`) · [43번 주제](../43-io-reader-writer-and-composition/)(`Decoder` 가 받는 `io.Reader`)
- [JS 31번](../../../js/syntax/31-json/)(JSON — 큰 정수 손실 · `JSON.rawJSON`) · [Python 47번](../../../python/syntax/47-json/)(JSON — 정수는 `int` 로 정확)

## 용어 풀이

- **`json.Unmarshal` / `json.Marshal`** — JSON 글자 → Go 값 / Go 값 → JSON 글자.
- **`InvalidUnmarshalError`** — 둘째 인자가 `nil` 이거나 포인터가 아닐 때의 에러 타입. `Type` 필드에 받은 타입이 있다.
- **`json.RawMessage`** — 해석하지 않은 JSON 글자를 담는 `[]byte`.
- **`json.Unmarshaler`** — `UnmarshalJSON([]byte) error` 하나짜리 인터페이스. 필드가 이것을 만족하면 디코더가 그 글자를 넘긴다.
- **`json.Number`** — 숫자를 **글자 그대로** 담는 문자열 타입. `Int64()`·`Float64()` 로 꺼낸다.
- **`omitempty` / `omitzero`** — 비었으면 뺀다(길이 0·false·0·nil) / 제로값이면 뺀다(`IsZero()` 우선, 1.24+).
- **`Decoder.Token` / `More`** — 다음 토큰(`[`·`{`·값) 하나 / 지금 배열·객체에 원소가 더 있나.
- **`GOEXPERIMENT=nojsonv2`** — 이 판에서 v2 를 끄고 **옛 v1 엔진**으로 빌드하는 스위치.

---

## 더 들어가면

- ★ **v2 의 옵션**(`MatchCaseInsensitiveNames` · `FormatNilSliceAsNull` 등)으로 v1 동작을 되살리는 것 — **안 던졌다.**
- ★ **`omitzero` 이전 판**의 태그 무시 — 툴체인이 없어 **못 쟀다.**
- ★ **`Decoder` 의 메모리 사용** — 원소 단위로 읽는다는 것은 `InputOffset` 으로 보였지만 **바이트는 재지 않았다.**
