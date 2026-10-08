# ai-engineering/14-structured-output-and-tool-calling — 구조화 출력과 도구 호출: 스키마 강제의 보장 범위, 검증·거부·잘림 처리, 도구 계약 — 정리 (힌트)

## 해결하는 문제

모델은 글을 만든다. 앱이 필요한 것은 **필드가 정해진 데이터**나 **실행할 함수 호출**이다.

```text
  모델 출력(글)                                  앱이 원하는 것
  "환불해 드릴게요. 주문 o-17, 금액은 3천 원"   →   {"orderId":"o-17","action":"refund","amount":3000}
                                                    refund(orderId="o-17", amount=3000)
```

- 프롬프트로 "JSON으로 답하라"고 부탁하면 대개는 맞게 온다. 하지만 필드가 빠지거나, 숫자가 문자열로 오거나, 설명 문장이 붙는다.
- Anthropic Structured outputs 문서(2026-10-08 확인)도 구조화 출력이 없으면 JSON 문법 오류·필수 필드 누락·타입 불일치가 생길 수 있다고 적는다.

쉬운 예: 주문서다.
- 자유롭게 쓴 손 편지 주문은 사람이 읽어야 한다. 빠진 정보가 있을 수 있다.
- 칸이 정해진 양식(체크박스·숫자 칸)이면 형식은 맞는다. 하지만 양식이 "그 주문번호가 이 고객 것인지"까지 보장하지는 않는다. 창구 직원이 따로 확인한다.

똑같은 구조다.\
스키마 강제(구조화 출력)는 양식이다. 형식은 맞춰 주지만, 업무 규칙·권한 확인은 여전히 앱 몫이다.

백엔드 실무 예:
- 상담 기록에서 환불 요청 구조체를 뽑아 주문 시스템에 넘긴다.
- 에이전트가 `cancel_order(orderId)` 같은 도구를 호출하게 한다([20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md)).

## 동작·원리

### 1. 형식을 맞추는 세 단계

| 방법 | 보장 | 근거(2026-10-08 확인) |
|---|---|---|
| 프롬프트로 부탁 | 없음 | — |
| JSON mode | 문법상 올바른 JSON(일부 예외 상황은 직접 감지) | OpenAI "Structured Outputs" 가이드: 둘 다 올바른 JSON을 내지만 스키마 준수는 Structured Outputs만 보장 |
| 스키마 강제(Structured Outputs·strict 도구) | 스키마 준수 — 단 §3의 예외가 있다 | OpenAI 가이드 같은 절, Anthropic "Structured outputs"·"Strict tool use" |

- *구조화 출력(structured outputs)*: 제공자에게 JSON 스키마를 주면 출력이 그 스키마를 따르도록 생성 과정에서 강제하는 기능.
- *strict 도구 사용*: 도구 인자(입력 스키마)에 같은 강제를 적용하는 것. Anthropic 문서는 도구 이름이 늘 유효하고 입력이 `input_schema`를 엄격히 따른다고 적는다.
- 스키마 언어는 JSON Schema다. 현재 판은 2020-12이고 Core·Validation 두 문서로 나뉜다.

### 2. 제약 디코딩 — 허용되지 않는 토큰을 가린다

```text
  스키마 {"amount": integer}를 문법(상태 기계)으로 바꾼 뒤, 토큰마다:

  지금까지 출력   {"amount":
  문법 상태       "정수의 첫 글자를 기다림"
  모델 확률       '"' 0.40   '3' 0.35   '삼' 0.15   '1' 0.10
  마스크          '"' ✗      '3' ✓      '삼' ✗      '1' ✓        ← 문법이 허용하지 않는 토큰의 확률을 0으로
  다시 정규화      '3' 0.78   '1' 0.22                             → 이 안에서 샘플링(07)
```

