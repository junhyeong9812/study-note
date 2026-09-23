# cs/issue/reliability/change-detection-key-design — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **지문의 누락 축.** 지문이 표시 상태 일부(예: 항목 수·revision)만 보면, 나머지 상태(답변 텍스트·토큰 사용량·모델 이름)만 바뀐 경우 지문이 같아 "변화 없음"으로 판정된다.\
그러면 emit·스냅샷 저장이 건너뛰어지고 화면(게이지·타임라인)은 낡은 채 멈춘다 — 판정 로직은 설계대로 "변화 없음"을 보고했으므로 **에러가 나지 않는다**.\
교정은 지문 튜플에 빠진 축을 넣고, 불변식 "지문은 표시에 영향을 주는 모든 상태를 포함한다"를 문서화하는 것이다.
   > **fingerprint(지문)** — 큰 상태를 비교하지 않고 변화 여부만 싸게 판단하려고 만든 요약값.

2. **근사 키의 충돌.** 합은 서로 다른 조합이 같은 값을 낼 수 있고, **리셋되는 카운터**의 합은 재구축(카운터가 1부터 재부여) 뒤 우연히 예전 값과 같아진다 — "내용은 다른데 키가 같다"(ABA류).\
길이만 보면 같은 길이 재작성을, 마지막 uuid만 보면 uuid 없는 레코드 append를, 설정 리비전만 보면 "같은 설정 + 새 이미지"를 놓친다.\
교정: 재구축 때만 증가하는 **세대 카운터**를 키에 더하거나, 원천의 정체성(파일 서명 `(len, mtime_ns)`)을 키로 쓴다.\
판정식이 여러 곳에 복제돼 있으면 서로 발산하므로 **단일 판별 함수**로 모은다.
   > **ABA 문제** — 값이 A→B→A로 돌아와 "안 바뀌었다"고 오판되는 현상.

3. **디렉터리 mtime.** 디렉터리의 mtime은 **자기 직속 엔트리(이름) 목록이 바뀔 때만** 갱신된다 — 하위 파일 내용이 바뀌거나 손자 폴더에 파일이 생겨도 움직이지 않는다.\
`YYYY/` 폴더는 새 월 폴더가 생길 때만 갱신되므로 연초 mtime을 가진 채로 남고, "최근 mtime 폴더만 내려간다"는 가지치기가 오늘 파일이 든 가지 전체를 건너뛴다 — 결과는 빈 목록(무음).\
교정: 디렉터리 mtime 필터를 버리고 전체 순회 + **파일** mtime으로 판정, 재파싱 절약은 파일 서명으로.

4. **mtime 보존 복원과 해상도.** 증분 빌드는 소스 mtime이 산출물보다 새로울 때만 재컴파일한다.\
내용을 원복하면서 mtime을 예전 값으로 보존하면 빌드는 "안 바뀜"으로 보고 **직전 뮤턴트가 든 바이너리**를 재사용한다 — 다음 케이스 결과가 전부 무효(실제로 1차 실행 전체를 버림).\
교정: 원복 후 `touch`로 재컴파일을 강제하고, 원복 잔재 0을 확인한다.\
초 단위 mtime은 같은 초 안의 연속 변경을 같은 값으로 보이게 하므로 `st_mtime_ns`를 쓰고, 추가·삭제까지 잡으려면 (상대경로, ns mtime) 목록을 해시한다.

5. **자라는 값의 게이팅.** 프롬프트는 등장 순간 확정되지만 답변은 여러 폴에 걸쳐 자란다.\
"이 턴의 답변을 보냈나"를 **키 존재**로 판정하면 첫 조각을 보낸 뒤 이후 성장은 전부 "이미 보냄"으로 억제돼 **첫 조각에서 얼어붙는다**.\
게이트를 없애면 매 폴(수백 ms)마다 전문을 재전송해 대역폭이 폭증한다.\
교정: **값으로 게이팅**하되 값 사본(메모리 2배) 대신 `(길이, 해시)` 지문만 보관한다.

6. **잠금 키 ≠ 무효화 키.** 무효화 키는 "결과가 바뀌면 키도 바뀌어야" 옳다. 잠금 키는 "같은 대상이면 키가 같아야" 옳다.\
잠금 키에 가변 서명(`len-mtime`)을 넣으면, 진행 중 파일은 델타마다 서명이 바뀌어 매번 **새 키 = 잠금 없음**이 되고 재회수 → 새 서명 → 재회수 루프가 선다(초당 수백 회 연결, 본문 사본 누적).\
판정 축을 "내용이 비었나"로 두면 빈 성공 응답이 매 렌더마다 조건을 되살리는 같은 구조가 된다.\
교정: 잠금 키는 **불변 주소**(호스트·세션·에이전트·경로)만, 가변 서명은 `isStale()` 같은 **신선도 표시**로 분리(재회수는 사용자 동작), 캐시는 정체성당 한 벌 교체.
   > **정체성(identity) 키** — "같은 것"을 가리키는 값. 대상의 내용이 바뀌어도 변하지 않아야 한다.

