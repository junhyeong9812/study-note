# cs/issue/cross-cutting/reliability/non-transactional-multi-step — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **half-state와 순서.** 트랜잭션이 없으면 중간에 멈춘 지점의 상태가 그대로 남는다 — 누구도 롤백해 주지 않는다. 그래서 "어느 단계가 끝난 상태에서 멈출 수 있나"를 순서가 결정한다.\
   되돌릴 수 없는 단계가 앞에 있으면 뒤의 실패가 **양쪽을 다 잃는** 상태를 만들고, 뒤에 있으면 실패해도 **원래 상태가 무손상**이다.
   > **half-state** — 다단계 변경이 중간에 멈춰 어느 쪽 불변식도 성립하지 않는 상태.

2. **make-before-break.** `close(old) → start(new)`에서 start가 실패하면 살아 있던 세션을 이미 닫았으므로 **둘 다 잃는다**.\
   순서를 "요약 성공 게이트 → start(new) → 메타 기록(복구 가능한 단계) → 화면 전환 → 시드 주입 → close(old) 마지막"으로 바꾸면, 어디서 실패해도 기존 세션은 무손상이다.\
   남는 문제는 중간에 만든 새 세션이다 — 메타 기록 실패 시 새 프로세스가 어디에도 안 붙은 **고아**로 남았다. 교정: 새 ID를 try 밖에 선언하고 catch에서 명시적으로 닫는다.
   > **make-before-break** — 새 연결을 먼저 만들고 확인한 뒤 옛 연결을 끊는 순서.

3. **실패 가능한 쪽 먼저, 그 결과로 게이트.** 저장: 비밀 저장이 실패했는데도 "비밀 저장됨" 플래그로 연결을 만들어, 재시작 후 재접속이 실패했다 → 비밀 저장이 성공했을 때만(또는 비밀이 없을 때만) 메타데이터를 저장하고, 실패면 세션 전용으로 안내.\
   삭제: 메타데이터를 먼저 지우고 비밀 삭제 실패를 무시하자 UI에서 연결이 사라져 **재시도할 수도 없고**, 비밀은 저장소에 **고아**로 남았다 → 비밀 삭제 먼저, 실패하면 메타데이터 보존 + 알림. "항목 없음" 삭제는 성공으로 친다. ID는 UUID로 재사용하지 않아 고아와 새 항목이 충돌하지 않게 한다.

4. **실패 분기의 파괴.** 이전 버전을 이력 폴더로 옮기는데 이름이 충돌하면 이동을 건너뛰고, 그 뒤 원본 디렉토리를 통째 삭제했다 — 이동이 성공했다는 가정 위의 삭제라 **이전 버전이 소실**됐다. 교정: 목적지 이름을 접미사로 유일화, "빈 디렉토리만" 삭제, 이월 잔여가 있으면 통째 보존.\
   판별하며 즉시 삭제: 여러 파일을 스캔하며 바로 지우다 늦게 읽기 실패가 나면 **일부만 삭제**된 상태가 남는다. 읽기 실패 파일을 건너뛰고 새로 쓰면 재아카이브마다 **중복**이 쌓인다. 교정: 전수 판별을 끝낸 뒤 일괄 삭제(2단계), 읽기 실패는 전파해 드러낸다. 파생 인덱스는 append가 아니라 디스크 전체 스캔으로 재생성한다.

5. **잔해가 가드를 영구 오탐으로.** 등록 = 폴더 생성 → 파일 3개 → 상태 보드 5단계인데, 파일 2개만 try 안에 있었다. 중간 실패 시 폴더가 남고, 다음 재시도는 "이미 존재"(409)로 **영원히** 막힌다.\
   교정: 전 단계를 try로 감싸 실패 시 **이번 호출이 만든 폴더만** 삭제하고 예외를 다시 던진다 — "재시도 가능한 상태"가 불변식이다. 임시 폴더를 완성한 뒤 rename하는 방식은 보드가 별도 파일이라 완전한 원자성이 안 돼 선택하지 않았다(보드 행만 남는 경우는 다음 등록이 갱신해 무해). 테스트는 보드 자리에 같은 이름 폴더를 놓아 실제 파일시스템 실패를 주입했다.

