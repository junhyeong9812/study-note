# cs/issue/network/payload-transfer-cost — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **크기 × 빈도.**\
   1회 약 24MB × 초당 약 6.7회(150ms 주기) ≈ 초당 167MB가 IPC를 지난다.\
   이 프레임워크는 이벤트 payload를 참조가 아니라 **직렬화 문자열로 통째로** 건넸고, 수신 측(웹뷰)은 그 버퍼를 공유 매핑으로 받아 회수 속도보다 빨리 쌓였다 — "emit 1회 = 그 크기의 off-heap 버퍼 1개"가 고빈도로 곱해진 것이다(수신 측이 왜 늦게 회수하는지는 원문도 추론으로 표기).\
   결정적이었던 것은 payload의 77%가 **이미 끝나서 다시는 바뀌지 않는 본문**(완료된 하위 작업의 전사)이었다는 점이다 — 바뀌지 않는 데이터를 매 틱 다시 보내고 있었다.

2. **측정 도구의 관측 범위.**\
   개발자 도구 힙 스냅샷은 스크립트 엔진의 힙만 본다. 메모리의 66%(80개 매핑·3.44GB)는 힙 밖의 **공유 메모리 매핑**에 있었다.\
   `/proc/<pid>/smaps`로 프로세스 매핑을 종류별로 분해해서야 보였고, 매핑 크기 ÷ 2(UTF-16) ≈ payload 크기로 독립 교차검증했다.\
   의심 받던 UI 라이브러리들(터미널·렌더러·에디터)은 전체의 1% 미만으로 무죄였다 — 도구가 못 보는 곳에 범인이 있으면, 보이는 곳의 용의자를 계속 의심하게 된다.
   > **off-heap 메모리** — 언어 런타임의 GC 힙 밖에서 잡힌 메모리. 힙 스냅샷·GC 통계에 잡히지 않는다.

3. **deferred hydration이 줄이는 항.**\
   **크기** 항을 줄인다 — 빈도(150ms)는 그대로 두고, 매 틱 싣는 것을 메타(id·부모·개수·완료 여부·서명)로 바꿨다. 본문은 사용자가 펼칠 때 별도 요청으로 한 번만 가져온다(정본은 디스크).\
   재유출 방지는 3중: ①메타 타입에 **본문 필드 자체가 없음**(타입 보장) ②모든 이벤트 직렬화 결과에 본문 마커가 없음을 확인하는 테스트 ③소비자 쪽에서 본문이 비어 있음을 단언.\
   곁들인 조치: 항목 본문 상한 32KB → 4KB(원인은 거대 항목 1개가 아니라 평균 3KB × 1,587개였다 — 기존 32KB 상한은 절감 0.46%로 사실상 무효), emit마다 13MB를 복사하던 반환을 소유 → 차용으로 바꿔 복사 제거.\
   결과: payload −79%, RSS 5.22GB → 0.57GB(−89%), 공유 매핑 80개 → 4개(−99.3%) — payload 축소율보다 더 줄어든 건 **누적 자체**가 사라졌기 때문이다.
   > **deferred hydration** — 목록·스트림에는 가벼운 메타만 두고, 무거운 본문은 필요한 순간에 따로 채워 넣는 방식.

4. **증분 전송을 선택하지 않은 이유.**\
   증분은 수신 측이 "이전 상태 + 변경분"을 병합해야 하고, 병합을 한 번 빠뜨리면 에러 없이 **화면이 조용히 낡는다**.\
   그래서 증분을 도입하려면 **전량 재동기화 폴백**(어긋남을 감지하면 전체 상태로 복구)이 먼저 있어야 한다 — 이 사건에선 2단계로 보류했다.\
   (같은 사건에서 emit 디바운스도 시도했지만 순서 엣지 케이스를 반복 생성해 되돌렸다.)

5. **인코딩 팽창과 수신 측 필터.**\
   JSON에는 바이너리 타입이 없어 바이트 배열이 `[27,91,48,...]` 같은 **숫자 텍스트 나열**이 된다 → 3~4배. base64는 약 1.33배다(인코딩/디코딩이 256개 값 전부에서 동치임을 전수 확인).\
   전역 이벤트 하나를 모든 패널이 구독하고 각자 "내 세션인가"를 거르면, 패널 K개가 **모두 전체 payload를 역직렬화**한다 → 비용 × K.\
   교정은 **세션별 이벤트 이름**(`output-{id}`)으로 보내는 쪽에서 나누는 것 — 프레임워크가 리스너가 있는 웹뷰에만 디스패치함을 확인했다. 디코딩 실패는 예외로 방어하고, 재부착 실패 경로에 필요한 세션 필터 한 곳은 유지했다.

6. **took과 왕복의 차이.**\
   `took`은 검색 엔진이 요청을 처리한 시간이다(응답 직렬화·네트워크 전송·클라이언트 쪽 대기와 파싱은 포함하지 않는다). 왕복 33초 − 0.355초는 그 바깥 구간 — 주로 **응답 직렬화 + 전송 + 클라이언트 역직렬화**(와 클라이언트 쪽 대기) — 의 비용이며, 원인은 반환 필드 필터 없이 대형 중첩 문서 200건을 통째로 받은 10.6MB 응답이었다.\
   구간을 가르려면 호출 전후 시각(클라이언트 측)과 엔진의 `took`을 **한 로그 줄에 함께** 남긴다.\
   응답 크기는 hit 수 × 반환 필드 크기이므로, 화면에 필요한 필드만 화이트리스트(`_source.includes`)로 받으면 hit 수를 줄이지 않고 크기 항을 줄인다 → 1.67MB(약 6.4배 감소). (한 변형은 빈 목록을 반환해 사실상 필터가 없었다 — "빈 화이트리스트 = 전부"에 주의.)

