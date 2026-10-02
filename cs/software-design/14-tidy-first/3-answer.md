# software-design/14-tidy-first — 정답

## 정답

### 1. 섞으면 어려워지는 셋

- 리뷰: 동작 변경 몇 줄이 정리 수십·수백 줄에 묻힌다.
- 검증: "정리는 동작을 안 바꿨다"를 따로 확인할 수 없다. 출력이 바뀌어도 정책 때문인지 정리 실수 때문인지 모른다.
- 되돌리기: 동작만 되돌리려 해도 커밋 단위로 정리까지 같이 되돌아간다.

### 2. 되돌릴 수 있음

- Beck "Structure & Behavior"(2021): 둘을 가르는 것은 reversibility다. 추출한 함수는 인라인하면 없던 일이 되지만, 동작 변경의 결과(고객·데이터)는 되돌리기 어렵다.
- 함의: 구조 변경은 가볍게 훑고, 동작 변경은 꼼꼼히 본다. 그러려면 둘이 분리돼 있어야 한다. 서비스 분리처럼 되돌리기 비싼 구조 변경은 예외로 신중히.

### 3. 정리 시점

- 안 함: 이 코드를 다시 만질 일이 없다.
- 먼저: 정리하면 지금 할 동작 변경이 쉬워진다.
- 바로 뒤: 방금 바꾼 곳을 곧 또 바꾼다.
- 나중에 따로: 지금은 시간이 없다(목록에 남긴다).
- 근거 문장: "for each desired change, make the change easy (warning: this may be hard), then make the easy change"(Beck, 2012 트윗. Fowler 2015 글이 인용).
- 네 기준의 세부 표현은 독자 노트로만 확인했다 [?].

### 4. 리뷰 크기

(실험, JDK 21.0.12 temurin, 2026-10-02)

```text
--- mixed-change: 연체료 정리 + 회원 상한 3000
 5 files changed, 21 insertions(+), 23 deletions(-)
--- split-change: 회원 상한 3000
 1 file changed, 2 insertions(+), 1 deletion(-)
```

- 섞은 커밋 44줄(+21/−23), 정책은 2줄. 나눈 쪽 동작 커밋은 3줄(+2/−1) 전체가 정책이다.
- `Lib.java` 삭제 + `LateFees.java` 새 파일로 보여, 상한 줄이 수정(−/+ 쌍)이 아니라 새 파일의 한 줄로 나타났다. 내용이 많이 바뀌어 rename으로 짝지어지지 않았다.

### 5. 지문

```text
@start: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
@split-tidy: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
@split-change: fingerprint=73c1301d  one(40)=3000 guest(40)=5000
@mixed-change: fingerprint=73c1301d  one(40)=3000 guest(40)=5000
```

- 시작과 정리 커밋이 같고(`4cf83b86`), 동작 커밋에서 바뀐다(`73c1301d`, 회원 40일 4,000 → 3,000).
- 정리 커밋의 지문이 시작과 같으므로, 시험한 입력 범위(연체일 −1~80, 회원/비회원, 합계 경로)에서 정리가 동작을 바꾸지 않았음을 보인다.

### 6. revert

```text
--- split: git revert split-change → exit=0, 충돌 0건, 되돌린 파일:  1 file changed, 1 insertion(+), 2 deletions(-)
    javac exit=0
@rev-split: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
--- mixed: git revert mixed-change → exit=0, 충돌 0건, 되돌린 파일:  5 files changed, 23 insertions(+), 21 deletions(-)
    Kiosk.java:2: error: cannot find symbol
    javac exit=1
```

- 나눈 쪽: 1파일만 되돌아가고 컴파일 성공, 지문이 시작 동작으로 돌아왔다.
- 섞은 쪽: 텍스트 충돌 없이 revert됐지만 이름 변경까지 되돌아가, 새 이름을 쓰던 `Kiosk.java`가 컴파일되지 않았다. 정책 줄만 되돌리는 새 커밋을 손으로 만들어야 한다.

### 7. 나누기와 리뷰 옵션

```bash
git add -p                                   # 정리 덩어리만 골라 스테이징
git commit -m "정리: ... (동작 그대로)"
git add -A && git commit -m "동작 변경 ..."
```

- 너무 엉켰으면 변경을 `git stash`로 치우고 정리부터 다시 한다.
- 옵션: `git diff -M`(이름 변경 짝짓기), `git diff --color-moved`(이동만 한 줄 표시), `git diff -w`(공백 변경 무시).

### 8. 2주 지연

- 원인: 정리 범위에 상한이 없었다. 변경을 쉽게 만드는 데 필요하지 않은 정리까지 "온 김에" 붙어 PR이 길어졌고, 오래 열린 만큼 main과 충돌이 쌓였다.
- 대처: 지금 변경에 필요한 정리만 먼저 하고 나머지는 "나중에 따로" 목록으로 뺀다. 정리 PR은 작게 자주 합친다(오래 사는 브랜치의 충돌은 [13-refactoring](../13-refactoring/2-summary.md) 실험 B).

### 9. 경제학

- 시간 가치: 오늘의 가치가 내일보다 크다 → 동작을 먼저 내고 정리를 미루고 싶다.
- 옵션 가치: 구조가 좋으면 내일 할 수 있는 일의 선택지가 늘어난다 → 정리를 먼저 하고 싶다.
- 정리 시점 판단은 이 두 힘의 저울질이다(해석). 다시 안 만질 코드면 옵션 가치가 없으니 안 함.
- Constantine의 등가(독자 노트의 정리 [?]): 소프트웨어 비용 ≈ 변경 비용 ≈ 큰 변경의 비용 ≈ 결합. 큰 변경을 비싸게 만드는 것은 결합의 연쇄다.
