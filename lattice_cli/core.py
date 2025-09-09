from estimator.estimator import *
from estimator.estimator.lwe_parameters import *
from estimator.estimator.nd import *
import math


def estimate_rop_secpar(
    ring_dim: int,
    q: int,
    s_dist: NoiseDistribution,
    e_dist: NoiseDistribution,
    m: int = oo,
    is_rough=True,
) -> int:
    params = LWEParameters(
        ring_dim,
        q,
        s_dist,
        e_dist,
        m,
    )
    estim = LWE.estimate.rough(params) if is_rough else LWE.estimate(params)
    vals = estim.values()
    if len(vals) == 0:
        return 0
    min_rop_log = math.log2(min(val["rop"] for val in vals))
    if min_rop_log == float("inf"):
        return 4294967295
    min_secpar = math.floor(min_rop_log)
    return min_secpar
