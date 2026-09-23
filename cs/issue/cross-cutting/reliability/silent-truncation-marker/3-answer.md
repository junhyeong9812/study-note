# cs/issue/cross-cutting/reliability/silent-truncation-marker — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 추출 블록·대표 원문 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답

<!-- 질문 1:1 대응 -->

1. 호출자는 반환값의 모양만 본다. 완주한 `Vec`과 예산이 떨어져 멈춘 `Vec`이 같은 타입이면, 호출자에게 "이게 전부다"와 "여기서 포기했다"를 가를 정보가 없다.\
"결과 0개"는 특히 위험하다. "대상이 정말 없음"이라는 정상 답과 모양이 똑같아서, 실제로는 예산이 무관한 디렉토리(캐시 등)에서 다 떨어졌는데도 누구도 이상하다고 느끼지 않는다.
   > **무음 절단(silent truncation)** — 상한 때문에 결과 일부가 버려졌는데 그 사실이 반환값·로그·화면 어디에도 드러나지 않는 것.

2. 방문 순서가 readdir 순서를 따르는 깊이 우선 탐색이기 때문이다. 예산이 어디서 떨어지는지는 트리 모양과 파일시스템이 돌려주는 순서에 달려 있고, 그 순서는 시스템 상수가 아니다.\
그래서 "몇 개가 누락된다"는 인용 가능한 성질이 아니다. 인용해야 할 성질은 **"누락이 일어나도 아무 신호가 없다(침묵)"** 이다.

3. 절단이다. 스크롤백 링버퍼는 상한에 닿으면 **앞부분(오래된 바이트)을 버리도록** 설계돼 있다. 큰 응답은 머리가 잘린 채 남고, 머리 없는 JSON은 파서 입장에서 그냥 "형식이 틀린 문자열"이다.\
절단 감지가 없으면 손실은 원인(상한)이 아니라 다음 단계의 오류 유형(파싱 실패)으로 나타나서, 디버깅이 엉뚱한 곳을 향한다.
   > **링버퍼(ring buffer)** — 고정 크기 버퍼에 새 데이터가 들어오면 가장 오래된 데이터를 덮어쓰는 구조. 최근 것만 필요할 때 맞고, 완결성이 필요할 때는 맞지 않다.

4. 표시할 때 자르면 원천은 온전하다. 필요하면 원문을 다시 가져오면 된다. 저장할 때 자르면 **잘린 본이 원천이 된다.** 원래 소스가 교체·삭제되면 복구할 길이 없고, 다시 열어도 절단본으로 고정된다.\
그래서 저장은 전문으로 하고, 자르는 것은 화면·IPC 전송처럼 **소비 직전의 경계**에서만 한다. 잘린 사실은 플래그로 함께 보낸다.

5. 길이 비교는 "딱 상한 길이의 정상 결과"와 "상한에서 잘린 결과"를 구분하지 못하고, 생산자가 경계를 조정하면(예: 공백 경계에서 끊기) 결과가 상한보다 짧아져 비교를 빠져나간다.\
생산자는 자기가 잘랐는지 **확실히 안다.** 그 사실을 `{text, truncated}` 같은 명시 플래그로 넘기면 소비자가 추측할 필요가 없다.

6. 상한을 올리면 지금 보이는 누락은 사라지지만, 데이터가 101개를 넘는 날 같은 일이 다시 조용히 일어난다. 문제를 뒤로 미룬 것이다.\
목표는 "제한 제거"가 아니라 **"무음 손실 제거"** 다. 폭주를 막는 상한은 두되, 넘으면 **명시 예외**로 멈추거나 절단 표식을 붙여 소비자가 알게 해야 한다.

