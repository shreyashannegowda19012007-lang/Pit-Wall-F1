"""
Telemetry Pipeline Orchestrator & Lineage Manager for F1 Time-Series Telemetry Platform.
Orchestrates end-to-end execution:
RAW -> INGESTION -> VALIDATION -> CLEANING -> SYNCHRONIZATION -> ALIGNMENT -> FEATURES -> STORAGE -> LINEAGE.
Provides safe failure handling and complete lineage audit trails for reproducibility.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import hashlib
import logging

from telemetry_schema import validate_schema_compliance
from telemetry_ingestion import TelemetryIngestionService, IngestedDataset
from telemetry_validation import validate_telemetry_df, TelemetryValidationResult
from telemetry_cleaning import clean_telemetry_df
from telemetry_sync import synchronize_telemetry_channels
from lap_alignment import align_laps_by_distance
from telemetry_features import FeatureEngineeringService, FeatureDataset
from telemetry_storage import TelemetryStorageEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineRunResult:
    """Structured report produced by an end-to-end telemetry pipeline run."""
    success: bool
    analysis_id: str
    raw_dataset_id: str
    cleaned_dataset_id: str
    aligned_dataset_id: str
    feature_set_id: str
    processing_version: str
    validation: Dict[str, Any]
    cleaning_meta: Dict[str, Any]
    sync_meta: Dict[str, Any]
    alignment_meta: Dict[str, Any]
    feature_summary: Dict[str, Any]
    lineage: Dict[str, Any]
    error: Optional[str] = None
    processed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "analysis_id": self.analysis_id,
            "raw_dataset_id": self.raw_dataset_id,
            "cleaned_dataset_id": self.cleaned_dataset_id,
            "aligned_dataset_id": self.aligned_dataset_id,
            "feature_set_id": self.feature_set_id,
            "processing_version": self.processing_version,
            "validation": self.validation,
            "cleaning_meta": self.cleaning_meta,
            "sync_meta": self.sync_meta,
            "alignment_meta": self.alignment_meta,
            "feature_summary": self.feature_summary,
            "lineage": self.lineage,
            "error": self.error,
            "processed_at": self.processed_at
        }


class TelemetryPipeline:
    """
    Production-Grade Telemetry Data Pipeline Orchestrator.
    """

    PROCESSING_VERSION = "v2.4.0"

    def __init__(self, storage_engine: Optional[TelemetryStorageEngine] = None):
        self.storage = storage_engine or TelemetryStorageEngine()

    def process_session_telemetry(
        self,
        raw_data: Any,
        session_id: str,
        driver_id: str,
        lap_number: Optional[int] = None,
        ref_raw_data: Optional[Any] = None,
        ref_driver_id: Optional[str] = None,
        source: str = "FASTF1",
        target_freq_hz: float = 100.0
    ) -> PipelineRunResult:
        """
        Executes the end-to-end 10-stage telemetry data pipeline for a driver's lap.
        """
        analysis_id = f"ANALYSIS-{driver_id}-{session_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        try:
            # 1. INGESTION (RAW)
            if isinstance(raw_data, pd.DataFrame):
                ingested_raw = TelemetryIngestionService.ingest_from_dataframe(raw_data, source=source, session_id=session_id, driver_id=driver_id, lap_number=lap_number)
            elif hasattr(raw_data, 'get_telemetry'):
                ingested_raw = TelemetryIngestionService.ingest_from_fastf1_lap(raw_data, session_id=session_id, driver_id=driver_id)
            else:
                ingested_raw = TelemetryIngestionService.ingest_from_dataframe(pd.DataFrame(), source="INVALID_SOURCE", session_id=session_id, driver_id=driver_id)

            raw_df = ingested_raw.raw_df
            raw_dataset_id = ingested_raw.dataset_id

            if raw_df.empty:
                return PipelineRunResult(
                    success=False, analysis_id=analysis_id, raw_dataset_id=raw_dataset_id,
                    cleaned_dataset_id="N/A", aligned_dataset_id="N/A", feature_set_id="N/A",
                    processing_version=self.PROCESSING_VERSION, validation={"status": "FAILED"},
                    cleaning_meta={}, sync_meta={}, alignment_meta={}, feature_summary={}, lineage={},
                    error="Raw telemetry input is empty or null."
                )

            # Persist Raw Dataset Metadata
            self.storage.save_dataset_metadata(ingested_raw.get_metadata())

            # 2. VALIDATION
            val_result = validate_telemetry_df(raw_df)
            val_schema_ok, schema_errors, schema_warnings = validate_schema_compliance(raw_df)

            val_dict = val_result.to_dict()
            val_dict["schema_errors"] = schema_errors
            val_dict["schema_warnings"] = schema_warnings

            self.storage.save_validation_result(val_dict, raw_dataset_id)

            if not val_result.is_valid:
                return PipelineRunResult(
                    success=False, analysis_id=analysis_id, raw_dataset_id=raw_dataset_id,
                    cleaned_dataset_id="N/A", aligned_dataset_id="N/A", feature_set_id="N/A",
                    processing_version=self.PROCESSING_VERSION, validation=val_dict,
                    cleaning_meta={}, sync_meta={}, alignment_meta={}, feature_summary={}, lineage={},
                    error=f"Critical Telemetry Validation Failure: {val_result.errors}"
                )

            # 3. CLEANING
            cleaned_df, clean_meta = clean_telemetry_df(raw_df, val_result)
            cleaned_checksum = TelemetryIngestionService.calculate_df_checksum(cleaned_df)
            cleaned_dataset_id = f"CLEAN-{driver_id}-{session_id}-{cleaned_checksum[:10]}"

            # 4. TIME-SERIES SYNCHRONIZATION (Multi-frequency target 100Hz)
            synced_df, sync_meta = synchronize_telemetry_channels(cleaned_df, target_freq_hz=target_freq_hz)

            # 5. DISTANCE ALIGNMENT (vs reference lap or baseline)
            if ref_raw_data is not None:
                if isinstance(ref_raw_data, pd.DataFrame):
                    ref_cleaned, _ = clean_telemetry_df(ref_raw_data)
                elif hasattr(ref_raw_data, 'get_telemetry'):
                    ref_tel = ref_raw_data.get_telemetry().add_distance()
                    ref_cleaned, _ = clean_telemetry_df(ref_tel)
                else:
                    ref_cleaned = cleaned_df.copy()
            else:
                ref_cleaned = cleaned_df.copy()

            aligned_df, align_meta = align_laps_by_distance(
                synced_df, ref_cleaned,
                grid_step_m=1.0,
                driver_a_code=driver_id,
                driver_b_code=ref_driver_id or "REF"
            )

            aligned_checksum = TelemetryIngestionService.calculate_df_checksum(aligned_df)
            aligned_dataset_id = f"ALIGN-{driver_id}-{session_id}-{aligned_checksum[:10]}"

            # Persist Telemetry Samples in Database
            lap_id = f"LAP-{driver_id}-{session_id}-{lap_number or 0}"
            self.storage.save_telemetry_samples(aligned_df, aligned_dataset_id, lap_id)

            # 6. FEATURE ENGINEERING
            feat_dataset = FeatureEngineeringService.extract_lap_features(
                aligned_df, dataset_id=aligned_dataset_id, session_id=session_id, driver_id=driver_id, lap_number=lap_number
            )
            feat_dict = feat_dataset.to_dict()
            feature_set_id = feat_dataset.feature_set_id
            self.storage.save_features(feat_dict)

            # 7. LINEAGE REGISTRATION
            lineage_dict = {
                "lineage_id": f"LIN-{analysis_id}",
                "analysis_id": analysis_id,
                "raw_dataset_id": raw_dataset_id,
                "cleaned_dataset_id": cleaned_dataset_id,
                "aligned_dataset_id": aligned_dataset_id,
                "feature_set_id": feature_set_id,
                "processing_version": self.PROCESSING_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.storage.save_lineage(lineage_dict)

            return PipelineRunResult(
                success=True,
                analysis_id=analysis_id,
                raw_dataset_id=raw_dataset_id,
                cleaned_dataset_id=cleaned_dataset_id,
                aligned_dataset_id=aligned_dataset_id,
                feature_set_id=feature_set_id,
                processing_version=self.PROCESSING_VERSION,
                validation=val_dict,
                cleaning_meta=clean_meta,
                sync_meta=sync_meta,
                alignment_meta=align_meta,
                feature_summary=feat_dict,
                lineage=lineage_dict
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed for driver {driver_id}: {e}", exc_info=True)
            return PipelineRunResult(
                success=False, analysis_id=analysis_id, raw_dataset_id="N/A",
                cleaned_dataset_id="N/A", aligned_dataset_id="N/A", feature_set_id="N/A",
                processing_version=self.PROCESSING_VERSION, validation={}, cleaning_meta={},
                sync_meta={}, alignment_meta={}, feature_summary={}, lineage={},
                error=str(e)
            )
