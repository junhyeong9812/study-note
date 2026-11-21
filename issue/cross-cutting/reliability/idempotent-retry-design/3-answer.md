# issue/cross-cutting/reliability/idempotent-retry-design — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **멱등 = 여러 번 해도 한 번 한 것과 같은 연산.** 세션 이력을 이벤트마다 append했더니, 재개 시 파일을 처음부터 다시 읽으면서 과거 항목이 **다시 append**되어 중복이 쌓였다. 세션 카운트도 고유 ID가 아니라 줄 수를 세서 리비전·재독마다 부풀었다.\
   멱등하게 만드는 두 방법: ① 결과 전체를 **덮어쓰는 스냅샷**(원자적 temp → rename) ② `(session, id)` 같은 **고유 키로 병합**. 이렇게 하면 처음부터 다시 읽는 것이 별도 replay 로직 없이 결정론적 재구성이 된다.
   > **멱등(idempotent)** — `f(f(x)) = f(x)`. 재시도·재독이 결과를 바꾸지 않는 성질.

2. **exactly-once의 경쟁 창.** 터미널에 텍스트를 주입하는 배달에서 ACK를 추론하고, 타임아웃이 진행 중인 write를 취소하지 못해 늦은 실쓰기 + 재시도 중복이 났다. 그래서 요청 ID dedupe 원장을 넣었더니 원장에 다시 blocker(claim 선기록 race·상한 축출 후 release 오삭제·재시도 effect 미재실행)가 나왔다 — 같은 곳을 두 번 넘게 고쳐도 또 깨지는 **churn**이다.\
   취소 불가 부작용은 "보냈나 안 보냈나"를 원장과 원자적으로 맞출 수 없으므로 claim·release·축출 사이마다 경쟁 창이 생긴다.\
   재설계: 주입은 "제출 없는 채우기"라 **중복이 파괴적이지 않다** → 원장·타임아웃·자동 재시도를 제거하고 at-least-once + 수동 [다시 적용]으로 바꾸자 다음 감사에서 blocker 0. "희귀 중복은 무해"라는 트레이드오프는 코드 주석·테스트로 명시했다.
   > **at-least-once** — 최소 한 번 전달(중복 가능). 소비 쪽이 멱등이면 효과는 한 번이 된다.

3. **최초 명령 재생 = 처음부터 다시.** 세션 객체가 생성 시 명령을 보관해 두고 재기동에 그대로 썼는데, 그 명령에 "이 ID로 **새로** 만들기" 플래그가 들어 있었다 — 이미 존재하는 ID로 다시 생성을 시도해 상태를 위반한다.\
   재시도 경로는 **현재 영속 상태**(마커 파일 등)에서 명령을 다시 도출해야 한다(여기선 "재개" 명령).\
   교정: 공유 세션 코드는 건드리지 않고, 죽은/미등록 세션으로의 재접속을 거절(4404)하게 해 클라이언트가 시작 API를 다시 부르도록 했다 — 시작 API가 마커 기반으로 재개 명령을 만든다.

4. **outbox는 at-least-once다.** 릴레이는 "외부 발송 성공"과 "완료 커밋" 사이에서 죽으면 다음에 다시 보낸다.\
   외부가 발급하는 접수 ID는 **호출 결과로만** 얻으므로 호출 전에 기록할 수 없다 — "접수 ID 선기록으로 중복 방지"는 성립하지 않는다.\
   올바른 장치: **요청 측 멱등 키를 외부와 공유**(외부 API가 멱등 키를 지원해 같은 키를 중복으로 인식할 때) 또는 **접수 결과 사후 대조**. 소비자 쪽에서는 `commandId` 같은 유일 키 불변식으로 재전달·DLQ 재투입의 이중 처리를 막는다.

