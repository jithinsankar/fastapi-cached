# fastapicache/inspector.py
import inspect
import enum
from typing import Literal, get_origin, get_args

def get_discrete_params(func: callable) -> dict[str, list]:
    """
    Inspects a function's signature and returns a dictionary of parameters
    that are discrete (Enum or Literal) along with their possible values.

    Args:
        func: The function to inspect.

    Returns:
        A dictionary mapping parameter names to a list of their possible values.
        e.g., {'subregion': [<SubregionEnum.EMEA: 'EMEA'>, ...]}
    """
    discrete_params = {}
    signature = inspect.signature(func)

    for name, param in signature.parameters.items():
        param_type = param.annotation

        # Handle Enums
        if isinstance(param_type, type) and issubclass(param_type, enum.Enum):
            discrete_params[name] = list(param_type)
            continue

        # Handle Literals
        if get_origin(param_type) is Literal:
            discrete_params[name] = list(get_args(param_type))
            continue
            
    return discrete_params