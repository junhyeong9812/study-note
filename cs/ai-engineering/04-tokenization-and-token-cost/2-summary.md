# ai-engineering/04-tokenization-and-token-cost — 토큰화와 토큰 비용: BPE 병합, 언어별 토큰 수, 잘린 응답 — 정리 (힌트)

## 해결하는 문제

모델은 글자를 읽지 않는다. 정해진 크기의 어휘표에 있는 **번호(토큰 ID)의 나열**을 읽고 쓴다.

```text
  "캐시 hit"  ──토크나이저──>  [ 31245, 8812, 4410 ]  ──모델──>  [ 902, 77, ... ]  ──디토크나이저──>  "적중했다 ..."
                (텍스트 → 번호)                         (번호 → 번호)                  (번호 → 텍스트)
```

- 어휘표를 무엇으로 채울지가 문제다.
  - 단어 단위: 어휘표에 없는 단어(신조어·이름·오타)를 표현하지 못한다.
  - 글자(또는 바이트) 단위: 아무 글이나 표현하지만 나열이 길어진다. 길수록 모델이 느리고 비싸다.
  - *서브워드(subword)*: 그 중간. 자주 나오는 조각은 한 토큰, 드문 단어는 여러 조각으로 쪼갠다.
- Sennrich 외(ACL 2016)는 압축 알고리즘인 BPE(byte pair encoding)로 서브워드 조각을 고르는 방법을 냈다. GPT-2 논문(Radford 외 2019 §2.2)은 이를 **바이트** 위에서 돌려 기본 어휘 256개로 모든 유니코드 문자열을 표현했다.
  - *토큰*: 어휘표의 한 항목. 단어 하나일 수도, 단어 조각·바이트 하나일 수도 있다.

쉬운 예: 자주 쓰는 말에 줄임말을 붙인 메모 사전이다.
- "데이터베이스"를 자주 쓰면 "DB" 한 칸으로 적는다. 처음 보는 단어는 글자 하나하나 적는다.
- 사전을 영어 문서로 만들었다면, 한국어 문장은 줄임말이 적어 칸을 많이 쓴다.

똑같은 구조다.\
토크나이저는 학습 말뭉치에서 자주 나온 조각을 한 토큰(어휘표 번호 하나)으로 묶는다. 학습 말뭉치에 덜 나온 언어는 같은 뜻에 더 많은 토큰이 든다.

백엔드에서 토큰은 세 가지 단위다.
- **과금 단위**: 입력 토큰·출력 토큰마다 값을 매긴다.
- **한도 단위**: 문맥 창(context window)·분당 토큰 한도(TPM)가 토큰으로 정해진다.
- **시간 단위**: 출력은 토큰 하나씩 생성되므로 출력 토큰이 많을수록 응답이 길어진다. 첫 토큰까지의 시간(TTFT)은 따로 든다([10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md)).

그래서 글자 수로 비용·한도를 어림하면 언어에 따라 크게 틀리고, 출력 한도에 걸려 잘린 응답을 성공으로 저장하는 사고가 난다.

## 동작·원리

### 1. 텍스트 → 바이트 → 토큰

```text
  "캐시 hit"
     │ UTF-8 인코딩 (architecture/04)
     ▼
  EC BA 90  EC 8B 9C  20  68 69 74           ← 바이트 10개 (한글 음절 = 3바이트, 영문·공백 = 1바이트)
     │ 사전 분할 (공백·문자 종류 기준으로 단어 후보를 자른다)
     ▼
  [EC BA 90 EC 8B 9C]   [20 68 69 74]
     │ 학습된 병합 규칙을 순위대로 적용
     ▼
  [ "캐시" ]            [ " hit" ]            ← 토큰 2개 (병합 규칙이 있을 때)
  [EC][BA][90][EC]...   ...                   ← 병합 규칙이 없으면 바이트 하나 = 토큰 하나
```

