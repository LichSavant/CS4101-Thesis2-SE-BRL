"""Pytest process-wide prohibition for the current verification-only scope.

Load with -p ml.tests.no_fit_guard BEFORE test collection. No stub succeeds in
place of fitting: any attempted fit raises and fails the entire session, even
if a test catches the exception. Inference on previously fitted state is allowed.
"""
import pytest

_patch=pytest.MonkeyPatch()
_attempts=[]


def _forbidden(*args,**kwargs):
    _attempts.append("blocked fit; no training executed")
    raise AssertionError("Model/learned-transform fitting prohibited by active researcher scope")


# Install while importing the explicitly requested plugin, before collection or
# fixtures. All genuine supported families and their learned transforms are
# blocked globally, including worker threads, independently of test-local guards.
from ml.classifier_adapters import FoldClassifier
from ml.experiment_engine import FittedSigmoid
from ml.features import TfidfExtractor, ConventionalFeatureBuilder
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from xgboost import XGBClassifier
import xgboost

for cls in (FoldClassifier,TfidfExtractor,ConventionalFeatureBuilder,LogisticRegression,LinearSVC,
            RandomForestClassifier,TfidfVectorizer,CountVectorizer,TfidfTransformer,SimpleImputer,
            StandardScaler,OneHotEncoder,Pipeline,ColumnTransformer,CalibratedClassifierCV,IsotonicRegression,XGBClassifier):
    for name in ("fit","fit_transform","partial_fit"):
        if hasattr(cls,name):_patch.setattr(cls,name,_forbidden)
_patch.setattr(FittedSigmoid,"fit",classmethod(_forbidden))
_patch.setattr(xgboost,"train",_forbidden)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session,exitstatus):
    if _attempts:session.exitstatus=1


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(f"No-fit process guard: {len(_attempts)} blocked fitting attempts; 0 fitting executions.")


def pytest_unconfigure():
    _patch.undo()
