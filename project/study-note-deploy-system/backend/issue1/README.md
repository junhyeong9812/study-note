# issue1 — 스캐폴드 + compose: app·ES(nori)·로그 Redis·BGE-M3 한 묶음

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/2

## 1. 배경 (요구사항)

backend는 혼자 돌지 않는다 — 검색엔진(Elasticsearch, 이하 ES), 임베딩 서버(BGE-M3: 글을
숫자 벡터로 바꿔주는 모델), 로그 중앙 큐(Redis)가 같이 떠야 한다. 이 넷을 한 서버(.158)에서
**하나의 compose 파일로 묶어** 기동 순서·상태 확인·재시작 정책을 한 곳에서 관리한다.
그리고 첫 이슈에서 반드시 확인해야 할 **가정**이 있었다: "15GB 메모리 서버에 ES(2GB heap)
+ JVM 앱 + GPU 임베딩 모델이 동시에 올라가는가".

## 2. 검토한 방식들

### 선택 — compose 한 파일, ES는 nori 플러그인을 넣어 직접 빌드

- ES 공식 이미지엔 한국어 형태소 분석기(nori — "낙관적 락을" → "낙관/적/락/을"로 쪼개는
  도구)가 없다. `Dockerfile` 두 줄(`FROM elasticsearch` + `plugin install analysis-nori`)로
  해결 — 우리 색인 설계가 nori를 전제하므로 첫 이슈에서 실증해야 했다.
- BGE-M3는 local-llm 시절 만든 이미지(12.4GB)를 지우지 않고 남겨뒀던 것을 재편입.
  다운로드·빌드 없이 그대로 씀.

### 대안 — 서비스별 따로 compose (탈락)

- 기동 순서(ES가 뜬 뒤 app)와 내부 네트워크(app만 ES에 닿게)를 한 파일에서 표현할 수 없다.
  → 탈락.

### 대안 — ES 대신 경량 검색엔진(Meilisearch 등) (탈락)

- 한국어 형태소 분석 + 벡터 검색(kNN)을 한 엔진에서 — 이 둘을 동시에 성숙하게 제공하는 게
  ES라서. 이미 local-llm에서 검증된 조합이기도 하다. → 탈락.

## 3. 구현 워크플로우

```
docker compose up
  ├─ elasticsearch (nori 빌드, heap 2G)  ── healthcheck: _cluster/health
  ├─ redis (:6379 LAN 노출)              ── healthcheck: redis-cli ping
  ├─ embedding (BGE-M3, GPU)            ── healthcheck: /health/deep (GPU 실추론 1건)
  └─ app (:8090 LAN 노출)  ← depends_on: ES healthy, embedding healthy
        └─ healthcheck: /actuator/health

노출 경계:  LAN에 열리는 건 app :8090 과 redis :6379 뿐.
           ES :9200 · embedding :8080 은 compose 내부 네트워크에서만 (expose) —
           "DB·검색·내부 API는 LAN 안에, 앱 포트만 밖으로"를 컨테이너 수준에서 강제.
```

## 4. 코드 변경 (핵심)

```yaml
# docker-compose.yml — 경계를 포트 선언으로 표현
app:      ports:  ["${BIND_ADDR:?set-in-env}:8090:8090"]   # 밖으로 (LAN 주소 지정 필수)
redis:    ports:  ["${BIND_ADDR:?set-in-env}:6379:6379"]   # 밖으로 — 다른 서버(llm)가 로그를 던짐
elasticsearch: expose: ["9200"]                             # 안으로만
embedding:     expose: ["8080"]                             # 안으로만
```

```dockerfile
# elasticsearch/Dockerfile — 한국어의 전제
FROM docker.elastic.co/elasticsearch/elasticsearch:8.17.3
RUN bin/elasticsearch-plugin install --batch analysis-nori
```

## 5. 구현 중 마주친 문제

### embedding 컨테이너가 영원히 unhealthy — 배포가 멈춤

**증상**: `depends_on: embedding: service_healthy`를 걸어둔 상태에서 배포하자:

```
dependency failed to start: container backend-embedding is unhealthy
```

**진단**: 헬스체크가 왜 실패하는지 실제 실행 기록을 열었다:

```
$ docker inspect backend-embedding --format '{{json .State.Health}}'
Status: unhealthy
ExitCode 1: /bin/sh: 1: curl: not found
ExitCode 1: /bin/sh: 1: curl: not found
ExitCode 1: /bin/sh: 1: curl: not found
```

서버가 아픈 게 아니라 **검사 도구가 없었다** — 우리가 쓴 healthcheck 명령이 `curl`인데,
BGE-M3 이미지(python slim 계열)엔 curl이 안 들어 있다. local-llm 시절 원본 compose를
확인하니 이미 같은 문제를 겪고 python으로 우회해놨었다:

```yaml
# local-llm/servers/embedding/docker-compose.yml (원본)
test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health/deep', timeout=20)\" || exit 1"]
start_period: 300s     # 첫 기동 시 모델 다운로드+로딩 여유
```

**수정**: 원본 방식 그대로 계승(python urllib + `/health/deep` + start_period 300s).
처음에 얕은 `/health`를 봤던 것도 이때 `/health/deep`으로 교정.

**배경**: `/health/deep`이어야 하는 이유는 원본 코드 주석에 실측 사고로 남아 있다 —
"2026-07-31 재부팅 후 컨테이너가 GPU를 잃었는데 /health가 loaded:true를 계속 반환,
docker는 6일 내내 healthy로 표시했고 그 사이 임베딩이 전부 죽어 있었다." 헬스체크는
"프로세스 생존"이 아니라 **계약(추론 가능)**을 검증해야 한다. 그리고 남이 만든 이미지에
healthcheck를 붙일 땐 그 이미지에 검사 도구가 있는지부터.

## 6. 결론

4개 컨테이너 기동, nori 형태소 분석 동작, Redis PONG, 메모리 5.3GB 사용/10GB 여유(가정
실증). 그리고 뜻밖의 관통 테스트 — .164의 llm 래퍼에 `LOG_REDIS_URL`을 넣자 로그 한 줄이
.158 Redis Stream에 규약 포맷(`logtest-1:llm-wrapper:rewrite ok 3485ms`)으로 도착했다.
서버 두 대를 가로지르는 로그 파이프라인이 이 시점에 살아났다. PR: #2
