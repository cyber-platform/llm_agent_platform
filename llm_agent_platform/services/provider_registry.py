from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm_agent_platform.auth.credentials import AuthAvailability
from llm_agent_platform.config import STATE_DIR


class ProviderRegistryError(Exception):
    """Raised when provider registry bootstrap data is invalid."""


@dataclass(frozen=True, slots=True)
class ProviderModelDescriptor:
    model_id: str
    display_name: str
    capabilities: tuple[str, ...]
    lifecycle: str
    upstream_id: str
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    provider_id: str
    route_name: str
    display_name: str
    auth_kind: str
    runtime_adapter: str
    discovery_enabled: bool
    snapshot_enabled: bool
    bootstrap_models: tuple[ProviderModelDescriptor, ...]
    raw_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProviderCatalogSnapshot:
    provider_id: str
    source: str
    models: tuple[ProviderModelDescriptor, ...]


def _registry_root() -> Path:
    return Path(__file__).resolve().parents[1] / "provider_registry"


def _registry_file() -> Path:
    return _registry_root() / "registry.json"


def _provider_models_from_payload(payload: list[dict[str, Any]]) -> tuple[ProviderModelDescriptor, ...]:
    models: list[ProviderModelDescriptor] = []
    for item in payload:
        model_id = str(item["model_id"])
        models.append(
            ProviderModelDescriptor(
                model_id=model_id,
                display_name=str(item["display_name"]),
                capabilities=tuple(str(cap) for cap in item.get("capabilities", [])),
                lifecycle=str(item["lifecycle"]),
                upstream_id=str(item["upstream_id"]),
                metadata=dict(item.get("metadata") or {}),
            )
        )
    return tuple(models)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ProviderRegistryError(f"Expected JSON object in {path}")
    return payload


def _load_descriptor(path: Path) -> ProviderDescriptor:
    payload = _load_json(path)
    provider_id = str(payload["provider_id"])
    route_name = str(payload["route_name"])
    if provider_id != route_name:
        raise ProviderRegistryError(
            f"provider_id and route_name must match for {path}: {provider_id!r} != {route_name!r}"
        )

    auth = payload.get("auth") or {}
    transport = payload.get("transport") or {}
    catalog = payload.get("catalog") or {}
    bootstrap = catalog.get("bootstrap") or {}
    discovery = catalog.get("discovery") or {}
    cache = catalog.get("cache") or {}

    return ProviderDescriptor(
        provider_id=provider_id,
        route_name=route_name,
        display_name=str(payload["display_name"]),
        auth_kind=str(auth.get("kind", "")),
        runtime_adapter=str(transport.get("runtime_adapter", "")),
        discovery_enabled=bool(discovery.get("enabled", False)),
        snapshot_enabled=bool(cache.get("snapshot_enabled", False)),
        bootstrap_models=_provider_models_from_payload(list(bootstrap.get("models") or [])),
        raw_payload=payload,
    )


def _snapshot_path(provider_id: str) -> Path:
    return Path(STATE_DIR) / provider_id / "catalog" / "models.json"


def _auth_available_for_provider(provider: ProviderDescriptor, availability: AuthAvailability) -> bool:
    kind = provider.auth_kind
    if kind == "gemini-oauth":
        return availability.gemini_quota
    if kind == "qwen-oauth":
        return availability.qwen_quota
    if kind == "gcp-service-account":
        return availability.vertex
    if kind == "openai-api-key":
        return False
    return False


class ProviderRegistry:
    def __init__(self, providers: tuple[ProviderDescriptor, ...]):
        self.providers = providers
        self._by_id = {provider.provider_id: provider for provider in providers}

    @classmethod
    def load(cls) -> "ProviderRegistry":
        registry_payload = _load_json(_registry_file())
        providers_payload = registry_payload.get("providers") or []
        if not isinstance(providers_payload, list) or not providers_payload:
            raise ProviderRegistryError("Provider registry must contain non-empty providers list")

        providers: list[ProviderDescriptor] = []
        seen_provider_ids: set[str] = set()
        seen_route_names: set[str] = set()
        root = _registry_root()

        for item in providers_payload:
            if not isinstance(item, dict):
                raise ProviderRegistryError("Each provider registry entry must be an object")
            descriptor_rel_path = item.get("descriptor_path")
            if not isinstance(descriptor_rel_path, str) or not descriptor_rel_path:
                raise ProviderRegistryError("Each provider registry entry must define descriptor_path")
            descriptor = _load_descriptor(root / descriptor_rel_path)
            if descriptor.provider_id in seen_provider_ids:
                raise ProviderRegistryError(f"Duplicate provider_id in registry: {descriptor.provider_id}")
            if descriptor.route_name in seen_route_names:
                raise ProviderRegistryError(f"Duplicate route_name in registry: {descriptor.route_name}")
            seen_provider_ids.add(descriptor.provider_id)
            seen_route_names.add(descriptor.route_name)
            providers.append(descriptor)

        return cls(tuple(providers))

    def get_provider(self, provider_id: str) -> ProviderDescriptor:
        try:
            return self._by_id[provider_id]
        except KeyError as exc:
            raise ProviderRegistryError(f"Unknown provider_id: {provider_id}") from exc

    def load_catalog(self, provider_id: str) -> ProviderCatalogSnapshot:
        provider = self.get_provider(provider_id)
        snapshot_path = _snapshot_path(provider.provider_id)
        if provider.discovery_enabled and provider.snapshot_enabled and snapshot_path.exists():
            payload = _load_json(snapshot_path)
            models = _provider_models_from_payload(list(payload.get("models") or []))
            if models:
                return ProviderCatalogSnapshot(
                    provider_id=provider.provider_id,
                    source=str(payload.get("source", "discovery")),
                    models=models,
                )

        return ProviderCatalogSnapshot(
            provider_id=provider.provider_id,
            source="bootstrap",
            models=provider.bootstrap_models,
        )

    def list_models_for_availability(self, availability: AuthAvailability) -> list[str]:
        model_ids: list[str] = []
        seen: set[str] = set()

        for provider in self.providers:
            if not _auth_available_for_provider(provider, availability):
                continue
            for model in self.load_catalog(provider.provider_id).models:
                if model.model_id in seen:
                    continue
                seen.add(model.model_id)
                model_ids.append(model.model_id)

        return model_ids


_provider_registry_singleton: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    global _provider_registry_singleton
    if _provider_registry_singleton is None:
        _provider_registry_singleton = ProviderRegistry.load()
    return _provider_registry_singleton
