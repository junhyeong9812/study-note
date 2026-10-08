# pgvector - 동작 구조 분석

상위: [PostgreSQL](../README.md)

이 폴더는 pgvector(C)의 동작 구조를 소스 기준으로 정리하는 자리다. PostgreSQL 확장으로 벡터 타입과 거리 연산자, 근사 최근접 검색 인덱스(HNSW, IVFFlat)를 더한다. PostgreSQL의 인덱스 접근 메서드(Index AM) 인터페이스에 새 인덱스가 어떻게 끼워지는지를 보여준다.

현재 상태: [아키텍처 지도](architecture/README.md)에 흐름 다섯 편(함수 문서 42편)과 [API 역인덱스](architecture/api-index.md)가 있다. 모든 코드 인용은 기준 커밋의 소스에서 잘라 넣었고 `check-code-blocks.py` 로 대조했다. 작성과 별도의 검증 워커가 줄 번호·예시 계산·기본값을 소스로 다시 대조했다.

## 읽는 기준

- 소스: [pgvector/pgvector](https://github.com/pgvector/pgvector) - 기준 커밋 `v0.8.7` [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876)
- 공식 문서: [pgvector README](https://github.com/pgvector/pgvector#readme)
- PostgreSQL 쪽 인덱스 접근 메서드 흐름과 짝지어 읽는다 ([PostgreSQL 아키텍처 지도](../architecture/README.md))

## 개념 교차표에서 맡는 칸

- 색인: 벡터 색인(HNSW 그래프, IVFFlat 클러스터)
- 확장 구조: 타입·연산자·인덱스 접근 메서드 등록
