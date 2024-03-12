"""Tests for read and save filings."""

from datetime import date
import os
from unittest.mock import patch

import pytest

from pyesef.helpers.hierarchy import Hierarchy
from pyesef.helpers.read_and_save_filings import (
    data_list_to_clean_df,
    read_and_save_filings,
)
from pyesef.load_parse_file.common import EsefData

HIERARCHY_TEST_DATA = {
    "AdjustmentsForDecreaseIncreaseInTradeAndOtherReceivables": (
        "CashFlowsFromUsedInOperatingActivities"
    ),
    "AdjustmentsForIncreaseDecreaseInTradeAndOtherPayables": (
        "CashFlowsFromUsedInOperatingActivities"
    ),
    "CashAndCashEquivalents": "CurrentAssets",
    "CashFlowsFromUsedInFinancingActivities": (
        "IncreaseDecreaseInCashAndCashEquivalents"
    ),
    "CashFlowsFromUsedInInvestingActivities": (
        "IncreaseDecreaseInCashAndCashEquivalents"
    ),
    "CashFlowsFromUsedInOperatingActivities": (
        "IncreaseDecreaseInCashAndCashEquivalents"
    ),
    "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital": (
        "CashFlowsFromUsedInOperatingActivities"
    ),
    "CurrentAccruedExpensesAndOtherCurrentLiabilities": "CurrentLiabilities",
    "CurrentAssets": "Assets",
    "CurrentFinancialAssetsAtFairValueThroughProfitOrLoss": "CurrentAssets",
    "CurrentLiabilities": "EquityAndLiabilities",
    "CurrentPrepaidExpenses": "CurrentAssets",
    "DeferredTaxExpenseIncomeRelatingToOriginationAndReversalOfTemporaryDifferences": (
        "ProfitLoss"
    ),
    "DeferredTaxLiabilities": "NoncurrentLiabilities",
    "DirectOperatingExpenseFromInvestmentProperty": (
        "RentalIncomeFromInvestmentPropertyNetOfDirectOperatingExpense"
    ),
    "DividendsPaidClassifiedAsFinancingActivities": (
        "CashFlowsFromUsedInFinancingActivities"
    ),
    "DividendsReceivedClassifiedAsOperatingActivities": (
        "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital"
    ),
    "Equity": "EquityAndLiabilities",
    "FinanceCosts": "ResultatEfterFinansiellaKostnader",
    "FinanceIncome": "ResultatEfterFinansiellaKostnader",
    "Forvaltningsresultat": (
        "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital"
    ),
    "ForvaltningsresultatFranIntresseforetagOchJointVenture": (
        "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital"
    ),
    "GainsLossesOnChangeInFairValueOfDerivatives": "ProfitLossBeforeTax",
    "GeneralAndAdministrativeExpense": "ResultatEfterFinansiellaKostnader",
    "IncomeTaxExpenseContinuingOperations": "ProfitLoss",
    "IncomeTaxesPaidClassifiedAsOperatingActivities": (
        "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital"
    ),
    "InvesteringarIBefintligaFastigheterOchOvrigaAnlaggningstillgangar": (
        "CashFlowsFromUsedInInvestingActivities"
    ),
    "InvesteringarINybyggnation": "CashFlowsFromUsedInInvestingActivities",
    "InvestmentProperty": "NoncurrentAssets",
    "InvestmentsInSubsidiariesJointVenturesAndAssociates": "NoncurrentAssets",
    "LongtermBorrowings": "NoncurrentLiabilities",
    "NoncurrentAssets": "Assets",
    "NoncurrentDerivativeFinancialLiabilities": "NoncurrentLiabilities",
    "NoncurrentLeaseLiabilities": "NoncurrentLiabilities",
    "NoncurrentLiabilities": "EquityAndLiabilities",
    "NoncurrentReceivables": "NoncurrentAssets",
    "OtherAdjustmentsForNoncashItems": (
        "CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital"
    ),
    "OtherComprehensiveIncome": "ComprehensiveIncome",
    "OtherCurrentNonfinancialLiabilities": "CurrentLiabilities",
    "OtherNoncurrentAssets": "NoncurrentAssets",
    "OtherNoncurrentFinancialAssets": "NoncurrentAssets",
    "ProceedsFromBorrowingsClassifiedAsFinancingActivities": (
        "CashFlowsFromUsedInFinancingActivities"
    ),
    "ProceedsFromIssuingShares": "CashFlowsFromUsedInFinancingActivities",
    "ProceedsFromSalesOfInvestmentProperty": "CashFlowsFromUsedInInvestingActivities",
    "ProfitLoss": "ComprehensiveIncome",
    "ProfitLossBeforeTax": "ProfitLoss",
    "PropertyTaxExpense": (
        "RentalIncomeFromInvestmentPropertyNetOfDirectOperatingExpense"
    ),
    "PurchaseOfFinancialInstrumentsClassifiedAsInvestingActivities": (
        "CashFlowsFromUsedInInvestingActivities"
    ),
    "PurchaseOfInvestmentProperty": "CashFlowsFromUsedInInvestingActivities",
    "RentalIncomeFromInvestmentProperty": (
        "RentalIncomeFromInvestmentPropertyNetOfDirectOperatingExpense"
    ),
    "RentalIncomeFromInvestmentPropertyNetOfDirectOperatingExpense": (
        "ResultatEfterFinansiellaKostnader"
    ),
    "RepaymentsOfBorrowingsClassifiedAsFinancingActivities": (
        "CashFlowsFromUsedInFinancingActivities"
    ),
    "ResultatEfterFinansiellaKostnader": "ProfitLossBeforeTax",
    "RightofuseAssetsThatDoNotMeetDefinitionOfInvestmentProperty": "NoncurrentAssets",
    "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod": (
        "ResultatEfterFinansiellaKostnader"
    ),
    "ShorttermBorrowings": "CurrentLiabilities",
    "TradeAndOtherCurrentReceivables": "CurrentAssets",
    "VardeforandringarForvaltningsfastigheter": "ProfitLossBeforeTax",
}


