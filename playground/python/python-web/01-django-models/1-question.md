# python/python-web/01 — Django Models (모델 정의) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 초안 글에 `publish()` 를 부르면 (예측)

```python
# 질문용 발췌 — Post 모델은 정리의 것과 같다
post = Post.objects.create(title="첫 글", slug="first", content="본문", author=author)
# … 하루가 지난 뒤 …
post.publish()
```

- `publish()` 뒤 DB 의 `status` 칸에 들어 있는 두 글자는 무엇인가?
- `created_at` · `updated_at` · `published_at` 가운데 `publish()` 때문에 값이 바뀌는 칸은 어느 것들인가?

### 2. 카테고리 셋을 기본 정렬로 읽으면 (예측)

```python
# 질문용 발췌 — Category.Meta.ordering = ['order', 'name']
Category.objects.create(name="python", slug="python", order=1)
Category.objects.create(name="web", slug="web", order=0)
Category.objects.create(name="django", slug="django", order=0)
names = [c.name for c in Category.objects.all()]
```

- `names` 에 이름이 담기는 차례는 어떻게 되나?

### 3. 새 글의 `status` 값 (예측)

```python
# 질문용 발췌
post = Post(title="t", slug="t", content="c", author=author)
a = post.status
b = Post.Status.DRAFT.label
```

- DB 에 저장된다면 `status` 칸에 들어갈 글자는 무엇인가?
- `b` 에 담기는 것은 무엇인가?

### 4. `category` 에 `SET_NULL` 과 `null=True` 를 함께 적은 까닭 (왜)

- `on_delete=models.SET_NULL` 을 쓰면서 `null=True` 를 빼면 왜 안 되나?

### 5. `author` 에 `related_name='posts'` 를 적은 까닭 (왜)

- 작성자 쪽에서 그 작성자의 글을 찾을 때 `related_name` 이 무슨 일을 하나?

### 6. `blank=True` 만 준 칸 (경계)

- `excerpt = models.CharField(max_length=500, blank=True)` 에서 폼으로 비운 값을 받을 수 있나?
- 같은 칸에 DB 의 NULL 을 넣는 것도 허용되나?

### 7. 필드를 하나 더한 뒤 (경계)

- `Post` 에 필드를 더하고 `makemigrations` 만 돌렸을 때 DB 테이블에 그 칸이 생기나?

### 8. `unique_slug_per_date` 제약이 막는 범위 (경계)

- 슬러그가 같고 `published_at` 이 같은 날 오전 9시와 오후 3시인 두 글을 DB 제약이 막나?

### 9. 세 관계 필드와 테이블 구조 (연결)

- `ForeignKey` 의 연결은 어느 테이블에 기록되고, `ManyToManyField` 의 연결은 어디에 기록되나?

## 실습

### 실습 1. 블로그 앱의 `models.py` 만들기

**만들 것** — 카테고리 · 태그 · 작성자 · 게시글 네 모델과 그 관계, `Meta` 옵션, 모델 메서드를 갖춘 `models.py` 를 쓴다.
파일 끝에는 마이그레이션 명령 · `on_delete` 선택지 메모와 핵심 정리를 찍는 `print` 줄을 둔다.

**준비물** — Django 가 깔린 프로젝트(`django-admin startproject mysite` → `python manage.py startapp blog`, `INSTALLED_APPS` 에 `blog` 추가). `ImageField` 를 쓰므로 Pillow 도 필요하다.

**요구 조건**

1단계 — `Category`
1. `name` 은 100자까지의 문자열이며 겹칠 수 없다.
2. `slug` 는 100자까지의 슬러그이며 겹칠 수 없다.
3. `description` 은 긴 텍스트이며 폼에서 비울 수 있고 기본값은 빈 문자열이다.
4. `is_active` 는 불리언이며 기본 `True`, `order` 는 정수이며 기본 `0` 이다.
5. `created_at` 은 처음 만들 때 한 번만, `updated_at` 은 저장할 때마다 지금 시각이 들어간다.
6. `Meta` 에서 보일 이름을 `'카테고리'` / `'카테고리들'` 로, 기본 정렬을 `order` 다음 `name` 오름차순으로, 테이블 이름을 `blog_category` 로 정한다.
7. `__str__` 은 `name` 을 돌려준다.
8. `get_absolute_url` 은 URL 이름 `'category-detail'` 에 `slug` 를 넘겨 경로를 만든다.

