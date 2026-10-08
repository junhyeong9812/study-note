# ai-engineering/25-ai-symptom-index — 정답

## 정답

### 1. 200인데 실패인 경우

- 200은 응답 헤더를 보내는 시점의 "요청 성공"(RFC 9110 15.3.1)이다. 스트리밍 응답은 200 뒤에 진행되므로, 스트림이 끝까지 왔는지·출력이 쓸 만한지는 200이 말해 주지 않는다.
- 출력 한도에 닿아 잘림 → **중단 사유** 필드가 한도 계열(제공자마다 필드부터 다르다 — Anthropic `stop_reason: max_tokens`, OpenAI Chat `finish_reason: length`, OpenAI Responses `status: incomplete` + `incomplete_details.reason: max_output_tokens`) — [11-2](../11-llm-api-client-contract/2-summary.md) · [14-2](../14-structured-output-and-tool-calling/2-summary.md).
- 스트림 도중 오류 → 스트림 안 **`error` 이벤트**, 또는 **종료 이벤트를 받지 못함** — [11-1](../11-llm-api-client-contract/2-summary.md).
- 거부 → 중단 사유·거부 필드 — [14-3](../14-structured-output-and-tool-calling/2-summary.md).
- 그 밖에 응답 모델이 요청 모델과 다름(폴백 — [13-1](../13-model-routing-and-fallback/2-summary.md)), 자연 종료인데 스키마 위반([14-1](../14-structured-output-and-tool-calling/2-summary.md))도 200 안에 있다.

### 2. `Triage.java`의 두 집계

- 상태 코드만: `{성공=7, 실패(400)=1, 실패(429)=3}`.
- 필드 순서 규칙: "성공" 7줄 가운데 "계약상 성공"으로 분류된 줄은 r01 **1줄**이다. 응답 계약을 어긴 줄은 **4줄**이다 — 스트림 error 이벤트(r02), 잘림(r03), 거부(r04), 종료 이벤트 없음(r05). 나머지 2줄은 응답 자체는 계약을 지켰지만 다른 leaf로 갈 후보다 — 폴백 응답(r09), 캐시 쓰기만(r10). r10은 캐시 효율 지표로 따로 볼 문제이고, 한 줄만으로는 약한 증거다(첫 요청은 원래 쓰기만 한다).
- 429 세 줄
  - r06: retry-after 20s, 시도 1회 → 기다렸다 재시도([11](../11-llm-api-client-contract/2-summary.md) §5).
  - r07: 같은 요청 시도 6회 → 재시도가 한도를 채움([11-4](../11-llm-api-client-contract/2-summary.md) · [13-2](../13-model-routing-and-fallback/2-summary.md)).
  - r08: 지출 한도 code(`enforced_spend_limit_reached`, retry-after 없음) → 기다려도 안 풀림, 재시도 중지·경보([11-5](../11-llm-api-client-contract/2-summary.md)). 시도도 3회였지만 규칙 순서상 code 규칙이 먼저 걸렸다. 겹친 경우에는 둘 다 확인한다. retry-after가 없다는 것만으로는 한도 소진이라 정하지 않는다 — 일시 한도 429도 헤더 없이 올 수 있다.

### 3. 같은 토큰, 다른 비용

- (6): 2026-10-07 입력 총량 1,800,000, 비용 2.45 · 2026-10-08 입력 총량 1,792,000, 비용 4.10(예시 단가).
- (3): 프롬프트 v1의 캐시 읽기 비율 0.833, v2는 0.000이고 쓰기만 있는 호출이 728건이다.
- 설명: 사고 날에는 chat 기능의 입력이 "싸게 읽던 캐시"에서 "비싸게 쓰는 캐시"로 바뀌었다. 계산하면 10-08 = 입력 336,000 × 1.0 + 캐시 쓰기 1,456,000 × 1.25 + 출력 388,000 × 5.0 = 4,096,000 → 4.10이다. 10-07에는 같은 자리에 캐시 읽기 1,500,000 × 0.1이 있었다.
- 그래서 비용 급증은 토큰을 **종류별로** 나눠야 보인다. 원인 후보는 접두 앞의 가변값·최소 길이 미달·TTL 만료다([12-1](../12-prompt-and-semantic-caching/2-summary.md) · [12-5](../12-prompt-and-semantic-caching/2-summary.md)).

