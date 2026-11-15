"""Профиль нагрузки: разгон -> полка -> спад (Коцур, лекция 2: ramp-up, hold, ramp-down).

Числа задаются переменными окружения, чтобы один и тот же файл годился для прогонов на 10, 50 и 100:
  USERS - сколько одновременных пользователей на полке
  RAMP  - секунд на разгон, HOLD - секунд на полке, DOWN - секунд на спад
"""
import os

from locust import LoadTestShape

USERS = int(os.environ.get("USERS", "10"))
RAMP = int(os.environ.get("RAMP", "20"))
HOLD = int(os.environ.get("HOLD", "60"))
DOWN = int(os.environ.get("DOWN", "10"))


class RampHoldDown(LoadTestShape):
    def tick(self):
        t = self.get_run_time()
        rate = max(1.0, USERS / max(RAMP, 1))
        if t < RAMP:                                   # разгон: пользователи добавляются плавно
            return max(1, round(USERS * t / RAMP)), rate
        if t < RAMP + HOLD:                            # полка: измеряем именно здесь
            return USERS, rate
        if t < RAMP + HOLD + DOWN:                     # спад
            left = RAMP + HOLD + DOWN - t
            return max(1, round(USERS * left / DOWN)), rate
        return None                                    # конец теста
