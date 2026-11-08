# reglas.py
# Aqui estan las reglas del proyecto, escritas con Python basico.
# Los demas programas de la carpeta importan estas funciones.

import unicodedata

# Si el objeto del contrato tiene alguna de estas palabras, es de medicamentos o insumos medicos.
PALABRAS_SI = [
    "medicament", "farmaco", "farmaceutic", "suministro de insumos",
    "dispositivos medicos", "material medico", "insumos medico",
    "vacuna", "reactivo",
]

# Si tiene alguna de estas, es un contrato de personal y NO lo queremos.
PALABRAS_NO = [
    "regente", "quimico", "prestar servicios", "prestacion de servicios",
    "apoyo", "profesional", "auxiliar", "tecnologo", "tecnologa",
    "direccion de medicamentos", "acompanamiento juridico",
]


def quitar_tildes(texto):
    # Pasa el texto a minuscula y le quita las tildes (por ejemplo: medicacion queda igual y farmaceutica no lleva tilde).
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    resultado = ""
    for letra in texto:
        if not unicodedata.combining(letra):
            resultado = resultado + letra
    return resultado


def es_de_medicamentos(texto):
    # Devuelve True si el contrato es de medicamentos o insumos medicos.
    texto = quitar_tildes(texto)

    tiene_palabra_si = False
    for palabra in PALABRAS_SI:
        if palabra in texto:
            tiene_palabra_si = True

    tiene_palabra_no = False
    for palabra in PALABRAS_NO:
        if palabra in texto:
            tiene_palabra_no = True

    return tiene_palabra_si and not tiene_palabra_no


def categoria_del_contrato(texto):
    # Clasifica el contrato en una de 5 categorias.
    texto = quitar_tildes(texto)

    if "vacuna" in texto:
        return "Vacunas"
    if "reactivo" in texto or "laboratorio" in texto:
        return "Laboratorio y reactivos"
    if "dispositivos m" in texto or "material m" in texto or "insumos m" in texto or "odontol" in texto:
        return "Dispositivos e insumos medicos"
    if "medicament" in texto or "farmaco" in texto or "farmac" in texto:
        return "Medicamentos"
    return "Otros insumos de salud"


def nivel_de_alerta(saldo):
    # El nivel depende de cuanto dinero falta por pagar (en pesos).
    if saldo >= 100000000:
        return "Alta"
    if saldo >= 20000000:
        return "Media"
    if saldo > 0:
        return "Baja"
    return "Sin alerta"