def test_data_list_to_clean_df__drop_duplicates() -> None:
    """Test drop dupliates part of function data_list_to_clean_df."""
    function_result = data_list_to_clean_df(
        data_list=[
            EsefData(
                period_end=date(2023, 12, 31),
                lei="lei123",
                wider_anchor_or_xml_name="GainsLossesOnDisposalsOfInvestmentProperties",
                xml_name="GainsLossesOnDisposalsOfInvestmentProperties",
                xml_name_parent="ProfitLossBeforeTax",
                value=-1577000.0,
                legal_name=None,
                wider_anchor=None,
                membership=None,
                label=None,
                currency="SEK",
                is_company_defined=False,
                sort_order=1,
            ),
            EsefData(
                period_end=date(2023, 12, 31),
                lei="lei123",
                wider_anchor_or_xml_name="GainsLossesOnDisposalsOfInvestmentProperties",
                xml_name="GainsLossesOnDisposalsOfInvestmentProperties",
                xml_name_parent="ProfitLossBeforeTax",
                value=-1577000.0,
                legal_name=None,
                wider_anchor=None,
                membership=None,
                label=None,
                currency="SEK",
                is_company_defined=False,
                sort_order=1,
            ),
        ]
    )
    assert len(function_result) == 1


def test_read_and_save_filings() -> None:
    """Test read_and_save_filings."""
    with patch(
        "pyesef.helpers.read_and_save_filings.PATH_ARCHIVES",
        os.path.abspath(os.path.join("tests", "fixtures")),
    ):
        read_and_save_filings(move_parsed_file=False)

        assert True


@pytest.mark.parametrize(
    "xml_name, parent_node",
    [
        ("GeneralAndAdministrativeExpense", "ComprehensiveIncome"),
        ("CashAndCashEquivalents", "Assets"),
        (
            "RepaymentsOfBorrowingsClassifiedAsFinancingActivities",
            "IncreaseDecreaseInCashAndCashEquivalents",
        ),
    ],
)
def test_hierarchy_function(xml_name, parent_node) -> None:
    """Test node functionality."""
    hierarchy = Hierarchy(hierarchy_dict=HIERARCHY_TEST_DATA)

    ultimate_parent = hierarchy.get_ultimate_parent(xml_name)

    assert ultimate_parent is not None
    assert ultimate_parent.name == parent_node