- *바이트 수준 BPE*: 기본 어휘가 바이트 256개다. 어떤 문자열이든 최소한 바이트 토큰으로 떨어지므로 "어휘표에 없음(UNK)"이 생기지 않는다(GPT-2 §2.2: 유니코드 코드포인트 기준이면 기본 어휘가 13만 개를 넘는다고 지적).
- GPT-2는 바이트에 BPE를 그대로 적용하면 `dog.`·`dog!`·`dog?` 같은 변형이 따로 병합돼 어휘 칸을 낭비해서, 문자 종류(글자·구두점 등)를 넘는 병합을 막았다. 공백에는 예외를 두었다(§2.2 — 압축 효율이 크게 좋아졌다고 적는다).
- 한글 음절은 UTF-8에서 3바이트다. 병합 규칙이 없으면 음절 하나가 토큰 3개가 된다([architecture/04](../../architecture/04-character-encoding-unicode/2-summary.md)).

### 2. BPE 학습 — 가장 잦은 인접 쌍을 하나로 합치기를 반복

Sennrich 외 2016의 Algorithm 1 예제 어휘를 그대로 돌린 결과다(`</w>` = 단어 끝 표시).

```text
  시작 어휘(단어 빈도):  l o w </w> ×5   l o w e r </w> ×2   n e w e s t </w> ×6   w i d e s t </w> ×3

  1. e + s       (빈도 9)  → n e w es t </w>,  w i d es t </w>
  2. es + t      (빈도 9)  → n e w est </w>,   w i d est </w>
  3. est + </w>  (빈도 9)  → n e w est</w>,    w i d est</w>
  4. l + o       (빈도 7)  → lo w </w>,  lo w e r </w>
  5. lo + w      (빈도 7)  → low </w>,   low e r </w>
  6. n + e       (빈도 6)
  7. ne + w      (빈도 6)
  8. new + est</w> (빈도 6) → newest</w>          ← 자주 나온 단어는 통째로 한 토큰
  9. low + </w>  (빈도 5)  → low</w>
 10. w + i       (빈도 3)  → wi d est</w>        ← 드문 단어는 조각으로 남는다
```

- 한 바퀴: (1) 모든 인접 쌍의 빈도를 센다 → (2) 가장 잦은 쌍을 고른다 → (3) 어휘 전체에서 그 쌍을 새 기호로 바꾼다.
- 병합 횟수 = 어휘 크기를 정하는 하이퍼파라미터다(Sennrich 외: 기본 기호 수 + 병합 수 = 최종 어휘 크기).
- 1~3번은 빈도가 9로 같았다. 동점을 어떻게 깨느냐는 구현마다 다르다(이 실행은 파이썬 dict 삽입 순서).

### 3. 인코딩 — 병합 규칙을 학습 순서대로 적용

```text
  규칙표(순위):  0:(e,s)  1:(es,t)  2:(est,</w>)  3:(l,o)  4:(lo,w) ...

  "lowest</w>"  →  l o w e s t </w>
     현재 인접 쌍 중 순위가 가장 앞선 (e,s) 병합   →  l o w es t </w>
     그다음 (es,t)                                →  l o w est </w>
     그다음 (est,</w>)                            →  l o w est</w>
     그다음 (l,o) → (lo,w)                        →  low est</w>     ← 토큰 2개
```

- 학습에 없던 단어("lowest")도 아는 조각("low"+"est")으로 쪼개진다. 이것이 서브워드의 이점이다.
- 같은 문장이라도 **규칙표(토크나이저)가 다르면 토큰 수가 다르다.** 모델을 바꾸면 토크나이저가 바뀔 수 있다.
  - Anthropic 문서(2026-10-08 확인, "Token counting"): Claude Opus 4.7 이후 모델의 새 토크나이저는 같은 입력에 대략 30% 더 많은 토큰을 낸다. 옛 모델에서 잰 토큰 수를 새 모델 비용·문맥 창 어림에 다시 쓰지 말라고 적는다.

### 실험: 미니 바이트 수준 BPE로 본 한국어·영어 토큰 수

