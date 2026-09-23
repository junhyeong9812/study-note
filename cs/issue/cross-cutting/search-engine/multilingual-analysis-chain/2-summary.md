# cs/issue/search-engine/multilingual-analysis-chain — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
입력 ─▶ [char_filter] ─▶ [tokenizer] ─▶ [token filter 1] ─▶ [token filter 2] ─▶ 토큰
         원문 대소문자      단어 경계        정규화              언어별 변환
         그대로 봄          (공백·사전)      (lowercase·folding)  (음차 등)    

[순서]      folding ─▶ 변환     : ü가 u로 사라진 뒤 변환 → ü 규칙 미적용   ✗
            교정: folding(preserve_original) → 원문·폴딩 두 토큰 같은 position
            char_filter는 lowercase보다 먼저 → 매핑에 대소문자 쌍 모두 나열

[비대상 입력]  변환기 fallback = "모르는 문자 → 기본 출력값"
            숫자·타 스크립트 ─▶ "xxx"  (에러 없음, 토큰 파괴)
            + search_analyzer 없음 → 쿼리도 같은 변환 재통과 → 오매칭
            교정: 가드1 루프 내 숫자 skip  +  가드2 진입부 "대상 스크립트 없으면 passthrough"
                  (오버라이드한 서브클래스에도 명시) → 재색인

[혼합 입력]  공백 split만 → "비라틴,영어" 한 토큰 → 부분 변환 → "변환문자,영어"
            → 커스텀 필터 인덱스 계산 붕괴 (변환문자+쉼표 OK, 변환문자+영어 OK, 셋 동시 THROW)
            교정: 남은 라틴 런 음차 + 구분자 공백 정규화 → 필터 입력 불변식(단일 스크립트) 복원

[경계 없는 문자체계]  substring → 짧은 키워드가 긴 단어 내부에 걸림
            교정: 사전 분절기(icu_tokenizer) 서브필드 + match_phrase  (단어 경계 보존)
                  / 1글자 토큰 + match_phrase(연속 부분일치 — 경계는 보장 안 함) + 스크립트 판정 라우팅

[체인 설정]  decompound mixed(그래프) × 다중 단어 동의어 → build 실패 → discard
            BOM·CRLF 파일 → 규칙 문자열 오염 → 빌드 시 인코딩·줄바꿈 정규화
            편집거리 fuzzy × 음절 단위 한글 → 짧은 단어는 AUTO 허용 0 · 허용하면 음절 통째 치환도 거리 1 → edge n-gram, fuzzy는 영문 필드만 또는 1로 제한
```

## 핵심 문장

- 분석기 체인은 **순서가 있는 파이프라인**이다 — 앞 단계가 지운 정보는 뒤 단계가 쓸 수 없다.
- char_filter는 lowercase보다 **먼저** 돈다.
- 변환 필터의 "모르는 입력" 처리는 **원문 통과**여야 한다 — 기본값 덮어쓰기는 에러 없이 토큰을 파괴한다.
- 문자체계마다 **토큰화 전제**가 다르다 — 비대상 스크립트 fallback과 혼합 입력을 명시적으로 처리한다.
- `_analyze`로 재현되지 않으면 **실제 색인 경로의 입력 형태**(전처리·split)를 의심한다.
