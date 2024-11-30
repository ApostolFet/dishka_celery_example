from collections.abc import Iterator
from logging import Logger

from celery import Celery, Task, current_app
from celery.result import AsyncResult
from celery.signals import worker_process_shutdown
from celery.utils.log import get_task_logger
from dishka import Provider, Scope, make_container, provide
from dishka.integrations.celery import (
    DishkaTask,
    FromDishka,
    setup_dishka,
)
from flask import Flask, Response, jsonify, request

celery_app = Celery(
    task_cls=DishkaTask,
    broker="amqp://admin:mypass@rabbit:5672//",
    backend="redis://redis:6379/0",
)

logger = get_task_logger(__name__)


class MyClass:
    def __init__(self, logger: Logger):
        self._logger = logger

    def log(self, message: str):
        self._logger.info(message)


@celery_app.on_after_configure.connect()
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, test.s("forever"), name="forever")
    sender.add_periodic_task(30.0, test.s("best of the best"), name="best")


@celery_app.task()
def test(input_str: str, my_str: FromDishka[str], my_class: FromDishka[MyClass]):
    my_class.log(f"{my_str} {input_str}")


@celery_app.task(bind=True)
def add_my_int(
    task: Task,
    x: int,
    *,
    y: FromDishka[int],
    my_class: FromDishka[MyClass],
):
    if task.request.retries < 1:
        task.retry(countdown=5)

    z = x + y
    my_class.log(str(z))
    return z


class MyProveder(Provider):
    @provide(scope=Scope.APP)
    def get_my_str(self) -> Iterator[str]:
        logger.info("init my str")
        yield "dishka"
        logger.info("close my str")

    @provide(scope=Scope.REQUEST)
    def get_my_int(self) -> Iterator[int]:
        logger.info("init my int")
        yield 17
        logger.info("close my int")

    @provide(scope=Scope.REQUEST)
    def get_my_class(self) -> MyClass:
        return MyClass(logger)


@worker_process_shutdown.connect()
def close_dishka(*args, **kwargs):
    container: Container = current_app.conf["dishka_container"]
    container.close()


container = make_container(MyProveder())
setup_dishka(
    container,
    celery_app,
)

flask_app = Flask(__name__)


@flask_app.post("/")
def run_add_my_int() -> tuple[Response, int]:
    request_json = request.json
    if request_json is None:
        return jsonify({"message": "json not specified"}), 422
    x = request_json["x"]

    result = add_my_int.apply_async((x,))
    return jsonify({"result_id": result.id}), 200


@flask_app.get("/")
def get_result_add_my_int() -> tuple[Response, int]:
    request_json = request.json
    if request_json is None:
        return jsonify({"message": "json not specified"}), 422
    id = request_json["id"]

    result = AsyncResult(id, app=celery_app)
    return jsonify({"result": result.get()}), 200
