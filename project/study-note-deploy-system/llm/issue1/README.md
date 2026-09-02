# issue1 — Ollama 래핑 서버: /rewrite·/health (문지기 + 검증)

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/4

## 1. 배경 (요구사항)

study-note 검색 시스템에서 로컬 LLM(qwen3:8b)이 맡는 일은 "답 생성"이 아니라
**검색어를 다듬는 작업**다. 문제는 Ollama(모델을 GPU에 올려 HTTP로 서빙해주는 프로그램)를
그대로 backend에 노출하면:

- 프롬프트(모델에게 주는 지시문)가 backend 코드 여기저기에 흩어진다.
- backend가 아무 모델이나 골라 부를 수 있어, 모델 교체가 "전 서버 수정"이 된다.
- GPU는 1장인데 요청이 몰리면 전부 느려지다 같이 죽는다.

그래서 Ollama 앞에 얇은 서버를 하나 세워 **프롬프트·모델·수용량 제어를 한 곳이 소유**하게 한다.

## 2. 검토한 방식들

### 선택 — FastAPI 얇은 래핑 + Ollama (compose로 한 쌍)

- 이 서버의 핵심 임무는 "모델 출력이 약속한 JSON 모양인지 검증"인데,
  FastAPI의 pydantic(파이썬 데이터 검증 라이브러리)은 모델 정의가 곧 검증기이자
  Ollama에게 보낼 JSON 스키마가 된다 — 한 라이브러리로 세 가지를 해결.
- 동시성이 설계상 2로 고정이라(GPU 1장) 무거운 프레임워크가 필요 없다.

### 대안 — backend가 Ollama를 직접 호출 (탈락)

```
backend ──프롬프트 조립──▶ ollama :11434
```
- 프롬프트 소유권이 backend로 넘어간다. 프롬프트 한 줄 고치는데 backend 배포.
- 검색 오케스트레이션(ES·임베딩·LLM)과 모델 제어가 한 코드에 섞인다. → 탈락.

### 대안 — vLLM (탈락)

- 동시 처리량은 압도적이지만 사용자 1명 시스템엔 과잉. 8GB GPU에선 4bit 양자화가
  강제라 품질 이점도 없음. 모델을 GPU에 상주 선점(유휴 언로드 없음). → 탈락.
  단, 나중에 LoRA(모델 부분 튜닝) 서빙이 필요해지면 그때 런타임만 교체한다 —
  이 교체가 가능하도록 backend에는 HTTP 계약만 노출한 게 이 구조의 실익.

### 대안 — 래퍼가 자체 대기열(큐) 운영 (탈락)

```
요청 ──▶ [래퍼의 큐에 줄세움] ──▶ ollama
```
- Ollama가 이미 내부 큐로 직렬화한다. 같은 일을 두 겹으로 하는 셈이고,
  줄이 길어지면 사용자 검색이 LLM에 인질로 잡힌다. → "넘치면 즉시 거절"로.

## 3. 구현 워크플로우

```
                    [토폴로지 — LAN에 열리는 건 :8000 하나]
backend ──HTTP──▶ wrapper :8000
                     │ compose 내부 네트워크 (호스트 비노출)
                     ▼
                  ollama :11434  (GPU, OLLAMA_NUM_PARALLEL=1)
   · Ollama 포트를 호스트에 안 여는 이유: backend가 프롬프트를 우회해
     직접 치는 경로를 구조적으로 차단
   · 모델은 env MODEL로 고정 — 요청이 모델을 지정할 수 없다

                    [/rewrite 한 건의 흐름]
요청 {request_id, query}
  ▼
api.py (라우터 — HTTP만 담당)
  ▼
usecase/rewrite.py
  ├─① 문지기: 세마포어(동시 2명 카운터)가 다 찼나?
  │        └─ 찼으면 대기 없이 즉시 503 {"code":"busy"} — 7.7ms 실측
  ├─② 총예산 5초 타이머 시작 (재시도 포함 전체가 5초 안)
  ├─③ domain/prompt.py 가 프롬프트 조립 → ollama /api/chat 호출
  │        (format=JSON스키마: 모델이 스키마 밖 출력을 못 하게 강제 — 1단 방어)
  ├─④ validate.py: pydantic 파싱 (2단 방어)
  │        └─ 실패 시 "네 출력이 이렇게 틀렸다"를 붙여 딱 1회 재요청 (3단 방어)
  │             └─ 또 실패 → 422 {"code":"schema_violation"}
  ▼
성공 → 구조화된 검색 재료 반환
```

**/rewrite가 하는 일 (쉽게):** 사용자가 친 검색어("낙관적 락이랑 비관적 락 차이")를
받아서, 검색엔진(ES)이 잘 찾도록 **검색 준비물**로 바꿔준다 — 핵심 단어 목록,
영어↔한국어 대응어("optimistic locking"), 어느 주제 폴더(db-engine-lab)·어느 문서
종류를 뒤질지. **답을 만드는 게 아니다.** 답을 찾는 건 검색엔진, 최종 합성은 상위 모델의 몫.

**/digest (계약만 예약):** 검색이 찾아온 문서 조각들을 모델이 읽고 한국어로 요약해주는
API. 지금은 만들지 않지만 **입출력 모양(계약)을 미리 못기록해 둔다** — 나중에 구현할 때
backend 코드를 안 고치게 하려고. 그래서 호출하면 501("아직 없음")을 준다.

**/health:** Ollama에 닿는지 + 모델이 실제로 설치돼 있는지 확인. 모델이 없으면
503을 줘서 배포 시스템이 "정상인 척"하지 못하게 한다.

## 4. 코드 변경 (diff와 맥락)

