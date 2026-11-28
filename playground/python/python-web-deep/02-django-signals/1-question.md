# python/python-web-deep/02 — Django 시그널: post_save와 커스텀 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. User 하나를 save 하면 (예측)

```python
# 질문용 발췌
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile(user_id=instance.pk, bio="")
        profile.save()
        print(f"  [시그널] Profile 생성: user_id={instance.pk}")

post_save.connect(create_profile, sender=User)

user = User(name="Alice", email="alice@example.com")
user.save()
```

- `user.save()` 한 번에 `create_profile` 은 몇 번 불리나?
- 안쪽의 `profile.save()` 가 보내는 `post_save` 에 `create_profile` 이 다시 반응하나?
- 찍히는 줄의 `user_id` 값을 실행 전에 알 수 있나?

### 2. 같은 Order 를 두 번 save 하고 delete 하면 (예측)

```python
# 질문용 발췌
@receiver(post_save, sender=Order)
def notify_order(sender, instance, created, **kwargs):
    action = "생성" if created else "수정"
    print(f"  [시그널] 주문 {action}: {getattr(instance, 'item', 'unknown')}")

@receiver(pre_delete, sender=Order)
def log_deletion(sender, instance, **kwargs):
    print(f"  [시그널] 주문 삭제 예정: {getattr(instance, 'item', 'unknown')}")

order = Order(item="Python 책", price=30000)
order.save()
order.price = 25000
order.save()
order.delete()
```

- 세 호출이 차례로 찍는 줄은 무엇인가?

### 3. 결제 완료 시그널 하나에 수신자 셋 (예측)

```python
# 질문용 발췌
payment_completed = Signal()

@receiver(payment_completed)
def send_receipt(sender, order_id, amount, **kwargs):
    print(f"  [영수증] 주문 #{order_id}: {amount}원 결제 완료")

@receiver(payment_completed)
def update_inventory(sender, order_id, **kwargs):
    print(f"  [재고] 주문 #{order_id} 재고 차감")

@receiver(payment_completed)
def notify_seller(sender, order_id, **kwargs):
    print(f"  [알림] 판매자에게 주문 #{order_id} 통보")

payment_completed.send(sender='PaymentService', order_id=1001, amount=50000)
```

- 어떤 줄들이 어떤 순서로 찍히나?
- `amount` 를 매개변수로 두지 않은 두 수신자는 그 인자를 어디서 받나?

### 4. created 를 pk 를 매기기 전에 구하는 까닭 (왜)

- `Model.save()` 는 왜 `created = self.pk is None` 을 pk 를 매기기 전에 계산하나?

### 5. signals.py 를 ready() 에서 임포트하는 까닭 (왜)

- 수신자를 `signals.py` 에 다 써 두었는데도 왜 `apps.py` 의 `ready()` 에서 그 모듈을 임포트해야 하나?

### 6. 수신자에서 **kwargs 를 빼면 (경계)

- `notify_seller` 의 매개변수를 `(sender, order_id)` 로 줄이면 3번의 `send` 는 어디서 깨지나?

### 7. sender 를 지정할 때와 비울 때 (경계)

- `@receiver(post_save)` 처럼 `sender` 를 비우면 어떤 저장에 반응하나?
- `Order` 를 상속한 클래스의 객체를 저장하면 `sender=Order` 로 건 `notify_order` 가 불리나?

### 8. 지운 객체를 다시 save 하면 (경계)

- 2번의 `order.delete()` 뒤에 `order.save()` 를 또 부르면 `notify_order` 가 받는 `created` 는 무엇인가?

### 9. 시그널과 Observer · pub-sub (연결)

- `Signal` 의 `connect` 와 `send` 는 pub-sub 구조에서 각각 무엇에 해당하나?
- 「`User` 코드는 `Profile` 을 모른다」가 디커플링인 까닭은?

### 10. 동기 실행과 Celery (연결)

- 결제 완료 수신자 하나가 메일 보내느라 오래 걸리면 `send` 를 부른 쪽은 어떻게 되나?
- 원본이 「비동기 필요 시 Celery」를 덧붙인 까닭은?