6. **되돌릴 수 없는 내부 변경을 먼저.** 인증 코드 재발송에서 발송이 실패해도 기존 코드가 무효화되고 요청 한도가 소비됐다 — 사용자는 **손해만** 본다. 교정: 발송 성공 뒤에 발급·활성화.\
   참조 선확정: 세션 시작 시 마커(세션 ID)를 먼저 영속화하고 실제 프로세스 생성은 나중에 했는데, 최초 생성이 실패해도 마커가 남아 이후 시작은 **존재하지 않는 세션을 재개**하려다 반복 실패했다. 처방은 "생성 성공 시 마커 확정"이며, 실패가 드물어 알려진 한계로 문서화했다(복구 = 마커 줄 삭제 후 재시작).

7. **이관의 커밋 순서.** 송신 쪽이 "이동을 위한 제거"와 "닫기"를 구분하지 않아 제거 순간 백엔드 세션이 죽었고, 수신 쪽이 추가 성공 **전에** 처리 완료로 표시해 실패 시 패널이 유실됐다. 필요한 것: 이동 중 표시(detach ≠ close), 진행 중 집합으로 **재진입 차단**, 수신 측 `ok` ack를 받은 **뒤에만** 송신 측 정리(거부·타임아웃이면 원본에 재삽입), 양쪽에서 전제(프로젝트) **재검증**, 진행 중이면 빈 창 자동 닫기 보류. ack·타임아웃 정착 경로는 finally로 잠금 해제를 보장한다.\
   역순 보상: 여러 파일을 전부-아니면-전무로 만들 때 중간 실패면 만든 것을 역순으로 지운다. 그런데 "모든 상위 디렉토리 생성" 호출은 내가 만든 디렉토리와 원래 있던 디렉토리를 구분해 주지 않는다. 교정: 바깥 → 안으로 **한 단계씩 생성**하며 `성공 = 내 것 / AlreadyExists = 남의 것`으로 기록한다. 사전 스냅샷("원래 뭐가 있었나")은 스냅샷과 생성 사이에 다른 프로세스가 끼어드는 경쟁 창이 있어 부족하다.

## 문제 구조 (추상화 코드)

### 변형 A — 파괴를 새것 확보보다 먼저 (+ 중간 자원 고아)
① 문제 코드
```ts
await invoke("close", { id: oldId });
const started = await invoke("start", {...});         // 실패 → old 도 new 도 없음
await invoke("setMeta", { id: started.id });          // 실패 → new 가 고아
```
② 고친 코드
```ts
let newId: number | null = null;
try {
  const started = await invoke("start", {...}); newId = started.id;
  await invoke("setMeta", { id: started.id, prev: oldId });   // seed 전, 복구 가능
  remount(); await seed(started.id);
} catch (e) {
  if (newId != null) await invoke("close", { id: newId }).catch(() => {});   // 중간 자원 회수
  throw e;                                                    // 실패는 호출자에게 전파
}
await invoke("close", { id: oldId });   // 파괴는 마지막 — try 밖: 이 실패가 new 회수로 번지지 않게
```
무엇이 깨졌나: 되돌릴 수 없는 단계를 앞에 두고, 실패 경로에서 만든 것을 회수하지 않았다.

### 변형 B — 두 저장소: 실패 가능한 쪽을 나중에·무시
① 문제 코드
```ts
const storeOk = await secrets.set(id, secret);
upsertMeta({ id, hasStoredSecret: true });      // 비밀 저장 실패여도 "저장됨"
function remove(id) { deleteMeta(id); secrets.delete(id).catch(() => {}); }   // 고아 비밀
```
② 고친 코드
```ts
if (!secret || storeOk) upsertMeta({ id, hasStoredSecret: !!secret });
else notify("비밀 저장 실패 — 세션 전용으로 접속");
async function remove(id): Promise<boolean> {
  const r = await secrets.delete(id);            // 실패 가능한 쪽 먼저 (NoEntry = 성공)
  if (!r.ok) { notify("삭제 실패"); return false; }   // 메타 보존 → 재시도 가능
  deleteMeta(id); return true;
}
```
무엇이 깨졌나: 한쪽 실패를 확인하지 않고 다른 쪽을 진행해 불일치를 영구화했다.

