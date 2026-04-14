from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, url_for

from frontend_contract import (
    ScenarioInput,
    collect_scenario_input,
    compare_scenarios,
    run_scenario,
)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "comp1110-restaurant-queue-simulation"

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.route("/run", methods=["GET", "POST"])
    def run() -> str:
        if request.method == "GET":
            scenario = ScenarioInput.default(label="Scenario A")
            return render_template(
                "result_form.html",
                page_title="Run scenario",
                scenario=scenario,
                result=None,
                comparison=None,
                mode="single",
                fallback_notice=None,
            )

        scenario = collect_scenario_input(request, prefix="")
        if scenario is None:
            flash("Please provide at least a scenario name and restaurant configuration.")
            return redirect(url_for("run"))

        try:
            result = run_scenario(scenario)
        except ValueError as exc:
            flash(str(exc))
            return render_template(
                "result_form.html",
                page_title="Run scenario",
                scenario=scenario,
                result=None,
                comparison=None,
                mode="single",
                fallback_notice=None,
            )

        return render_template(
            "result_form.html",
            page_title="Run scenario",
            scenario=scenario,
            result=result,
            comparison=None,
            mode="single",
            fallback_notice=result.fallback_notice,
        )

    @app.route("/compare", methods=["GET", "POST"])
    def compare() -> str:
        if request.method == "GET":
            left = ScenarioInput.default(label="Scenario A")
            right = ScenarioInput.default(label="Scenario B")
            return render_template(
                "compare.html",
                left=left,
                right=right,
                comparison=None,
                fallback_notice=None,
            )

        left = collect_scenario_input(request, prefix="a_")
        right = collect_scenario_input(request, prefix="b_")
        if left is None or right is None:
            flash("Please provide both scenarios before comparing them.")
            return redirect(url_for("compare"))

        try:
            left_result = run_scenario(left)
            right_result = run_scenario(right)
            comparison = compare_scenarios(left_result, right_result)
        except ValueError as exc:
            flash(str(exc))
            return render_template(
                "compare.html",
                left=left,
                right=right,
                comparison=None,
                fallback_notice=None,
            )

        return render_template(
            "compare.html",
            left=left,
            right=right,
            comparison=comparison,
            fallback_notice=left_result.fallback_notice or right_result.fallback_notice,
        )

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok", "service": "frontend"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
