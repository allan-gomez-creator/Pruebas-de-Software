# cuentas/correo_consola.py — Backend de desarrollo: imprime el correo ya decodificado.
from django.core.mail.backends.console import EmailBackend as ConsolaBase


class EmailBackend(ConsolaBase):
    def write_message(self, message):
        # Imprime asunto, destinatario y cuerpo en texto plano (sin quoted-printable),
        # para poder copiar el enlace completo sin "=" ni saltos de línea.
        self.stream.write(f"Asunto: {message.subject}\n")
        self.stream.write(f"Para: {', '.join(message.to)}\n\n")
        self.stream.write(message.body)
        self.stream.write("\n" + "-" * 70 + "\n")