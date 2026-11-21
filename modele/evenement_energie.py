from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict
import hashlib
import json


@dataclass
class EvenementEnergie:
    """Modèle métier normalisé pour tout événement collecté."""
    source: str
    format_origine: str
    categorie: str
    donnees: Dict[str, Any]
    horodatage_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        empreinte_source = {
            "source": self.source,
            "format_origine": self.format_origine,
            "categorie": self.categorie,
            "donnees": self.donnees,
        }
        payload_canonique = json.dumps(empreinte_source, sort_keys=True, ensure_ascii=False)
        self.event_id = hashlib.sha256(payload_canonique.encode("utf-8")).hexdigest()[:16]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)