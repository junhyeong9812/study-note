# language/21-language-choice-tradeoffs — 정답

## 정답

### 1. 순위가 놓치는 것

- 벤치마크는 "맞게 돌 때 얼마나 빠른가"만 잰다. 운영 비용은 대개 "틀렸을 때 무슨 일이 벌어지나"에서 난다.
- 세 축(원고 [languages/README.md](../../../languages/README.md) 축 ①): 틀렸을 때 어떻게 틀리는가 · 그 도메인의 지식이 어디에 쌓여 있는가 · 5년 뒤 누가 고치는가. 성능은 이 셋 안에 흩어져 있다.
- 조용한 실패가 더 비싼 이유: 크래시는 그 자리에서 알림·로그가 남고 영향이 멈춘다. 조용한 오답은 틀린 값으로 계속 돌며 다른 데이터로 번지고, 대사나 민원으로 늦게 발견돼 되돌릴 범위가 커진다.

### 2. 네 등급과 `MAX + 1`

```text
  컴파일 거부      Go: 상수식 math.MaxInt32 + 1 을 int32에 → "overflows" 컴파일 오류
  즉시 예외        Java: Math.addExact → ArithmeticException
  조용한 틀린 값   Java int +, Go int32 + → -2147483648 / JS (2147483647+1)|0 → -2147483648
  미정의 동작      C: 부호 있는 int 넘침 (language 20)
  (넘침 없음)      Python int: 2147483648 — 임의 정밀도
```

- 실험 1 출력 그대로다. 같은 Java·Go에서도 연산(`+` vs `addExact`)이나 상수/변수에 따라 등급이 다르다.

### 3. 범위 밖 인덱스와 파싱 (실험 1)

| | `arr[5]` (길이 3) | `"12a"` → 숫자 |
|---|---|---|
| Java 21 | `ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3` | `NumberFormatException` |
| Go 1.23 | `panic: runtime error: index out of range [5] with length 3`(종료 코드 2) | `strconv.Atoi` 에러 반환(`_`로 버리면 0) |
| Python 3.12 | `IndexError('list index out of range')` | `ValueError` |
| node 22 | `undefined` | `Number` → `NaN`, `parseInt` → `12` |
| C(gcc 13 -O0) | UB — 이 실험에서는 오류 없이 어떤 정수(실행마다 다름, 예: `159879248`)가 찍혔다. 다른 결과도 허용된다 | `atoi` → `12` |

- 같은 언어 안에서 갈리는 예
  - JS: `Number("12a")`는 `NaN`(검사 가능한 신호), `parseInt("12a")`는 `12`(앞부분만 읽고 조용히 성공).
  - Java: `x + 1`은 조용히 감기고, `Math.addExact(x, 1)`은 예외.
  - Python: `arr[5]`는 `IndexError`지만 `arr[-1]`은 오류가 아니라 마지막 원소(3)다.

### 4. Go 에러 무시와 node 거부

- `n, _ := strconv.Atoi(s)`: 컴파일 통과. 에러가 버려지고 `n`은 0(실험 1).
- `n, err := ...`에서 `err`를 안 쓰면: **컴파일 오류** `declared and not used: err`(실험 1 `unused.go`). Go는 "받고 잊기"는 막지만 "명시적으로 버리기"는 막지 않는다. 그래서 `errcheck` 같은 린터가 필요하다(원고 go 언어-특성 §6).
- node 22: 처리 안 한 `Promise.reject`가 잡히지 않은 예외로 올라가 프로세스가 exit 1로 끝났다. Node.js 문서: `--unhandled-rejections`의 기본이 v15.0.0부터 `throw`(그 전엔 경고).

### 5. 두 축과 통화

| 진영 | 메모리 안전 | 데이터 레이스 없음 | 지불 통화 |
|---|---|---|---|
| C/C++ | 없음(UB) — 개발자 규율 | 없음(UB) | 운영 중 사고 |
| JVM(Java·Kotlin) | 런타임(GC·경계 검사) | 보장 안 함 — 명세가 결과를 제한(JLS 17장)하지만 값은 어긋남 | 실행 자원 |
| Go | 런타임(GC·경계 검사) | 보장 안 함 — 여러 워드 값의 경쟁은 메모리 손상 가능 | 실행 자원 |
| Rust | 컴파일러(소유권·차용·수명) — safe Rust 한정, `unsafe`는 개발자 몫 | 컴파일러(`Send`·`Sync`) — safe Rust 한정 | 사람의 시간(학습·설계·빌드) |

