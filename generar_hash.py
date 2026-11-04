import os
import hashlib
import getpass

login = input("Usuario de respaldo (por ejemplo invitado): ").strip().lower()
nombre = input("Nombre que se mostrara (por ejemplo Invitado): ").strip()
rol = input("Rol (Enter para Invitado; tambien puede ser Auditor): ").strip() or "Invitado"
clave = getpass.getpass("Contrasena de al menos 8 caracteres (no se ve al escribir): ")
clave2 = getpass.getpass("Repite la contrasena: ")
if len(clave) < 8 or clave != clave2:
    raise SystemExit("La contrasena es muy corta o no coincide.")
sal = os.urandom(16).hex()
h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 200000).hex()
print("")
print("Copia este bloque y pegalo AL FINAL de tus Secrets (no incluye la contrasena):")
print("")
print("[[respaldo]]")
print('login = "' + login + '"')
print('nombre = "' + nombre + '"')
print('rol = "' + rol + '"')
print('password_hash = "pbkdf2_sha256$200000$' + sal + "$" + h + '"')