7. **각 사례에서 줄인 항.**\
   스트림 payload — 빈도는 유지, **크기**(완료 본문 제거·상한·복사 제거).\
   IPC 인코딩 — **크기**(숫자 배열 → base64).\
   전역 이벤트 — 사실상 **빈도(수신 횟수)**: 한 번의 emit이 K번 파싱되던 것을 해당 구독자 1번으로.\
   검색 응답 — **크기**(필드 화이트리스트).\
   공통 원리: 받는 쪽이 지금 쓰지 않는 바이트는 보내지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 바뀌지 않는 대형 본문을 매 틱 전량 재전송
① 문제 코드
```rust
loop {                                                  // 150ms 폴
    let fp = fingerprint(&state);                       // 스트리밍 중엔 매 틱 바뀜
    if fp != last_fp {
        let snapshot = state.clone();                   // 전체 딥클론
        let frames = snapshot.ordered_frames();         // 완료 항목 본문까지 매번 복사 (소유 Vec)
        app.emit("timeline", &frames);                  // JSON 문자열로 통째 전달 (~24MB)
        last_fp = fp;
    }
    sleep(POLL);
}
```
② 고친 코드
```rust
struct DoneMeta { id: Id, parent: Id, total: usize, completed: bool, sig: FileSig }   // 본문 필드 없음

fn frames<'a>(state: &'a State) -> Vec<Frame<'a>> {     // 소유 → 차용: emit당 복사 제거
    state.frames.iter().map(|f| match f.done {
        true  => Frame::Done(f.meta()),                 // 완료 = 메타만
        false => Frame::Live(cap_content(&f.items, 4 * 1024)),   // 진행 중 = 항목당 4KB 상한
    }).collect()
}

#[command]
fn get_items(id: Id) -> Vec<Item> { read_from_disk(id) }   // 펼칠 때만 회수 (정본 = 디스크)

#[test]
fn no_body_leaks() { for ev in all_events() { assert!(!serialize(&ev).contains(BODY_MARKER)); } }
```
무엇이 깨졌나: 1회 크기가 "적당"하다는 전제 위에 고빈도 전량 재전송을 얹어, 크기 × 빈도가 off-heap 누적률이 됐다.\
같은 구조: 원격 데몬이 같은 표면(자랄 때마다 통째 재전송되는 응답 목록)을 네트워크 너머로 재생산할 위험 → 원격 메타 타입에도 본문 필드를 두지 않고 기존 조회 명령에 "하위 항목 요청"을 추가, 자라는 응답은 값 게이팅 + (길이, 해시) 지문만 보관, 사라진 세션 payload는 연속 두 번 폴링에서 실종일 때 정리.

### 변형 B — 바이너리의 JSON 숫자 배열 직렬화 + 수신 측 필터
① 문제 코드
```rust
#[derive(Serialize)]
struct Output { session_id: Id, data: Vec<u8> }         // JSON → [27,91,48,...] 3~4배
app.emit("output", Output { session_id, data });        // 전역 이벤트 1개
```
```ts
listen("output", (e) => { if (e.payload.session_id !== myId) return; /* ... */ });  // 패널 K개가 모두 파싱
```
② 고친 코드
```rust
app.emit(&format!("output-{id}"), B64.encode(&bytes));   // ~1.33배, 세션별 이벤트
```
```ts
listen(`output-${myId}`, (e) => {
    let bytes: Uint8Array;
    try { bytes = Uint8Array.from(atob(e.payload), c => c.charCodeAt(0)); }
    catch { return; }                                    // 디코딩 실패 방어
    // ...
});
```
무엇이 깨졌나: 텍스트 포맷의 바이너리 팽창과, 보내는 쪽에서 할 필터를 모든 수신자에게 떠넘긴 곱셈.

### 변형 C — 검색 응답을 반환 필드 필터 없이 통째로 수신
① 문제 코드
```python
def build_body(self, query):
    body = {"query": query, "size": 200}
    includes = self.get_source_includes()                # 어떤 변형은 [] → 사실상 필터 없음
    if includes:
        body["_source"] = {"includes": includes}
    return body                                          # 대형 중첩 문서 200건 → 10.6MB
```
② 고친 코드
```python
INCLUDE_FIELDS = ["id", "title", "status", "nested.name", ...]   # 화면이 쓰는 필드만

class DetailBuilder(BaseBuilder):
    def get_source_includes(self):
        return INCLUDE_FIELDS                            # 통짜 중첩 필드는 dotted path로 좁힘

t0 = perf_counter()
resp = await client.search(body=self.build_body(q))
log.info("search elapsed=%dms took=%dms hits=%d",       # 구간 분리: 왕복 vs 엔진
         (perf_counter() - t0) * 1000, resp["took"], len(resp["hits"]["hits"]))
```
무엇이 깨졌나: 서버 처리시간만 보고, 전송·역직렬화 비용을 지배하는 응답 크기를 통제하지 않았다.\
부수 발견: 핫패스에서 매 호출 INFO 레벨로 상위 결과를 순회하는 디버그 로깅이 부하의 일부일 가능성 → DEBUG 가드 또는 제거를 권장(기록상 미적용).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
