"""
BGP-4 (Border Gateway Protocol / RFC 4271) Best Path Decision Engine.
Implements the 10-step deterministic best-path selection algorithm,
attribute comparisons, and decision path tracking.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class BGPOrigin(str, Enum):
    IGP = "IGP"  # 'i' (highest preference)
    EGP = "EGP"  # 'e' (medium preference)
    INCOMPLETE = "INCOMPLETE"  # '?' (lowest preference)


class PeeringType(str, Enum):
    EBGP = "EBGP"
    IBGP = "IBGP"
    LOCAL = "LOCAL"


@dataclass
class BGPRoute:
    prefix: str
    next_hop: str
    peer_ip: str
    peer_router_id: str
    peering_type: PeeringType
    weight: int = 0                    # Step 1: Highest (Cisco-specific, 0-65535)
    local_pref: int = 100              # Step 2: Highest (100 default)
    is_locally_originated: bool = False # Step 3: Local > Remote
    as_path: List[int] = None          # Step 4: Shortest AS-Path length
    origin: BGPOrigin = BGPOrigin.IGP  # Step 5: IGP < EGP < Incomplete
    med: int = 0                       # Step 6: Lowest Multi-Exit Discriminator
    igp_metric_to_next_hop: int = 0    # Step 8: Lowest IGP metric to next-hop
    age_seconds: float = 0.0           # Step 9: Oldest eBGP route

    def __post_init__(self):
        if self.as_path is None:
            self.as_path = []


@dataclass
class BGPEvaluationStep:
    step_number: int
    step_name: str
    surviving_candidates: List[str]
    eliminated_candidates: List[str]
    reason: str


class BGPRoutingEngine:
    """Deterministic BGP-4 Best Path Selection Engine."""

    @classmethod
    def select_best_path(
        cls,
        routes: List[BGPRoute],
        always_compare_med: bool = False
    ) -> Tuple[BGPRoute, List[BGPEvaluationStep]]:
        """
        Evaluate candidate BGP routes for the same prefix and determine winning path.
        Returns: (winning_route, decision_log)
        """
        if not routes:
            raise ValueError("No candidate routes provided for BGP evaluation")

        candidates = list(routes)
        log: List[BGPEvaluationStep] = []

        # Helper to record a reduction step
        def record_step(
            step_num: int,
            name: str,
            surviving: List[BGPRoute],
            eliminated: List[BGPRoute],
            reason_msg: str
        ):
            log.append(
                BGPEvaluationStep(
                    step_number=step_num,
                    step_name=name,
                    surviving_candidates=[f"{r.next_hop} (RID {r.peer_router_id})" for r in surviving],
                    eliminated_candidates=[f"{r.next_hop} (RID {r.peer_router_id})" for r in eliminated],
                    reason=reason_msg
                )
            )

        # Step 1: Highest Weight (Local Cisco attribute)
        max_weight = max(r.weight for r in candidates)
        survivors = [r for r in candidates if r.weight == max_weight]
        eliminated = [r for r in candidates if r.weight < max_weight]
        if eliminated:
            record_step(1, "WEIGHT", survivors, eliminated, f"Prefer highest weight: {max_weight}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 2: Highest Local Preference
        max_lp = max(r.local_pref for r in candidates)
        survivors = [r for r in candidates if r.local_pref == max_lp]
        eliminated = [r for r in candidates if r.local_pref < max_lp]
        if eliminated:
            record_step(2, "LOCAL_PREF", survivors, eliminated, f"Prefer highest local-pref: {max_lp}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 3: Locally Originated over Learned
        has_local = any(r.is_locally_originated for r in candidates)
        if has_local:
            survivors = [r for r in candidates if r.is_locally_originated]
            eliminated = [r for r in candidates if not r.is_locally_originated]
            if eliminated:
                record_step(3, "LOCAL_ORIGIN", survivors, eliminated, "Prefer locally originated route")
            candidates = survivors
            if len(candidates) == 1:
                return candidates[0], log

        # Step 4: Shortest AS-Path Length
        min_as_len = min(len(r.as_path) for r in candidates)
        survivors = [r for r in candidates if len(r.as_path) == min_as_len]
        eliminated = [r for r in candidates if len(r.as_path) > min_as_len]
        if eliminated:
            record_step(4, "AS_PATH_LENGTH", survivors, eliminated, f"Prefer shortest AS-path length: {min_as_len}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 5: Lowest Origin Code (IGP < EGP < Incomplete)
        origin_rank = {BGPOrigin.IGP: 0, BGPOrigin.EGP: 1, BGPOrigin.INCOMPLETE: 2}
        min_origin = min(origin_rank[r.origin] for r in candidates)
        survivors = [r for r in candidates if origin_rank[r.origin] == min_origin]
        eliminated = [r for r in candidates if origin_rank[r.origin] > min_origin]
        if eliminated:
            best_origin_str = [k for k, v in origin_rank.items() if v == min_origin][0].value
            record_step(5, "ORIGIN_CODE", survivors, eliminated, f"Prefer lowest origin: {best_origin_str}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 6: Lowest MED (Multi-Exit Discriminator)
        min_med = min(r.med for r in candidates)
        survivors = [r for r in candidates if r.med == min_med]
        eliminated = [r for r in candidates if r.med > min_med]
        if eliminated:
            record_step(6, "MED", survivors, eliminated, f"Prefer lowest MED: {min_med}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 7: eBGP over iBGP
        has_ebgp = any(r.peering_type == PeeringType.EBGP for r in candidates)
        if has_ebgp:
            survivors = [r for r in candidates if r.peering_type == PeeringType.EBGP]
            eliminated = [r for r in candidates if r.peering_type != PeeringType.EBGP]
            if eliminated:
                record_step(7, "EBGP_OVER_IBGP", survivors, eliminated, "Prefer external eBGP over internal iBGP")
            candidates = survivors
            if len(candidates) == 1:
                return candidates[0], log

        # Step 8: Lowest IGP Metric to Next-Hop
        min_igp = min(r.igp_metric_to_next_hop for r in candidates)
        survivors = [r for r in candidates if r.igp_metric_to_next_hop == min_igp]
        eliminated = [r for r in candidates if r.igp_metric_to_next_hop > min_igp]
        if eliminated:
            record_step(8, "IGP_METRIC", survivors, eliminated, f"Prefer lowest IGP metric to next-hop: {min_igp}")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 9: Oldest eBGP Route (Tiebreaker for stability)
        max_age = max(r.age_seconds for r in candidates)
        survivors = [r for r in candidates if r.age_seconds == max_age]
        eliminated = [r for r in candidates if r.age_seconds < max_age]
        if eliminated and len(survivors) < len(candidates):
            record_step(9, "OLDEST_ROUTE", survivors, eliminated, "Prefer oldest stable eBGP route")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Step 10: Lowest BGP Router ID (IPv4 address as integer)
        def rid_to_int(rid_str: str) -> int:
            octs = [int(x) for x in rid_str.split(".")]
            return (octs[0] << 24) | (octs[1] << 16) | (octs[2] << 8) | octs[3]

        min_rid_val = min(rid_to_int(r.peer_router_id) for r in candidates)
        survivors = [r for r in candidates if rid_to_int(r.peer_router_id) == min_rid_val]
        eliminated = [r for r in candidates if rid_to_int(r.peer_router_id) > min_rid_val]
        if eliminated:
            record_step(10, "ROUTER_ID", survivors, eliminated, "Prefer lowest BGP Router ID")
        candidates = survivors
        if len(candidates) == 1:
            return candidates[0], log

        # Final Tiebreaker: Lowest Peer IP Address
        min_peer_ip_val = min(rid_to_int(r.peer_ip) for r in candidates)
        winner = [r for r in candidates if rid_to_int(r.peer_ip) == min_peer_ip_val][0]
        return winner, log
