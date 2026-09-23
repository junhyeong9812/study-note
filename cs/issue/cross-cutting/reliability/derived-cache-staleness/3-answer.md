# cs/issue/reliability/derived-cache-staleness — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **실패를 빈 목록으로 캐시.** 얻는 것: 실패해도 로딩 상태가 끝나 UI가 멈추지 않는다.\
잃는 것: 실패 결과가 성공 결과와 **같은 캐시에, 만료·무효화 없이** 들어가 일시적 실패(권한 순간 오류·마운트 지연)가 영구 "빈 폴더"로 굳는다 — 사용자는 오류가 아니라 정상적인 빈 결과를 본다.\
negative caching을 쓰려면 **짧은 TTL·명시 무효화·재시도 경로** 중 하나가 함께 있어야 하고, 가능하면 실패를 "빈 성공"이 아닌 오류 상태로 구분해 저장한다.\
원문은 정적 트리라는 전제로 이 트레이드오프를 의식적으로 수용하고 재시도·무효화는 구현하지 않았다. 같은 계열로, 상태 파일 손상과 최초 실행을 구분 없이 기본값으로 흡수하면 "손상 사실"이 조용히 사라진다.
   > **negative caching** — "없음/실패"라는 결과 자체를 캐시하는 것. 반복 실패 요청을 줄이지만 만료 없이 두면 장애를 영구화한다.

2. **갱신 건너뜀을 신선함으로 오인.** throttle 창의 갱신 함수는 **갱신 없이** 성공처럼(`nil`) 돌아온다. 호출부가 "에러 없음 = 방금 새로 받음"으로 믿으면 **이미 만료된 캐시 키**로 서명을 검증한다 — 폴링이 계속 throttle 창에 걸리면 무기한.\
TTL은 "언제 갱신을 시도할지"가 아니라 **"이보다 오래된 데이터는 쓰지 않는다"는 staleness 상한**이어야 한다 → 키를 돌려주기 직전 `now - fetchedAt < ttl`을 다시 확인하고, 아니면 Stale 오류.\
대가(명시): throttle 창에 새로 회전된 키 id가 오면 잠시 거절된다 — 가용성을 조금 내주고 만료 키 사용을 막는다. 빈 키 id는 갱신 시도 없이 바로 거절한다.
   > **staleness 상한** — 데이터 나이의 최댓값. 넘으면 사용을 거부한다.

3. **스냅샷은 한 주기 늦다.** 스냅샷은 폴링(수백 ms)마다 갱신되는 파생 사본이라, 요약을 만드는 순간 마지막 poll 이후의 기록(마지막 턴)이 아직 없을 수 있다.\
완결성이 필요한 순간에는 **정본(원본 로그 파일)을 새로 읽는다** — 새 리더를 만들어 오프셋 0부터 1회 읽으면 idle 세션 전체를 얻는다.\
정본에도 없는 정보(영속되지 않는 하위 스트림 변경)는 읽을 수 없으므로 한계로 기록한다.

4. **import 시점 연결과 실패 싱글톤.** 모듈 import는 한 번만 실행되고 재시도·deadline·종료 훅이 없다 — 그 시점에 연결이 실패해 싱글톤을 `None`으로 고정하면, 이후 서버가 살아나도 **다시 연결하는 코드 경로가 없어** 재시작만이 해법이 된다(실패 결과의 캐시).\
또한 `import app`만 해도 실 DB 연결·ping이 일어나 테스트가 외부 timeout에 묶이고, 종료 시에도 일부 클라이언트만 닫힌다.\
교정(계획): 연결·헬스체크를 애플리케이션 **lifespan startup**으로 옮기고(병렬 초기화 + 전체 deadline), shutdown에서 전부 close한다. 캐시 서버 클라이언트는 timeout 재시도·주기 헬스체크가 있는 풀이나 lazy 재연결로 바꾼다.
   > **lifespan** — 애플리케이션 시작·종료 시점에 자원을 만들고 정리하는 훅.

5. **Context는 쿠키의 사본이다.** Provider의 초기화 effect(의존성 `[]`)는 **마운트 시 한 번만** 쿠키를 읽는다. SPA 내부 라우팅은 Provider를 다시 마운트하지 않으므로, 로그인이 쿠키를 바꿔도 Context 사본은 옛 값 그대로다.\
외부 저장소는 변경을 사본에 알리지 않는다 → 쿠키를 바꾼 쪽이 **사본(Context)도 명시적으로 갱신**하고 이동한다(`login(); router.push('/')`).\
부수: Provider value를 인라인 객체로 넘기면 매 렌더 새 참조가 되어 모든 consumer가 리렌더된다 → 메모이즈.

