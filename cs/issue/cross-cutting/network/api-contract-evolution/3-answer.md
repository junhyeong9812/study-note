# cs/issue/network/api-contract-evolution — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `contract-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **광고 ≠ 구현.**\
   capability 목록은 "이런 걸 할 수 있다"는 선언일 뿐, 그 메서드가 실제로 구현돼 있다는 보장이 아니다.\
   어댑터가 프로토콜 스키마를 채우느라 필드는 광고하면서 핸들러는 비워 둘 수 있고, 실제 로그인은 프로토콜 밖(out-of-band — 별도 로그인 명령이 남긴 자격 파일 재사용)에서 일어나고 있었다.\
   그래서 교정은 `authMethods`를 차단 조건으로 쓰지 않고 `authenticate` 호출을 없앤 뒤, 실제로 돌아오는 `requires_auth` 에러만 표면화해 "이 명령으로 로그인하라"고 안내하는 것이었다.\
   상대 구현이 무엇을 하는지는 **소스를 읽고 스모크로 호출해 보는 것**으로만 확정한다 — 계획 단계에서 "로그인 재사용은 계약이 아니라 어댑터 가정"이라고 짚었고, 실측으로 확정했다.
   > **capability 광고** — 프로토콜 협상 때 한쪽이 "지원한다"고 알리는 기능·메서드 목록.

2. **버전 에코의 위험.**\
   프로토콜 버전 문자열은 구체 능력의 묶음을 함의한다 — 예컨대 어떤 버전은 batch(배열) 요청 수신을 요구한다.\
   서버가 요청 버전을 무조건 에코하면, 자기가 만족하지 못하는 능력을 가진 척하게 된다 — 실제로 봉투 검증이 배열을 거부하는데도 batch를 요구하는 버전을 수락한 불일치가 재점검에서 다시 잡혔다.\
   교정은 **지원 화이트리스트**(batch를 요구하는 버전은 제외)이고, 목록에 없는 요청엔 서버가 지원하는 버전으로 답한다 — 클라이언트는 그 버전을 자기도 지원하면 그 버전으로 진행하고, 지원하지 않으면 초기화 단계에서 "버전 불일치"로 **명시적으로 실패**(연결 종료)한다. 어느 쪽이든 "수락한 척"의 무음 오동작은 사라진다.\
   봉투도 파싱 전에 구조를 검증한다: 객체가 아니거나 `jsonrpc` 값이 틀리면 -32600, id 없는 알림(notification)엔 응답하지 않는다, 도구 실패는 JSON-RPC error가 아니라 결과 안의 `isError:true`.
   > **JSON-RPC 봉투** — `{jsonrpc, id, method, params}` 형태의 요청 틀. id가 없으면 응답을 기대하지 않는 알림이다.

3. **과대 진술된 문서의 결과.**\
   소비자는 "bounded"를 믿고 상한 처리를 빼고, "resume는 이어간다"를 믿고 실패 경로를 설계하지 않는다 — 결과는 에러가 아니라 **무음 유실**(조용히 새 세션, 무한정 커지는 응답)이다.\
   계약 스윕에서 과대 진술이 다수였고 과소 진술은 0건이었다 — 문서는 구현보다 앞서 "하고 싶은 것"을 쓰는 쪽으로 치우친다.\
   교정 기준: 각 단언을 코드로 역검증하고, 불성립이면 **조건부로 약화 + 잔여(안 되는 부분) 명시**. 새 문구는 **전부 테스트가 뒷받침하는 것만** 쓴다.

4. **응답 형태 변경의 배포 순서.**\
   배열 → 래퍼는 비호환 변경이라, 두 배포 사이의 창에서 한쪽은 모르는 형태를 받는다.\
   소비자(프론트)가 먼저 나가면: 새 소비자가 **구 배열 응답을 받으면 크래시 없이 폴백 화면으로 강하**하도록 짰기 때문에 안전하다.\
   제공자(서버)가 먼저 나가면: 구 소비자는 래퍼를 모르므로 깨진다 → 위험. 그래서 결론은 **동시 배포 권장**(최소한 폴백을 가진 쪽 선배포).\
   새 필드 추가는 보통 하위호환 확장이다 — 모르는 필드를 무시하는 관용적 파서라면 구 소비자의 파싱이 깨지지 않는다(단 모르는 필드에 실패하도록 설정된 엄격한 역직렬화기·스키마 검증을 쓰는 소비자는 여기서도 깨지므로, 소비자의 파서 정책을 확인해야 한다. 또 의미는 어긋날 수 있다 — 이 사례에서 구 화면은 새 필드를 몰라 기존 필드의 특수값을 평범한 값으로 표시하게 되므로, 기록은 여기서도 동시 배포를 권장했다).
   > **하위호환 확장(additive change)** — 기존 필드를 바꾸지 않고 필드만 더하는 변경. 구 소비자가 그대로 동작한다.

