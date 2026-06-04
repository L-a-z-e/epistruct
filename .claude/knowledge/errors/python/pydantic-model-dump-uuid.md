# Pydantic model_dump() UUID 타입 에러

## 증상

```
AttributeError: 'UUID' object has no attribute 'replace'
```

`uuid.UUID(record["id"])` 호출 시 발생. `record`는 Pydantic `model_dump()`로 얻은 dict.

## 원인

Pydantic v2의 `model_dump()`는 기본적으로 필드를 Python 네이티브 타입으로 반환한다.
`uuid.UUID` 타입으로 선언된 필드는 **이미 `uuid.UUID` 객체**로 반환된다.

```python
class MyModel(BaseModel):
    id: uuid.UUID

m = MyModel(id="00000000-0000-0000-0000-000000000001")
data = m.model_dump()
type(data["id"])  # <class 'uuid.UUID'> ← 문자열이 아님

uuid.UUID(data["id"])  # AttributeError: 'UUID' object has no attribute 'replace'
```

`uuid.UUID()` 생성자는 문자열만 받기 때문에 UUID 객체를 넘기면 에러.

## 해결

```python
# 방법 1: isinstance 분기 (타입 안전)
raw_id = record["id"]
user_id = raw_id if isinstance(raw_id, uuid.UUID) else uuid.UUID(str(raw_id))

# 방법 2: model_dump(mode="json")으로 모두 직렬화
data = model.model_dump(mode="json")  # UUID → str 변환됨
user_id = uuid.UUID(data["id"])
```

방법 1을 기본으로 사용. 방법 2는 JSON 직렬화가 필요한 경우(외부 전송 등)에 사용.

## 예방

- `model_dump()` 결과를 dict로 넘길 때 타입을 `dict[str, Any]`로 선언하지 말고
  원본 Pydantic 객체를 직접 전달하거나 `isinstance` 분기 처리.
- service 레이어 파라미터에 `uuid.UUID` 타입 힌트를 명시하면 mypy가 사전에 잡음.

## 발생 맥락

Supabase webhook router → service 호출 시:
```python
# router.py
await service.handle_webhook(payload.type, payload.record.model_dump(), old)

# services.py — model_dump() 결과의 id는 이미 UUID 객체
user_id = uuid.UUID(record["id"])  # ← 에러
```