6. **비동기 flush 로그로 "지금"을 판정.** 대화 로그 파일은 비동기로 디스크에 flush되므로, 훅이 실행되는 순간 **이번 턴의 사용자 메시지가 아직 파일에 없을 수 있다** — "푸시해줘"라고 했는데 이전 턴만 보고 차단하는 false-block이 실제로 재현됐다.\
이것은 read-your-writes 보장이 없는 읽기다 — 방금 일어난 사실을 같은 흐름의 다음 판정이 못 본다.\
교정: 프롬프트 제출 이벤트의 **페이로드(현재 턴 원문, 지연 없음)**를 세션 사이드카에 원자적으로 기록하고 판정은 사이드카를 우선 읽는다. 이후 턴 번호·시각 헤더로 턴 결속을 강화하고 로그 폴백을 제거했으며, 최종적으로는 자연어 승인 판정 자체를 플랫폼의 구조화된 승인 UI로 옮겼다.
   > **read-your-writes** — 자기가 방금 쓴 것을 곧바로 읽을 수 있다는 일관성 보장.

7. **네 대응의 위치.** 모두 "사본이 정본보다 늦거나 굳는다"를 다룬다 — 다른 것은 개입 지점이다.\
정본 직접 읽기 = **읽는 쪽**이 필요한 순간 사본을 건너뛴다.\
수명주기 관리 = **사본을 만드는 시점**을 제어 가능한 곳(lifespan)으로 옮겨 실패가 굳지 않게 한다.\
변경 시 명시 갱신 = **쓰는 쪽**이 정본과 사본을 함께 바꾼다.\
이벤트 페이로드 = 같은 사건의 **더 빠른 경로**를 진실 소스로 고른다.

## 문제 구조 (추상화 코드)

### 변형 A — 실패를 성공과 같은 캐시에 (negative caching, 무효화 없음)
① 문제 코드
```ts
try {
  const children = await readDir(path)
  set(s => ({ cache: { ...s.cache, [path]: children } }))
} catch (err) {
  console.error(err)
  set(s => ({ cache: { ...s.cache, [path]: [] } }))    // 일시 실패 → 영구 빈 목록 (무효화·재시도 없음)
}
```
② 필요한 것 (원문은 정적 트리 전제로 수용 — 미구현)
```ts
catch (err) {
  set(s => ({ cache: { ...s.cache, [path]: { error: err, at: Date.now() } } }))  // 실패는 실패로 구분
}
// 읽는 쪽: error 엔트리는 TTL 경과 또는 사용자 새로고침 시 재시도
```
무엇이 깨졌나: 실패 결과가 만료 없이 성공 결과와 같은 자리에 굳었다.\
같은 구조: 상태 파일 로드가 "손상"과 "최초 실행"을 구분 없이 기본값으로 흡수 → 손상 사실이 사라짐.

### 변형 B — 갱신 건너뜀을 신선함으로 오인
① 문제 코드
```go
func (ks *KeySet) Get(kid string) (*Key, error) {
    if ks.expired() {
        if err := ks.refresh(); err != nil { return nil, err }   // throttle 창: 갱신 없이 nil
    }
    return ks.keys[kid], nil                                      // 만료된 키 반환
}
```
② 고친 코드
```go
func (ks *KeySet) Get(kid string) (*Key, error) {
    if kid == "" { return nil, ErrNoKid }                         // 페치 없이 거절
    if ks.expired() { _ = ks.refresh() }
    if clock.Now().Sub(ks.fetchedAt) >= ks.ttl {                  // 반환 직전 나이 재확인
        return nil, ErrStale
    }
    return ks.keys[kid], nil
}
```
무엇이 깨졌나: "갱신 함수가 에러 없이 끝남"을 "데이터가 신선함"의 증거로 썼다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A·B)은 "캐시에 실패·나이를 드러내 굳지 않게 한다"이다. 같은 원리(사본은 늦고 굳는다)에 개입 지점이 달라 다른 방안이 쓰인 사례:

