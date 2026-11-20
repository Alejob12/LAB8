"""
Servidor SMTP local aislado de la organización ficticia (mail.andescorp.local).

Implementa protocolo SMTP (RFC 5321) sobre asyncio sin relay externo:
- Escucha exclusivamente en BIND_HOST:SMTP_PORT (por defecto 127.0.0.1:1025).
- Rechaza con código 550 cualquier destinatario fuera de la allowlist `@andescorp.local`.
- Almacena cada correo localmente en `MailStorage` y genera logs detallados en `logs/smtp_server.log`.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from config.settings import BIND_HOST, ORG_DOMAIN, SMTP_PORT, is_allowed_recipient
from servidor_correo.mail_storage import MailStorage

_ADDR_RE = re.compile(r"<([^>]+)>")


def _extract_address(argument: str) -> str:
    match = _ADDR_RE.search(argument)
    if match:
        return match.group(1).strip()
    parts = argument.split(":", 1)
    candidate = parts[1] if len(parts) == 2 else argument
    return candidate.strip().split()[0].strip("<>")


class LocalSMTPServer:
    """Servidor SMTP asíncrono de laboratorio sin capacidad de envío a internet."""

    def __init__(
        self,
        host: str = BIND_HOST,
        port: int = SMTP_PORT,
        storage: MailStorage | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.storage = storage or MailStorage()
        self._server: asyncio.AbstractServer | None = None

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername")
        peer_str = f"{peer[0]}:{peer[1]}" if peer else "local"
        self.storage.log_smtp("INFO", f"CONN_OPEN peer={peer_str}")

        mail_from: str = ""
        rcpt_list: list[str] = []

        async def send(line: str) -> None:
            writer.write((line + "\r\n").encode("utf-8"))
            await writer.drain()

        await send(f"220 mail.{ORG_DOMAIN} ESMTP AndesCorp-Lab8-SimulatedMail (Isolated)")

        try:
            while not reader.at_eof():
                raw_line = await reader.readline()
                if not raw_line:
                    break
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line:
                    continue

                upper = line.upper()
                if upper.startswith("EHLO"):
                    client_host = line[4:].strip() or "localhost"
                    self.storage.log_smtp("INFO", f"EHLO peer={peer_str} helo={client_host}")
                    await send(f"250-mail.{ORG_DOMAIN} Hello {client_host}")
                    await send("250-SIZE 5242880")
                    await send("250-8BITMIME")
                    await send("250 SMTPUTF8")

                elif upper.startswith("HELO"):
                    client_host = line[4:].strip() or "localhost"
                    self.storage.log_smtp("INFO", f"HELO peer={peer_str} helo={client_host}")
                    await send(f"250 mail.{ORG_DOMAIN} Hello {client_host}")

                elif upper.startswith("MAIL FROM:"):
                    mail_from = _extract_address(line)
                    rcpt_list = []
                    self.storage.log_smtp("INFO", f"MAIL_FROM peer={peer_str} sender={mail_from}")
                    await send("250 2.1.0 Originator OK")

                elif upper.startswith("RCPT TO:"):
                    rcpt = _extract_address(line)
                    if not is_allowed_recipient(rcpt):
                        self.storage.log_smtp(
                            "WARN",
                            f"RCPT_REJECTED peer={peer_str} rcpt={rcpt} reason=EXTERNAL_DOMAIN_BLOCKED",
                        )
                        await send(
                            f"550 5.7.1 Relay denied: entorno simulado solo permite destinatarios @{ORG_DOMAIN}"
                        )
                        continue
                    rcpt_list.append(rcpt)
                    self.storage.log_smtp("INFO", f"RCPT_ACCEPTED peer={peer_str} rcpt={rcpt}")
                    await send("250 2.1.5 Recipient OK")

                elif upper == "DATA":
                    if not mail_from or not rcpt_list:
                        await send("503 5.5.1 Bad sequence of commands (need MAIL FROM and RCPT TO)")
                        continue
                    await send("354 End data with <CR><LF>.<CR><LF>")
                    chunks: list[bytes] = []
                    while True:
                        data_line = await reader.readline()
                        if not data_line:
                            break
                        if data_line in (b".\r\n", b".\n"):
                            break
                        # Des-escapar dot-stuffing RFC 5321
                        if data_line.startswith(b".."):
                            data_line = data_line[1:]
                        chunks.append(data_line)
                    raw_msg = b"".join(chunks)

                    stored_ids: list[str] = []
                    for rcpt in rcpt_list:
                        msg_id = self.storage.store_received_message(mail_from, rcpt, raw_msg)
                        stored_ids.append(msg_id)
                        self.storage.log_smtp(
                            "INFO",
                            f"DELIVERED peer={peer_str} from={mail_from} to={rcpt} bytes={len(raw_msg)} msg_id={msg_id}",
                        )

                    await send(f"250 2.0.0 OK queued_locally id={stored_ids[0]}")
                    mail_from = ""
                    rcpt_list = []

                elif upper == "RSET":
                    mail_from = ""
                    rcpt_list = []
                    await send("250 2.0.0 Reset OK")

                elif upper == "NOOP":
                    await send("250 2.0.0 OK")

                elif upper == "QUIT":
                    await send(f"221 2.0.0 mail.{ORG_DOMAIN} closing connection")
                    break

                else:
                    await send("502 5.5.2 Command not implemented in lab SMTP")
        except Exception as exc:
            self.storage.log_smtp("ERROR", f"SESSION_ERROR peer={peer_str} error={exc}")
        finally:
            self.storage.log_smtp("INFO", f"CONN_CLOSE peer={peer_str}")
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self) -> None:
        self._server = await asyncio.start_server(self.handle_client, self.host, self.port)
        self.storage.log_smtp(
            "INFO",
            f"SMTP_SERVER_STARTED listen={self.host}:{self.port} allowed_domain=@{ORG_DOMAIN}",
        )

    async def serve_forever(self) -> None:
        await self.start()
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self.storage.log_smtp("INFO", "SMTP_SERVER_STOPPED")


def main() -> None:
    server = LocalSMTPServer()
    print(f"[SMTP Local] Escuchando en {server.host}:{server.port} (solo @{ORG_DOMAIN})")
    try:
        asyncio.run(server.serve_forever())
    except KeyboardInterrupt:
        print("\n[SMTP Local] Detenido.")


if __name__ == "__main__":
    main()