7. 경고 로그는 손실이 **일어났음을** 알릴 뿐, 청크 뒷부분이 검색에서 빠지는 결과는 그대로다.\
앞 단계의 최대 출력(청크 ≤ 약 8K자)보다 뒤 단계 입력 상한(9000자)을 크게 잡으면, 정상 입력에서는 절단이 **구조적으로 불가능**해진다. 경고는 부등식이 깨졌을 때를 위한 안전벨트로 남긴다.
   > **상한 정렬(cap alignment)** — 파이프라인의 각 단계 상한을 `앞 단계 최대 출력 ≤ 뒤 단계 입력 상한`이 되도록 맞추는 것.

## 문제 구조 (추상화 코드)

> 사건들은 "상한에 걸린 결과가 어떤 모양으로 호출자에게 가나"로 나뉜다.

### 변형 A — 예산 소진과 완주가 같은 반환형

① 문제 코드
```rust
fn scan_roots(start: &Path) -> Vec<Root> {
    let mut roots = Vec::new();
    let mut visited = 0;
    for dir in dfs(start) {                          // readdir 순서 DFS
        visited += 1;
        if visited > VISIT_BUDGET || depth(dir) > MAX_DEPTH { break; }   // 조용히 멈춤
        if is_root(dir) { roots.push(dir.into()); }
        if roots.len() >= MAX_ROOTS { at_cap = true; break; }           // 이 상한만 표시됨
    }
    roots                                            // "포기"와 "완주"가 같은 Vec
}
// 홈 디렉토리 스캔: 예산이 캐시 디렉토리에서 소진 → 수 초 뒤 0개
```
② 고친 코드 (스캐너를 소유하지 않아 직접 못 고친 경우의 대응)
```rust
// 1) 넓은 기본 스캔을 쓰지 않고, 목록 출처를 명시한다
let listing = from_explicit_sources(env_roots, workspace_file, base_dir);   // 각 출처가 notes로 무엇을 했는지 보고
// 2) 계약을 사실로 축소: at_cap은 "root 개수 상한"만 뜻한다 — false를 "전부"로 읽지 말 것
// 3) 침묵 자체를 테스트로 고정
#[test] fn a_scan_that_gave_up_is_indistinguishable_from_a_complete_one() { /* ... */ }
```
무엇이 깨졌나: 방문·깊이 예산 소진이 반환값에 흔적을 남기지 않아, 부분 결과가 완전한 결과로 읽혔다.\
처방 후보로 기록된 것: 예산 소진을 부분 결과 플래그로 보고, 캐시류 디렉토리 조기 가지치기, 스캔 루트를 프로젝트 기반으로.

같은 구조:
- 같은 스캐너를 여러 소비자가 썼고, 한 곳은 "고치지 않고 계약에 이름 붙여 등재"로 처리했다(수정 방안 미기록).

### 변형 B — 오래된 것을 버리는 링버퍼로 완결 응답을 수집

① 문제 코드
```rust
let buf = RingBuffer::with_cap(SCROLLBACK_CAP);   // 1MB, 넘치면 앞부분 drain
run_command(cmd, &buf);
let reply: Reply = serde_json::from_slice(buf.bytes())?;   // 큰 응답 → 머리 잘림 → "not JSON"
// 응답 크기 선언은 64MB
```
② 고친 코드
```rust
let collector = ReplyCollector::with_cap(MAX_REPLY);   // 응답 전용, 선언과 같은 64MB
run_command(cmd, &collector);
let bytes = collector.assemble()?;                     // 상한 도달 시 Err("reply truncated at cap")
let reply: Reply = serde_json::from_slice(&bytes)?;
// 스트림 초기 seed에도 같은 검사, ~3MB 응답 테스트로 이빨 확인
```
무엇이 깨졌나: 버퍼의 설계 목적(최근 것만)과 용도(전부 필요)가 달랐고, 절단이 파싱 오류로 위장했다.

### 변형 C — 절단본을 원천에 저장하고, 절단 여부를 모양으로 추론

