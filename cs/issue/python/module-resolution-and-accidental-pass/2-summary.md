# cs/issue/python/module-resolution-and-accidental-pass — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

**한 문장:** 파이썬의 import는 실행 시점의 `sys.path`에 의존하는데, `python -m pytest`와 `pytest`는 그 경로에 서로 다른 폴더를 넣기 때문에, 코드가 올바른지와 무관하게 **어떻게 실행했느냐가 초록불을 가른다** — 로컬의 우연한 통과가 CI의 실패를 가린다.

```
[같은 코드, 같은 테스트 — 그런데 실행 방식만 다름]

  $ python -m pytest              $ pytest
        │                                │
   sys.path 맨 앞에                  sys.path 맨 앞에
   현재 폴더(CWD) 삽입               테스트 파일이 있는 폴더 삽입
   (파이썬이 -m 실행 시 넣음)        (rootdir 기반 prepend)
        │                                │
   from app import ...              from app import ...
   → CWD에 app/ 있으니 찾음          → 테스트 폴더엔 app/ 없음
        ▼                                ▼
    ✅ 우연히 통과                    ❌ collection error (ImportError)
   (로컬 개발 = 초록불)              (CI·깨끗한 환경 = 빨간불)
```

**뿌리 문제 하나, 실행 경로 둘.** 코드(`app`)와 테스트가 다른 폴더에 있는데 `app`을 절대 import(`from app import ...`)로 부른다. 그러면 "`app`을 어디서 찾을지"가 실행 시 `sys.path`에 달리고, 실행 방식마다 그 경로가 달라 갈린다. 이 뿌리를 **두 실행 경로에서 각각** 못 박아야 한다:

- **런타임(uvicorn)**: `--app-dir src` — "import 기준 폴더는 src다"라고 서버에 알림.
- **테스트(pytest)**: `pyproject.toml`의 `pythonpath = ["src"]` — 테스트 실행 시 src를 경로에 추가.

**임시방편이던 빈 conftest.py.** 테스트 폴더에 빈 `conftest.py`를 두면 pytest가 그 폴더(또는 rootdir)를 경로에 넣어주는 부수효과로 import가 우연히 풀렸다. 하지만 그건 "왜 통하는지"가 우연한 부수효과라 의도가 안 드러난다 → `pyproject`의 `pythonpath`로 **명시적으로** 못 박는 게 정식 해법. 정식화 후 빈 conftest는 삭제.

**판정 원칙 = 실측.** 리뷰어가 "문제다/아니다"로 갈렸을 때, 말싸움 대신 **conftest 없이 pytest를 직접 돌려** collection error를 재현했다. "누가 맞는지 따지지 말고 직접 실행해 재현한다."

**더 큰 함정과의 연결.** "실행 방식이 초록불을 가른다"는 곧 **green 위장** — 초록불이 코드의 정당성이 아니라 실행 환경의 우연을 반영한 것이다. 성공 신호(초록불)를 산출물(어느 환경에서든 재현되는 통과)로 되물어야 한다.

## 핵심 문장

- 파이썬 import는 실행 시점 `sys.path`에 의존한다 — 코드가 옳은지와 별개로 실행 방식이 결과를 가를 수 있다.
- `python -m pytest`는 CWD를, 그냥 `pytest`는 테스트 파일 폴더를 경로에 넣는다 → 코드·테스트가 다른 폴더면 갈린다.
- 우연한 통과(accidental pass)는 실행 환경이 우연히 틀을 맞춰줘 나는 초록불이다 — 환경이 바뀌면 깨진다.
- 뿌리는 하나("app을 어디서 찾나"), 못 박을 실행 경로는 둘(런타임 `--app-dir`, 테스트 `pythonpath`).
- 판정은 말싸움이 아니라 직접 실행해 재현 — green 위장은 실측으로만 갈린다.