5. **문서-코드 드리프트를 기계로 잡기.**\
   문서 코드 블록이 구현을 주석 스텁으로 대체하면, 따라 친 코드는 타입이 맞아 **컴파일은 되지만 동작이 비어** 있다(여기선 영속화 로드/저장) — 타이핑 실수가 아니라 문서의 누락이다.\
   교정은 문서를 실행물로 다루는 것: 코드 블록마다 정본 앵커(`// <경로> @ <커밋>`)를 달아 정본과 대조하고, **src를 전부 지운 뒤 문서에서 추출한 코드만으로 빌드·테스트해 green**이 나와야 통과로 본다.\
   문서만으로 빌드하면 "문서에 정의 없이 쓰인 헬퍼" 같은 누락도 컴파일 에러로 드러난다(일반론 — 이 사례의 헬퍼 누락은 별도 작업에서 먼저 보완됐다).

6. **외부 입력 필드 드리프트.**\
   `jq -r '.prompt'`처럼 한 필드명에 의존하면, 필드가 사라져도 에러가 나지 않고(jq는 없는 키를 `null`로 평가하고 종료 코드 0) **조용히 무의미한 값**을 읽는다 — `-r` 출력이면 셸 변수에는 리터럴 문자열 `"null"`이 들어가, 이후 로직은 빈 값 검사조차 통과한 채 정상 진행할 수 있다.\
   소비자 방어: 폴백 후보를 나열(`.prompt // .user_message // empty`)하고, 그 필드를 **감시 항목**으로 등록해 런타임 버전이 바뀔 때마다 실측한다. 결정 출력 형식도 문서의 현행 형식과 대조해 둔다.\
   한계: 폴백은 이미 아는 이름만 막는다 — 전혀 새로운 이름으로 바뀌면(`// empty` 덕에) 빈 값이 되므로, 빈 값일 때 경고하는 관측이 함께 있어야 한다.

7. **착수 전 확인으로 바꾸기.**\
   같은 원리다 — 계획이 "외부 도구가 이 기능을 제공한다"는 **주장**을 전제로 했고, 설치본이라는 **사실**을 확인하지 않았다(그 기능은 제공자가 내부 API로만 쓰고 CLI로 노출하지 않은 것이었다).\
   절차로 바꾸면: 가장 위험한 외부 가정은 **착수 직후, 그 위에 쌓기 전에** 실제 설치본(`--help`, 최신 릴리스, 소스)으로 스모크한다.\
   이 사건은 사후에 5개 옵션을 비교해, 이미 받아 둔 원본 덤프를 재활용하는 자체 스트리밍 파서로 우회했다(대가: 템플릿 전개가 안 돼 일부 항목 누락).

## 문제 구조 (추상화 코드)

### 변형 A — 광고된 capability를 호출 조건으로 사용
① 문제 코드
```kotlin
val init = client.initialize()
if (init.authMethods.isNotEmpty()) {
    client.authenticate(init.authMethods.first())   // 광고만 믿음 → "Method not implemented"
}
client.newSession()
```
② 고친 코드
```kotlin
val init = client.initialize()                       // authMethods는 차단 조건으로 쓰지 않는다
try {
    client.newSession()
} catch (e: RpcError) {
    if (e.code == AUTH_REQUIRED) return NeedsAuth(command = LOGIN_COMMAND)   // 실제 에러만 표면화
    throw e
}
```
무엇이 깨졌나: 프로토콜 필드의 존재를 메서드 구현의 증거로 읽었다.

### 변형 B — 버전 협상 에코 + 봉투 미검증
① 문제 코드
```rust
fn initialize(req: InitRequest) -> InitResult {
    InitResult { protocol_version: req.protocol_version, /* ... */ }   // 무엇이든 수락한 척
}
fn handle(raw: &str) -> Option<Response> {
    let msg: Request = serde_json::from_str(raw).ok()?;               // 구조 검증 없이 파싱
    Some(dispatch(msg))                                                 // 알림에도 응답
}
```
② 고친 코드
```rust
const SUPPORTED: [&str; 2] = [VERSION_A, VERSION_C];   // batch를 요구하는 VERSION_B 제외
fn initialize(req: InitRequest) -> InitResult {
    let v = if SUPPORTED.contains(&req.protocol_version.as_str()) { req.protocol_version } else { VERSION_A.into() };
    InitResult { protocol_version: v, /* ... */ }       // 클라이언트가 불일치를 보고 명시 실패
}
fn handle(value: Value) -> Option<Response> {
    if !value.is_object() || value["jsonrpc"] != "2.0" { return Some(error(-32600)); }
    if value.get("id").is_none() { dispatch_notification(value); return None; }   // 알림엔 무응답
    Some(dispatch(value))                                // 도구 실패는 result.isError = true
}
```
무엇이 깨졌나: 버전이 함의하는 능력(batch)을 구현하지 않은 채 그 버전을 선언했다.

