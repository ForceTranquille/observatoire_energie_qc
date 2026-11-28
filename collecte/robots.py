"""Lecture de robots.txt selon le code HTTP (politique du site en matière de scraping)."""
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)


def charger_robots(
    base: str, user_agent: str, timeout: int = 15
) -> Tuple[RobotFileParser, Optional[int]]:
    """Retourne (analyseur, code HTTP) pour https://hote/robots.txt.

    200 -> règles lues · 401/403 -> tout refusé · autre 4xx -> tout permis ·
    5xx ou réseau en panne -> refus par prudence.
    """
    rp = RobotFileParser()
    rp.set_url(f"{base}/robots.txt")
    try:
        reponse = requests.get(
            f"{base}/robots.txt", headers={"User-Agent": user_agent}, timeout=timeout
        )
    except requests.RequestException as exc:
        logger.warning("robots.txt %s injoignable (%s) : refus par prudence", base, exc)
        rp.disallow_all = True
        return rp, None

    code = reponse.status_code
    if code == 200:
        rp.parse(reponse.text.splitlines())
    elif code in (401, 403):
        rp.disallow_all = True
    elif 400 <= code < 500:
        rp.allow_all = True
    else:
        rp.disallow_all = True
    logger.info("robots.txt %s -> HTTP %s", base, code)
    return rp, code


def url_autorisee(
    url: str,
    user_agent: str,
    timeout: int = 15,
    cache: Optional[Dict[str, RobotFileParser]] = None,
) -> bool:
    """True si robots.txt autorise `user_agent` à lire `url`."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    base = f"{parsed.scheme}://{parsed.netloc}"
    if cache is not None and base in cache:
        rp = cache[base]
    else:
        rp, _ = charger_robots(base, user_agent, timeout)
        if cache is not None:
            cache[base] = rp
    return rp.can_fetch(user_agent, url)
