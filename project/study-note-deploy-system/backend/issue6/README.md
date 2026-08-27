# issue6 — 레이어 재편: 암묵적이던 의존 방향을 폴더로 못박다

- 이슈 #11 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/13

## 1. 배경

처음 구조는 기능별 패키지(sync/indexing/search/content)에 Controller·Service·Client가
섞여 있었다. 레이어는 "클래스 이름 관례"로만 존재 — 그래서 리뷰에서 실제 부작용이
나왔다(ES 접근이 두 곳으로 갈라짐, content가 sync 패키지를 역참조). 게이트 리뷰 중
사용자가 지적: "도메인으로 응집도는 높이되 api/service/domain/infra 의존은 확실히
분리해야 하지 않나" — 맞는 지적이라 재편.

## 2. 검토한 방식들

### 선택 — 레이어 4단 (api/usecase/domain/infra), 의존 역전은 안 함

```
api/      Controller·오류핸들러·봉투    (HTTP 관심사)
usecase/  Sync·Indexing·Search·Tree     (흐름 조립)
domain/   Chunker·DocClassifier·TreeBuilder·SearchHit  (순수 로직 — 아무것도 import 안 함)
infra/    Git·ES·Embedding·Llm·RequestLog (바깥 세상)

의존 방향: api → usecase → (domain, infra) · infra → domain 허용 · domain은 무의존
```

- llm 래퍼(app/api/domain/usecase/validate)와 구조 동형 — 리포를 오가도 지도가 같다.
- **의존 역전(도메인이 인터페이스를 소유, infra가 구현)은 도입하지 않았다** — 지금
  usecase가 infra 구체 클래스를 직접 쓴다. 인터페이스 한 겹은 "인프라를 갈아끼울 때"와
  "테스트에서 인프라를 결계 치고 싶을 때" 가치가 생기는데, 지금은 mockk가 구체 클래스를
  그대로 mock해줘서 테스트 격리도 이미 된다. 필요가 생기는 순간에 뽑는다(결정 기록).

### 대안 — 기능별 패키지 유지 + 내부에 레이어 폴더 (탈락)

- 기능 4개×레이어 4단 = 폴더 16개. 이 규모(파일 18개)에 과잉. 파일이 늘어 기능별로
  다시 묶고 싶어지는 날이 오면 그때 재검토.

## 3. 리팩토링 절차 (동작 보존)

```
① 기존 테스트 22건 green 확인 (기준선)
② git mv로 파일 이동 + 패키지 선언·임포트만 수정 — 로직 변경 0
③ 테스트 다시 green + 배포 후 기존 API 응답 그대로 (계약 표면 diff 0)
```

## 4. 구현 중 마주친 문제

### 배포하자 앱이 무한 재시작 — "같은 이름의 빈이 두 개"

**증상**: 배포 후 스모크가 전부 연결 실패(exit code 000). 컨테이너 상태와 로그:

```
$ docker ps -a | grep backend-app
backend-app    Restarting (1) 38 seconds ago

$ docker logs backend-app | grep Caused
Caused by: org.springframework.context.annotation.ConflictingBeanDefinitionException:
  Annotation-specified bean name 'globalErrorHandler'
  for bean class [xyz.junproject.backend.common.GlobalErrorHandler]
  conflicts with existing, non-compatible bean definition of same name and class
  [xyz.junproject.backend.api.GlobalErrorHandler]
```

**진단**: `common.GlobalErrorHandler`와 `api.GlobalErrorHandler`가 **동시에** 존재한다는
얘기인데, 로컬엔 `common/`이 없다(git mv로 옮겼으니). 서버의 소스 디렉토리를 의심 —
배포는 `rsync -a`(복사)였고 **`--delete`가 없었다.** rsync는 "로컬에 있는 걸 복사"만
하지 "로컬에서 사라진 걸 서버에서 지우기"는 `--delete`를 줘야 한다. 서버엔 옛
`common/ sync/ indexing/ search/` 패키지가 유령처럼 남았고, Docker 빌드(`COPY src`)가
옛/새 파일을 전부 컴파일 → Spring이 같은 빈 이름 두 개를 보고 기동 거부.

**수정** (배포 명령):

```diff
-rsync -a -e "ssh -i $K" --exclude .git ... ./ jun@<host>:~/backend/
+rsync -a --delete -e "ssh -i $K" --exclude .git --exclude .env ... ./ jun@<host>:~/backend/
+#        ^^^^^^^^ 로컬에서 사라진 파일을 서버에서도 제거   ^^^^^^^^^^^^ 서버의 배포 설정은 보호
```

`--delete`를 켜면 서버에만 있어야 하는 파일(.env — 시크릿)이 같이 지워질 수 있어서
`--exclude .env`를 함께 추가했다.

**배경**: "복사"만 하는 배포는 **삭제를 전달하지 못한다**. 파일 이동이 큰 리팩토링일수록
잔재가 남는다. 이번엔 Spring이 기동을 거부해줘서(시끄러운 실패) 즉시 잡았지만, 만약
충돌 없는 잔재였다면 옛 코드가 조용히 섞여 돌았을 것 — 시끄러운 실패가 고마운 경우.

## 5. 결론

레이어가 폴더로 강제되고, llm 래퍼와 구조 동형. 22건 green·계약 변화 0. PR: #13
