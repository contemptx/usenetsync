import os, sys, socket, importlib

REQUIRED = [
    "NNTP_HOST","NNTP_PORT","NNTP_USERNAME","NNTP_PASSWORD","NNTP_SSL","NNTP_GROUP",
    "DATABASE_URL","FRONTEND_BASE_URL","VITE_BACKEND_URL","PRODUCTION_NNTP_CLIENT_IMPORT"
]

def _require_env():
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

def _enforce_ssl_port():
    if os.environ["NNTP_SSL"].lower() != "true":
        raise RuntimeError("NNTP_SSL must be true (Newshosting requires SSL).")
    if int(os.environ["NNTP_PORT"]) != 563:
        raise RuntimeError("NNTP_PORT must be 563 (SSL).")

def _probe_dns():
    host = os.environ["NNTP_HOST"]
    try:
        socket.gethostbyname(host)
    except Exception as e:
        raise RuntimeError(f"Cannot resolve NNTP_HOST={host}: {e}")

class _BlockNntplib:
    def find_spec(self, fullname, path, target=None):
        if fullname == "nntplib":
            raise ImportError("nntplib is forbidden. Use pynntp (imported as 'nntp').")
        return None

# Install import guard early
sys.meta_path.insert(0, _BlockNntplib())

def pytest_sessionstart(session):
    _require_env()
    _enforce_ssl_port()
    _probe_dns()

def load_production_client():
    spec = os.getenv("PRODUCTION_NNTP_CLIENT_IMPORT", "")
    if ":" not in spec:
        raise RuntimeError("Set PRODUCTION_NNTP_CLIENT_IMPORT to 'module:ClassName'")
    mod_name, cls_name = spec.split(":", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)

# Session-scoped fixture for the production client class (not instance)
def pytest_configure(config):
    pass