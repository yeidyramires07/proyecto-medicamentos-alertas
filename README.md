# Alertas de contratos de medicamentos en Colombia

Proyecto integrador de cuarto semestre. Une tres materias:
Computación Paralela y Distribuida, Redes e Infraestructura y Analítica y Visualización de Datos.
Objetivo de Desarrollo Sostenible: ODS 3, salud y bienestar.

## Qué hace

- Toma 100.000 contratos públicos y se queda con los de medicamentos e insumos médicos.
- Calcula cuánto falta por pagar en cada contrato y le pone un nivel de alerta (Alta, Media, Baja).
- Muestra los contratos en una aplicación web con filtros, un mapa por departamento y gráficos.
- El administrador puede enviar las alertas por Telegram a compradores, EPS y farmacias.

## Carpetas

- `app.py`: la aplicación web (Streamlit).
- `enviar_telegram.py`: envía un mensaje por Telegram. Lo usa la aplicación.
- `procesamiento/`: limpieza de los datos.
  - `reglas.py`: las reglas del proyecto (qué es un contrato de medicamentos, categorías y niveles de alerta).
  - `filtrar_paralelo.py`: limpieza en serie y con multiprocessing, con medición de speedup y eficiencia.
  - `spark_resumen.py`: lo mismo con Apache Spark.
  - `crear_alertas.py`: calcula el saldo pendiente y el nivel de alerta.
- `analisis/`: `eda.py` crea los gráficos exploratorios (carpeta `graficos/`).
- `base_de_datos/`: scripts que crean y cargan la base MySQL y los usuarios.
- `bd/`: esquema de la base de datos y tablas en CSV.
- `utilidades/`: `obtener_chat_id.py` para saber el chat_id de Telegram de una persona.

## Cómo ejecutarlo

```
pip install -r requirements.txt
streamlit run app.py
```

Las claves de la base de datos y el token de Telegram no están en el código:
van en los Secrets de Streamlit o en variables de entorno.

## Privacidad

Se quitó la columna con los números de documento de quien ordena el gasto.
Las alertas solo se envían a personas que iniciaron el bot de Telegram.

## Integrantes

(Escribir aquí los nombres del grupo)