### 방안 1 — 완결성이 필요하면 정본 직접 읽기
```rust
// 문제: 주기 스냅샷(한 poll 뒤처짐)으로 요약 → 마지막 턴 누락
let text = render_for_summary(&stored_snapshot);
// 고친: 새 리더로 원본 로그를 오프셋 0부터 1회 읽음
let snap = LogTail::new(&log_path).poll()?;
let text = render_for_summary(&snap);
// 원본에도 영속되지 않는 하위 스트림 변경은 한계로 기록
```

### 방안 2 — 연결은 import가 아니라 lifespan이 소유
```python
# 문제
db = Database(url); db.ping()                 # 모듈 레벨 — import만 해도 연결·ping
try: cache = CacheClient(url)
except Exception: cache = None                # 첫 실패가 프로세스 수명 내내 고정
# 고친 (계획)
@asynccontextmanager
async def lifespan(app):
    app.state.db, app.state.cache = await asyncio.wait_for(
        asyncio.gather(open_db(), open_cache(retry_on_timeout=True, health_check_interval=HEALTH_INTERVAL)),
        timeout=STARTUP_DEADLINE)
    yield
    await close_all(app.state)                # 모든 클라이언트 종료
```

### 방안 3 — 외부 저장소의 사본은 바꾼 쪽이 명시 갱신
```tsx
// 문제: Provider가 마운트 때 쿠키를 1회 읽음 → 로그인 후 라우팅해도 사본은 옛 값
useEffect(() => { setLoggedIn(hasSessionCookie()) }, [])
await loginRequest(); router.push("/")
// 고친
await loginRequest(); authLogin() /* setLoggedIn(true) */; router.push("/")
const value = useMemo(() => ({ loggedIn, authLogin, authLogout }), [loggedIn])   // 인라인 객체 리렌더 방지
```

### 방안 4 — 비동기 flush 로그 대신 이벤트 페이로드를 진실 소스로
```bash
# 문제: 판정 훅이 비동기 flush되는 대화 로그에서 마지막 사용자 메시지를 grep
last_msg=$(jq -r 'select(.type=="user")|.message.content' "$log" | tail -1)   # 이번 턴 아직 없음
# 고친: 프롬프트 제출 이벤트 훅이 페이로드를 사이드카에 원자 기록
#   (capture) printf '#turn=%s\n#ts=%s\n%s' "$n" "$(date +%s)" "$prompt" > "$tmp" && mv "$tmp" "$sidecar"
if [ -s "$sidecar" ]; then last_msg=$(cat "$sidecar"); fi                    # 판정은 사이드카 우선
# 최종: 자연어 승인 판정 자체를 플랫폼의 구조화된 승인(ask) UI로 이관
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 실패·나이를 캐시에 드러냄 | 캐시를 유지해야 한다(비용·폭주 방지) | 상태 구분·나이 검사 | 거절 증가(가용성 대가) | 키 세트·목록 캐시 |
| 1. 정본 직접 읽기 | 정본을 다시 읽는 비용이 감당 가능 | 1회 전체 읽기 | 정본에 없는 정보는 여전히 없음 | 요약·내보내기 등 완결성 순간 |
| 2. lifespan 소유 | 외부 연결이 일시 장애를 겪는다 | 기동 구조 변경 | deadline 초과 시 기동 실패(의도된 소음) | 서버 앱의 DB·캐시 클라이언트 |
| 3. 명시 갱신 | 사본을 바꾸는 쓰기 경로를 안다 | 쓰기 경로마다 호출 | 새 쓰기 경로에서 갱신 누락 | 클라이언트 전역 상태 |
| 4. 이벤트 페이로드 | 같은 사건의 동기 경로가 있다 | 사이드카·원자 쓰기 | 페이로드 경로가 없는 사건(끼어든 메시지)은 못 봄 | 훅·판정 로직 |

**결론**: 사본을 없앨 수 없으면 **사본의 나이와 실패를 드러내** 굳지 않게 한다(기본·2).\
완결성·최신성이 판정의 전제면 사본을 건너뛰고 **정본이나 동기 페이로드**를 읽는다(1·4).\
사본을 바꾸는 쓰기 경로가 한정돼 있으면 **쓰는 쪽이 함께 갱신**하는 것이 가장 싸다(3) — 단 쓰기 경로가 늘 때마다 그 규칙이 따라가야 한다.
