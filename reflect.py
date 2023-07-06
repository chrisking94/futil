# -*- coding: utf-8 -*-
# @Time         : 14:13 2022/01/17
# @Author       : Chris
# @Description  : Reflection utilities.
import importlib
import inspect
from typing import Dict, Any


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


def set_fields(obj, field2value: Dict[str, Any], absent_ok=False):
    """
    Set fields for object.
    :param obj: Target object.
    :param field2value: Field name - value mapping.
    :param absent_ok: If 'False', raise exception when the field is absent from 'obj'. Otherwise, ignore the field.
    """
    f2val = vars(obj)
    for name, value in field2value.items():
        if name not in f2val:
            if absent_ok:
                continue
            else:
                raise AttributeError(f"Field '{name}' does not exist on object '{obj}' of type '{type(obj)}'.")
        setattr(obj, name, value)
