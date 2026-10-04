"""
Report Data Assembler for Phase 5: Automated Geological Reporting
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Fetches and compiles verified relational mining records from extraction_db
according to the requested scope (document, project, or cumulative).
Calculates reserve reconciliation parameters strictly when source values exist.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.services.extraction.db import extraction_db
from app.schemas.extraction import (
    MineProject,
    Borehole,
    CoalSeam,
    ProximateAnalysis,
    GeologicalMetric,
)
from app.schemas.report import (
    ReportScope,
    ReportProvenanceItem,
    SeamReconciliationRow,
)


class ReportDataAssembler:
    """Assembles structured Phase 4 data scoped to a document, project, or cumulative database."""

    def __init__(self, db=None):
        self.db = db or extraction_db

    def assemble_data(
        self,
        scope: ReportScope,
        document_id: Optional[str] = None,
        source_document: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assembles all relevant domain entities and provenance citations
        strictly matching the requested scope without inventing data.
        """
        doc_filter = None
        source_filter = None
        search_filter = None

        if scope == ReportScope.DOCUMENT:
            # Prefer filename scoping so reports match Phase 4 document filters
            # even when a newer upload ID does not match stored extraction IDs.
            if source_document:
                source_filter = source_document
            else:
                doc_filter = document_id
        elif scope == ReportScope.PROJECT:
            search_filter = project_name

        # 1. Fetch Mines & Projects
        mines = self.db.list_mines(
            document_id=doc_filter,
            search=search_filter,
            source_document=source_filter,
        )

        # 2. Fetch Boreholes
        boreholes = self.db.list_boreholes(
            document_id=doc_filter,
            search=search_filter,
            source_document=source_filter,
        )

        # 3. Fetch Coal Seams
        seams = self.db.list_seams(
            document_id=doc_filter,
            search=search_filter,
            source_document=source_filter,
        )

        # 4. Fetch Proximate Analyses
        proximate = self.db.list_proximate_analyses(
            document_id=doc_filter,
            source_document=source_filter,
        )
        if search_filter:
            # If project scoped, filter proximate records whose borehole or seam links to project
            valid_borehole_ids = {b.borehole_id for b in boreholes if b.borehole_id}
            valid_seam_ids = {s.seam_id for s in seams if s.seam_id}
            proximate = [
                p for p in proximate
                if (p.borehole_id and p.borehole_id in valid_borehole_ids)
                or (p.seam_id and p.seam_id in valid_seam_ids)
            ]

        # 5. Fetch Geological Metrics
        metrics = self.db.list_metrics(
            document_id=doc_filter,
            source_document=source_filter,
        )
        if search_filter:
            # Filter metrics mentioning project name
            metrics = [
                m for m in metrics
                if search_filter.lower() in m.metric_name.lower()
                or (m.category and search_filter.lower() in m.category.lower())
            ]

        # 6. Build Provenance Items
        provenance_sources = self._extract_provenance(mines, boreholes, seams, proximate, metrics)

        # 7. Build Seam Reconciliation Records
        reconciliation_rows = self._calculate_reconciliation_rows(seams)

        return {
            "mines": mines,
            "boreholes": boreholes,
            "seams": seams,
            "proximate": proximate,
            "metrics": metrics,
            "provenance_sources": provenance_sources,
            "reconciliation_rows": reconciliation_rows,
            "total_records": len(mines) + len(boreholes) + len(seams) + len(proximate) + len(metrics),
        }

    def _extract_provenance(
        self,
        mines: List[MineProject],
        boreholes: List[Borehole],
        seams: List[CoalSeam],
        proximate: List[ProximateAnalysis],
        metrics: List[GeologicalMetric],
    ) -> List[ReportProvenanceItem]:
        """Extracts unique source citations across all consumed records."""
        seen = set()
        items: List[ReportProvenanceItem] = []

        def add_item(entity, entity_type: str, entity_id: str):
            key = (entity.document_id, entity.source_document, entity.source_page, entity.evidence_text)
            if key not in seen and entity.source_document:
                seen.add(key)
                items.append(
                    ReportProvenanceItem(
                        document_id=entity.document_id or "",
                        source_document=entity.source_document,
                        source_page=entity.source_page or 1,
                        evidence_text=entity.evidence_text or "",
                        entity_type=entity_type,
                        entity_id=entity_id,
                    )
                )

        for m in mines:
            add_item(m, "Mine / Project", m.project_name or m.id)
        for b in boreholes:
            add_item(b, "Borehole Log", b.borehole_id or b.id)
        for s in seams:
            add_item(s, "Coal Seam", s.seam_id or s.id)
        for p in proximate:
            add_item(p, "Proximate Analysis", f"{p.seam_id or 'Seam'}-{p.borehole_id or 'Borehole'}")
        for g in metrics:
            add_item(g, "Geological Metric", g.metric_name or g.id)

        # Sort citations by document name and page number
        items.sort(key=lambda x: (x.source_document, x.source_page))
        return items

    def _calculate_reconciliation_rows(self, seams: List[CoalSeam]) -> List[SeamReconciliationRow]:
        """
        Calculates recovery percentage and mining losses ONLY when both gross and extractable reserves exist.
        Never invents missing values; preserves None when unavailable.
        """
        rows: List[SeamReconciliationRow] = []

        for s in seams:
            recovery_pct = None
            mining_loss = None

            if s.gross_reserves_mt is not None and s.extractable_reserves_mt is not None:
                if s.gross_reserves_mt > 0:
                    recovery_pct = round((s.extractable_reserves_mt / s.gross_reserves_mt) * 100.0, 2)
                    mining_loss = round(s.gross_reserves_mt - s.extractable_reserves_mt, 3)

            rows.append(
                SeamReconciliationRow(
                    seam_id=s.seam_id,
                    borehole_id=s.borehole_id,
                    depth_from=s.depth_from,
                    depth_to=s.depth_to,
                    thickness=s.thickness,
                    coal_grade=s.coal_grade,
                    category=s.category,
                    gross_reserves_mt=s.gross_reserves_mt,
                    extractable_reserves_mt=s.extractable_reserves_mt,
                    recovery_percentage=recovery_pct,
                    mining_loss_mt=mining_loss,
                    source_document=s.source_document,
                    source_page=s.source_page,
                    evidence_text=s.evidence_text or "",
                )
            )

        return rows
