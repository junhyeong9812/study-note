# go/syntax/45 — `encoding/json`: 태그·`omitempty`·포인터·숫자·스트리밍 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다(6번만 `node v18.19.1`). 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 디코드 값 · `2 / 6` · `7 / 10` · 에러 문구 · 「`nojsonv2` 로 빌드한 판과 다른 줄 0」.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `vet` 은 `[1]`·`[2]` 두 줄을 짚는다 · `[1]` `non-pointer main.T` · `[2]` `Unmarshal(nil)` · `[3]` `nil *main.T` · `[4]`·`[5]` 성공 · `CanSet` 은 `false`/`true`

**출력**

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

**왜 그런가**

- ★★★ 문서 「**If v is nil or not a pointer, Unmarshal returns an InvalidUnmarshalError**」. `[3]` 처럼 **타입은 포인터인데 값이 `nil`** 이어도 같은 에러다 — 그리고 `vet` 은 타입만 보므로 **`[3]` 을 못 짚는다.**
- ★★ `[5]` `&p` 는 `p` 가 `nil` 이어도 된다 — 「If the pointer is nil, Unmarshal allocates a new value for it to point to」.
- ★ 마지막 줄 `다른 줄 0` — 옛 v1 엔진도 문구까지 같았다.

### 2. 인자는 **사본**이라 채워도 호출한 쪽이 못 본다 — 그 사실은 **명세**, 「그래서 거절한다」는 **`encoding/json` 의 계약**

- ★★★ Go 는 함수 인자를 **값으로 복사**한다(16번). `Unmarshal(in, t)` 이 받은 것은 `t` 의 사본이고, `reflect` 로 봐도 **`CanSet() = false`** — 주소가 없는 값이라 **고칠 수 없다.** `&t` 를 주면 `Elem()` 이 호출한 쪽의 `t` 자체라 **`true`**.
- ★★ 채울 수 없는 것을 **조용히 넘기지 않고 에러로 알리는 것**이 라이브러리의 선택이다 — 문서가 그 에러 타입까지 약속한다.

### 3. `int` `0 0 0 1` · `*int` `nil nil &0 &1` · `RawMessage` `nil "null" "0" "1"` · `any` `nil nil float64(0) float64(1)` · `Opt` 넷이 다름 · `sql.NullInt64` 둘은 `{0 false}`, 숫자는 에러 — `2 / 6` · `int 5 → 5 · *int &7 → nil`

**출력**

```text
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

- ★★★ `null` 은 **포인터·인터페이스·맵·슬라이스만 `nil` 로** 만들고 **나머지에는 효과가 없다**(문서) — 그래서 `int` 는 전부 0, 이미 5 였으면 **5 그대로**.
- ★★★ `*int` 와 `any` 는 **빠짐과 `null` 이 같은 `nil`** 이다. `RawMessage` 는 `null` 을 **글자로** 남기고, `Opt` 는 `UnmarshalJSON` 이 **불렸는지**를 적는다.

### 4. `*int` 는 **「값이 있었나(0 포함)」까지만** 가른다 · 셋을 다 가르려면 **`json.RawMessage` 나 `UnmarshalJSON` 을 단 타입** · `sql.NullInt64` 는 **JSON 용이 아니다**

- ★★★ 3번 — `*int` 의 `{}` 와 `{"A":null}` 이 둘 다 `nil`. 「지워라」와 「안 보냄」이 **같은 값**이 된다.
- ★★★ `Opt` 처럼 **포인터 수신자 `UnmarshalJSON`** 을 달면, 키가 없으면 **안 불리고**, `null` 이면 **글자 `null` 로 불린다** — 두 사실로 셋이 갈린다.
- ★★ `sql.NullInt64` 는 **`UnmarshalJSON` 이 없다** — 숫자 `0`·`1` 이 `cannot unmarshal number` 에러다. 이름의 「Null」은 **SQL 의 NULL** 이다.

### 5. `[1]` `float64` · `9007199254740992` · `[2]` `int64` 정확 · `[3]` `json.Number` 정확 — `int` 필드는 **`1` 만** 통과(`1.0`·`1.5`·`1e3`·`"1"`·20자리 전부 에러) · `,string` 태그로 `"1"` → 1

**출력**

```text
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

- ★★★ `any` 에 숫자는 **`float64`**(문서의 표). `2^53 + 1` 은 `float64` 로 **표현이 안 돼** 이웃 값으로 반올림됐다 — **에러가 없다.**
- ★★ 손실은 **`any` 를 고른 탓**이다 — `int64` 필드면 정확하고, `UseNumber` 는 **글자 그대로** 들고 있다가 정확히 꺼낸다.
- ★★ `int` 필드는 **값이 정수여도 글자에 점·지수가 있으면 거절**한다(`1.0`·`1e3`). 넘치는 수는 **자르지 않고 에러**.

### 6. JS 는 `9007199254740992` — **5번 `[1]` 과 같은 값** · 파이썬은 **`int` 로 정확히** 받았다

**출력**

```text
===== 명령: node t45num.js =====
typeof: number · 값: 9007199254740992 · === 9007199254740992: true
Number.MAX_SAFE_INTEGER: 9007199254740991
(exit 0)
```

- ★★★ JS 의 숫자는 **전부 배정밀도**라 `JSON.parse` 가 Go 의 `any` 경로와 **같은 반올림**을 한다. [JS 31번](../../../js/syntax/31-json/)의 20자리 id 손실과 같은 집안이다.
- ★★ [Python 47번](../../../python/syntax/47-json/) — 같은 글자가 **`int` 로 정확히** 돌아왔고, `.0` 을 붙여야 `float` 가 됐다. **받는 쪽 언어가 무엇을 기본으로 고르나**가 손실을 정한다.

