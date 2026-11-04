import nucleo

resumen, registrado = nucleo.enviar_lote(None, 3, "automatico", True)
print("Destinatarios procesados:", len(resumen))
for f in resumen:
    print(" ", f["destinatario"], "|", f["rol"], "|", f["departamento"], "| elegidos:", f["contratos_elegidos"], "| enviados:", f["enviados"], "| errores:", f["errores"])
print("Auditoria registrada:", registrado)