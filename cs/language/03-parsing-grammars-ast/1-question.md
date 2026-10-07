# language/03-parsing-grammars-ast — 질문

## 질문

1. (왜) 정규식(유한 오토마타)으로 `((((1))))` 같은 괄호 짝을 검사할 수 없는 이유는? 무엇을 하나 더 주면 되나?
2. (그림) `expr ::= term (('+'|'-') term)*`, `term ::= factor (('*'|'/') factor)*`, `factor ::= NUMBER | '(' expr ')'` 문법으로 `3+5*2`와 `(3+5)*2`의 AST를 그려라. 곱셈이 먼저 묶이는 이유를 문법의 층으로 설명하라.
3. (예측) `8-3-2`를 세 문법 (A) `term ('-' term)*`, (B) `term '-' expr | term`, (C) `expr '-' term | term`으로 재귀 하강 파싱하면 각각 무엇이 나오나?
4. (그림) 재귀 하강 파서가 `((1))`을 읽는 도중의 호출 스택을 그려라. 중첩 깊이 d와 프레임 수의 관계는?
5. (예측) 기본 스레드 스택(JDK 21 Linux/x64)에서 `(`ᵈ`1)`ᵈ를 d=1,000·5,000·50,000으로 넣으면? `-Xss8m`이면? 깊이 상한 256을 두면?
6. (경계) 같은 `[`ᵈ`]`ᵈ를 CPython 3.12 `json.loads`와 node 22 `JSON.parse`에 넣으면 어떻게 다른가? 이 차이에서 얻는 교훈은?
7. (연결) 파스 트리와 AST는 무엇이 다른가? 실제 파서는 대개 어느 것을 만드나?
8. (장애 진단) 수십 KB짜리 JSON 요청 하나로 워커가 `StackOverflowError`로 죽었다. `catch (Exception e)`로 감쌌는데 왜 안 잡혔나? 근본 대처는?
9. (장애 진단) 앞단은 `role` 파라미터를 Python `dict(parse_qsl(...))`로 검사하고 뒷단은 node `URLSearchParams.get`으로 읽는다. `role=user&role=admin`이 오면? HTTP의 `Content-Length`·`Transfer-Encoding` 문제와 어떤 점이 같은 구조인가?
10. (연결) RFC 8259는 JSON 중복 키와 중첩 깊이에 대해 무엇이라 적나? Jackson에서는 어떤 설정으로 대응하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