- 무엇: 영어 단어 152개·한국어 단어 147개로 Zipf 가중 무작위 문장(8단어)을 만들고, 학습 말뭉치의 언어 비율만 바꿔 바이트 수준 BPE(병합 300회)를 학습했다. 같은 시험 문장(언어별 300문장)을 토큰화해 셌다.
- 단순화: 실제 토크나이저의 어휘는 수만~수십만 개다. 이 실험은 **방향**을 보이는 모형이지 실제 모델의 토큰 비율이 아니다.
- 코드 핵심(`exp/04/bpe.py`):

```python
PRE = re.compile(r" ?[^\s]+")          # 앞 공백을 단어에 붙여 사전 분할 (GPT-2 방식의 단순화)

def train(lines, num_merges):
    vocab = Counter(tuple(m.encode()) for line in lines for m in PRE.findall(line))  # 기본 기호 = 바이트
    for rank in range(num_merges):
        pairs = Counter()
        for sym, f in vocab.items():
            for p in zip(sym, sym[1:]):
                pairs[p] += f                                   # 인접 쌍 빈도표 (해시맵)
        best = max(pairs.items(), key=lambda kv: (kv[1], -kv[0][0], -kv[0][1]))[0]
        ...                                                     # best를 새 ID로 바꿔 어휘 갱신
```

(실험, Python 3.12 `python:3.12-slim`, Docker `--network none --cpus=2`, 2026-10-08 — 시드 고정이라 2회 실행 출력 동일)

```text
시험 문장: 언어별 300문장 x 8단어 (seed 101·102), 병합 300회
학습 말뭉치                언어       글자    바이트     토큰    토큰/글자    바이트/토큰     4글자=1토큰 추정 오차
영어 위주 9:1             영     11214  11214   3191     0.28      3.51             -12%
영어 위주 9:1             한      8304  20712   7989     0.96      2.59             -74%
균형 1:1                영     11214  11214   4380     0.39      2.56             -36%
균형 1:1                한      8304  20712   4738     0.57      4.37             -56%
한국어 위주 1:9            영     11214  11214   6917     0.62      1.62             -59%
한국어 위주 1:9            한      8304  20712   3707     0.45      5.59             -44%
[영어 위주 학습] ' 쿠버네티스': 글자 6 바이트 16 토큰 12
[영어 위주 학습] ' kubernetes': 글자 11 바이트 11 토큰 9
[영어 위주 학습] ' 캐시': 글자 3 바이트 7 토큰 1
[영어 위주 학습] ' cache': 글자 6 바이트 6 토큰 1
[균형 학습, 한국어 시험문장 NFC] 코드포인트 8304 바이트 20712 토큰 4738
[균형 학습, 한국어 시험문장 NFD] 코드포인트 16401 바이트 45003 토큰 45003
```

- 관찰 1: 같은 한국어 시험 문장이 영어 위주로 학습한 토크나이저에서 7,989토큰, 한국어 위주에서 3,707토큰이다. 문장은 그대로이고 **토크나이저만** 바뀌었다(2.2배).
- 관찰 2: 한국어는 글자당 바이트가 약 2.5배(20,712 ÷ 8,304)다. 병합이 덜 된 토크나이저에서는 이 바이트 수가 토큰 수로 거의 그대로 이어진다.
- 관찰 3: "4글자 = 1토큰" 어림은 모든 행에서 실제보다 적게 잡았고, 영어 위주 토크나이저의 한국어에서 가장 크게(-74%) 틀렸다. 이 모형의 어휘가 작아서 영어도 틀렸다 — 실제 비율은 그 모델의 토큰 계수기로 잰다.
- 관찰 4: 학습에 없던 " 쿠버네티스"는 16바이트가 12토큰으로 거의 바이트 단위로 떨어졌다. 학습에 많이 나온 " 캐시"는 1토큰이다.
- 관찰 5: 같은 한국어 문장을 NFD(자모 분리)로 넣으니 병합 규칙이 하나도 맞지 않아 **바이트 수 = 토큰 수**(45,003)가 됐다. 화면에는 같은 글자로 보인다.
  - 실제 토크나이저가 입력을 먼저 유니코드 정규화하는지는 토크나이저마다 다르다(SentencePiece는 기본으로 입력을 NFKC로 정규화한다 — Kudo·Richardson 2018 §3.4). 앱이 보내기 전에 NFC로 맞춰 두면 이 차이를 없앨 수 있다.

