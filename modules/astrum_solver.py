import asyncio

from dev import GeneralSettings
from modules.evm_client import EVMClient
from config import TOTAL_USER_AGENT
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry, RequestClient, Logger


class AstrumSolver(Logger, RequestClient):
    def __init__(self, client: EVMClient):
        Logger.__init__(self)
        RequestClient.__init__(self, client)

        self.client = client
        self.api_key = GeneralSettings.ASTRUMSOLVER_API_KEY
        self.create_task_url = "https://service.astrum.foundation/vercel/createTask"
        self.get_result_url = "https://service.astrum.foundation/vercel/getTaskResult"

    async def solve_captcha(self, captcha_name: str, data_for_solver: dict):

        payload = {
            "clientKey": self.api_key,
        }

        self.logger_msg(*self.client.acc_info, msg=f"Start solving {captcha_name.capitalize()} captcha")

        if captcha_name == "hcaptcha":
            site_key = data_for_solver["websiteKey"]
            website_url = data_for_solver.get("websiteURL", "https://discord.com/")
            captcha_rqdata = data_for_solver.get("captcha_rqdata")

            captcha_cookie = ""
            if data_for_solver.get("cookies"):
                captcha_cookie = data_for_solver["cookies"]

            task = {
                "type": "HCaptchaTask",
                "websiteURL": website_url,
                "websiteKey": site_key,
                "data": captcha_rqdata,
                "cookies": captcha_cookie,
                "userAgent": TOTAL_USER_AGENT,
                "fallbackToActualUA": True,
            }

        elif captcha_name == "turnstile":
            site_key = data_for_solver["websiteKey"]
            website_url = data_for_solver["websiteURL"]

            task = {
                "type": "TurnstileTask",
                "websiteURL": website_url,
                "websiteKey": site_key,
            }

        elif captcha_name == "cf_clearance":
            task = {
                "type": "TurnstileTask",
                "cloudflareTaskType": "cf_clearance",
            } | data_for_solver

        elif captcha_name == "vercel":
            payload["proxyURL"] = self.client.proxy_url
            payload["websiteURL"] = data_for_solver['websiteURL']

        elif captcha_name == "geetest":
            website_url = data_for_solver["websiteURL"]
            gt = data_for_solver["gt"]
            version = data_for_solver["version"]

            task = {
                "type": "GeeTestTask",
                "websiteURL": website_url,
                "gt": gt,
                "version": version,
                "initParameters": {"riskType": "slide"},
                "userAgent": TOTAL_USER_AGENT,
            }

        elif captcha_name == "recaptchaV3":
            website_url = data_for_solver["websiteURL"]
            site_key = data_for_solver["websiteKey"]

            task = {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": website_url,
                "websiteKey": site_key,
                "minScore": data_for_solver.get('minScore', 0.3),
                "pageAction": "play",
            }

        elif captcha_name == "recaptchaV2":
            website_url = data_for_solver["websiteURL"]
            site_key = data_for_solver["websiteKey"]

            task = {
                "type": "RecaptchaV2Task",
                "websiteURL": website_url,
                "websiteKey": site_key,
                "userAgent": TOTAL_USER_AGENT,
            }
        else:
            raise SoftwareExceptionWithoutRetry(
                f"{self.__class__.__name__} do not support this type of Captcha: {captcha_name}"
            )

        counter = 0
        while True:
            try:

                response = await self.make_request(
                    method="POST", url=self.create_task_url, json=payload, module_name="Create task for captcha"
                )
            except Exception as error:
                if "ERROR_KEY_DOES_NOT_EXIST" in str(error):
                    raise SoftwareExceptionWithoutRetry(f"Please check your CAPMONSTER_API_KEY, it is incorrect")
                else:
                    raise error

            if response.get("errorId") == 0:
                result: str = await self.get_captcha_result(response["taskId"], captcha_name)

                if not result:
                    self.logger_msg(*self.client.acc_info, msg=f"Will try again in 10 second", type_msg="warning")
                    await asyncio.sleep(10)
                    counter += 1
                    if counter > 9:
                        raise SoftwareExceptionWithoutRetry("Can not create captcha task in 10 times")
                else:
                    return result
            else:
                error_description = response.get("errorDescription")
                error_code = response.get("errorCode")
                raise SoftwareException(f"Error code: {error_code}, error text: {error_description}")

    async def get_captcha_result(self, task_id, captcha_type):
        payload = {
            "taskId": task_id,
            "clientKey": self.api_key,
        }

        total_time = 0
        timeout = 360
        while True:
            try:
                response = await self.make_request(
                    method="POST", url=self.get_result_url, json=payload, module_name="Get captcha result"
                )

                if response.get("errorId"):
                    error_text = response.get("errorDescription")
                    error_code = response.get("errorCode")
                    raise SoftwareException(f"Error code: {error_code}, error text: {error_text}")

                if response["status"] == "closed":

                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Successfully solved {captcha_type.capitalize()} captcha",
                        type_msg="success",
                    )

                    recaptcha_response = None

                    if captcha_type == "hcaptcha":
                        return response["solution"]["gRecaptchaResponse"]

                    if captcha_type == "turnstile":
                        return response["solution"]["token"]

                    elif captcha_type == "geetest":
                        recaptcha_response = {
                            "lotNumber": response["solution"]["lot_number"],
                            "passToken": response["solution"]["pass_token"],
                            "genTime": response["solution"]["gen_time"],
                            "captchaOutput": response["solution"]["captcha_output"],
                        }

                    elif captcha_type == "cf_clearance":
                        return response["solution"]["cf_clearance"]

                    elif captcha_type in ["recaptchaV2", "recaptchaV3"]:
                        return response["solution"]["gRecaptchaResponse"]

                    elif captcha_type == "vercel":
                        return response["solution"]["token"]

                    return recaptcha_response

                total_time += 5
                await asyncio.sleep(5)

                if total_time > timeout:
                    raise SoftwareException("Can`t get captcha solve in 360 second")

            except Exception as error:
                self.logger_msg(*self.client.acc_info, msg=f"Can`t get captcha result: {error}", type_msg="warning")
                break
