# python/python-web/04 — Django Forms (폼 처리) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 숫자만 든 이름과 한 글자 이름 (예측)

```python
# 질문용 발췌 — ContactForm 은 원본 그대로
base = {'email': 'a@b.com', 'subject': 'general',
        'message': '문의 내용을 충분히 적었습니다', 'agree': 'on'}
f1 = ContactForm(data={**base, 'name': '007'})
f2 = ContactForm(data={**base, 'name': 'a'})
f1.is_valid(); f2.is_valid()
```

- `f1` 과 `f2` 의 `name` 칸 오류는 각각 어느 검사 단계에서 생기나?
- `clean_name()` 은 두 폼 가운데 어느 쪽에서 불리나?

### 2. 버그 리포트를 스무 글자로 보내면 (예측)

```python
# 질문용 발췌 — ContactForm 은 원본 그대로
f = ContactForm(data={'name': '홍길동', 'email': 'a@b.com', 'subject': 'bug',
                      'message': 'x' * 20, 'agree': 'on'})
ok = f.is_valid()
```

- `ok` 의 값과, 생긴 오류가 붙는 자리(어느 칸인지 · 폼 전체인지)는 무엇인가?

### 3. 대문자로 쓴 금지어와 금지어를 품은 낱말 (예측)

```python
# 질문용 발췌 — validate_no_profanity 는 원본 그대로
validate_no_profanity('Buy SPAM now')
validate_no_profanity('scampi pasta')
validate_no_profanity('hello world')
```

- 세 호출은 각각 어떻게 끝나며, 예외가 나면 그 문구는 무엇인가?

### 4. `contact_view` 에 검사를 통과하지 못한 POST 가 오면 (예측)

- 이때 `contact_view` 는 어떤 응답을 돌려주고, 그 응답의 폼에는 무엇이 들어 있나?

### 5. `clean_name()` 끝의 `return` 을 지우면 (왜)

- `return name.strip()` 을 지웠을 때 검사가 통과해도 뷰가 받는 `cleaned_data['name']` 이 망가지는 까닭은 무엇인가?

### 6. `clean()` 은 `cleaned_data.get()` 으로 꺼낸다 (왜)

- `clean_name()` 은 `self.cleaned_data['name']` 으로 꺼내도 되는데 `clean()` 은 `.get()` 과 `and message` 를 쓰는 까닭은 무엇인가?

### 7. `clean_title()` 에서 자기 자신을 빼는 줄 (경계)

- `qs = qs.exclude(pk=self.instance.pk)` 를 지우면, 새 글 쓰기와 제목을 그대로 둔 글 수정 가운데 어느 쪽이 어떻게 깨지나?

### 8. `commit=False` 로 저장을 미룰 때 (경계)

- `author` 를 `exclude` 한 `PostForm` 으로 새 글을 저장하면서 `tags` 까지 남기려면, `form.save(commit=False)` 뒤에 무엇을 어떤 차례로 해야 하나?

### 9. `initial` 과 `instance`, 그리고 `Form` 과 `ModelForm` (연결)

- 둘 다 칸을 미리 채우는 `initial` 과 `instance` 는 어떻게 다르며, 그 차이가 `Form` 과 `ModelForm` 의 차이와 어떻게 이어지나?

## 실습

### 실습 1. 문의 폼 · 글 수정 폼 · 두 뷰 · 금지어 검사를 갖춘 Django 폼 모듈

**만들 것** — 모델과 무관한 문의 폼, `Post` 모델에서 뽑은 글 폼, 두 폼을 쓰는 함수형 뷰 두 개, 금지어를 막는 validator 와 댓글 폼을 한 파일에 만든다.

**준비물** — Django 가 설치된 프로젝트가 필요하다. `Post` 모델(`title` · `content` · `category` · `tags`(ManyToMany) · `status` · `excerpt` 필드)과 `redirect` · `render` · `get_object_or_404` 는 정답 코드에 정의나 import 가 없으므로, 프로젝트의 `models.py` 와 `django.shortcuts` 에서 가져와야 한다.

**요구 조건**

1단계 — 문의 폼 `ContactForm`(`forms.Form` 상속)

