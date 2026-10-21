"""
Region Mapper — maps source region strings to canonical brain_regions records.
Handles Allen Aging's 4 regions: FWM, HIP, PCx, TCx.
"""

import logging
from sqlalchemy.orm import Session
from backend.models.orm import BrainRegion, BrainAtlas, RegionMapping

logger = logging.getLogger("manas.atlas.region_mapper")

# Allen Aging has 4 structure acronyms → map to canonical names
ALLEN_AGING_REGION_MAP = {
    "FWM": {
        "name": "Frontal White Matter",
        "hemisphere": "bilateral",
        "anatomical_category": "white_matter",
        "lobe": "frontal",
        "abbreviation": "FWM",
    },
    "HIP": {
        "name": "Hippocampus",
        "hemisphere": "bilateral",
        "anatomical_category": "limbic",
        "lobe": "temporal",
        "abbreviation": "HIP",
    },
    "PCx": {
        "name": "Parietal Cortex",
        "hemisphere": "bilateral",
        "anatomical_category": "cortical",
        "lobe": "parietal",
        "abbreviation": "PCx",
    },
    "TCx": {
        "name": "Temporal Cortex",
        "hemisphere": "bilateral",
        "anatomical_category": "cortical",
        "lobe": "temporal",
        "abbreviation": "TCx",
    },
}

ATLAS_SHORT_NAME = "ARA_HUMAN"


class RegionMapper:
    """
    Maps source region strings → canonical BrainRegion records.
    For Allen Aging, creates the 4 known regions if not yet present.
    Flags ambiguous mappings for review.
    """

    def __init__(self, db: Session):
        self.db = db
        self._cache: dict[str, int | None] = {}
        self.atlas = self._get_or_create_atlas()

    def _get_or_create_atlas(self) -> BrainAtlas:
        atlas = self.db.query(BrainAtlas).filter(
            BrainAtlas.short_name == ATLAS_SHORT_NAME
        ).first()
        if not atlas:
            atlas = BrainAtlas(
                name="Allen Human Reference Atlas",
                short_name=ATLAS_SHORT_NAME,
                version="2013-human-v1",
                species="Homo sapiens",
                source_url="http://api.brain-map.org/api/v2/structure_graph_download/10.json",
                description="Allen Institute Human Reference Atlas — brain region ontology.",
            )
            self.db.add(atlas)
            self.db.commit()
            self.db.refresh(atlas)
        return atlas

    def ensure_allen_aging_regions(self):
        """Create canonical records for all 4 Allen Aging brain regions."""
        for acronym, info in ALLEN_AGING_REGION_MAP.items():
            existing = self.db.query(BrainRegion).filter(
                BrainRegion.atlas_id == self.atlas.atlas_id,
                BrainRegion.abbreviation == acronym,
            ).first()
            if not existing:
                region = BrainRegion(
                    atlas_id=self.atlas.atlas_id,
                    name=info["name"],
                    abbreviation=info["abbreviation"],
                    hemisphere=info["hemisphere"],
                    anatomical_category=info["anatomical_category"],
                    lobe=info["lobe"],
                    depth=1,
                    is_leaf=True,
                )
                self.db.add(region)
                self.db.flush()
                # Record the mapping
                mapping = RegionMapping(
                    source_name=acronym,
                    source_dataset="allen_aging",
                    canonical_region_id=region.region_id,
                    mapping_method="manual",
                    confidence="HIGH",
                    reviewer="MANAS-system",
                    notes=f"Allen Aging acronym {acronym} → {info['name']}",
                )
                self.db.add(mapping)
        self.db.commit()

    def map(
        self,
        source_name: str,
        source_dataset: str = "allen_aging",
        hemisphere: str = "bilateral",
    ) -> int | None:
        """
        Map a source region name to a canonical region_id.
        Returns None if mapping cannot be resolved (flagged for review).
        """
        return self._map_internal(source_name, source_dataset, hemisphere)

    map_region = map

    def _map_internal(
        self,
        source_name: str,
        source_dataset: str = "allen_aging",
        hemisphere: str = "bilateral",
    ) -> int | None:
        """
        Map a source region name to a canonical region_id.
        Returns None if mapping cannot be resolved (flagged for review).
        """
        cache_key = f"{source_dataset}:{source_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Ensure Allen Aging regions exist
        self.ensure_allen_aging_regions()

        # 1. Check existing mapping record
        existing = self.db.query(RegionMapping).filter(
            RegionMapping.source_name == source_name,
            RegionMapping.source_dataset == source_dataset,
        ).first()
        if existing and existing.confidence != "MANUAL_REQUIRED":
            self._cache[cache_key] = existing.canonical_region_id
            return existing.canonical_region_id

        # 2. Exact abbreviation match in canonical regions
        region = self.db.query(BrainRegion).filter(
            BrainRegion.atlas_id == self.atlas.atlas_id,
            BrainRegion.abbreviation == source_name,
        ).first()

        if not region:
            # 3. Name match (case-insensitive)
            region = self.db.query(BrainRegion).filter(
                BrainRegion.atlas_id == self.atlas.atlas_id,
                BrainRegion.name.ilike(source_name),
            ).first()

        if region:
            # Record mapping
            if not existing:
                m = RegionMapping(
                    source_name=source_name,
                    source_dataset=source_dataset,
                    canonical_region_id=region.region_id,
                    mapping_method="exact",
                    confidence="HIGH",
                    reviewer="MANAS-system",
                )
                self.db.add(m)
                self.db.commit()
            self._cache[cache_key] = region.region_id
            return region.region_id

        # 4. Unresolvable — flag for manual review
        logger.warning(
            f"Region '{source_name}' from dataset '{source_dataset}' "
            "cannot be mapped → MANUAL_REQUIRED"
        )
        if not existing:
            m = RegionMapping(
                source_name=source_name,
                source_dataset=source_dataset,
                canonical_region_id=None,
                mapping_method="unresolved",
                confidence="MANUAL_REQUIRED",
                notes="Automatic mapping failed — requires human review",
            )
            self.db.add(m)
            self.db.commit()
        self._cache[cache_key] = None
        return None

    def get_unresolved_mappings(self) -> list[dict]:
        """Return all mappings requiring manual review."""
        unresolved = self.db.query(RegionMapping).filter(
            RegionMapping.confidence == "MANUAL_REQUIRED"
        ).all()
        return [
            {
                "mapping_id": m.mapping_id,
                "source_name": m.source_name,
                "source_dataset": m.source_dataset,
                "notes": m.notes,
            }
            for m in unresolved
        ]