### 7. `omitempty` 는 `ptrto0`·`struct`·`time` 을 남기고 · `omitzero` 는 `ptrto0`·`empsl`·`empmap` 을 남긴다 — **둘 다 `7 / 10`**

**출력**

```text
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

- ★★★ `omitempty` 의 「비었음」은 **false·0·nil 포인터·nil 인터페이스·길이 0 인 배열·슬라이스·맵·문자열** 뿐이다(문서) — **구조체가 없다.** 그래서 `time.Time{}` 이 `"0001-01-01T00:00:00Z"` 로 나간다.
- ★★★ `omitzero` 는 **제로값**(또는 `IsZero()`)이다 — **`[]int{}` 는 `nil` 이 아니라 제로값이 아니다.**

### 8. 대소문자 변형 셋은 전부 `Name:a` · 태그 `id` 에 `"ID"` 도 들어감 · 중복 키는 **뒤의 것**(8 / 7) · 필드 둘이면 **정확히 맞는 쪽, 없으면 앞의 필드** · `"NAME"` 은 `DisallowUnknownFields` 도 통과, `"Nmae"` 만 에러

**출력**

```text
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

- ★★★ 문서 「preferring an exact match but also accepting a **case-insensitive** match」. 「exact 우선」은 **한 키에 맞는 필드가 둘일 때**의 규칙이다(`Name`·`NAME` 세 줄).
- ★★ **한 필드에 맞는 키가 둘**이면 정확히 맞는지와 무관하게 **나중에 온 키**가 이겼다 — 문서에 없는 **이 판의 관찰**이다(옛 엔진도 같았다 — `다른 줄 0`).

### 9. **안 막는다** — 대소문자만 다른 키는 「아는 필드」다 · 막는 것은 **어느 필드에도 안 맞는 키**(`"Nmae"`) · 막으려면 **v2**(대소문자 구분이 기본)로

- ★★★ 8번 — `{"NAME":"a"}` 가 `DisallowUnknownFields` 아래에서도 `Name:a` · `err=<nil>`.
- ★★ v1 에서 대소문자 구분을 켜는 옵션은 이 문서가 **안 던졌다.** v2 의 기본이 구분이라는 것은 11번 블록이 보였다.

### 10. `[1]` `[` → `{N:1}`·`{N:2}`·`{N:3}`(`InputOffset` 8·16·24) → `]` · `[2]` 둘 뒤 `io.EOF` · `[3]` `Unmarshal` 은 **에러·값 없음**, 첫 `Decode` 는 **`<nil>`·`{N:1}`**, 둘째 `Decode` 가 에러 · `More()` 는 `true` — **똑같이 다루지 않는다**

**출력**

```text
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

- ★★★ `Unmarshal` 은 입력 **전체**가 JSON 값 하나여야 한다. `Decoder` 는 **스트림에서 값 하나씩** 읽으므로, 첫 `Decode` 는 뒤의 글자를 **아직 안 봤다.**
- ★★ 「요청 본문이 JSON 하나인가」를 `Decoder` 로 확인하려면 **`Decode` 뒤에 `More()` 나 둘째 `Decode` 의 `io.EOF`** 를 봐야 한다.

### 11. **켤 것이 없다** — 기본으로 빌드되고 **`GOEXPERIMENT=nojsonv2` 를 주면 안 된다** · v2 는 **대소문자를 구분하고 · 중복 키를 에러로 막고 · 뒤따르는 글자도 에러**(단 앞의 값은 **이미 채운다**)

```text
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

- ★★★ `[기본] build exit=0` · `[GOEXPERIMENT=nojsonv2] build exit=1`. 이 판의 `go doc encoding/json` 이 「All the behavior of the v1 package is implemented in terms of the v2 package」라고 적는다 — **v1 도 이미 v2 엔진 위에서 돈다.**
- ★★ v2 도 `any` 의 숫자는 **`float64`** 다 — 5번의 손실은 v2 로 옮겨도 **그대로**.
- ★ v2 의 **`{"Name":"a"} x` 가 `Name:a` 를 채운 채 에러**다. 에러를 보고도 값을 쓰면 v1 과 결과가 다르다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 빠진 키 대 `null` 격자 (`t45null`) | 입력 4 × 타입 6 · 탭 칸 | 캡처마다 | **`2 / 6`** |
| ★★★ `omitempty` 대 `omitzero` (`t45omit`) | 값 10 × 태그 2 | 캡처마다 | **`7 / 10` · `7 / 10`** |
| ★★ 두 v1 엔진 | 같은 소스를 `GOEXPERIMENT=nojsonv2` 로 한 번 더 빌드해 출력 `diff` | v1 블록 6개 × 캡처마다 | **다른 줄 0** |
| ★★ 큰 정수 (`t45num`·`t45numjs`) | `any` · `int64` · `UseNumber` · node | 캡처마다 | `…992` 손실 · Go `any` 와 JS 같음 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `InvalidUnmarshalError` · `null` 의 효과 · `float64` · 대소문자 무시 · `omitempty`/`omitzero` | **표준 라이브러리 문서의 계약** |
| 중복 키에서 뒤의 것 | **이 판의 관찰**(두 엔진 모두) |
| v2 가 기본 빌드 · 옛 엔진은 `nojsonv2` | **이 판(`go1.27.1`)의 빌드 설정** |
| `2^53 + 1` 의 반올림 | **IEEE 754 배정밀도** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). JS 블록은 `node` 가 있어야 한다.