5. **두 의도, 두 축.** 재개 의도를 본문에 넣으면 내용 digest가 바뀌어 충돌(Conflict)로 거절되고, 밖에 두면 "이미 처리한 요청"으로 멱등 보고만 된다 — 어느 쪽도 재실행이 안 돼 **조용히 멈춘다**.\
   교정: 충돌 판정 축 = 내용 digest, 재개 축 = attempt 번호로 분리하고, 완료된 것은 재개 금지, 오래된 attempt는 보고만 한다.\
   기존 레코드에는 attempt가 없어 기본값 0으로 읽히는데, 그러면 첫 실행의 attempt 1이 "재개"로 오인된다 — 스키마 확장 시 **구 레코드 정규화**가 필요하다.

6. **부분 커밋 + 재전달 = 이중 쓰기.** 서비스 함수가 로그를 저장하며 내부에서 커밋하고, 뒤의 upsert가 실패하면 메시지는 재전달된다 — 이미 커밋된 로그가 **다시 저장**된다.\
   교정: 핸들러가 전체를 **한 트랜잭션**으로 커밋하고 서비스 내부 커밋을 금지, 비멱등 INSERT는 upsert·유일 키로 바꾼다.\
   저장소 순서: 멱등 가드가 있는 쪽을 먼저 쓰면, 재처리 때 그 가드가 "이미 처리됨"으로 막아 **다른 쪽 기록이 유실**된다. 차단 목록 등록은 DB 확정 뒤 캐시 발효 순서로 바꿨다.

7. **워터마크는 성공 후에만.** 색인 실패가 집계되지 않은 채 워터마크가 전진하자, 실패한 문서들이 다음 증분의 조회 범위에서 **영원히 빠졌다**. 교정: 모든 쓰기 경로의 실패를 집계하고 `failed == 0`일 때만 전진.\
   기준점 소실: 워터마크가 가리키는 이전 커밋이 얕은 복제 이력 밖으로 밀려나면 `diff prev..HEAD`가 실패하고, 워터마크가 안 움직이니 **매번 같은 곳에서 실패**(영구 스톨)한다. 교정: diff 실패 시 **경고와 함께 전체 처리로 강등**하고, 전체 처리 후 이번 버전이 아닌 문서를 삭제해 고아를 정리하고, 수동 전체 재처리 경로를 둔다.\
   겹치는 윈도우: 증분 범위를 "직전 1일"로 고정하면 하루 실패가 영구 구멍이다. 쓰기가 **멱등(키 기준 upsert)**이면 윈도우를 7일로 겹쳐 다음 성공 실행이 누락분을 자동 흡수한다(처리량 증가는 수용).

## 문제 구조 (추상화 코드)

### 변형 A — 재독 가능한 입력을 이벤트 append로 저장
① 문제 코드
```rust
for ev in read_from(offset0) { history.append(ev); }   // 재독 때 과거 항목 재기록
let count = history.lines().count();                  // 리비전·재독으로 부풀림
```
② 고친 코드
```rust
let snap = merge_by_key(read_from(offset0), |e| (e.session, e.id));   // (session,id) 병합
snapshot::save_atomic(path, &snap);                                   // temp → rename 덮어쓰기
let count = snap.unique_ids().len();
```
무엇이 깨졌나: 재생 가능한 입력을 비멱등 연산(append)으로 저장했다.

### 변형 B — 취소 불가 부작용 위의 exactly-once 원장
① 문제 코드
```ts
async function deliver(req) {
  if (!ledger.claim(req.id)) return;            // 선기록 claim — 경쟁 창
  try { await withTimeout(write(req), TIMEOUT); }  // 타임아웃이 진행 중 write 를 못 멈춤
  catch { ledger.release(req.id); retry(req); } // 늦은 실쓰기 + 재시도 = 중복
}
```
② 고친 코드
```ts
async function deliver(req) {
  await write(req);                  // 원장·타임아웃·자동 재시도 제거
  acked.add(req.id);
}
// 실패 시 사용자에게 [다시 적용] — 희귀 중복은 "채우기"라 무해 (주석·테스트로 명시)
```
무엇이 깨졌나: 멱등에 가까운 연산에 불필요한 exactly-once를 요구해 경쟁 창을 스스로 만들었다.\
같은 구조: 같은 원장이 4라운드 연속 blocker → 요구를 at-least-once로 하향하자 소멸.

