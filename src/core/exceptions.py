class SniperError(Exception):
    """Base exception for Local Sniper Agent."""


class ConfigError(SniperError):
    pass


class ScraperError(SniperError):
    pass


class AnalysisError(SniperError):
    pass


class DealEvaluationError(SniperError):
    pass


class NotificationError(SniperError):
    pass
