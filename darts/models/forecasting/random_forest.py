"""
Random Forest
-------------

A forecasting model using a random forest regression. It uses some of the target series' lags, as well as optionally
some covariate series' lags in order to obtain a forecast.

See [1] for a reference around random forests.

The implementations is wrapped around `RandomForestRegressor
<https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html#sklearn.ensemble.RandomForestRegressor>`_.

References
----------
.. [1] https://en.wikipedia.org/wiki/Random_forest
"""
from darts.logging import get_logger
from typing import Optional, Union, Tuple, List
from darts.models.forecasting.regression_model import RegressionModel
from sklearn.ensemble import RandomForestRegressor

logger = get_logger(__name__)


class RandomForest(RegressionModel):
    def __init__(self,
                 lags: Union[int, list] = None,
                 lags_past_covariates: Union[int, List[int]] = None,
                 lags_future_covariates: Union[Tuple[int, int], List[int]] = None,
                 n_estimators: Optional[int] = 100,
                 max_depth: Optional[int] = None,
                 **kwargs):
        """Random Forest

        Parameters
        ----------
        lags
            Lagged target values used to predict the next time step. If an integer is given the last `lags` past lags
            are used (from -1 backward). Otherwise a list of integers with lags is required (each lag must be < 0).
        lags_past_covariates
            Number of lagged past_covariates values used to predict the next time step. If an integer is given the last
            `lags_past_covariates` past lags are used (inclusive, starting from lag -1). Otherwise a list of integers
            with lags < 0 is required.
        lags_future_covariates
            Number of lagged future_covariates values used to predict the next time step. If an tuple (past, future) is
            given the last `past` lags in the past are used (inclusive, starting from lag -1) along with the first
            `future` future lags (starting from 0 - the prediction time - up to `future - 1` included). Otherwise a list
            of integers with lags is required.
        n_estimators : int
            The number of trees in the forest.
        max_depth : int
            The maximum depth of the tree. If None, then nodes are expanded until all leaves are pure or until all
            leaves contain less than min_samples_split samples.
        **kwargs
            Additional keyword arguments passed to `sklearn.ensemble.RandomForest`.
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.kwargs = kwargs
        self.kwargs["n_estimators"] = self.n_estimators
        self.kwargs["max_depth"] = self.max_depth

        super().__init__(
            lags=lags,
            lags_past_covariates=lags_past_covariates,
            lags_future_covariates=lags_future_covariates,
            model=RandomForestRegressor(**kwargs)
        )

    def __str__(self):
        return (f"RandomForest(lags={self.lags}, lags_past_covariates={self.lags_past_covariates}, "
                f"lags_historical_covariates={self.lags_historical_covariates}, "
                f"lags_future_covariates={self.lags_future_covariates}, "
                f"n_estimators={self.n_estimators}, max_depth={self.max_depth}")