### 변형 C — 실패 분기에서 삭제 · 판별과 삭제를 섞음
① 문제 코드
```rust
if rename(prev, &history.join(name)).is_err() { /* 충돌: 건너뜀 */ }
fs::remove_dir_all(prev)?;                     // 이동 안 됐는데 삭제 → 이전 버전 소실

for f in dir { if is_old(&read(f)?) { remove(f)?; } }   // 늦은 읽기 실패 → 일부만 삭제
```
② 고친 코드
```rust
let carry_leftover = moved.join("history").is_dir();
match history_name {
    Some(n) if !carry_leftover => rename(moved, unique(history.join(n)))?,  // 유일 이름으로 보존
    None    if !carry_leftover => remove_if_unchanged(moved)?,              // 미변경만 제거
    _ => {}                                                                 // 잔여 있으면 통째 보존
}

let olds: Vec<_> = dir.map(|f| Ok((f, is_old(&read(f)?)))).collect::<Result<_>>()?;  // 1단계: 전수 판별
for (f, old) in olds { if old { remove(f)?; } }                                     // 2단계: 일괄 삭제
```
무엇이 깨졌나: 앞 단계의 성공을 가정한 파괴가 실패 분기에서도 실행됐다.

### 변형 D — 부수효과 I/O를 상태 전이의 선행 조건으로
① 문제 코드
```ts
function setSplit(v) {
  persist(v);          // 저장소 용량·프라이빗 모드에서 throw → 아래 전부 스킵
  set({ split: v }); reconcile(); broadcast();
}
```
② 고친 코드 (처방)
```ts
function setSplit(v) {
  try { persist(v); } catch (e) { reportPersistFailure(e); }   // 전이는 항상 완주
  set({ split: v }); reconcile(); broadcast();
}
```
무엇이 깨졌나: I/O 예외가 전이 전체를 중단시켜 디스크(닫힘)와 메모리(열림)가 발산했다(처방만 기록, 해결 미기록).\
같은 구조: 공유 저장소를 여러 창이 쓰는데 동기 채널이 없어, 한 창의 초기화가 다른 창의 상태를 저장소에서 조용히 덮음(구조적 한계로 별도 작업).

### 변형 E — 부분 생성 잔해가 존재 검사 가드를 영구 차단
① 문제 코드
```python
if target.exists(): raise Conflict(409)
target.mkdir()
write(target / "a.md", ...)
try: write(target / "b.md", ...); write(target / "c.md", ...)
except: ...
update_board(...)                     # 실패 → 폴더 잔존 → 다음 재시도 영원히 409
```
② 고친 코드
```python
try:
    target.mkdir()                              # exist_ok=False: 검사와 생성을 한 번에 (존재 검사→mkdir 사이 경쟁 제거)
except FileExistsError:
    raise Conflict(409)
try:
    write(target / "a.md", ...); write(target / "b.md", ...)
    write(target / "c.md", ...); update_board(...)
except Exception:
    shutil.rmtree(target, ignore_errors=True)   # mkdir 성공 뒤이므로 이번 호출이 만든 폴더만 보상 삭제
    raise
```
무엇이 깨졌나: 잔해를 남겨 재시도 가능 상태를 깨뜨렸다.

