# -*- coding: utf-8 -*-
# @Time         : 14:13 2022/01/17
# @Author       : Chris
# @Description  : Reflection utilities.
import importlib
import inspect


def get_class(full_name: str) -> type:
    chips = full_name.split(".")
    module_name = ".".join(chips[:-1])
    class_name = chips[-1]
    module = importlib.import_module(module_name)
    clazz = getattr(module, class_name)
    return clazz


def instantiate(clazz: type, candidate_kwargs: dict):
    """
    Instantiate clazz using arguments from 'candidate_kwargs'.
    """
    name2val = {}
    signature = inspect.signature(clazz.__init__)
    iter_params = iter(signature.parameters.values())
    next(iter_params)  # Skip 'self'
    for param in iter_params:
        if param.name in candidate_kwargs:
            name2val[param.name] = candidate_kwargs[param.name]
        else:
            if param.default == inspect.Parameter.empty:
                raise Exception(f"Value of parameter non-optional '{param.name}' not provided, "
                                f"class={type(clazz)}, "
                                f"constructor={signature}")
    return clazz(**name2val)