### 변형 C — 문서 주석이 구현보다 큰 보장을 광고
① 문제 코드
```rust
/// 모든 응답은 bounded다.
/// resume: 이전 세션을 이어간다.
pub fn spawn(req: SpawnRequest) -> Session {
    if let Some(id) = req.resume {
        if let Some(t) = find_transcript(id) { return resume(t); }
    }
    new_session()                                        // 못 찾으면 보고 없이 새 세션
}
```
② 고친 코드
```rust
/// 응답 상한: <목록의 명령>만 bounded. 그 외 명령은 상한 없음.
/// resume: 전사를 찾으면 이어가고, 못 찾으면 새 세션으로 시작한다(호출자에게 구분 신호 없음).
pub fn spawn(req: SpawnRequest) -> Session { /* 동작 변경 없음 — 문구를 구현에 맞춤 */ }
// 새 문구의 각 문장은 테스트 1개 이상이 받친다
```
무엇이 깨졌나: 문서가 구현과 독립적으로 쓰여, 소비자가 존재하지 않는 보장을 근거로 설계할 수 있었다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리(광고·문서·전제 ≠ 실제 구현)에 대해, 드리프트가 생기는 자리마다 다른 방안이 쓰였다.

### 방안 1 — 문서 속 코드를 추출·빌드해 드리프트 검증
```kotlin
// 문제: 문서 코드 블록
private fun load() { /* binary read */ }             // 컴파일 OK, 영속화 비어 있음
// 고친: 정본 앵커 + 실제 본문
// <경로> @ <커밋>
private fun load() {
    DataInputStream(open()).use { input -> repeat(input.readInt()) { /* ... */ } }
}
```
```sh
rm -rf src/                          # 코드 삭제
extract-blocks docs/impl/ --out src/ # 문서에서만 복원
build && test                        # green이어야 문서가 정본과 일치
```

### 방안 2 — 비호환 응답 변경은 배포 순서 계획 + 소비자 폴백
```ts
// 제공자: GET /items   [..]  →  { baseYear, anchorMonth, rows: [..] }
// 소비자(선배포 가능하게)
const body = await res.json();
if (!body || !Array.isArray(body.rows)) return renderFallback();   // 구 배열 응답 → 크래시 없이 폴백
render(body.rows);
```

### 방안 3 — 외부 도구 기능은 착수 전 실제 설치본으로 확인
```sh
# 문제: 계획이 --edition 플래그를 전제 → 스크립트 작성·배포 후 발견
# 고친: 착수 직후 스모크
tool --version && tool --help | grep -q -- '--edition' || echo "BLOCKER: 설치본에 기능 없음"
```
```python
# 이 사건의 우회: 이미 받은 덤프를 스트리밍 파싱 (메모리 거의 일정)
for _ev, elem in ET.iterparse(bz2.open(path, "rb"), events=("end",)):
    if elem.tag == f"{ns}page":
        yield parse(elem)
        elem.clear()   # 주의: clear()만으론 루트가 빈 자식 참조를 계속 쥔다 —
                       # 수백만 건이면 루트 자식도 정리해야(예: start 이벤트로 root를 잡아 root.clear()) 메모리가 평탄하다
```

### 방안 4 — 외부 런타임 입력 스키마 드리프트를 소비자 측에서 방어
```sh
prompt=$(jq -r '.prompt' <<<"$input")                             # 문제: 필드 바뀌면 조용히 문자열 "null"
prompt=$(jq -r '.prompt // .user_message // empty' <<<"$input")   # 고친: 폴백 후보 + 감시 항목 등록
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 문서 코드 추출·빌드 | 문서 코드가 정본을 완전히 담도록 쓸 수 있다 | 추출 도구·앵커 유지 | 앵커가 낡으면 대조가 거짓 green | 문서를 보고 코드를 재구성하는 학습·구현 문서 |
| 2. 배포 순서 + 폴백 | 소비자·제공자를 따로 배포한다 | 폴백 코드·배포 조율 | 폴백 없는 쪽이 먼저 나가면 깨짐 | 응답 형태를 바꾸는 비호환 변경 |
| 3. 설치본 사전 확인 | 외부 도구를 고칠 수 없다 | 착수 전 스모크 수 분 | 확인 안 하면 뒤늦은 블로커·재작업 | 계획이 외부 기능 하나에 걸려 있을 때 |
| 4. 소비자 폴백 필드 | 제공자 스키마를 통제할 수 없다 | 폴백 목록·감시 | 모르는 새 이름엔 여전히 빈 값 | 예고 없이 바뀌는 외부 런타임 입력 |

**결론**: 드리프트가 생기는 자리를 누가 통제하느냐로 고른다.\
양쪽을 다 통제하면(자기 문서·자기 API) 방안 1·2처럼 **검증을 파이프라인에 넣거나 배포 순서를 설계**한다.\
상대를 통제할 수 없으면(외부 도구·런타임) 방안 3·4처럼 **착수 전 실측 + 소비자 방어**가 남는 선택이다.
