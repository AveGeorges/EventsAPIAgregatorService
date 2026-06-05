class DomainError(Exception):
    """Базовая доменная ошибка."""

    status_code: int = 400
    code: str = "domain_error"
    default_message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