### 4. 429가 끝나지 않을 때

- 먼저 가를 두 가지
  - **기다리면 풀리는가**: 오류 type·code와 `retry-after` 유무. code가 쿼터·지출 계열이면 재시도를 멈추고 경보한다([11-5](../11-llm-api-client-contract/2-summary.md), 벤더별 동작). 일시 한도인데 `retry-after`만 없으면 횟수·총 시간을 제한한 백오프+지터로 재시도한다(OpenAI "Rate limits").
  - **재시도가 한도를 채우는가**: 429를 겪은 요청의 시도 수, 재시도 간격, 층별(SDK·앱·게이트웨이) 재시도 설정([11-4](../11-llm-api-client-contract/2-summary.md) · [13-2](../13-model-routing-and-fallback/2-summary.md)).
- 요청 단위로 세는 이유: 0-2 SQL (2)에서 하루 평균 요청당 호출 수는 1.120이었지만, 429를 겪은 요청만 보면 5.00이었다. 평균은 정상 요청이 증폭을 희석한다.
- 그 밖의 갈래: 언어별 토큰 비율(한국어에서 글자 수 어림 — [04-1](../04-tokenization-and-token-cost/2-summary.md)), 특정 계정의 폭주([22-4](../22-prompt-injection-and-llm-security/2-summary.md)), 에이전트 루프([20-1](../20-agent-loop-and-tool-safety/2-summary.md)).

### 5. 멈칫과 첫 토큰 지연

- 첫 토큰이 늦다 → **TTFT**(보냄 → 첫 청크)를 클라이언트·서버 두 위치로 본다. 첫 청크가 메타데이터 이벤트(Anthropic `message_start`)일 수 있으니 첫 출력 토큰 시각은 따로 남긴다([10](../10-inference-latency-metrics/2-summary.md)). 차이가 크면 네트워크·게이트웨이([10-2](../10-inference-latency-metrics/2-summary.md)). 프롬프트 길이에 따라 가파르게 늘면 프리필([06-2](../06-transformer-and-attention/2-summary.md)). 부하 때만이면 대기열·선점([09-4](../09-inference-serving-and-batching/2-summary.md)). 배포 직후 첫 요청만이면 스키마 문법 컴파일([14-4](../14-structured-output-and-tool-calling/2-summary.md)).
- 스트림이 멈칫한다 → **청크 간격의 p99와 요청별 최대 간격**을 본다. 여러 스트림이 같은 순간 멈추면 다른 요청의 긴 프리필이 디코드를 막는 경우([09-3](../09-inference-serving-and-batching/2-summary.md)).
- 평균 TPOT가 놓치는 이유: TPOT는 요청마다 평균 하나라, 한 번의 긴 간격이 그 요청의 수십 토큰에 나눠진다([10-1](../10-inference-latency-metrics/2-summary.md)). 이벤트 간격(ITL)과 토큰 간격(TPOT)을 같은 이름으로 그려도 비교가 틀린다([10-3](../10-inference-latency-metrics/2-summary.md)).

### 6. 임베딩 모델 점진 교체

- 1차 확인
  - 벡터 행의 모델별 개수(`SELECT model, count(*) … GROUP BY model`)와, 질의를 임베딩한 모델이 검색 필터의 모델과 같은지.
  - 고정 질의셋의 recall@10을 배포 전후로.
