# Go — 문법·API 주제 목록

> 1단계 리스트업이다. 3파일(질문·서머리·정답)이 **있는 주제는 제목에 링크가 걸려 있다**(2026-09-24 기준 **12 / 52**). 나머지는 아직 없다.
> 기준 소스: [Go 명세](https://go.dev/ref/spec) (확인한 판 `go1.27`, 2026-05-26) · [표준 라이브러리](https://pkg.go.dev/std) (`go1.27.1`) · [Effective Go](https://go.dev/doc/effective_go) · 버전 표기는 각 릴리스 노트(`https://go.dev/doc/go1.NN`)
> 실행 검증: **가능**. 이 머신에 Go 툴체인이 들어왔다 — `go version` 이 `go version go1.27.1 linux/amd64` 라고 답한다(2026-09-24 실측). `gofmt`·`go vet`·`go tool compile`·`go list` 도 같은 판이다.\
> 3파일의 코드 예시는 **전부 돌려서 출력을 파일로 캡처해 싣는다** — 「실행 검증 안 됨」 표시는 쓰지 않는다.\
> 명세 인용도 웹이 아니라 이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` (`Language version go1.27 (May 26, 2026)`)에서 직접 뜬다 — 위 기준 소스의 판 표기를 그 파일로 확인했다.
> 기준일 2026-09-24. (2026-09-20 의 「실행 검증 불가 — 툴체인 없음」 선언은 01\~04 배치에서 실측으로 갈아 끼웠다. 05번 이후 주제도 같은 전제로 쓴다.)

## 이 언어에서 무엇을 자르는 축

Go는 문법 표면이 작다. 그래서 **문법 규칙 수가 아니라 「조용히 틀리는 자리」가 주제 수를 정한다.**
같은 이유로 이 목록은 세 축으로 자른다.

1. **값이 어떻게 복사되는가** — 제로값·값 의미론·슬라이스와 맵의 참조 성질. Go에서 버그가 가장 많이 숨는 층이다.
2. **인터페이스와 오류가 어떤 값인가** — 암묵 구현, 인터페이스의 (타입, 값) 쌍, 값으로서의 `error`.
3. **동시성의 수명 관리** — 고루틴은 시작이 싸고 **끝내기가 어렵다**. 채널·`select`·`context`가 전부 이 하나를 둘러싼다.

옆 축인 [`../언어-특성/README.md`](../언어-특성/README.md)는 *Go를 고를 것인가*를 다룬다.
GC 설계·기동 시간·단일 바이너리·"작은 언어"의 찬반은 **거기**고, 여기는 **그래서 어떻게 쓰는가**다.
예컨대 "고루틴이 왜 싼가"는 노트, "고루틴을 어떻게 끝내는가"는 이 목록(31번)이다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | [패키지 선언·import·`main`과 `init`](01-packages-imports-main-and-init/) | 문법 | 한 프로그램이 어떤 순서로 초기화되는지 설명하고, `init` 여러 개와 패키지 의존 순서에서 실행 순서를 예측할 수 있다 | — | — | A |
| 02 | [변수 선언 세 형태와 제로값](02-variable-declarations-and-zero-values/) | 문법 | `var`·`:=`·선언 블록을 언제 쓰는지 판단하고, 선언만 한 값이 무엇이 되는지를 타입별로 말할 수 있다 | 01 | [`../../../variables-and-memory/`](../../../variables-and-memory/) — 변수·메모리 일반은 거기, 여기는 Go 제로값 규칙으로 좁힘 | A |
| 03 | [상수·`iota`·타입 없는 상수](03-constants-iota-and-untyped-constants/) | 문법 | 타입 없는 상수가 대입 지점에서 어떤 타입이 되는지 예측하고, `iota` 블록의 값 전개를 손으로 적을 수 있다 | 02 | — | B |
| 04 | [수치 타입과 명시 변환·오버플로·정수 나눗셈](04-numeric-types-conversions-and-integer-division/) | 문법 | 왜 `int`와 `int64`가 섞이지 않는지 설명하고, 오버플로·절삭·부호 변환이 언제 조용히 일어나는지 판단할 수 있다 | 02 | [`../../../data-representation/`](../../../data-representation/) — 2의 보수 표현 자체는 거기, 여기는 Go의 변환 규칙으로 좁힘 | A |
| 05 | [배열과 슬라이스는 무엇이 다른가](05-arrays-vs-slices-value-and-header/) | 문법 | 배열이 값이고 슬라이스가 헤더(포인터·len·cap)라는 사실로부터 대입·함수 인자 전달의 결과를 예측할 수 있다 | 02 | [`../../../../data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) — 동적 배열 자료구조는 거기, 여기는 Go 슬라이스 헤더의 표면으로 좁힘 | A |
| 06 | [`len`/`cap`과 `append`의 재할당](06-len-cap-and-append-reallocation/) | 문법 | `append` 후 원본 배열이 공유되는지 새로 잡혔는지를 `cap`으로 판단하고, 성장 전략이 왜 구현 세부인지 설명할 수 있다 | 05 | [`../../../../data-structure/01-dynamic-array/`](../../../../data-structure/01-dynamic-array/) — 증폭 상각 분석은 거기 | A |
| 07 | ★ [슬라이스 공유로 조용히 틀리는 자리](07-slice-sharing-silent-bugs/) | 관용구 | 부분 슬라이스에 `append` 했을 때 원본이 덮이는 경우를 코드만 보고 짚어내고, 그 버그가 왜 에러 없이 지나가는지 설명할 수 있다 | 06 | [`../../../../ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) — 조용한 실패 일반론은 거기, 여기는 슬라이스 별칭 한 사례로 좁힘 | A |
| 08 | [`copy`·3-인덱스 슬라이스·재슬라이싱의 메모리 유지](08-copy-three-index-slicing-and-memory-retention/) | 관용구 | 공유를 끊어야 하는 자리를 골라 `copy`나 `s[a:b:c]`로 막고, 작은 조각이 큰 배열을 살려 두는 누수를 진단할 수 있다 | 07 | — | A |
| 09 | [맵: 선언·comma-ok·`delete`·순회 순서](09-maps-declaration-comma-ok-delete-and-iteration-order/) | 문법 | 없는 키를 읽으면 왜 제로값이 나오는지, 순회 순서가 무작위화된 이유와 그에 의존한 코드가 어떻게 깨지는지 말할 수 있다 | 02 | [`../../../../data-structure/05-hashmap/`](../../../../data-structure/05-hashmap/) · [`29-open-addressing`](../../../../data-structure/29-open-addressing/) — 해시 테이블 원리는 거기, 여기는 Go 맵의 표면과 보증으로 좁힘 | A |
| 10 | [문자열·`byte`·`rune`과 UTF-8 순회](10-strings-bytes-runes-and-utf8-iteration/) | 문법 | 인덱싱이 바이트를 주고 `range`가 코드포인트를 주는 차이를 설명하고, 한글 문자열의 `len`을 예측할 수 있다 | 04 | [`../../../data-representation/`](../../../data-representation/) — 인코딩 일반은 거기 | A |
| 11 | [`strings`·`strconv`·`bytes`·`unicode/utf8`](11-strings-strconv-bytes-and-unicode-utf8/) | 표준 API | 문자열 조작을 어느 패키지로 할지 고르고, `Builder`로 이어붙이는 자리와 `+`로 충분한 자리를 판단할 수 있다 | 10 | — | B |
| 12 | [함수: 다중 반환·명명 반환값·가변 인자](12-functions-multiple-returns-named-results-and-variadics/) | 문법 | `(T, error)` 관례가 왜 언어 문법에서 나오는지 설명하고, 명명 반환값이 `defer`와 만날 때의 효과를 예측할 수 있다 | 02 | — | A |
| 13 | 클로저와 변수 캡처, 루프 변수 의미 변경(1.22) | 문법 | 클로저가 값이 아니라 변수를 잡는다는 사실로 출력 결과를 예측하고, 같은 코드가 1.21과 1.22에서 왜 다른지 말할 수 있다 | 12 | — | A |
| 14 | `for`의 네 형태 · 정수 range(1.22) · 함수 range(1.23) | 문법 | `range`가 복사를 만드는 자리를 짚고, `for i := range 10`과 반복자 함수 순회가 어느 버전부터인지 말할 수 있다 | 13 | — | A |
| 15 | `switch`·타입 스위치·`fallthrough`·라벨·`goto` | 문법 | Go의 `switch`가 왜 기본으로 안 흘러내리는지, 라벨 `break`/`continue`가 필요한 중첩 루프를 골라낼 수 있다 | 14 | — | B |
| 16 | 포인터와 값 복사 의미론, `new`와 `make` | 문법 | 어떤 대입이 복사이고 어떤 것이 공유인지 판단하고, `new`와 `make`가 갈리는 이유를 타입으로 설명할 수 있다 | 05 | [`../../../variables-and-memory/`](../../../variables-and-memory/) — 포인터 개념 자체는 거기 | A |
| 17 | 구조체: 리터럴·비교 가능성·필드 태그·정렬 | 문법 | 구조체가 `==`로 비교되는 조건을 말하고, 필드 순서가 크기에 미치는 영향을 설명할 수 있다 | 16 | [`../../../data-representation/`](../../../data-representation/) — 정렬·패딩 일반은 거기 | A |
| 18 | 임베딩과 필드·메서드 승격 | 문법 | 임베딩이 상속이 아니라 승격임을 예로 보이고, 이름이 충돌할 때 어느 쪽이 이기는지 예측할 수 있다 | 17 | [`../../../oop-basics/`](../../../oop-basics/) — 상속·합성 논의는 거기, 여기는 Go 승격 규칙으로 좁힘 | A |
| 19 | ★ 메서드 집합: 값 리시버 대 포인터 리시버 | 문법 | 어떤 타입이 어떤 인터페이스를 만족하는지 메서드 집합 규칙으로 판정하고, 값으로 담았더니 인터페이스 대입이 안 되는 에러를 해석할 수 있다 | 18 | — | A |
| 20 | 인터페이스 선언과 암묵 구현 | 문법 | `implements` 없이 만족되는 구조가 설계에 무엇을 바꾸는지 설명하고, 인터페이스를 소비자 쪽에 두는 이유를 말할 수 있다 | 19 | [`../../../oop-basics/`](../../../oop-basics/) — 다형성 일반은 거기 | A |
| 21 | ★ `nil` 인터페이스와 `nil` 포인터를 담은 인터페이스 | 문법 | 인터페이스 값이 (타입, 값) 쌍임을 근거로 `err != nil`이 참이 되는 코드를 만들어 보이고, 그 함정을 막는 반환 규칙을 세울 수 있다 | 20 | — | A |
| 22 | 타입 단언·`any`·`comparable` | 문법 | 단언의 두 형태(패닉형·comma-ok형)를 고르고, 런타임 타입 검사에 기대는 설계가 어디서 값을 잃는지 판단할 수 있다 | 20 | — | B |
| 23 | `error` 인터페이스와 값으로서의 오류 | 문법 | 오류가 예외가 아니라 반환값이라는 선택의 결과를 호출부 코드 모양으로 설명할 수 있다 | 20 | — | A |
| 24 | 오류 래핑 `%w`와 `errors.Is`/`As`/`Join` | 표준 API | 래핑 체인을 그리고 `Is`와 `As`를 언제 쓰는지 고를 수 있다 — `%w`·`Is`/`As`는 1.13, `Join`은 1.20부터 | 23 | — | A |
| 25 | 센티넬 오류 대 커스텀 오류 타입 — 오류 표면 설계 | 관용구 | 호출자가 분기해야 하는 오류와 로그로 충분한 오류를 갈라, 패키지가 공개할 오류 표면을 설계할 수 있다 | 24 | [`../../../../ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) — 실패 분류 일반은 거기, 여기는 Go 오류 값 설계로 좁힘 | A |
| 26 | `defer`: 평가 시점·LIFO·명명 반환값 수정·루프 안의 `defer` | 문법 | `defer`의 인자가 언제 평가되는지로 출력을 예측하고, 루프에서 파일 핸들이 쌓이는 코드를 고칠 수 있다 | 12 | — | A |
| 27 | `panic`·`recover`와 쓰는 자리 | 문법 | 패닉이 스택을 어떻게 풀고 `recover`가 어디서만 듣는지 설명하고, 라이브러리 경계에서 패닉을 오류로 바꿀지 판단할 수 있다 | 26 | [`../../../../systems/call-stack/`](../../../../systems/call-stack/) — 스택 되감기 일반은 거기 | B |
| 28 | 고루틴: `go` 문·시작 비용·종료 조건 | 문법 | `go f()`가 만드는 것이 무엇인지, `main`이 끝나면 왜 다 사라지는지 설명할 수 있다 | 12 | [`../../../process-thread/`](../../../process-thread/) — 스레드·프로세스 일반은 거기 · [`../언어-특성/README.md`](../언어-특성/README.md) §2 — 고루틴 단가의 논증은 거기 | A |
| 29 | 채널: 버퍼·방향·`close`·`range`·`nil` 채널 | 문법 | 버퍼 유무로 송수신이 언제 막히는지 예측하고, 닫힌 채널과 `nil` 채널의 동작 차이를 말할 수 있다 | 28 | [`../../../../ops-patterns/05-backpressure/`](../../../../ops-patterns/05-backpressure/) — 배압 패턴은 거기, 여기는 채널의 차단 규칙으로 좁힘 | A |
| 30 | `select`·`default`·타임아웃 | 문법 | 여러 채널을 기다리는 코드를 쓰고, `default`가 붙는 순간 의미가 어떻게 바뀌는지 설명할 수 있다 | 29 | — | A |
| 31 | ★ 고루틴 누수 | 관용구 | 받는 쪽이 사라진 송신, 취소 없는 대기 같은 누수 형태를 코드에서 짚고, 누수를 테스트로 잡는 방법을 세울 수 있다 | 30 | [`../../../../ops-patterns/failure-modes/`](../../../../ops-patterns/failure-modes/) — 실패 모드 총론은 거기 | A |
| 32 | `sync`: `Mutex`·`RWMutex`·`WaitGroup`·`Once` | 표준 API | 채널로 풀 문제와 뮤텍스로 풀 문제를 갈라 고르고, 복사하면 안 되는 타입이 무엇인지 말할 수 있다 | 29 | [`../../../process-thread/`](../../../process-thread/) — 동기화 원리는 거기 | A |
| 33 | `sync/atomic`과 `sync.Map`을 고르는 자리 | 표준 API | 원자 연산으로 충분한 경우와 아닌 경우를 구분하고, `sync.Map`이 이기는 접근 패턴을 말할 수 있다 | 32 | — | C |
| 34 | ★ `context`: 취소·데드라인·값 | 표준 API | 취소가 호출 트리를 따라 어떻게 전파되는지 그리고, `context`를 첫 인자로 받는 관례와 값 전달 남용의 경계를 판단할 수 있다 | 31 | [`../../../../ops-patterns/deadline-propagation/`](../../../../ops-patterns/deadline-propagation/) — 데드라인 전파 패턴은 거기, 여기는 `context` API 사용법으로 좁힘 | A |
| 35 | 데이터 레이스와 `-race` | 관용구 | 레이스를 만드는 최소 코드를 쓰고, 검출기가 무엇을 보장하고 무엇을 못 보는지 말할 수 있다 | 32 | [`../../../process-thread/`](../../../process-thread/) — 경쟁 조건 일반은 거기 | B |
| 36 | Go 메모리 모델을 코드에서 읽기 | 관용구 | 어떤 연산이 happens-before를 만드는지 채널·뮤텍스·`Once`로 설명하고, "잘 돌아가더라"가 왜 근거가 아닌지 말할 수 있다 | 35 | — | C |
| 37 | 제네릭: 타입 파라미터와 제약 인터페이스(1.18) | 문법 | 타입 파라미터를 쓸 자리와 인터페이스로 충분한 자리를 가르고, `~` 제약과 제약 인터페이스의 문법을 읽을 수 있다 | 22 | — | B |
| 38 | `slices`·`maps`·`cmp`(1.21) | 표준 API | 직접 쓰던 정렬·탐색·비교를 표준 제네릭 함수로 바꾸고, 정렬 안정성과 비교 함수 계약을 말할 수 있다 | 37 | [`../../../../algorithm/01-elementary-sort/`](../../../../algorithm/01-elementary-sort/) — 정렬 알고리즘은 거기, 여기는 API 선택으로 좁힘 | B |
| 39 | `iter`와 사용자 정의 반복자(1.23) | 표준 API | `iter.Seq`/`Seq2`를 반환하는 함수를 쓰고, 반복자가 조기 종료될 때 정리 코드가 어떻게 도는지 설명할 수 있다 | 38 | — | C |
| 40 | 패키지 가시성·이름 규칙·`internal` | 문법 | 대문자 하나가 공개 API 계약을 만든다는 점에서 패키지 경계를 설계하고, `internal`이 막는 것을 말할 수 있다 | 01 | — | B |
| 41 | 모듈: `go.mod`·버전 선택·워크스페이스 | 관용구 | 최소 버전 선택이 무엇을 고르는지 설명하고, 의존 충돌·`replace`·워크스페이스를 판단할 수 있다 | 40 | — | B |
| 42 | `fmt`: 포맷 동사·`Stringer`·`Errorf` | 표준 API | `%v`·`%+v`·`%#v`의 출력을 예측하고, `String()` 안에서 자기 자신을 출력해 무한 재귀가 나는 자리를 짚을 수 있다 | 20 | — | B |
| 43 | `io.Reader`/`Writer`와 조합 | 표준 API | 작은 인터페이스 둘이 왜 표준 라이브러리 전체를 엮는지 설명하고, `Read`의 계약(n>0과 `io.EOF`)을 지켜 읽는 루프를 쓸 수 있다 | 20 | — | A |
| 44 | `os`·`bufio`·`io.Copy` — 파일과 표준 입출력 | 표준 API | 버퍼링이 언제 필요한지 판단하고, `Flush`·`Close` 누락으로 데이터가 사라지는 자리를 짚을 수 있다 | 43 | — | B |
| 45 | `encoding/json`: 태그·`omitempty`·포인터·숫자·스트리밍 | 표준 API | 언마샬 대상이 포인터여야 하는 이유, 빠진 필드와 `null`을 구분하는 방법, `float64`로 들어오는 숫자 문제를 다룰 수 있다 | 17 | — | A |
| 46 | `net/http` 서버: `ServeMux` 패턴(1.22)·`Handler`·미들웨어 | 표준 API | 핸들러가 인터페이스 하나라는 점에서 미들웨어를 직접 쓰고, 1.22부터 라우팅 패턴이 무엇을 흡수했는지 말할 수 있다 | 43 | [`../../../../systems/server-design/`](../../../../systems/server-design/) — 서버 구조 설계는 거기, 여기는 `net/http` 표면으로 좁힘 | A |
| 47 | ★ `net/http` 클라이언트: `Client` 재사용·타임아웃·`Body` 닫기 | 표준 API | 기본 `Client`에 타임아웃이 없다는 사실의 결과를 설명하고, `Body`를 안 닫아 커넥션이 재사용되지 않는 코드를 고칠 수 있다 | 46 | [`../../../../ops-patterns/01-retry-backoff/`](../../../../ops-patterns/01-retry-backoff/) — 재시도 정책은 거기, 여기는 클라이언트 설정과 자원 반납으로 좁힘 | A |
| 48 | `time`: `Time`·`Duration`·단조 시계·`Timer`/`Ticker`(1.23 변경) | 표준 API | 경과 시간을 재는 올바른 방법을 고르고, 1.23부터 타이머 채널과 GC 동작이 어떻게 달라졌는지 말할 수 있다 | 30 | — | A |
| 49 | `testing`: 표 기반 테스트·`t.Run`·`t.Cleanup`·`t.Parallel` | 표준 API | 케이스를 표로 접고, 병렬 하위 테스트에서 자원 정리 순서를 예측할 수 있다 | 14 | — | A |
| 50 | 벤치마크·`testing.B`·프로파일 읽기 | 표준 API | 벤치마크가 최적화로 지워지지 않게 쓰고, 할당 수치(`-benchmem`)를 근거로 개선 여부를 판단할 수 있다 | 49 | — | C |
| 51 | `os/signal`과 정상 종료 | 관용구 | 신호를 받아 `context`를 취소하고 진행 중 요청을 마무리하는 종료 경로를 코드로 세울 수 있다 | 34 | [`../../../../ops-patterns/19-graceful-shutdown/`](../../../../ops-patterns/19-graceful-shutdown/) — 종료 패턴은 거기, 여기는 Go에서의 배선으로 좁힘 | B |
| 52 | 도구: `gofmt`·`go vet`·빌드 태그·`go:embed`·탈출 분석 읽기 | 관용구 | 포맷 논쟁이 왜 없는지 설명하고, `-gcflags=-m` 출력으로 값이 힙으로 갔는지 판단할 수 있다 | 41 | [`../../../memory-management/`](../../../memory-management/) — 스택·힙 일반은 거기 | C |

