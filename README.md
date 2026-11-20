# marketplace-alojamientos
Marketplace de alojamientos tipo Airbnb desarrollado con Django: publicación de alojamientos, búsqueda, cotización, reservas y auditoría.

Link GitHub: https://github.com/Camilooop7/marketplace-alojamientos

Para ejecutar el programa se debe tener en cuenta el manual técnico (`Manual_Tecnico_Marketplace.pdf`) para lograr ejecutarlo correctamente.
Si se desea, se puede usar el que ya está desplegado: https://marketplace-alojamientos-kmp6.vercel.app

Para hacer la ejecución de las pruebas se debe ejecutar desde la carpeta `marketplace_back`, con el entorno virtual activo:

```
python manage.py test
```

Para las pruebas de carga y estrés se usa Locust, primero se instala y se preparan los datos en una base SQLite local:

```
pip install locust
$env:DATABASE_URL="sqlite:///carga.sqlite3"
python pruebas_carga/preparar_datos.py
python manage.py runserver
```

Con el servidor corriendo, en otra terminal:

```
locust -f pruebas_carga/locustfile.py --host http://127.0.0.1:8000
locust -f pruebas_carga/estres.py --host http://127.0.0.1:8000
```

El primero es la prueba de carga y el segundo la de estrés (sube de 10 a 150 usuarios por etapas). Los resultados se ven en http://localhost:8089