1. `name` 은 2자 이상 100자 이하의 문자열 칸이며 라벨은 `이름`, 한 줄 입력 위젯이다.
2. `email` 은 이메일 형식을 스스로 검사하는 칸이며 라벨은 `이메일` 이다.
3. `subject` 는 빈 값 · `general` · `bug` · `feature` 네 가지에서 고르는 선택 칸이며 라벨은 `문의 유형` 이다.
4. `message` 는 여러 줄 입력 위젯을 쓰는 문자열 칸이며 라벨은 `메시지`, 10자 미만이면 `최소 10자 이상 입력하세요.` 로 막는 validator 를 단다.
5. `agree` 는 반드시 체크해야 하는 칸이며 라벨은 `개인정보 수집 동의`, 비었을 때 문구는 `동의가 필요합니다.` 다.
6. `clean_name()` 은 이름이 숫자로만 되어 있으면 `이름에 숫자만 사용할 수 없습니다.` 로 막고, 아니면 앞뒤 공백을 벗겨 돌려준다.
7. `clean()` 은 부모의 `clean()` 을 먼저 부른 뒤, 문의 유형이 `bug` 이고 메시지가 있으며 30자 미만이면 `버그 리포트는 최소 30자 이상 상세히 작성해주세요.` 로 폼 전체를 막고, 아니면 정제된 데이터를 돌려준다.

2단계 — 글 폼 `PostForm`(`forms.ModelForm` 상속)

8. `Meta` 에서 기준 모델을 `Post` 로, 포함 필드를 `title` · `content` · `category` · `tags` · `status` · `excerpt` 여섯으로 정한다.
9. `title` 은 한 줄 입력, `content` · `excerpt` 는 여러 줄 입력, `tags` 는 체크박스 여러 개로 그리도록 위젯을 바꾼다.
10. 라벨(`title` · `content` · `excerpt`), `excerpt` 의 안내 문구, `title` 의 오류 종류별 문구(`max_length` · `required`)를 `Meta` 에 둔다.
11. `clean_title()` 은 같은 제목의 글이 있으면 `이미 같은 제목의 글이 존재합니다.` 로 막되, 수정 중이면 자기 자신은 빼고 센다. 통과하면 제목을 돌려준다.

3단계 — 뷰

12. `contact_view` 는 POST 면 받은 데이터로 폼을 만들어 검사하고, 통과하면 정제된 `name` · `email` 을 꺼낸 뒤 `contact-success` 로 redirect 한다. GET 이면 문의 유형을 `general` 로 미리 고른 빈 폼을 만든다. 그 밖의 경우는 `contact.html` 에 폼을 넘겨 그린다.
13. `post_edit_view(request, pk)` 는 `pk` 로 글을 찾고(없으면 404), POST 면 그 글에 묶어 받은 데이터로 폼을 만들어 통과 시 저장하고 `post-detail`(그 글의 `pk`)로 redirect 한다. GET 이면 그 글의 값으로 채운 폼을 만든다. 그 밖의 경우는 `blog/post_form.html` 에 폼을 넘겨 그린다.

4단계 — 커스텀 validator

14. `validate_no_profanity(value)` 는 `spam` · `scam` 이 대소문자와 무관하게 값 안에 들어 있으면 `부적절한 단어가 포함되어 있습니다: <걸린 낱말>` 로 막는다.
15. `CommentForm` 의 `content` 칸은 이 validator 를 달고 세 줄짜리 여러 줄 입력으로 그린다.

5단계 — 정리 출력

16. 파일 끝에서 핵심 정리 문장들을 `print` 한다(문장은 시작 코드에 있다).

**시작 코드**