### 변형 C — 재시도가 최초 생성 명령을 재생
① 문제 코드
```python
class Session:
    def __init__(self, cmd): self.cmd = cmd          # ["agent", "--session-id", sid] (신규 생성)
    def restart(self): self.proc = spawn(self.cmd)   # 죽은 뒤 재접속 → 같은 ID 로 또 "생성"
```
② 고친 코드
```python
@ws_route("/ws/{sid}")
async def attach(ws, sid):
    s = sessions.get(sid)
    if s is None or (s.proc is not None and not s.alive):
        await ws.close(code=4404); return           # 클라이언트는 /start 재호출
# /start: 마커가 있으면 ["agent", "--resume", sid] 로 재도출
```
무엇이 깨졌나: 비멱등 명령을 캡처해 재시도에 그대로 썼다.

### 변형 D — 커밋과 발행의 dual write · 소비자 멱등 키 부재
① 문제 코드
```kotlin
tx { job.complete() }        // 커밋
publisher.send(JobCompleted) // 여기서 크래시 → 이벤트 소실, 상태=완료라 재시도 경로도 없음
// 소비자: 재전달·DLQ 재투입마다 보정 처리를 또 기록
```
② 고친 코드
```kotlin
tx { job.complete(); outbox.insert(JobCompleted) }   // 같은 커밋
// 릴레이가 outbox 를 읽어 전달 (at-least-once)
// 소비자: UNIQUE(command_id) + UNIQUE(원 대상 축) — 같은 지시·같은 대상의 이중 상쇄 차단
```
무엇이 깨졌나: 상태 변경과 발행이 별개 쓰기였고, 재전달에 대비한 소비자 유일 키가 없었다(설계 리뷰 단계 사례).\
같은 구조: outbox 발송의 중복 방지책을 "외부 접수 ID 선기록"으로 서술 → 불성립, "요청 측 멱등 키 공유 또는 사후 대조"로 교체.

### 변형 E — 멱등 키 하나로 "중복 무시"와 "재시도"를 동시에 표현
① 문제 코드
```go
key := digest(cmd)                     // 재개 의도를 cmd 에 넣으면 digest 변경 → Conflict
if rec, ok := store.Get(key); ok {     // 밖에 두면 → 멱등 Report, 재실행 안 됨
    return rec.Report()
}
```
② 고친 코드
```go
rec, ok := store.Get(digest(cmd))                  // 충돌 축
if !ok { rec = store.Create(digest(cmd), req) }    // 첫 요청 = 신규 기록 후 실행
if ok && rec.State == Completed { return rec.Report() }   // 완료 = 재개 금지
if ok && req.Attempt <= rec.Attempt { return rec.Report() } // 오래된 attempt (중복 재전송)
rec.Attempt = req.Attempt                          // 재개 축
// 마이그레이션: attempt 없는 구 레코드는 정규화 (기본값 0 이 "재개"로 오인되지 않게)
```
무엇이 깨졌나: 두 의도를 한 키에 담아 어느 쪽도 표현할 수 없었다.

### 변형 F — 재전달되는 핸들러 안의 부분 커밋
① 문제 코드
```python
def on_message(msg):
    write_log(msg)          # 내부에서 commit
    upsert_stats(msg)      # 실패 → 재전달 → write_log 가 또 저장
    db.commit()
```
② 고친 코드
```python
def on_message(msg):
    with db.transaction():             # 서비스 내부 commit 금지, 핸들러 단일 트랜잭션
        write_log(msg)                  # 유일 키 + upsert
        upsert_stats(msg)
# 두 저장소: DB 확정 → 캐시 발효 (멱등 가드 있는 쪽을 먼저 쓰지 않는다)
```
무엇이 깨졌나: 재전달 단위와 트랜잭션 단위가 달랐다(정적 분석으로 발견·수정, 재현 기록 없음).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(변형 A~F)은 "연산 자체를 멱등하게 만든다"이다. 같은 원리(재시도 = 자동 복구)에 다른 방안이 쓰인 사례:

