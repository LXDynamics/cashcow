"""Analysis package for CashCow."""

from .monte_carlo import (
    Distribution,
    UncertaintyModel,
    MonteCarloSimulator,
    create_common_uncertainties,
    save_simulation_results
)
from .whatif import (
    Parameter,
    WhatIfScenario,
    WhatIfAnalyzer,
    create_standard_parameters
)

__all__ = [
    'Distribution',
    'UncertaintyModel', 
    'MonteCarloSimulator',
    'create_common_uncertainties',
    'save_simulation_results',
    'Parameter',
    'WhatIfScenario',
    'WhatIfAnalyzer',
    'create_standard_parameters'
]