# issue1 — 스캐폴드 + compose: app·ES(nori)·로그 Redis·BGE-M3 한 묶음

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/2

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "선택 / 대안 탈락" 세 줄 요약    ──▶     각 갈림길마다: 무엇이 문제였나
>                                          → 무엇을 고민했나 → 그래서 이렇게
> compose를 글로 설명            ──▶     실제 커밋(62c6928)의 compose를 그대로 인용
> 헬스체크 문제를 서술로만        ──▶     [기존 healthcheck] ↔ [변경 healthcheck]
>                                          diff를 나란히 (0ef4b29 실제 커밋)
> nori·바인딩 용어 던짐          ──▶     그 자리에서 한 줄 풀이
> ```
> 표현도 순화: "박아뒀다" → "명시했다".

---

## 1. 배경 — 왜 "한 묶음"이어야 했나

backend는 혼자 돌지 않는다. 검색 화면 하나가 뜨려면 네 개의 프로세스가 동시에 살아 있어야 한다.

> 용어 — 각 프로세스가 하는 일
> - **app**: Spring Boot 애플리케이션(자바 계열 웹 서버). `:8090`으로 front의 요청을 받는다.
> - **ES(Elasticsearch)**: 검색엔진. 문서를 색인해두고 질의에 맞는 것을 찾아준다.
> - **embedding(BGE-M3)**: "글을 숫자 벡터로 바꿔주는" 모델 서버. 의미 기반(벡터) 검색의 재료를 만든다.
> - **Redis**: 로그를 한곳에 모으는 중앙 큐(스트림). 여러 서버가 로그 한 줄씩 던져 넣는다.

이 넷을 한 서버(.158)에 올리는데, 문제는 **기동 순서와 네트워크 경계**다. ES가 아직 안 떴는데
app이 색인을 시도하면 실패한다. embedding이 모델을 다 못 올렸는데 app이 벡터를 요청하면 거부당한다.
그리고 ES·embedding 같은 내부 엔진이 LAN(사내망)에 그대로 노출되면 안 된다. 이 세 가지 —
**순서·상태 확인·노출 경계** — 를 한곳에서 관리하려면 서비스별로 흩어진 설정이 아니라
**하나의 `docker-compose.yml`**가 필요했다.

그리고 첫 이슈에서 반드시 실증해야 할 **가정**이 하나 있었다: "15GB 메모리 서버 한 대에
ES(heap 2GB) + JVM 앱 + GPU 임베딩 모델을 동시에 올려도 버티는가." 이게 안 되면 설계 전체를
다시 그려야 하므로, 착수 직후 스모크로 먼저 확인할 대상으로 잡아뒀다.

---

## 2. 갈림길마다의 판단

### 갈림길 (1) — 서비스별 따로 compose vs. 한 파일로 묶기

**무엇이 문제였나:** 처음엔 "ES는 ES compose, app은 app compose" 식으로 서비스마다 파일을
나누는 게 깔끔해 보였다. 각자 독립적으로 켜고 끌 수 있으니까.

**무엇을 고민했나:** 그런데 "ES가 healthy가 된 뒤에 app을 띄운다"는 순서를, 파일이 나뉘어
있으면 표현할 방법이 없다. `depends_on`(어느 서비스가 먼저 떠야 하는지 선언하는 도커 컴포즈 기능)은
**같은 compose 파일 안의 서비스끼리만** 걸린다. 내부 네트워크(app만 ES에 닿게 하고, ES는 밖으로
안 열기)도 한 파일이어야 한 네트워크로 묶여 표현된다.

**그래서 이렇게 했다:** 네 서비스를 **하나의 compose 파일**에 넣었다. 순서는 `depends_on`으로,
경계는 `ports`(밖으로 열기) vs `expose`(내부에서만 보이기)로 한곳에서 선언한다.

### 갈림길 (2) — ES 대신 경량 검색엔진을 쓸까

**무엇이 문제였나:** ES는 무겁다(heap 2GB를 잡아먹는다). Meilisearch 같은 가벼운 검색엔진을 쓰면
메모리 여유가 생긴다.

**무엇을 고민했나:** 하지만 우리가 필요한 건 두 가지를 **한 엔진**에서 하는 것이다 —
① 한국어 형태소 분석(문장을 의미 단위로 쪼개기)과 ② 벡터 검색(kNN). 경량 엔진들은 이 둘 중
하나가 미성숙하다. 두 엔진을 따로 두면 색인·질의를 두 번 하고 결과를 합쳐야 한다.

**그래서 이렇게 했다:** ES로 간다. 이미 local-llm 프로젝트에서 이 조합(nori + kNN)을 검증한
전례가 있어 위험이 낮다.

> 용어 — nori: ES용 한국어 형태소 분석기. "낙관적 락을"을 그냥 통글자로 두지 않고
> "낙관 / 적 / 락 / 을"처럼 의미 단위로 쪼개, 한국어 검색이 제대로 걸리게 한다.

**부수 결정 — nori는 직접 빌드:** ES 공식 이미지엔 nori가 없다. 그래서 공식 이미지 위에 nori만
얹은 얇은 `Dockerfile`을 만들었다. 우리 색인 설계가 nori를 전제하므로 첫 이슈에서 실제로 빌드가
되는지 확인해야 했다.

`elasticsearch/Dockerfile` (커밋 62c6928):
```dockerfile
FROM docker.elastic.co/elasticsearch/elasticsearch:8.17.3
# 한국어 형태소 분석기 — es-index.md D4의 nori analyzer 전제
RUN bin/elasticsearch-plugin install --batch analysis-nori
```

### 갈림길 (3) — BGE-M3 이미지를 새로 만들까, 있던 걸 재활용할까

**무엇이 문제였나:** 임베딩 모델(BGE-M3) 이미지는 12.4GB로 크다. 새로 빌드하면 모델 다운로드에
시간이 오래 걸린다.

**그래서 이렇게 했다:** local-llm 시절 만들어 놓고 지우지 않은 이미지가 .158에 그대로 남아 있었다.
다운로드·빌드 없이 그 이미지(`embedding-embedding:latest`)를 **재편입**했다. compose에서
`build`가 아니라 `image`로 참조만 한다.

---

## 3. 노출 경계 — 포트 선언으로 담을 세운다

핵심은 "어느 포트가 LAN 밖으로 열리고, 어느 포트가 내부 전용인가"를 compose가 강제하게 만든 것이다.

```
docker compose up
  ├─ elasticsearch (nori 빌드, heap 2G)  ── expose 9200  → 내부 전용
  ├─ redis (:6379)                        ── ports  6379  → LAN (타 서버가 로그 XADD)
  ├─ embedding (BGE-M3, GPU)              ── expose 8080  → 내부 전용
  └─ app (:8090)  ← depends_on: ES healthy, redis started, embedding healthy
        └─ ports 8090 → LAN (front가 호출)