### 방안 1 — 진행 표지는 전량 성공 후에만 조건부 전진
```java
// 문제: 부분 실패가 로그만 남기고 failed() 에 안 잡힘 → 게이트 통과 → 워터마크 전진
if (!r.failures().isEmpty()) log.warn(...);

// 고친
if (!r.failures().isEmpty()) {
    status.recordFailure(r.failures().size());
    status.setLastError("partial failure: " + r.failures().get(0).reason());
}
dispatcher.awaitAll();                          // 비동기 태스크의 집계가 보이도록 happens-before
if (status.failed() == 0) watermark.advance(maxUpdateId);
```

### 방안 2 — 기준점 소실 시 전체 처리로 시끄럽게 강등
```kotlin
val changes = if (prev == null) git.allFiles().map { Added(it) }
              else runCatching { git.changed(prev, head) }
                     .getOrElse { log.warn("diff failed, full"); full = true; git.allFiles().map { Added(it) } }
index(changes, head)
if (full) deleteWhere { it.version != head }    // 고아 정리
writeLastVersion(head)                          // 예외가 나면 여기 못 온다
// + 수동 전체 재처리 엔드포인트, 동시 실행은 compareAndSet(null, head) single-flight
```

### 방안 3 — 겹치는 멱등 증분 윈도우
```python
# 문제: changed_since = today - 1  → 하루 실패 = 그날 변경분 영구 누락
plan_delta(changed_since=today - timedelta(days=7))   # 키 기준 upsert 라 겹쳐도 안전
# 단조 증가 ID 기반 소스는 "대상의 max_id 이후"를 추출해 자체 복구 성질을 가짐
# (단, 동시 트랜잭션에서 ID 할당 순서 ≠ 커밋 순서면 늦게 커밋된 작은 ID 행을 놓칠 수 있다)
```

### 방안 4 — 한 행위의 다중 트리거 제거
```yaml
# 문제: 태그 push + 릴리스 생성 둘 다 게시 워크플로를 트리거 → 불변 저장소가 두 번째 게시 거부
on: { push: { tags: ['v*'] }, release: { types: [created] } }
# 고친(절차): 태그+릴리스를 한 번에 만드는 명령 대신 태그 push만 수행해 1회 발동,
#            릴리스 노트는 게시 완료 후 별도 생성 (워크플로 트리거 자체의 변경은 기록 없음)
git push origin v1.2.3
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 연산을 멱등하게 | 키·스냅샷으로 결과를 정할 수 있다 | 키 설계·트랜잭션 경계 조정 | 키를 잘못 잡으면 정당한 두 건이 합쳐짐 | 재전달·재독이 일상인 처리 |
| 1. 성공 후 조건부 전진 | 모든 쓰기 경로의 실패를 셀 수 있다 | 실패 집계 배선 | 집계에서 빠진 경로가 있으면 다시 영구 누락 | 워터마크·커서 기반 증분 |
| 2. 전체 처리로 강등 | 전체 처리 비용을 감당할 수 있다 | 강등 시 처리량 | 조용히 강등하면 비용 폭증이 숨음(그래서 경고) | 기준점이 외부 이력에 의존 |
| 3. 겹치는 윈도우 | 쓰기가 멱등(키 upsert) | 반복 처리량 | 윈도우보다 긴 장애는 여전히 구멍 | 일 단위 배치, 변경량이 작음 |
| 4. 트리거 단일화 | 대상 저장소가 재게시를 거부한다 | 없음 | 절차를 어기면(태그+릴리스 동시 생성) 재발 | 불변 아티팩트 게시 |

**결론**: 먼저 연산을 멱등하게 만든다 — 그래야 나머지 방안(재시도·겹침·강등)이 안전해진다(기본).\
진행 표지가 있으면 성공 후에만 전진시키고(1), 기준점이 사라질 수 있으면 전체 처리 출구를 둔다(2).\
처리 비용이 작으면 겹치는 윈도우가 가장 단순한 자가 치유다(3).\
대상이 멱등하지 않은 불변 저장소라면 중복 요청 자체를 트리거 단계에서 없앤다(4).

## 방안 비교 — "한 번만 알린다": 되돌릴 수 없는 출력과 기록 중 무엇을 먼저 확정하나

같은 원리(취소할 수 없는 부작용은 "했나 안 했나"를 기록과 원자적으로 맞출 수 없다 — 변형 B)가 작은 셸 스크립트에서 나온 사례다.\
스크립트는 편집 도구 호출 앞에서 도는 훅이고, 작업 폴더마다 **한 번만** 안내 알림(JSON 한 줄)을 표준 출력으로 낸다.\
부작용 = 표준 출력에 쓰기 — 한 번 나간 바이트는 어떤 순서로도 되돌릴 수 없다.\
기록 = 상태 디렉토리의 기록 파일에 "이 폴더는 이미 알렸다"는 한 줄(줄마다 폴더 경로 하나).\
동시 호출은 잠금(`flock`) 하나로 직렬화했다 — "이미 알렸나 확인"과 기록을 같은 잠금 안에서 한다.\
둘을 한 트랜잭션으로 묶을 수 없으므로, 실패가 끼면 **빠지거나(안 뜸) 겹치거나(한 번 더 뜸)** 둘 중 하나는 남는다.

```
                     ┌───── 같은 잠금 안 ─────┐