- *제약 디코딩(constrained decoding)*: 디코딩 단계마다 문법이 허용하는 토큰만 남기고 샘플링하는 방법. Anthropic 문서는 이를 "grammar-constrained sampling", 스키마를 "compiled grammar"로 바꿔 쓴다고 적는다.
- 위 그림은 원리 설명용 개념 그림이다(확률은 예시). 제공자 내부 구현은 공개 문서 범위 밖이다.
- 디코딩·샘플링 자체는 [07-decoding-and-nondeterminism](../07-decoding-and-nondeterminism/2-summary.md)이 단일 출처다.
- 문법 컴파일에는 비용이 든다(Anthropic 문서, 2026-10-08 확인).
  - 새 스키마의 **첫 요청은 컴파일 때문에 지연이 더 길다.** 컴파일된 문법은 마지막 사용부터 24시간 캐시된다.
  - 스키마 구조나 (도구와 함께 쓸 때) 도구 집합을 바꾸면 캐시가 무효가 된다. 이름·설명만 바꾸면 유지된다.
  - 복잡도 상한이 있다: 요청당 strict 도구 20개, 선택 파라미터 합계 24개, 합집합 타입 파라미터 16개, 컴파일 시간 제한 180초. 넘으면 400.
  - OpenAI "Structured Outputs" 가이드는 "어떤 스키마든 첫 요청은 추가 지연"이라고 적는다. "Function calling" 가이드의 strict 모드 한계 절은 같은 내용을 "미세조정 모델에 한해" 항목 아래 적는다. 두 문서의 문구가 갈리므로 첫 요청 지연은 직접 재 본다.

### 3. 보장의 경계 — 스키마를 강제해도 남는 것

| 남는 것 | Anthropic(Messages API) | OpenAI | 앱이 할 일 |
|---|---|---|---|
| 거부 | `stop_reason: "refusal"`, HTTP 200, 생성 토큰 과금, 출력이 스키마와 안 맞을 수 있음 | `refusal` 필드로 감지 | 스키마 오류로 보지 않는다. 같은 요청 재시도는 무의미 |
| 출력 한도에 잘림 | `stop_reason: "max_tokens"`, 스키마와 안 맞을 수 있음 | Responses: `status: "incomplete"` + `incomplete_details.reason: "max_output_tokens"` · Chat Completions: `finish_reason: "length"` | 부분 파싱하지 않는다. 한도를 올려 다시 요청 |
| 지원하지 않는 키워드 | 숫자 범위(`minimum`·`maximum`·`multipleOf`)·문자열 길이·재귀 스키마 미지원 → 쓰면 400 | `minimum`·`maximum`·`pattern`·`minItems` 등 지원(미세조정 모델은 미지원), 모든 필드 `required`·`additionalProperties: false` 필수 | 범위·길이는 앱에서 검증 |
| enum 대소문자 | enum·const 값의 대소문자를 보장하지 않음(오류·특별 중단 사유 없음) | (문서에서 확인 못 함) | 대소문자 무시 비교, 대소문자만 다른 enum 금지 |
| 업무 규칙·권한 | 스키마가 모름 | 스키마가 모름 | 소유권·상태·한도를 서버에서 확인 |

- 출처: Anthropic "Structured outputs"(Invalid outputs·JSON Schema limitations 절), OpenAI "Structured Outputs" 가이드(Supported properties·All fields must be required·refusal 절), 모두 2026-10-08 확인. 지원 범위는 자주 바뀐다 — 쓰기 전에 다시 확인한다.
- Anthropic SDK 도우미는 지원하지 않는 제약(예: `minimum`)을 보낼 스키마에서 빼고 필드 설명에 적어 넣는다. 응답을 검증하는 도우미는 원래 스키마의 제약을 코드에서 다시 검사한다. 하지만 `transform_schema()`처럼 변환만 하거나 제약을 손으로 빼고 보내면, 설명으로 옮긴 제약은 생성 단계에서 **강제되지 않으므로** 앱이 검증해야 한다(문서 "How SDK transformation works").
- JSON Schema 2020-12 자체의 기본값도 알아 둔다(Core 10.3.2.3, Validation 6.1.1).
  - `additionalProperties`를 생략하면 빈 스키마와 같다. 정의 밖 속성을 허용한다.
  - `integer`는 "소수부가 0인 수"와 맞는다. `3000.0`도 integer다.

