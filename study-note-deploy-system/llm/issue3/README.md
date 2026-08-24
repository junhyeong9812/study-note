# issue3 — src/app ↔ src/test 미러 구조

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/6

## 1. 배경 (요구사항)

wrapper 폴더에 코드 파일들과 테스트가 평평하게 섞여 있었다. 모듈이 늘수록
"이 코드의 테스트는 어디 있지?"를 찾는 비용이 커진다. 코드를 `src/app` 아래로
모으고, 테스트를 **같은 모양(미러)**으로 `src/test`에 두면 대응 관계가 경로만
봐도 드러난다.

## 2. 검토한 방식들

### 선택 — src/{app, test} 미러 + 모듈별 테스트 분리

```
src/app/domain/prompt.py      ↔  src/test/domain/test_prompt.py
src/app/usecase/rewrite.py    ↔  src/test/usecase/test_rewrite.py
src/app/validate.py           ↔  src/test/test_validate.py
src/app/logger.py             ↔  src/test/test_logger.py
(+ src/test/test_api.py — 엔드포인트를 통째로 도는 통합 테스트는 유지)
```
- 미러의 값어치: 모듈을 열면 테스트 위치가 자동으로 정해진다. 테스트가 없는
  모듈도 한눈에 보인다.

### 대안 — tests/ 한 폴더에 전부 (탈락)

- 파일 몇 개일 땐 되지만, 커지면 테스트 파일 하나가 모든 모듈을 알게 되어
  "무엇이 무엇을 검증하나"가 흐려진다. → 탈락.

## 3. 구현 워크플로우 (기존 → 변경)

```
[기존]                          [변경]
wrapper/                        wrapper/
  app.py  api.py  validate.py     pyproject.toml   ← pytest 설정(경로 문제의 정답)
  logger.py                       Dockerfile       ← --app-dir src 로 기동 경로 변경
  domain/  usecase/               src/
  tests/test_api.py                 app/   (패키지 — from app.domain... 절대 임포트)
  conftest.py                       test/  (app 미러)
```

## 4. 코드 변경 (diff와 맥락)

```diff
# Dockerfile — 코드 위치가 바뀌었으니 기동 명령도
-CMD ["uvicorn", "app:app", ...]
+CMD ["uvicorn", "app.app:app", "--app-dir", "src", ...]
```

```toml
# pyproject.toml — "테스트가 import를 못 찾는" 문제의 정식 해법
[tool.pytest.ini_options]
pythonpath = ["src"]      # 테스트 실행 시 src를 임포트 경로에 추가
testpaths = ["src/test"]
```

이 설정 덕에 이전의 임시방편(빈 conftest.py로 경로를 잡던 것)을 지웠다.

## 5. 구현 중 마주친 문제

### 문제 — (직전 이슈에서) `pytest` 명령이 임포트 에러로 죽는 문제의 정체

- **원인(워크플로우)**: pytest를 그냥 실행하면 **테스트 파일이 있는 폴더**만
  임포트 경로에 넣는다. 코드가 옆 폴더에 있으면 `from app import ...`가 못 찾는다.
  (`python -m pytest`로 돌리면 현재 폴더가 경로에 들어가 우연히 통과 — 그래서
  개발 중엔 안 보였다. 리뷰어 한쪽은 "문제다", 다른 쪽 감사는 "문제 아니다"로
  갈렸고, **직접 실행해보고 판정**했다: conftest 없으면 collection error 재현.)
- **수정**: 임시방편(conftest) → 이번 이슈에서 pyproject 설정으로 정식화.
- **배경**: "누가 맞는지 말싸움 말고 실측"이 이 프로젝트의 판정 원칙.

## 6. 결론

코드는 `src/app` 패키지, 테스트는 그 미러. 25건(당시) 전부 green 유지, 기동은
`--app-dir src`. 이 PR에 실기동에서 발견된 thinking 폭주 수정(issue1 문서의
문제 3)도 함께 실렸다. PR: #6
