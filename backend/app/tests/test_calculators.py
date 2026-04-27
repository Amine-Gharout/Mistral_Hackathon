"""Unit tests for deterministic subsidy calculators."""

from app.calculators.income import determine_income_bracket
from app.calculators.mpr import calculate_mpr_par_geste
from app.calculators.eco_ptz import calculate_eco_ptz


class TestIncomeBracket:
    def test_blue_bracket_hors_idf(self):
        result = determine_income_bracket(
            rfr=15000, household_size=2, is_ile_de_france=False
        )
        assert result["bracket"] == "tres_modeste"
        assert result["color"] == "bleu"

    def test_rose_bracket_idf(self):
        result = determine_income_bracket(
            rfr=80000, household_size=2, is_ile_de_france=True
        )
        assert result["color"] == "rose"

    def test_household_size_affects_bracket(self):
        result_small = determine_income_bracket(
            rfr=25000, household_size=1, is_ile_de_france=False
        )
        result_large = determine_income_bracket(
            rfr=25000, household_size=5, is_ile_de_france=False
        )
        order = {"bleu": 0, "jaune": 1, "violet": 2, "rose": 3}
        assert order[result_large["color"]] <= order[result_small["color"]]


class TestMPRCalculator:
    def test_heat_pump_blue_bracket(self):
        result = calculate_mpr_par_geste(
            geste_id="pac_air_eau",
            bracket="tres_modeste",
        )
        assert result["eligible"] is True
        assert result["amount"] > 0

    def test_ineligible_geste_returns_false(self):
        result = calculate_mpr_par_geste(
            geste_id="nonexistent_geste",
            bracket="tres_modeste",
        )
        assert result["eligible"] is False


class TestEcoPTZ:
    def test_single_geste_loan(self):
        result = calculate_eco_ptz(parcours="par_geste", nb_gestes=1)
        assert result["eligible"] is True
        assert 0 < result["max_amount"] <= 50000

    def test_multiple_gestes_higher_amount(self):
        single = calculate_eco_ptz(parcours="par_geste", nb_gestes=1)
        multiple = calculate_eco_ptz(parcours="par_geste", nb_gestes=3)
        assert multiple["max_amount"] >= single["max_amount"]