### 4. 도구 호출 계약 — 모델은 제안하고, 앱이 실행한다

```text
  앱 → 모델: 도구 목록 [{name, description, input_schema}] + 대화
  모델 → 앱: tool_use {id: "toolu_1", name: "cancel_order", input: {"orderId": "o-99"}}   stop_reason: tool_use
  앱:        ① 이름이 허용 목록에 있나  ② 인자 스키마 검증  ③ 권한·업무 규칙(o-99가 이 사용자 것인가)
             ④ 부작용 도구면 멱등 키 ⑤ 실행
  앱 → 모델: tool_result {tool_use_id: "toolu_1", content: "...", is_error: false}
  모델 → 앱: 결과를 반영한 다음 응답(또는 다음 도구 호출)
```

- Anthropic 형식: 결과는 `tool_use_id`로 짝을 맞춘 `tool_result` 블록이다. 도구 실행이 실패하면 `is_error: true`와 오류 내용을 돌려준다. `tool_result` 블록은 해당 `tool_use` 바로 다음 user 메시지의 맨 앞에 와야 한다("Handle tool calls", 2026-10-08 확인).
- OpenAI 형식: Responses API는 `call_id`로 짝을 맞춘 `function_call_output`, Chat Completions는 `tool_call_id`. 응답 하나에 호출이 0개·1개·여러 개 올 수 있으니 여러 개를 가정하라고 적는다. strict 모드를 켜 두라고 권한다("We recommend always enabling strict mode")("Function calling", 2026-10-08 확인).
- 형식 이름은 벤더 고유다. 공통인 것은 "모델은 호출을 **제안**할 뿐, 실행은 앱이 검증 뒤에 한다"는 구조다.
- 연구 배경: Toolformer(Schick 외 2023)는 어떤 API를 언제 어떤 인자로 부를지를 모델이 자기 지도 방식으로 배우게 했다(초록). 모델이 도구 사용을 "판단"한다는 것은 틀릴 수 있다는 뜻이기도 하다.

### 실험: 응답 처리 계약 — 중단 사유 → 문법 → 스키마 → 업무 규칙

JDK만으로 최소 JSON 파서와 JSON Schema 부분집합 검증기(`type`·`properties`·`required`·`additionalProperties`·`enum`·`minimum`·`maximum`·`maxLength`)를 만들었다. 모델 응답은 손으로 만든 모형이다.

```java
static Outcome handle(ModelReply r, boolean alreadyReasked) {
    switch (r.stopReason) {                                  // 1. 중단 사유가 먼저다
        case "max_tokens" -> { return new Outcome(Verdict.REJECT_TRUNCATED, "잘린 출력은 부분 파싱하지 않는다"); }
        case "refusal"    -> { return new Outcome(Verdict.REJECT_REFUSAL, "거부는 스키마 오류가 아니다"); }
        case "end_turn", "tool_use" -> { }
        default -> { return new Outcome(Verdict.REJECT_INVALID, "알 수 없는 중단 사유 " + r.stopReason); }
    }
    Object v;
    try { v = new P(r.text).parse(); }                       // 2. 문법
    catch (IllegalArgumentException e) { return alreadyReasked ? reject(e) : reask(e); }
    normalizeEnumCase(v);                                    // 대소문자만 다른 enum 정규화
    List<String> errs = new ArrayList<>();
    validate(v, SCHEMA, "$", errs);                          // 3. 스키마 — 범위·정의 밖 속성까지
    if (!errs.isEmpty()) return alreadyReasked ? reject(errs) : reask(errs);
    if (!OWNED.contains(((Map<?, ?>) v).get("orderId")))     // 4. 업무 규칙·권한 — 스키마가 모르는 것
        return new Outcome(Verdict.REJECT_FORBIDDEN, "이 사용자 소유가 아님 → 실행하지 않음");
    return new Outcome(Verdict.ACCEPT, v.toString());
}
```

