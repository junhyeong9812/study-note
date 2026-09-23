# cs/issue/data/discriminator-not-shape — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
다형 레코드 스트림
   { role: user,      content: "질문" }            ← 프롬프트
   { role: user,      content: [tool_result ...] }  ← 도구 결과 (user 지만 프롬프트 아님)
   { role: assistant, content: "답" }               ← 답
   { role: system,    content: "..." }              ← 시스템
   { 층: 모델 입력,  content: "<주입 컨텍스트>" }   ← 사용자 발화 아님

[모양으로 분기]
   content 가 문자열?  → 프롬프트   ✗ assistant/system 문자열도 turn 을 엶
   role == user?       → 프롬프트   ✗ 도구 결과도 user
   모델 입력 층 읽기   → 발화       ✗ 주입 컨텍스트·시스템 프롬프트가 발화로 뜸

[판별자로 분기]
   role = message.role ?? record.kind
   프롬프트 = role==user AND content 가 도구 결과 아님
   답       = role==assistant
   층 분리: 대화 = 사용자 가시 이벤트 층, 도구 = 모델 입력 층
   못 읽는 것: 날조하지 않음 → 건너뛰고 카운트

[스키마]
   discriminated union: type 이 분기를 고름 → type 없으면 어느 분기로도 검증 불가 → 필수
```

## 핵심 문장

- 다형 레코드는 **모양(shape)이 아니라 명시적 판별자**(role·type·층)로 해석한다 — 같은 모양이 다른 의미를 가진다.
- "user 레코드 = 프롬프트"는 거짓이다 — 도구 결과도 user 레코드다. 판별자 + 내용 종류를 함께 본다.
- 한 사건을 여러 층으로 이중 기록하는 로그는 **목적에 맞는 층**을 골라 읽는다.
- 판별 유니온 스키마에서 판별자는 **필수**다 — 없으면 어느 분기로도 검증할 수 없다.
- 해석할 수 없는 레코드는 비슷한 종류로 **날조하지 말고** 건너뛰며 센다.
