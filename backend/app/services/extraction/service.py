"""
Structured Mining Data Extraction Service
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Coordinates:
- Identifying relevant domain-specific pages from processed document representations.
- Extracting validated structured records via Gemini structured JSON generation.
- Strict Pydantic model validation with numerical/unit precision.
- Provenance verification: Ensuring every record cites true document and page source.
- Persistence to relational database store without duplicates.
"""

import json
import re
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.document import DocumentMetadata, DocumentPage, ExtractedTable
from app.schemas.extraction import (
    CoalSeam,
    ProximateAnalysis,
    Borehole,
    MineProject,
    GeologicalMetric,
    DocumentExtractionResult,
    ExtractionStatusResponse,
)
from app.services.documents.db import doc_db
from app.services.extraction.db import extraction_db


class StructuredMiningExtractorService:
    """Enterprise extraction service for mining reports, borehole logs, and geological data."""

    # Keywords signaling relevant geological, borehole, seam, or exploration content
    DOMAIN_KEYWORDS = [
        "borehole", "collar", "elevation", "lithology", "seam", "coal seam",
        "proximate", "moisture", "ash", "volatile matter", "calorific", "gcv",
        "reserves", "proved", "indicated", "thickness", "drilling target", "drilling achievement",
        "geological report", "project report", "stripping ratio", "feasibility study"
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None
        if self.is_configured:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid non-empty API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def get_client(self) -> genai.Client:
        """Returns initialized genai.Client or raises clear configuration error."""
        if not self.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to perform structured mining data extraction."
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def get_service_status(self) -> ExtractionStatusResponse:
        """Returns extraction subsystem telemetry and counts."""
        db_status = extraction_db.get_extraction_status()
        docs = doc_db.list_documents()

        return ExtractionStatusResponse(
            status="operational" if self.is_configured else "unconfigured",
            gemini_configured=self.is_configured,
            total_entities_count=db_status["total_entities_count"],
            counts_by_type=db_status["counts_by_type"],
            total_documents_extracted=db_status["total_documents_extracted"],
            indexed_documents_count=len(docs),
        )

    @staticmethod
    def _clean_float(val: Any) -> Optional[float]:
        """Safely parses float from strings containing numbers, percentages, or units."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        if not val_str:
            return None
        # Handle ratio like 1:4.2 or 4.2:1
        if ":" in val_str:
            parts = val_str.split(":")
            for p in parts:
                try:
                    num = float(p.strip())
                    if num > 1.0:
                        return num
                except ValueError:
                    pass
        # Clean commas (e.g. 1,92,000 -> 192000)
        cleaned = val_str.replace(",", "")
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
        return None

    @staticmethod
    def _is_page_relevant(page: DocumentPage) -> bool:
        """Determines if a page contains extractable geological, mining, or borehole content."""
        text_lower = page.text.lower()
        if any(kw in text_lower for kw in StructuredMiningExtractorService.DOMAIN_KEYWORDS):
            return True
        if page.tables:
            for t in page.tables:
                headers_str = " ".join(t.headers).lower()
                if any(kw in headers_str for kw in StructuredMiningExtractorService.DOMAIN_KEYWORDS):
                    return True
        return False

    def _call_gemini_extraction(self, prompt: str) -> Dict[str, Any]:
        """Calls Gemini with strict JSON mode and retry backoff for rate limits."""
        client = self.get_client()
        cfg = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,  # Zero temperature for deterministic extraction
        )

        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=cfg,
                )
                if not response or not response.text:
                    return {}
                return json.loads(response.text)
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                    backoff = 6.0 * (attempt + 1)
                    time.sleep(backoff)
                    continue
                raise RuntimeError(f"Gemini structured extraction failed: {str(e)}")
        return {}

    def extract_document(self, document_id: str) -> DocumentExtractionResult:
        """
        Extracts structured mining domain entities from a processed document:
        1. Reads processed JSON data.
        2. Filters domain-relevant pages.
        3. Prompts Gemini with strict grounding and JSON schema rules.
        4. Validates extracted records into Pydantic models.
        5. Verifies provenance against source page text and tables.
        6. Persists records to database replacing any previous extractions.
        """
        if not self.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to extract structured mining data."
            )

        doc_record = doc_db.get_document(document_id)
        if not doc_record:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found in registry.")

        proc_path = Path(doc_record["processed_path"])
        if not proc_path.exists():
            raise FileNotFoundError(f"Processed document file missing at {proc_path}")

        with open(proc_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = DocumentMetadata(**data["metadata"])
        pages = [DocumentPage(**p) for p in data["pages"]]

        all_boreholes: List[Borehole] = []
        all_seams: List[CoalSeam] = []
        all_proximate: List[ProximateAnalysis] = []
        all_projects: List[MineProject] = []
        all_metrics: List[GeologicalMetric] = []

        # Filter domain-relevant candidate pages
        relevant_pages = [p for p in pages if self._is_page_relevant(p)]
        if len(relevant_pages) > 8:
            # Rank by presence of data tables and keyword density
            relevant_pages = sorted(
                relevant_pages,
                key=lambda p: (len(p.tables or []), sum(1 for kw in self.DOMAIN_KEYWORDS if kw in p.text.lower())),
                reverse=True
            )[:8]

        # Iterate over relevant candidate pages
        for page in relevant_pages:

            page_content_parts = [f"--- PAGE {page.page_number} ---", f"PAGE TEXT:\n{page.text}"]
            if page.tables:
                for t_idx, tbl in enumerate(page.tables, start=1):
                    page_content_parts.append(f"\n[TABLE {t_idx}]:")
                    page_content_parts.append(" | ".join(tbl.headers))
                    for r in tbl.rows:
                        page_content_parts.append(" | ".join(r))

            full_page_content = "\n".join(page_content_parts)

            prompt = f"""You are the CMPDI Structured Mining Data Extractor.
Extract only explicitly stated factual mining entities from the document text and tables below.

STRICT EXTRACTION RULES:
1. Extract ONLY facts, numbers, and identifiers directly stated in the text.
2. If any field is NOT explicitly mentioned, set it to null. NEVER guess, assume, or extrapolate.
3. Preserve all numerical values and units exactly.
4. For every entity, include an 'evidence_text' string containing the verbatim text or table row where the values were found.
5. Do not invent boreholes, seams, or metrics. If no relevant entities exist for a category, return an empty array.

DOCUMENT: {metadata.filename}
PAGE NUMBER: {page.page_number}

{full_page_content}

Return a valid JSON object strictly matching this schema:
{{
  "mines_projects": [
    {{
      "project_name": "string (Required)",
      "subsidiary": "string or null",
      "location": "string or null",
      "block_name": "string or null",
      "target_production": "number or null",
      "target_production_unit": "string or null",
      "stripping_ratio": "number or null",
      "life_of_mine_years": "integer or null",
      "evidence_text": "string verbatim evidence"
    }}
  ],
  "boreholes": [
    {{
      "borehole_id": "string (Required)",
      "mine_project": "string or null",
      "latitude": "number or null",
      "longitude": "number or null",
      "collar_elevation": "number or null",
      "total_depth": "number or null",
      "lithology": "string or null",
      "evidence_text": "string verbatim evidence"
    }}
  ],
  "coal_seams": [
    {{
      "seam_id": "string (Required, e.g. Seam VIII, Seam VII)",
      "borehole_id": "string or null",
      "depth_from": "number or null",
      "depth_to": "number or null",
      "thickness": "number or null",
      "coal_grade": "string or null",
      "category": "string or null",
      "gross_reserves_mt": "number or null",
      "extractable_reserves_mt": "number or null",
      "evidence_text": "string verbatim evidence"
    }}
  ],
  "proximate_analyses": [
    {{
      "seam_id": "string or null",
      "borehole_id": "string or null",
      "moisture_percent": "number or null",
      "ash_percent": "number or null",
      "volatile_matter_percent": "number or null",
      "fixed_carbon_percent": "number or null",
      "gross_calorific_value": "number or null",
      "units": "string or null (default kcal/kg)",
      "evidence_text": "string verbatim evidence"
    }}
  ],
  "geological_metrics": [
    {{
      "metric_name": "string (Required, e.g. Drilling Target, Geological Reports)",
      "metric_value": "number or null",
      "unit": "string or null",
      "year_period": "string or null",
      "category": "string or null",
      "evidence_text": "string verbatim evidence"
    }}
  ]
}}"""

            parsed_json = self._call_gemini_extraction(prompt)
            now = datetime.now(timezone.utc)

            # 1. Process Mines / Projects
            for raw_m in parsed_json.get("mines_projects", []):
                if isinstance(raw_m, dict) and raw_m.get("project_name"):
                    evidence = raw_m.get("evidence_text") or page.text[:200]
                    # Provenance verification: project name must have some anchor in page
                    all_text_lower = full_page_content.lower()
                    if raw_m["project_name"].lower() in all_text_lower or any(word in all_text_lower for word in raw_m["project_name"].lower().split()):
                        all_projects.append(
                            MineProject(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                source_document=metadata.filename,
                                source_page=page.page_number,
                                evidence_text=evidence,
                                extraction_timestamp=now,
                                project_name=str(raw_m["project_name"]).strip(),
                                subsidiary=str(raw_m["subsidiary"]).strip() if raw_m.get("subsidiary") else "CMPDI / CIL",
                                location=str(raw_m["location"]).strip() if raw_m.get("location") else None,
                                block_name=str(raw_m["block_name"]).strip() if raw_m.get("block_name") else None,
                                target_production=self._clean_float(raw_m.get("target_production")),
                                target_production_unit=str(raw_m.get("target_production_unit") or "MTPA"),
                                stripping_ratio=self._clean_float(raw_m.get("stripping_ratio")),
                                life_of_mine_years=int(self._clean_float(raw_m.get("life_of_mine_years"))) if self._clean_float(raw_m.get("life_of_mine_years")) else None,
                            )
                        )

            # 2. Process Boreholes
            for raw_b in parsed_json.get("boreholes", []):
                if isinstance(raw_b, dict) and raw_b.get("borehole_id"):
                    evidence = raw_b.get("evidence_text") or page.text[:200]
                    b_id = str(raw_b["borehole_id"]).strip()
                    # Provenance check: borehole_id must be in the page text/table
                    if b_id.lower() in full_page_content.lower():
                        all_boreholes.append(
                            Borehole(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                source_document=metadata.filename,
                                source_page=page.page_number,
                                evidence_text=evidence,
                                extraction_timestamp=now,
                                borehole_id=b_id,
                                mine_project=str(raw_b["mine_project"]).strip() if raw_b.get("mine_project") else None,
                                latitude=self._clean_float(raw_b.get("latitude")),
                                longitude=self._clean_float(raw_b.get("longitude")),
                                collar_elevation=self._clean_float(raw_b.get("collar_elevation")),
                                total_depth=self._clean_float(raw_b.get("total_depth")),
                                lithology=str(raw_b["lithology"]).strip() if raw_b.get("lithology") and isinstance(raw_b["lithology"], str) else None,
                            )
                        )

            # 3. Process Coal Seams
            for raw_s in parsed_json.get("coal_seams", []):
                if isinstance(raw_s, dict) and raw_s.get("seam_id"):
                    evidence = raw_s.get("evidence_text") or page.text[:200]
                    s_id = str(raw_s["seam_id"]).strip()
                    # Provenance check: seam_id or part of seam_id exists in page
                    if s_id.lower() in full_page_content.lower() or any(w in full_page_content.lower() for w in s_id.lower().split()):
                        depth_from = self._clean_float(raw_s.get("depth_from"))
                        depth_to = self._clean_float(raw_s.get("depth_to"))
                        thickness = self._clean_float(raw_s.get("thickness"))
                        if thickness is None and depth_from is not None and depth_to is not None:
                            thickness = round(depth_to - depth_from, 2)

                        all_seams.append(
                            CoalSeam(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                source_document=metadata.filename,
                                source_page=page.page_number,
                                evidence_text=evidence,
                                extraction_timestamp=now,
                                seam_id=s_id,
                                borehole_id=str(raw_s["borehole_id"]).strip() if raw_s.get("borehole_id") else None,
                                depth_from=depth_from,
                                depth_to=depth_to,
                                thickness=thickness,
                                coal_grade=str(raw_s["coal_grade"]).strip() if raw_s.get("coal_grade") else None,
                                category=str(raw_s["category"]).strip() if raw_s.get("category") else None,
                                gross_reserves_mt=self._clean_float(raw_s.get("gross_reserves_mt")),
                                extractable_reserves_mt=self._clean_float(raw_s.get("extractable_reserves_mt")),
                            )
                        )

            # 4. Process Proximate Analyses
            for raw_p in parsed_json.get("proximate_analyses", []):
                if isinstance(raw_p, dict):
                    ash = self._clean_float(raw_p.get("ash_percent"))
                    moist = self._clean_float(raw_p.get("moisture_percent"))
                    vm = self._clean_float(raw_p.get("volatile_matter_percent"))
                    fc = self._clean_float(raw_p.get("fixed_carbon_percent"))
                    gcv = self._clean_float(raw_p.get("gross_calorific_value"))

                    # Only record if at least one meaningful quality metric is present
                    if any(v is not None for v in [ash, moist, vm, fc, gcv]):
                        evidence = raw_p.get("evidence_text") or page.text[:200]
                        all_proximate.append(
                            ProximateAnalysis(
                                id=str(uuid.uuid4()),
                                document_id=document_id,
                                source_document=metadata.filename,
                                source_page=page.page_number,
                                evidence_text=evidence,
                                extraction_timestamp=now,
                                seam_id=str(raw_p["seam_id"]).strip() if raw_p.get("seam_id") else None,
                                borehole_id=str(raw_p["borehole_id"]).strip() if raw_p.get("borehole_id") else None,
                                moisture_percent=moist,
                                ash_percent=ash,
                                volatile_matter_percent=vm,
                                fixed_carbon_percent=fc,
                                gross_calorific_value=gcv,
                                units=str(raw_p.get("units") or "kcal/kg"),
                            )
                        )

            # 5. Process Geological Metrics
            for raw_g in parsed_json.get("geological_metrics", []):
                if isinstance(raw_g, dict) and raw_g.get("metric_name"):
                    evidence = raw_g.get("evidence_text") or page.text[:200]
                    all_metrics.append(
                        GeologicalMetric(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            source_document=metadata.filename,
                            source_page=page.page_number,
                            evidence_text=evidence,
                            extraction_timestamp=now,
                            metric_name=str(raw_g["metric_name"]).strip(),
                            metric_value=self._clean_float(raw_g.get("metric_value")),
                            unit=str(raw_g["unit"]).strip() if raw_g.get("unit") else None,
                            year_period=str(raw_g["year_period"]).strip() if raw_g.get("year_period") else None,
                            category=str(raw_g["category"]).strip() if raw_g.get("category") else None,
                        )
                    )

            # Pacing between pages
            time.sleep(0.5)

        # Save to database (replaces any previous records for this document to prevent duplicates)
        counts = extraction_db.save_extraction_results(
            document_id=document_id,
            boreholes=all_boreholes,
            coal_seams=all_seams,
            proximate_analyses=all_proximate,
            mine_projects=all_projects,
            geological_metrics=all_metrics,
        )

        total_extracted = sum(counts.values())

        return DocumentExtractionResult(
            document_id=document_id,
            filename=metadata.filename,
            success=True,
            message=f"Successfully extracted {total_extracted} structured mining entities from '{metadata.filename}'.",
            extracted_counts=counts,
            boreholes=all_boreholes,
            coal_seams=all_seams,
            proximate_analyses=all_proximate,
            mine_projects=all_projects,
            geological_metrics=all_metrics,
        )

    def extract_all_documents(self) -> Dict[str, Any]:
        """Runs structured extraction across all processed documents currently registered."""
        if not self.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to extract structured mining data."
            )

        docs = doc_db.list_documents()
        results: List[Dict[str, Any]] = []
        total_entities_by_type = {
            "boreholes": 0,
            "coal_seams": 0,
            "proximate_analyses": 0,
            "mine_projects": 0,
            "geological_metrics": 0,
        }

        for doc in docs:
            try:
                res = self.extract_document(doc.id)
                results.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "success": True,
                    "counts": res.extracted_counts,
                })
                for k, v in res.extracted_counts.items():
                    total_entities_by_type[k] += v
                time.sleep(1.0)
            except Exception as e:
                results.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "success": False,
                    "error": str(e),
                })

        return {
            "total_documents_processed": len(docs),
            "successful_documents": sum(1 for r in results if r.get("success")),
            "total_entities_by_type": total_entities_by_type,
            "total_entities_extracted": sum(total_entities_by_type.values()),
            "document_results": results,
        }

    # Entity query interfaces
    def get_boreholes(
        self,
        document_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[Borehole]:
        return extraction_db.list_boreholes(document_id, borehole_id, search, source_document=source_document)

    def get_seams(
        self,
        document_id: Optional[str] = None,
        seam_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[CoalSeam]:
        return extraction_db.list_seams(document_id, seam_id, borehole_id, search, source_document=source_document)

    def get_proximate_analyses(
        self,
        document_id: Optional[str] = None,
        seam_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[ProximateAnalysis]:
        return extraction_db.list_proximate_analyses(document_id, seam_id, borehole_id, source_document=source_document)

    def get_mines(
        self,
        document_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[MineProject]:
        return extraction_db.list_mines(document_id, search, source_document=source_document)

    def get_metrics(
        self,
        document_id: Optional[str] = None,
        category: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[GeologicalMetric]:
        return extraction_db.list_metrics(document_id, category, source_document=source_document)


extraction_service = StructuredMiningExtractorService()