방안 5  확인 → 기록 확정 ─────────────────────┘ → 출력          출력 실패 = 기록만 남음 → 영영 안 뜸 (at-most-once)
방안 6  확인 → 기록 확정 → 출력 → (실패 시) 되돌리기            되돌리기가 실패·오작동 → 안 뜨거나 다른 기록이 지워짐
방안 7  확인 → ①준비(임시 파일) → ②출력 → ③확정(rename)        ①② 실패 = 기록 파일 그대로 → 다음에 뜸
                                                                ③만 실패 = 이미 나감 + 기록 없음 → 한 번 더 (at-least-once)
```

### 방안 5 — 기록을 확정한 뒤 출력한다 (처음 형태)
```bash
(
  exec 9>>"$record.lock" || exit 1
  flock -x -w 2 9 || exit 1
  if [ -e "$record" ]; then
    grep -qxF -- "$key" "$record"; seen_rc=$?
    [ "$seen_rc" = 0 ] && exit 10                      # 이미 알림
    [ "$seen_rc" = 1 ] || exit 1                       # 읽기 실패를 "없음"으로 보지 않는다
  fi
  temporary=$(mktemp "$dir/.record.XXXXXX") || exit 1
  if [ -e "$record" ]; then
    cat -- "$record" > "$temporary" || { rm -f -- "$temporary"; exit 1; }
  fi
  printf '%s\n' "$key" >> "$temporary" || { rm -f -- "$temporary"; exit 1; }
  mv -fT -- "$temporary" "$record" || { rm -f -- "$temporary"; exit 1; }   # 기록 확정
) 2>/dev/null || record_rc=$?
case "$record_rc" in
  0) printf '%s\n' "$notice" ;;                        # 잠금 밖에서 출력 — 실패해도 기록은 이미 확정됐다
  10) ;;
  *) echo "경고: 알림 기록 실패 — 알림 생략(통과)." >&2 ;;
