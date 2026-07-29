"""Research-only cross-asset opportunity comparison."""

from freakto.cross_asset.evaluation import RankerEvaluation, evaluate_rankings
from freakto.cross_asset.forward import CrossAssetForwardTracker
from freakto.cross_asset.opportunity_ranker import (
    RankingReport,
    rank_opportunities,
)

__all__ = [
    "CrossAssetForwardTracker",
    "RankerEvaluation",
    "RankingReport",
    "evaluate_rankings",
    "rank_opportunities",
]
