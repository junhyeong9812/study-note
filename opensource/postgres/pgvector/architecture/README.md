# pgvector 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 아직 흐름 문서가 없는 골격 상태다.

기준 커밋: 정해지면 적는다 ([pgvector/pgvector](https://github.com/pgvector/pgvector)). 모든 줄 번호는 그 커밋 기준으로 쓴다.

이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [pgvector](../README.md)

## 흐름 후보

아래는 공식 문서와 로드맵에서 뽑은 **후보**다. 소스를 읽고 진입점을 확인한 흐름만 `flows/` 아래 폴더로 만들고, 진입점 칸에 파일과 줄 번호를 적는다.

| 흐름 | 상태 | 진입점 |
|---|---|---|
| 확장 로드와 vector 타입 | 후보 | - |
| 거리 연산자 | 후보 | - |
| HNSW 빌드 | 후보 | - |
| HNSW 검색 | 후보 | - |
| IVFFlat 빌드와 검색 | 후보 | - |

## 구조

`structure/`(무엇이 있는가)와 `flows/`(무엇이 일어나는가)는 첫 문서를 쓸 때 만든다. 형식은 [Elasticsearch 아키텍처 지도](../../../elasticsearch/architecture/README.md)를 따른다.
