"""Proxy support for zzoDrive.

Supported formats:
  mtproxy://host:port?secret=xxx       MTProto proxy (native Telethon)
  socks5://[user:pass@]host:port       SOCKS5 (needs python-socks)
  socks4://[user:pass@]host:port       SOCKS4 (needs python-socks)
  http://[user:pass@]host:port         HTTP CONNECT (needs python-socks)
"""
import asyncio
import ssl
from urllib.parse import urlparse, parse_qs

from telethon.network import connection as tg_connection

try:
    from python_socks.async_.asyncio import Proxy as SocksProxy
    HAS_SOCKS = True
except ImportError:
    HAS_SOCKS = False


def _normalize_tg_link(url):
    """Convert tg://proxy?server=X&port=Y&secret=Z into mtproxy:// form."""
    if not url.startswith("tg://proxy"):
        return url
    p = urlparse(url)
    qs = parse_qs(p.query)
    server = qs.get("server", [""])[0]
    port = qs.get("port", [""])[0]
    secret = qs.get("secret", [""])[0]
    if not server or not port or not secret:
        return url
    return f"mtproxy://{server}:{port}?secret={secret}"


def parse(url):
    if not url:
        return None
    url = _normalize_tg_link(url)
    p = urlparse(url)
    if not p.scheme or not p.hostname or not p.port:
        return None
    info = {
        "type": p.scheme.lower(),
        "host": p.hostname,
        "port": int(p.port),
        "user": p.username or "",
        "pass": p.password or "",
    }
    if info["type"] == "mtproxy":
        qs = parse_qs(p.query)
        info["secret"] = qs.get("secret", [""])[0]
    return info


def make_mtproxy(info):
    secret = info.get("secret", "")
    if not secret:
        raise ValueError("MTProxy URL requires ?secret=...")
    if secret.startswith("dd"):
        conn = tg_connection.ConnectionTcpMTProxyRandomizedIntermediate
    elif secret.startswith("ee"):
        raise ValueError(
            "FakeTLS MTProxy (secret starting with 'ee') is not supported. "
            "Use a 'dd' secret MTProxy instead."
        )
    else:
        conn = tg_connection.ConnectionTcpMTProxyAbridged
    return conn, (info["host"], info["port"], secret)


def make_socks(info):
    if not HAS_SOCKS:
        raise RuntimeError(
            "SOCKS/HTTP proxy requires python-socks.\n"
            "Install with: pip install 'python-socks[asyncio]'"
        )

    ptype = info["type"]
    if ptype in ("socks5", "socks5h"):
        base = f"socks5://{info['host']}:{info['port']}"
    elif ptype == "socks4":
        base = f"socks4://{info['host']}:{info['port']}"
    elif ptype in ("http", "https"):
        base = f"http://{info['host']}:{info['port']}"
    else:
        raise ValueError(f"Unsupported proxy type: {ptype}")

    if info["user"]:
        scheme, rest = base.split("://", 1)
        base = f"{scheme}://{info['user']}:{info['pass']}@{rest}"

    proxy_url = base

    class SocksConnection(tg_connection.ConnectionTcpFull):
        async def _connect(self, timeout=None, ssl=None):
            proxy = SocksProxy.from_url(proxy_url)
            sock = await proxy.connect(
                dest_host=self._ip,
                dest_port=self._port,
                timeout=timeout,
            )
            self._sock = sock
            if ssl:
                self._reader, self._writer = await asyncio.open_connection(
                    sock=sock, ssl=ssl, server_hostname=self._ip,
                )
            else:
                self._reader, self._writer = await asyncio.open_connection(sock=sock)
            return self._reader, self._writer

    return SocksConnection, None


def make_connection(proxy_url):
    """Returns (connection_class, proxy_tuple_or_None)."""
    info = parse(proxy_url)
    if not info:
        return tg_connection.ConnectionTcpFull, None

    if info["type"] == "mtproxy":
        return make_mtproxy(info)

    return make_socks(info)
