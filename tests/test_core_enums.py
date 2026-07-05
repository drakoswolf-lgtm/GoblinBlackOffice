import pytest
from app.core.enums import (
    CollarId,
    PaidBy,
    ReimbursementStatus,
    BillableStatus,
    InvoiceStatus,
    LineItemType,
    ReviewStatus,
    TaxTreatment,
)


def test_collar_id_values():
    assert CollarId.BLACK == "black"
    assert CollarId.RED == "red"
    assert CollarId.BLUE == "blue"
    assert CollarId.GREEN == "green"
    assert CollarId.GOLD == "gold"


def test_paid_by_values():
    assert PaidBy.CLIENT == "client"
    assert PaidBy.EMPLOYEE == "employee"
    assert PaidBy.COMPANY == "company"


def test_reimbursement_status_values():
    assert ReimbursementStatus.PENDING == "pending"
    assert ReimbursementStatus.APPROVED == "approved"
    assert ReimbursementStatus.REJECTED == "rejected"
    assert ReimbursementStatus.PAID == "paid"


def test_billable_status_values():
    assert BillableStatus.BILLABLE == "billable"
    assert BillableStatus.NON_BILLABLE == "non_billable"
    assert BillableStatus.WRITE_OFF == "write_off"


def test_invoice_status_values():
    assert InvoiceStatus.DRAFT == "draft"
    assert InvoiceStatus.SENT == "sent"
    assert InvoiceStatus.VIEWED == "viewed"
    assert InvoiceStatus.PARTIAL == "partial"
    assert InvoiceStatus.PAID == "paid"
    assert InvoiceStatus.OVERDUE == "overdue"
    assert InvoiceStatus.VOID == "void"


def test_line_item_type_values():
    assert LineItemType.LABOUR == "labour"
    assert LineItemType.EXPENSE == "expense"
    assert LineItemType.MATERIAL == "material"
    assert LineItemType.FLAT_FEE == "flat_fee"
    assert LineItemType.DISCOUNT == "discount"
    assert LineItemType.TAX == "tax"


def test_review_status_values():
    assert ReviewStatus.PENDING == "pending"
    assert ReviewStatus.IN_REVIEW == "in_review"
    assert ReviewStatus.APPROVED == "approved"
    assert ReviewStatus.REJECTED == "rejected"
    assert ReviewStatus.CHANGES_REQUESTED == "changes_requested"


def test_tax_treatment_values():
    assert TaxTreatment.TAXABLE == "taxable"
    assert TaxTreatment.EXEMPT == "exempt"
    assert TaxTreatment.ZERO_RATED == "zero_rated"
    assert TaxTreatment.OUT_OF_SCOPE == "out_of_scope"


def test_enums_are_str_subclass():
    for enum_class in [
        CollarId, PaidBy, ReimbursementStatus, BillableStatus,
        InvoiceStatus, LineItemType, ReviewStatus, TaxTreatment,
    ]:
        for member in enum_class:
            assert isinstance(member, str)


def test_enum_members_are_iterable():
    assert len(list(CollarId)) == 5
    assert len(list(PaidBy)) == 3
    assert len(list(ReimbursementStatus)) == 4
    assert len(list(BillableStatus)) == 3
    assert len(list(InvoiceStatus)) == 7
    assert len(list(LineItemType)) == 6
    assert len(list(ReviewStatus)) == 5
    assert len(list(TaxTreatment)) == 4
