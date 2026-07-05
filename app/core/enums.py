from enum import Enum


class CollarId(str, Enum):
    BLACK = "black"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    GOLD = "gold"


class PaidBy(str, Enum):
    CLIENT = "client"
    EMPLOYEE = "employee"
    COMPANY = "company"


class ReimbursementStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class BillableStatus(str, Enum):
    BILLABLE = "billable"
    NON_BILLABLE = "non_billable"
    WRITE_OFF = "write_off"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class LineItemType(str, Enum):
    LABOUR = "labour"
    EXPENSE = "expense"
    MATERIAL = "material"
    FLAT_FEE = "flat_fee"
    DISCOUNT = "discount"
    TAX = "tax"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class TaxTreatment(str, Enum):
    TAXABLE = "taxable"
    EXEMPT = "exempt"
    ZERO_RATED = "zero_rated"
    OUT_OF_SCOPE = "out_of_scope"
