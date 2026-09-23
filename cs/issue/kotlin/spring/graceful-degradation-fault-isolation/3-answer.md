# cs/issue/kotlin/spring/graceful-degradation-fault-isolation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. 파이프라인에서 핵심 기능(검색)은 반드시 응답해야 하는 것이고, llm 재작성·의미 검색은 **결과를 더 좋게 만드는 보조**다. 이걸 불변식으로 못 박는 이유는, 아무 방어 없이 단계를 이으면 보조 단계의 예외가 그대로 위로 전파돼 검색 전체가 503으로 죽기 때문이다 — 즉 "질을 높이려던 부품"이 "가용성을 인질로 잡는다". "인질로 잡는다"는 곧 **부품 A(선택적)의 고장이 부품 B(필수)의 가용성을 결정**하는 잘못된 의존 방향이다. 불변식은 이 방향을 금지한다: 보조는 있으면 보태고 없으면 빠질 뿐, 핵심을 끌어내리지 못한다.
   > **불변식(invariant)** — 시스템이 어떤 상황에서도 항상 참으로 유지해야 하는 성질. 여기선 "보조가 죽어도 검색은 응답한다".

2. **결함 격리**는 장애의 전파를 막는 벽이다 — 한 부품의 실패가 경계를 넘어 다른 부품·전체로 번지지 않게 한다(여기선 kNN 호출을 try/catch로 감싸 임베딩 예외를 검색 스레드 안에 가둠). **우아한 성능 저하**는 부품이 빠진 뒤의 거동이다 — 전체가 죽는 대신 축소된 형태로 계속 작동한다(BM25 단독으로 내려앉되 여전히 결과를 줌). 둘의 관계: 격리가 "번짐을 막아" 강등할 여지를 만들고, 강등이 "그 자리를 축소 동작으로 메운다". "llm 실패 → 원본 질의로 진행", "임베딩 실패 → BM25 단독"은 **각각 격리(예외 흡수) + 강등(축소 동작)의 결합**이다.
   > **결함 격리(fault isolation)** — 한 구성요소의 장애가 다른 구성요소로 번지지 않도록 경계를 두는 것.
   > **우아한 성능 저하(graceful degradation)** — 일부 기능이 불가능해져도 시스템 전체가 멈추지 않고 축소된 기능으로 계속 동작하는 것.

3. (a) 원점수 더하기는 스케일이 다른 두 점수(BM25 무한대 스케일 vs 코사인 0~1)를 섞어 **큰 쪽이 작은 쪽을 완전히 지배**한다 — kNN이 사실상 무시된다. (b) 각자 최대값 정규화는 **이상치 하나에 전체가 눌린다** — 어쩌다 BM25 100점짜리가 하나 나오면 나머지가 다 0.x로 깔린다. (c) RRF는 원점수를 버리고 등수만 써서(`새점수 = Σ 1/(k+rank)`, k=60) 스케일과 이상치 문제를 동시에 없앤다. **한쪽이 비어도 성립하는 이유**: 합은 각 랭킹이 기여하는 항의 덧셈인데, 비어 있는 랭킹은 단지 항이 0개일 뿐 수식이 깨지지 않는다. 폴백과 궁합이 좋은 이유가 이것 — "임베딩 죽으면 kNN 랭킹 = 빈 리스트"가 되어도 RRF는 BM25 랭킹만으로 그대로 병합한다. 별도 분기가 필요 없다.
   > **RRF(Reciprocal Rank Fusion, 역순위 융합)** — 여러 랭킹을 각 항목의 등수의 역수 합으로 합치는 방법. 점수 스케일을 안 봐 이질적 랭킹을 안정적으로 섞는다.

4. llm은 "뭐야"로 끝나는 질문형 질의를 보고 `kind=question`을 제안했다 — "question 문서를 찾는 거겠지"라는 추론인데, 사람 의도(질문에 대한 **답**을 찾는다)와 정반대다. 이걸 하드 필터로 적용하니 정리·정답·글 종류가 전부 걸러져 답 문서가 전멸했다. "약한 모델의 출력은 참고 자료지 결정권자가 아니다"란, 부정확할 수 있는 모델 출력에 **되돌릴 수 없는 결정권(하드 필터로 결과를 제거)** 을 주면 그 부정확성이 그대로 결과를 오염시킨다는 것이다. 그래서 제안을 **버리지 않되 로그로만 축적**한다 — 완전히 무시하면 "제안이 실제로 얼마나 맞나"를 측정할 재료가 사라지고, 곧바로 신뢰하면 결과가 오염된다. 로그 축적은 "결정권은 안 주되 데이터는 모은다"는 중간 지점이다.

