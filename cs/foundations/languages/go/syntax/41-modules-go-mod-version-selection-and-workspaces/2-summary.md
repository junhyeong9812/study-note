# go/syntax/41 — 모듈: `go.mod`·버전 선택·워크스페이스 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — `go help modules` · `go help work` · 툴체인 소스 `cmd/go/internal/mvs/mvs.go`(`BuildList` 주석) · `cmd/go/internal/modload/modfile.go`(`exclude` 처리 주석).
> 전부 **이 툴체인에서 직접 떴다.** `go help` 가 가리키는 [Go Modules Reference](https://go.dev/ref/mod)와 `research.swtch.com/vgo-mvs` 는 **네트워크를 막아서 안 열었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **외부 네트워크를 한 번도 안 썼다** — 의존 모듈은 스크래치패드 안에 직접 만든 **로컬 파일 프록시**(`GOPROXY=file://…`)에서 받았고, 체크섬 DB 는 `GOSUMDB=off` 로 껐다(머리말 `t41env`).\
> ★★ **경로 표기** — 출력에 찍히는 프록시 경로는 `<프록시>`, 블록 작업 디렉토리는 `<작업>` 으로 **캡처 스크립트가 바꿔 적었다**(로컬 절대 경로를 문서에 안 남기려고). 그 밖의 글자는 그대로다.\
> ★★ **버전** — 이 문서는 **이 판(1.27.1) 하나**에서만 쟀다. 모듈·워크스페이스·`go` 줄 규칙이 **언제부터인지는 릴리스 노트를 안 열어 적지 않는다**(GOPATH 모드와도 견주지 않았다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**MVS 격자** — `a`·`b` 의 판 3 × 3 을 요구하게 하고 `go list -m` 이 고른 `c` 를 찍는 로그」.
마지막 두 줄 「**요구 중 최댓값을 고른 칸 9 / 9**」 · 「**최신(v1.3.0)을 고른 칸 0 / 9**」((2)절).
★★ 짝이 되는 창은 「**`go run` 이 찍는 `Which()` — 각 의존이 실제로 어느 `c` 에 붙어 빌드됐나**」다. ★★★ `c v1.0.0` 을 요구한 `b` 도 **`c v1.1.0` 에 붙어** 빌드된다((1)절).

★★★ **이 주제의 경계** — import 경로가 **누구를 막나**(`internal`)는 [40번 주제](../40-package-visibility-naming-and-internal/) (2)절이 정본이다 — 그 편은 `replace` 를 **실험 배선**으로만 썼고 「버전 선택의 정본은 41번」이라고 넘겼다. 여기가 그 41번이다.
패키지 **초기화 순서**는 [01번 주제](../01-packages-imports-main-and-init/)다. `go.mod` 의 `go` 줄이 **언어 의미**(루프 변수)를 바꾸는 것은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)다 — 여기서는 `go` 줄이 **빌드를 막는 것**만 본다((7)절).

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ **없다** — 명세에 `module` 이라는 낱말이 **0 줄**이다(아래 `t41spec`) |
| **도구(`go` 명령)의 규칙** | `go help` 와 `cmd/go` 소스가 적은 것 | ★★★ **최소 버전 선택(MVS)** — 「방문한 모듈마다 **가장 높은 요구 판**」 · `replace`·`exclude` 는 **메인 모듈의 것만** · `go.work` 의 `use` 가 메인 모듈을 늘린다 |
| **이 판의 관찰** | 이 머신에서 찍힌 것 | `go: downloading` 줄의 순서 · `go work init` 이 쓴 `go 1.27.1` 줄 |

★★★ **선을 긋는다** — 이 주제의 규칙은 **전부 `go` 명령의 것**이다. 「Go 는 최소 버전을 고른다」는 **언어의 성질이 아니라 도구의 알고리즘**이다. 다른 빌드 도구(Bazel 등)는 다른 규칙으로 고를 수 있다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: echo "명세에서 module 이 나오는 줄: $(grep -c -i "module" "$(go env GOROOT)/doc/go_spec.html")"; go help modules | sed -n "1,5p" =====
명세에서 module 이 나오는 줄: 0
Modules are how Go manages dependencies.

A module is a collection of packages that are released, versioned, and
distributed together. Modules may be downloaded directly from version control
repositories or from module proxy servers.
(exit 0)
```

```text
===== 명령: sed -n "83,89p" "$(go env GOROOT)/src/cmd/go/internal/mvs/mvs.go"; sed -n "644,646p" "$(go env GOROOT)/src/cmd/go/internal/modload/modfile.go" =====
// BuildList traverses the graph and returns a list containing the highest
// version for each visited module. The first element of the returned list is
// target itself; reqs.Max requires target.Version to compare higher than all
// other versions, so no other version can be selected. The remaining elements
// of the list are sorted by path.
//
// See https://research.swtch.com/vgo-mvs for details.
	for _, mainModule := range ld.MainModules.Versions() {
		if index := ld.MainModules.Index(mainModule); index != nil && len(index.exclude) > 0 {
			// Drop any requirements on excluded versions.
(exit 0)
```

- ★★★ **「a list containing the highest version for each visited module」** — MVS 의 정의가 이 한 문장이다. **「가장 높은 판」인데 「요구된 판 가운데」** 다. 프록시에 더 높은 판이 있어도 **아무도 요구하지 않으면 방문하지 않는다.**
- ★★ `modfile.go` 의 주석 「**Drop any requirements on excluded versions**」 — `exclude` 는 판을 **올려 주는** 것이 아니라 그 요구를 **지운다**((4)절이 그 결과를 잰다).

```text
===== 명령: go env GOPROXY GOSUMDB GONOSUMDB GOFLAGS GOTOOLCHAIN =====
file://<프록시>
off
*
-mod=mod -modcacherw
local
(exit 0)
```

- 이 다섯 줄이 이 문서의 환경이다. ★ **`GOFLAGS=-mod=mod`** 는 `go.mod` 를 필요한 만큼 **고쳐 쓰게** 한다((1)절에서 `// indirect` 줄이 생긴 까닭). `-modcacherw` 는 블록마다 모듈 캐시를 지우려고 넣었다. ★★★ **`-mod=mod` 가 워크스페이스에서는 에러가 된다**((6)절).

### 로컬 파일 프록시 — 무엇을 만들었나

```python
# t41mkproxy.py
#!/usr/bin/env python3
"""mkproxy.py <모듈소스디렉토리> <프록시디렉토리> — GOPROXY=file:// 가 읽는 꼴을 만든다.
소스 디렉토리 아래 `<모듈경로>@<판>/` 마다 <모듈경로>/@v/{list,<판>.info,<판>.mod,<판>.zip} 을 쓴다."""
import json, pathlib, sys, zipfile, shutil
src, out = map(pathlib.Path, sys.argv[1:3])
shutil.rmtree(out, ignore_errors=True)
lists = {}
for d in sorted(p for p in src.rglob('*@v*') if p.is_dir()):
    rel = d.relative_to(src).as_posix()
    mod, ver = rel.rsplit('@', 1)
    v = out / mod / '@v'
    v.mkdir(parents=True, exist_ok=True)
    (v / f'{ver}.mod').write_bytes((d / 'go.mod').read_bytes())
    (v / f'{ver}.info').write_text(json.dumps({"Version": ver, "Time": "2026-01-01T00:00:00Z"}) + "\n")
    with zipfile.ZipFile(v / f'{ver}.zip', 'w') as z:
        for f in sorted(d.rglob('*')):
            if f.is_file():
                zi = zipfile.ZipInfo(f'{mod}@{ver}/' + f.relative_to(d).as_posix(), (2026, 1, 1, 0, 0, 0))
                z.writestr(zi, f.read_bytes())
    lists.setdefault(mod, []).append(ver)
for mod, vs in lists.items():
    (out / mod / '@v' / 'list').write_text(''.join(v + '\n' for v in vs))
```

```text
===== 소스: t41a110.go =====
package a

import "example.com/c"

// Which 는 이 모듈이 빌드될 때 붙은 c 의 판을 돌려준다.
func Which() string { return "a v1.1.0 → " + c.V }
===== 소스: t41c110.go =====
package c

// V 는 이 판의 이름이다.
const V = "c v1.1.0"
===== 명령: find . -type f | sort; echo; grep -r "^require\|^replace" --include=go.mod . | sort =====
./example.com/a@v1.0.0/go.mod
./example.com/a@v1.0.0/t41a100.go
./example.com/a@v1.1.0/go.mod
./example.com/a@v1.1.0/t41a110.go
./example.com/a@v1.2.0/go.mod
./example.com/a@v1.2.0/t41a120.go
./example.com/b@v1.0.0/go.mod
./example.com/b@v1.0.0/t41b100.go
./example.com/b@v1.1.0/go.mod
./example.com/b@v1.1.0/t41b110.go
./example.com/b@v1.2.0/go.mod
./example.com/b@v1.2.0/t41b120.go
./example.com/c@v1.0.0/go.mod
./example.com/c@v1.0.0/t41c100.go
./example.com/c@v1.1.0/go.mod
./example.com/c@v1.1.0/t41c110.go
./example.com/c@v1.2.0/go.mod
./example.com/c@v1.2.0/t41c120.go
./example.com/c@v1.3.0/go.mod
./example.com/c@v1.3.0/t41c130.go
./example.com/d/v2@v2.0.0/go.mod
./example.com/d/v2@v2.0.0/t41d200.go
./example.com/r@v1.0.0/go.mod
./example.com/r@v1.0.0/t41r100.go

./example.com/a@v1.0.0/go.mod:require example.com/c v1.0.0
./example.com/a@v1.1.0/go.mod:require example.com/c v1.1.0
./example.com/a@v1.2.0/go.mod:require example.com/c v1.2.0
./example.com/b@v1.0.0/go.mod:require example.com/c v1.0.0
./example.com/b@v1.1.0/go.mod:require example.com/c v1.1.0
./example.com/b@v1.2.0/go.mod:require example.com/c v1.2.0
./example.com/r@v1.0.0/go.mod:replace example.com/c v1.1.0 => example.com/c v1.2.0
./example.com/r@v1.0.0/go.mod:require example.com/c v1.1.0
(exit 0)
```

```text
===== 명령: cd "$PROXY" && find example.com/c -type f | sort && cat example.com/c/@v/list example.com/c/@v/v1.1.0.info && python3 -m zipfile -l example.com/c/@v/v1.1.0.zip =====
example.com/c/@v/list
example.com/c/@v/v1.0.0.info
example.com/c/@v/v1.0.0.mod
example.com/c/@v/v1.0.0.zip
example.com/c/@v/v1.1.0.info
example.com/c/@v/v1.1.0.mod
example.com/c/@v/v1.1.0.zip
example.com/c/@v/v1.2.0.info
example.com/c/@v/v1.2.0.mod
example.com/c/@v/v1.2.0.zip
example.com/c/@v/v1.3.0.info
example.com/c/@v/v1.3.0.mod
example.com/c/@v/v1.3.0.zip
v1.0.0
v1.1.0
v1.2.0
v1.3.0
{"Version": "v1.1.0", "Time": "2026-01-01T00:00:00Z"}
File Name                                             Modified             Size
example.com/c@v1.1.0/go.mod                    2026-01-01 00:00:00           30
example.com/c@v1.1.0/t41c110.go                2026-01-01 00:00:00           66
(exit 0)
```

- ★★ **`a`·`b` 는 판마다 「자기 판과 같은 `c`」를 요구한다** — `a v1.1.0` → `c v1.1.0`, `b v1.0.0` → `c v1.0.0`. **`c` 는 `v1.0.0`\~`v1.3.0` 네 판**이 프록시에 있다.
- ★ `r v1.0.0` 은 **자기 `go.mod` 에 `replace`** 를 달고 나온다((5)절의 재료). `d` 는 **`example.com/d/v2`** 라는 경로로만 있다((7)절).
- 프록시 한 판 = `@v/list` 한 줄 + `.info` · `.mod` · `.zip` 세 파일이다. zip 안의 경로는 `모듈@판/` 으로 시작한다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`go list -m all` 이 고른 판 · `9 / 9` · `0 / 9`** | MVS 는 **요구 그래프만의 함수**다 — 시간·네트워크·캐시를 안 본다 |
| 안 흔들린다 | `go.mod` 의 `diff` · `Which()` 가 찍은 줄 · 에러 문구 · `exit` | 같은 입력이면 같다 |
| **순서만 흔들린다** | ★ `go: downloading …` **줄의 순서** | 병렬로 내려받는다 — 그래서 **내려받기가 섞인 블록은 stderr 를 `sort` 해서 싣는다**(명령 배너에 적혀 있다) |
| **판을 탄다** | `go work init` 이 적는 `go 1.27.1` | 툴체인 판을 그대로 적는다 |

★ 정규화 규칙은 **기본 넷**만 썼다. 경로 치환(`<프록시>`·`<작업>`)은 **캡처가 할 때부터** 해서 재대조에서 흔들리지 않는다.

## 한눈에 — 쉽게 말하면

**회식 날짜를 고른다.** 팀원 `a` 는 「**11일 이후면 된다**」, `b` 는 「**10일 이후면 된다**」고 적어 냈다. 총무(`go` 명령)는 **둘 다 만족하는 가장 이른 날 — 11일**을 고른다.
달력에 13일이 있어도 **아무도 13일을 달라고 안 했으니** 안 고른다. 그리고 `b` 도 11일에 온다 — **「10일 이후」에 11일이 들어 있으니까.**
Cargo 의 총무는 반대로 **「조건을 만족하는 가장 늦은 날(13일)」** 을 고른다((8)절).

| 비유 | 실체 |
|---|---|
| 「11일 이후면 된다」 | ★★★ **`require example.com/c v1.1.0`** — 「**이 판 이상**」이라는 **하한**이다 |
| 둘 다 만족하는 가장 이른 날 | ★★★ **MVS** — 요구들 중 **최댓값**(`9 / 9`) |
| 달력의 13일 | ★★ 프록시의 **`c v1.3.0`** — 요구한 사람이 없으면 **안 고른다**(`0 / 9`) |
| 「10일 이후」를 낸 `b` 도 11일에 온다 | ★★★ **`b v1.0.0 → c v1.1.0`**((1)절) |
| 총무에게 「11일은 안 된다」고 적어 냄 | ★★ **`exclude`** — 그 요구를 **지운다**. 다른 팀원 조건으로 **10일로 내려갈 수도** 있다((4)절) |
| 팀원이 자기 수첩에 적은 「대리 참석」 메모 | ★★★ **의존 모듈의 `replace`** — **총무는 안 본다**((5)절) |
| 사무실 안 사람들끼리 먼저 모여 보기 | ★★ **`go.work`** — 로컬 디렉토리들을 **메인 모듈로 함께** 쓴다((6)절) |

```text
   ★★★ (1)절의 요구 그래프와 MVS 가 고른 것

        ex (메인 모듈)
        ├── require a v1.1.0 ──→ a v1.1.0 ── require c v1.1.0 ─┐
        └── require b v1.0.0 ──→ b v1.0.0 ── require c v1.0.0 ─┤
                                                               ▼
                         c 에 대한 요구 = { v1.1.0, v1.0.0 }   → 최댓값 v1.1.0
                         프록시에 있는 c = v1.0.0 v1.1.0 v1.2.0 v1.3.0   (v1.2.0·v1.3.0 은 아무도 요구 안 함)

        빌드 목록:  a v1.1.0 · b v1.0.0 · c v1.1.0   ← a 도 b 도 이 c 하나에 붙는다
```

> **모듈(module)** — 판을 매겨 함께 배포하는 패키지 묶음. 뿌리에 `go.mod` 가 있다.

> **메인 모듈(main module)** — `go` 명령을 부른 자리의 모듈. ★ **`replace`·`exclude` 가 효력을 갖는 유일한 자리**다. 워크스페이스에서는 `use` 한 모듈이 전부 메인 모듈이 된다.

> **빌드 목록(build list)** — 이번 빌드에 쓰는 「모듈마다 판 하나」의 목록. `go list -m all` 이 찍는다.

> **최소 버전 선택(MVS)** — 요구 그래프를 돌며 모듈마다 **요구된 판 중 가장 높은 것**을 고르는 `go` 명령의 알고리즘.

## 이 주제가 답하려는 질문

1. **MVS 는 무엇을 고르나** — 「최신」인가, 「요구 중 최댓값」인가. 낮은 판을 요구한 의존은 무엇에 붙나.
2. **요구를 바꾸는 손잡이 넷(`go get`·`exclude`·`replace`·`go.work`)은 각각 무엇을 바꾸나** — 그리고 **누구의 것이 효력을 갖나.**
3. **판이 경로에 들어가는 자리(`/v2`)와 `go` 줄은 무엇을 막나.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **MVS 격자 — 요구 3 × 3 → 고른 `c`** | 선택 규칙 자체 | ★ 본체 창 · 스크립트가 **탭 4칸**을 세고 두 수를 찍는다 |
| ★★★ **`go run` 의 `Which()`** | 의존이 **실제로 어느 판에 붙어** 빌드됐나 | 각 모듈이 `c.V` 를 돌려준다 — `go list` 가 **말한 것**과 **빌드된 것**을 한 번 더 맞춘다 |
| ★★ **`go.mod` 의 `diff`** | 손잡이가 **파일에 무엇을 적었나** | (3)절 |
| ★★ **`go mod graph`·`go mod why`** | **요구**(그래프)와 **선택**(빌드 목록)의 차이 | (3)절 |
| ★★ **받아 온 의존의 `go.mod`** | 의존이 **무엇을 적어 보냈는데 무시됐나** | (5)절 — 모듈 캐시의 `.mod` |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ `exclude` 하면 **「다음으로 높은 판」으로 올라간다**고 읽기 쉬운데, 이 판에서는 **요구를 지우고 남은 요구로 다시 고른다** — 그래서 **내려갈 수도**, **최신으로 튈 수도** 있다. 둘 다 에러도 경고도 없다 | (4)절 |
| **부적용 — 실행 시간·성능** | 버전 선택은 **빌드 전에 끝난다.** 잴 시간이 없다 | — |
| **못 잰 것 — 공개 프록시·체크섬 DB** | `proxy.golang.org`·`sum.golang.org` 의 동작, `go.sum` 검증 실패 | ★ **네트워크를 막아서** — `GOSUMDB=off` 로 **검증 자체를 껐다.** 체크섬 불일치는 이 문서가 재지 않았다 |

### (1) ★★★ MVS 는 무엇을 고르나 — `a` 는 `c v1.1.0`, `b` 는 `c v1.0.0`

**언제 쓰나** — 두 의존이 **같은 모듈의 다른 판**을 요구할 때(의존 충돌).

```go
// t41main.go
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
```

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 명령: go list -m all 2>e.txt; echo "list exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; go run . 2>e.txt; echo "run exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; echo "── 실행 뒤 go.mod ──"; cat go.mod =====
ex
example.com/a v1.1.0
example.com/b v1.0.0
example.com/c v1.1.0
list exit=0
a v1.1.0 → c v1.1.0
b v1.0.0 → c v1.1.0
run exit=0
  (stderr) go: downloading example.com/a v1.1.0
  (stderr) go: downloading example.com/b v1.0.0
  (stderr) go: downloading example.com/c v1.1.0
── 실행 뒤 go.mod ──
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.1.0 // indirect
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`go list -m all` 이 `example.com/c v1.1.0`** — 요구 `{v1.1.0, v1.0.0}` 의 **최댓값**이다. 프록시의 `v1.2.0`·`v1.3.0` 은 **목록에 없다.**
- ★★★ **`b v1.0.0 → c v1.1.0`** — `b` 는 `c v1.0.0` 을 요구했는데 **`c v1.1.0` 에 붙어 빌드됐다.** 빌드 목록에는 **모듈마다 판이 하나**뿐이라 `b` 만을 위한 `v1.0.0` 은 없다.
  ★ 이것이 성립하는 전제 — **`require` 는 「정확히 이 판」이 아니라 「이 판 이상」** 이고, 같은 메이저 판 안에서는 **뒤 판이 앞 판과 호환된다**고 약속한다(시맨틱 버전의 약속 — 지키는 것은 **모듈 작성자**이고 `go` 명령은 **검사하지 않는다**).
- ★★ **실행 뒤 `go.mod` 에 `require example.com/c v1.1.0 // indirect`** 가 생겼다 — `GOFLAGS=-mod=mod` 라서 `go run` 이 **고른 판을 적어 넣었다.** `// indirect` 는 「메인이 직접 import 하지 않는다」는 표시다.
- `(stderr)` 세 줄은 `go: downloading` — **첫 빌드에서 받았다.** 앞의 `go list -m all` 은 이 줄을 **안 냈다**(판을 고르는 데는 소스가 필요 없다 — 이 설명은 추론이고 모듈 캐시를 열어 보지는 않았다).

비용 — 없다.

### (2) ★★★ MVS 격자 — 요구 3 × 3

`a` 와 `b` 의 판을 각각 `v1.0.0`·`v1.1.0`·`v1.2.0` 으로 바꿔 가며 **아홉 번** 물었다(판마다 `a vX` 는 `c vX` 를 요구한다):

```text
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 명령: L="v1.0.0 v1.1.0 v1.2.0"; top=$(go list -m -versions example.com/c | tr " " "\n" | tail -1); echo "프록시에 있는 c 의 판: $(go list -m -versions example.com/c | cut -d" " -f2-) — 최신 $top"; : > rows.tsv; m=0; n=0; x=0; for va in $L; do for vb in $L; do printf "module ex\n\ngo 1.27\n\nrequire (\n\texample.com/a %s\n\texample.com/b %s\n)\n" $va $vb > go.mod; rm -f go.sum; got=$(go list -m -f "{{.Version}}" example.com/c 2>/dev/null); run=$(go run . 2>/dev/null | tr "\n" " "); hi=$(printf "%s\n%s\n" $va $vb | sort -V | tail -1); m=$((m+1)); [ "$got" = "$top" ] && n=$((n+1)); [ "$got" = "$hi" ] && x=$((x+1)); printf "a %s(→c %s)\tb %s(→c %s)\t고른 c %s\t%s\n" $va $va $vb $vb "$got" "$run" >> rows.tsv; done; done; awk -F"\t" "NF!=4{print \"칸 수 어긋남: \" NR; bad=1} END{exit bad}" rows.tsv || exit 1; cat rows.tsv; echo "요구 중 최댓값을 고른 칸 $x / $m"; echo "최신($top)을 고른 칸 $n / $m" =====
프록시에 있는 c 의 판: v1.0.0 v1.1.0 v1.2.0 v1.3.0 — 최신 v1.3.0
a v1.0.0(→c v1.0.0)	b v1.0.0(→c v1.0.0)	고른 c v1.0.0	a v1.0.0 → c v1.0.0 b v1.0.0 → c v1.0.0 
a v1.0.0(→c v1.0.0)	b v1.1.0(→c v1.1.0)	고른 c v1.1.0	a v1.0.0 → c v1.1.0 b v1.1.0 → c v1.1.0 
a v1.0.0(→c v1.0.0)	b v1.2.0(→c v1.2.0)	고른 c v1.2.0	a v1.0.0 → c v1.2.0 b v1.2.0 → c v1.2.0 
a v1.1.0(→c v1.1.0)	b v1.0.0(→c v1.0.0)	고른 c v1.1.0	a v1.1.0 → c v1.1.0 b v1.0.0 → c v1.1.0 
a v1.1.0(→c v1.1.0)	b v1.1.0(→c v1.1.0)	고른 c v1.1.0	a v1.1.0 → c v1.1.0 b v1.1.0 → c v1.1.0 
a v1.1.0(→c v1.1.0)	b v1.2.0(→c v1.2.0)	고른 c v1.2.0	a v1.1.0 → c v1.2.0 b v1.2.0 → c v1.2.0 
a v1.2.0(→c v1.2.0)	b v1.0.0(→c v1.0.0)	고른 c v1.2.0	a v1.2.0 → c v1.2.0 b v1.0.0 → c v1.2.0 
a v1.2.0(→c v1.2.0)	b v1.1.0(→c v1.1.0)	고른 c v1.2.0	a v1.2.0 → c v1.2.0 b v1.1.0 → c v1.2.0 
a v1.2.0(→c v1.2.0)	b v1.2.0(→c v1.2.0)	고른 c v1.2.0	a v1.2.0 → c v1.2.0 b v1.2.0 → c v1.2.0 
요구 중 최댓값을 고른 칸 9 / 9
최신(v1.3.0)을 고른 칸 0 / 9
(exit 0)
```

그림 해설 (한 단계씩):

- 첫 줄 — 프록시에 있는 `c` 는 **네 판**, 최신은 **`v1.3.0`**.
- ★★★ **아홉 칸 전부 「두 요구의 최댓값」** — `요구 중 최댓값을 고른 칸 9 / 9`.
- ★★★ **`최신(v1.3.0)을 고른 칸 0 / 9`** — `v1.3.0` 은 **누구도 요구하지 않아** 한 번도 안 뽑혔다. 「Go 는 호환되는 최신을 쓴다」는 **틀린 요약**이다.
- ★★ **넷째 칸(`a v1.1.0` · `b v1.0.0`)이 (1)절과 한 글자도 같다** — 격자는 (1)절을 아홉 번 한 것이다.
- ★ **`a` 도 안 올라간다** — `a v1.2.0` 이 있는데 `a v1.1.0` 을 요구한 칸은 **`a v1.1.0` 으로 빌드된다**(넷째\~여섯째 줄의 `Which()`). MVS 는 **모든 모듈에** 같은 규칙을 쓴다.

```text
   ★★★ 격자를 표로 — 고른 c (a 가 요구한 c ↓ · b 가 요구한 c →)

                      b: v1.0.0    b: v1.1.0    b: v1.2.0
        a: v1.0.0     v1.0.0       v1.1.0       v1.2.0
        a: v1.1.0     v1.1.0       v1.1.0       v1.2.0
        a: v1.2.0     v1.2.0       v1.2.0       v1.2.0

        v1.3.0 은 어느 칸에도 없다 — 「최신」은 선택 규칙에 들어가지 않는다
```

- ★★★ **그래서 잠금 파일(lock file)이 없어도 재현된다** — 선택이 **`go.mod` 들의 요구만의 함수**라서, 누가 언제 빌드해도 같은 판이 나온다. 새 판이 프록시에 올라와도 **아무도 요구를 올리지 않으면 빌드가 안 바뀐다.** `go.sum` 은 판을 고르는 파일이 아니라 **받은 내용의 해시**를 적는 파일이다.

비용 — 없다.

### (3) ★★ `go get` 으로 올리고 내리면 — `go.mod` 의 `diff`

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.1.0 // indirect
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 명령: cp go.mod 0.mod; go get example.com/c@v1.2.0 2>e.txt; echo "[go get example.com/c@v1.2.0] exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; diff 0.mod go.mod; go run . 2>/dev/null; cp go.mod 1.mod; go get example.com/c@v1.0.0 2>e.txt; echo "[go get example.com/c@v1.0.0] exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; diff 1.mod go.mod; go run . 2>/dev/null =====
[go get example.com/c@v1.2.0] exit=0
  (stderr) go: downloading example.com/c v1.2.0
  (stderr) go: upgraded example.com/c v1.1.0 => v1.2.0
10c10
< require example.com/c v1.1.0 // indirect
---
> require example.com/c v1.2.0 // indirect
a v1.1.0 → c v1.2.0
b v1.0.0 → c v1.2.0
[go get example.com/c@v1.0.0] exit=0
  (stderr) go: downgraded example.com/a v1.1.0 => v1.0.0
  (stderr) go: downgraded example.com/c v1.2.0 => v1.0.0
  (stderr) go: downloading example.com/a v1.0.0
  (stderr) go: downloading example.com/c v1.0.0
6c6
< 	example.com/a v1.1.0
---
> 	example.com/a v1.0.0
10c10
< require example.com/c v1.2.0 // indirect
---
> require example.com/c v1.0.0 // indirect
a v1.0.0 → c v1.0.0
b v1.0.0 → c v1.0.0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **`go get example.com/c@v1.2.0`** — `diff` 는 **`// indirect` 줄 하나**(`v1.1.0` → `v1.2.0`). 메인이 **요구를 직접 올렸으니** MVS 의 최댓값이 `v1.2.0` 이 되고 `a`·`b` 둘 다 `v1.2.0` 에 붙는다.
- ★★★ **`go get example.com/c@v1.0.0` — `a` 가 같이 내려갔다** — `go: downgraded example.com/a v1.1.0 => v1.0.0`. `a v1.1.0` 은 **`c v1.1.0` 이상**을 요구하므로 `c v1.0.0` 과 **함께 있을 수 없다.** `go get` 은 `c` 를 내리려고 **`a` 를 그 조건을 만족하는 판(`v1.0.0`)까지 끌어내렸다.**
  ★ **메인 `go.mod` 의 직접 요구(`example.com/a v1.1.0`)가 바뀌었다** — 한 줄 명령이 **두 줄을 고친다.** `diff` 를 안 보면 모른다.

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 명령: go mod graph 2>e.txt; echo "graph exit=$?"; go mod why -m example.com/c 2>>e.txt; echo "why exit=$?"; sort e.txt | sed "s/^/  (stderr) /" =====
ex example.com/a@v1.1.0
ex example.com/b@v1.0.0
ex go@1.27
example.com/a@v1.1.0 example.com/c@v1.1.0
example.com/a@v1.1.0 go@1.21
example.com/b@v1.0.0 example.com/c@v1.0.0
example.com/b@v1.0.0 go@1.21
go@1.27 toolchain@go1.27
graph exit=0
# example.com/c
ex
example.com/a
example.com/c
why exit=0
  (stderr) go: downloading example.com/a v1.1.0
  (stderr) go: downloading example.com/b v1.0.0
  (stderr) go: downloading example.com/c v1.1.0
(exit 0)
```

- ★★★ **`go mod graph` 에는 `example.com/b@v1.0.0 example.com/c@v1.0.0`** — **요구**는 그대로 남아 있다. 그런데 빌드 목록의 `c` 는 `v1.1.0` 이다((1)절). **그래프는 「누가 무엇을 요구했나」이고 빌드 목록은 「그래서 무엇을 골랐나」다.**
- ★★ `go mod why -m example.com/c` — **메인 → `a` → `c`** 한 길만 찍는다(`b` 쪽 길은 안 찍었다). `go help mod why` 가 「**a shortest path in the import graph**」라 적는다 — **길 하나**이고, 모듈이 아니라 **패키지 import 그래프**의 길이다.

```text
===== 명령: go help mod why | sed -n "3,6p" =====
Why shows a shortest path in the import graph from the main module to
each of the listed packages. If the -m flag is given, why treats the
arguments as a list of modules and finds a path to any package in each
of the modules.
(exit 0)
```

비용 — 없다.

### (4) ★★★ `exclude` — 요구를 지운다, 올려 주지 않는다

`exclude example.com/c v1.1.0` 을 메인에 적었다. 두 경우를 쟀다 — **`b` 가 있을 때**와 **`a` 하나뿐일 때**:

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

exclude example.com/c v1.1.0
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 명령: go list -m all 2>e.txt; echo "list exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; go run . 2>e.txt; echo "run exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; echo "── 실행 뒤 go.mod ──"; cat go.mod =====
ex
example.com/a v1.1.0
example.com/b v1.0.0
example.com/c v1.0.0
list exit=0
a v1.1.0 → c v1.0.0
b v1.0.0 → c v1.0.0
run exit=0
  (stderr) go: downloading example.com/a v1.1.0
  (stderr) go: downloading example.com/b v1.0.0
  (stderr) go: downloading example.com/c v1.0.0
── 실행 뒤 go.mod ──
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.0.0 // indirect

exclude example.com/c v1.1.0
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.27

require example.com/a v1.1.0

exclude example.com/c v1.1.0
===== 소스: t41onlya.go =====
package main

import (
	"fmt"

	"example.com/a"
)

func main() { fmt.Println(a.Which()) }
===== 명령: go list -m all 2>e.txt; echo "list exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; go run . 2>e.txt; echo "run exit=$?"; sort e.txt | sed "s/^/  (stderr) /"; echo "── 실행 뒤 go.mod ──"; cat go.mod =====
ex
example.com/a v1.1.0
list exit=0
a v1.1.0 → c v1.3.0
run exit=0
  (stderr) go: downloading example.com/a v1.1.0
  (stderr) go: downloading example.com/c v1.3.0
  (stderr) go: finding module for package example.com/c
  (stderr) go: found example.com/c in example.com/c v1.3.0
── 실행 뒤 go.mod ──
module ex

go 1.27

require example.com/a v1.1.0

require example.com/c v1.3.0 // indirect

exclude example.com/c v1.1.0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`a`·`b` 가 있으면 `c v1.0.0`** — `a v1.1.0` 의 「`c v1.1.0` 이상」 요구가 **통째로 지워지고**, 남은 `b` 의 `c v1.0.0` 이 최댓값이 됐다. 그래서 **`a v1.1.0 → c v1.0.0`** — **`a` 가 요구한 하한보다 낮은 판**에 붙어 빌드됐다.
  ★★★ **에러도 경고도 없다** — `(stderr)` 는 `go: downloading` 뿐이다. `a` 가 `c v1.1.0` 에 새로 생긴 무언가를 썼다면 **여기서 컴파일 에러**가 났을 것이다(이 실험의 `a` 는 `c.V` 만 써서 안 났다).
- ★★★ **`a` 하나뿐이면 `c v1.3.0`** — 요구가 지워지자 `go list -m all` 에 **`c` 가 아예 없다.** 그런데 `a` 는 `c` 패키지를 import 하므로 `go run` 이 **「`c` 를 제공하는 모듈을 찾는다」**(`finding module for package`) → **최신 `v1.3.0`** 을 가져와 `// indirect` 로 적었다.
- ★★ **「제외하면 다음 판으로 올라간다」는 둘 다에서 틀렸다** — 한쪽은 **내려갔고**(`v1.0.0`) 한쪽은 **최신으로 튀었다**(`v1.3.0`). 다음 판 `v1.2.0` 은 **어느 쪽에서도 안 뽑혔다.**
  ★ 소스 주석(머리말 `t41src`)이 규칙 그대로다 — 「**Drop any requirements on excluded versions**」.

비용 — 없다.

### (5) ★★★ `replace` — 메인 모듈의 것만 효력이 있다

`r v1.0.0` 은 자기 `go.mod` 에 `replace example.com/c v1.1.0 => example.com/c v1.2.0` 을 달고 나온다. 메인이 `r` 을 요구하면:

```text
===== 소스: go.mod =====
module example.com/c

go 1.21
===== 소스: t41cfork.go =====
package c

// V 는 이 사본의 이름이다.
const V = "c (로컬 디렉토리 cfork)"
===== 소스: go.mod =====
module ex

go 1.27

require example.com/r v1.0.0
===== 소스: t41onlyr.go =====
package main

import (
	"fmt"

	"example.com/r"
)

func main() { fmt.Println(r.Which()) }
===== 명령: cp go.mod 0.mod; echo "[1] 메인 go.mod 그대로"; go list -m all 2>/dev/null; go run . 2>/dev/null; echo "── 받아 온 r 의 go.mod ──"; cat "$GOMODCACHE/cache/download/example.com/r/@v/v1.0.0.mod"; printf "\nreplace example.com/c v1.1.0 => example.com/c v1.2.0\n" >> go.mod; echo "[2] 같은 replace 를 메인 go.mod 에"; go list -m all 2>/dev/null; go run . 2>/dev/null; cp 0.mod go.mod; printf "\nreplace example.com/c => ./cfork\n" >> go.mod; echo "[3] 로컬 디렉토리로 replace"; go list -m all 2>/dev/null; go run . 2>/dev/null; echo "run exit=$?" =====
[1] 메인 go.mod 그대로
ex
example.com/c v1.1.0
example.com/r v1.0.0
r v1.0.0 → c v1.1.0
── 받아 온 r 의 go.mod ──
module example.com/r

go 1.21

require example.com/c v1.1.0

replace example.com/c v1.1.0 => example.com/c v1.2.0
[2] 같은 replace 를 메인 go.mod 에
ex
example.com/c v1.1.0 => example.com/c v1.2.0
example.com/r v1.0.0
r v1.0.0 → c v1.2.0
[3] 로컬 디렉토리로 replace
ex
example.com/c v1.1.0 => ./cfork
example.com/r v1.0.0
r v1.0.0 → c (로컬 디렉토리 cfork)
run exit=0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[1]` — `r v1.0.0 → c v1.1.0`** — `r` 의 `go.mod` 에 `replace` 가 **분명히 있는데**(받아 온 `.mod` 를 찍었다) **무시됐다.** `go list -m all` 에도 `=>` 가 없다.
- ★★★ **`[2]` — 같은 줄을 메인 `go.mod` 에 적으면 `c v1.1.0 => example.com/c v1.2.0`** · `r v1.0.0 → c v1.2.0`. **글자가 같은 `replace` 가 메인에서만 효력이 있다.**
- ★★ **`[3]` — 로컬 디렉토리로 `replace example.com/c => ./cfork`** — 판 없이 적으면 **모든 판**을 바꾼다. `go list -m all` 이 `example.com/c v1.1.0 => ./cfork` — **MVS 가 고른 판(`v1.1.0`)은 그대로 적히고, 내용만 디렉토리에서 온다.**
- ★★ **왜 의존의 `replace` 를 무시하나** — 의존마다 자기 `replace` 를 들고 오면 **두 의존이 같은 모듈을 서로 다른 곳으로 바꿔 달라고 할 때** 누구 말을 들을지 정할 수 없다. 그래서 **빌드를 하는 쪽(메인)** 만 바꿀 수 있다. ★ 이 설명은 이 판의 **행동에서 거꾸로 읽은 것**이고, 설계 문서(Modules Reference)는 **안 열었다.**
- ★ **`replace` 는 라이브러리를 배포할 때 사용자에게 전달되지 않는다** — `[1]` 이 바로 그 장면이다. 포크를 쓰게 하고 싶으면 **요구를 포크 경로로 바꿔야** 한다.

비용 — 없다.

### (6) ★★ `go.work` — 두 모듈을 `replace` 없이 함께 고친다

```text
===== 명령: go help work | sed -n "15,18p;50,53p" =====
A workspace is specified by a go.work file that specifies a set of
module directories with the "use" directive. These modules are used as
root modules by the go command for builds and related operations.  A
workspace that does not specify modules to be used cannot be used to do
The replace directive has the same syntax as the replace directive in a
go.mod file and takes precedence over replaces in go.mod files.  It is
primarily intended to override conflicting replaces in different workspace
modules.
(exit 0)
```

`app`(메인)과 `c` 의 로컬 사본을 한 디렉토리 아래 두고 `go work init ./app ./c`:

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.1.0 // indirect
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 소스: go.mod =====
module example.com/c

go 1.21
===== 소스: t41cwork.go =====
package c

// V 는 이 사본의 이름이다.
const V = "c (작업 공간의 로컬 사본)"
===== 명령: find . -path ./.modcache -prune -o -type f -print | sort; cd app || exit 1; echo "[1] go.work 없음 · GOWORK=\"$(go env GOWORK)\""; go run . 2>/dev/null; cd .. || exit 1; GOFLAGS= go work init ./app ./c; echo "[go work init ./app ./c] exit=$?"; cat go.work; cd app || exit 1; echo "[2] go.work 있음 · GOFLAGS=$GOFLAGS 그대로"; go run . 2>e.txt; echo "run exit=$?"; sed "s/^/  (stderr) /" e.txt; echo "[3] GOFLAGS 비움 · GOWORK=$(GOFLAGS= go env GOWORK | sed "s|.*/|…/|")"; GOFLAGS= go list -m all; GOFLAGS= go run .; echo "run exit=$?"; echo "[4] GOWORK=off"; GOWORK=off go run . 2>/dev/null; echo "run exit=$?"; echo "app/go.mod 의 replace 줄 수: $(grep -c replace go.mod)" =====
./app/go.mod
./app/t41main.go
./c/go.mod
./c/t41cwork.go
[1] go.work 없음 · GOWORK=""
a v1.1.0 → c v1.1.0
b v1.0.0 → c v1.1.0
[go work init ./app ./c] exit=0
go 1.27.1

use (
	./app
	./c
)
[2] go.work 있음 · GOFLAGS=-mod=mod -modcacherw 그대로
run exit=1
  (stderr) go: -mod may only be set to readonly or vendor when in workspace mode, but it is set to "mod"
  (stderr) 	Remove the -mod flag to use the default readonly value, 
  (stderr) 	or set GOWORK=off to disable workspace mode.
[3] GOFLAGS 비움 · GOWORK=…/go.work
ex
example.com/c
example.com/a v1.1.0
example.com/b v1.0.0
a v1.1.0 → c (작업 공간의 로컬 사본)
b v1.0.0 → c (작업 공간의 로컬 사본)
run exit=0
[4] GOWORK=off
a v1.1.0 → c v1.1.0
b v1.0.0 → c v1.1.0
run exit=0
app/go.mod 의 replace 줄 수: 0
(exit 0)
```

그림 해설 (한 단계씩):

- `[1]` — `go.work` 가 없으면 프록시의 `c v1.1.0`.
- ★★★ **`[2]` — `GOFLAGS=-mod=mod` 그대로면 `run exit=1`** — `-mod may only be set to readonly or vendor when in workspace mode`. ★ **이 문서의 다른 절이 전부 기대는 설정이 워크스페이스에서는 거부된다** — 브리핑·환경 스크립트에 `-mod=mod` 를 박아 두면 여기서 걸린다.
- ★★★ **`[3]` — `GOFLAGS` 를 비우면 `c (작업 공간의 로컬 사본)`** · `go list -m all` 에 **`example.com/c` 가 판 없이** 찍힌다 — **메인 모듈이 둘**(`ex`·`example.com/c`)이 된 것이다. 메인 모듈에는 판이 없다.
- ★★ **`[4]` — `GOWORK=off` 면 다시 `c v1.1.0`** — `go.work` 를 무시한다.
- ★★★ **`app/go.mod 의 replace 줄 수: 0`** — **`go.mod` 를 한 글자도 안 고쳤다.** `replace ./c` 로 같은 일을 하면 그 줄을 **커밋할 위험**이 있는데, `go.work` 는 **별도 파일**이라 그 위험이 없다(`go.work` 를 커밋하지 않는 것이 흔한 관례다 — 이 문서가 **잰 것은 아니다**).
- ★ `go work init` 이 적은 `go 1.27.1` 은 **툴체인 판**이다(판을 탄다).

비용 — 없다.

### (7) ★★ 판이 경로에 들어가는 자리 — `/v2` 와 `go` 줄

```text
===== 소스: go.mod =====
module ex

go 1.27

require example.com/d v2.0.0
===== 소스: t41v2.go =====
package main

import (
	"fmt"

	"example.com/d"
)

func main() { fmt.Println(d.V) }
===== 명령: go build -o /dev/null . 2>e.txt; echo "[require example.com/d v2.0.0] build exit=$?"; sed "s/^/  (stderr) /" e.txt; sed -i "s|example.com/d v2.0.0|example.com/d/v2 v2.0.0|" go.mod; sed -i "s|\"example.com/d\"|\"example.com/d/v2\"|" t41v2.go; go run . 2>/dev/null; echo "[경로에 /v2] run exit=$?" =====
[require example.com/d v2.0.0] build exit=1
  (stderr) go: errors parsing go.mod:
  (stderr) go.mod:5: require example.com/d: version "v2.0.0" invalid: should be v0 or v1, not v2
d v2.0.0
[경로에 /v2] run exit=0
(exit 0)
```

- ★★★ **`require example.com/d v2.0.0` — `version "v2.0.0" invalid: should be v0 or v1, not v2`** · `build exit=1`. `go.mod` 를 **파싱하는 단계**에서 막힌다.
  **메이저 판 2 이상은 모듈 경로에 `/v2` 가 붙어야** 한다 — `example.com/d` 와 `example.com/d/v2` 는 **다른 모듈**이다.
- ★★ **경로를 `/v2` 로 바꾸자 `d v2.0.0`** · `run exit=0`. ★ import 경로는 `example.com/d/v2` 인데 **패키지 이름은 `d`** 다(소스에서 `d.V` 로 부른다).
- ★★ **그래서 v1 과 v2 가 한 빌드에 같이 들어갈 수 있다** — 경로가 다르니 MVS 에게는 **다른 모듈 둘**이다(이 문서는 **둘을 같이 넣어 보지는 않았다**).

```text
===== 소스: t41tc.go =====
package main

func main() {}
===== 명령: n=0; for v in 1.21 1.27 1.27.1 1.28; do printf "module ex\n\ngo %s\n" $v > go.mod; go build -o /dev/null . 2>e.txt; rc=$?; [ $rc -ne 0 ] && n=$((n+1)); echo "[go $v] build exit=$rc $(cat e.txt)"; done; echo "빌드가 막힌 판 $n / 4" =====
[go 1.21] build exit=0 
[go 1.27] build exit=0 
[go 1.27.1] build exit=0 
[go 1.28] build exit=1 go: go.mod requires go >= 1.28 (running go 1.27.1; GOTOOLCHAIN=local)
빌드가 막힌 판 1 / 4
(exit 0)
```

- ★★★ **`go 1.28` 만 막혔다** — `go: go.mod requires go >= 1.28 (running go 1.27.1; GOTOOLCHAIN=local)`. **`go` 줄은 「이 판 이상의 툴체인」이라는 요구**다. `go 1.21` 은 1.27.1 로 빌드된다.
  ★ `GOTOOLCHAIN=local` 이 아니면 `go` 명령은 **새 툴체인을 내려받으러 간다** — 이 문서는 그것을 **일부러 막았다**(네트워크 금지).
- `빌드가 막힌 판 1 / 4`.

비용 — 없다.

### (8) ★★ Cargo 는 정반대를 고른다 — 같은 모양을 Rust 로

**같은 요구 그래프**(`a 1.1.0` → `c "1.1.0"`, `b 1.0.0` → `c "1.0.0"`, 레지스트리에 `c 1.0.0`\~`1.3.0`)를 **로컬 디렉토리 레지스트리**로 만들어 `cargo run --offline`:

```text
===== 소스: config.toml =====
[source.crates-io]
replace-with = "local"

[source.local]
directory = "../vendor"
===== 소스: Cargo.toml =====
[package]
name = "app"
version = "0.1.0"
edition = "2021"

[dependencies]
a = "1.1.0"
b = "1.0.0"
===== 소스: main.rs =====
fn main() {
    println!("{}", a::which());
    println!("{}", b::which());
}
===== 소스: lib.rs =====
// 이 크레이트가 빌드될 때 붙은 c 의 판을 돌려준다.
pub fn which() -> String {
    format!("a 1.1.0 -> {}", c::V)
}
===== 명령: grep -H -A1 "^\[dependencies\]" vendor/*/Cargo.toml | grep -v "^--$\|dependencies"; ls vendor; cd app || exit 1; CARGO_HOME="$TMPDIR/cargohome" cargo run --offline -q 2>e.txt; echo "cargo run exit=$?"; sed "s/^/  (stderr) /" e.txt; grep -A1 "name = \"c\"" Cargo.lock =====
vendor/a-1.1.0/Cargo.toml-c = "1.1.0"
vendor/b-1.0.0/Cargo.toml-c = "1.0.0"
a-1.1.0
b-1.0.0
c-1.0.0
c-1.1.0
c-1.2.0
c-1.3.0
a 1.1.0 -> c 1.3.0
b 1.0.0 -> c 1.3.0
cargo run exit=0
name = "c"
version = "1.3.0"
(exit 0)
```

- ★★★ **`a 1.1.0 -> c 1.3.0` · `b 1.0.0 -> c 1.3.0`** · `Cargo.lock` 의 `c` 는 **`1.3.0`**. Cargo 의 `"1.1.0"` 은 **`^1.1.0`(1.1.0 이상 2.0.0 미만)** 이고, 그 범위에서 **가장 높은 판**을 고른다.
- ★★★ **같은 그래프에서 Go 는 `v1.1.0`, Cargo 는 `1.3.0`** — Go 는 **요구들의 최댓값**, Cargo 는 **범위 안의 최신**이다.
  그래서 Cargo 는 **`Cargo.lock` 없이는 재현이 안 되고**(새 판이 나오면 답이 바뀐다), Go 는 **`go.mod` 만으로 재현된다**((2)절).
- ★ [Rust 01번](../../../rust/syntax/01-cargo-crates-and-modules/)이 `Cargo.lock` 을 「cargo 가 쓰는 것 — 실제로 고른 의존성 버전」이라 적었다. 여기서 **왜 그 파일이 필요한지**가 보인다 — 선택이 **시간에 달려 있기** 때문이다.
- ★ 이 블록의 레지스트리는 `.cargo/config.toml` 의 `[source.local] directory = "../vendor"` 로 **crates.io 를 로컬 디렉토리로 갈아 끼운 것**이다. 크레이트마다 `.cargo-checksum.json`(`{"files":{},"package":null}`)을 두었다 — 배너에는 안 실었다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
```

규칙 불릿.

- ★★★ **`require M vX`** — 「`M` 은 **`vX` 이상**」. MVS 가 모든 요구 중 **최댓값**을 고른다. **최신은 고르지 않는다.**
- ★★ **`// indirect`** — 메인이 직접 import 하지 않는 모듈의 요구. `go mod tidy`·`-mod=mod` 가 적는다.
- ★★★ **`replace M [vX] => 경로|M' vY`** — **메인 모듈의 것만** 효력. 판을 빼면 모든 판을 바꾼다.
- ★★★ **`exclude M vX`** — 그 판을 **요구하는 줄을 지운다.** 올려 주는 규칙이 아니다.
- ★★ **메이저 2 이상은 경로에 `/vN`**. `go` 줄은 **툴체인 하한**이다.
- ★★ **`go.work` 의 `use DIR`** — 그 모듈을 **메인 모듈로 추가**한다. `replace` 없이 로컬 사본이 쓰인다. `-mod=mod` 와 **같이 못 쓴다.**

### 금지 사례 — 누가 막나

| 쓴 꼴 | 누가 막나 | 어디서 |
|---|---|---|
| `require example.com/d v2.0.0`(경로에 `/v2` 없음) | **`go` 명령** — `should be v0 or v1, not v2`(`go.mod` 파싱) | (7)절 |
| `go 1.28` 을 1.27.1 로(`GOTOOLCHAIN=local`) | **`go` 명령** — `go.mod requires go >= 1.28` | (7)절 |
| 워크스페이스에서 `-mod=mod` | **`go` 명령** — `-mod may only be set to readonly or vendor` | (6)절 |
| 의존 모듈의 `go.mod` 에 `replace` | ★★★ **아무도 안 막는다 — 조용히 무시** | (5)절 |
| `exclude` 로 의존의 하한을 지움 | ★★★ **아무도 안 막는다 — 하한 아래 판으로 빌드될 수 있다** | (4)절 |

## 어디서 틀리나

### 1. ★★★ 「`go` 는 호환되는 최신 판을 쓴다」

- (2)절 — **`최신(v1.3.0)을 고른 칸 0 / 9`.** 고르는 것은 **요구들의 최댓값**이다. 최신이 필요하면 **`go get M@latest` 로 요구를 올린다.**

### 2. ★★★ 「`b` 는 `c v1.0.0` 을 요구했으니 `c v1.0.0` 으로 빌드된다」

- (1)절 — **`b v1.0.0 → c v1.1.0`.** 빌드 목록에는 모듈마다 **판 하나**다.

### 3. ★★★ 「`exclude` 하면 다음 판으로 올라간다」

- (4)절 — **`v1.0.0` 으로 내려간 판**과 **`v1.3.0` 으로 튄 판**이 나왔다. `exclude` 는 **요구를 지우고 다시 고른다.**

### 4. ★★★ 「라이브러리 `go.mod` 에 `replace` 를 적어 두면 사용자에게도 적용된다」

- (5)절 `[1]` — **무시됐다.** 메인 모듈의 것만 효력이 있다.

### 5. ★★ 「`go get c@v1.0.0` 은 `c` 만 바꾼다」

- (3)절 — **`a` 가 `v1.1.0` → `v1.0.0` 으로 같이 내려갔다.** 메인 `go.mod` 의 **직접 요구**가 바뀌었다.

### 6. ★★ 「`go mod graph` 가 곧 쓰이는 판이다」

- (3)절 — 그래프에 `b@v1.0.0 → c@v1.0.0` 이 있지만 **쓰이는 `c` 는 `v1.1.0`** 이다.

### 7. ★★ 「워크스페이스에서도 늘 쓰던 `GOFLAGS` 로 된다」

- (6)절 `[2]` — **`-mod=mod` 가 에러**다.

### 8. ★ 「v2 는 `require … v2.0.0` 한 줄로 올린다」

- (7)절 — **경로가 바뀐다**(`/v2`). import 문도 같이 고쳐야 한다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **MVS — 요구 중 최댓값** | **`go` 명령의 알고리즘** — 명세에 `module` 이 0 줄 | (2)절 · `t41spec` · `t41src` |
| ★★★ `replace`·`exclude` 는 메인 모듈의 것만 | **`go` 명령의 규칙** | (5)절 |
| ★★ `exclude` = 요구를 지움 | **`go` 명령의 구현**(`modfile.go` 주석) | (4)절 |
| ★★ 메이저 2 이상 `/vN` | **`go` 명령의 규칙**(`go.mod` 파싱 에러) | (7)절 |
| `go` 줄 = 툴체인 하한 | **`go` 명령의 규칙** | (7)절 |
| 「뒤 판은 앞 판과 호환된다」 | ★★★ **모듈 작성자의 약속** — 아무도 검사하지 않는다 | (1)절 |
| `go: downloading` 줄 순서 | **이 판의 관찰**(병렬) | 흔들리는 칸 |
| Cargo — 범위 안의 최신 | **cargo 의 규칙**(이 머신 `cargo 1.92.0`) | (8)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 의존의 새 판이 필요하다 | ★★★ **`go get M@vX`** 로 **요구를 올린다** | MVS 는 최신을 저절로 안 고른다((2)절) |
| 의존의 특정 판이 깨졌다 | ★★ `exclude` **보다** 위 판을 `go get` | `exclude` 는 내려갈 수도 있다((4)절) |
| 포크·로컬 사본을 **내 빌드에서만** | **`replace`**(메인) | 사용자에게는 안 간다((5)절) |
| 여러 모듈을 **동시에 고치며** 시험 | ★★ **`go.work`** | `go.mod` 를 안 고친다((6)절) |
| 호환이 깨지는 변경을 배포 | **`/v2` 새 경로** | v1 사용자를 안 깨뜨린다((7)절) |
| 판을 낮추기 | `go get M@낮은판` + ★ **`go.mod` `diff` 확인** | 다른 의존이 같이 내려간다((3)절) |

## 핵심 문장

- ★★★ **MVS 는 「요구된 판 중 최댓값」을 고른다 — 최신이 아니다.** `9 / 9` · `최신을 고른 칸 0 / 9`.
- ★★★ **낮은 판을 요구한 의존도 고른 판에 붙어 빌드된다** — `b v1.0.0 → c v1.1.0`. `require` 는 하한이다.
- ★★★ **`replace`·`exclude` 는 메인 모듈의 것만 효력이 있다** — 의존의 `replace` 는 **조용히 무시된다.**
- ★★★ **`exclude` 는 요구를 지운다** — 하한 아래로 내려가거나(`v1.0.0`) 최신으로 튄다(`v1.3.0`).
- ★★ **`go.work` 는 `go.mod` 를 안 고치고 로컬 모듈을 메인으로 더한다** — 단 `-mod=mod` 와 같이 못 쓴다.
- ★★ **같은 그래프에서 Cargo 는 `1.3.0`**(범위 안의 최신) — 그래서 Cargo 는 잠금 파일이 필요하고 Go 는 `go.mod` 만으로 재현된다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 41번)
- [40번 주제](../40-package-visibility-naming-and-internal/)(가시성·`internal`) — ★ 목록상 선행 · `internal` 은 **import 경로 접두**로 막는다 — 모듈 경로가 그 접두가 된다. 그쪽은 **누가 import 하나**, 여기는 **어느 판이 오나**
- [01번 주제](../01-packages-imports-main-and-init/)(패키지·`init`) · [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)(`go` 줄이 루프 변수 의미를 바꾼다 — 여기는 `go` 줄이 **빌드를 막는 것**만)
- [Rust 01번](../../../rust/syntax/01-cargo-crates-and-modules/)(`Cargo.toml`·`Cargo.lock`) — ★ 잠금 파일의 정본은 그쪽 · [Python 42번](../../../python/syntax/42-modules-packages-and-import/)(`import` 와 패키지 — 판 선택은 **pip 의 몫**이라 그 편에 없다)
- 목록의 **52번 주제**(도구 — `go vet`·빌드 태그)

## 용어 풀이

- **모듈** — 판을 매겨 함께 배포하는 패키지 묶음. 뿌리의 `go.mod` 가 경로와 요구를 적는다.
- **메인 모듈** — `go` 명령을 부른 모듈. 워크스페이스에서는 `use` 한 모듈 전부.
- **요구(requirement)** — `require M vX`. 「`vX` 이상」이라는 하한.
- **빌드 목록** — 모듈마다 판 하나. `go list -m all`.
- **MVS(최소 버전 선택)** — 요구 그래프에서 모듈마다 요구된 판의 최댓값을 고르는 알고리즘.
- **`// indirect`** — 메인이 직접 import 하지 않는 모듈에 대한 요구 표시.
- **`replace` / `exclude`** — 모듈을 다른 판·경로로 바꾸기 / 그 판에 대한 요구 지우기. 메인 모듈에서만.
- **워크스페이스(`go.work`)** — 여러 로컬 모듈을 메인 모듈로 함께 쓰는 설정 파일.
- **모듈 프록시** — `@v/list`·`.info`·`.mod`·`.zip` 을 내주는 서버(여기서는 `file://` 디렉토리).
- **메이저 판 접미사(`/v2`)** — 메이저 2 이상 모듈의 경로 끝. 판이 다른 모듈을 **다른 경로**로 만든다.
- **캐럿 요구(Cargo `^1.1.0`)** — 「1.1.0 이상, 2.0.0 미만에서 **가장 높은 것**」.

---

## 더 들어가면

- ★ **`go.sum` 검증 실패·체크섬 DB** — 네트워크를 막고 `GOSUMDB=off` 로 **검증을 껐다.** `go.sum` 이 틀렸을 때의 에러는 **안 쟀다.**
- ★ **`retract`**(자기 판을 철회) · **모듈 그래프 가지치기**(의존의 `go` 줄에 따라 그래프를 어디까지 읽나) — 이 문서의 의존은 전부 `go 1.21` 한 판이라 **견주지 않았다.**
- ★ **`vendor/`**(`-mod=vendor`) — 안 던졌다.
- ★ v1 과 `/v2` 를 **한 빌드에 같이** 넣는 것 — 안 던졌다((7)절).