노출 경계:  LAN에 열리는 건 app :8090 과 redis :6379 뿐.
           ES :9200 · embedding :8080 은 compose 내부 네트워크에서만(expose) —
           "DB·검색·내부 API는 LAN 안에, 앱 포트만 밖으로"를 컨테이너 수준에서 강제.
```

> 용어 — `ports` vs `expose`: `ports: ["6379:6379"]`는 호스트(=LAN)에도 그 포트를 연다.
> `expose: ["9200"]`은 **같은 compose 네트워크 안의 다른 컨테이너에게만** 보이게 하고
> 호스트엔 안 연다. 즉 expose된 ES는 app에서는 닿지만 LAN의 다른 기계에서는 닿지 않는다.

실제 compose (커밋 62c6928, `docker-compose.yml`):
```yaml
services:
  app:
    build: .
    container_name: backend-app
    ports:
      - "8090:8090"          # LAN — front가 호출
    depends_on:
      elasticsearch:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      # localhost 금지 — 컨테이너 안에서 ::1로 풀려 IPv4 바인딩 서버가 unhealthy로 찍힘
      test: ["CMD-SHELL", "curl -fsS -m 5 http://127.0.0.1:8090/actuator/health || exit 1"]

  elasticsearch:
    build: ./elasticsearch
    expose:
      - "9200"               # 내부 전용 — 호스트·LAN 비노출 (경계: 앱만 엣지에)
    environment:
      ES_JAVA_OPTS: "-Xms2g -Xmx2g"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"          # LAN — llm(.164) 등 타 호스트가 XADD

  embedding:
    image: embedding-embedding:latest   # local-llm에서 보존한 BGE-M3 이미지 (.158 로컬)
    expose:
      - "8080"               # 내부 전용 — backend만 호출