7. **오프셋 tail의 불연속.** 오프셋 리더는 보통 "파일이 오프셋보다 짧아지면 처음부터"만 처리한다.\
rename으로 **더 큰 새 파일**이 들어오거나, truncate 후 오프셋을 넘겨 재성장하거나, **같은 길이로 원자 교체**되면 길이 조건이 걸리지 않아 스트림은 연속으로 보이고 그 사이 내용은 무음 유실된다.\
교정: 매 tick `(dev, ino, len, head 256B)`를 기록해 dev/ino 변경 = 교체, 길이 감소 = 절단, 선두 바이트 **접두 불일치** = 재작성으로 판정하고 0부터 재동기 + 알림.\
head는 접두 비교라 정상 append를 오탐하지 않는다. 잔여 한계: truncate 후 재성장 + 선두 256B 동일은 못 잡는다(명시).

## 문제 구조 (추상화 코드)

### 변형 A — 지문이 표시 상태 일부만 반영
① 문제 코드
```rust
let fp = (items.len(), rev_sum, turns.len(), answer_len_sum, dates.len(), sub_count);
if fp != last_fp { emit(snapshot()); last_fp = fp; }   // 사용량·모델만 바뀐 레코드는 무시
```
② 고친 코드
```rust
// 불변식: fp는 표시에 영향을 주는 모든 상태를 포함한다
let ctx_fp = t.last_usage().map(|u| u.input + u.cache_read + u.cache_creation).unwrap_or(0);
let model_fp: u64 = t.model().map(|m| m.bytes().map(u64::from).sum()).unwrap_or(0);
let fp = (items.len(), rev_sum, turns.len(), answer_len_sum, dates.len(), sub_count,
          token_sum, ctx_fp, model_fp);
```
무엇이 깨졌나: 감지 키가 출력의 입력 일부만 덮었다.\
같은 구조: 변경 알림을 "건드린 도구 항목"에서만 발생시켜 도구 없는 Q&A 턴이 화면에 안 나옴 → 전체 상태 튜플 지문 + 변화 시 전체 스냅샷 emit.

### 변형 B — 리셋 가능한 카운터의 합을 버전 키로
① 문제 코드
```rust
let rev = items.iter().map(|i| i.revision).sum::<u64>();   // 재구축 시 revision 1부터 재부여
if rev == cached.rev { return cached.body; }               // 같은 합·다른 내용 → stale
```
② 고친 코드
```rust
struct Frame { /* ... */ sig: String }        // 원천 파일 서명 (len, mtime_ns)
let fp = (/* ... */, sub_gen);                // 재활성 확정 시에만 증가하는 세대 카운터
// 프론트 캐시: e.sig === frame.sig 일 때만 fresh
```
무엇이 깨졌나: 단조가 아닌 파생값을 식별자로 썼다.

### 변형 C — 단일 특징으로 "같은 내용" 판정
① 문제 코드
```rust
fn is_latest(a: &Stat, b: &Stat) -> bool { a.bytes == b.bytes }   // 판정식이 세 곳에 제각각
```
② 고친 코드
```rust
fn same_content(&self, other: &Stat) -> bool {                    // 단일 판별식
    if self.lines != other.lines { return false; }
    match (&self.last_uuid, &other.last_uuid) {
        (Some(a), Some(b)) => a == b && self.bytes == other.bytes, // uuid AND bytes
        _ => self.bytes == other.bytes,
    }
}
```
무엇이 깨졌나: 한 특징(크기·마지막 id)을 바꾸지 않는 변경이 보이지 않았고, 복제된 판정식이 서로 발산했다.\
같은 구조: 파일 "완료"·캐시 판정을 길이 단독으로 → `(len, mtime_ns)` 서명.\
같은 구조: 배포 레코드 승격을 설정 리비전만으로 비교 → "같은 설정 + 새 이미지"(대다수 배포)를 중복으로 삼킴 → 레코드 상태 전체(커밋·요청 id 포함) 비교.

### 변형 D — mtime의 의미·해상도·보존
① 문제 코드
```rust
for year in dirs(root) {
    if mtime(year) < since { continue; }          // 디렉터리 mtime = 직속 엔트리 변경만
    // ...
}
```
```sh
cp -p original.rs src/x.rs && cargo test         # mtime 보존 원복 → 재컴파일 skip
```
② 고친 코드
```rust
for f in walk(root).filter(|p| p.ends_with(".jsonl")) {
    if file_mtime(f) < spawn_time - 2s { continue; }   // 파일 mtime으로 판정
    if sig(f) == cached_sig(f) { continue; }           // (len, mtime) 같으면 재파싱 생략
}
```
```sh
cp original.rs src/x.rs && touch src/x.rs && cargo test   # 재컴파일 강제, 원복 잔재 grep 0 확인
```
```python
h = sha1()
for rel, st in sorted(walk_files(root)):          # 추가·삭제·수정 모두
    h.update(rel.encode()); h.update(str(st.st_mtime_ns).encode())   # 초 단위 대신 ns
```
무엇이 깨졌나: mtime을 "하위 전체의 변경 시각"·"내용이 바뀌면 반드시 바뀌는 값"으로 착각했다.\
같은 구조: 사이드카 캐시 신선도를 mtime 단독으로 → `스키마 버전 + 본문 길이 + mtime` 3중 결합(불일치 = stale → 재생성).

