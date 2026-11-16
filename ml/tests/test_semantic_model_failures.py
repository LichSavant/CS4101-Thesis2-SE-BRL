"""Fake loaders only. Never import real transformers/torch or inspect weights."""
from contextlib import nullcontext
from types import SimpleNamespace
import sys

import pytest

from ml.se_brl.semantic_candidates import PinnedLocalNliScorer, SemanticInferenceUnavailable


@pytest.mark.parametrize("labels,num_labels", [
    ({-1:"entailment",0:"neutral",1:"contradiction"},3),
    ({0:"entailment",1:"neutral",7:"contradiction"},3),
    ({False:"entailment",1:"neutral",2:"contradiction"},3),
    ({"00":"entailment","1":"neutral","2":"contradiction"},3),
    ({0:"entailment",1:"neutral",2:"contradiction"},4),
    ({0:"entailment",1:"neutral",2:"contradiction"},True),
])
def test_noncanonical_logit_index_mappings_are_unavailable(monkeypatch,labels,num_labels):
    class Model:
        config=SimpleNamespace(id2label=labels,num_labels=num_labels)
        def to(self,device):assert device=="cpu";return self
        def eval(self):return self
    def load(*args,**kwargs):
        assert kwargs["local_files_only"] is True and len(kwargs["revision"])==40
        return Model()
    monkeypatch.setitem(sys.modules,"transformers",SimpleNamespace(
        AutoModelForSequenceClassification=SimpleNamespace(from_pretrained=load),
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**kw:object())))
    monkeypatch.setitem(sys.modules,"torch",SimpleNamespace())
    with pytest.raises(SemanticInferenceUnavailable,match="labels"):PinnedLocalNliScorer()


@pytest.mark.parametrize("shape", [(1,10),(3,0),(3,),(),(3,513)])
def test_token_shape_and_limit_fail_before_forward(shape):
    scorer=PinnedLocalNliScorer.__new__(PinnedLocalNliScorer)
    scorer.hypotheses={"urgency":["synthetic"]*3};scorer.spec={"max_tokens":512}
    scorer.tokenizer=lambda *a,**kw:{"input_ids":SimpleNamespace(shape=shape)}
    with pytest.raises(SemanticInferenceUnavailable):scorer.score("synthetic", "urgency")


def test_tokenizer_and_model_runtime_details_are_not_exposed():
    scorer=PinnedLocalNliScorer.__new__(PinnedLocalNliScorer)
    scorer.hypotheses={"urgency":["synthetic"]*3};scorer.spec={"max_tokens":512}
    def broken(*a,**kw):raise RuntimeError("private-model-path")
    scorer.tokenizer=broken
    with pytest.raises(SemanticInferenceUnavailable,match="tokenization failed") as e:scorer.score("synthetic","urgency")
    assert "private" not in str(e.value)
    scorer.tokenizer=lambda *a,**kw:{"input_ids":SimpleNamespace(shape=(3,10))}
    scorer.model=broken;scorer.torch=SimpleNamespace(inference_mode=nullcontext)
    with pytest.raises(SemanticInferenceUnavailable,match="inference failed") as e:scorer.score("synthetic","urgency")
    assert "private" not in str(e.value)
