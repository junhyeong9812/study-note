# engineering-practice/03-version-control-and-git-internals — 질문

## 질문

1. (왜) git 커밋은 "변경분"이 아니라 "스냅샷"이라는데, 그러면 커밋마다 저장소 크기가 프로젝트 전체만큼 늘어나지 않는 이유는? 객체 모델의 어떤 성질 두 가지가 이를 막나?
2. (계산) 내용이 `hello\n`(6바이트)인 파일의 git 블롭 ID는 무엇을 해시한 값인가? 파일 이름을 바꾸거나 다른 디렉터리에 복사하면 블롭 ID는 바뀌나?
3. (예측) `a.txt`(hello)·`src/b.txt`(hello)·`src/c.txt`(world)를 첫 커밋한 직후 객체는 몇 개인가? 이어서 `c.txt`만 고쳐 커밋하면 새 객체는 몇 개, 각각 무엇인가?
4. (그림) 3-way 병합의 base·ours·theirs를 그리고, 줄 단위로 "자동 반영"과 "충돌"이 갈리는 조건을 표로 정리하라. base는 커밋 그래프에서 어떤 점인가?
5. (예측) Alice가 원격 `main`을 fetch하지 않은 채 `git push --force-with-lease`를 하면? fetch한 뒤에 같은 명령을 하면? `--force-if-includes`를 더하면?
6. (경계) reflog로 복구할 수 있는 것과 없는 것을 구분하라. bare 원격(서버)에 reflog가 남나? 기본 만료 기간은?
7. (장애 진단) "고친 버그가 재발했다." `git log`에는 수정 커밋이 `main`에 들어가 있고, 수정 브랜치를 다시 병합하면 `Already up to date.`가 나온다. 무슨 일이 있었고, 어떤 명령으로 확인·복구하나?
8. (경계) `git merge -s ours`와 `git merge -X ours`는 무엇이 다른가? 충돌을 `git checkout --ours`로 통째로 고르는 것은 어느 쪽에 가까운가?
9. (연결) 충돌이 하나도 없이 병합됐는데 빌드가 깨질 수 있는 이유는? 3-way 병합이 판정하는 것과 판정하지 않는 것을 나눠 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