### 변형 E — 자라는 값을 키 존재로 게이팅
① 문제 코드
```rust
if sent.contains(&turn_id) { continue; }         // 첫 조각 뒤 성장분 억제
sent.insert(turn_id); send(answer);
```
② 고친 코드
```rust
let mark = (answer.len(), fnv(answer));          // 값 사본 대신 길이+해시
if sent.get(&turn_id) == Some(&mark) { continue; }
sent.insert(turn_id, mark); send(answer);
```
무엇이 깨졌나: 감지 키가 값의 변화를 포함하지 않았다(게이트를 없애면 반대로 매 폴 전문 재전송).

### 변형 F — 정직한 키가 없는 캐시
① 문제 코드
```ts
cache.key = dirMtime(project)   // 디렉터리 밖 심링크 대상·coarse mtime FS 변경을 못 잡음
```
② 고친 코드
```ts
// 입력 전부를 덮는 키를 만들 수 없으면 캐시를 두지 말고 비용 자체를 줄인다
const label = readHeadFileDirectly(repo)        // 외부 프로세스 호출 → 파일 직독
```
무엇이 깨졌나: 캐시 키가 결과에 영향을 주는 입력(심링크 대상)을 덮지 못했다.\
반대 방향(같은 원리): 불변 스토어에서 "변화 없음"인데 새 객체 `{}`를 반환하면 **모든 구독자가 깨어난다** → `set(s => changed ? {...s, ...} : s)`로 자기 자신을 반환.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "변경 감지 키에 결과의 입력 전부를 넣는다"이다. 같은 원리에 키의 역할이 달라 다른 방안이 쓰인 사례:

### 방안 1 — 파일 정체성 튜플 (dev, ino, len, head)
```rust
// 문제: if len < offset { offset = 0 }   // 교체·재성장·동일 길이 교체를 못 봄
struct FileMark { dev: u64, ino: u64, len: u64, head: Vec<u8> /* 첫 256B */ }
fn resync_reason(prev: &FileMark, now: &FileMark) -> Option<Resync> {
    if prev.dev != now.dev || prev.ino != now.ino { return Some(Resync::Replaced); }
    if now.len < prev.len { return Some(Resync::Truncated); }
    if !now.head.starts_with(&prev.head) { return Some(Resync::Rewritten); }   // 접두 비교: append 오탐 0
    None
}
// Some(_) → 0부터 재구축 + 알림 ("반복이지 유실 아님" — id로 병합)
```

### 방안 2 — 잠금 키는 불변 주소만, 신선도는 분리
```ts
// 문제: 가변 서명이 잠금 키에 → 델타마다 새 키 → 재회수 무한 루프
const lockKey = `${session}/${agentId}#${sig}`          // sig = `${len}-${mtimeNs}`
if (!attempted.has(lockKey)) { attempted.add(lockKey); fetch() }

// 고친: 자동 회수 원시 하나로 통합
const key = bodyKey(host, session, agentId)             // 주소만
if (!entry(key).attempted && !inFlight.has(key)) { inFlight.add(key); fetch(key) }
const stale = isStale(entry(key), sig)                  // 신선도는 표시만 — 재회수는 사용자 버튼
// 같은 주소+같은 인자 요청은 합치고, 다른 인자면 세대를 올려 늦은 응답을 버림
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 입력 전부를 감지 키에 | 결과의 입력을 열거할 수 있다 | 키 계산 비용 | 축 하나 누락 = 무음 stale | 폴링 emit·캐시 무효화·빌드 |
| 1. 파일 정체성 튜플 | 읽는 파일이 교체·절단될 수 있다 | 매 tick stat + 256B 읽기 | truncate 후 재성장 + 선두 동일은 미탐 | append 로그 tail |
| 2. 잠금 = 주소, 신선도 분리 | 부수효과(원격 호출)를 한 번만 걸어야 한다 | 자동 재회수 포기(사용자 버튼) | 신선도 표시를 사용자가 놓칠 수 있음 | 자동 회수·중복 요청 억제 |

**결론**: 키를 만들기 전에 **역할**을 먼저 정한다.\
"바뀌었나"를 묻는 키는 입력 전부를 넣어야 하고(빠지면 갱신 누락), "같은 것인가"를 묻는 키는 불변 정체성만 넣어야 한다(가변값이 들면 무한 루프).\
읽고 있는 파일 자체가 바뀔 수 있으면 내용 키가 아니라 **파일 정체성**으로 불연속을 먼저 판정한다.
