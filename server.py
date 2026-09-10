#!/usr/bin/env python3
"""Combined Zoom callback + Calendly MCP/OAuth shim for ngrok on a Pi.

Zoom:
  Register https://YOUR_DOMAIN/callback as Redirect URL + Allow List.
  This service captures /callback?code=...

Calendly:
  Point the Calendly MCP URL at https://YOUR_DOMAIN
  We redirect /authorize, forward /token + /register to calendly.com,
  rewrite discovery, and proxy MCP to https://mcp.calendly.com.
"""
from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MCP_ORIGIN = "https://mcp.calendly.com"
AUTH_ORIGIN = "https://calendly.com"
LISTEN_HOST = os.environ.get("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("PORT", "8790"))
PUBLIC_BASE = os.environ.get("PUBLIC_BASE", "").rstrip("/")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/var/lib/oauth-tunnel"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
ZOOM_CALLBACK_FILE = DATA_DIR / "zoom_last_callback.json"
ZOOM_HISTORY_FILE = DATA_DIR / "zoom_callback_history.jsonl"

HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def metadata(public_base: str) -> dict:
    issuer = public_base or f"http://127.0.0.1:{LISTEN_PORT}"
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{AUTH_ORIGIN}/oauth/authorize",
        "token_endpoint": f"{issuer}/token",
        "registration_endpoint": f"{issuer}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["mcp:scheduling:read", "mcp:scheduling:write"],
    }


def rewrite_headers(headers: dict, public_base: str) -> dict:
    out = {}
    for key, value in headers.items():
        if key.lower() == "www-authenticate" and public_base:
            value = re.sub(
                r'resource_metadata="https://mcp\.calendly\.com/\.well-known/oauth-protected-resource"',
                f'resource_metadata="{public_base}/.well-known/oauth-protected-resource"',
                value,
            )
            value = value.replace(
                "https://mcp.calendly.com/.well-known/oauth-protected-resource",
                f"{public_base}/.well-known/oauth-protected-resource",
            )
        out[key] = value
    return out


def forward(method: str, url: str, headers: dict, body: bytes | None):
    req = Request(url, data=body if body else None, method=method)
    for key, value in headers.items():
        if key.lower() in HOP:
            continue
        req.add_header(key, value)
    try:
        with urlopen(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()
    except URLError as exc:
        return 502, {"content-type": "text/plain"}, str(exc.reason).encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        path = urlsplit(self.path).path
        print(f"{self.command} {path} {args[1] if len(args) > 1 else ''}", flush=True)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or 0)
        return self.rfile.read(length) if length else b""

    def _send(self, status: int, headers: dict, body: bytes):
        headers = rewrite_headers(headers, PUBLIC_BASE)
        self.send_response(status)
        sent = set()
        for key, value in headers.items():
            lk = key.lower()
            if lk in HOP or lk in {"content-length", "transfer-encoding"}:
                continue
            self.send_header(key, value)
            sent.add(lk)
        if "content-type" not in sent:
            self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self._send(status, {"content-type": "application/json"}, body)

    def _html(self, status: int, html: str):
        body = html.encode()
        self._send(status, {"content-type": "text/html; charset=utf-8"}, body)

    def _handle_zoom_callback(self, query: str):
        from urllib.parse import parse_qs

        qs = parse_qs(query)
        payload = {k: (v[0] if len(v) == 1 else v) for k, v in qs.items()}
        if payload.get("code") or payload.get("error"):
            ZOOM_CALLBACK_FILE.write_text(json.dumps(payload))
            with ZOOM_HISTORY_FILE.open("a") as f:
                f.write(json.dumps(payload) + "\n")
            print(
                "ZOOM_CAPTURED keys=",
                list(payload.keys()),
                "has_code=",
                "code" in payload,
                flush=True,
            )
        self._html(
            200,
            "<html><body><h1>Zoom OAuth captured.</h1>"
            "<p>You can close this tab.</p></body></html>",
        )

    def _handle(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        public = PUBLIC_BASE

        # Zoom OAuth callback
        if path in ("/callback", "/zoom/callback"):
            self._handle_zoom_callback(parsed.query)
            return

        # Calendly discovery
        if path in (
            "/.well-known/oauth-authorization-server",
            "/.well-known/openid-configuration",
        ):
            self._json(200, metadata(public))
            return

        if path == "/.well-known/oauth-protected-resource":
            issuer = public or AUTH_ORIGIN
            self._json(
                200,
                {
                    "resource": f"{public}/" if public else f"{MCP_ORIGIN}/",
                    "authorization_servers": [
                        f"{issuer}/" if public else f"{AUTH_ORIGIN}/"
                    ],
                    "scopes_supported": [
                        "mcp:scheduling:read",
                        "mcp:scheduling:write",
                    ],
                    "bearer_methods_supported": ["header"],
                },
            )
            return

        # Health
        if path in ("/healthz", "/"):
            if self.command == "GET" and path == "/healthz":
                self._json(
                    200,
                    {
                        "ok": True,
                        "public_base": public or None,
                        "zoom_callback": "/callback",
                        "calendly_mcp": "proxy",
                    },
                )
                return

        query = parsed.query
        if path in ("/authorize", "/oauth/authorize"):
            target = f"{AUTH_ORIGIN}/oauth/authorize"
            if query:
                target = f"{target}?{query}"
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        body = self._read_body()
        headers = {k: v for k, v in self.headers.items()}

        if path in ("/token", "/oauth/token"):
            status, resp_headers, resp_body = forward(
                self.command, f"{AUTH_ORIGIN}/oauth/token", headers, body
            )
            self._send(status, resp_headers, resp_body)
            return

        if path in ("/register", "/oauth/register"):
            status, resp_headers, resp_body = forward(
                self.command, f"{AUTH_ORIGIN}/oauth/register", headers, body
            )
            self._send(status, resp_headers, resp_body)
            return

        # Everything else → Calendly MCP
        target = f"{MCP_ORIGIN}{path}"
        if query:
            target = f"{target}?{query}"
        status, resp_headers, resp_body = forward(
            self.command, target, headers, body
        )
        self._send(status, resp_headers, resp_body)

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_OPTIONS(self):
        self._handle()

    def do_HEAD(self):
        self._handle()


if __name__ == "__main__":
    httpd = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(
        f"listening on {LISTEN_HOST}:{LISTEN_PORT} public={PUBLIC_BASE or '(unset)'}",
        flush=True,
    )
    httpd.serve_forever()