5. 리뷰어 둘 다 "rewrite의 `kind` 제안을 파싱만 하고 안 쓴다(사문 필드)"를 지적했고, 그 지적은 **설계 문서(제안을 쓰기로 함)와 코드(안 씀) 사이의 불일치**로는 옳았다. 하지만 지적대로 제안을 쓰게 배선하자 실측에서 결과가 무너졌다 — 즉 **불일치는 해소됐지만, 원래 설계("모델 제안을 하드 필터로 쓴다")가 유해**했던 것이다. 리뷰는 "코드가 설계대로인가"는 판정하지만 "설계가 옳은가"는 실행해 봐야만 드러난다. 그래서 리뷰 지적을 반영한 코드도 재배포 스모크로 재검증했고, 거기서 설계 자체를 뒤집었다.

6. **호출자가 알아야 한다.** 응답에 `rewrite_on`·`dense_on`를 실어 "이번 결과가 완전한 하이브리드인지, 강등된 것인지"를 드러낸다. "조용히 강등"은 결과가 나빠졌는데도 신호가 없어 아무도 모르는 것 — 이는 곧 **silent failure**다(실패가 발생했으나 신호에 반영 안 됨). "시끄럽게 강등"은 강등을 응답 뱃지·warning 로그로 관측 가능하게 만들어, 호출자가 결과 품질을 판단하고 운영자가 임베딩 장애를 알아채게 한다. 가용성을 지키려 강등하되, 강등 사실 자체는 숨기지 않는 것이 핵심이다.
   > **상태 뱃지** — 응답에 실어 보내는 처리 상태 플래그(`*_on`). 강등·폴백이 일어났음을 호출자가 관측하게 해 조용한 실패를 막는다.

## 발생한 문제 / 해결 (추상 원리)

**문제:** ① 보조 기능(llm·임베딩)의 장애가 핵심 기능(검색)을 503으로 죽임(인질). ② 이질적 스케일의 두 랭킹을 합치는 안정적 방법 필요. ③ 부정확할 수 있는 모델 제안에 하드 결정권을 줘 결과 오염.

**해결:** ① 각 보조 경로를 try/catch로 감싸 예외를 흡수하고(격리) 축소 동작으로 강등(원본 질의·BM25 단독)하되 항상 200(성능 저하). ② RRF로 등수만 합쳐 스케일·이상치 문제 제거 — 한쪽이 비어도 성립해 폴백과 맞물림. ③ 하드 결정은 명시 입력만, 모델 제안은 로그로 축적(참고 자료화). ④ 강등은 응답 뱃지(`*_on`)로 노출 — 조용한 강등(silent failure) 금지. ⑤ 리뷰 반영 코드도 실측 재검증(설계 유해함은 실측만 잡음).

## 문제 구조 (추상화 코드)

### 변형 A — 보조 전처리(모델 질의 재작성) 장애를 흡수해 원본 질의로 강등
① 문제 코드
```kotlin
fun search(q: String): Response {
    val rewritten = rewriter.rewrite(q)            // 보조 서비스 장애·지연 → 예외 → 검색 전체 503
    // ...
}
```
② 고친 코드
```kotlin
class RewriteClient : RewritePort {
    private val http = client(connectTimeout = 2.s, readTimeout = 7.s)     // 타임아웃 명시
    override fun rewrite(id: String, q: String): Outcome = try {
        val r = http.post("/rewrite", body(id, q))
        if (r.success && r.data != null) Outcome(used = true, keywords = r.data.keywords /* ... */)
        else fallback(id, "success=false")
    } catch (e: Exception) { fallback(id, e.javaClass.simpleName) }    // 어떤 예외든 흡수
    private fun fallback(id: String, why: String) = Outcome(used = false).also { log.warn(id, "rewrite fallback: $why") }
}
val query = if (outcome.used) (listOf(q) + outcome.keywords).distinct().joinToString(" ") else q
```
무엇이 깨졌나: 선택적 개선 단계가 핵심 응답의 필수 단계처럼 호출돼, 그 장애가 핵심 응답의 장애가 됐다.

