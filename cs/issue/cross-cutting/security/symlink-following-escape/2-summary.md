# cs/issue/security/symlink-following-escape — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
요청: ROOT 안의 경로 p 에 파일을 만든다/읽는다/지운다

 [검사]                                  [사용]
 exists(p)      ─ 링크 추종 ─┐           write_text(p) ─ 링크 추종 ─→ 링크 대상에 씀
 is_file(p)                  │           read_text(p)
 최종 성분만 검사            │           mkdir(parents) ─ 중간 링크 추종
                             │           move(tmp, p)   ─ 다른 FS면 copy → 링크 추종
                             ▼
     dangling 링크 → "없음"  ⇒ 검사 통과 ⇒ 쓰기는 ROOT 밖으로   ✗ 탈출
     중간 성분 링크          ⇒ 최종 경로는 멀쩡 ⇒ 실제 위치는 ROOT 밖  ✗ 탈출
     생성 분기만 링크 비추종 ⇒ 갱신 분기로 ROOT 밖 읽기/쓰기          ✗ 탈출
     고정 /tmp 경로           ⇒ 공격자가 미리 둔 링크를 create_dir_all 통과 ✗ 선점

[교정 — 검사와 사용의 링크 의미를 같게]
  판정      : lstat (symlink_metadata / is_symlink) — "링크 자체도 존재"
  생성      : open(p, "x") = O_CREAT|O_EXCL — 검사+생성이 한 syscall (TOCTOU 없음)
  포함 검사 : 전체 경로 resolve → root in 실경로.parents (문자열 prefix 금지)
  모든 분기 : 생성·읽기·갱신·이동 전부 같은 정책 (기존 파일이 링크면 거절)
  이동      : 대상 링크 검사 + 기존 대상 unlink 후 생성, 산출물 확인 후에만 move
  공유 디렉터리: create_dir(원자) + lstat 재검사 + 소유자 + 0700
```

## 핵심 문장

- 링크를 따라가는 API(`exists`·`metadata`·`open("w")`)와 안 따라가는 API(`lstat`·`is_symlink`·O_EXCL)를 **검사와 사용에 섞으면** 그 틈으로 경계를 탈출한다.
- "경로 슬롯이 점유됐나"와 "무엇을 가리키나"는 다른 질문이다 — dangling 링크는 전자엔 "예", 후자엔 "없음".
- 존재 검사 후 생성은 경쟁 창이 남는다 → **O_EXCL로 검사와 생성을 한 syscall**에 묶는다.
- 포함 검사는 최종 성분이 아니라 **전체 경로를 resolve한 실경로**로 한다.
- 링크 정책은 **모든 분기(생성·읽기·갱신·이동·삭제)에 대칭**이어야 한다 — 한 분기만 막으면 다른 분기가 문이 된다.
- 환경에 따라 동작이 갈리는 유틸(`move`: rename vs copy)은 보안 성질도 환경에 따라 갈린다.