## 실습

### 실습 1. Django 시그널 시스템을 순수 파이썬으로 흉내 내기

**만들 것** — `Signal` 디스패처와 저장 · 삭제 때 시그널을 보내는 `Model` 을 만들고, 빌트인 시그널 수신자와 커스텀 시그널 수신자를 등록해 차례로 발화시킨다.

**준비물** — Django 를 설치하지 않는다. 정답 코드는 Django 시그널을 흉내 낸 순수 파이썬이며 표준 라이브러리 `typing` 만 쓴다.

**요구 조건**

1단계 — `Signal` 클래스

1. `receivers` 리스트에 `(수신자, 거를 발신자)` 쌍을 담는다.
2. `connect(receiver, sender=None, **kwargs)` 는 쌍을 리스트 끝에 붙인다.
3. `disconnect(receiver, ...)` 는 그 함수가 든 쌍을 모두 빼낸다.
4. `send(sender, **kwargs)` 는 거르는 값이 `None` 이거나 `sender` 와 같은 수신자만 `receiver(sender=sender, **kwargs)` 로 부르고, `(수신자, 반환값)` 쌍의 리스트를 돌려준다.

2단계 — 빌트인 시그널과 모델

5. `pre_save` · `post_save` · `pre_delete` · `post_delete` 를 `Signal()` 로 만든다.
6. `Model.__init__` 은 `pk` 를 `None` 으로 두고 키워드 인자를 속성으로 붙인다.
7. `Model.save()` 는 `created` 를 판정하고 → `pre_save` 를 보내고 → 새 객체면 `pk = id(self)` → `post_save` 를 `created` 와 함께 보내고 → `self` 를 돌려준다.
8. `Model.delete()` 는 `pre_delete` 를 보내고 → `pk` 를 `None` 으로 바꾸고 → `post_delete` 를 보내고 → 옛 pk 를 돌려준다.
9. `User` · `Order` · `Profile` 은 `Model` 을 상속만 한다.

3단계 — 빌트인 시그널 수신자

10. `create_profile` 은 `created` 일 때만 `Profile(user_id=..., bio="")` 를 저장하고 생성 줄을 찍으며, `connect` 로 `User` 에만 등록한다.
11. `receiver(signal, sender=None)` 데코레이터 함수를 만든다 — 함수를 등록하고 그대로 돌려준다.
12. `notify_order` 는 `post_save` · `Order` 에 데코레이터로 등록하고 `created` 에 따라 「생성」/「수정」과 `item` 을 찍는다.
13. `log_deletion` 은 `pre_delete` · `Order` 에 등록하고 「삭제 예정」과 `item` 을 찍는다.

4단계 — 실행 시나리오

14. `User(name="Alice", ...)` 를 저장한다.
15. `Order(item="Python 책", price=30000)` 를 저장하고, `price` 를 `25000` 으로 바꿔 다시 저장하고, 삭제한다.

5단계 — 커스텀 시그널

16. `payment_completed` 와 `user_logged_in` 을 만든다.
17. `payment_completed` 에 `send_receipt`(주문 번호 · 금액) · `update_inventory` · `notify_seller` 를 차례로, `user_logged_in` 에 `record_login`(`user_id` · `ip`)을 등록한다.
18. `payment_completed` 를 `sender='PaymentService'`, `order_id=1001`, `amount=50000` 으로, `user_logged_in` 을 `sender='AuthService'`, `user_id=42`, `ip='192.168.1.1'` 로 보낸다.

6단계 — 마무리

19. 실제 Django 코드 패턴 문자열과 핵심 정리 여섯 줄을 찍는다(시작 코드에 채워 둠).

**시작 코드**

