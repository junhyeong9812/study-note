# ai-engineering/23-llm-observability-and-cost — 정답

## 정답

### 1. 새로 챙길 것

- 비용이 토큰 종류(일반 입력·캐시 읽기·캐시 쓰기·출력)마다 다른 단가로 매겨진다. 제공자마다 usage 필드의 의미도 다르다.
- 입력·출력 원문이 개인정보·비밀을 담은 큰 데이터다.
- 관측 규약(OpenTelemetry GenAI semantic conventions)이 Development 상태라 이름·의미가 바뀐다.

### 2. 제공자별 input_tokens

- Anthropic: `input_tokens` = 200(마지막 캐시 지점 뒤 토큰만), `cache_read_input_tokens` = 9,000. 총 입력 = 읽기 + 쓰기 + `input_tokens`("Prompt caching").
- OpenAI Responses: `input_tokens` = 9,200(캐시 포함), `input_tokens_details.cached_tokens` = 9,000. 문서의 비용 예제가 `input_tokens − cached_tokens − cache_write_tokens`로 일반 입력을 구한다.
- OTel: `gen_ai.usage.input_tokens` = **9,200**(캐시 포함, SHOULD). Anthropic 세부 규약은 `input_tokens`에 캐시 읽기·쓰기를 더해 이 값을 만들라고 한다(MUST).

### 3. 비용

- 일반 200×3 + 캐시 9,000×(3×0.1) + 출력 400×15 = 600 + 2,700 + 6,000 = 9,300 → ÷100만 = **$0.009300**(실험 A, `LlmCost.java`도 같음).
- OpenAI 쪽에 캐시 토큰을 또 더하면 입력 18,200·일반 9,200이 되어 $0.036300, 약 **3.9배**. 캐시 할인을 아예 모르면 $0.033600(3.6배).
- 반대로 Anthropic `input_tokens` 200을 총량으로 착각하면 일반 입력 −8,800, 비용 −$0.017700(음수). 음수 검사로 바로 잡힌다.

### 4. 비용 입력 vs ITPM 입력

- 다르다. Anthropic "Rate limits": 대부분 모델에서 캐시 읽기 토큰은 ITPM에 들어가지 않는다(`input_tokens` + `cache_creation_input_tokens`만 셈 — 캐시 인지 ITPM). 일부 모델(문서의 각주 표시 모델)은 캐시 읽기도 센다.
- 비용은 캐시 읽기 토큰에도 (낮은 단가로) 매겨진다. 그래서 한도 대시보드와 비용 대시보드의 "입력 토큰"을 같은 숫자로 기대하면 안 된다.

### 5. 태그

- 기능·테넌트·모델·프롬프트 버전 태그를 남겼어야 한다. 실험 C에서 기능 태그로 나누자 agent 기능이 $3.58 → $14.89로 증가분 대부분이었다(summary는 +$0.29, search는 그대로).
- 지표(카운터)에는 낮은 카디널리티 태그(기능·모델·테넌트 등급)만, 높은 카디널리티(사용자 ID·요청 ID)는 스팬·로그에. 요청 진입점의 기능·테넌트를 컨텍스트로 LLM 스팬까지 전파한다([reliability/17](../../reliability/17-distributed-tracing/2-summary.md)).

### 6. 이름 변경과 침묵한 경보

- 옛 이름의 시계열이 0이 아니라 **데이터 없음**이 됐다. 임계값 경보는 표본이 있어야 평가되므로 울리지 않는다. absent(데이터 없음) 경보만 울린다(실험 D).
- 실제 변경: `semantic-conventions` v1.37.0의 `gen_ai.client.token.usage`(히스토그램 + `gen_ai.token.type`) → `semantic-conventions-genai` main의 `gen_ai.client.inference.usage.*` 카운터(#374, 2026-09-22). 추론 지연은 `gen_ai.client.operation.duration` 대신 `gen_ai.client.inference.duration`(#521, 2026-10-06).
- 대처: 계측 라이브러리 버전 고정, 업그레이드 때 이름 diff, absent 경보, 핵심 비용 지표는 자체 이름으로도 기록.

### 7. 원문 기록

- 계측 라이브러리는 지시·입력·출력 원문을 기본으로 기록하지 않고(SHOULD NOT), 켜는 옵션을 준다(SHOULD). `gen_ai.input.messages` 등은 Opt-In 속성이고 개인정보 경고가 붙어 있다.
- 선택지: 기록 안 함(기본) / 스팬 속성에 기록(규제가 적용되지 않거나 저장소가 규제를 지키는 환경, 예: 운영 전) / 외부 저장소에 두고 스팬엔 참조(운영 환경 권장, 별도 접근 통제).
- 평소에는 길이·해시·버전만 남긴다(실험 B 스팬).

### 8. 10%만 잡힌 비용

- 비용을 트레이스 백엔드의 **샘플링된 스팬** 속성 합으로 계산했을 가능성. 트레이스를 10%만 남기면 합도 10% 근처가 된다.
- 비용은 샘플링하지 않는 카운터 지표로 집계한다. OTel 토큰 지표 문서도 사용량 카운터를 총량·비용 근사용으로, 작업별 히스토그램은 분위·이상치용으로 구분한다.

### 9. 끊긴 스트림의 finish_reasons

- 끝 이유를 기대했는데 받지 못한 경우(생성 실패·취소·끝 이벤트 전 스트림 종료) 그 자리에 `error`를 넣는다(SHOULD, "Client Inference" 각주).
- 쓸모: 잘리거나 끊긴 응답 비율을 지표로 셀 수 있다. 반쪽 응답을 성공으로 저장하는 버그([11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md))를 운영에서 감지하는 신호가 된다.
