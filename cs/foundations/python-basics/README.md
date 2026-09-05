# 파이썬 기본 문법 — 자료구조·제어문·연산자 (컴퓨터사이언스 부트캠프 with 파이썬 보충 노트)

> 원고: computer_science repo의 python_data_structures/ 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.

## 목차

| 원본 파일 | 절 |
|---|---|
| python_data_structures/list.py | 1. 리스트 |
| python_data_structures/dictionary.py | 2. 딕셔너리 |
| python_data_structures/tuple.py | 3. 튜플 |
| python_data_structures/set.py | 4. 집합(set) |
| python_data_structures/operator_example.py | 5. 연산자 |
| python_data_structures/control_flow_statement.py | 6. 제어문 — if/else와 조건 표현식 |
| python_data_structures/for_loop_example.py | 7. for 반복문 예제 |
| python_data_structures/while_loop_example.py | 8. while 반복문 예제 |

## 1. 리스트

출처: `computer_science/python_data_structures/list.py`

```python
a = [1, 2, 3]
a[1] = 4
print(a)  # [1, 4, 3]
```

리스트 안의 값이 변경되었을 때 해당 인덱스의 참조만 변경.

리스트 추가:

```python
a = [1, 2, 3]
a += [4, 5, 6]
print(a)  # [1, 2, 3, 4, 5, 6]
```

이와 같이 리스트 자체가 확장되어 요소가 추가된다.

리스트 삽입:

```python
a = [1, 3, 4]
a[1:1] = [2]
```

이와 같이 1:1 슬라이싱을 통해 2를 삽입하면 3, 4를 밀어내고 그 자리에 2를 삽입한다.

슬라이싱이란 `[start:end]`가 기본 구조로 `[:end]`(처음부터), `[start:]`(끝까지), `[:]`(전체 복사)가 있다. 증감폭(Step): `[::2]`와 같이 사용하여 간격을 두고 추출한다. 역순 슬라이싱 `[::-1]`을 사용하여 요소를 뒤집을 수 있다.

```python
a = [0, 1, 2, 3, 4, 5]
print(a[1:4])   # [1, 2, 3]
print(a[:3])    # [0, 1, 2]
print(a[::2])   # [0, 2, 4]
print(a[::-1])  # [5, 4, 3, 2, 1, 0]
```

이때 삽입하는 객체가 반복자 객체인 경우 — 파이썬의 슬라이스 할당은 지정한 범위를 도려내고 그 자리에 새로운 반복 가능 객체(iterable)를 채워 넣는 방식. `a[1:3] = [9,9]`는 1~2번 자리를 지우고 9,9를 넣는다. `a[1:1] = [9,9]`는 아무것도 지우지 않고 그 자리에 9,9를 넣는다.

리스트 삭제:

```python
a = [1, 2, 3, 4, 5]
a[2:4] = []
print(a)  # [1, 2, 5]
```

이와 같이 빈 리스트로 삭제할 수 있다. 슬라이싱이므로 인덱스 4 즉 end는 포함되지 않는다.

리스트 내장 함수:

```python
a = [1, 2, 3]; a.append(4)        # [1, 2, 3, 4] 추가한다.
a = [1, 2, 3]; a.extend([4, 5])   # [1, 2, 3, 4, 5] 확장한다. 여러 개 추가 가능
a = [1, 3, 4]; a.insert(1, 2)     # [1, 2, 3, 4]
a = [1, 2, 3, 4]; a.clear()       # []
a = [1, 2, 3, 4, 2, 5, 2]; a.remove(2)  # [1, 3, 4, 2, 5, 2] 가장 왼쪽의 2만 지워지는 것을 확인

a = [1, 2, 3, 4, 5, 6]
print(a.pop(2))  # 3
print(a.pop())   # 6
print(a.pop(0))  # 1

a = [1, 2, 3, 2, 2, 2, 2]
print(a.count(2))  # 5

a = [1, 2, 3, 2, 4, 5, 2, 6, 7]
print(a.index(2))     # 1
print(a.index(2, 2))  # 3
print(a.index(2, 4))  # 6
```

index() 메서드 문법 — 기본 형태 `list.index(value, start, end)`. value: 찾고 싶은 값, start: 검색을 시작할 인덱스, end: 검색을 마칠 인덱스 바로 직전까지.

리스트 sort 메서드:

```python
a = [6, 3, 2, 1, 5, 4]
a.sort()             # [1, 2, 3, 4, 5, 6]
a.sort(reverse=True) # [6, 5, 4, 3, 2, 1]

# even_pred: 숫자를 받아 2로 나눈 나머지 반환
def even_pred(num):
    return num % 2

a.sort(key=even_pred)
print(a)  # [6, 4, 2, 5, 3, 1]
```

이렇게 함수의 인자 key를 전달하면 리스트가 각 요소에 대해서 2로 나눈 값으로 1차 정렬하고 그 연산 값으로 정렬한다.

```python
a = [1, 2, 3, 4, 5, 6]
a.sort(key=lambda x: x % 2)
print(a)  # [2, 4, 6, 1, 3, 5] 람다를 통한 간단한 구조
```