### 변형 F — 외부 부작용 전에 되돌릴 수 없는 내부 변경 · 참조 선확정
① 문제 코드
```kotlin
codes.invalidate(user); rateLimit.consume(user)
mailer.send(user, newCode)            // 실패 → 사용자는 코드도 한도도 잃음
```
```python
marker.write(session_id)              # 참조 먼저 확정
spawn(["agent", "--session-id", session_id])   # 실패 → 댕글링 마커 → 이후 재개 반복 실패
```
② 고친 코드
```kotlin
rateLimit.check(user)                 // 한도 '검사'는 발송 전 (소비만 뒤로 미룬다)
mailer.send(user, newCode)            // 성공 후에만
codes.activate(user, newCode); rateLimit.consume(user)
```
```python
proc = spawn(["agent", "--session-id", session_id])
marker.write(session_id)              # 처방: 생성 성공 시 확정 (당시는 알려진 한계로 문서화)
```
무엇이 깨졌나: 실패할 수 있는 외부 단계보다 되돌릴 수 없는 내부 단계를 먼저 했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(변형 A~F)은 "단계 순서로 실패를 격리하고, 잔해는 보상한다"이다. 같은 원리에 다른 방안이 쓰인 사례:

### 방안 1 — 소유권 이관: 수신 측 ACK 후 송신 측 정리
```ts
async function handOff(id) {
  if (inFlight.has(id)) return;                 // 재진입 차단 (더블클릭 = 이중 시작)
  inFlight.add(id);
  const ack = waitFor("transfer-result", id);
  transferring.add(id); api.getPanel(id)?.close(); transferring.delete(id);   // detach ≠ close
  if (api.getPanel(id)) { inFlight.delete(id); return; }                      // 실제 제거 확인
  emit("transfer", { id, project });
  try {
    const r = await ack;
    if (!r.ok) reinsert(id);                    // 거부 → 원본에 재삽입(손실 0)
  } catch { reinsert(id); }                     // 타임아웃 → 재삽입
  finally { inFlight.delete(id); }              // 잠금 해제 보장
}
// 수신 측: project 검증 → addPanel 성공 → transfer-result{ ok: true }
// 빈 창 자동 닫기: everHadPanel && empty && !hasInFlight() 일 때만, debounce 후
```

### 방안 2 — 역순 보상 롤백 + 단계별 "내가 만든 것" 판별
```rust
fn ensure_dirs(path) -> Result<Vec<PathBuf>> {
    let mut mine = vec![];
    for p in ancestors_outer_to_inner(path) {
        match fs::create_dir(&p) {
            Ok(())                                  => mine.push(p),   // 내 것
            Err(e) if e.kind() == AlreadyExists     => {}              // 남의 것 — 롤백 대상 아님
            Err(e)                                  => return Err(e),
        }
    }
    Ok(mine)
}
// create_files: 실패 시 created 를 역순 삭제(best-effort), 정리 실패는 "일부 항목 정리 실패: …" 로 가시화
// 다중 생성 패턴의 조합 폭발은 사전 개수 상한으로 즉시 거부
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 순서 격리 + 보상 | 단계를 재배열할 수 있다 | 순서 설계·catch 회수 | 보상 자체가 실패하면 잔해(가시화 필요) | 단일 호출 안의 다단계 변경 |
| 1. ACK 후 정리 | 두 참여자가 메시지로 확인을 주고받는다 | ack 프로토콜·타임아웃·재진입 잠금 | 이관 중 전제가 바뀌면 재삽입이 오래된 대상으로 갈 수 있음(기록된 잔여) | 창·프로세스 간 소유권 이전 |
| 2. 역순 보상 + 소유 판별 | 각 단계가 결과로 소유를 알려준다 | 단계 분해(한 레벨씩 생성) | 경쟁 창은 단일 스레드 테스트로 재현 불가(구조 제거로 대응) | 전부-아니면-전무 파일 생성 |

**결론**: 먼저 순서를 바꿀 수 있는지 본다 — 파괴를 마지막에 두는 것만으로 대부분의 half-state가 사라진다(기본).\
참여자가 둘이면 순서만으로는 부족하다 — **수신 측 확정(ACK)**이 송신 측 정리의 조건이 된다(1).\
되돌려야 하는 단계가 많으면 보상 롤백을 쓰되, **"내가 만든 것"을 연산 결과로 기록**해야 남의 것을 지우지 않는다(2).
