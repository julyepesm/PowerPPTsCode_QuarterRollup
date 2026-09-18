"""JSON-backed vehicle taxonomy used by both data grouping and image lookup."""

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


def normalize_vehicle_alias(value):
    """Normalize only for matching aliases explicitly declared in the catalog."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


@dataclass(frozen=True)
class VehicleResolution:
    raw_name: str
    canonical_name: str
    canonical_key: str
    brand_key: str
    model_id: Optional[str]
    images: dict
    classification: str
    status: str
    generate_slides: bool
    reason: str
    mapped: bool


class VehicleCatalog:
    """Load and validate the single source of vehicle taxonomy."""

    def __init__(self, base_path, config_path=None):
        self.base_path = os.path.abspath(base_path)
        self.config_path = os.path.abspath(
            config_path
            or os.path.join(
                self.base_path, "Scripts", "config", "vehicle_images.json"
            )
        )
        self.image_root = None
        self._defaults = {}
        self._unmapped = {}
        self._brands = {}
        self._alias_index = {}
        self._load()

    def _load(self):
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(
                f"Vehicle image catalog not found: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        image_root = config.get("image_root")
        brands = config.get("brands")
        defaults = config.get("defaults", {})
        unmapped = config.get("unmapped", {})
        if not isinstance(image_root, str) or not image_root.strip():
            raise ValueError("vehicle_images.json requires a non-empty image_root")
        if not isinstance(brands, dict):
            raise ValueError("vehicle_images.json requires a brands object")
        if not isinstance(defaults, dict):
            raise ValueError("vehicle_images.json defaults must be an object")
        if not isinstance(unmapped, dict):
            raise ValueError("vehicle_images.json unmapped must be an object")

        self._defaults = {
            "classification": str(defaults.get("classification", "vehicle")).strip(),
            "status": str(defaults.get("status", "approved")).strip(),
            "generate_slides": defaults.get("generate_slides", True),
            "reason": str(defaults.get("reason", "")).strip(),
        }
        self._unmapped = {
            "classification": str(unmapped.get("classification", "unmapped")).strip(),
            "status": str(unmapped.get("status", "pending_review")).strip(),
            "generate_slides": unmapped.get("generate_slides", False),
            "reason": str(unmapped.get("reason", "")).strip(),
        }
        for section_name, policy in (
            ("defaults", self._defaults),
            ("unmapped", self._unmapped),
        ):
            if not policy["classification"] or not policy["status"]:
                raise ValueError(
                    f"vehicle_images.json {section_name} requires classification and status"
                )
            if not isinstance(policy["generate_slides"], bool):
                raise ValueError(
                    f"vehicle_images.json {section_name}.generate_slides must be boolean"
                )

        self.image_root = os.path.abspath(
            os.path.join(self.base_path, image_root.replace("/", os.sep))
        )

        for raw_brand, brand_data in brands.items():
            brand_key = normalize_vehicle_alias(raw_brand)
            models = brand_data.get("models", []) if isinstance(brand_data, dict) else []
            if not isinstance(models, list):
                raise ValueError(f"Brand '{raw_brand}' must contain a models list")

            model_ids = set()
            alias_index = {}
            normalized_models = []
            for model in models:
                if not isinstance(model, dict):
                    raise ValueError(f"Invalid model entry under brand '{raw_brand}'")
                model_id = str(model.get("id", "")).strip()
                canonical_name = str(model.get("canonical_name", "")).strip()
                aliases = model.get("aliases", [])
                images = model.get("images", {})
                classification = str(
                    model.get("classification", self._defaults["classification"])
                ).strip()
                status = str(model.get("status", self._defaults["status"])).strip()
                generate_slides = model.get(
                    "generate_slides", self._defaults["generate_slides"]
                )
                reason = str(model.get("reason", self._defaults["reason"])).strip()
                if not model_id or not canonical_name:
                    raise ValueError(
                        f"Every model under '{raw_brand}' requires id and canonical_name"
                    )
                if model_id in model_ids:
                    raise ValueError(
                        f"Duplicate model id '{model_id}' under brand '{raw_brand}'"
                    )
                if not isinstance(aliases, list):
                    raise ValueError(
                        f"Aliases for '{canonical_name}' must be a list"
                    )
                if not isinstance(images, dict):
                    raise ValueError(
                        f"Images for '{canonical_name}' must be an object"
                    )
                if not classification or not status:
                    raise ValueError(
                        f"'{canonical_name}' requires classification and status"
                    )
                if not isinstance(generate_slides, bool):
                    raise ValueError(
                        f"generate_slides for '{canonical_name}' must be boolean"
                    )
                if not generate_slides and not reason:
                    raise ValueError(
                        f"Excluded model '{canonical_name}' requires a reason"
                    )

                model_ids.add(model_id)
                normalized_model = {
                    "id": model_id,
                    "canonical_name": canonical_name,
                    "aliases": list(aliases),
                    "images": {
                        "insights": images.get("insights"),
                        "exec": images.get("exec"),
                    },
                    "classification": classification,
                    "status": status,
                    "generate_slides": generate_slides,
                    "reason": reason,
                }
                normalized_models.append(normalized_model)

                for alias in [canonical_name, *aliases]:
                    alias_key = normalize_vehicle_alias(alias)
                    if not alias_key:
                        raise ValueError(
                            f"Empty alias found for '{canonical_name}'"
                        )
                    existing = alias_index.get(alias_key)
                    if existing and existing["id"] != model_id:
                        raise ValueError(
                            f"Alias '{alias}' is assigned to both "
                            f"'{existing['canonical_name']}' and '{canonical_name}' "
                            f"under brand '{raw_brand}'"
                        )
                    alias_index[alias_key] = normalized_model

            self._brands[brand_key] = normalized_models
            self._alias_index[brand_key] = alias_index

    def resolve(self, brand, vehicle_name):
        """Resolve a raw Power BI value to its canonical catalog model."""
        raw_name = "" if vehicle_name is None else str(vehicle_name).strip()
        brand_key = normalize_vehicle_alias(brand)
        alias_key = normalize_vehicle_alias(raw_name)
        model = self._alias_index.get(brand_key, {}).get(alias_key)
        if model:
            return VehicleResolution(
                raw_name=raw_name,
                canonical_name=model["canonical_name"],
                canonical_key=f"{brand_key}:{model['id']}",
                brand_key=brand_key,
                model_id=model["id"],
                images=model["images"],
                classification=model["classification"],
                status=model["status"],
                generate_slides=model["generate_slides"],
                reason=model["reason"],
                mapped=True,
            )

        # Unmapped values remain independent; aggressive alias normalization is
        # never used to merge data unless the JSON explicitly declares it.
        unmapped_identity = raw_name.casefold()
        return VehicleResolution(
            raw_name=raw_name,
            canonical_name=raw_name,
            canonical_key=f"{brand_key}:unmapped:{unmapped_identity}",
            brand_key=brand_key,
            model_id=None,
            images={"insights": None, "exec": None},
            classification=self._unmapped["classification"],
            status=self._unmapped["status"],
            generate_slides=self._unmapped["generate_slides"],
            reason=self._unmapped["reason"],
            mapped=False,
        )

    def resolve_image_path(self, brand, vehicle_name, slide_kind):
        """Return the configured image path, or ``None`` with no filename fallback."""
        kind_key = str(slide_kind).lower().strip()
        if kind_key == "summary":
            kind_key = "exec"
        if kind_key not in {"insights", "exec"}:
            return None

        resolution = self.resolve(brand, vehicle_name)
        relative_path = resolution.images.get(kind_key)
        if not relative_path or not isinstance(relative_path, str):
            return None

        candidate = os.path.abspath(
            os.path.join(self.image_root, relative_path.replace("/", os.sep))
        )
        try:
            if os.path.commonpath([self.image_root, candidate]) != self.image_root:
                return None
        except ValueError:
            return None
        return candidate if os.path.isfile(candidate) else None

    def validate_configured_assets(self):
        """Return configured image paths that do not exist under Design/Cars."""
        missing = []
        for brand_key, models in self._brands.items():
            for model in models:
                for kind_key, relative_path in model["images"].items():
                    if not relative_path:
                        continue
                    candidate = os.path.abspath(
                        os.path.join(
                            self.image_root, relative_path.replace("/", os.sep)
                        )
                    )
                    if not os.path.isfile(candidate):
                        missing.append({
                            "brand": brand_key,
                            "model": model["canonical_name"],
                            "kind": kind_key,
                            "path": relative_path,
                        })
        return missing


@lru_cache(maxsize=8)
def get_vehicle_catalog(base_path, config_path=None):
    """Return a cached catalog for a project root/configuration pair."""
    resolved_base = os.path.abspath(base_path)
    resolved_config = os.path.abspath(config_path) if config_path else None
    return VehicleCatalog(resolved_base, resolved_config)