리스트 컴프리헨션:

```python
li2 = [e for e in range(1, 101)]
# [1, 2, 3, ..., 100] 이와 같이 반복문으로 바로 생성 가능

li4 = [e for e in range(1, 101) if e % 2 == 0]
# [2, 4, 6, ..., 100]
```

## 2. 딕셔너리

출처: `computer_science/python_data_structures/dictionary.py`

딕셔너리의 요소는 순서가 없고 저장되는 데이터의 키와 값이 쌍을 이룬다. 이처럼 키와 대응되는 형태의 딕셔너리는 map이나 table이라고도 불린다. 값은 중복될 수 있지만 key는 중복될 수 없다.

```python
dic = {}
dic['abc'] = 1
dic[2] = 2
dic[(1, 2, 3)] = 3
print(dic)  # {'abc': 1, 2: 2, (1, 2, 3): 3}
```

```python
# 삽입
dic = {'a': 97, 'b': 98}
dic['c'] = 99   # {'a': 97, 'b': 98, 'c': 99}
# 수정
dic['c'] = 100  # {'a': 97, 'b': 98, 'c': 100}
# 삭제
del dic['c']    # {'a': 97, 'b': 98}
```

딕셔너리의 요소에 접근할 때 [] 연산자를 사용하는데, 키가 딕셔너리 안에 존재하지 않는다면 오류가 나온다. 그렇기에 없는 키에 접근할 때는 get() 메서드를 통해 접근.

```python
dic = {'a': 97, 'b': 98, 'c': 99}
print(dic.get('a'))       # 97
print(dic.get('d'))       # None
print(dic.get('d', 100))  # 100

dic2 = {'d': 100, 'e': 101}
dic.update(dic2)
# {'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101}
```

## 3. 튜플

출처: `computer_science/python_data_structures/tuple.py`

튜플은 리스트와 닮은 점이 많다. 인덱싱과 슬라이싱이 가능하지만 변경 불가능한 객체이다. 변경이 불가능하기에 삽입·변경·삭제 같은 내장 함수는 없고 검색 함수인 count와 index만 존재한다.

```python
tu = (1, 2, 3)
tu2 = 4, 5, 6         # (4, 5, 6)
tu3 = 1, 2, 3, 2, 2
print(tu3.count(2))   # 3
print(tu3.index(2))   # 1
```

## 4. 집합(set)

출처: `computer_science/python_data_structures/set.py`

집합의 요소는 순서가 없고 중복될 수 없다. 집합을 나타낼 때는 딕셔너리처럼 {}를 사용할 수 있지만, 빈 집합은 {}로 만들 수 없고 set()로 할 수 있다.

```python
s = set()
print(s)  # set()
```

## 5. 연산자

출처: `computer_science/python_data_structures/operator_example.py`

```python
print(10/3)    # 3.3333333333333335  / 연산자는 실수형 나눗셈
print(10//3)   # 3                   // 연산자는 정수형 나눗셈
print(2 ** 3)  # 8                   ** 연산자는 거듭제곱
```

논리 연산자:

```python
a = True
print(not a)  # False

a, b = True, False
print(a and b)  # False
print(a or b)   # True
```

파이썬이 거짓으로 판단하는 경우는 "아무것도 아니다"는 파이썬의 내장 객체인 None, 빈 리스트 [], 빈 딕셔너리 {}, 빈 튜플 (), 빈 문자열 "", 정수 0.

```python
print(not [1, 2])        # False
print(not [])            # True
print([1, 2] and [3, 4]) # [3, 4] 참
print([] and [3, 4])     # [] 거짓
```

## 6. 제어문 — if/else와 조건 표현식

출처: `computer_science/python_data_structures/control_flow_statement.py`

```python
import random

def if_else_example():
    rand_num = random.randint(1, 9)
    print("Computer : {}".format(rand_num))

    player_num = int(input("Make a guess(1~9) : "))
    # input() 함수는 표준 입력에서 사용자가 입력한 문자열을 읽어온다.
    print("Player : {}".format(player_num))

    print("You win!" if player_num == rand_num else "You lose!")

def conditional_expression_example():
    a = 4
    print("a > 3" if a > 3 else "a<= 3")
    # a > 3
```

## 7. for 반복문 예제

출처: `computer_science/python_data_structures/for_loop_example.py`

3판 2선승 숫자 맞히기 게임:

```python
result = [None, None, None]

for i in range(3):
    random_num = random.randint(1, 9)
    player_num = int(input("Make a guess(1-9) : "))

    if random_num == player_num:
        result[i] = "player"
    else:
        result[i] = "computer"

if result.count("player") >= 2:
    print("You win!")
else:
    print("You lose!")
```

## 8. while 반복문 예제

출처: `computer_science/python_data_structures/while_loop_example.py`

같은 게임에 입력 검증을 while로 추가:

```python
player_num = input("Make a guess(1~9) : ")
while not player_num.isdigit():
    print("Must be an integer from 1 to 9")
    player_num = input("Make a guess(1~9) : ")

player_num = int(player_num)
```
