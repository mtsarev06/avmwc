class NotPerformedException(Exception):
    pass


class ArchivingError(NotPerformedException):
    pass


class ExtractionError(NotPerformedException):
    pass
