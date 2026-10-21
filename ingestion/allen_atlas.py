"""
Allen Human Brain Atlas — Region Ontology Ingester.
Downloads the ARA (Allen Reference Atlas) ontology via the Brain Map API
and populates the brain_atlases + brain_regions tables.

No registration required. Direct API access.
API: http://api.brain-map.org/api/v2/structure_graph_download/10.json
     (Structure graph 10 = Human, ARA)
"""

import requests
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.orm import BrainAtlas, BrainRegion

logger = logging.getLogger("manas.ingestion.allen_atlas")

HUMAN_STRUCTURE_GRAPH_URL = "http://api.brain-map.org/api/v2/structure_graph_download/10.json"
ATLAS_SHORT_NAME = "ARA_HUMAN"
ATLAS_VERSION = "2013-human-v1"


class AllenAtlasIngester:
    """
    Ingests the Allen Human Reference Atlas brain-region ontology.
    Populates brain_atlases and brain_regions tables.
    Must be run before any data ingestion.
    """

    def __init__(self, db: Session):
        self.db = db

    def run(self) -> BrainAtlas:
        logger.info("Starting Allen Human Brain Atlas ontology ingestion")
        atlas = self._get_or_create_atlas()
        logger.info(f"Atlas: {atlas.name} (id={atlas.atlas_id})")

        data = self._fetch_ontology()
        children = data.get("msg", [{}])[0].get("children", [])
        count = [0]
        self._ingest_children(children, atlas.atlas_id, parent_id=None, depth=0, count=count)
        self.db.commit()
        logger.info(f"Ingested {count[0]} brain regions")
        return atlas

    def _get_or_create_atlas(self) -> BrainAtlas:
        atlas = self.db.query(BrainAtlas).filter(BrainAtlas.short_name == ATLAS_SHORT_NAME).first()
        if atlas:
            return atlas
        atlas = BrainAtlas(
            name="Allen Human Reference Atlas",
            short_name=ATLAS_SHORT_NAME,
            version=ATLAS_VERSION,
            species="Homo sapiens",
            source_url=HUMAN_STRUCTURE_GRAPH_URL,
            description=(
                "Allen Institute for Brain Science Human Reference Atlas. "
                "Ontology of brain structures used in Allen human brain studies."
            ),
        )
        self.db.add(atlas)
        self.db.commit()
        self.db.refresh(atlas)
        return atlas

    def _fetch_ontology(self) -> dict:
        logger.info(f"Fetching ontology from {HUMAN_STRUCTURE_GRAPH_URL}")
        resp = requests.get(HUMAN_STRUCTURE_GRAPH_URL, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _ingest_children(
        self,
        children: list,
        atlas_id: int,
        parent_id: int | None,
        depth: int,
        count: list,
    ):
        if not hasattr(self, "_existing_cache"):
            self._existing_cache = {
                str(r[0]): r[1]
                for r in self.db.query(BrainRegion.source_region_id, BrainRegion.region_id)
                .filter(BrainRegion.atlas_id == atlas_id)
                .all()
            }

        for node in children:
            source_id = str(node.get("id", ""))
            if source_id in self._existing_cache:
                region_id = self._existing_cache[source_id]
            else:
                name = node.get("name", "Unknown")
                acronym = node.get("acronym", "")
                region = BrainRegion(
                    atlas_id=atlas_id,
                    source_region_id=source_id,
                    name=name,
                    abbreviation=acronym,
                    hemisphere="bilateral",    # ARA is bilateral by default
                    parent_region_id=parent_id,
                    anatomical_category=self._infer_category(name, acronym),
                    lobe=self._infer_lobe(name, acronym),
                    depth=depth,
                    is_leaf=len(node.get("children", [])) == 0,
                )
                self.db.add(region)
                self.db.flush()
                region_id = region.region_id
                self._existing_cache[source_id] = region_id
                count[0] += 1
                if count[0] % 50 == 0:
                    self.db.commit()

            sub_children = node.get("children", [])
            if sub_children:
                self._ingest_children(sub_children, atlas_id, region_id, depth + 1, count)

    @staticmethod
    def _infer_category(name: str, acronym: str) -> str:
        name_lower = name.lower()
        if any(t in name_lower for t in ["cortex", "cortical", "gyrus", "sulcus"]):
            return "cortical"
        if any(t in name_lower for t in ["hippocampus", "amygdala", "thalamus",
                                          "basal ganglia", "striatum", "putamen",
                                          "caudate", "pallidum", "substantia nigra"]):
            return "subcortical"
        if any(t in name_lower for t in ["cerebellum", "cerebellar"]):
            return "cerebellar"
        if any(t in name_lower for t in ["brainstem", "pons", "medulla", "midbrain"]):
            return "brainstem"
        if any(t in name_lower for t in ["white matter", "corpus callosum"]):
            return "white_matter"
        if any(t in name_lower for t in ["hippocamp", "entorhinal", "parahippocampal"]):
            return "limbic"
        return "other"

    @staticmethod
    def _infer_lobe(name: str, acronym: str) -> str | None:
        name_lower = name.lower()
        if any(t in name_lower for t in ["frontal", "prefrontal", "premotor"]):
            return "frontal"
        if any(t in name_lower for t in ["temporal", "superior temporal", "middle temporal"]):
            return "temporal"
        if any(t in name_lower for t in ["parietal", "somatosensory"]):
            return "parietal"
        if any(t in name_lower for t in ["occipital", "visual"]):
            return "occipital"
        if any(t in name_lower for t in ["cingulate", "insular", "insula"]):
            return "limbic"
        return None