### 변형 B — 벡터 검색 장애 시 키워드 검색 단독으로 강등 + 등수 기반 병합
① 문제 코드
```kotlin
val lexical = keywordSearch(q)
val dense = vectorSearch(embed(q))                  // 임베딩·벡터 경로 장애 → 전체 실패
return merge(lexical, dense)                        // 점수 스케일이 달라 합산이 불안정
```
② 고친 코드
```kotlin
val lexical = keywordSearch(q)
val (dense, denseOn) = try { vectorSearch(q) to true }
                         catch (e: Exception) { log.warn("dense fallback"); emptyList<Hit>() to false }
val merged = rrfMerge(listOf(lexical, dense), size)                  // 한쪽이 비어도 성립
return Response(results = merged, rewriteOn = outcome.used, denseOn = denseOn)   // 강등을 응답에 노출

fun rrfMerge(rankings: List<List<Hit>>, size: Int, k: Int = 60) =
    rankings.flatMap { r -> r.mapIndexed { i, h -> "${h.docId}#${h.chunkNo}" to (h to 1.0 / (k + i + 1)) } }
        .groupBy({ it.first }, { it.second })
        .map { (_, xs) -> xs.first().first to xs.sumOf { it.second } }   // 같은 청크는 점수 합산
        .sortedByDescending { it.second }.take(size)
```
무엇이 깨졌나: 두 랭킹 중 하나의 장애가 병합 전체를 막았고, 강등 여부가 호출자에게 보이지 않을 수 있었다.

### 변형 C — 부정확할 수 있는 모델 제안에 하드 결정권을 주지 않음
① 문제 코드
```kotlin
val filterKinds = outcome.suggestedKind?.let { listOf(it) } ?: defaultKinds   // 제안이 하드 필터가 됨
// 실측: 모델이 답이 없는 문서 종류를 제안 → 답 문서가 전부 필터링돼 결과 0
```
② 고친 코드
```kotlin
val filterTopic = explicitTopic                                    // 하드 필터는 명시 입력만
val filterKinds = explicitKinds?.takeIf { it.isNotEmpty() } ?: defaultKinds
if (outcome.used && outcome.suggestedKind != null)
    log.info(id, "rewrite hint (미적용): kind=${outcome.suggestedKind}")   // 제안은 로그로만 축적
```
무엇이 깨졌나: 보조 경로가 "실패"가 아니라 "그럴듯한 틀린 값"을 낼 때도 핵심 결과를 오염시킬 수 있었다.

### 변형 D — 부가 기능(통계 적재)을 요청 경로에서 동기로 실행 (리뷰 권고)
① 문제 코드
```kotlin
class StatsInterceptor : HandlerInterceptor {
    override fun afterCompletion(/* ... */) {
        statsRepo.insertView(/* ... */)             // 요청마다 동기 DB 적재 2건
        statsRepo.insertDaily(/* ... */)            // 통계 DB 장애·지연이 본 응답으로 전파 (DoS 소지)
    }
}
```
② 고친 코드 (권고안)
```kotlin
override fun afterCompletion(/* ... */) {
    events.publish(ViewEvent(/* ... */))            // 비동기 이벤트 또는 버퍼 적재로 분리
}
@Async @EventListener
fun on(e: ViewEvent) = runCatching { statsRepo.insert(e) }.onFailure { log.warn("stats drop", it) }   // 수집 트랜잭션·예외 격리
```
무엇이 깨졌나: 부가 기능의 장애 도메인이 핵심 요청과 합쳐져 있었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "요청 경로 안에서 보조 호출을 try/catch로 감싸 흡수하고 축소 동작으로 강등하며, 강등을 응답에 노출한다"이다. 같은 원리(보조 기능의 장애가 핵심을 인질로 잡지 못하게)에 다른 방안이 쓰인 사례:

### 방안 1 — 쓰기 순서: 핵심 산출물을 느린 보조 작업보다 먼저 디스크에 확정
```rust
// 문제: 느린 보조 작업(모델로 제목 추출, 수 분)이 끝나야 첫 파일이 써짐 → 중단 시 전손
//       직전 정상 요약(last-good)이 메모리에만 → 보조 작업 중 크래시 시 영구 소실
// 고친:
let out = write_archive(&root, &src, FALLBACK_TITLE)?;       // 1) 핵심 산출물을 대체 제목으로 먼저 확정
persist_last_good(&out)?;                                    // 2) 직전 정상 요약도 첫 write 직후 디스크 선기록
match extract_title(&src) {                                  // 3) 느린 보조 작업
    Ok(t)  => write_archive(&root, &src, &t)?,               //    성공 → 멱등 재실행(폴더명 변경 겸함)
    Err(e) => { restore_last_good(&out)?; warn(e) }          //    실패 → 이전 요약 복원 + 경고
}
```
"부분 성공 허용"은 핵심 산출물이 실패 가능한 보조 작업보다 먼저 확정되는 **순서**일 때만 코드 구조로 성립한다.\
선택하지 않은 방법: 보조 작업 실패 시 기존 산출물 삭제 — 일시 장애를 데이터 손실로 만든다.

