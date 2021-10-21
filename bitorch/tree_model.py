import libsbn
import numpy as np
import phylotorch.evolution.tree_model
import torch
from phylotorch.core.abstractparameter import AbstractParameter
from phylotorch.evolution.taxa import Taxa
from phylotorch.evolution.tree_model import (
    ReparameterizedTimeTreeModel as BaseReparameterizedTimeTreeModel,
)
from phylotorch.evolution.tree_model import UnRootedTreeModel as BaseUnRootedTreeModel
from phylotorch.typing import ID
from torch import Tensor


class GeneralNodeHeightTransform(
    phylotorch.evolution.tree_model.GeneralNodeHeightTransform
):
    r"""
    Transform from ratios to node heights.
    """

    def __init__(self, tree, inst, cache_size=0):
        super(GeneralNodeHeightTransform, self).__init__(tree, cache_size=cache_size)
        self.inst = inst

    def _call(self, x):
        # the transform is called during construction of the transformed parameter
        # and inst is not initialized yet
        if self.inst is None:
            return super()._call(x)
        else:
            fn = NodeHeightAutogradFunction.apply
            return fn(self.inst, x)

    def _inverse(self, y):
        raise NotImplementedError

    def log_abs_det_jacobian(self, x, y):
        return torch.zeros(1)


class NodeHeightAutogradFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, inst, ratios_root_height):
        ctx.inst = inst
        node_heights = []
        params_numpy = ratios_root_height.detach().numpy()
        for batch_idx in range(ratios_root_height.shape[0]):
            inst.tree_collection.trees[0].initialize_time_tree_using_height_ratios(
                params_numpy[batch_idx, ...]
            )
            node_heights.append(
                torch.tensor(
                    np.array(inst.tree_collection.trees[0].node_heights, copy=True)[
                        ratios_root_height.shape[-1] + 1 :
                    ]
                )
            )
        return torch.stack(node_heights)

    @staticmethod
    def backward(ctx, grad_output):
        grad = []
        grad_output_numpy = grad_output.numpy()
        for batch_idx in range(grad_output.shape[0]):
            grad.append(
                torch.tensor(
                    libsbn.ratio_gradient_of_height_gradient(
                        ctx.inst.tree_collection.trees[0],
                        grad_output_numpy[batch_idx, ...],
                    )
                )
            )
        return None, torch.stack(grad)


class ReparameterizedTimeTreeModel(BaseReparameterizedTimeTreeModel):
    def __init__(
        self, id_: ID, tree, taxa: Taxa, ratios_root_heights: AbstractParameter
    ):
        BaseReparameterizedTimeTreeModel.__init__(
            self, id_, tree, taxa, ratios_root_heights
        )
        self.inst = None

    def set_instance(self, inst):
        self.inst = inst

    @property
    def node_heights(self) -> torch.Tensor:
        if self.inst is None and self.heights_need_update:
            return super().node_heights
        elif self.heights_need_update:
            self._heights = GeneralNodeHeightTransform(self, self.inst)(
                self._internal_heights.tensor
            )
            self._node_heights = torch.cat(
                (
                    self.sampling_times.expand(
                        self._internal_heights.tensor.shape[:-1] + (-1,)
                    ),
                    self._heights,
                ),
                -1,
            )
            self.heights_need_update = False
        return self._node_heights

    def _call(self, *args, **kwargs) -> Tensor:
        return torch.zeros(self._heights.shape[:-1])


class UnRootedTreeModel(BaseUnRootedTreeModel):
    def __init__(self, id_: ID, tree, taxa: Taxa, branch_lengths: AbstractParameter):
        super().__init__(id_, tree, taxa, branch_lengths)
        self.inst = None

    def set_instance(self, inst):
        self.inst = inst

    @classmethod
    def from_json(cls, data, dic):
        tree_model = BaseUnRootedTreeModel.from_json(data, dic)
        taxon_to_index = {}
        for node in tree_model.tree.leaf_node_iter():
            taxon_to_index[node.taxon.label] = node.index
        tree_model._taxa.sort(key=lambda x: taxon_to_index[str(x)])
        return tree_model
