# python — Python·FastAPI 이슈 패턴

llm 래퍼(Python + FastAPI)에서 뿌리내린 이슈. 언어(모듈 해석)와 프레임워크(FastAPI 응답 경계) 층을 나눈다.

| 하위 | 무엇 | 패턴 |
|------|------|------|
| (언어레벨) [module-resolution-and-accidental-pass](module-resolution-and-accidental-pass/) | pytest vs `python -m`이 sys.path를 다르게 잡아 초록불이 실행방식에 따라 갈림(우연한 통과) | llm3 |
| [fastapi/](fastapi/) | FastAPI 응답 경계·기능 표면 | 응답 정규화(프레임워크 밖 응답) · YAGNI dead-contract |