★ 표시는 **조용히 틀리는 자리** — 컴파일도 되고 테스트도 통과하는데 값이 어긋나는 주제다. 다른 것을 줄이더라도 이 여섯(7·8·19·21·31·47)은 먼저 쓴다.

## 기존 주제와 겹치는 것

| 겹친 주제 | 기존 위치 | 어떻게 좁혔나 |
|---|---|---|
| 5·6 슬라이스 | [`data-structure/01-dynamic-array`](../../../../data-structure/01-dynamic-array/) | 증폭 상각·성장 전략은 기존 주제. 여기서는 슬라이스 헤더 3필드와 `append` 재할당 **관찰 방법**만 |
| 9 맵 | [`data-structure/05-hashmap`](../../../../data-structure/05-hashmap/) · [`29-open-addressing`](../../../../data-structure/29-open-addressing/) | 해시 충돌 처리는 기존 주제. 여기서는 comma-ok·순회 무작위화·주소를 못 잡는 제약 |
| 28·32·35 동시성 | [`foundations/process-thread`](../../../process-thread/) | 스레드·경쟁 조건 개념은 기존 주제. 여기서는 `go`/채널/`sync`의 **문법과 계약** |
| 34 `context` | [`ops-patterns/deadline-propagation`](../../../../ops-patterns/deadline-propagation/) | 데드라인 전파 설계는 기존 주제. 여기서는 `context` 타입의 API와 관례 |
| 51 정상 종료 | [`ops-patterns/19-graceful-shutdown`](../../../../ops-patterns/19-graceful-shutdown/) | 패턴 자체는 기존 주제. 여기서는 `signal.NotifyContext`→`Server.Shutdown` 배선 |
| 47 HTTP 클라이언트 | [`ops-patterns/01-retry-backoff`](../../../../ops-patterns/01-retry-backoff/) | 재시도·백오프 정책은 기존 주제. 여기서는 `Client` 필드와 자원 반납 |
| 46 HTTP 서버 | [`systems/server-design`](../../../../systems/server-design/) | 서버 아키텍처는 기존 주제. 여기서는 `Handler` 인터페이스와 1.22 라우팅 패턴 |
| 38 정렬 | [`algorithm/01-elementary-sort`](../../../../algorithm/01-elementary-sort/) | 알고리즘은 기존 주제. 여기서는 `slices.Sort`와 `SortFunc` 중 무엇을 고르나 |
| 18·20 인터페이스·임베딩 | [`foundations/oop-basics`](../../../oop-basics/) | 다형성·상속 논의는 기존 주제. 여기서는 승격 규칙과 암묵 구현의 **문법적 결과** |
| 4·10·17 표현 | [`foundations/data-representation`](../../../data-representation/) | 2의 보수·인코딩·패딩은 기존 주제. 여기서는 Go 변환 규칙과 `rune`/`byte` |
| 7·25·31 실패 | [`ops-patterns/failure-modes`](../../../../ops-patterns/failure-modes/) | 실패 분류 총론은 기존 주제. 여기서는 Go 고유의 세 사례 |
| 2·16 변수·포인터 | [`foundations/variables-and-memory`](../../../variables-and-memory/) | 메모리 모형은 기존 주제. 여기서는 제로값 규칙과 `new`/`make` |
| 27 패닉 | [`systems/call-stack`](../../../../systems/call-stack/) | 스택 되감기는 기존 주제. 여기서는 `defer`/`recover`의 동작 순서 |
| 52 탈출 분석 | [`foundations/memory-management`](../../../memory-management/) | GC·할당 일반은 기존 주제. 여기서는 `-gcflags=-m` 출력 읽기 |

