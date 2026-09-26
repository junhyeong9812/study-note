# go/syntax/45 — `encoding/json`: 태그·`omitempty`·포인터·숫자·스트리밍 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 표준 라이브러리 문서의 계약인가, 이 판의 관찰인가」를 먼저 적어라.**
> 모든 Go 실험은 `module ex` · `go 1.27` 이고 `go build -trimpath` 로 빌드해 돌렸다(`go1.27.1`). v1 블록은 `GOEXPERIMENT=nojsonv2` 로 한 번 더 빌드해 견줬다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 둘째 인자 다섯 가지 (예측)

```go
// t45ptr.go
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
```

<!-- go vet . 을 먼저 돌리고(종료 코드와 상관없이) 빌드해 실행한다. -->

- `go vet` 이 짚는 줄은 어느 것인가? `[1]`\~`[5]` 각각의 `err` 와 값, 마지막 두 줄은?

### 2. 사본에는 쓸 수 없다 (왜)

- 1번의 `[1]` 에서 라이브러리가 **채우기 전에 거절하는** 이유를, 마지막 두 줄(`CanSet`)과 [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)의 값 복사로 설명하라. 이것은 명세의 성질인가 `encoding/json` 의 계약인가?

### 3. 빠진 키·`null`·0·1 과 여섯 타입 (예측)

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

- 여섯 행 × 네 입력의 스물네 칸은? 마지막 줄의 수는? 아래 「이미 값이 든 필드」 줄은?

### 4. PATCH 의 세 뜻 (경계)

- 「안 보냄 · 지워라(`null`) · 0 으로 바꿔라」를 가려야 하는 입력이 있다. 3번의 결과로 `*int` 는 **어디까지** 가르나? 셋을 다 가르려면 어떤 타입을 고르고, `sql.NullInt64` 는 왜 후보가 아닌가?

### 5. `9007199254740993` (예측)

```go
// t45num.go
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
```

- `[1]`\~`[3]` 세 줄과 `int` 필드 여섯 줄, 마지막 태그 줄은 각각?

### 6. 같은 숫자, 다른 언어 (연결)

```javascript
// t45num.js
const v = JSON.parse("9007199254740993");
console.log("typeof:", typeof v, "· 값:", v, "· === 9007199254740992:", v === 9007199254740992);
console.log("Number.MAX_SAFE_INTEGER:", Number.MAX_SAFE_INTEGER);
```

- 이 JS 가 찍는 값은? 5번의 `[1]` 과 견주면 같은가? [Python 47번](../../../python/syntax/47-json/)의 파이썬 `json` 은 같은 글자를 어떤 타입으로 받았나?

### 7. 열 가지 값과 두 태그 (예측)

```go
// t45omit.go
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
```

- 두 JSON 줄과 표의 스무 칸, 마지막 줄은?

### 8. 키 이름의 대소문자 (예측)

```go
// t45case.go
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
```

- 여섯 줄 · 세 줄 · 두 줄 각각의 결과는?

### 9. `DisallowUnknownFields` 가 막는 것 (경계)

- 8번의 결과로, 외부 입력의 **대소문자만 바꾼 키**를 `DisallowUnknownFields` 가 막아 주나? 막는 것은 무엇이고, 막으려면 무엇을 바꿔야 하나?

### 10. 배열 원소 하나씩, 그리고 뒤따르는 글자 (예측)

```go
// t45stream.go
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
```

- `[1]`·`[2]`·`[3]` 의 각 줄은? `Unmarshal` 과 첫 `Decode` 는 `{"N":1} x` 를 똑같이 다루나?

### 11. 이 판의 v2 (연결)

- 이 판(`go1.27.1`)에서 `encoding/json/v2` 를 import 하려면 무엇을 켜야 하나 — 아니면 무엇을 꺼야 **안** 되나? v2 는 8번의 두 구멍(대소문자 무시 · 중복 키)과 10번의 뒤따르는 글자를 어떻게 다루나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
