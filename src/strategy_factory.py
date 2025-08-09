from .strategy_engine import *
from .position_sizer import *


def create_position_sizer(config: dict) -> PositionSizer:
    """
    Factory function to create position sizer objects from configuration.

    :param config: Dictionary containing position sizer configuration with 'type' and 'params'
    :return: Instance of a PositionSizer subclass based on the configuration
    """

    sizer_type = config.get("type", "FixedPositionSizer")
    params = config.get("params", {})

    # Map of available position sizer classes
    available_sizers = {cls.__name__: cls for cls in PositionSizer.__subclasses__()}
    sizer_class = available_sizers.get(sizer_type)

    if not sizer_class:
        raise ValueError(
            f"Strategy Factory Error: Unknown position sizer type: '{sizer_type}'. "
            f"Available types: {list(available_sizers.keys())}"
        )

    try:
        return sizer_class(**params)
    except TypeError as e:
        raise ValueError(
            f"Strategy Factory Error: Invalid parameters for {sizer_type}: {e}"
        )


def create_strategy(config: dict) -> Strategy:
    """
    Factory function to dynamically create a strategy object from a configuration dictionary.
    Supports both legacy format (with embedded position sizing) and new format (with separate position sizer).

    :param config: Dictionary containing strategy configuration
    :return: Instance of a Strategy subclass based on the configuration
    """

    strategy_name = config.get("name", "Unnamed Strategy")
    strategy_description = config.get("description", "No description provided")
    strategy_type = config.get("type", "BuyAndHoldStrategy")
    params = config.get("params", {})

    # Build custom position sizer
    position_sizer = create_position_sizer(config["position_sizer"])

    # Get available strategy classes through introspection
    available_strategies = {cls.__name__: cls for cls in Strategy.__subclasses__()}
    strategy_class = available_strategies.get(strategy_type)

    if not strategy_class:
        raise ValueError(
            f"Strategy Factory Error: Unknown strategy type: '{strategy_type}'. "
            f"Available types: {list(available_strategies.keys())}"
        )

    try:
        # Create strategy with position sizer
        return strategy_class(
            name=strategy_name,
            description=strategy_description,
            position_sizer=position_sizer,
            **params
        )
    except TypeError as e:
        raise ValueError(
            f"Strategy Factory Error: Invalid parameters for {strategy_type}: {e}"
        )