```python
"""Django 시그널: 빌트인과 커스텀 시그널"""
from typing import Any, Callable, List


class Signal:
    def __init__(self, providing_args=None):
        # TODO: (수신자, 거를 발신자) 쌍을 담을 리스트
        pass

    def connect(self, receiver: Callable, sender=None, **kwargs):
        # TODO: 쌍을 명단 끝에 붙인다
        pass

    def disconnect(self, receiver: Callable, sender=None, **kwargs):
        # TODO: receiver 가 든 쌍을 모두 뺀다
        pass

    def send(self, sender, **kwargs):
        # TODO: sender 거르기 → receiver(sender=sender, **kwargs) → 결과 모아 반환
        pass


# TODO: 빌트인 시그널 넷 (pre_save, post_save, pre_delete, post_delete)


class Model:
    def __init__(self, **kwargs):
        self.pk = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def save(self):
        # TODO: created 판정 → pre_save → (새 객체면 pk = id(self)) → post_save(created=...)
        return self

    def delete(self):
        # TODO: pre_delete → pk 를 None 으로 → post_delete → 옛 pk 반환
        pass


class User(Model):
    pass

class Order(Model):
    pass

class Profile(Model):
    pass


print("=== 시그널 수신자 등록 ===")

def create_profile(sender, instance, created, **kwargs):
    # TODO: 새로 만든 User 일 때만 Profile 을 저장하고 아래 줄을 찍는다
    # print(f"  [시그널] Profile 생성: user_id={instance.pk}")
    pass

# TODO: create_profile 을 post_save 에 User 한정으로 등록


def receiver(signal, sender=None, **kwargs):
    # TODO: 함수를 signal 에 등록하고 함수를 그대로 돌려주는 데코레이터
    pass


# TODO: notify_order — post_save, Order 한정
#   print(f"  [시그널] 주문 {action}: {getattr(instance, 'item', 'unknown')}")

# TODO: log_deletion — pre_delete, Order 한정
#   print(f"  [시그널] 주문 삭제 예정: {getattr(instance, 'item', 'unknown')}")


print("\n=== 시그널 실행 ===")

print("--- User 생성 ---")
# TODO

print("\n--- Order 생성 ---")
# TODO

print("\n--- Order 수정 ---")
# TODO

print("\n--- Order 삭제 ---")
# TODO


print("\n=== 커스텀 시그널 ===")

# TODO: payment_completed, user_logged_in 만들기

# TODO: send_receipt   → print(f"  [영수증] 주문 #{order_id}: {amount}원 결제 완료")
# TODO: update_inventory → print(f"  [재고] 주문 #{order_id} 재고 차감")
# TODO: notify_seller  → print(f"  [알림] 판매자에게 주문 #{order_id} 통보")
# TODO: record_login   → print(f"  [로그인] user_id={user_id}, ip={ip}")

print("--- 결제 완료 시그널 ---")
# TODO: payment_completed 발송

print("\n--- 로그인 시그널 ---")
# TODO: user_logged_in 발송


print("\n=== Django 실제 코드 패턴 ===")
print("""
# signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User

# 빌트인 시그널
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# 커스텀 시그널
order_completed = Signal()  # providing_args deprecated in 4.0+

@receiver(order_completed)
def handle_completion(sender, order, **kwargs):
    send_email(order.user.email, 'Order Complete', ...)
    update_analytics(order)

# apps.py (시그널 등록)
class MyAppConfig(AppConfig):
    name = 'myapp'
    def ready(self):
        import myapp.signals  # 시그널 모듈 임포트
""")

print("=== 핵심 정리 ===")
print("1. post_save(created=True): 새 객체 생성 시")
print("2. post_save(created=False): 기존 객체 수정 시")
print("3. pre_delete: 삭제 전 정리 작업")
print("4. 커스텀 시그널: Signal() + @receiver로 비즈니스 이벤트")
print("5. apps.py의 ready()에서 signals 모듈을 임포트해야 등록됨")
print("6. 시그널은 동기적으로 실행됨 (비동기 필요 시 Celery)")
```

**확인 방법** — `python django-signals.py` 로 돌린다.
「User 생성」 아래에 Profile 생성 줄이 하나, Order 쪽에 생성 · 수정 · 삭제 예정 줄이 하나씩, 결제 완료 아래에 영수증 · 재고 · 알림 세 줄이 그 순서로, 로그인 아래에 한 줄이 있는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
