# go/syntax/41 — 모듈: `go.mod`·버전 선택·워크스페이스 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `go list -m` 이 고른 판 · `Which()` 두 줄 · `go.mod` `diff` · `exit` · 에러 문구 · `9 / 9` · `0 / 9`.
> **순서만 흔들리는 칸** — `go: downloading` 줄(그래서 정렬해 실었다). 프록시 경로는 `<프록시>`, 작업 디렉토리는 `<작업>` 으로 캡처가 바꿔 적었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `c v1.1.0` — `b v1.0.0 → c v1.1.0` · `require example.com/c v1.1.0 // indirect` 가 더해진다

**출력**

```text
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

**왜 그런가**

- ★★★ 요구 `{v1.1.0(a), v1.0.0(b)}` 의 **최댓값**이 `v1.1.0` 이다. 빌드 목록은 **모듈마다 판 하나**라 `b` 도 그 판에 붙는다.
- ★★ `require` 는 **「이 판 이상」** 이다 — `b` 의 `c v1.0.0` 은 `v1.1.0` 으로 **만족된다**(같은 메이저 판의 호환은 **작성자의 약속**이고 `go` 명령은 검사하지 않는다).
- ★ `-mod=mod` 라서 `go run` 이 고른 판을 `// indirect` 로 적었다. 규칙은 **`go` 명령**의 것이다 — 명세에 `module` 이 0 줄이다.

### 2. 아홉 칸 전부 「두 요구의 최댓값」 — `9 / 9` · 최신 `v1.3.0` 은 `0 / 9`

**출력**

```text
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

**왜 그런가**

- ★★★ `mvs.go` 의 `BuildList` 주석 — 「**the highest version for each visited module**」. **요구된** 판 가운데 가장 높은 것이다. `v1.3.0` 은 누구도 요구하지 않아 **방문되지 않는다.**
- ★ `a v1.2.0` 이 있는데도 `a v1.1.0` 을 요구한 칸은 `a v1.1.0` 으로 빌드된다 — 규칙이 **모든 모듈에** 같다.

### 3. 선택이 `go.mod` 들의 요구만의 함수라서 — 대가는 「올리고 싶으면 직접 `go get` 한다」

- ★★★ 새 판이 프록시에 올라와도 **아무의 요구도 안 바뀌면 답이 안 바뀐다.** 그래서 **잠금 파일 없이** 누가 언제 빌드해도 같은 판이 나온다.
- ★★ 대가 — **보안 수정 판이 나와도 저절로 안 들어온다.** `go get M@latest`(또는 원하는 판)로 **요구를 올려** `go.mod` 에 남겨야 한다.
- ★ `go.sum` 은 판을 고르지 않는다 — **받은 내용의 해시**를 적는다.

### 4. 첫째는 `// indirect` 한 줄(`v1.1.0` → `v1.2.0`) · 둘째는 **`a` 를 `v1.1.0` → `v1.0.0` 으로 같이 내린다**

**출력**

```text
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

**왜 그런가**

- ★★ 첫째 — 메인이 `c v1.2.0` 을 **직접 요구**하니 최댓값이 `v1.2.0` 이 되고 둘 다 거기 붙는다.
- ★★★ 둘째 — `a v1.1.0` 은 `c v1.1.0` **이상**을 요구하므로 `c v1.0.0` 과 한 빌드에 못 있다. `go get` 이 **`a` 를 조건에 맞는 판(`v1.0.0`)으로 끌어내렸다** — `go: downgraded example.com/a v1.1.0 => v1.0.0`. 메인의 **직접 요구 줄**이 바뀐다.

### 5. 첫째는 `a v1.1.0 → c v1.0.0`(하한 아래) · 둘째는 `c` 가 목록에서 사라졌다가 `go run` 이 **`v1.3.0`(최신)** 을 적는다

**출력**

```text
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

**왜 그런가**