`history/` 에는 **Go 편이 없다**(언어 갈래는 java·js·python·rust뿐이고, 나머지는 spring·database·network·web이다). 그래서 Go는 "언제 들어온 기능인가"를 이 목록 안에서 버전 표기로 처리한다 — 역사 서술은 하지 않고 **「어느 버전부터」만** 적는다.

## 뺀 것과 이유

| 뺀 것 | 이유 |
|---|---|
| GC 설계·STW 지연·힙 튜닝의 논증 | [`../언어-특성/README.md`](../언어-특성/README.md) §3. 여기는 문법·API 축이다 |
| 고루틴이 왜 2KB인가·M:N 스케줄러 내부 | 같은 노트 §2. 여기서는 `go`/채널의 **사용법**만 |
| 단일 바이너리·기동 시간·배포 | 같은 노트 §4~5 |
| "Go를 언제 고르는가"·표현력 비용 | 같은 노트 §6·§8~9 |
| `cgo`·어셈블리·`unsafe` 심화 | 표면이 넓고 학습 단계에서 인출 빈도가 낮다. 2단계 이후 별도 묶음으로 |
| `reflect` 심화 | 45(JSON)에서 필요한 만큼만 닿는다. 직접 쓰는 일은 드물다 |
| `crypto/*`·`database/sql`·`text/template` | 언어 문법이 아니라 도메인 API다. 필요해지는 시점에 별도 주제로 |
| 표준 라이브러리 전수 순회 | 200개가 넘는다. 위 목록은 **언어 표면과 맞닿은 패키지만** 고른 것이다 |