스키마: `orderId` 문자열(최대 32자), `action` ∈ {refund, cancel}, `amount` 정수 1~1,000,000, 셋 다 필수, 정의 밖 속성 금지. 사용자가 소유한 주문은 o-17·o-18.\
비교 대상 "순진" 코드는 파싱만 하고 없는 `amount`를 0으로 채운다.

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12, `--network none --cpus=2`, 2026-10-08, 2회 실행 출력 동일)

```text
정상               순진: 실행: refund o-17 amount=3000            | 계약: ACCEPT            {orderId=o-17, action=refund, amount=3000}
필드 누락            순진: 실행: refund o-17 amount=0               | 계약: REASK             $: required 'amount' 없음
타입 불일치           순진: 실행: refund o-17 amount=3000            | 계약: REASK             $.amount: type integer 기대, 실제 string
enum 대소문자        순진: 실행: Refund o-17 amount=3000            | 계약: ACCEPT            {orderId=o-17, action=refund, amount=3000}
범위 밖             순진: 실행: refund o-17 amount=99999999        | 계약: REASK             $.amount: maximum 1000000 초과
정의 밖 속성          순진: 실행: refund o-17 amount=3000            | 계약: REASK             $: 정의 밖 속성 'note'
잘림(max_tokens)   순진: 예외 IllegalArgumentException            | 계약: REJECT_TRUNCATED  잘린 출력은 부분 파싱하지 않는다 → 한도를 올려 재요청하거나 실패
거부(refusal)      순진: 예외 IllegalArgumentException            | 계약: REJECT_REFUSAL    거부는 스키마 오류가 아니다 → 같은 요청 재시도 안 함
남의 주문            순진: 실행: cancel o-99 amount=1               | 계약: REJECT_FORBIDDEN  주문 o-99은 이 사용자 소유가 아님 → 실행하지 않음
-- 재요청 1회 상한: 두 번째도 스키마 위반이면 거절
1차 REASK → 2차 REJECT_INVALID ($.amount: minimum 1 미만)
```

- **필드 누락**: 순진한 코드는 기본값 0으로 "환불 0원"을 실행했다. 오류 없이 틀린 값이 하류로 갔다.
- **타입 불일치**: 순진한 코드는 문자열 `"3000"`을 그대로 넘겼다. 숫자로 쓰는 하류 코드에서 나중에 터진다.
- **범위 밖**: Anthropic처럼 숫자 범위를 API가 강제하지 않는 경우, 이 검사는 앱에만 있다.
- **잘림·거부**: 순진한 코드는 둘 다 같은 파싱 예외로 끝난다. 이 예외로 "재요청"하면 거부에도 같은 요청을 반복한다. 계약 코드는 중단 사유로 먼저 갈라 서로 다른 처리로 보낸다.
- **남의 주문**: 형식은 완벽하다. 스키마로는 못 막고, 소유권 확인만 막는다.
- 모형의 단순화: 이 실험은 `end_turn`과 `tool_use`를 같은 경로로 보내 `r.text`를 JSON으로 파싱한다. 실제 Anthropic 응답에서 도구 인자는 텍스트가 아니라 `tool_use` 블록의 `input` **객체**에 오고, 한 응답에 `tool_use` 블록이 여러 개일 수 있다("Handle tool calls", 2026-10-08 확인). 실제 코드는 블록마다 `id`·`name`·`input`을 꺼내 §4의 ①~③(이름 허용 목록 → 인자 스키마 → 권한)을 거친다.
- 재요청은 1회로 묶었다. 두 번째도 틀리면 거절한다 — 무한 재요청은 비용·지연만 키운다.

## 쓰이는 자료구조·알고리즘

