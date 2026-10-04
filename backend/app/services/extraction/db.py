"""
Relational Database Store for Structured Mining Entities
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Provides persistent, ACID-compliant storage for validated mining data:
- mines/projects
- boreholes
- coal seams
- proximate analyses
- geological report metrics

Enforces:
- Document provenance (document_id, filename, page_number, evidence_text)
- Clean deduplication upon document reprocessing
- Easy migration path to PostgreSQL
"""

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.schemas.extraction import (
    CoalSeam,
    ProximateAnalysis,
    Borehole,
    MineProject,
    GeologicalMetric,
)


class ExtractionDatabase:
    """Manages relational SQLite storage for structured mining domain entities."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.BASE_DIR / "storage" / "extraction.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes relational schema for mining entities."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mines_projects (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    subsidiary TEXT,
                    location TEXT,
                    block_name TEXT,
                    target_production REAL,
                    target_production_unit TEXT,
                    stripping_ratio REAL,
                    life_of_mine_years INTEGER,
                    source_document TEXT NOT NULL,
                    source_page INTEGER NOT NULL,
                    evidence_text TEXT NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS boreholes (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    borehole_id TEXT NOT NULL,
                    mine_project TEXT,
                    latitude REAL,
                    longitude REAL,
                    collar_elevation REAL,
                    total_depth REAL,
                    lithology TEXT,
                    source_document TEXT NOT NULL,
                    source_page INTEGER NOT NULL,
                    evidence_text TEXT NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coal_seams (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    seam_id TEXT NOT NULL,
                    borehole_id TEXT,
                    depth_from REAL,
                    depth_to REAL,
                    thickness REAL,
                    coal_grade TEXT,
                    category TEXT,
                    gross_reserves_mt REAL,
                    extractable_reserves_mt REAL,
                    source_document TEXT NOT NULL,
                    source_page INTEGER NOT NULL,
                    evidence_text TEXT NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS proximate_analyses (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    seam_id TEXT,
                    borehole_id TEXT,
                    moisture_percent REAL,
                    ash_percent REAL,
                    volatile_matter_percent REAL,
                    fixed_carbon_percent REAL,
                    gross_calorific_value REAL,
                    units TEXT,
                    source_document TEXT NOT NULL,
                    source_page INTEGER NOT NULL,
                    evidence_text TEXT NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS geological_metrics (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    unit TEXT,
                    year_period TEXT,
                    category TEXT,
                    source_document TEXT NOT NULL,
                    source_page INTEGER NOT NULL,
                    evidence_text TEXT NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
                """
            )
            # Create indexing for rapid queries by document and entity IDs
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mines_doc ON mines_projects(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_boreholes_doc ON boreholes(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_seams_doc ON coal_seams(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proximate_doc ON proximate_analyses(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_doc ON geological_metrics(document_id)")
            conn.commit()

    def clear_document_records(self, document_id: str, source_document: Optional[str] = None) -> None:
        """Purges previous records for document_id or source_document to prevent duplicates on reprocessing."""
        del_where = "WHERE document_id = ?"
        del_params = [document_id]
        if source_document:
            del_where += " OR source_document = ?"
            del_params.append(source_document)

        with self._get_connection() as conn:
            conn.execute(f"DELETE FROM mines_projects {del_where}", del_params)
            conn.execute(f"DELETE FROM boreholes {del_where}", del_params)
            conn.execute(f"DELETE FROM coal_seams {del_where}", del_params)
            conn.execute(f"DELETE FROM proximate_analyses {del_where}", del_params)
            conn.execute(f"DELETE FROM geological_metrics {del_where}", del_params)
            conn.commit()

    def save_extraction_results(
        self,
        document_id: str,
        boreholes: List[Borehole],
        coal_seams: List[CoalSeam],
        proximate_analyses: List[ProximateAnalysis],
        mine_projects: List[MineProject],
        geological_metrics: List[GeologicalMetric],
    ) -> Dict[str, int]:
        """Saves all extracted records in a single transaction, replacing any prior records for the document."""
        counts = {
            "boreholes": len(boreholes),
            "coal_seams": len(coal_seams),
            "proximate_analyses": len(proximate_analyses),
            "mine_projects": len(mine_projects),
            "geological_metrics": len(geological_metrics),
        }

        # Resolve source_document name if present on any entity to cleanly replace prior uploads
        source_doc = None
        for entity_list in [boreholes, coal_seams, proximate_analyses, mine_projects, geological_metrics]:
            if entity_list and hasattr(entity_list[0], "source_document") and entity_list[0].source_document:
                source_doc = entity_list[0].source_document
                break

        del_where = "WHERE document_id = ?"
        del_params = [document_id]
        if source_doc:
            del_where += " OR source_document = ?"
            del_params.append(source_doc)

        with self._get_connection() as conn:
            # 1. Clear any prior extractions for this document to prevent duplicate accumulation
            conn.execute(f"DELETE FROM mines_projects {del_where}", del_params)
            conn.execute(f"DELETE FROM boreholes {del_where}", del_params)
            conn.execute(f"DELETE FROM coal_seams {del_where}", del_params)
            conn.execute(f"DELETE FROM proximate_analyses {del_where}", del_params)
            conn.execute(f"DELETE FROM geological_metrics {del_where}", del_params)

            # 2. Insert Mines / Projects
            for m in mine_projects:
                rec_id = m.id or str(uuid.uuid4())
                ts = m.extraction_timestamp.isoformat() if isinstance(m.extraction_timestamp, datetime) else str(m.extraction_timestamp)
                conn.execute(
                    """
                    INSERT INTO mines_projects (
                        id, document_id, project_name, subsidiary, location, block_name,
                        target_production, target_production_unit, stripping_ratio, life_of_mine_years,
                        source_document, source_page, evidence_text, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id, document_id, m.project_name, m.subsidiary, m.location, m.block_name,
                        m.target_production, m.target_production_unit, m.stripping_ratio, m.life_of_mine_years,
                        m.source_document, m.source_page, m.evidence_text, ts
                    )
                )

            # 3. Insert Boreholes
            for b in boreholes:
                rec_id = b.id or str(uuid.uuid4())
                ts = b.extraction_timestamp.isoformat() if isinstance(b.extraction_timestamp, datetime) else str(b.extraction_timestamp)
                conn.execute(
                    """
                    INSERT INTO boreholes (
                        id, document_id, borehole_id, mine_project, latitude, longitude,
                        collar_elevation, total_depth, lithology,
                        source_document, source_page, evidence_text, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id, document_id, b.borehole_id, b.mine_project, b.latitude, b.longitude,
                        b.collar_elevation, b.total_depth, b.lithology,
                        b.source_document, b.source_page, b.evidence_text, ts
                    )
                )

            # 4. Insert Coal Seams
            for s in coal_seams:
                rec_id = s.id or str(uuid.uuid4())
                ts = s.extraction_timestamp.isoformat() if isinstance(s.extraction_timestamp, datetime) else str(s.extraction_timestamp)
                conn.execute(
                    """
                    INSERT INTO coal_seams (
                        id, document_id, seam_id, borehole_id, depth_from, depth_to, thickness,
                        coal_grade, category, gross_reserves_mt, extractable_reserves_mt,
                        source_document, source_page, evidence_text, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id, document_id, s.seam_id, s.borehole_id, s.depth_from, s.depth_to, s.thickness,
                        s.coal_grade, s.category, s.gross_reserves_mt, s.extractable_reserves_mt,
                        s.source_document, s.source_page, s.evidence_text, ts
                    )
                )

            # 5. Insert Proximate Analyses
            for p in proximate_analyses:
                rec_id = p.id or str(uuid.uuid4())
                ts = p.extraction_timestamp.isoformat() if isinstance(p.extraction_timestamp, datetime) else str(p.extraction_timestamp)
                conn.execute(
                    """
                    INSERT INTO proximate_analyses (
                        id, document_id, seam_id, borehole_id, moisture_percent, ash_percent,
                        volatile_matter_percent, fixed_carbon_percent, gross_calorific_value, units,
                        source_document, source_page, evidence_text, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id, document_id, p.seam_id, p.borehole_id, p.moisture_percent, p.ash_percent,
                        p.volatile_matter_percent, p.fixed_carbon_percent, p.gross_calorific_value, p.units,
                        p.source_document, p.source_page, p.evidence_text, ts
                    )
                )

            # 6. Insert Geological Metrics
            for g in geological_metrics:
                rec_id = g.id or str(uuid.uuid4())
                ts = g.extraction_timestamp.isoformat() if isinstance(g.extraction_timestamp, datetime) else str(g.extraction_timestamp)
                conn.execute(
                    """
                    INSERT INTO geological_metrics (
                        id, document_id, metric_name, metric_value, unit, year_period, category,
                        source_document, source_page, evidence_text, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id, document_id, g.metric_name, g.metric_value, g.unit, g.year_period, g.category,
                        g.source_document, g.source_page, g.evidence_text, ts
                    )
                )

            conn.commit()

        return counts

    def list_boreholes(
        self,
        document_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[Borehole]:
        query = "SELECT * FROM boreholes WHERE 1=1"
        params: List[Any] = []
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        if source_document:
            query += " AND source_document = ?"
            params.append(source_document)
        if borehole_id:
            query += " AND borehole_id = ?"
            params.append(borehole_id)
        if search:
            query += " AND (borehole_id LIKE ? OR mine_project LIKE ? OR lithology LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY source_document ASC, borehole_id ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                Borehole(
                    id=r["id"],
                    document_id=r["document_id"],
                    borehole_id=r["borehole_id"],
                    mine_project=r["mine_project"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    collar_elevation=r["collar_elevation"],
                    total_depth=r["total_depth"],
                    lithology=r["lithology"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"],
                    extraction_timestamp=datetime.fromisoformat(r["extraction_timestamp"]),
                )
                for r in rows
            ]

    def list_seams(
        self,
        document_id: Optional[str] = None,
        seam_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[CoalSeam]:
        query = "SELECT * FROM coal_seams WHERE 1=1"
        params: List[Any] = []
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        if source_document:
            query += " AND source_document = ?"
            params.append(source_document)
        if seam_id:
            query += " AND seam_id = ?"
            params.append(seam_id)
        if borehole_id:
            query += " AND borehole_id = ?"
            params.append(borehole_id)
        if search:
            query += " AND (seam_id LIKE ? OR coal_grade LIKE ? OR category LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY source_document ASC, depth_from ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                CoalSeam(
                    id=r["id"],
                    document_id=r["document_id"],
                    seam_id=r["seam_id"],
                    borehole_id=r["borehole_id"],
                    depth_from=r["depth_from"],
                    depth_to=r["depth_to"],
                    thickness=r["thickness"],
                    coal_grade=r["coal_grade"],
                    category=r["category"],
                    gross_reserves_mt=r["gross_reserves_mt"],
                    extractable_reserves_mt=r["extractable_reserves_mt"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"],
                    extraction_timestamp=datetime.fromisoformat(r["extraction_timestamp"]),
                )
                for r in rows
            ]

    def list_proximate_analyses(
        self,
        document_id: Optional[str] = None,
        seam_id: Optional[str] = None,
        borehole_id: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[ProximateAnalysis]:
        query = "SELECT * FROM proximate_analyses WHERE 1=1"
        params: List[Any] = []
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        if source_document:
            query += " AND source_document = ?"
            params.append(source_document)
        if seam_id:
            query += " AND seam_id = ?"
            params.append(seam_id)
        if borehole_id:
            query += " AND borehole_id = ?"
            params.append(borehole_id)

        query += " ORDER BY source_document ASC, source_page ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                ProximateAnalysis(
                    id=r["id"],
                    document_id=r["document_id"],
                    seam_id=r["seam_id"],
                    borehole_id=r["borehole_id"],
                    moisture_percent=r["moisture_percent"],
                    ash_percent=r["ash_percent"],
                    volatile_matter_percent=r["volatile_matter_percent"],
                    fixed_carbon_percent=r["fixed_carbon_percent"],
                    gross_calorific_value=r["gross_calorific_value"],
                    units=r["units"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"],
                    extraction_timestamp=datetime.fromisoformat(r["extraction_timestamp"]),
                )
                for r in rows
            ]

    def list_mines(
        self,
        document_id: Optional[str] = None,
        search: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[MineProject]:
        query = "SELECT * FROM mines_projects WHERE 1=1"
        params: List[Any] = []
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        if source_document:
            query += " AND source_document = ?"
            params.append(source_document)
        if search:
            query += " AND (project_name LIKE ? OR location LIKE ? OR block_name LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY project_name ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                MineProject(
                    id=r["id"],
                    document_id=r["document_id"],
                    project_name=r["project_name"],
                    subsidiary=r["subsidiary"],
                    location=r["location"],
                    block_name=r["block_name"],
                    target_production=r["target_production"],
                    target_production_unit=r["target_production_unit"],
                    stripping_ratio=r["stripping_ratio"],
                    life_of_mine_years=r["life_of_mine_years"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"],
                    extraction_timestamp=datetime.fromisoformat(r["extraction_timestamp"]),
                )
                for r in rows
            ]

    def list_metrics(
        self,
        document_id: Optional[str] = None,
        category: Optional[str] = None,
        source_document: Optional[str] = None,
    ) -> List[GeologicalMetric]:
        query = "SELECT * FROM geological_metrics WHERE 1=1"
        params: List[Any] = []
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        if source_document:
            query += " AND source_document = ?"
            params.append(source_document)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY source_document ASC, source_page ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                GeologicalMetric(
                    id=r["id"],
                    document_id=r["document_id"],
                    metric_name=r["metric_name"],
                    metric_value=r["metric_value"],
                    unit=r["unit"],
                    year_period=r["year_period"],
                    category=r["category"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"],
                    extraction_timestamp=datetime.fromisoformat(r["extraction_timestamp"]),
                )
                for r in rows
            ]

    def get_extraction_status(self) -> Dict[str, Any]:
        """Calculates system-wide entity counts and document extraction status."""
        with self._get_connection() as conn:
            b_count = conn.execute("SELECT COUNT(*) FROM boreholes").fetchone()[0]
            s_count = conn.execute("SELECT COUNT(*) FROM coal_seams").fetchone()[0]
            p_count = conn.execute("SELECT COUNT(*) FROM proximate_analyses").fetchone()[0]
            m_count = conn.execute("SELECT COUNT(*) FROM mines_projects").fetchone()[0]
            g_count = conn.execute("SELECT COUNT(*) FROM geological_metrics").fetchone()[0]

            # Count unique documents with extracted records
            docs_extracted = conn.execute(
                """
                SELECT COUNT(DISTINCT document_id) FROM (
                    SELECT document_id FROM boreholes
                    UNION
                    SELECT document_id FROM coal_seams
                    UNION
                    SELECT document_id FROM proximate_analyses
                    UNION
                    SELECT document_id FROM mines_projects
                    UNION
                    SELECT document_id FROM geological_metrics
                )
                """
            ).fetchone()[0]

            total_entities = b_count + s_count + p_count + m_count + g_count

            return {
                "total_entities_count": total_entities,
                "counts_by_type": {
                    "boreholes": b_count,
                    "coal_seams": s_count,
                    "proximate_analyses": p_count,
                    "mine_projects": m_count,
                    "geological_metrics": g_count,
                },
                "total_documents_extracted": docs_extracted,
            }


extraction_db = ExtractionDatabase()
