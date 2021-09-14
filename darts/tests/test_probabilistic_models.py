import numpy as np

from .base_test_class import DartsBaseTestClass
from ..utils import timeseries_generation as tg
from ..metrics import mae, rho_risk
from ..logging import get_logger
from darts.models import ExponentialSmoothing, ARIMA
from darts.models.forecasting_model import GlobalForecastingModel
logger = get_logger(__name__)

try:
    from ..models import RNNModel, TCNModel
    from darts.utils.likelihood_models import GaussianLikelihoodModel
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning('Torch not available. TCN tests will be skipped.')
    TORCH_AVAILABLE = False

models_cls_kwargs_errs = [
    (ExponentialSmoothing, {}, 0.4),
    (ARIMA, {'p': 1, 'd': 0, 'q': 1}, 0.17)
]

if TORCH_AVAILABLE:
    models_cls_kwargs_errs += [
        (RNNModel, {'input_chunk_length': 2, 'training_length': 10, 'n_epochs': 20, 'random_state': 0,
                    'likelihood': GaussianLikelihoodModel()}, 1.9),
        (TCNModel, {'input_chunk_length': 10, 'output_chunk_length': 5, 'n_epochs': 60, 'random_state': 0,
                    'likelihood': GaussianLikelihoodModel()}, 0.28)
    ]


class ProbabilisticTorchModelsTestCase(DartsBaseTestClass):

    np.random.seed(0)
    constant_ts = tg.constant_timeseries(length=200, value=0.5)
    constant_noisy_ts = constant_ts + tg.gaussian_timeseries(length=200, std=0.1)
    constant_multivar_ts = constant_ts.stack(constant_ts)
    constant_noisy_multivar_ts = constant_noisy_ts.stack(constant_noisy_ts)
    num_samples = 5

    def test_fit_predict_determinism(self):

        for model_cls, model_kwargs, _ in models_cls_kwargs_errs:

            # whether the first predictions of two models initiated with the same random state are the same
            model = model_cls(**model_kwargs)
            model.fit(self.constant_ts)
            pred1 = model.predict(n=10, num_samples=2).values()

            model = model_cls(**model_kwargs)
            model.fit(self.constant_ts)
            pred2 = model.predict(n=10, num_samples=2).values()

            self.assertTrue((pred1 == pred2).all())

            # test whether the next prediction of the same model is different
            pred3 = model.predict(n=10, num_samples=2).values()
            self.assertTrue((pred2 != pred3).any())

    def test_probabilistic_forecast_accuracy(self):
        for model_cls, model_kwargs, err in models_cls_kwargs_errs:
            self.helper_test_probabilistic_forecast_accuracy(model_cls, model_kwargs, err,
                                                             self.constant_ts, self.constant_noisy_ts)
            if issubclass(model_cls, GlobalForecastingModel):
                self.helper_test_probabilistic_forecast_accuracy(model_cls, model_kwargs, err,
                                                                 self.constant_multivar_ts,
                                                                 self.constant_noisy_multivar_ts)

    def test_probabilistic_forecast_risk(self):
        for model_cls, model_kwargs, err in models_cls_kwargs_errs:
            self.helper_test_probabilistic_forecast_risk(model_cls, model_kwargs, err,
                                                             self.constant_ts, self.constant_noisy_ts)
            if issubclass(model_cls, GlobalForecastingModel):
                self.helper_test_probabilistic_forecast_risk(model_cls, model_kwargs, err,
                                                                 self.constant_multivar_ts,
                                                                 self.constant_noisy_multivar_ts)

    def helper_test_probabilistic_forecast_accuracy(self, model_cls, model_kwargs, err, ts, noisy_ts):
        model = model_cls(**model_kwargs)
        model.fit(noisy_ts[:100])
        pred = model.predict(n=100, num_samples=100)

        # test accuracy of the median prediction and quantile (=0.5) rho-risk compared to the noiseless ts
        mae_err_median = mae(ts[100:], pred)
        self.assertLess(mae_err_median, err)

        # test accuracy for increasing quantiles between 0.7 and 1 (it should decrease, mae should increase),
        tested_quantiles = [0.7, 0.8, 0.9, 0.99]
        mae_err = mae_err_median
        for quantile in tested_quantiles:
            new_mae = mae(ts[100:], pred.quantile_timeseries(quantile=quantile))
            self.assertLess(mae_err, new_mae)
            mae_err = new_mae

        # test accuracy for decreasing quantiles between 0.3 and 0 (it should decrease, mae should increase),
        tested_quantiles = [0.3, 0.2, 0.1, 0.01]
        mae_err = mae_err_median
        for quantile in tested_quantiles:
            new_mae = mae(ts[100:], pred.quantile_timeseries(quantile=quantile))
            self.assertLess(mae_err, new_mae)
            mae_err = new_mae

    def helper_test_probabilistic_forecast_risk(self, model_cls, model_kwargs, err, ts, noisy_ts):
        model = model_cls(**model_kwargs)
        model.fit(noisy_ts[:100])
        pred = model.predict(n=100, num_samples=100)

        # test rho-risk (at quantile=0.5) compared to the noiseless ts
        rrisk_median = rho_risk(ts[100:], pred, rho=0.5)
        self.assertLess(rrisk_median, err)

        # test risk for increasing quantiles between 0.75 and 1 should increase
        tested_quantiles = [0.8, 0.9, 0.95, 0.99]  # some test cases actually have minimum risk around 0.75
        rrisk_err = rho_risk(ts[100:], pred, rho=0.75)
        for quantile in tested_quantiles:
            new_rrisk = rho_risk(ts[100:], pred, rho=quantile)
            self.assertLess(rrisk_err, new_rrisk)
            rrisk_err = new_rrisk

        # test risk for decreasing quantiles between 0.25 and 0 should increase
        tested_quantiles = [0.2, 0.1, 0.05, 0.01]  # some test cases actually have minimum risk around 0.25
        rrisk_err = rho_risk(ts[100:], pred, rho=0.25)
        for quantile in tested_quantiles:
            new_rrisk = rho_risk(ts[100:], pred, rho=quantile)
            self.assertLess(rrisk_err, new_rrisk)
            rrisk_err = new_rrisk
