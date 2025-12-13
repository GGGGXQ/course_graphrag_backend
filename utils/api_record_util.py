import time
import json
from typing import Callable
from traceback import format_exc

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute

import config
from utils.logger_util import logger

class RequestRecordRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            base_req_msg = f"[{request.method} {request.url.path}"
            before = time.time()
            try:
                response: Response = await original_route_handler(request)
                status_code = response.status_code
                base_req_msg += f" {status_code}] "
            except HTTPException as e:
                status_code = e.status_code
                base_req_msg += f" {status_code}] "
                logger.warning(f"{base_req_msg} HTTPException: {e.detail}")
                raise e
            except Exception as e:
                status_code = 500
                base_req_msg += f" {status_code}] "
                logger.error(f"{base_req_msg} Internal server error: {format_exc()}")
                if config.DEBUG_MODE:
                    raise e
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Internal server error, please contact the administrator.",
                    )
            finally:
                duration = time.time() - before

                if request.headers.get("X-Forwarded-For"):
                    ip_message = f"Forwarded For: {request.headers['X-Forwarded-For']}"  # noqa
                elif request.headers.get("X-Real-IP"):
                    ip_message = f"Real IP: {request.headers['X-Real-IP']}"
                else:
                    ip_message = f"Host: {request.headers.get('host')}"

                req_message = base_req_msg
                req_message += f"{ip_message}"

                req_message += f" process time: {round(duration, 2)},"
                req_message += f" params: {json.dumps(request.query_params.multi_items(), ensure_ascii=False)},"  # noqa
                req_message += f" headers: {json.dumps(request.headers.items(), ensure_ascii=False)}"  # noqa

                match status_code:
                    case 200 | 201 | 204:
                        logger.debug(req_message)

                    case 400 | 401 | 403 | 404 | 409 | 422:
                        logger.warning(req_message)
                    case 500:
                        logger.error(req_message)
                    case _:
                        logger.info(req_message)

            return response

        return custom_route_handler