```python
# [웹 프레임워크] Django Forms — 시작 코드
from django import forms
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
# 준비: Post 모델과 redirect · render · get_object_or_404 를 프로젝트에서 import 한다


# === 1. 일반 Form ===
class ContactForm(forms.Form):
    name = forms.CharField(
        # TODO: 길이 규칙(2~100자)
        label='이름',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '이름을 입력하세요'
        })
    )
    # TODO: email — 이메일 형식을 스스로 검사하는 필드
    #       label='이메일', widget=forms.EmailInput(attrs={'class': 'form-control'})

    # TODO: subject — 선택 필드
    #       choices: ('', '선택하세요'), ('general', '일반 문의'), ('bug', '버그 리포트'), ('feature', '기능 요청')
    #       label='문의 유형'

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5
        }),
        label='메시지',
        # TODO: 10자 미만을 막는 validator
    )
    agree = forms.BooleanField(
        label='개인정보 수집 동의',
        # TODO: 반드시 체크 + 비었을 때 문구 '동의가 필요합니다.'
    )

    def clean_name(self):
        # TODO: 숫자로만 된 이름을 막고, 앞뒤 공백을 벗겨 돌려준다
        pass

    def clean(self):
        # TODO: 부모 clean() 호출 → subject 가 bug 이고 message 가 30자 미만이면 폼 전체 오류
        pass


# === 2. ModelForm ===
class PostForm(forms.ModelForm):
    class Meta:
        # TODO: 기준 모델과 포함할 필드 여섯
        widgets = {
            # TODO: 'title' — 한 줄 입력, attrs={'class': 'form-control', 'placeholder': '제목을 입력하세요'}
            # TODO: 'content' — 여러 줄 입력, attrs={'class': 'form-control', 'rows': 15}
            # TODO: 'excerpt' — 여러 줄 입력, attrs={'class': 'form-control', 'rows': 3}
            # TODO: 'tags' — 체크박스 여러 개
        }
        labels = {
            'title': '제목',
            'content': '내용',
            'excerpt': '요약',
        }
        help_texts = {
            'excerpt': '글의 간단한 요약 (선택사항)',
        }
        error_messages = {
            'title': {
                'max_length': '제목이 너무 깁니다.',
                'required': '제목을 입력해주세요.',
            },
        }

    def clean_title(self):
        # TODO: 같은 제목의 글을 찾되, 수정 중이면 자기 자신은 뺀다
        pass


# === 3. 뷰에서 폼 사용 ===
def contact_view(request):
    # TODO: POST → 바인딩 · 검사 · 정제된 값 꺼내기 · redirect('contact-success')
    # TODO: GET  → subject 를 'general' 로 미리 고른 빈 폼
    return render(request, 'contact.html', {'form': form})


def post_edit_view(request, pk):
    # TODO: pk 로 글 찾기(없으면 404)
    # TODO: POST → 그 글에 묶어 바인딩 · 검사 · 저장 · redirect('post-detail', pk=...)
    # TODO: GET  → 그 글의 값으로 채운 폼
    return render(request, 'blog/post_form.html', {'form': form})


# === 4. 커스텀 Validator ===
def validate_no_profanity(value):
    bad_words = ['spam', 'scam']
    # TODO: 대소문자와 무관하게 금지어가 들어 있으면 걸린 낱말을 담아 막는다


class CommentForm(forms.Form):
    content = forms.CharField(
        # TODO: validator 등록
        widget=forms.Textarea(attrs={'rows': 3})
    )


# === 5. 폼 필드 타입 정리 ===
# CharField, EmailField, URLField, IntegerField, FloatField,
# DecimalField, BooleanField, ChoiceField, MultipleChoiceField,
# DateField, DateTimeField, TimeField, FileField, ImageField,
# TypedChoiceField, SlugField, UUIDField, JSONField

print("Django Forms 핵심 정리")
print("="*50)
print("Form: 수동 필드 정의, 유연한 유효성 검사")
print("ModelForm: 모델 기반 자동 생성, save()로 DB 저장")
print("clean_<field>(): 단일 필드 유효성 검사")
print("clean(): 다중 필드 교차 검사")
print("widgets: 폼 필드 HTML 위젯 커스터마이징")
print("initial: 폼 초기값 / instance: 기존 객체 바인딩")
```

**확인 방법** — 프로젝트 안에서 `python manage.py shell` 을 열고 이 모듈을 불러온 뒤, `ContactForm(data={...})` 를 여러 값으로 만들어 `is_valid()` · `errors` · `non_field_errors()` 를 확인한다. 금지어 함수는 몇 가지 문자열로 직접 불러 보고, 두 뷰는 URL 에 연결해 브라우저에서 GET 화면 · 잘못된 POST · 올바른 POST 를 차례로 보낸다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
