from celery import Celery
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from dishka import Provider, Scope, make_container, provide
from dishka.integrations.celery import (
    DishkaTask,
    FromDishka,
    inject,
    setup_dishka,
)
from flask import Flask, Response, jsonify, request

celery_app = Celery(
    task_cls=DishkaTask,
    broker="amqp://admin:mypass@rabbit:5672//",
    backend="redis://redis:6379/0",
)

logger = get_task_logger(__name__)


@celery_app.on_after_configure.connect()
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, test.s("forever"), name="forever")
    sender.add_periodic_task(30.0, test.s("best of the best"), name="best")


@celery_app.task()
def test(input_str: str, my_str: FromDishka[str]):
    logger.info("%s %s", my_str, input_str)


@celery_app.task()
def add_my_int(x: int, *, y: FromDishka[int]):
    z = x + y
    logger.info(z)
    return z


class MyProveder(Provider):
    scope = Scope.REQUEST
    my_int = provide(lambda self: 17, provides=int)
    my_str = provide(lambda self: "dishka", provides=str)


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