① 문제 코드
```rust
let text = cap_content(&full, 32 * 1024);
snapshot.save(text);                         // 잘린 본이 영구 원천이 된다
// ...
let out = run_model(input);
let truncated = out.len() >= OUTPUT_CAP;     // 길이로 추론 → 공백 경계에서 끊기면 우회
apply(out);                                  // cap 도달 결과도 정상처럼 적용
let prompt = format!("<memo>{input}</memo>"); // 입력에 종료 태그가 있으면 결과가 무음 절단
```
② 고친 코드
```rust
snapshot.save(&full);                                    // 저장은 전문
emit(Payload { text: cap_content(&full), content_truncated: true_if_cut });   // 자르는 건 전송 경계에서만
// 화면: 절단 배너 + 원문 lazy 조회 커맨드

let RunResult { text, truncated } = run_model_capped(input);   // 생산자가 플래그로 알린다
if truncated { return Err(NotApplied("output cap reached")); } // cap 도달 = 적용 불가 + 사유

let tag = random_nonce();                                      // 고정 구분자 대신 nonce
if input.contains(&closing(tag)) { return Err(Rejected); }     // 입력에 종료 태그 → 사전 거부
// 결과 길이가 급감하면 경고 배지
```
무엇이 깨졌나: 상한으로 자른 데이터가 원본과 구분되는 표식 없이 원천 저장·적용 경로로 흘러갔다.\
lazy 조회가 없는 경로에서는 본문에 "전체 N바이트 중 앞부분만" 문구를 남겨 표식을 대신했다.

### 변형 D — 상한 초과를 "조용히 줄이고 계속"

① 문제 코드
```java
for (String kw : keywords) {
    if (kw != null && !kw.isBlank() && clauses < MAX_CLAUSES) {   // 초과분은 무음 무시 → 리콜 손실
        query.add(kw); clauses++;
    }
}
```
② 고친 코드
```java
if (keywords.size() > MAX_TOTAL_KEYWORDS) {                       // 폭주 안전핀 = 절단이 아니라 명시 예외
    throw new LimitExceeded(keywords.size());
}
List<Query> chunks = partition(keywords, MAX_CLAUSES);            // 절단 대신 청크로 나눠 합집합
return union(chunks);
```
무엇이 깨졌나: 상한을 "넘치면 버린다"로 구현해, 호출자·운영자 모두 결손을 몰랐다.

① 문제 코드 (표시용 슬라이스)
```python
for bucket in buckets[:10]:          # 11번째 이후 버킷이 경고 없이 사라짐 → 필터 합계 < 전체 건수
    out.append(normalize(bucket))
```
② 고친 코드 (기록된 조치: 다른 경로와 같은 상한으로 상향)
```python
for bucket in buckets[:100]:         # 연도 100, 국적류 20 — 상한 제거·집계 크기 연동은 기록 없음
    out.append(normalize(bucket))
```
무엇이 깨졌나: 경로마다 복사된 코드의 상한이 제각각이라 일부 경로만 절단됐다. 상향은 누락을 뒤로 미룰 뿐 표식은 여전히 없다(질문 6).

같은 구조:
- 정적 배열 길이가 공표 수치와 달라도 조용히 잘릴 위험 → 기동 시 길이 검사로 fail-fast(뮤테이션으로 실증).
- 사전 크기가 최소 기준에 한참 못 미치는데 fail-open으로 색인을 계속 → 색인분 전체가 축소판 → 사전 완성 후 전체 재색인.

## 검증 기록

- 2026-09-24: 추출 블록·대표 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

> 기본 방안(변형 A~D)은 **"잘린 결과에 표식을 붙이거나 명시 오류로 바꾼다"** 이다.\
> 아래 세 방안은 표식 대신 절단 자체의 모양을 바꾼다.

### 방안 1 — 레코드 단위 중단 대신 총량 예산 + 선할당 금지

