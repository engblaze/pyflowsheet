from __future__ import annotations

from typing import Any

from .border import DrawingBorder
from .legend import DrawingLegend
from .notes import GeneralNotes
from .revision_block import RevisionBlock
from .sheet_sizes import SheetSizeConfig, get_sheet_size_config
from .title_block import TitleBlock


def _normalize_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    try:
        return dict(obj)
    except Exception:
        return {}


class DrawingFrame:
    """ASME Y14.1 Standard Drawing Frame Coordinator.

    Orchestrates the drawing border, revision block, dynamic legend, title block,
    and general notes according to sheet size configurations (A, B, C, D, E).
    """

    def __init__(
        self,
        sheet_size: str = "D",
        metadata: Any = None,
        settings: Any = None,
        enabled: bool = True,
        show_border: bool = True,
        show_title_block: bool = True,
        show_revision_block: bool = True,
        show_legend: bool = True,
        show_notes: bool = True,
        custom_legend_entries: list[dict[str, Any]] | None = None,
        border: DrawingBorder | None = None,
        revision_block: RevisionBlock | None = None,
        legend: DrawingLegend | None = None,
        title_block: TitleBlock | None = None,
        notes_block: GeneralNotes | None = None,
    ):
        meta_dict = _normalize_dict(metadata)
        settings_dict = _normalize_dict(settings)

        self.sheet_size = str(sheet_size or meta_dict.get("sheet_size") or "D").strip().upper()
        self.cfg: SheetSizeConfig = get_sheet_size_config(self.sheet_size)

        # Ensure sheet_size is set in metadata dict for TitleBlock
        if not meta_dict.get("sheet_size"):
            meta_dict["sheet_size"] = self.sheet_size

        self.metadata = meta_dict
        self.settings = settings_dict

        self.enabled = enabled
        self.show_border = show_border
        self.show_title_block = show_title_block
        self.show_revision_block = show_revision_block
        self.show_legend = show_legend
        self.show_notes = show_notes

        entries = (
            custom_legend_entries
            if custom_legend_entries is not None
            else meta_dict.get("custom_legend_entries")
        )
        self.custom_legend_entries: list[dict[str, Any]] = list(entries) if entries else []

        self.border: DrawingBorder = border or DrawingBorder(cfg=self.cfg)
        self.revision_block: RevisionBlock = revision_block or RevisionBlock(
            rect=self.cfg.revision_block_rect,
            revisions=meta_dict.get("revisions"),
        )
        self.legend: DrawingLegend = legend or DrawingLegend(
            rect=self.cfg.legend_rect,
            custom_entries=self.custom_legend_entries,
        )
        self.title_block: TitleBlock = title_block or TitleBlock(
            metadata=meta_dict,
            rect=self.cfg.title_block_rect,
        )
        self.notes_block: GeneralNotes = notes_block or GeneralNotes(
            notes=meta_dict.get("notes"),
            rect=self.cfg.notes_rect,
        )

    @property
    def notes(self) -> GeneralNotes:
        return self.notes_block

    @classmethod
    def from_metadata(
        cls,
        metadata: Any = None,
        settings: Any = None,
    ) -> DrawingFrame:
        if metadata is not None and hasattr(metadata, "metadata") and hasattr(metadata, "settings"):
            if settings is None:
                settings = getattr(metadata, "settings", None)
            metadata = getattr(metadata, "metadata", None)

        meta_dict = _normalize_dict(metadata)

        # Support passing full flowsheet dict containing 'metadata'
        if "metadata" in meta_dict and isinstance(meta_dict["metadata"], dict):
            if settings is None and "settings" in meta_dict:
                settings = meta_dict["settings"]
            meta_dict = _normalize_dict(meta_dict["metadata"])

        settings_dict = _normalize_dict(settings)
        if "drawing_frame" in settings_dict:
            df_settings = _normalize_dict(settings_dict["drawing_frame"])
        else:
            df_settings = settings_dict

        sheet_size = df_settings.get("sheet_size") or meta_dict.get("sheet_size") or "D"
        enabled = df_settings.get("enabled", meta_dict.get("enabled", True))
        show_border = df_settings.get("show_border", meta_dict.get("show_border", True))
        show_title_block = df_settings.get(
            "show_title_block", meta_dict.get("show_title_block", True)
        )
        show_revision_block = df_settings.get(
            "show_revision_block", meta_dict.get("show_revision_block", True)
        )
        show_legend = df_settings.get("show_legend", meta_dict.get("show_legend", True))
        show_notes = df_settings.get("show_notes", meta_dict.get("show_notes", True))
        custom_legend_entries = df_settings.get(
            "custom_legend_entries", meta_dict.get("custom_legend_entries")
        )

        return cls(
            sheet_size=sheet_size,
            metadata=meta_dict,
            settings=settings_dict,
            enabled=enabled,
            show_border=show_border,
            show_title_block=show_title_block,
            show_revision_block=show_revision_block,
            show_legend=show_legend,
            show_notes=show_notes,
            custom_legend_entries=custom_legend_entries,
        )

    def get_bounds(self) -> list[float]:
        return list(self.cfg.bounds)

    def draw(self, ctx, flowsheet=None) -> None:
        if not self.enabled:
            return

        if self.show_border and self.border is not None:
            self.border.draw(ctx)

        if self.show_revision_block and self.revision_block is not None:
            self.revision_block.draw(ctx)

        if self.show_legend and self.legend is not None:
            self.legend.draw(ctx, flowsheet=flowsheet)

        if self.show_title_block and self.title_block is not None:
            self.title_block.draw(ctx)

        if self.show_notes and self.notes_block is not None:
            self.notes_block.draw(ctx)