esac
```
처음 설계의 근거(코드 주석): "먼저 내고 기록이 실패하면 다음 호출이 또 내서 '한 번'이 깨지고, 기록 실패 시 알림을 빼면 최악이 '한 번 빠짐'이라 소음보다 낫다."\
리뷰에서 반대쪽 실패가 지적됐다 — 기록 뒤 **출력이** 실패하면(stdout 닫힘·가득 참) "한 번"이 소비되고 알림은 보이지 않는다. 그 폴더에서는 다시 뜨지 않는다.

### 방안 6 — 출력이 실패하면 기록을 되돌린다 (보상 — 리뷰 1회차 뒤)
```bash
(
  # ... 잠금 · 확인 · 준비 · 기록 확정(방안 5 와 같다) ...
  printf '%s\n' "$notice" && exit 0                    # 출력을 잠금 안으로 옮겼다
  # 출력 실패 — 방금 더한 마지막 줄만 지운다. 잠금을 잡은 채라 마지막 줄은 이 호출의 것이다.
  rollback=$(mktemp "$dir/.record.XXXXXX") || exit 21
  sed '$d' "$record" > "$rollback" && mv -fT -- "$rollback" "$record" \
    || { rm -f -- "$rollback"; exit 21; }
  exit 20
) 2>/dev/null || record_rc=$?
# 21 = "출력 실패·되돌리기도 실패 — 이 작업 폴더의 알림은 다시 뜨지 않습니다(통과)."
```
다음 리뷰에서 **되돌리기 자체**에서 새 결함 3건이 나왔다.
```
① 되돌리기도 실패(임시 파일·mv)  → rc 21 — 결국 "한 번" 소비 (방안 5 의 실패가 그대로 남는다)
② 끝 개행 없는 기록 파일         "A" + "B\n" → "AB\n" 한 줄 → sed '$d' 가 A 의 기록까지 지운다
③ 닫힌 파이프                    printf 에서 SIGPIPE → 서브셸이 죽어 되돌리기 줄에 도달하지 못함, rc 141
                                 → 경고는 "기록 실패"라고 원인을 잘못 말한다  (shell/closed-pipe-sigpipe)