2단계 — `Tag` · `Author`
9. `Tag` 는 50자까지의 겹치지 않는 `name` 하나를 가지고, `__str__` 은 그 이름이다.
10. `Author.user` 는 `'auth.User'` 와 일대일이며, 사용자가 지워지면 함께 지워지고, 사용자 쪽에서는 `author_profile` 로 찾는다.
11. `Author` 는 비울 수 있는 `bio`(긴 텍스트) · `website`(URL) · `avatar`(이미지, `avatars/` 아래 업로드)를 가진다.
12. `Author.__str__` 은 사용자의 전체 이름을 돌려준다.

3단계 — `Post`
13. 모델 안에 선택지 `Status` 를 둔다: 초안 `'DF'` · 게시됨 `'PB'` · 보관됨 `'AR'`.
14. `title`(200자) · `slug`(200자, `published_at` 날짜마다 유일) · `content`(긴 텍스트) · `excerpt`(500자, 비울 수 있음)를 가진다.
15. `status` 는 두 글자 문자열이며 `Status` 의 선택지만 받고 기본은 초안이다.
16. `author` 는 `Author` 를 가리키는 다대일 관계로, 작성자가 지워지면 글도 지워지고 역참조 이름은 `posts` 다.
17. `category` 는 `Category` 를 가리키는 다대일 관계로, 카테고리가 지워지면 NULL 이 되며 DB · 폼 모두 비울 수 있고 역참조 이름은 `posts` 다.
18. `tags` 는 `Tag` 와 다대다이며 비울 수 있고 역참조 이름은 `posts` 다.
19. `view_count` 는 0 이상 정수(기본 0), `rating` 은 총 3자리 중 소수 2자리의 소수(기본 0.00)다.
20. `published_at` 은 DB · 폼 모두 비울 수 있는 날짜 시각이고, `created_at` · `updated_at` 은 `Category` 와 같은 규칙이다.
21. `Meta` 에서 기본 정렬을 `published_at` 내림차순으로 하고, `-published_at` 과 `slug` 에 인덱스를 두고, (`slug`, `published_at`) 조합에 이름 `unique_slug_per_date` 의 유일 제약을 건다.
22. `__str__` 은 `title` 을 돌려준다.
23. `publish()` 는 상태를 게시됨으로, `published_at` 을 지금 시각으로 바꾸고 저장한다.

4단계 — 파일 끝
24. 마이그레이션 명령 넷(`makemigrations` · `migrate` · `showmigrations` · `sqlmigrate`)과 `on_delete` 선택지 여섯을 주석으로 적는다.
25. 핵심 정리 제목, `=` 50개 줄, 그리고 필드 타입 · 관계 필드 · Meta 옵션 · 자동 시각 · TextChoices · 마이그레이션 순서를 한 줄씩 `print` 한다.

**시작 코드**

```python
# Django Models - 모델 정의와 관계
# 실행: django-admin startproject mysite && cd mysite && python manage.py startapp blog

# === models.py ===
from django.db import models
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    """카테고리 모델 - 기본 필드 타입 예시"""
    # TODO: name, slug, description, is_active, order, created_at, updated_at

    class Meta:
        pass  # TODO: verbose_name, verbose_name_plural, ordering, db_table

    def __str__(self):
        pass  # TODO

    def get_absolute_url(self):
        pass  # TODO: reverse(...)


class Tag(models.Model):
    """태그 모델 - ManyToMany 관계용"""
    # TODO: name

    def __str__(self):
        pass  # TODO


class Author(models.Model):
    """작성자 모델 - OneToOne 관계 예시"""
    # TODO: user (OneToOne), bio, website, avatar

    def __str__(self):
        pass  # TODO


class Post(models.Model):
    """게시글 모델 - 다양한 관계와 필드"""
    # TODO: class Status(...)

    # TODO: title, slug, content, excerpt, status
    # TODO: 관계 필드 author, category, tags
    # TODO: 숫자 필드 view_count, rating
    # TODO: 날짜 필드 published_at, created_at, updated_at

    class Meta:
        pass  # TODO: ordering, indexes, constraints

    def __str__(self):
        pass  # TODO

    def publish(self):
        pass  # TODO: 상태 변경 + 발행 시각 기록 + 저장


# === Migration 명령어 (터미널) ===
# TODO: 명령 넷

# === on_delete 옵션 ===
# TODO: 선택지 여섯

# TODO: 핵심 정리 print
```

**확인 방법** — `blog/models.py` 로 두고 `python manage.py makemigrations blog` 를 돌려 마이그레이션 파일이 만들어지는지 본다.
`python manage.py sqlmigrate blog 0001` 로 네 테이블 · 중간 테이블 · 인덱스 · 제약이 SQL 에 들어 있는지 읽어 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
