"""
Telemetry Ingestion Service for F1 Time-Series Data Pipeline.
Standardizes raw data inputs (CSV, JSON, FastF1, OpenF1, Parquet, Synthetic) into a unified internal representation.
Calculates SHA-256 checksums, dataset_id keys, and reproducible lineage metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import hashlib
import json
from datetime import datetime, timezone
import logging
from telemetry_schema import DataProvenance, DataStatus

logger = logging.getLogger(__name__)


@dataclass
class IngestedDataset:
    """Standardized internal representation of an ingested telemetry dataset."""
    dataset_id: str
    source: str
    source_file: Optional[str]
    ingestion_timestamp: str
    session_id: str
    driver_id: str
    lap_number: Optional[int]
    row_count: int
    schema_version: str
    processing_version: str
    checksum: str
    raw_df: pd.DataFrame = field(default_factory=pd.DataFrame, repr=False)
    provenance: Optional[DataProvenance] = None

    def get_metadata(self) -> Dict[str, Any]:
        meta = {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "source_file": self.source_file,
            "ingestion_timestamp": self.ingestion_timestamp,
            "session_id": self.session_id,
            "driver_id": self.driver_id,
            "lap_number": self.lap_number,
            "row_count": self.row_count,
            "schema_version": self.schema_version,
            "processing_version": self.processing_version,
            "checksum": self.checksum
        }
        if self.provenance:
            meta["provenance"] = {
                "provider_name": self.provenance.provider_name,
                "endpoint": self.provenance.endpoint,
                "session_identifier": self.provenance.session_identifier,
                "retrieval_timestamp": self.provenance.retrieval_timestamp,
                "historical_or_live": self.provenance.historical_or_live,
                "cache_status": self.provenance.cache_status,
                "schema_version": self.provenance.schema_version,
                "data_completeness": self.provenance.data_completeness.value
            }
        return meta


class TelemetryIngestionService:
    """
    Unified Ingestion Layer for Formula One Telemetry Datasets.
    Enforces reproducible metadata generation and cryptographic checksumming.
    """

    SCHEMA_VERSION = "v2.4.0"
    PROCESSING_VERSION = "v2.4.0"

    @classmethod
    def calculate_df_checksum(cls, df: pd.DataFrame) -> str:
        """Computes a deterministic SHA-256 hash of a Pandas DataFrame content."""
        if df is None or df.empty:
            return hashlib.sha256(b"EMPTY_DATAFRAME").hexdigest()

        # Use csv byte serialization for stable hash calculation
        data_bytes = df.to_csv(index=False).encode('utf-8')
        return hashlib.sha256(data_bytes).hexdigest()

    @classmethod
    def generate_dataset_id(cls, source: str, session_id: str, driver_id: str, lap_number: Optional[int], checksum: str) -> str:
        """Generates a unique, deterministic dataset ID key."""
        raw_key = f"{source}:{session_id}:{driver_id}:{lap_number or 'ALL'}:{checksum[:16]}"
        hash_suffix = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:12]
        return f"DS-{driver_id}-{session_id}-{hash_suffix}"

    @classmethod
    def ingest_from_dataframe(
        cls,
        df: pd.DataFrame,
        source: str = "DATAFRAME",
        session_id: str = "UNKNOWN_SESSION",
        driver_id: str = "UNKNOWN_DRIVER",
        lap_number: Optional[int] = None,
        source_file: Optional[str] = None,
        provenance: Optional[DataProvenance] = None
    ) -> IngestedDataset:
        """
        Ingests an in-memory Pandas DataFrame into the standardized pipeline dataset model.
        """
        raw_copy = df.copy() if df is not None else pd.DataFrame()
        row_count = len(raw_copy)
        checksum = cls.calculate_df_checksum(raw_copy)
        dataset_id = cls.generate_dataset_id(source, session_id, driver_id, lap_number, checksum)
        ingest_time = datetime.now(timezone.utc).isoformat()

        return IngestedDataset(
            dataset_id=dataset_id,
            source=source,
            source_file=source_file,
            ingestion_timestamp=ingest_time,
            session_id=session_id,
            driver_id=driver_id,
            lap_number=lap_number,
            row_count=row_count,
            schema_version=cls.SCHEMA_VERSION,
            processing_version=cls.PROCESSING_VERSION,
            checksum=checksum,
            provenance=provenance,
            raw_df=raw_copy
        )

    @classmethod
    def ingest_from_csv(cls, file_path: str, session_id: str, driver_id: str, lap_number: Optional[int] = None) -> IngestedDataset:
        """Ingests raw telemetry from a CSV file."""
        try:
            df = pd.read_csv(file_path)
            return cls.ingest_from_dataframe(
                df=df,
                source="CSV",
                session_id=session_id,
                driver_id=driver_id,
                lap_number=lap_number,
                source_file=file_path
            )
        except Exception as e:
            logger.error(f"Failed to ingest CSV file '{file_path}': {e}")
            return cls.ingest_from_dataframe(pd.DataFrame(), source="CSV_FAILED", session_id=session_id, driver_id=driver_id, source_file=file_path)

    @classmethod
    def ingest_from_json(cls, json_payload: Any, session_id: str, driver_id: str, lap_number: Optional[int] = None) -> IngestedDataset:
        """Ingests raw telemetry from a JSON payload or string."""
        try:
            if isinstance(json_payload, str):
                data = json.loads(json_payload)
            else:
                data = json_payload

            df = pd.DataFrame(data)
            return cls.ingest_from_dataframe(
                df=df,
                source="JSON",
                session_id=session_id,
                driver_id=driver_id,
                lap_number=lap_number
            )
        except Exception as e:
            logger.error(f"Failed to ingest JSON payload: {e}")
            return cls.ingest_from_dataframe(pd.DataFrame(), source="JSON_FAILED", session_id=session_id, driver_id=driver_id)

    @classmethod
    def ingest_from_fastf1_lap(cls, lap_obj: Any, session_id: str, driver_id: str) -> IngestedDataset:
        """Ingests raw telemetry trace directly from a FastF1 Lap object."""
        try:
            if not hasattr(lap_obj, 'get_telemetry'):
                raise ValueError("Lap object does not support get_telemetry()")

            telemetry = lap_obj.get_telemetry().add_distance()
            lap_num = int(lap_obj.get('LapNumber', 0)) if pd.notna(lap_obj.get('LapNumber')) else None

            return cls.ingest_from_dataframe(
                df=telemetry,
                source="FASTF1",
                session_id=session_id,
                driver_id=driver_id,
                lap_number=lap_num
            )
        except Exception as e:
            logger.error(f"Failed to ingest FastF1 lap for driver {driver_id}: {e}")
            return cls.ingest_from_dataframe(pd.DataFrame(), source="FASTF1_FAILED", session_id=session_id, driver_id=driver_id)