```
한 번 고친 곳의 수정에서 새 결함이 연달아 나왔으므로, 되돌리기를 다듬지 않고 **순서를 다시 설계**했다.

### 방안 7 — 준비 → 출력 → 확정 (이 사례의 선택)
```bash
(
  trap '' PIPE                                         # 닫힌 파이프도 printf 의 rc 로 받는다
  # ... 잠금 파일 배타 생성 · 읽기 전용으로 열기(exec 9<) · 심링크 검사 ...
  flock -x -w 2 9 || exit 1                            # 잠금 실패 — 이번 호출은 생략, 기록 그대로
  if [ -e "$record" ] || [ -L "$record" ]; then
    { [ -f "$record" ] && [ ! -L "$record" ]; } || exit 2
    grep -qxF -- "$key" "$record"; seen_rc=$?
    [ "$seen_rc" = 0 ] && exit 10
    [ "$seen_rc" = 1 ] || exit 2
  fi
  # ① 준비 — 기록 파일은 아직 바이트까지 그대로
  temporary=$(mktemp "$dir/.record.XXXXXX") || exit 2
  if [ -e "$record" ]; then
    cat -- "$record" > "$temporary" || { rm -f -- "$temporary"; exit 2; }
    if [ -s "$record" ]; then                          # 끝 개행이 없으면 먼저 보탠다 — 줄 경계 보존
      last_byte=$(tail -c 1 -- "$record") || { rm -f -- "$temporary"; exit 2; }
      if [ -n "$last_byte" ]; then printf '\n' >> "$temporary" || { rm -f -- "$temporary"; exit 2; }; fi
    fi
  fi
  printf '%s\n' "$key" >> "$temporary" || { rm -f -- "$temporary"; exit 2; }
  # ② 출력 — 되돌릴 수 없는 부작용
  printf '%s\n' "$notice" || { rm -f -- "$temporary"; exit 3; }
  # ③ 확정 — 커밋 지점을 부작용 뒤로
  mv -fT -- "$temporary" "$record" || { rm -f -- "$temporary"; exit 4; }
) 2>/dev/null || record_rc=$?
# 경고는 단계별 한 줄: 1 잠금 · 2 준비 · 3 출력("기록은 그대로라 다음 쓰기에서 다시 뜬다")
#                     4 확정("알림은 나갔으나 확정 실패 — 다음 쓰기에서 한 번 더 뜬다")
```
되돌리기 단계가 없으니 되돌리기의 실패도 없다.\
①·②가 실패하면 기록 파일은 바이트까지 그대로다(다른 폴더의 기록도). 잠금 대기 실패로 생략된 호출도 "한 번"을 소비하지 않으므로, 같은 폴더의 다음 쓰기에서 뜬다 — 이것이 "빠지지 않는다"의 뜻이다(어느 호출에서든 반드시 뜬다는 뜻이 아니라, 영영 안 뜨는 경로가 없다는 뜻).\
③만 실패하면 알림은 이미 나갔고 기록이 없으므로 다음 호출에서 한 번 더 뜬다.\
둘을 동시에 막을 수는 없다는 설명을 듣고, 사용자가 "안 뜨는 일은 없게, 드물게 한 번 더 뜨는 것은 받아들인다"를 골랐다 — 코드 주석에는 "빠지는 것보다 한 번 더가 낫다"로 남겼다.

출력 자체가 반만 나가는 경우도 따져야 했다 — 확정을 미뤄도 이미 나간 절반은 되돌릴 수 없다.\
파이프에 PIPE_BUF(Linux 4096바이트) 이하를 **한 번의** `write(2)` 로 쓰면 통째로 쓰인다(pipe(7)).\
리뷰 감사에서 "길이가 짧다"만으로는 증명이 아니라는 지적이 있었다 — 쓰는 쪽이 여러 번의 write 로 나누면 이 보장이 없다.\
그래서 strace 로 실측했다: 알림 출력은 write(2) 한 번, 313바이트였다. 알림 길이가 4096 보다 짧다는 것은 테스트 사례로 고정했다.\
파이프가 아닌 stdout(파일로 돌린 출력의 디스크 풀 등)에서 일부만 쓰이는 경우는 보장 범위 밖으로 명세에 적었다(그때도 기록은 확정하지 않는다).

| 방안 | 보장 | 커밋 지점 | 실패 모드 | 맞는 조건 |
|------|------|-----------|-----------|-----------|
| 5. 기록 → 출력 | 많아야 한 번(at-most-once) | 부작용 앞 | 출력 실패 = 영구 누락, 경고만 남는다 | 중복이 해롭고 누락이 싸다 |
| 6. 기록 → 출력 → 되돌리기 | 겉으로는 정확히 한 번 | 부작용 앞 + 보상 | 보상의 실패·부분 동작(줄 경계·신호)이 새 누락과 다른 기록 손상을 만든다 | 보상이 단순하고 원자적일 때만 — 이 사례는 아니었다 |
| 7. 준비 → 출력 → 확정 | 적어도 한 번(at-least-once) | 부작용 뒤 | 확정 실패 = 한 번 더 뜬다 | 중복이 무해하고 누락이 비싸다 |

**결론**: 되돌릴 수 없는 부작용과 그 기록을 한 원자 단위로 묶을 수 없으면, 고를 수 있는 것은 "기록 먼저(at-most-once)"와 "부작용 먼저·확정 나중(at-least-once)" 둘이다 — 어느 실패가 더 싼지로 고른다.\
정확히 한 번을 흉내 내려고 보상(되돌리기)을 붙이면 보상 자체가 실패하고 오작동하는 경로가 생긴다 — 변형 B 의 원장이 리뷰마다 새 결함을 낸 것과 같은 구조다.\
보상을 다듬기보다 **커밋 지점을 부작용 뒤로 옮겨** 되돌릴 것을 없앤다. 확정 전 상태는 임시 파일에 준비하고 rename 한 번으로 바꿔, 확정하지 않은 동안 원본이 그대로이게 한다.\
부작용이 출력이면 그 출력 자체가 원자적인지(한 번의 write·PIPE_BUF 이하)도 실측으로 확인한다.

검증 기록: 2026-11-22 — 사건 기록·리뷰 기록(3회차)·수정 전후 코드 대조·추상화. 실측(같은 기록): 새 순서에서 테스트 426개 통과 · 되돌리기를 남긴 변형·출력 전에 확정하는 변형(8개 빨강)·줄 경계 보탬을 뺀 변형(2개 빨강) 모두 빨강 · 알림 출력 write(2) 1회 313바이트(strace).
