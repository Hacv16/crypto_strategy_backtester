from src.strategy_engine import *


def create_strategy(config: dict) -> Strategy:
    """
    Factory function to dynamically create a strategy object from a
    config dictionary.
    """
    strategy_name = config.get("name", "Unnamed Strategy")
    strategy_description = config.get("description", "No description provided")

    strategy_type = config.get("type", "BuyAndHoldStrategy")
    params = config.get("params", {})

    available_strategies = {cls.__name__: cls for cls in Strategy.__subclasses__()}
    strategy_class = available_strategies.get(strategy_type)

    if strategy_class:
        return strategy_class(strategy_name, strategy_description, **params)
    else:
        raise ValueError(
            f"Unknown strategy type: '{strategy_type}'. "
            f"Available types are: {list(available_strategies.keys())}"
        )