- **재귀 하강 파서** — JSON 문법(값 = 객체 | 배열 | 문자열 | 수 | 리터럴)을 함수 호출 구조 그대로 읽는다. 잘린 입력은 "입력 끝" 오류로 드러난다.
- **스키마 검증 = 두 트리를 함께 내려가는 순회** — 인스턴스 트리와 스키마 트리를 같은 경로로 내려가며 키워드마다 검사하고, 오류에 경로(`$.amount`)를 붙인다.
- **문법 상태 기계(유한 오토마톤·푸시다운 오토마톤)** — 제약 디코딩이 "다음에 허용되는 토큰"을 계산하는 틀이다(§2 개념).
- **허용 목록(해시 집합)** — 도구 이름 허용 목록, 사용자 소유 ID 집합([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **사전·사후 조건** — 도구 호출 전 인자 검증이 계약에 의한 설계의 사전 조건이다([software-design/23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 처리 순서를 고정한다

```text
  ① 중단 사유      잘림 → 한도 올려 재요청/실패 · 거부 → 재시도 없이 처리 · 도구 호출 → ②로
  ② 문법           JSON 파싱 — 실패하면 재요청 1회
  ③ 정규화          대소문자 등 문서가 경고한 흔들림만 좁게 — 스키마 검증 **전에**(enum은 정확 일치라 "Refund" ≠ "refund")
  ④ 스키마          JSON Schema 2020-12 검증기 — API가 강제하지 못한 키워드(범위·길이)까지
  ⑤ 업무 규칙·권한   소유권·상태 전이·금액 한도 — 서버의 진실과 대조
  ⑥ 실행            부작용 도구는 멱등 키와 함께(20, reliability/13)
```

- 스키마 검증은 직접 만들지 말고 JSON Schema 2020-12를 지원하는 검증 라이브러리를 쓴다. 실험의 검증기는 원리를 보이려는 부분집합이다.
- 재요청할 때는 검증 오류 메시지(경로·기대값)를 함께 보낸다. 같은 요청을 그대로 반복하면 같은 분포에서 다시 뽑을 뿐이다.

### 2. 도구 인자는 사용자 입력처럼 다룬다

```java
record CancelOrderArgs(String orderId) {}

ToolResult cancelOrder(CancelOrderArgs args, AuthContext auth, String idempotencyKey) {
    Order o = orders.findById(args.orderId())
            .orElseThrow(() -> new ToolError("주문 없음: " + args.orderId()));
    if (!o.ownerId().equals(auth.userId()))                     // 모델이 만든 ID를 믿지 않는다
        return ToolResult.error("이 주문을 취소할 권한이 없습니다");   // is_error: true로 모델에 돌려준다
    if (!o.status().canCancel())
        return ToolResult.error("이미 " + o.status() + " 상태라 취소할 수 없습니다");
    return ToolResult.ok(orders.cancel(o.id(), idempotencyKey));  // 재시도로 두 번 와도 한 번만
}
```

- 권한은 **세션의 사용자**로 확인한다. 모델 출력이나 프롬프트에 든 사용자 ID로 확인하지 않는다.
- 모델 출력이 SQL·HTML·셸로 흘러가는 경로는 출력 처리 부실 문제다([22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md), [security/18-injection](../../security/18-injection/2-summary.md)).

### 3. 새 스키마 배포

- 새 스키마 첫 요청은 문법 컴파일로 늦다(Anthropic 문서). 배포 직후 워밍업 요청을 한 번 보내거나, 첫 요청의 첫 토큰 타임아웃을 넉넉히 둔다([11](../11-llm-api-client-contract/2-summary.md)).
- 스키마를 자주 바꾸면 컴파일 캐시(24시간)가 계속 무효가 된다. 스키마 버전을 관리하고 묶어서 바꾼다([api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md)).

## 장애 시나리오와 대처

### 1. 스키마 검증 없이 파싱만 → 누락·타입 불일치가 하류로 전파 (⚠ 커리큘럼)

- 현상: 환불 금액 0원, 문자열 금액으로 인한 하류 `ClassCastException`이 드문드문 생긴다.
- 보이는 형태: LLM 호출 쪽 로그는 정상. 실험에서 순진한 코드는 누락된 `amount`를 0으로 채워 "환불 0원"을 실행했다.
- 원인: JSON 문법만 확인했다. 필수 필드·타입·범위를 검증하지 않았다.
- 대처: 파싱 뒤 스키마 검증을 빠짐없이 거치게 한다. 기본값으로 빈 필드를 채우지 않는다.

### 2. 출력 한도로 잘린 구조화 출력을 부분 파싱 (⚠ 커리큘럼)

- 현상: 목록의 뒷부분 항목이 조용히 빠진다.
- 보이는 형태: `stop_reason: "max_tokens"`(Anthropic)·`status: "incomplete"`(OpenAI Responses)·`finish_reason: "length"`(OpenAI Chat Completions). "관대한" 파서가 닫히지 않은 배열을 닫아 앞부분만 돌려준다.
- 원인: 출력이 한도에 닿아 중간에서 끊겼다. 제공자 문서도 이때 출력이 스키마와 안 맞을 수 있다고 적는다.
- 대처: 중단 사유를 파싱보다 먼저 본다. 잘린 출력은 버리고 `max_tokens`를 올리거나 요청을 쪼갠다([11](../11-llm-api-client-contract/2-summary.md)).

### 3. 거부(refusal)를 스키마 오류로 오인해 재시도 반복 (⚠ 커리큘럼)

- 현상: 특정 입력에서 재요청이 상한까지 반복되고 비용만 쌓인다.
- 보이는 형태: 응답은 200, 내용은 거부 문장. 실험에서 순진한 코드는 거부와 잘림이 같은 파싱 예외였다.
- 원인: 거부는 스키마 제약보다 우선한다(Anthropic 문서). 같은 요청을 다시 보내도 대개 같은 결과다.
- 대처: `stop_reason: "refusal"`·`refusal` 필드를 먼저 확인해 별도 경로로 보낸다(사용자 안내·사람 검토·다른 처리).

### 4. 새 스키마 첫 요청만 문법 컴파일로 지연 → 첫 호출만 타임아웃 (⚠ 커리큘럼)

- 현상: 배포 직후 첫 몇 건만 타임아웃, 이후 정상.
- 보이는 형태: 첫 토큰 지연이 배포 직후에만 크게 튄다.
- 원인: 새 스키마의 문법을 처음 컴파일한다(Anthropic 문서: 첫 요청 추가 지연, 24시간 캐시, 스키마 구조·도구 집합 변경 시 무효).
- 대처: 배포 때 워밍업 요청, 첫 요청의 첫 토큰 타임아웃을 넉넉히, 스키마 변경을 묶어서.

### 5. 모델이 만든 도구 인자를 검증 없이 실행 → 엉뚱한 ID의 레코드 수정 (⚠ 커리큘럼)

- 현상: 고객 A의 요청으로 고객 B의 주문이 취소됐다.
- 보이는 형태: 도구 호출 로그의 인자는 스키마상 완벽하다(실험의 `o-99`).
- 원인: strict 모드는 형식만 보장한다. 어떤 주문 ID가 이 사용자 것인지는 모른다. 모델이 대화·검색 문서 속 다른 ID를 집어 왔을 수 있다.
- 대처: 세션 사용자 기준 소유권·상태 확인을 도구 구현 안에서 한다. 부작용 도구는 멱등 키와 사람 확인을 둔다([20](../20-agent-loop-and-tool-safety/2-summary.md)).

### 6. 대소문자만 다른 enum 값으로 분기 누락

- 현상: `"Refund"`가 와서 `switch`의 어느 분기에도 안 걸리고 기본 처리로 빠진다.
- 보이는 형태: 오류도 특별한 중단 사유도 없다(Anthropic 문서가 이렇게 적는다).
- 원인: 제공자가 enum·const 값의 대소문자를 보장하지 않는다.
- 대처: enum은 대소문자를 무시해 비교하고, 대소문자만 다른 enum 값을 만들지 않는다. 그다음 스키마 검증을 다시 한다(실험의 "enum 대소문자" → ACCEPT).

## 핵심 문장

- 프롬프트로 부탁하면 형식 보장이 없고, JSON mode는 문법만, 스키마 강제는 스키마까지 보장한다.
- 스키마 강제에도 거부·잘림·지원하지 않는 키워드·enum 대소문자 예외가 있다. 그래서 중단 사유 → 문법 → 스키마 → 업무 규칙 순서로 앱이 다시 확인한다.
- 지원 범위는 제공자마다 다르다. 한쪽 API가 막아 주던 범위 검사가 다른 쪽에서는 앱에만 있다.
- 거부는 스키마 오류가 아니다. 같은 요청을 다시 보내지 않는다.
- 도구 호출은 모델의 제안이다. 인자를 사용자 입력처럼 검증하고, 권한은 세션 사용자로 확인한 뒤 실행한다.

## 관련 주제·근거

- 선행
  - [07-decoding-and-nondeterminism](../07-decoding-and-nondeterminism/2-summary.md) — 디코딩·샘플링(제약 디코딩이 끼어드는 자리)
  - [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md) — 중단 사유·잘림
  - [api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md) — 스키마와 직렬화
- 후속·연결
  - [13-model-routing-and-fallback](../13-model-routing-and-fallback/2-summary.md) — 폴백 모델의 지원 범위 차이
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md), [20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md), [21-mcp-protocol](../21-mcp-protocol/2-summary.md), [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md)
  - [software-design/23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md), [security/18-injection](../../security/18-injection/2-summary.md), [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
- 명세
  - JSON Schema 2020-12 — Core 10.3.2.3 `additionalProperties`(생략 = 빈 스키마), Validation 6.1.1 `type`(integer = 소수부 0인 수)·6.1.2 `enum`·6.2 수치·6.3.1 `maxLength`(RFC 8259 문자 수)·6.5.3 `required` <https://json-schema.org/draft/2020-12/json-schema-core> · <https://json-schema.org/draft/2020-12/json-schema-validation>
- 제공자 문서(모두 2026-10-08 확인)
  - Anthropic "Structured outputs" — 제약 샘플링·컴파일 문법, 첫 요청 지연·24시간 캐시·무효 조건, 지원/미지원 키워드, Invalid outputs(refusal·max_tokens·enum 대소문자), 복잡도 상한 <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
  - Anthropic "Strict tool use" <https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use> · "Handle tool calls"(`tool_result`·`is_error`·배치 순서) <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
  - OpenAI "Structured Outputs" — JSON mode와 차이, 지원 키워드, 모든 필드 required·`additionalProperties: false`, refusal, incomplete 처리 <https://developers.openai.com/api/docs/guides/structured-outputs>
  - OpenAI "Function calling" — `call_id`·`function_call_output`, 호출 0·1·여러 개, strict 권장, 병렬 호출 <https://developers.openai.com/api/docs/guides/function-calling>
- 논문
  - Schick 외, "Toolformer: Language Models Can Teach Themselves to Use Tools", arXiv 2023-02-09 <https://arxiv.org/abs/2302.04761>
- 실험 목록 (코드: scratchpad `ai/09/Struct14.java`)
  - 최소 JSON 파서 + JSON Schema 부분집합 검증기 + 처리 계약(중단 사유 → 문법 → 스키마 → 업무 규칙), 모형 응답 9종 + 재요청 1회 상한 — `eclipse-temurin:21-jdk`(OpenJDK 21.0.12), `--network none --cpus=2`, 2026-10-08, 2회 실행(출력 동일). 명령: `java Struct14.java`