① 문제 코드
```rust
for rec in records {
    if rec.len() > RECORD_CAP { break; }      // 첫 초과 레코드에서 중단 → 뒤의 정상 레코드 무음 탈락
    let buf = reader.read_until(b'\n')?;      // 상한 확인 전에 메모리를 먼저 할당 → 총량 상한 우회
    // ...
}
```
② 고친 코드
```rust
let mut remaining = TOTAL_BUDGET;
for rec in records {
    let cap = RECORD_CAP.min(remaining);      // 레코드 상한은 남은 예산을 반영
    match read_bounded(reader, cap)? {
        Oversized => { skipped += 1; continue; }   // 초과 레코드는 건너뛰고 계속
        Line(l)   => { remaining -= l.len(); handle(l); }
    }
}
if not_found { eprintln!("... not detected within budget"); }   // 미검출 로그
```

### 방안 2 — 상한 있는 저장소의 축출 표시 + 재사용 id 무효화

① 문제 코드
```rust
fn record(&mut self, id: Id, reason: Reason) {
    if self.items.len() == CAP { self.items.pop_front(); }   // 안 읽힌 항목도 무표시 축출
    self.items.push_back((id, reason));                      // "아직 없음" == "밀려 사라짐"
}
```
② 고친 코드
```rust
fn record(&mut self, id: Id, reason: Reason) {
    if self.items.len() == CAP {
        let victim = self.evict_read_first();                 // 읽힌 것부터 밀어낸다
        if !victim.read { self.tombstones.insert(victim.id); } // 안 읽힌 채 밀려나면 표식
    }
    self.items.push_back((id, reason));
}
fn opened(&mut self, id: Id) { self.forget(id); }   // id를 새 소유자에게 준 즉시 옛 기록 삭제
// 조회: tombstone이면 "보관 한도에 밀려 사라졌습니다"
```

### 방안 3 — 단계 간 상한 부등식을 구조적으로 정렬

① 문제 코드
```text
chunker:   chunk ≤ 8KB   (≈ 8192자)
embedder:  input[:6000]  + warn("truncated")     ← 뒤 단계 상한 < 앞 단계 최대 출력 → 청크 뒷부분 검색 제외
```
② 고친 코드
```text
chunker:   chunk ≤ 8KB   (≈ 8192자)
embedder:  input[:9000]  + warn("truncated")     ← 9000 > 8192 → 정상 입력에선 절단 불가, 경고는 안전벨트
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 표식·명시 오류 | 소비자가 표식을 읽을 수 있다 | 반환형·계약 변경 | 소비자가 표식을 무시하면 여전히 침묵 | 상한을 없앨 수 없는 탐색·수집·표시 |
| 1. 총량 예산 + 선할당 금지 | 입력이 레코드 단위로 나뉜다 | 레코드별 상한 계산 | 초과 레코드 자체는 여전히 빠짐(로그로만) | 로그·기록 파일처럼 거대 레코드가 드문 입력 |
| 2. 축출 표시 + id 무효화 | 저장소가 고정 크기다 | tombstone 관리 | tombstone도 결국 상한이 필요 | 소비자가 늦게 읽으러 오는 유계 캐시 |
| 3. 상한 부등식 정렬 | 앞 단계 최대 출력이 알려져 있다 | 뒤 단계 상한 상향(자원) | 앞 단계 상한이 바뀌면 부등식이 깨짐 | 여러 단계가 각자 상한을 가진 파이프라인 |

**결론**: 상한을 없앨 수 없고 결과가 호출자에게 그대로 가면 기본 방안(표식 또는 명시 오류)이 맞다.\
절단 지점이 "레코드 하나"라서 정상 데이터 꼬리가 잘린다면 총량 예산으로 바꾼다(1).\
유계 저장소는 축출 자체가 정상 동작이므로, 표식으로 "밀려 사라짐"을 "아직 없음"과 구분한다(2).\
단계 간 상한이 서로 알려져 있으면 부등식을 맞춰 절단이 아예 일어나지 않게 하는 것이 가장 확실하다(3).