- ★★★ `exclude` 는 **그 판을 요구하는 줄을 지운다**(`modfile.go` — 「Drop any requirements on excluded versions」). 첫째는 `a` 의 요구가 지워져 **남은 `b` 의 `v1.0.0`** 이 최댓값이 됐다 — `a` 는 **자기 하한보다 낮은 판**에 붙었고 **경고가 없다.**
- ★★★ 둘째는 `c` 에 대한 요구가 **하나도 안 남아** `go list -m all` 에 `c` 가 없다. `a` 가 `c` 를 import 하니 `go run` 이 **「그 패키지를 주는 모듈」을 새로 찾아 최신 `v1.3.0`** 을 적었다.
- ★★ 「다음 판(`v1.2.0`)으로 올라간다」는 **어느 쪽에서도 안 나왔다.**

### 6. `[1]` `c v1.1.0`(의존의 `replace` 무시) · `[2]` `c v1.2.0` · `[3]` `c (로컬 디렉토리 cfork)`

**출력**

```text
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

**왜 그런가**

- ★★★ **`replace` 는 메인 모듈의 것만 효력이 있다.** `r` 의 `go.mod` 에 같은 줄이 있어도(받아 온 `.mod` 에 찍혔다) `[1]` 은 `v1.1.0` 이다.
- ★★ `[2]` — 같은 글자를 **메인**에 적자 `c v1.1.0 => example.com/c v1.2.0`.
- ★★ `[3]` — 판 없는 `replace` 는 **모든 판**을 바꾼다. `v1.1.0 => ./cfork` — **고른 판은 MVS 가, 내용은 디렉토리가** 준다.

### 7. `[2]` 는 `exit=1`(`-mod may only be set to readonly or vendor when in workspace mode`) · `[3]` 은 `example.com/c` 가 **판 없이** 찍힌다 · `replace` 줄 수 `0`

**출력**

```text
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

**왜 그런가**

- ★★★ `go.work` 의 `use` 는 그 디렉토리를 **메인 모듈로 더한다** — 메인 모듈에는 판이 없어서 `example.com/c` 가 판 없이 찍혔다. `a`·`b` 둘 다 **로컬 사본**에 붙었다.
- ★★★ 워크스페이스에서는 **`-mod=mod` 가 거부된다** — 이 문서의 다른 블록이 다 쓰는 설정인데 여기서만 `GOFLAGS` 를 비웠다.
- ★★ **`app/go.mod` 는 한 글자도 안 바뀌었다** — `replace` 없이 같은 효과. `GOWORK=off` 면 원래대로 `v1.1.0`.

### 8. `go.mod` 파싱 단계 — `version "v2.0.0" invalid: should be v0 or v1, not v2` · `go.mod` 의 경로와 **import 경로** 둘 다 `/v2` 로

**출력**

```text
===== 명령: go build -o /dev/null . 2>e.txt; echo "[require example.com/d v2.0.0] build exit=$?"; sed "s/^/  (stderr) /" e.txt; sed -i "s|example.com/d v2.0.0|example.com/d/v2 v2.0.0|" go.mod; sed -i "s|\"example.com/d\"|\"example.com/d/v2\"|" t41v2.go; go run . 2>/dev/null; echo "[경로에 /v2] run exit=$?" =====
[require example.com/d v2.0.0] build exit=1
  (stderr) go: errors parsing go.mod:
  (stderr) go.mod:5: require example.com/d: version "v2.0.0" invalid: should be v0 or v1, not v2
d v2.0.0
[경로에 /v2] run exit=0
(exit 0)
```

- ★★★ **빌드가 아니라 `go.mod` 를 읽는 자리에서** 막힌다(`errors parsing go.mod`). 메이저 판 2 이상은 **경로 자체가 `…/v2`** 인 다른 모듈이다.
- ★★ 고칠 자리 둘 — `require example.com/d/v2 v2.0.0` 과 **`import "example.com/d/v2"`**. 패키지 이름은 그대로 `d` 다.

### 9. `go 1.28` 만 — `go.mod requires go >= 1.28 (running go 1.27.1; GOTOOLCHAIN=local)` · 툴체인 판의 하한

