# ai-engineering/14-structured-output-and-tool-calling — 정답

## 정답

### 1. 세 단계의 보장

| 방법 | 보장 |
|---|---|
| 프롬프트로 부탁 | 없음 — 대개 맞지만 필드 누락·타입 불일치·설명 문장이 섞일 수 있다 |
| JSON mode | 문법상 올바른 JSON(일부 예외는 직접 감지 — OpenAI 가이드) |
| 스키마 강제 | 스키마 준수 — 단 거부·잘림 등 예외가 있다(문항 3) |

- OpenAI "Structured Outputs" 가이드: JSON mode와 Structured Outputs 둘 다 올바른 JSON을 내지만, 스키마 준수는 Structured Outputs만 보장한다(2026-10-08 확인).

### 2. 제약 디코딩 한 단계

```text
 지금까지 출력  {"amount":
 문법 상태      정수의 첫 글자 대기
 모델 확률      '"' 0.40  '3' 0.35  '삼' 0.15  '1' 0.10      (예시)
 마스크         ✗         ✓         ✗          ✓
 재정규화        '3' 0.78  '1' 0.22  → 이 안에서 샘플링
```

- 스키마를 문법(상태 기계)으로 바꾸고, 토큰마다 허용되지 않는 토큰의 확률을 0으로 만든 뒤 샘플링한다. Anthropic 문서는 이를 grammar-constrained sampling이라 부른다. 그림은 개념 설명이고 제공자 내부 구현은 공개 범위 밖이다.

### 3. 스키마 강제 뒤에도 남는 것

- 거부: HTTP 200, 출력이 스키마와 안 맞을 수 있음(Anthropic `stop_reason: "refusal"`, OpenAI `refusal` 필드).
- 출력 한도에 잘림: 스키마와 안 맞을 수 있음(Anthropic `max_tokens`, OpenAI Responses `incomplete`, Chat Completions `length`).
- 지원하지 않는 키워드: API가 강제하지 않는 제약.
- enum 대소문자: Anthropic 문서는 대소문자를 보장하지 않는다고 적는다.
- 업무 규칙·권한: 스키마는 소유권·상태를 모른다.
- 숫자 범위: Anthropic Structured outputs 문서는 `minimum`·`maximum`·`multipleOf` 같은 수치 제약을 지원하지 않는다(쓰면 400)고 적는다. OpenAI 가이드는 `minimum`·`maximum`을 지원 목록에 둔다(미세조정 모델은 미지원). Anthropic 쪽에서는 범위 검사가 앱에만 있다.

### 4. 실험 세 경우

| 경우 | 순진한 코드 | 계약 코드 |
|---|---|---|
| 필드 누락 | `amount=0`으로 "환불 0원" 실행 | `REASK` — `$: required 'amount' 없음` |
| 타입 불일치 | 문자열 `"3000"`을 그대로 넘김(하류에서 나중에 터짐) | `REASK` — `$.amount: type integer 기대, 실제 string` |
| 남의 주문 | `cancel o-99` 실행 | `REJECT_FORBIDDEN` — 소유권 확인에서 막음 |

- 스키마로 막을 수 없는 것은 **남의 주문**이다. 형식은 완벽하고, 소유권은 서버 데이터와 대조해야만 안다.

### 5. 중단 사유가 먼저인 이유

- 잘린 출력과 거부는 처리 방법이 다르다.
  - 잘림: 한도를 올려 다시 요청하거나 요청을 쪼갠다.
  - 거부: 같은 요청을 다시 보내도 대개 같다. 재시도 없이 다른 경로(안내·사람 검토)로 보낸다.
- 둘 다 파싱 예외로만 보면(실험의 순진한 코드는 둘 다 `IllegalArgumentException`) "파싱 실패 → 재요청" 규칙이 거부에도 적용돼 재요청이 상한까지 반복되고 비용만 쌓인다.
- 잘린 JSON을 관대한 파서로 닫아 쓰면 뒷부분이 조용히 사라진다.

### 6. JSON Schema 기본값

- `additionalProperties` 생략 = 빈 스키마와 같은 동작(Core 10.3.2.3) → 정의 밖 속성을 **허용**한다. 막으려면 `false`를 명시한다(OpenAI Structured Outputs는 모든 객체에 `false`를 요구한다).
- `3000.0`은 integer에 **맞는다**. Validation 6.1.1: integer는 소수부가 0인 수와 맞는다. 언어의 정수 타입과 같은 뜻이 아니다.

### 7. 배포 직후 첫 요청 타임아웃

- 원인: 새 스키마의 첫 요청은 문법 컴파일로 지연이 길다. Anthropic 문서: 컴파일된 문법은 마지막 사용부터 24시간 캐시되고, 스키마 구조나 도구 집합이 바뀌면 무효가 된다(이름·설명만 바꾸면 유지).
- 대처: 배포 때 워밍업 요청, 첫 요청의 첫 토큰 타임아웃을 넉넉히([11](../11-llm-api-client-contract/2-summary.md)).
- 매일 조금씩 바꾸면 그때마다 캐시가 무효가 되어 첫 요청 지연이 매일 반복된다. 스키마 변경을 묶고 버전으로 관리한다.

### 8. 남의 주문 취소

- 막았어야 할 곳: 도구 구현 안(서버). strict 모드는 형식만 보장하고, 어떤 ID가 이 사용자 것인지는 모른다.
- 확인 순서
  1. 도구 이름이 허용 목록에 있나
  2. 인자 스키마 검증
  3. 대상 레코드가 존재하나
  4. 소유권 — **세션의 사용자**와 대조(모델 출력·프롬프트 속 사용자 ID가 아니다)
  5. 상태 전이가 가능한가(이미 배송됨 등)
  6. 부작용이면 멱등 키, 고위험이면 사람 확인
  7. 실패는 `is_error: true` 같은 오류 결과로 모델에 돌려준다

### 9. 짝 맞추기와 실패 결과

- Anthropic: `tool_use` 블록의 `id` ↔ `tool_result`의 `tool_use_id`. `tool_result`는 해당 `tool_use` 바로 다음 user 메시지의 맨 앞에 둔다. 실행 실패는 `is_error: true`와 오류 내용.
- OpenAI: Responses API는 `call_id` ↔ `function_call_output`의 `call_id`, Chat Completions는 `tool_call_id`. 응답 하나에 호출이 여러 개 올 수 있다.
- 형식 이름은 벤더 고유이고, "모델은 제안, 앱이 검증 후 실행, 결과를 짝 ID로 돌려줌"이 공통 구조다.

### 10. 대소문자만 다른 enum

- 원인: 제공자가 enum·const의 대소문자를 보장하지 않는다(Anthropic Structured outputs 문서 — 정상 완료, 오류·특별 중단 사유 없음).
- 대처: 대소문자를 무시해 비교·정규화한 뒤 스키마를 다시 검증한다(실험의 "enum 대소문자" → `ACCEPT`). 대소문자만 다른 enum 값을 스키마에 두지 않는다. `switch`의 기본 분기를 조용한 처리로 두지 말고 오류로 만든다.
