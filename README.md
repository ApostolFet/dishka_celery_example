# Dishka-celery example

Поднять контейнеры

1. docker compose up -d

2. Проверка переодических задач
   После того как все контейнеры будут работать, можно будет увидеть в логах воркера два сообщения,
   которые генерируются по расписанию:

```
my_app.app.test[22398f32-6636-4f53-85ea-e9f26c3b178e]: dishka best of the best
my_app.app.test[4c2c9f8a-08de-45b2-858f-d691fe50f4e2]: dishka forever
```

3. Проверка запуска задач и получения реузультата

Воспользуйтесь [коллекцией Postman](https://www.postman.com/mymarket616261/workspace/publicworkspace/collection/17532424-5c2b7da5-edf0-4018-99ba-2e086200073a?action=share&creator=17532424) отправьте запрос в send_task с числом и получите result_id,
Для получения результата вставьте result_id в запрос get_result в поле id и отправьте запрос.
Результа должен быть больше на 17, чем ваше число
