from locust import LoadTestShape

from locustfile import Anfitrion, Huesped

ETAPAS = [(10, 60), (25, 60), (50, 60), (75, 60), (100, 60), (150, 60)]


class SubidaPorEtapas(LoadTestShape):
    def tick(self):
        transcurrido = self.get_run_time()
        limite = 0
        for usuarios, duracion in ETAPAS:
            limite += duracion
            if transcurrido < limite:
                return usuarios, 10
        return None
