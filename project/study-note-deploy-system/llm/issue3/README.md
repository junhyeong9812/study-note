# issue3 — src/app ↔ src/test 미러 구조로 정리하다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/6

---

## 1. 무엇이 문제였나 — "이 코드의 테스트는 어디 있지?"

wrapper 폴더에 코드 파일과 테스트가 평평하게 섞여 있었다. 파일이 몇 개일 땐 괜찮지만
모듈이 늘수록 "이 코드의 테스트가 어디 있지?"를 찾는 비용이 커지고, **테스트가 아예
없는 모듈**이 눈에 안 띈다.

그리고 더 실질적인 통증이 하나 있었다 — 직전 이슈에서 `pytest`를 그냥 실행하면 임포트
에러로 죽는 문제가 있었는데, 임시방편(빈 conftest.py로 경로를 잡던 것)으로 덮어둔 상태였다.
이번에 구조를 잡으면서 그 정체까지 정리하기로 했다.

---

## 2. 무엇을 고민했나

### 갈래 A — tests/ 한 폴더에 테스트 전부 (탈락)

파일 몇 개일 땐 되지만, 커지면 테스트 파일 하나가 모든 모듈을 알게 되어 "무엇이 무엇을
검증하나"가 흐려진다. → 탈락.

### 갈래 B — src/{app, test} 미러 + 모듈별 테스트 분리 (선택)

```
src/app/domain/prompt.py      ↔  src/test/domain/test_prompt.py
src/app/usecase/rewrite.py    ↔  src/test/usecase/test_rewrite.py
src/app/validate.py           ↔  src/test/test_validate.py
src/app/logger.py             ↔  src/test/test_logger.py
(+ src/test/test_api.py — 엔드포인트를 통째로 도는 통합 테스트는 유지)
```

미러의 값어치: 모듈을 열면 테스트 위치가 경로만 봐도 자동으로 정해진다. 테스트가 없는
모듈도 한눈에 드러난다. → B 채택.

---

## 3. 그래서 이렇게 — 기존 ↔ 변경

```
[기존]                          [변경]
wrapper/                        wrapper/
  app.py  api.py  validate.py     pyproject.toml   ← pytest 설정(경로 문제의 정답)
  logger.py                       Dockerfile       ← --app-dir src 로 기동 경로 변경
  domain/  usecase/               src/
  tests/test_api.py                 app/   (패키지 — from app.domain... 절대 임포트)
  conftest.py  (임시방편)            test/  (app의 미러)
```

---

## 4. 코드 — 실제 커밋에서 (`refactor da73064`)

**기동 명령 — 코드 위치가 바뀌었으니** (`wrapper/Dockerfile`):

```diff
-COPY . .
+COPY src ./src
 EXPOSE 8000
-CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
+CMD ["uvicorn", "app.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
```

> 용어 — `--app-dir src`: uvicorn(파이썬 웹서버)에게 "임포트의 기준 폴더는 src다"라고
> 알려주는 옵션. 그래야 `app.app:app`(= src/app/app.py 안의 app 객체)을 찾아 띄운다.

**"테스트가 import를 못 찾는" 문제의 정식 해법** (`wrapper/pyproject.toml` 신규):

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]      # 테스트 실행 시 src를 임포트 경로에 추가
testpaths = ["src/test"]
```

이 설정 덕에 이전의 임시방편이던 빈 conftest.py를 지웠다:

```diff
-wrapper/conftest.py   (빈 파일 — 경로만 잡던 임시방편)
+삭제
```

---

## 5. 구현 중 마주친 문제

### 문제 — `pytest`가 임포트 에러로 죽던 문제의 정체

- **무엇이 문제였나**: pytest를 그냥 실행하면 **테스트 파일이 있는 폴더**만 임포트 경로에
  넣는다. 코드가 옆 폴더에 있으면 `from app import ...`가 못 찾는다.
- **왜 개발 중엔 안 보였나**: `python -m pytest`로 돌리면 현재 폴더가 경로에 들어가
  우연히 통과한다. 그래서 로컬에선 초록불이었다.
- **판정을 어떻게 했나**: 리뷰어 한쪽은 "문제다", 다른 쪽 감사는 "문제 아니다"로 갈렸다.
  말싸움 대신 **직접 실행해 재현**했다 — conftest 없이 pytest를 돌리니 collection error
  발생. "누가 맞는지 따지지 말고 실측한다"가 이 프로젝트의 판정 원칙이다.
- **그래서 이렇게**: 임시방편(conftest) → 이번 이슈에서 pyproject 설정으로 정식화.

---

## 6. 결론

코드는 `src/app` 패키지, 테스트는 그 미러인 `src/test`. 당시 25건 전부 green 유지, 기동은
`--app-dir src`. 이 PR에는 실기동에서 발견된 thinking 폭주 수정(issue1 문서의 문제 3)도
함께 실렸다. PR: #6.