### 방안 2 — 선택 기능의 헬스 지표를 가용성 집계에서 분리
```yaml
# 문제: 메일 스타터가 SMTP 연결을 시도하는 헬스 지표를 자동 등록 → 메일 미설정이면 전체 health DOWN
#       → 오케스트레이터가 정상 앱을 비정상으로 판정
# 문제(같은 구조): 기본 health에 평소엔 접속하지 않는(마이그레이션 때만 lazy 접속) DB 지표 포함 → DOWN
management:
  health:
    mail.enabled: false          # 선택 기능은 집계에서 제외 — 진단은 별도 관리자 경로로 유지
    db.enabled: false            # 선택적 외부 의존 제외
# 컨테이너 프로브는 liveness 그룹(/actuator/health/liveness)을 사용
# (부수: 경량 런타임 이미지에 프로브 도구(curl)가 없어 판별 불가 → 도구 설치)
```

### 방안 3 — 네이티브 크래시는 프로세스 경계로 격리
```python
# 문제: 네이티브(C) 라이브러리가 손상 입력에서 세그폴트(원인은 추정으로 기록) → try/except로 못 잡고 프로세스 즉사
#       게다가 open만 감싸고 페이지 추출·날짜 루프엔 예외 처리 없음 → 한 건 실패가 전체 파이프라인 중단
for day in days:
    for f in files(day):
        doc = safe_open(f); text = doc.page(0).get_text()     # 세그폴트면 로그 없이 전체 종료
# 고친
with Pool(processes=1, maxtasksperchild=500) as pool:
    for day in days:
        try:
            for f in files(day):
                r = pool.apply_async(extract, (f,))
                try: text = r.get(timeout=30)                # 타임아웃 → 스킵
                except Exception as e: record_failed(f, e); continue   # 파이썬 예외 스킵, 워커 사망은 풀이 재생성
        except Exception as e: failed_days.append(day)
print_summary(failed_days)
# 결과(이미지 등)는 bytes로 반환해 메인에서 변환 — IPC 오버헤드는 감수
```

### 방안 4 — 서비스 관리자의 약한 의존으로 보조 유닛 실패 전파 차단
```ini
# 문제(리뷰 권고안): 보조 유닛이 가리키는 바이너리가 미설치 → 보조 유닛 실패 → 재부팅 시 컨테이너 런타임 전체 기동 실패 위험
[Unit]
Requires=gpu-helper.service
# 고친: 약한 의존 — 보조 유닛이 실패해도 대상 유닛은 뜬다
[Unit]
Wants=gpu-helper.service
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 요청 내 try/catch 흡수·강등 | 보조 호출이 예외로 실패를 알린다 | 흡수·폴백 코드, 강등 노출 필드 | 조용한 강등(노출 누락) · 크래시는 못 잡음 | 같은 프로세스의 원격 호출 |
| 1. 핵심 산출물 선확정 | 산출물이 디스크에 남는다 | 멱등 재기록 | 순서가 깨지면 부분 성공이 전손 | 느린 보조 작업이 있는 배치·저장 |
| 2. 헬스 집계에서 선택 기능 제외 | 오케스트레이터가 health로 생사를 판정 | 진단 경로 별도 유지 | 제외한 기능의 장애가 보이지 않음 | 선택 기능·lazy 의존이 있는 서비스 |
| 3. 서브프로세스 격리 | 실패가 예외가 아니라 프로세스 사망일 수 있다 | IPC 오버헤드 | 결과 직렬화 비용·타임아웃 튜닝 | 네이티브 라이브러리·손상 입력 |
| 4. 약한 의존(Wants) | 의존 유닛이 필수가 아니다 | 없음 | 필수 의존을 약하게 걸면 순서·전제가 깨짐 | 서비스 관리자 유닛 간 보조 의존 |

**결론**: 격리 경계는 **실패가 어떤 모양으로 오느냐**로 고른다.\
예외로 오면 호출 지점에서 흡수·강등하고(기본), 프로세스를 죽이는 실패면 프로세스 경계로(3), 보고 체계(헬스 집계·유닛 의존)를 타고 번지면 그 집계에서 끊는다(2·4).\
시간 축으로 번지는 실패(중단 시 전손)는 격리가 아니라 **확정 순서**로 막는다(1). 어느 방안이든 강등은 응답·로그·요약으로 드러내야 한다.
