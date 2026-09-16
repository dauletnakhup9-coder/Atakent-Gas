import enum


class ApplicationType(str, enum.Enum):
    METER_NOT_WORKING = "METER_NOT_WORKING"
    MPI_REMOVAL = "MPI_REMOVAL"
    GAS_LEAK = "GAS_LEAK"


class ApplicationStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Priority(str, enum.Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FileType(str, enum.Enum):
    METER_PHOTO = "METER_PHOTO"
    GAS_LEAK_PHOTO = "GAS_LEAK_PHOTO"
    OTHER = "OTHER"


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DISPATCHER = "DISPATCHER"
    OPERATOR = "OPERATOR"
