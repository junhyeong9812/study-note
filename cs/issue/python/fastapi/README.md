# python/fastapi — FastAPI 응답 경계·기능 표면 패턴

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [response-normalization-framework-boundary](response-normalization-framework-boundary/) | pydantic 검증 실패·404·500은 라우터 진입 전 프레임워크가 자기 형식으로 응답 → 전역 예외 핸들러로 봉투 정규화 | llm4 |
| [yagni-dead-contract](yagni-dead-contract/) | 예측으로 만든 예약 계약은 수요 0·미래 불분명 → 유지비만. YAGNI·제거하되 결정 흔적은 남김 | llm5 |