**출력**

```text
===== 명령: n=0; for v in 1.21 1.27 1.27.1 1.28; do printf "module ex\n\ngo %s\n" $v > go.mod; go build -o /dev/null . 2>e.txt; rc=$?; [ $rc -ne 0 ] && n=$((n+1)); echo "[go $v] build exit=$rc $(cat e.txt)"; done; echo "빌드가 막힌 판 $n / 4" =====
[go 1.21] build exit=0 
[go 1.27] build exit=0 
[go 1.27.1] build exit=0 
[go 1.28] build exit=1 go: go.mod requires go >= 1.28 (running go 1.27.1; GOTOOLCHAIN=local)
빌드가 막힌 판 1 / 4
(exit 0)
```

- ★★ `go` 줄은 **「이 판 이상의 툴체인으로 빌드하라」** 는 요구다. `GOTOOLCHAIN=local` 이 아니면 새 툴체인을 **내려받으러 간다**(이 문서는 막았다).

### 10. Cargo 는 `c 1.3.0` — 범위 안의 최신 · 그래서 Cargo 는 `Cargo.lock` 이 있어야 재현된다

**출력**

```text
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

- ★★★ Cargo 의 `"1.1.0"` 은 **`^1.1.0`** 이고 그 범위의 **가장 높은 판**을 고른다 — `a`·`b` 둘 다 `1.3.0` 에 붙었다. Go 는 같은 그래프에서 `v1.1.0` 이다.
- ★★ Cargo 의 답은 **레지스트리에 새 판이 올라오면 바뀐다** — 그래서 **실제로 고른 판을 `Cargo.lock` 에 적어 고정**한다. Go 는 선택이 요구만의 함수라 `go.mod` 로 충분하다(`go.sum` 은 해시다).

### 11. 그래프는 「누가 무엇을 요구했나」, 빌드 목록은 「그래서 무엇을 골랐나」

**출력**

```text
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

- ★★★ `b@v1.0.0 → c@v1.0.0` 은 **요구**다. 같은 그래프에 `a@v1.1.0 → c@v1.1.0` 이 있고, MVS 가 둘 중 **최댓값**만 빌드 목록에 남긴다. `go list -m all` 이 **선택**, `go mod graph` 가 **요구**를 말한다.
- ★ `go mod why -m` 은 import 그래프의 **가장 짧은 길 하나**만 찍는다 — `b` 쪽 길은 안 나왔다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ MVS 격자 (`t41grid`) | 로컬 파일 프록시 · 요구 3 × 3 · 탭 4칸 검사 | 캡처마다 | **`9 / 9` · `0 / 9`** |
| ★★ `go get` · `exclude` · `replace` (`t41get`·`t41excl`·`t41exclone`·`t41deprep`) | 블록마다 새 모듈 캐시 | 캡처마다 | `a` 동반 하향 · 하한 아래 · 의존 `replace` 무시 |
| ★★ `go.work` (`t41work`) | `go work init` · `GOFLAGS` × `GOWORK` | 캡처마다 | `-mod=mod` 거부 · `replace` 0 줄 |
| ★ `/v2` · `go` 줄 (`t41v2`·`t41tc`) | 파싱 에러 · `GOTOOLCHAIN=local` | 캡처마다 | `1 / 4` |
| ★ Cargo 대비 (`t41cargo`) | 디렉토리 레지스트리 · `--offline` | 캡처마다 | `c 1.3.0` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 버전 선택·`replace`·`exclude`·`go.work` 규칙 | **`go` 명령**(이 판 1.27.1) — 명세가 아니다 |
| `go: downloading` 줄 순서 | 병렬 내려받기 — 정렬해 실었다 |
| `go work init` 의 `go` 줄 | 툴체인 판 |
| Cargo 의 선택 | **cargo 1.92.0** |
| 체크섬 검증 | ★ **껐다**(`GOSUMDB=off`) — 이 문서는 검증 실패를 재지 않았다 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다. 네트워크는 필요 없다(프록시를 캡처가 만든다).