문지기 — 줄 세우지 않고 즉시 거절 (`usecase/rewrite.py`):

```python
if sem.locked():          # 자리 있나만 보고 (기다리지 않음)
    raise Busy()          # → api 계층이 503 + Retry-After: 2 로 번역
async with sem:           # 입장. 예외가 나도 자동 퇴장(자리 반납)
```

총예산 타임아웃 — 리뷰에서 잡힌 결함의 수정:

```diff
- raw = await _chat(..., timeout)          # 호출마다 5초 → 재시도하면 최대 10초
+ async with asyncio.timeout(timeout):     # 요청 전체가 5초 안 (재시도 포함)
+     raw = await _chat(...)
```

## 5. 구현 중 마주친 문제

### 문제 1 — 설계 문서와 코드의 응답 모양이 달랐다 (리뷰 high)

- **원인**: 설계는 `filters{topic, doc_kind}`인데 구현하며 무심코 `topics[]`로 바꿈.
  테스트도 틀린 모양을 고정해버려 회귀 검출 불가.
- **수정**: 설계대로 되돌리고, 계약 밖 필드는 아예 거부(pydantic `extra="forbid"`).
- **배경**: 문서와 코드가 다른 이름을 말하면 backend는 어느 쪽을 믿어야 할지 모른다.
  "설계 문서가 계약의 정본"을 지키는 게 핵심. -> llm을 활용한 리뷰로 해당 부분을 발견

### 문제 2 — 모델이 없어도 "health"으로 보였다

- **원인**: 모델 미설치 때 `/health`가 몸통엔 "model_missing"이라 쓰면서 상태코드는
  200을 줬다. docker healthcheck는 상태코드만 보므로 healthy로 판정.
- **수정**: 모델 부재·응답 이상은 503.
- **배경**: "에러 없이 돌았다 ≠ 정상"의 전형. 실제로 `ollama pull`을 깜빡한 상태가
  정확히 이 시나리오였고, .164 스모크에서 503이 뜨는 걸 확인했다.

### 문제 3 — qwen3 thinking 폭주 → 전 요청 타임아웃 (실기동에서만 발견)

**증상**: 모델 pull 완료·GPU 로드 확인 후에도 /rewrite가 매번 **정확히 5초**에서 죽음:

```
$ time curl -X POST .../rewrite -d '{"request_id":"smoke-2","query":"낙관적 락이랑 비관적 락 차이"}'
{"error":"upstream_timeout"}
real    0m5.006s        ← 총예산 5s가 정확히 발동 (계약은 동작, 추론이 문제)
```

**진단**: ① `ollama ps` — 모델은 100% GPU 로드 정상. ② 같은 요청을 Ollama에 **직접**
쳐봄 → 8분 넘게 안 끝남. ③ GPU와 Ollama 서버 로그:

```
$ nvidia-smi ...
98 %, 5470 MiB, 8192 MiB                        ← GPU는 풀가동 중

$ docker logs llm-ollama | tail
slot print_timing: id 0 | task 834 | n_gen = 31325, tg = 63.94 t/s
slot   operator(): id 0 | task 834 | slot context shift, n_keep = 4, n_left = 4091, n_discard = 2045
```

초당 64토큰으로 **멀쩡히** 생성 중인데 이미 **31,000+ 토큰** — 답이 안 끝나는 게 아니라
**끝낼 생각이 없는** 상태다(4096 컨텍스트를 넘겨 context shift까지 발생). 프롬프트에 넣은
`/no_think`(Qwen 문법의 생각-끄기 스위치)를 Ollama의 qwen3 챗 템플릿이 특별 취급하지
않고 일반 텍스트로 넘긴 것 — thinking이 켜진 채 JSON 스키마 강제(format)와 얽혀 종결
조건에 도달하지 못했다. 그리고 wrapper가 5초에 연결을 끊어도 **Ollama는 서버쪽 생성을
계속했다**(task 834가 계속 돎) — 그래서 후속 요청까지 GPU를 못 잡고 연쇄 타임아웃.

**수정** (usecase/rewrite.py):

```diff
             "stream": False,
+            "think": False,            # 근본 원인 제거 — ollama의 공식 생각-끄기는 API 필드
             "format": schema,
-            "options": {"temperature": 0},
+            "options": {"temperature": 0, "num_predict": 512},
+                                       # 폭주 가드레일 — 클라이언트 절단이 서버를 못 지키므로
```
프롬프트의 `/no_think` 문자열은 삭제(효과 없는 주술).

**결과**: 콜드 3.56s → 웜 **1.33s**, 출력 정상.

**배경**: ① 모델 카드의 프롬프트 문법이 서빙 런타임에서도 통한다고 가정하지 말 것 —
모델 제어는 그 런타임의 공식 API로. ② **클라이언트 타임아웃은 서버 자원을 보호하지
않는다** — 서버측 생성 상한(num_predict)이 유일한 방어선(31k 토큰이 그 증거).
③ 이건 mock 테스트로는 절대 못 잡는 유형 — 실기동 스모크를 머지 조건에 넣은 게 유효했다.

## 6. 결론

Ollama 앞에 "프롬프트를 소유하는 게이트웨이"를 세웠다. 동시 2건 초과는 7.7ms 만에
거절하고, 모델 출력은 3단(스키마 강제→검증→피드백 재시도 1회)으로 방어하며,
요청 전체가 5초 예산을 넘지 않는다. 수치들(세마포어 2, 5초, 재시도 1회)은
전부 "일단 이 값, 로그로 실측 후 조정" 항목으로 등재해 뒀다.
PR: #4 (테스트 12건 + 실기동 스모크)