## 버전 기준

- **기준 판**: 명세 `go1.27`(2026-05-26) · 표준 라이브러리 `go1.27.1` 문서. 3파일 작성 시점에 판이 올라가면 표기만 갱신한다.
- **버전 의존 기능은 반드시 「어느 버전부터」를 적는다.** 이 목록이 이미 고정한 것:

| 기능 | 버전 | 주제 |
|---|---|---|
| 오류 래핑 `%w`·`errors.Is`/`As` | 1.13 | 24 |
| 제네릭(타입 파라미터) | 1.18 | 37 |
| `errors.Join` | 1.20 | 24 |
| `min`/`max`/`clear` 내장 함수 · `slices`·`maps`·`cmp` · `log/slog` | 1.21 | 38 |
| **`for` 루프 변수가 반복마다 새로 생성** | 1.22 | 13 |
| 정수 `range`(`for i := range 10`) | 1.22 | 14 |
| `ServeMux` 메서드·와일드카드 라우팅 패턴 | 1.22 | 46 |
| `math/rand/v2` | 1.22 | — (필요 시 38에 붙인다) |
| 함수 `range`(반복자)·`iter` 패키지 | 1.23 | 14·39 |
| `time.Timer`/`Ticker` 채널 비버퍼화·조기 GC | 1.23 | 48 |
| `unique` 패키지 | 1.23 | — |

- 1.24 이후(제네릭 타입 별칭, `os.Root`, `testing/synctest` 등)는 **3파일 작성 시점에 해당 릴리스 노트를 직접 열어 확인한 뒤** 표기한다. 이 목록에서는 확인한 것만 적었다.
- `go.mod`의 `go` 지시자가 **언어 의미를 바꾸는 경우**(1.22 루프 변수, 1.23 타이머)가 있다 — 13·48 주제에서 이 점을 반드시 다룬다.