- 원인: 질의는 새 모델, 문서 일부는 옛 모델의 벡터다. 같은 차원이라 저장·계산은 되지만 서로 다른 공간이라 값이 무의미하다([05-1](../05-embeddings-and-similarity/2-summary.md) · [18-2](../18-index-freshness-and-reembedding/2-summary.md)).
- 차원이 다를 때와의 차이: 차원이 다르면 삽입·검색에서 **오류가 난다**(검색 API 500 — [18-5](../18-index-freshness-and-reembedding/2-summary.md)). 크게 실패하므로 오히려 빨리 드러난다. 같은 차원의 혼합은 **조용히** 품질만 떨어진다.
- 대처: 이중 색인을 다 채운 뒤 한 번에 전환하고, 모델 버전 열로 질의와 같은 모델의 벡터만 거른다([18](../18-index-freshness-and-reembedding/2-summary.md) 「이중 색인 후 전환」).

### 7. 교체인가, 흔들림인가

- 가르는 질문: **우리 쪽에서 바뀐 것이 있나**(모델·임베딩·베이스·폴백 경로·프롬프트 버전). 같은 커밋·같은 평가셋을 다시 돌려도 점수가 다르면 8절, 특정 변경 시점부터 수준이 옮겨 갔으면 7절이다. 우리 변경이 없는데 특정 날짜부터 옮겨 갔으면 제공자 쪽 변화도 후보다([07-5](../07-decoding-and-nondeterminism/2-summary.md) · [26](../26-ai-incidents/2-summary.md) 사건 2).
- 8절의 원인 후보와 1차 확인
  - 비결정 출력 + 문항당 1회 채점 → 문항당 실행 횟수 K, 같은 조건 재실행의 표준편차([19-4](../19-llm-evaluation/2-summary.md)).
  - 표본 잡음을 차이로 읽음 → n·SE·짝 차이의 구간([19-1](../19-llm-evaluation/2-summary.md)).
  - 판정자 위치 편향 → 순서 교환 2회 판정의 일관률([19-2](../19-llm-evaluation/2-summary.md)).
  - (그 밖) 평가셋 과적합 → 보류셋 점수([19-3](../19-llm-evaluation/2-summary.md)), 군집 문항 → 군집 SE([19-5](../19-llm-evaluation/2-summary.md)).

### 8. 문서 속 지시를 따른 메일 발송

- 1차 확인: 그 턴의 문맥에 들어간 **불신 출처 목록**(검색 문서·메일·웹·도구 결과)과, 도구 인자(수신자) 값이 어디서 왔는지([22](../22-prompt-injection-and-llm-security/2-summary.md) 「적용 — 3. 진단」).
- 프롬프트만 고치면 안 되는 이유: 지시와 데이터가 한 채널(토큰 열)로 들어가서, 프롬프트 방어는 따를 확률을 낮출 뿐이다. 보장은 모델 밖 결정적 코드에서 나온다 — 도구 허용 목록, 인자 출처·수신자 허용 목록, 고위험 행동 사람 확인([22-1](../22-prompt-injection-and-llm-security/2-summary.md)). 사례는 [26](../26-ai-incidents/2-summary.md) 사건 3.
- 같은 절의 다른 증상
  - 캐시 키: 다른 고객사의 답이 나옴 → 의미 캐시 파티션 키에 테넌트가 없음([12-3](../12-prompt-and-semantic-caching/2-summary.md)).
  - 도구 인자 검증: 다른 고객의 주문이 취소됨, 인자는 스키마상 완벽 → 도구 구현 안에서 소유권을 확인하지 않음([14-5](../14-structured-output-and-tool-calling/2-summary.md)).

### 9. "일부 사용자만"을 재현하지 못함

- 답하지 못하는 질문: 적용 1의 **②(누구에게?)** — 응답 모델·라우팅 경로로 나눠 보는 것.
- 없는 필드: 0-1절 ②의 **요청 모델 · 응답 모델 · 프롬프트 버전**, 그리고 라우팅 이유·폴백 여부·시도 번호. 이것들이 없으면 경로별로 품질 지표를 나눌 수 없어 "일부 사용자"가 무작위 잡음처럼 보인다([13-3](../13-model-routing-and-fallback/2-summary.md) · [23](../23-llm-observability-and-cost/2-summary.md)).
- sticky 라우팅이면 문제가 일부 사용자에게 몰린다. [26](../26-ai-incidents/2-summary.md) 사건 2의 실험이 그 모양을 보인다.
