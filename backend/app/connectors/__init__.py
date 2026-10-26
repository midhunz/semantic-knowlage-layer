from app.connectors.base import Connector


def get_connector(kind: str, config: dict) -> Connector:
    if kind == "trino":
        from app.connectors.trino import TrinoConnector

        return TrinoConnector(config)
    raise ValueError(f"Unsupported source kind: {kind}")