### 4. 토큰이 정하는 세 가지 — 비용·한도·시간

```text
  요청 1건의 토큰 회계

  ┌──────────── 문맥 창 (예: 200k 토큰) ────────────┐
  │ 도구 정의 │ 시스템 프롬프트 │ 대화 기록 + 새 질문 │ 출력(생성 중) │
  └───────────┴─────────────────┴────────────────────┴──────────────┘
  ◄──────────────── 입력 토큰 (입력 단가) ──────────►◄─ 출력 토큰 ─►
                                                       (출력 단가, 하나씩 생성 = 시간)
```

- 비용 어림 식: `요청 비용 = 입력 토큰 × 입력 단가 + 출력 토큰 × 출력 단가`. 캐시 적중 토큰은 단가가 따로다([12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md)). 단가는 모델·날짜마다 바뀌므로 노트에 적지 않는다.
- 문맥 창: Anthropic Messages API 문서(2026-10-08 확인, "Context windows")
  - 도구 정의·시스템 프롬프트·모든 메시지·출력(확장 사고 포함)이 다 문맥 창에 들어간다.
  - 입력만으로 창을 넘으면 모든 모델에서 400 `invalid_request_error`("prompt is too long").
  - Claude 4.5 이후 모델은 `입력 + max_tokens`가 창을 넘어도 요청을 받는다. 생성이 창 끝에 닿으면 `stop_reason: "model_context_window_exceeded"`로 멈춘다. 그 이전 모델은 검증 오류를 낸다(베타 헤더 `model-context-window-exceeded-2025-08-26`로 같은 동작을 켤 수 있다).
- 어림 규칙은 언어 조건이 붙어 있다.
  - Gemini API 문서(2026-10-08 확인, "Tokens"): Gemini 모델에서 토큰 하나는 약 4글자, 100토큰은 영어 단어 약 60~80개. 한국어 수치는 없다.
  - tiktoken README: 실제로 평균 토큰 하나가 약 4바이트. 한글은 음절당 3바이트이므로 이 평균을 글자 수에 그대로 쓰면 안 된다.
- 정확한 수는 그 모델의 계수기로 센다.
  - Anthropic: token counting API. 문서가 "추정치이며 실제 입력 토큰과 조금 다를 수 있다"고 적는다(2026-10-08 확인).
  - OpenAI: tiktoken(`encoding_for_model`)으로 로컬에서 센다.
  - 응답의 `usage` 필드가 실제 과금된 수다. 이것을 저장해 어림을 보정한다.

### 5. 출력 한도에 걸린 응답 — 제공자마다 신호가 다르다

```text
  max_tokens = 5인 요청                         응답
  "주문 상태를 JSON으로 알려줘"   ──────>   {"status": "배송   ← 5토큰에서 멈춤 (HTTP 200)
                                            + 중단 사유 = "출력 한도"
```

| API (2026-10-08 확인) | 정상 종료 | 출력 한도로 잘림 |
|---|---|---|
| Anthropic Messages | `stop_reason: "end_turn"`·`"stop_sequence"` | `stop_reason: "max_tokens"`, `"model_context_window_exceeded"` |
| OpenAI Chat Completions | `finish_reason: "stop"` | `finish_reason: "length"` |
| OpenAI Responses | `status: "completed"` | `status: "incomplete"` + `incomplete_details.reason: "max_output_tokens"` |