```

> 참고: 이후 issue5(보안 리뷰)에서 `ports`의 바인딩 주소를 `${BIND_ADDR:?}:8090:8090`처럼
> LAN IP로 못 박는 fail-closed 하드닝을 추가한다. 이 시점(스캐폴드)에서는 아직 `8090:8090`이다.

---

## 4. 구현 중 마주친 문제 — embedding 컨테이너가 영원히 unhealthy

**상황:** embedding이 준비되기 전에 app이 벡터를 요청하지 않도록 `depends_on: embedding:
service_healthy`(embedding이 healthy가 될 때까지 app 기동을 미룸)를 걸었다. 그런데 배포하자
app이 영영 안 떴다:

```
dependency failed to start: container backend-embedding is unhealthy
```

**진단:** embedding이 정말 아픈지, 아니면 검사(healthcheck)가 잘못된 건지부터 갈랐다.
헬스체크의 실제 실행 기록을 열어봤다:

```
$ docker inspect backend-embedding --format '{{json .State.Health}}'
Status: unhealthy
ExitCode 1: /bin/sh: 1: curl: not found
ExitCode 1: /bin/sh: 1: curl: not found
```

서버가 아픈 게 아니라 **검사 도구가 없었다.** 우리가 쓴 healthcheck 명령이 `curl`인데,
BGE-M3 이미지(python slim 계열)엔 curl이 안 들어 있다. curl이 없으니 명령이 매번 실패하고,
도커는 그걸 "서비스가 아프다"로 해석한 것이다.

**무엇을 고민했나:** curl을 이미지에 설치하는 방법도 있지만, local-llm 시절 원본 compose를 열어
보니 **이미 같은 문제를 겪고 python으로 우회해둔 전례**가 있었다. 남이 검증한 방식을 그대로
계승하는 게 안전하다.

**어떻게 고쳤나:** 헬스체크를 curl에서 python `urllib`(파이썬 표준 라이브러리의 HTTP 호출 도구)로
바꾸고, 확인 대상도 얕은 `/health`에서 **`/health/deep`**(GPU로 실제 추론을 1건 돌려보는 깊은 검사)로
올렸다. 모델 로딩 시간을 감안해 `start_period`(기동 직후 이 시간 동안의 실패는 unhealthy로 세지 않음)를
300초로 뒀다.

`docker-compose.yml` embedding 헬스체크 (커밋 0ef4b29):
```diff
     healthcheck:
-      # /health/deep — GPU 실추론 확인. 얕은 /health는 GPU 유실을 못 잡았던 실측 이력
-      test: ["CMD-SHELL", "curl -fsS -m 25 http://127.0.0.1:8080/health/deep || exit 1"]
-      interval: 30s
-      timeout: 10s
-      retries: 3
+      # 이미지에 curl 없음 → python urllib (local-llm 원본 방식). 매 체크가 GPU 추론 1건이라 간격 60s.
+      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health/deep', timeout=20)\" || exit 1"]
+      interval: 60s
+      timeout: 25s
+      retries: 5
+      start_period: 300s     # 모델 로딩 여유
```

**왜 `/health/deep`이어야 하나 (원본 코드에 남은 실측):** local-llm 원본 주석에 사고 이력이
기록돼 있었다 — "2026-07-31 재부팅 후 컨테이너가 GPU를 잃었는데 얕은 `/health`는 `loaded:true`를
계속 반환했고, 도커는 6일 내내 healthy로 표시했다. 그 6일간 임베딩은 전부 죽어 있었다."
헬스체크는 "프로세스가 살아 있나"가 아니라 **"약속한 일(추론)을 실제로 하나"**를 검사해야 한다는
교훈이다. 그리고 남이 만든 이미지에 healthcheck를 붙일 땐 **그 이미지에 검사 도구가 들어 있는지부터**
확인해야 한다.

---

## 5. 결론

네 컨테이너 기동, nori 형태소 분석 동작, Redis `PONG` 응답, 메모리 5.3GB 사용 / 약 10GB 여유 —
1장의 가정("15GB에 셋 다 올라가는가")이 실증됐다. 그리고 뜻밖의 관통 테스트가 하나 붙었다:
.164의 llm 래퍼에 `LOG_REDIS_URL`을 넣자, 로그 한 줄이 .158의 Redis Stream에 규약 포맷
(`logtest-1:llm-wrapper:rewrite ok 3485ms`)으로 도착했다. **서버 두 대를 가로지르는 로그
파이프라인이 이 시점에 살아났다.** PR: #2