- 어느 쪽도 데드락·논리적 순서 버그는 막지 못한다(원고 rust 언어-특성 §9).
- 탐지기 비용: ASan 약 2배(Clang 문서), Go race detector 메모리 5~10배·실행 2~20배(Go 문서). 둘 다 실행된 경로만 본다.

### 6. 원고 비교표 교정

- Rust 경계 위반: 일반적으로 **런타임 panic**이다. The Rust Book 3.2는 사용자 입력 인덱스가 범위를 넘으면 `index out of bounds: the len is 5 but the index is 10`으로 panic하는 예를 보이고, "컴파일러가 사용자가 넣을 값을 알 수 없으므로 이 검사는 런타임에 일어나야 한다"고 적는다. 컴파일에서 막히는 것은 소유권·차용·수명(시간 축)이다.
- Go 데이터 레이스: "값만 어긋남"이 아니다. Go 메모리 모델은 기계어 한 워드보다 큰 값(인터페이스·맵·슬라이스·문자열)의 경쟁이 단일 쓰기에 대응하지 않는 값을 낼 수 있고, (포인터, 길이)·(포인터, 타입) 쌍의 일관성이 깨져 "임의의 메모리 손상"으로 이어질 수 있다고 적는다(<https://go.dev/ref/mem>).
- JVM 쪽 "정의되나 값이 어긋남"은 대체로 맞다. JLS 17장은 잘못 동기화된 프로그램도 허용되는 결과를 제한한다([language 13](../13-language-memory-model/2-summary.md)).

### 7. 기동 시간 (실험 2)

- 관찰(7회 × 2라운드를 두 번, `--cpus=2`, 이미지별 `true` 기준선 포함, 이 호스트·부하 한정): C 3~4ms, Go 4~6ms, Python 35~55ms, node 50~91ms(첫 회 190ms), Java 21 59~105ms(temurin 이미지 기준선 8~15ms 포함), `-Xshare:off`면 123~198ms.
- `-Xshare:off`(클래스 데이터 공유 끔)가 2배 가까이 느렸다 — CDS가 덜어 주는 클래스 로딩 비용이 이 환경 기동에서 작지 않다는 해석과 맞다(비율 자체는 재지 않았다).
- 결정적인 층: 호출마다 새로 뜨는 CLI, 스케일 0에서 시작하는 서버리스 함수, 짧은 배치 단계.
- 무의미한 층: 한 번 떠서 몇 주를 도는 코어 API 서버 — 기동은 상각되고, 비용은 DB 왕복·락 대기가 지배한다.

### 8. 다른 주문이 조회됨

- 원인: 64비트 주문 ID가 JSON 숫자로 내려가 JS `Number`(배정밀도)로 파싱됐다. 2^53 − 1(`9007199254740991`)을 넘는 정수는 정확히 담긴다는 보장이 없어 끝자리가 바뀐다. 실험 1에서 `MAX_SAFE_INTEGER + 2`는 `9007199254740992`로 나왔다(정확한 값은 …993).
- 대처: 큰 ID는 JSON에서 **문자열**로 주고받는다. 계산이 필요하면 `BigInt`. 받는 쪽에서 `Number.isSafeInteger`로 검사한다.

### 9. 원장 서비스의 언어 선택 절차

1. 최악 실패를 적는다 — 원장은 "조용한 오답"(이중 출금·잔액 오류).
2. 후보마다 실패 표(넘침·경계·파싱·에러 무시·비동기·부동소수)를 **실행으로** 채운다.
3. 층 조건: 오래 사는 서버라 기동은 상각된다. 상주 메모리·운영 관측 도구를 본다.
4. 생태계·팀: 결제·정산 라이브러리, 운영 경험, 채용, 5년 뒤 유지보수.
5. 고른 언어의 조용한 경로를 관례·린터·테스트로 막는다.

- Java라면 막을 조용한 경로와 코드
  - 정수 감김: `total = Math.addExact(total, amount);`(`long total`) 금액 계산은 `BigDecimal` + 명시적 반올림.
  - 삼킨 예외·비동기 미처리: 빈 `catch` 금지 규칙, `CompletableFuture` 사슬 끝에 `whenComplete`로 기록([language 16](../16-concurrency-design-patterns/2-summary.md)).
  - (더해서) 부동소수 금액 금지: `double` 대신 `BigDecimal`이나 최소 단위 정수.