- 잘림은 **HTTP 오류가 아니다.** 200 응답에 중단 사유로만 표시된다. 상태 코드만 보는 클라이언트는 성공으로 처리한다.
- 그 밖의 중단 사유(도구 호출 `tool_use`·`tool_calls`, 거부 `refusal`, 필터 `content_filter` 등)도 "완성된 답"이 아니다. 호출부가 사유별로 갈라 처리한다([11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **인접 쌍 빈도표 = 해시맵** — 키가 (기호, 기호) 쌍, 값이 빈도다([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **최빈 쌍 꺼내기 = 힙(우선순위 큐)** — 위 실험은 매 바퀴 전체를 다시 세는 단순 구현(병합 수 × 말뭉치 크기)이다. 병합 뒤 바뀐 쌍만 갱신하고 힙에서 최빈 쌍을 꺼내면 재계산을 줄인다([data-structure/07-heap](../../data-structure/07-heap/2-summary.md)). 특정 라이브러리의 내부 구현은 이 노트에서 확인하지 않았다 [?].
- **인코딩 = 순위표 조회 + 반복 병합** — 쌍 → 병합 순위 해시맵에서 현재 인접 쌍 중 순위가 가장 앞선 것을 고른다.
- **사전 분할 = 정규식** — 공백·문자 종류 경계로 단어 후보를 자른 뒤 그 안에서만 병합한다.
- **검색 토크나이저와 대비** — 전문 검색의 분석기(형태소·n-gram)는 사람이 정한 규칙으로 색인 용어를 만든다. BPE는 빈도로 조각을 학습한다. 모델은 학습 때 쓴 토크나이저로 추론해야 한다. 검색은 보통 색인·질의에 같은 분석기를 쓰지만, 자동완성(`edge_ngram`)·검색 시 동의어처럼 질의 쪽을 일부러 다르게 두기도 한다(Elasticsearch `search_analyzer` 문서, 2026-10-08 확인 · [database/46-full-text-search-and-analyzers](../../database/46-full-text-search-and-analyzers/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 원리 | 확인 |
|---|---|---|
| 한국어 요청만 예산·한도 초과 | 토큰/글자 비율이 언어·토크나이저마다 다르다 | 같은 뜻 한/영 프롬프트를 그 모델 계수기로 세어 비교 |
| 모델 교체 후 비용·문맥 초과가 늘었다 | 토크나이저가 바뀌어 같은 프롬프트의 토큰 수가 달라졌다 | 같은 요청을 옛·새 모델 ID로 각각 세어 `input_tokens` 비교 |
| 저장된 JSON이 가끔 파싱 실패, 문장이 중간에서 끊김 | 출력 한도 잘림을 200 = 성공으로 처리 | 저장 시점의 중단 사유(`stop_reason`·`finish_reason`·`status`) 분포 집계 |
| 같은 문서인데 어떤 파일만 토큰이 수 배 | 정규화 형식(NFC/NFD) 차이로 바이트가 늘었다 | 보내기 전 `Normalizer.isNormalized(s, NFC)` 비율 확인 |

### 2. 코드 — 중단 사유를 성공 판정에 넣는다 (Java 21)

```java
import java.nio.charset.StandardCharsets;

public class TokenBudget {
    enum Outcome { COMPLETE, TRUNCATED, OTHER }

    // 제공자마다 "출력 한도에서 잘림"을 알리는 값이 다르다 (2026-10-08 확인)
    static Outcome classify(String provider, String reason) {
        return switch (provider + ":" + reason) {
            // openai-responses의 reason = status("completed") 또는 incomplete_details.reason
            case "anthropic:end_turn", "anthropic:stop_sequence", "openai-chat:stop",
                 "openai-responses:completed" -> Outcome.COMPLETE;
            case "anthropic:max_tokens", "anthropic:model_context_window_exceeded",
                 "openai-chat:length", "openai-responses:max_output_tokens" -> Outcome.TRUNCATED;
            default -> Outcome.OTHER;   // tool_use·refusal·content_filter 등은 호출부가 따로 처리
        };
    }
}
```

- OpenAI Responses는 `status`를 먼저 보고, `incomplete`일 때만 `incomplete_details.reason`을 본다. `completed`여도 출력 항목이 거부(`refusal`)일 수 있어 따로 검사한다(OpenAI Structured Outputs 문서 예제, 2026-10-08 확인).
- `TRUNCATED`면 저장하지 않는다. 한도를 올려 재요청하거나, 이어 쓰기를 요청하거나, 실패로 기록한다.
- 구조화 출력(JSON)이라면 잘린 응답은 파싱 전에 걸러야 한다. 잘린 JSON이 우연히 파싱되는 경우도 있다(예: 배열이 짧게 끝난 것처럼 보이도록 잘림 — 예시).

(실험, OpenJDK 21.0.12 `eclipse-temurin:21-jdk`, Docker `--network none`, 2026-10-08 — `java TokenBudget.java`)

```text
Hello, world chars(UTF-16)=12 codePoints=12 utf8Bytes=12
안녕하세요 세계     chars(UTF-16)=8 codePoints=8 utf8Bytes=22
🙂           chars(UTF-16)=2 codePoints=1 utf8Bytes=4
anthropic max_tokens -> TRUNCATED
anthropic end_turn -> COMPLETE
openai-chat length -> TRUNCATED
openai-responses max_output_tokens -> TRUNCATED
openai-responses completed -> COMPLETE
anthropic refusal -> OTHER
```

- Java `String.length()`는 UTF-16 코드 유닛 수다. 이모지 하나가 2로 세어진다. 토큰 어림의 입력으로 `length()`를 쓰면 글자 수조차 틀린다.

### 3. 예산을 토큰으로 관리하는 순서

1. 프롬프트 템플릿마다 **그 모델의 계수기**로 고정부(시스템 프롬프트·도구 정의) 토큰을 잰다. 모델을 바꾸면 다시 잰다.
2. 가변부(사용자 입력·검색 결과)는 상한을 토큰으로 정한다. 글자 수 상한을 쓴다면 언어별로 따로 잡는다.
3. `max_tokens`는 "예상 답 길이 + 여유"로 정하고, 응답의 중단 사유로 잘림을 감지한다.
4. 응답 `usage`를 지표로 남겨(요청당 입력·출력 토큰, 언어별) 어림을 보정한다([23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md)).

## 장애 시나리오와 대처

### 1. 글자 수로 어림한 예산이 한국어에서 초과

- **현상**: 영어 트래픽 기준으로 잡은 월 예산·TPM 한도가 한국어 서비스를 붙이자 초과한다.
- **보이는 형태**: 429(분당 토큰 한도), 비용 알람, 긴 입력에서 400 "prompt is too long"(Anthropic). 오류가 한국어 요청에 몰린다.
- **원인**: "4글자 ≈ 1토큰" 같은 영어 기준 어림을 언어 구분 없이 썼다. 한국어는 글자당 바이트가 많고, 토크나이저 학습 말뭉치 비율에 따라 글자당 토큰이 늘어난다(위 실험에서 같은 문장이 토크나이저에 따라 3,707~7,989토큰).
- **대처**: 그 모델의 계수기로 언어별 실측 비율을 구한다. 한도 검사를 토큰 단위로 바꾼다. `usage`를 언어 태그와 함께 집계한다.

### 2. 출력 한도에 잘린 응답을 성공으로 저장

- **현상**: 요약·JSON 추출 결과가 가끔 중간에서 끊긴 채 DB에 들어간다.
- **보이는 형태**: 다운스트림 JSON 파싱 오류, 문장이 끊긴 요약. 원 요청 로그는 HTTP 200이다.
- **원인**: 중단 사유(`max_tokens`·`length`·`incomplete`)를 보지 않고 상태 코드만으로 성공을 판정했다.
- **대처**: 중단 사유를 성공 판정에 넣는다(위 `classify`). 잘림 비율을 지표로 두고 `max_tokens`를 조정한다. 잘린 결과는 저장하지 않고 재시도·실패로 처리한다.

### 3. 모델 교체 뒤 같은 프롬프트의 토큰 수·비용이 달라짐

- **현상**: 모델만 바꿨는데 비용이 늘고, 전에는 들어가던 긴 문서가 문맥 창·입력 상한에 걸린다.
- **보이는 형태**: 같은 요청의 `usage.input_tokens`가 모델별로 다르다. Anthropic 문서는 Opus 4.7 이후 토크나이저에서 대략 30% 증가를 예로 든다(2026-10-08 확인).
- **원인**: 토크나이저(병합 규칙표)가 바뀌었다. 토큰 수는 텍스트가 아니라 (텍스트, 토크나이저) 쌍의 성질이다.
- **대처**: 모델 교체 체크리스트에 "대표 프롬프트 토큰 재측정"을 넣는다. 토큰 기반 상한·비용 예측표를 모델 ID별로 둔다.

### 4. 대화 기록 누적으로 문맥 창 초과

- **현상**: 긴 상담 세션 후반에만 요청이 실패하거나 답이 짧게 끊긴다.
- **보이는 형태**: Anthropic에서 400 "prompt is too long" 또는 `stop_reason: "model_context_window_exceeded"`. 실패가 턴 수와 상관된다.
- **원인**: 매 턴 전체 기록을 다시 보내 입력 토큰이 턴마다 늘었다. 출력도 같은 창을 쓴다.
- **대처**: 기록을 토큰 예산 안으로 자르거나 요약한다. 요청 전에 계수기로 `입력 + max_tokens`를 검사한다.

### 5. 정규화 형식 차이로 일부 입력만 토큰 폭증

- **현상**: 특정 경로(예: macOS에서 올린 파일 이름·본문)를 포함한 요청만 비용이 수 배다.
- **보이는 형태**: 화면에는 같은 한글인데 바이트 수가 다르다(NFD는 음절이 자모 2~3개로 풀린다). 위 실험에서 같은 한국어 문장이 NFC 4,738토큰, NFD 45,003토큰.
- **원인**: 토크나이저 병합 규칙은 학습 때 본 바이트열에만 맞는다. NFD 바이트열에는 맞는 규칙이 없어 바이트 단위로 떨어졌다.
- **대처**: 모델에 보내기 전에 NFC로 정규화한다([architecture/04](../../architecture/04-character-encoding-unicode/2-summary.md)). 요청당 바이트/토큰 비율이 튀는 것을 지표로 잡는다.

## 핵심 문장

- 모델은 텍스트가 아니라 토큰 ID 나열을 읽고 쓴다. BPE는 가장 잦은 인접 쌍을 반복 병합해 어휘표를 만들고, 인코딩은 그 병합 규칙을 학습 순서대로 적용한다.
- 바이트 수준 BPE는 기본 어휘 256개로 어떤 문자열도 표현하지만, 병합 규칙이 없는 부분은 바이트 하나가 토큰 하나가 된다.
- 토큰 수는 (텍스트, 토크나이저) 쌍의 성질이다. 언어·토크나이저·정규화 형식이 바뀌면 같은 뜻의 토큰 수가 달라진다.
- 토큰은 과금·문맥 한도·생성 시간의 단위다. 어림은 그 모델의 계수기와 응답 `usage`로 보정한다.
- 출력 한도에 걸린 응답은 HTTP 200이다. 중단 사유(`max_tokens`·`length`·`incomplete`)를 성공 판정에 넣지 않으면 잘린 결과를 저장한다.

## 관련 주제·근거

- 선행
  - [architecture/04-character-encoding-unicode](../../architecture/04-character-encoding-unicode/2-summary.md) — UTF-8 바이트 수, NFC·NFD
- 후속·연결
  - [05-embeddings-and-similarity](../05-embeddings-and-similarity/2-summary.md) — 토큰 나열을 고정 길이 벡터로
  - [07-decoding-and-nondeterminism](../07-decoding-and-nondeterminism/2-summary.md) — 토큰을 하나씩 고르는 방법
  - [10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md) — 출력 토큰 수와 응답 시간
  - [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md) — 중단 사유·오류·재시도 계약
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) — 캐시 적중 토큰의 단가
  - [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md) — 토큰 사용량 집계
  - [database/46-full-text-search-and-analyzers](../../database/46-full-text-search-and-analyzers/2-summary.md) — 검색 분석기의 토큰화와 대비
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- 논문
  - Sennrich·Haddow·Birch, "Neural Machine Translation of Rare Words with Subword Units", ACL 2016 — Algorithm 1(BPE 학습 파이썬 코드와 예제 어휘), 최종 어휘 = 기본 기호 + 병합 수, §3.2 테스트 때 미등록으로 남는 것은 처음 보는 문자뿐 <https://arxiv.org/abs/1508.07909>
  - Radford 외, "Language Models are Unsupervised Multitask Learners"(GPT-2, 2019) §2.2 Input Representation — 바이트 수준 BPE, 기본 어휘 256, 유니코드 기준이면 13만 초과, 문자 종류를 넘는 병합 금지·공백 예외 <https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf>
  - Kudo·Richardson, "SentencePiece", EMNLP 2018 demo — 사전 분할 없이 원문 문장에서 직접 서브워드 학습, 언어 독립, §3.4 기본 NFKC 정규화 <https://arxiv.org/abs/1808.06226>
- 교재: Jurafsky·Martin, 『Speech and Language Processing』 3판 초안(2026-08-19판) 2장 Words and Tokens <https://web.stanford.edu/~jurafsky/slp3/>
- 문서 (모두 2026-10-08 확인)
  - tiktoken README — BPE 토크나이저, 평균 토큰 ≈ 4바이트, `encoding_for_model` <https://github.com/openai/tiktoken>
  - Anthropic "Context windows" — 창에 들어가는 것, 400 "prompt is too long", `model_context_window_exceeded` <https://platform.claude.com/docs/en/build-with-claude/context-windows>
  - Anthropic "Token counting" — 추정치, Opus 4.7 이후 토크나이저 약 30% 증가 <https://platform.claude.com/docs/en/build-with-claude/token-counting>
  - Anthropic "Handling stop reasons" — `end_turn`·`max_tokens`·`stop_sequence`·`tool_use`·`pause_turn`·`refusal`·`model_context_window_exceeded` <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
  - OpenAI API reference "Create chat completion" — `finish_reason`: `stop`·`length`·`tool_calls`·`content_filter`·`function_call` <https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create>
  - OpenAI "Structured Outputs" — Responses API `status: "incomplete"`·`incomplete_details.reason: "max_output_tokens"` 처리 예 <https://developers.openai.com/api/docs/guides/structured-outputs>
  - Elasticsearch "search_analyzer" — 보통 색인·질의에 같은 분석기, 자동완성 `edge_ngram`·검색 시 동의어는 질의 분석기를 따로 둘 수 있음 <https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/search-analyzer>
  - vLLM "Metrics" — TPOT = (종단 지연 − TTFT)/(출력 토큰 − 1) <https://docs.vllm.ai/en/latest/design/metrics/>
  - Gemini API "Tokens" — 약 4글자/토큰, 100토큰 ≈ 영어 60~80단어 <https://ai.google.dev/gemini-api/docs/tokens>
- 실험 목록
  - 미니 바이트 수준 BPE: 학습 말뭉치 언어 비율별 한/영 토큰 수, 미등록 단어, NFC/NFD — Python 3.12 `python:3.12-slim`, 시드 1·2·101·102, 2회 실행 동일
  - Sennrich Algorithm 1 예제 어휘 병합 10회 재현 — 같은 환경
  - 중단 사유 분류·UTF-16/코드포인트/UTF-8 바이트 비교 — OpenJDK 21.0.12 `eclipse-temurin:21-jdk`
