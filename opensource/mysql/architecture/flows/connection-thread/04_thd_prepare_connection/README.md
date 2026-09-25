# thd_prepare_connection

상위: [연결과 스레드](../README.md)

[03] 이 명령 루프에 들어가기 전에 부르는 **준비 단계의 묶음**이다. 열두 줄뿐이지만 "인증 실패"와 "준비 중 실패"를 다르게 다룬다는 점이 볼거리다. 인증이 실패하면 true 를 돌려주지만, 인증 뒤 준비가 실패하면 false 를 돌려주고 연결에 사망 표시만 해 둔다.

## 위치

`sql` / `sql_connect.cc` L892-L903 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_connect.cc#L892-L903))

## 실제 코드

```cpp
// sql_connect.cc L892-L903
bool thd_prepare_connection(THD *thd) {
  thd->enable_mem_cnt();

  bool rc;
  lex_start(thd);
  rc = login_connection(thd);

  if (rc) return rc;

  prepare_new_connection_state(thd);
  return false;
}
```

## 동작 흐름

```text
 L893  thd->enable_mem_cnt()       m_mem_cnt.enable() (sql_class.h L4867)
                                   연결별 메모리 집계를 켠다
 L896  lex_start(thd)              파서 상태(LEX)를 초기화한다
 L897  rc = [05] login_connection
 L899  rc 가 true 면 그대로 돌려준다    -> [03] L301 aborted_connects++
 L901  [06] prepare_new_connection_state
 L902  return false                     -> [03] L303 명령 루프로
```

`prepare_new_connection_state` 는 `void` 다. 그래서 그 안에서 실패해도 이 함수는 false 를 돌려주고, 실패는 `thd->killed` 로 전달된다.

```text
 반환값과 실제 결과

 return  thd->killed       상황                          [03] 에서 일어나는 일
 true    -                 인증 실패, 호스트 거부 등       aborted_connects++, 루프와 [07] 건너뜀
 false   NOT_KILLED        성공                          명령 루프
 false   KILL_CONNECTION   [06] 압축 컨텍스트 할당 실패   루프를 한 번도 안 돌고 [07] -> [08]
 false   KILL_CONNECTION   [06] init_connect 실행 실패    루프를 한 번도 안 돌고 [07] -> [08]

 마지막 두 줄은 aborted_connects 가 아니라
 end_connection 의 thd->killed 판정으로 Aborted_clients 에 잡힌다 (sql_connect.cc L753-L755)
```

## 결과가 쓰이는 곳

```text
 true
      --> [03] L301 이 aborted_connects 를 올리고 close_connection 으로 간다

 false
      --> [03] L303 의 thd_connection_alive 가 진짜 성공인지 가른다

 켜 둔 메모리 집계
      --> [06] 이 관리자 연결인지에 따라 집계 모드를 정한다 (set_orig_mode)
```

## 다루지 않는 것

`THD::enable_mem_cnt` 와 연결별 메모리 한도(`connection_memory_limit`, sys_vars.cc L3382)의 동작, `lex_start` 가 초기화하는 파서 상태의 세부는 [명령 디스패치](../../command-dispatch/README.md)와 메모리 관리의 곁가지라 요약만 했다.
